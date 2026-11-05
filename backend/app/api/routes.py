from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import jwt
from collections import defaultdict, deque
from threading import Lock
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from ..core.config import settings
from ..core.security import verify_password, create_access_token, decode_access_token
from ..db import get_db
from ..models.entities import User, CivicIssue, IssueAction
from ..schemas import LoginRequest, TokenResponse, IssueActionIn, OverviewOut, PriorityContextIn
from ..services.detector import detector, DetectorUnavailable
from ..services.media import store_image
from ..services.priority import score_issue, image_area_severity
from ..services.duplicates import find_duplicate_candidates

router = APIRouter(prefix="/api/v1")
_upload_events = defaultdict(deque)
_upload_lock = Lock()
bearer = HTTPBearer(auto_error=False)

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(401, "Authentication required.")
    try:
        payload = decode_access_token(credentials.credentials)
        user = db.scalar(select(User).where(User.email == payload.get("sub"), User.is_active.is_(True)))
        if not user:
            raise HTTPException(401, "Invalid or inactive account.")
        return user
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(401, "Invalid or expired token.")

def admin_user(user: User = Depends(current_user)) -> User:
    if user.role not in {"admin", "reviewer"}:
        raise HTTPException(403, "Administrator or reviewer role required.")
    return user

def serialize_issue(issue: CivicIssue) -> dict:
    return {
        "id": issue.id, "public_id": issue.public_id, "category": issue.verified_category or issue.category,
        "ai_category": issue.category, "verified_category": issue.verified_category,
        "classification_source": "human_verified" if issue.verified_category else ("ai" if issue.category else "pending"),
        "declared_category": issue.declared_category, "description": issue.description,
        "latitude": issue.latitude, "longitude": issue.longitude, "location_label": issue.location_label,
        "image_url": f"/api/v1/issues/{issue.id}/evidence/original",
        "annotated_image_url": f"/api/v1/issues/{issue.id}/evidence/annotated" if issue.annotated_image_path else None,
        "detection_confidence": issue.detection_confidence, "detection_status": issue.detection_status,
        "detection_payload": issue.detection_payload, "priority_score": issue.priority_score,
        "priority_level": issue.priority_level, "priority_breakdown": issue.priority_breakdown,
        "verification_status": issue.verification_status, "status": issue.status,
        "duplicate_candidates": issue.duplicate_candidates,
        "created_at": issue.created_at, "updated_at": issue.updated_at,
    }

@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return TokenResponse(access_token=create_access_token(user.email, user.role), role=user.role)

@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"email": user.email, "display_name": user.display_name, "role": user.role}

@router.post("/issues")
def create_issue(
    request: Request,
    image: UploadFile = File(...),
    latitude: float = Form(...), longitude: float = Form(...),
    description: str | None = Form(default=None),
    location_label: str | None = Form(default=None),
    declared_category: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    # Basic in-process protection for the public prototype endpoint. Production should
    # enforce distributed rate limits at the gateway as well.
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp()
    with _upload_lock:
        events = _upload_events[client_ip]
        while events and now - events[0] > 3600:
            events.popleft()
        if len(events) >= 10:
            raise HTTPException(429, "Too many reports from this network. Please try again later.")
        events.append(now)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(422, "Latitude or longitude is outside valid bounds.")
    if declared_category not in {None, "", "pothole", "garbage_accumulation"}:
        raise HTTPException(422, "Only pothole and garbage_accumulation are supported categories.")
    if description and len(description) > 2000:
        raise HTTPException(422, "Description must be 2,000 characters or fewer.")
    filename, width, height = store_image(image)
    public_id = f"CIV-{uuid4().hex[:16].upper()}"
    issue = CivicIssue(
        public_id=public_id, reporter_id=None, declared_category=declared_category or None,
        description=description, latitude=latitude, longitude=longitude,
        location_label=location_label, image_path=str(settings.media_path / filename),
        detection_status="pending", status="processing"
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    try:
        result = detector.predict(issue.image_path)
        issue.detection_payload = result
        issue.detection_status = result["state"]
        issue.category = result.get("primary_category")
        issue.detection_confidence = result.get("primary_confidence")
        if result.get("annotated_path"):
            issue.annotated_image_path = result["annotated_path"]
        if issue.category:
            issue.verification_status = "needs_review"
            issue.status = "needs_review"
            severity = image_area_severity(result["detections"], width, height, issue.category)
            factor_name = "visible_severity" if issue.category == "pothole" else "visible_extent"
            breakdown = score_issue(issue.category, {factor_name: severity})
            issue.priority_score = breakdown["score"]
            issue.priority_level = breakdown["level"]
            issue.priority_breakdown = {**breakdown, "provisional": True, "context_missing": True, "warning": "Image-area severity is only a visual proxy. Road exposure, public context, recurrence and duration require verified data or human review."}
            issue.duplicate_candidates = find_duplicate_candidates(db, issue)
        else:
            issue.priority_score = None
            issue.priority_level = "unassessed"
            issue.status = "needs_review"
    except DetectorUnavailable as exc:
        issue.detection_status = "not_configured"
        issue.detection_payload = {"state": "not_configured", "message": str(exc), "detections": []}
        issue.status = "awaiting_model"
        issue.priority_level = "unassessed"
    except Exception as exc:
        issue.detection_status = "error"
        issue.detection_payload = {"state": "error", "message": "Image analysis failed. Manual review is required."}
        issue.status = "needs_review"
        issue.priority_level = "unassessed"
    db.add(IssueAction(issue_id=issue.id, actor="system", action_type="report_submitted", new_status=issue.status, notes="Citizen issue report received."))
    db.commit()
    db.refresh(issue)
    return serialize_issue(issue)

@router.get("/issues")
def list_issues(category: str | None = None, priority: str | None = None, status: str | None = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    query = select(CivicIssue).order_by(CivicIssue.created_at.desc())
    if category in {"pothole", "garbage_accumulation"}: query = query.where(func.coalesce(CivicIssue.verified_category, CivicIssue.category) == category)
    if priority in {"low", "medium", "high", "critical"}: query = query.where(CivicIssue.priority_level == priority)
    if status: query = query.where(CivicIssue.status == status)
    rows = db.scalars(query.offset(max(0, offset)).limit(min(max(1, limit), 500))).all()
    return [serialize_issue(x) for x in rows]

@router.get("/issues/track/{public_id}")
def track_issue(public_id: str, db: Session = Depends(get_db)):
    issue = db.scalar(select(CivicIssue).where(CivicIssue.public_id == public_id))
    if not issue:
        raise HTTPException(404, "Report not found.")
    # Public response intentionally omits reporter identity and private admin notes.
    return {"public_id": issue.public_id, "category": issue.verified_category or issue.category, "declared_category": issue.declared_category, "classification_source": "human_verified" if issue.verified_category else ("ai" if issue.category else "pending"), "status": issue.status, "priority_level": issue.priority_level, "location_label": issue.location_label, "created_at": issue.created_at, "updated_at": issue.updated_at}

@router.get("/issues/{issue_id}")
def issue_detail(issue_id: int, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    issue = db.get(CivicIssue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found.")
    data = serialize_issue(issue)
    data["actions"] = [{"actor": a.actor, "action_type": a.action_type, "previous_status": a.previous_status, "new_status": a.new_status, "notes": a.notes, "created_at": a.created_at, "evidence_url": f"/api/v1/issues/{issue.id}/evidence/resolution?action_id={a.id}" if a.evidence_path else None} for a in issue.actions]
    return data

@router.patch("/issues/{issue_id}/review")
def review_issue(issue_id: int, payload: IssueActionIn, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    issue = db.get(CivicIssue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found.")
    allowed = {"submitted", "processing", "awaiting_model", "needs_review", "verified", "under_action", "work_reported_completed", "resolution_verified", "reopened", "rejected"}
    if payload.status not in allowed: raise HTTPException(422, "Invalid status.")
    if payload.status == "resolution_verified":
        if issue.status != "work_reported_completed":
            raise HTTPException(409, "Record completion evidence and mark work as reported completed first.")
        evidence = db.scalar(select(IssueAction).where(IssueAction.issue_id == issue.id, IssueAction.action_type == "resolution_evidence_uploaded").limit(1))
        if not evidence:
            raise HTTPException(409, "Upload resolution evidence before marking this issue verified.")
    previous = issue.status
    if payload.category_override:
        issue.verified_category = payload.category_override
        issue.verification_status = "verified"
        issue.duplicate_candidates = find_duplicate_candidates(db, issue)
    if payload.status == "verified" and not (issue.verified_category or issue.category):
        raise HTTPException(409, "Verify a supported issue category before marking this report verified.")
    issue.status = payload.status
    if payload.status == "verified": issue.verification_status = "verified"
    if payload.status == "resolution_verified": issue.verification_status = "resolution_verified"
    if payload.priority_override is not None:
        issue.priority_score = float(payload.priority_override)
        issue.priority_level = "critical" if payload.priority_override >= 75 else "high" if payload.priority_override >= 50 else "medium" if payload.priority_override >= 25 else "low"
        issue.priority_breakdown = {"override": True, "score": issue.priority_score, "reason": payload.notes, "reviewer": user.email}
    db.add(IssueAction(issue_id=issue.id, actor=user.email, action_type="admin_review", previous_status=previous, new_status=issue.status, notes=payload.notes))
    db.commit()
    db.refresh(issue)
    return serialize_issue(issue)



@router.post("/issues/{issue_id}/resolution-evidence")
def upload_resolution_evidence(issue_id: int, image: UploadFile = File(...), notes: str | None = Form(default=None), db: Session = Depends(get_db), user: User = Depends(admin_user)):
    issue = db.get(CivicIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found.")
    filename, _, _ = store_image(image)
    path = str(settings.media_path / filename)
    previous_status = issue.status
    action = IssueAction(issue_id=issue.id, actor=user.email, action_type="resolution_evidence_uploaded", previous_status=previous_status, new_status="work_reported_completed", notes=notes or "Resolution evidence uploaded for review.", evidence_path=path)
    db.add(action)
    if issue.status != "work_reported_completed":
        issue.status = "work_reported_completed"
    db.commit()
    db.refresh(action)
    return {"message": "Evidence uploaded. An authorised reviewer can now assess whether the issue is resolved.", "evidence_url": f"/api/v1/issues/{issue.id}/evidence/resolution?action_id={action.id}", "status": issue.status}

@router.patch("/issues/{issue_id}/priority-context")
def update_priority_context(issue_id: int, payload: PriorityContextIn, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    issue = db.get(CivicIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found.")
    effective_category = issue.verified_category or issue.category
    if effective_category not in {"pothole", "garbage_accumulation"}:
        raise HTTPException(409, "Priority context cannot be scored until a supported issue category is verified.")
    values = payload.model_dump(exclude={"notes"})
    applicable = {"pothole": {"visible_severity", "road_exposure", "safety_context", "recurrence", "duration"},
                  "garbage_accumulation": {"visible_extent", "public_obstruction", "location_context", "recurrence", "duration"}}[effective_category]
    values = {key: value for key, value in values.items() if key in applicable}
    # Do not silently score missing values. A reviewer must provide at least one measured factor.
    if not any(value is not None for value in values.values()):
        raise HTTPException(422, "Provide at least one verified priority factor.")
    result = score_issue(effective_category, values)
    issue.priority_score = result["score"]
    issue.priority_level = result["level"]
    issue.priority_breakdown = {**result, "provisional": True, "reviewer_context": True, "reviewer": user.email, "notes": payload.notes, "warning": "Human-entered context supports this provisional score; validate scoring rules with local field assessments."}
    db.add(IssueAction(issue_id=issue.id, actor=user.email, action_type="priority_context_updated", notes=payload.notes or "Priority context updated."))
    db.commit()
    db.refresh(issue)
    return serialize_issue(issue)

@router.get("/issues/{issue_id}/evidence/{kind}")
def get_issue_evidence(issue_id: int, kind: str, action_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    issue = db.get(CivicIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found.")
    if kind == "original":
        path = Path(issue.image_path)
    elif kind == "annotated":
        if not issue.annotated_image_path:
            raise HTTPException(404, "Annotated image is not available.")
        path = Path(issue.annotated_image_path)
    elif kind == "resolution":
        if not action_id:
            raise HTTPException(422, "action_id is required for resolution evidence.")
        action = db.scalar(select(IssueAction).where(IssueAction.id == action_id, IssueAction.issue_id == issue.id, IssueAction.action_type == "resolution_evidence_uploaded"))
        if not action or not action.evidence_path:
            raise HTTPException(404, "Resolution evidence not found.")
        path = Path(action.evidence_path)
    else:
        raise HTTPException(404, "Unknown evidence type.")
    if not path.is_file():
        raise HTTPException(404, "Evidence file not found.")
    return FileResponse(path, media_type="image/jpeg", filename=path.name, headers={"Cache-Control": "private, no-store"})

@router.get("/map/issues")
def map_issues(db: Session = Depends(get_db), user: User = Depends(admin_user)):
    rows = db.scalars(select(CivicIssue).order_by(CivicIssue.created_at.desc()).limit(1000)).all()
    return [{"id": x.id, "public_id": x.public_id, "category": x.verified_category or x.category, "latitude": x.latitude, "longitude": x.longitude, "priority_level": x.priority_level, "status": x.status} for x in rows]

@router.get("/analytics/overview", response_model=OverviewOut)
def overview(db: Session = Depends(get_db), user: User = Depends(admin_user)):
    total = db.scalar(select(func.count(CivicIssue.id))) or 0
    def count_where(*conditions): return db.scalar(select(func.count(CivicIssue.id)).where(*conditions)) or 0
    return OverviewOut(
        total=total,
        potholes=count_where(func.coalesce(CivicIssue.verified_category, CivicIssue.category) == "pothole"),
        garbage=count_where(func.coalesce(CivicIssue.verified_category, CivicIssue.category) == "garbage_accumulation"),
        critical=count_where(CivicIssue.priority_level == "critical"),
        high=count_where(CivicIssue.priority_level == "high"),
        medium=count_where(CivicIssue.priority_level == "medium"),
        low=count_where(CivicIssue.priority_level == "low"),
        awaiting_review=count_where(CivicIssue.status.in_(["needs_review", "awaiting_model"])),
        resolved=count_where(CivicIssue.status == "resolution_verified"),
        model_status=detector.status["state"]
    )

@router.get("/models/status")
def model_status(user: User = Depends(admin_user)):
    return detector.status

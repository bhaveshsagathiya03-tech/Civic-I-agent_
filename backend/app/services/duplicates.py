from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, asin, sqrt
from sqlalchemy import select, text, func, or_
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.entities import CivicIssue

def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6_371_000
    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * radius * asin(sqrt(a))

def find_duplicate_candidates(db: Session, issue: CivicIssue) -> list[dict]:
    effective_category = issue.verified_category or issue.category
    if not effective_category:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.duplicate_window_days)
    # PostGIS performs metre-based geography distance checks when running on PostgreSQL.
    if db.bind and db.bind.dialect.name == "postgresql":
        try:
            rows = db.execute(text("""
                SELECT id, public_id, latitude, longitude, created_at
                FROM civic_issues
                WHERE id <> :issue_id
                  AND COALESCE(verified_category, category) = :category
                  AND created_at >= :cutoff
                  AND ST_DWithin(
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                    :radius
                  )
                ORDER BY created_at DESC
                LIMIT 100
            """), {"issue_id": issue.id, "category": effective_category, "cutoff": cutoff,
                   "longitude": issue.longitude, "latitude": issue.latitude, "radius": settings.duplicate_radius_m}).mappings().all()
            return [{"issue_id": r["id"], "public_id": r["public_id"], "distance_m": round(haversine_m(issue.latitude, issue.longitude, r["latitude"], r["longitude"]), 1), "created_at": r["created_at"].isoformat(), "category": effective_category} for r in rows]
        except Exception:
            # A missing PostGIS extension should not silently break citizen reporting.
            db.rollback()
    rows = db.scalars(select(CivicIssue).where(
        CivicIssue.id != issue.id,
        func.coalesce(CivicIssue.verified_category, CivicIssue.category) == effective_category,
        CivicIssue.created_at >= cutoff
    ).order_by(CivicIssue.created_at.desc()).limit(250)).all()
    matches = []
    for row in rows:
        distance = haversine_m(issue.latitude, issue.longitude, row.latitude, row.longitude)
        if distance <= settings.duplicate_radius_m:
            matches.append({"issue_id": row.id, "public_id": row.public_id, "distance_m": round(distance, 1), "created_at": row.created_at.isoformat(), "category": row.category})
    return matches

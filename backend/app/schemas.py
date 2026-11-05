from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

Category = Literal["pothole", "garbage_accumulation"]
IssueStatus = Literal["submitted", "processing", "awaiting_model", "needs_review", "verified", "under_action", "work_reported_completed", "resolution_verified", "reopened", "rejected"]

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    public_id: str
    category: str | None
    ai_category: str | None = None
    verified_category: str | None = None
    classification_source: str = "pending"
    declared_category: str | None
    description: str | None
    latitude: float
    longitude: float
    location_label: str | None
    image_url: str
    annotated_image_url: str | None
    detection_confidence: float | None
    detection_status: str
    detection_payload: dict | None
    priority_score: float | None
    priority_level: str
    priority_breakdown: dict | None
    verification_status: str
    status: str
    duplicate_candidates: list | None
    created_at: datetime
    updated_at: datetime

class IssueActionIn(BaseModel):
    status: IssueStatus
    notes: str | None = Field(default=None, max_length=2000)
    priority_override: int | None = Field(default=None, ge=0, le=100)
    category_override: Category | None = None

class OverviewOut(BaseModel):
    total: int
    potholes: int
    garbage: int
    critical: int
    high: int
    medium: int
    low: int
    awaiting_review: int
    resolved: int
    model_status: str

class PriorityContextIn(BaseModel):
    visible_severity: float | None = Field(default=None, ge=0, le=100)
    road_exposure: float | None = Field(default=None, ge=0, le=100)
    safety_context: float | None = Field(default=None, ge=0, le=100)
    visible_extent: float | None = Field(default=None, ge=0, le=100)
    public_obstruction: float | None = Field(default=None, ge=0, le=100)
    location_context: float | None = Field(default=None, ge=0, le=100)
    recurrence: float | None = Field(default=None, ge=0, le=100)
    duration: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=2000)

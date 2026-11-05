from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="citizen")
    display_name: Mapped[str] = mapped_column(String(120), default="Citizen")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    issues: Mapped[list["CivicIssue"]] = relationship(back_populates="reporter")

class CivicIssue(Base):
    __tablename__ = "civic_issues"
    __table_args__ = (Index("ix_issue_lat_lon", "latitude", "longitude"), Index("ix_issue_category_status", "category", "status"))
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verified_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    declared_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_path: Mapped[str] = mapped_column(String(500))
    annotated_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    detection_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    detection_status: Mapped[str] = mapped_column(String(40), default="pending")
    detection_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_level: Mapped[str] = mapped_column(String(20), default="unassessed")
    priority_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="needs_review")
    status: Mapped[str] = mapped_column(String(40), default="submitted")
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("civic_issues.id"), nullable=True)
    duplicate_candidates: Mapped[list | None] = mapped_column(JSON, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    reporter: Mapped[User | None] = relationship(back_populates="issues")
    actions: Mapped[list["IssueAction"]] = relationship(back_populates="issue", cascade="all, delete-orphan")

class IssueAction(Base):
    __tablename__ = "issue_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("civic_issues.id", ondelete="CASCADE"), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    action_type: Mapped[str] = mapped_column(String(60))
    previous_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    issue: Mapped[CivicIssue] = relationship(back_populates="actions")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(120))
    weights_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    class_names: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="not_configured")
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

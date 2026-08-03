from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"
SEVERITIES = (SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL)

STATUS_NEW = "new"
STATUS_INVESTIGATING = "investigating"
STATUS_RESOLVED = "resolved"
STATUS_FALSE_POSITIVE = "false_positive"
STATUSES = (STATUS_NEW, STATUS_INVESTIGATING, STATUS_RESOLVED, STATUS_FALSE_POSITIVE)


class SecurityEvent(db.Model):
    """A single security event that is ingested from a customer's tooling."""
    __tablename__ = "security_events"
    __table_args__ = (
        CheckConstraint(
            f"severity IN ({', '.join(repr(s) for s in SEVERITIES)})", name="severity_valid"
        ),
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in STATUSES)})", name="status_valid"
        ),
        Index(
            "uq_security_events_org_source_external",
            "org_id",
            "source",
            "external_id",
            unique=True,
        ),
        Index(
            "ix_security_events_org_occurred_at",
            "org_id",
            db.desc("occurred_at"),
            db.desc("id"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )

    # --- Identity at the source ---
    source: Mapped[str] = mapped_column(String(60), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)

    # --- Content ---
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=db.text("'{}'::jsonb")
    )

    # --- Triage State ---
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=STATUS_NEW
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    # --- Time ---
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    organization: Mapped["Organization"] = relationship()
    assigned_to: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} org={self.org_id} {self.severity} {self.status}>"

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.organization import Organization

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLES = (ROLE_ADMIN, ROLE_ANALYST)


class User(db.Model):
    """A user within the system."""
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"role IN ({', '.join(repr(r) for r in ROLES)})", name="role_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Every write should go through the API, so updated_at should be fine;
    # no need for a DB-level guarantee for this project
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    organization: Mapped["Organization"] = relationship(back_populates="users")

    @property
    def is_provider(self) -> bool:
        return self.organization.is_provider

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} org={self.org_id} role={self.role}>"

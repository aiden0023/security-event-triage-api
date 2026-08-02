from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.user import User


class Organization(db.Model):
    """An organization using the API (could be a customer or the provider org)"""
    __tablename__ = "organizations"
    __table_args__ = (
        Index(
            "uq_organizations_is_provider",
            "is_provider",
            unique=True,
            postgresql_where=text("is_provider"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    is_provider: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    users: Mapped[list["User"]] = relationship(back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name!r} is_provider={self.is_provider}>"

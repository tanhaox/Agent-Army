from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class GuestIdentity(Base, BaseMixin):
    __tablename__ = "guest_identities"

    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    personality: Mapped[str | None] = mapped_column(String(200), nullable=True)
    core_issue: Mapped[str] = mapped_column(Text, nullable=False)
    speaking_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, default=list)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    creator: Mapped["User | None"] = relationship(back_populates="guest_identities")  # noqa: F821
    script_projects: Mapped[list["ScriptProject"]] = relationship(back_populates="guest")  # noqa: F821

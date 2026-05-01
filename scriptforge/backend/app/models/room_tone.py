from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class RoomTone(Base, BaseMixin):
    __tablename__ = "room_tones"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_rules: Mapped[str] = mapped_column(Text, nullable=False)
    forbidden_topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped["User | None"] = relationship(back_populates="room_tones")  # noqa: F821
    script_projects: Mapped[list["ScriptProject"]] = relationship(back_populates="room_tone")  # noqa: F821

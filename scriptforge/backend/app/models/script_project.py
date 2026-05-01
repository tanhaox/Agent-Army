from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class ScriptProject(Base, BaseMixin):
    __tablename__ = "script_projects"

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("room_tones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    persona_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    guest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guest_identities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    persona_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    script_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    emotion_curve: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strategy_mix: Mapped[str | None] = mapped_column(String(100), nullable=True)
    multi_version: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("script_projects.id", ondelete="SET NULL"), nullable=True
    )
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sensitive_hits: Mapped[dict | None] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    creator: Mapped["User | None"] = relationship(back_populates="script_projects")  # noqa: F821
    room_tone: Mapped["RoomTone | None"] = relationship(back_populates="script_projects")  # noqa: F821
    persona: Mapped["Persona | None"] = relationship(back_populates="script_projects")  # noqa: F821
    guest: Mapped["GuestIdentity | None"] = relationship(back_populates="script_projects")  # noqa: F821
    parent: Mapped["ScriptProject | None"] = relationship(
        remote_side="ScriptProject.id", backref="children"
    )

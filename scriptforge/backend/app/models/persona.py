from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class Persona(Base, BaseMixin):
    __tablename__ = "personas"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    global_style: Mapped[str] = mapped_column(Text, nullable=False)
    catchphrases: Mapped[dict | None] = mapped_column(JSON, default=list)
    reaction_patterns: Mapped[dict | None] = mapped_column(JSON, default=dict)
    sentence_templates: Mapped[dict | None] = mapped_column(JSON, default=list)
    core_values: Mapped[dict | None] = mapped_column(JSON, default=list)
    language_style: Mapped[dict | None] = mapped_column(JSON, default=dict)
    tone_adaptation: Mapped[dict | None] = mapped_column(JSON, default=dict)
    narrative_style: Mapped[dict | None] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    version_notes: Mapped[dict | None] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped["User | None"] = relationship(back_populates="personas")  # noqa: F821
    slices: Mapped[list["PersonaSlice"]] = relationship(  # noqa: F821
        back_populates="persona", cascade="all, delete-orphan"
    )
    script_projects: Mapped[list["ScriptProject"]] = relationship(back_populates="persona")  # noqa: F821

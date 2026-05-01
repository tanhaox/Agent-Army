from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class PersonaSlice(Base, BaseMixin):
    __tablename__ = "persona_slices"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

    persona: Mapped["Persona"] = relationship(back_populates="slices")  # noqa: F821

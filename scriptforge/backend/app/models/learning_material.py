from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class LearningMaterial(Base, BaseMixin):
    __tablename__ = "learning_materials"

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_strategies: Mapped[dict | None] = mapped_column(JSON, default=list)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    uploader: Mapped["User | None"] = relationship(back_populates="learning_materials")  # noqa: F821

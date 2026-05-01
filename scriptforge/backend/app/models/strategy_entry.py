from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class StrategyEntry(Base, BaseMixin):
    __tablename__ = "strategy_entries"

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    pattern_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emotional_curve: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sentence_templates: Mapped[dict | None] = mapped_column(JSON, default=list)
    tags: Mapped[dict | None] = mapped_column(JSON, default=list)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(Vector(512), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

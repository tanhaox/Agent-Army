import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin


class TaskRecord(Base, BaseMixin):
    __tablename__ = "task_records"

    task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    trigger: Mapped[str] = mapped_column(String(20), default="stream")
    url: Mapped[str] = mapped_column(String(1000), default="")
    anchor_name: Mapped[str] = mapped_column(String(200), default="")
    anchor_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), index=True, default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    downloaded_count: Mapped[int] = mapped_column(Integer, default=0)
    transcribed_count: Mapped[int] = mapped_column(Integer, default=0)
    persona_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    persona_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

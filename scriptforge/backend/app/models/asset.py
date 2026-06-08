import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Float, String, Text, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseMixin

import enum


class AssetType(str, enum.Enum):
    video = "video"
    audio = "audio"
    transcript = "transcript"


class Asset(Base, BaseMixin):
    __tablename__ = "assets"

    task_id: Mapped[str] = mapped_column(String(36), index=True)
    anchor_name: Mapped[str] = mapped_column(String(200), default="")
    video_title: Mapped[str] = mapped_column(String(500), default="")
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, name="asset_type_enum", create_type=False),
    )
    file_path: Mapped[str] = mapped_column(String(1000), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    transcription_text: Mapped[str | None] = mapped_column(Text, nullable=True)

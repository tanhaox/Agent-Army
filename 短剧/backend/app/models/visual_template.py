"""
视觉模板模型 - visual_templates 表。

系统预设模板（is_system=True）和用户自定义模板。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VisualTemplate(Base):
    """
    视觉模板表。

    Attributes:
        id: 模板 ID。
        name: 模板名称。
        description: 模板描述。
        settings: 完整视觉设定 JSON。
        is_system: 是否为系统内置模板。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "visual_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(), server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(), server_default=func.now(), onupdate=func.now(),
    )

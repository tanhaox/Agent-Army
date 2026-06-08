"""
API 配置数据模型 - api_configs 表。

存储各种外部服务的 API Key，加密保存。
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApiConfig(Base):
    """API 配置表。"""

    __tablename__ = "api_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    key_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="配置键名（如 ARK_API_KEY）",
    )
    encrypted_value: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="加密后的配置值",
    )
    display_name: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", comment="显示名称（如 火山引擎 API Key）",
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", comment="分类（llm / image / video / tts）",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<ApiConfig key={self.key_name}>"

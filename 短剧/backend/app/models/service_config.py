"""
服务商配置数据模型 - service_configs 表。

按服务商存储配置项，使用 JSONB 字段灵活存储各类参数。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ServiceConfig(Base):
    """服务商配置表。"""

    __tablename__ = "service_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="服务商标识（如 deepseek, volcano_ark）",
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="显示名称（如 DeepSeek, 火山引擎）",
    )
    configs: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}", comment="配置项 JSON",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ServiceConfig provider={self.provider}>"

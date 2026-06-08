"""
角色数据模型 - characters 表。

存储"数字演员"的角色卡、参考图路径、平台绑定等信息。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Character(Base):
    """
    角色表（数字演员）。

    Attributes:
        id: UUID 主键，自动生成。
        name: 角色名称。
        traits: 角色特征（性格、外貌、年龄等结构化描述）。
        reference_images: 参考图文件路径列表。
        voice_id: TTS 音色预留字段。
        platform_bindings: 各平台的角色绑定 ID。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="角色名称")
    traits: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        comment="角色特征描述",
    )
    reference_images: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
        comment="参考图路径列表",
    )
    voice_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="TTS 音色 ID",
    )
    base_image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, comment="基准图 URL（用于 img2img 参考）",
    )
    platform_bindings: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        comment="平台绑定 ID",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default=lambda: datetime.utcnow(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<Character id={self.id} name={self.name}>"

"""
剧本数据模型 - scripts 表。

使用 JSON 存储完整的剧本结构化内容。
PostgreSQL 下自动升级为 JSONB，SQLite 下使用 JSON。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func

from app.core.database import Base


class Script(Base):
    """
    剧本表。

    Attributes:
        id: UUID 主键，自动生成。
        project_name: 项目名称。
        theme: 剧本主题/创意描述。
        content: JSON/JSONB，存储完整的结构化剧本数据。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="项目名称")
    theme: Mapped[str] = mapped_column(Text, nullable=False, comment="剧本主题")
    project_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True, comment="关联项目 ID",
    )
    source_narrative_tree_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True, comment="源叙事树 ID",
    )
    source_outline_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True, comment="源概要 ID",
    )
    content: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        comment="结构化剧本内容",
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
        return f"<Script id={self.id} project={self.project_name}>"

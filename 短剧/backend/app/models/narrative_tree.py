"""
叙事树数据模型 - narrative_trees 表。

存储 AI 生成的叙事树（思维导图），支持用户选择分支后生成剧本。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NarrativeTree(Base):
    """
    叙事树表。

    Attributes:
        id: UUID 主键，自动生成。
        project_id: 关联项目 ID。
        user_theme: 用户输入的创意主题。
        tree_data: JSON/JSONB，存储完整叙事树结构。
        selected_branch_ids: JSON/JSONB，用户选中的节点 ID 列表。
        status: 状态 (draft / confirmed / converted)。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "narrative_trees"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="关联项目 ID",
    )
    user_theme: Mapped[str] = mapped_column(Text, nullable=False, comment="用户创意主题")
    tree_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        comment="叙事树结构",
    )
    selected_branch_ids: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        default=None,
        comment="用户选中的节点 ID 列表",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="状态: draft / confirmed / converted",
    )
    final_outline_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, comment="最终选中的概要 ID",
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
        return f"<NarrativeTree id={self.id} project={self.project_id} status={self.status}>"

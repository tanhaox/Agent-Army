"""
项目快照数据模型 - project_snapshots 表。

快照保存项目在某一时刻的剧本和分镜完整数据，用于版本回退和对比。
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectSnapshot(Base):
    """
    项目快照表。

    Attributes:
        id: UUID 主键。
        project_id: 关联项目 ID。
        snapshot_name: 快照名称（用户自定义或自动生成）。
        script_snapshot: 剧本完整内容快照（JSONB）。
        storyboards_snapshot: 分镜列表快照（JSONB）。
        metadata: 元数据（创建人、备注等）。
        created_at: 创建时间。
    """

    __tablename__ = "project_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="关联项目 ID",
    )
    snapshot_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="快照名称",
    )
    script_snapshot: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True, default=None, comment="剧本内容快照",
    )
    storyboards_snapshot: Mapped[list | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True, default=None, comment="分镜列表快照",
    )
    snapshot_meta: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True, default=None, comment="元数据",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<ProjectSnapshot id={self.id} name={self.snapshot_name}>"

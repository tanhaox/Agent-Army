"""
项目数据模型 - projects 表。

项目是短剧生产的顶层组织单位，关联剧本和分镜。
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Project(Base):
    """
    项目表。

    Attributes:
        id: UUID 主键，自动生成。
        name: 项目名称。
        description: 项目描述。
        current_script_id: 当前关联的剧本 ID。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="项目名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="项目描述")
    current_script_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, comment="当前关联剧本 ID",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active", comment="项目状态 (active/archived/completed)",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name}>"

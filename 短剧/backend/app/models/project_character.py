"""
项目-角色关联模型 - project_characters 表。

多对多关联：一个角色可以属于多个项目，一个项目可以有多个角色。
"""

import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectCharacter(Base):
    """
    项目-角色关联表。

    Attributes:
        project_id: 项目 ID（联合主键）。
        character_id: 角色 ID（联合主键）。
        role_name: 角色在剧中的名字。
        created_at: 创建时间。
    """

    __tablename__ = "project_characters"

    project_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, comment="项目 ID",
    )
    character_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, comment="角色 ID",
    )
    role_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="剧中角色名",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<ProjectCharacter project={self.project_id} character={self.character_id}>"

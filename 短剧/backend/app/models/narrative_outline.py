"""
叙事概要数据模型 - narrative_outlines 表。

存储从叙事树生成的剧情概要，每个叙事树可生成多个风格的概要。
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NarrativeOutline(Base):
    """
    叙事概要表。

    Attributes:
        id: UUID 主键。
        narrative_tree_id: 关联的叙事树 ID。
        style: 风格标签（虐心催泪、甜宠搞笑等）。
        outline_text: 剧情概要文本。
        version_label: 版本标识（A/B/C）。
        storyline: 从叙事树提取的主线描述。
        created_at: 创建时间。
    """

    __tablename__ = "narrative_outlines"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    narrative_tree_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="关联叙事树 ID",
    )
    style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="风格标签",
    )
    outline_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="剧情概要内容",
    )
    version_label: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="版本标识 (A/B/C)",
    )
    storyline: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="主线描述",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<NarrativeOutline id={self.id} style={self.style}>"

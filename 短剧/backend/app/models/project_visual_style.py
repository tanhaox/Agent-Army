"""
项目视觉风格模型 - project_visual_styles 表。

每个项目一条记录，存储风格锚点，确保生图和生视频的视觉一致性。
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectVisualStyle(Base):
    """项目视觉风格配置。"""

    __tablename__ = "project_visual_styles"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True,
        comment="关联项目 ID",
    )
    style_reference_image: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, comment="风格参考图 URL",
    )
    color_palette: Mapped[dict | None] = mapped_column(
        Text().with_variant(JSONB, "postgresql"), nullable=True, default=None,
        comment="主色调 JSON 数组",
    )
    lighting_rule: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None, comment="光照规则",
    )
    camera_style: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="运镜风格",
    )
    art_style: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None, comment="艺术风格",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<ProjectVisualStyle project={self.project_id}>"

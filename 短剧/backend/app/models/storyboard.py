"""
分镜数据模型 - storyboards 表。

存储分镜卡信息，包括镜头参数、动作描述、AI 生成的视频提示词等。
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 景别选项
SHOT_TYPES = ("远景", "全景", "中景", "近景", "特写")

# 运镜选项
CAMERA_MOVES = ("固定", "推", "拉", "摇", "移", "跟")

# 特效选项
VFX_OPTIONS = ("无", "光效", "粒子特效", "镜头特效", "色彩滤镜", "动态模糊", "转场特效")


class Storyboard(Base):
    """
    分镜表。

    Attributes:
        id: UUID 主键，自动生成。
        script_id: 关联剧本 ID（允许 NULL，第一期不强制外键）。
        episode_no: 集数。
        shot_no: 镜头序号。
        shot_type: 景别（远景/全景/中景/近景/特写）。
        camera_move: 运镜方式（固定/推/拉/摇/移/跟）。
        action: 角色动作描述。
        dialogue: 对话内容。
        emotion: 情绪标签。
        environment: 环境/背景描述。
        lighting: 光线描述。
        prompt_text: AI 生成的英文视频提示词。
        reference_image_url: 参考图 URL。
        approved: 是否定稿。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "storyboards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, comment="关联剧本 ID",
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True, comment="关联项目 ID",
    )
    episode_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="集数")
    shot_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="镜头序号")
    shot_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="景别")
    camera_move: Mapped[str] = mapped_column(String(20), nullable=False, comment="运镜方式")
    action: Mapped[str] = mapped_column(Text, nullable=False, comment="角色动作描述")
    dialogue: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="对话内容")
    emotion: Mapped[str] = mapped_column(String(50), nullable=False, comment="情绪标签")
    environment: Mapped[str] = mapped_column(Text, nullable=False, comment="环境/背景描述")
    lighting: Mapped[str] = mapped_column(Text, nullable=False, comment="光线描述")
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="英文视频提示词")
    vfx: Mapped[str | None] = mapped_column(Text, nullable=True, default="无", comment="特效描述")
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="负面提示词")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5", comment="镜头预估时长(秒)")
    is_key_moment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", comment="是否关键镜头")
    reference_image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, comment="参考图 URL",
    )
    approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否定稿",
    )
    pregen_materials: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="预生成素材URL",
    )
    video_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, comment="生成后的视频URL",
    )
    video_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending",
        comment="pending/generating/success/failed",
    )
    video_task_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="关联视频任务ID",
    )
    audio_config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="音效配置",
    )
    director_analysis: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=None, comment="智能导演分析结果",
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
        return f"<Storyboard id={self.id} ep={self.episode_no} shot={self.shot_no}>"

"""
视频任务数据模型 - video_tasks 表。

跟踪视频生成任务的状态、参数和结果（支持 Seedance 2.0 / Kling AI）。
"""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 任务状态枚举
TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_SUCCESS = "success"
TASK_STATUS_FAILED = "failed"


class VideoTask(Base):
    """
    视频生成任务表。

    Attributes:
        id: UUID 主键，自动生成。
        storyboard_id: 关联分镜 ID。
        provider_task_id: 视频生成后端返回的任务 ID（Seedance/Kling）。
        status: 任务状态 (pending/processing/success/failed)。
        prompt: 视频生成提示词。
        negative_prompt: 负面提示词。
        mode: 生成模式 (std/pro)。
        duration: 视频时长（秒）。
        aspect_ratio: 画面比例。
        image_urls: 参考图片 URL 列表（JSON 数组，Seedance 多模态）。
        video_url: 生成完成的视频 URL。
        error_message: 失败时的错误信息。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "video_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    storyboard_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="关联分镜 ID",
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None, index=True, comment="关联项目 ID",
    )
    provider_task_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="视频后端任务 ID",
    )
    # 兼容旧字段名
    kling_task_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, comment="Kling API 任务 ID（已弃用，用 provider_task_id）",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TASK_STATUS_PENDING, comment="任务状态",
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False, comment="视频提示词")
    negative_prompt: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="负面提示词",
    )
    mode: Mapped[str] = mapped_column(
        String(10), nullable=False, default="std", comment="生成模式 (std/pro)",
    )
    duration: Mapped[str] = mapped_column(
        String(10), nullable=False, default="5", comment="视频时长",
    )
    aspect_ratio: Mapped[str] = mapped_column(
        String(10), nullable=False, default="9:16", comment="画面比例",
    )
    image_urls: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="参考图片 URL JSON 数组",
    )
    video_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, default=None, comment="生成完成的视频 URL",
    )
    output_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, default=None, comment="输出 URL（兼容字段）",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="错误信息",
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
        return f"<VideoTask id={self.id} status={self.status}>"

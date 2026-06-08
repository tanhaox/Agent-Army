"""
视频任务相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VideoGenerateRequest(BaseModel):
    """视频生成请求体。"""

    storyboard_id: str = Field(..., description="关联分镜 ID")
    prompt: str = Field(..., min_length=1, max_length=5000, description="视频提示词")
    mode: str = Field(default="std", description="生成模式: std/pro")
    duration: str = Field(default="5", description="视频时长: 5 或 10 秒")
    aspect_ratio: str = Field(default="16:9", description="画面比例: 16:9, 9:16 等")
    project_id: Optional[str] = Field(default=None, description="关联项目 ID")


class VideoTaskResponse(BaseModel):
    """视频任务响应体。"""

    id: UUID
    storyboard_id: str
    project_id: Optional[str] = None
    kling_task_id: Optional[str] = None
    status: str
    prompt: str
    mode: str
    duration: str
    aspect_ratio: str
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

"""
分镜相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.storyboard import CAMERA_MOVES, SHOT_TYPES, VFX_OPTIONS


class StoryboardCreate(BaseModel):
    """创建分镜请求体。"""

    script_id: Optional[str] = Field(default=None, description="关联剧本 ID")
    project_id: Optional[str] = Field(default=None, description="关联项目 ID")
    episode_no: int = Field(..., ge=1, description="集数")
    shot_no: int = Field(..., ge=1, description="镜头序号")
    shot_type: str = Field(..., description=f"景别：{'/'.join(SHOT_TYPES)}")
    camera_move: str = Field(..., description=f"运镜：{'/'.join(CAMERA_MOVES)}")
    action: str = Field(..., min_length=1, max_length=2000, description="角色动作描述")
    dialogue: Optional[str] = Field(default=None, max_length=2000, description="对话内容")
    emotion: str = Field(..., min_length=1, max_length=50, description="情绪标签")
    environment: str = Field(..., min_length=1, max_length=2000, description="环境/背景描述")
    lighting: str = Field(..., min_length=1, max_length=500, description="光线描述")
    prompt_text: Optional[str] = Field(default=None, max_length=5000, description="英文视频提示词")
    vfx: str = Field(default="无", max_length=500, description=f"特效：{'/'.join(VFX_OPTIONS)}")
    negative_prompt: Optional[str] = Field(default=None, max_length=5000, description="负面提示词")
    reference_image_url: Optional[str] = Field(default=None, max_length=500, description="参考图 URL")
    duration_seconds: int = Field(default=5, ge=1, le=30, description="镜头预估时长(秒)")
    is_key_moment: bool = Field(default=False, description="是否关键镜头")


class StoryboardUpdate(BaseModel):
    """更新分镜请求体（所有字段可选）。"""

    script_id: Optional[str] = None
    episode_no: Optional[int] = Field(default=None, ge=1)
    shot_no: Optional[int] = Field(default=None, ge=1)
    shot_type: Optional[str] = None
    camera_move: Optional[str] = None
    action: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    dialogue: Optional[str] = Field(default=None, max_length=2000)
    emotion: Optional[str] = Field(default=None, min_length=1, max_length=50)
    environment: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    lighting: Optional[str] = Field(default=None, min_length=1, max_length=500)
    prompt_text: Optional[str] = Field(default=None, max_length=5000)
    vfx: Optional[str] = Field(default=None, max_length=500)
    negative_prompt: Optional[str] = Field(default=None, max_length=5000)
    reference_image_url: Optional[str] = Field(default=None, max_length=500)
    approved: Optional[bool] = None
    duration_seconds: Optional[int] = Field(default=None, ge=1, le=30)
    is_key_moment: Optional[bool] = None
    pregen_materials: Optional[dict[str, Any]] = None
    video_url: Optional[str] = None
    video_status: Optional[str] = None
    video_task_id: Optional[str] = None
    audio_config: Optional[dict[str, Any]] = None


class StoryboardResponse(BaseModel):
    """分镜响应体。"""

    id: UUID
    script_id: Optional[str]
    project_id: Optional[str] = None
    episode_no: int
    shot_no: int
    shot_type: str
    camera_move: str
    action: str
    dialogue: Optional[str]
    emotion: str
    environment: str
    lighting: str
    prompt_text: Optional[str]
    vfx: Optional[str] = "无"
    negative_prompt: Optional[str] = None
    reference_image_url: Optional[str]
    approved: bool
    duration_seconds: int = 5
    is_key_moment: bool = False
    pregen_materials: Optional[dict[str, Any]] = None
    video_url: Optional[str] = None
    video_status: str = "pending"
    video_task_id: Optional[str] = None
    audio_config: Optional[dict[str, Any]] = None
    director_analysis: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptGenerateRequest(BaseModel):
    """生成视频提示词请求体。"""

    shot_type: str = Field(..., min_length=1, description="景别")
    camera_move: str = Field(..., min_length=1, description="运镜方式")
    action: str = Field(..., min_length=1, max_length=2000, description="角色动作描述")
    emotion: str = Field(..., min_length=1, max_length=50, description="情绪标签")
    environment: str = Field(..., min_length=1, max_length=2000, description="环境/背景描述")
    lighting: str = Field(..., min_length=1, max_length=500, description="光线描述")
    vfx: str = Field(default="无", max_length=500, description="特效描述")

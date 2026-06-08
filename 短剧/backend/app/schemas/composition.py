"""
合成任务 Pydantic 模型（请求/响应 Schema）。
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class CompositionRequest(BaseModel):
    """合成请求体。"""

    script_id: Optional[str] = Field(default=None, description="剧本 ID")
    project_id: Optional[str] = Field(default=None, description="关联项目 ID")
    episode_no: int = Field(..., ge=1, description="集数")
    storyboard_ids: list[str] = Field(..., min_length=1, description="要合成的分镜 ID 列表")


class CompositionResponse(BaseModel):
    """合成任务响应体。"""

    id: str
    script_id: Optional[str] = None
    episode_no: int
    status: str
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    progress: Optional[str] = None

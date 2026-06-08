"""
剧本相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateScriptFromOutlineRequest(BaseModel):
    """从剧情概要生成剧本请求体。"""

    outline_text: str = Field(
        ..., min_length=10, max_length=2000,
        description="剧情概要（200-300字）",
    )
    style: str = Field(
        ..., min_length=1, max_length=50,
        description="风格标签（如虐心催泪、甜宠搞笑）",
    )
    project_id: str = Field(..., description="关联项目 ID")
    source_narrative_tree_id: str | None = Field(
        None, description="源叙事树 ID",
    )
    source_outline_id: str | None = Field(
        None, description="源概要 ID",
    )


class ScriptResponse(BaseModel):
    """剧本列表项（不含完整 content）。"""

    id: UUID
    project_name: str
    theme: str
    project_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScriptDetailResponse(BaseModel):
    """剧本详情（含完整 content）。"""

    id: UUID
    project_name: str
    theme: str
    project_id: Optional[str] = None
    content: dict[str, Any] = Field(description="完整结构化剧本数据")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptUpdateRequest(BaseModel):
    """更新剧本请求体。"""

    content: dict[str, Any] = Field(description="完整的剧本 content JSON")

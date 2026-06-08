"""
项目与快照相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- 项目 ---

class ProjectCreate(BaseModel):
    """创建项目请求体。"""

    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: Optional[str] = Field(default=None, max_length=2000, description="项目描述")


class ProjectUpdate(BaseModel):
    """更新项目请求体。"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    current_script_id: Optional[str] = None
    status: Optional[str] = Field(default=None, description="项目状态: active/archived/completed")


class ProjectResponse(BaseModel):
    """项目响应体。"""

    id: UUID
    name: str
    description: Optional[str] = None
    current_script_id: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDashboardResponse(BaseModel):
    """项目仪表盘响应体。"""

    project: ProjectResponse
    script_count: int = 0
    storyboard_count: int = 0
    character_count: int = 0
    video_task_count: int = 0
    recent_scripts: list[dict[str, Any]] = []
    recent_video_tasks: list[dict[str, Any]] = []


# --- 快照 ---

class SnapshotCreateRequest(BaseModel):
    """创建快照请求体。"""

    snapshot_name: Optional[str] = Field(default=None, max_length=200, description="快照名称（可选，默认自动生成）")
    remark: Optional[str] = Field(default=None, max_length=1000, description="备注")


class SnapshotBriefResponse(BaseModel):
    """快照简要信息（列表用）。"""

    id: UUID
    project_id: UUID
    snapshot_name: str
    created_at: datetime
    snapshot_meta: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class SnapshotDetailResponse(BaseModel):
    """快照详情（含完整数据）。"""

    id: UUID
    project_id: UUID
    snapshot_name: str
    script_snapshot: Optional[dict[str, Any]] = None
    storyboards_snapshot: Optional[list[dict[str, Any]]] = None
    snapshot_meta: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- 对比 ---

class CompareRequest(BaseModel):
    """快照对比请求体。"""

    snapshot_id_1: str = Field(..., description="快照 1 ID")
    snapshot_id_2: str = Field(..., description="快照 2 ID")


class CompareResponse(BaseModel):
    """快照对比结果。"""

    snapshot_1_name: str
    snapshot_2_name: str
    script_diff: dict[str, Any]
    storyboards_diff: dict[str, Any]


# --- 项目角色关联 ---


class GenerateStoryboardsRequest(BaseModel):
    """AI 生成分镜请求体。"""

    regenerate: bool = Field(default=False, description="是否重新生成（删除已有分镜）")


class GenerateStoryboardsResponse(BaseModel):
    """AI 生成分镜响应体。"""

    generated_count: int = Field(description="生成的分镜数量")
    storyboards: list[dict[str, Any]] = Field(default_factory=list, description="生成的分镜列表")


class ProjectCharacterRequest(BaseModel):
    """添加角色到项目请求体。"""

    character_id: str = Field(..., description="角色 ID")
    role_name: Optional[str] = Field(default=None, max_length=100, description="剧中角色名")


class ProjectCharacterResponse(BaseModel):
    """项目角色关联响应体。"""

    character_id: UUID
    character_name: str
    role_name: Optional[str] = None
    traits: dict[str, Any] = {}
    reference_images: list[str | dict[str, Any]] = []
    created_at: datetime

    model_config = {"from_attributes": True}

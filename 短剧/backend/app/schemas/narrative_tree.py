"""
叙事树相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class GenerateNarrativeTreeRequest(BaseModel):
    """生成叙事树请求体。"""

    theme: str = Field(..., min_length=2, max_length=500, description="创意主题")
    max_breadth: int = Field(default=3, ge=2, le=5, description="每层最大分支数")
    max_depth: int = Field(default=2, ge=1, le=3, description="最大深度")


class NarrativeTreeResponse(BaseModel):
    """叙事树响应体。"""

    id: str
    project_id: str
    user_theme: str
    tree_data: dict[str, Any]
    selected_branch_ids: list[str] | None = None
    status: str = "draft"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfirmBranchesRequest(BaseModel):
    """确认分支请求体。"""

    selected_branch_ids: list[str] = Field(..., min_length=1, description="用户选中的节点 ID 列表")


class GenerateScriptFromTreeRequest(BaseModel):
    """从叙事树生成剧本请求体。"""

    selected_branch_ids: list[str] = Field(
        ..., min_length=1,
        description="用户选中的节点 ID 列表，按深度顺序构成一条路径",
    )


class NarrativeTreeNodeBrief(BaseModel):
    """叙事树节点简要信息。"""

    id: str
    text: str
    tags: list[str] = []


class GenerateOutlinesRequest(BaseModel):
    """生成多版本剧情概要请求体。"""

    selected_branch_ids: list[str] = Field(
        ..., min_length=1,
        description="用户选中的节点 ID 列表，按深度顺序构成一条路径",
    )
    styles: list[str] | None = Field(
        default=None,
        description="风格列表，默认为虐心催泪/甜宠搞笑/强反转爽文",
    )


class ExpandNodeRequest(BaseModel):
    """扩展节点请求体。"""

    node_id: str = Field(..., description="要扩展的节点 ID")
    count: int = Field(default=3, ge=1, le=5, description="要生成的新分支数量")


class OutlineItem(BaseModel):
    """单个风格的剧情概要。"""

    id: str | None = Field(None, description="概要 ID（生成后返回）")
    style: str = Field(description="风格名称")
    text: str = Field(description="剧情概要文本")
    version: str = Field(description="版本标识（A/B/C）")


class NarrativeOutlineResponse(BaseModel):
    """叙事概要响应体（持久化记录）。"""

    id: str
    narrative_tree_id: str
    style: str
    outline_text: str
    version_label: str
    storyline: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateOutlinesResponse(BaseModel):
    """多版本剧情概要响应体。"""

    outlines: list[OutlineItem] = Field(description="生成的概要列表")
    storyline: str = Field(description="从叙事树提取的主线描述")

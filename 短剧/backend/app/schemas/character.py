"""
角色相关 Pydantic 模型（请求/响应 Schema）。
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    """创建角色请求体。"""

    name: str = Field(..., min_length=1, max_length=200, description="角色名称")
    traits: dict[str, Any] = Field(
        default_factory=dict,
        description="角色特征（性格、外貌、年龄等）",
        examples=[{"age": 25, "personality": "外冷内热", "appearance": "短发、黑眸"}],
    )
    voice_id: Optional[str] = Field(default=None, max_length=100, description="TTS 音色 ID")
    platform_bindings: dict[str, Any] = Field(
        default_factory=dict,
        description="平台绑定 ID",
    )


class CharacterUpdate(BaseModel):
    """更新角色请求体（所有字段可选）。"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    traits: Optional[dict[str, Any]] = None
    voice_id: Optional[str] = None
    base_image_url: Optional[str] = None
    platform_bindings: Optional[dict[str, Any]] = None


class GenerateCandidatesRequest(BaseModel):
    """生成候选照请求体。"""

    count: int = Field(default=4, ge=1, le=8, description="生成数量（1-8）")
    prompt_hint: Optional[str] = Field(default=None, description="可选的提示词补充")


class SetBaseImageRequest(BaseModel):
    """设置基准图请求体。"""

    image_url: str = Field(..., description="基准图 URL")


class GenerateAnglesRequest(BaseModel):
    """生成多角度请求体。"""

    angles: Optional[list[str]] = Field(
        default=None,
        description="角度列表，默认为 ['left_side', 'right_side', 'back', 'closeup_face']",
    )


class GenerateImageRequest(BaseModel):
    """AI 生成参考图请求体。"""

    angle: str = Field(
        default="front",
        description="拍摄角度：front（正面）/ three_quarter（3/4侧面）/ side（侧面）",
    )


class VisualSettings(BaseModel):
    """视觉基调设定。"""

    art_style: str = Field(default="anime", description="画风")
    era: str = Field(default="modern", description="时代")
    environment: str = Field(default="都市", description="环境氛围")
    color_palette: str = Field(default="暖色调", description="色调倾向")
    visual_style_suffix: str = Field(
        default="动漫风格，鲜艳色彩，精细渲染，4K",
        description="风格后缀，追加到每个角色 image_prompt 末尾",
    )


class GenerateCharactersRequest(BaseModel):
    """从剧本生成角色请求体。"""

    visual_settings: VisualSettings | None = Field(
        default=None,
        description="视觉基调设定（不提供则自动推断）",
    )


class GeneratedCharacterResponse(BaseModel):
    """生成的角色响应项。"""

    id: str
    name: str
    traits: dict[str, Any]
    image_prompt: str


class CharacterResponse(BaseModel):

    id: UUID
    name: str
    traits: dict[str, Any]
    reference_images: list[str | dict[str, Any]]
    voice_id: Optional[str]
    base_image_url: Optional[str] = None
    platform_bindings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

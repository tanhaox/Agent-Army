# -*- coding: utf-8 -*-
"""Pydantic schemas for API requests/responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class ArticleCreate(BaseModel):
    title: str | None = None
    source_url: str | None = None
    raw_text: str = Field(..., min_length=1, max_length=15000)


class RewriteRequest(BaseModel):
    model: Literal["flash", "pro"] | None = None
    prompt_template: str | None = None
    video_format: str | None = None  # portrait / landscape / square
    perspective: str | None = Field(default=None, max_length=500, description="洗稿前的补充观点（可选）")


class CorrectRequest(BaseModel):
    """洗稿后的修正观点请求."""
    perspective: str = Field(..., min_length=1, max_length=500, description="修正观点")
    model: Literal["flash", "pro"] | None = None



class FetchUrlRequest(BaseModel):
    url: str = Field(..., min_length=5)


class FetchUrlResponse(BaseModel):
    ok: bool
    title: str | None = None
    source_url: str | None = None
    raw_text: str | None = None
    error: str | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    source_url: str | None = None
    raw_text: str | None = Field(default=None, min_length=1, max_length=15000)


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    source_url: str | None
    status: str
    perspective_1: str | None = None
    created_at: datetime
    updated_at: datetime


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    line_index: int
    text: str
    control_chars: dict[str, Any] | None
    segment_type: str | None
    selected_for_host: bool
    host_order: int
    estimated_duration: float | None


class ArticleBriefOut(BaseModel):
    """文章精简输出（仅 id + title）."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    article_id: str
    host_id: str | None
    version: int
    script_text: str
    project_dir: str | None
    video_format: str = "portrait"
    perspective_2: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentOut]
    article: ArticleBriefOut | None = None
    title: str | None = None

    @model_validator(mode="after")
    def _derive_title(self) -> Self:
        if self.article is not None:
            self.title = self.article.title
        return self


class ScriptUpdate(BaseModel):
    script_text: str | None = Field(default=None, min_length=1)
    status: str | None = None
    project_dir: str | None = None
    video_format: str | None = None


class SegmentUpdate(BaseModel):
    text: str | None = None
    selected_for_host: bool | None = None
    host_order: int | None = None
    segment_type: str | None = None


class AudioJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_id: str
    voice_id: str | None
    output_dir: str
    status: str
    total_segments: int
    completed_segments: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class AudioFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    segment_id: str | None
    filename: str
    file_path: str
    duration: float | None
    sample_rate: int | None


class HostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    persona_key: str
    default_voice_id: str | None


class VoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    host_id: str | None
    name: str
    backend: str
    reference_audio_path: str | None
    reference_text: str | None
    base_url_fish: str | None
    base_url_f5: str | None
    master_audio_path: str | None
    master_text: str | None
    base_url_indextts: str | None
    config_json: dict[str, Any] | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def params(self) -> dict[str, Any] | None:
        if self.config_json and isinstance(self.config_json, dict):
            return self.config_json.get("params")
        return None


class VoiceCreate(BaseModel):
    host_id: str | None = None
    name: str = Field(..., min_length=1, max_length=128)
    backend: str = Field(default="fish", pattern=r"^(fish|f5|elevenlabs|indextts)$")
    reference_audio_path: str | None = None
    reference_text: str | None = None
    base_url_fish: str | None = None
    base_url_f5: str | None = None
    master_audio_path: str | None = None
    master_text: str | None = None
    base_url_indextts: str | None = None
    config_json: dict[str, Any] | None = None
    params: VoiceParams | None = None


class VoiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    backend: str | None = Field(default=None, pattern=r"^(fish|f5|elevenlabs|indextts)$")
    reference_audio_path: str | None = None
    reference_text: str | None = None
    base_url_fish: str | None = None
    base_url_f5: str | None = None
    master_audio_path: str | None = None
    master_text: str | None = None
    base_url_indextts: str | None = None
    config_json: dict[str, Any] | None = None
    params: VoiceParams | None = None


class VoiceParams(BaseModel):
    """Voice synthesis parameters: FFmpeg effects + TTS engine overrides."""

    # FFmpeg post-processing (all backends)
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速 (0.5–2.0)")
    pitch: float = Field(default=0, ge=-12, le=12, description="语调/音高偏移 (半音, -12–+12, 步进0.5)")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="音量增益 (0.0–2.0)")

    # Timbre / EQ shaping (all backends) — 真正的音色维度
    bass_gain: float = Field(default=0, ge=-24, le=24, description="低频厚度 (dB, -24–+24)")
    presence_gain: float = Field(default=0, ge=-24, le=24, description="临场感/中频 (dB, -24–+24)")
    air_gain: float = Field(default=0, ge=-24, le=24, description="高频通透 (dB, -24–+24)")

    # Fish Speech engine parameters (fish backend only)
    temperature: float | None = Field(default=None, ge=0.1, le=1.5, description="TTS 温度 (0.1–1.5)")
    top_p: float | None = Field(default=None, ge=0.1, le=1.0, description="TTS top_p (0.1–1.0)")
    repetition_penalty: float | None = Field(
        default=None, ge=1.0, le=2.0, description="TTS 重复惩罚 (1.0–2.0)"
    )
    seed: int | None = Field(
        default=None, ge=0, le=2147483647, description="TTS 随机种子 (None=随机, 固定数字=确定输出)"
    )

    # Quick preset (auto-fills the above fields when set)
    preset: str | None = Field(
        default=None,
        pattern=r"^(default|male|female|deep_male|loli|fast)$",
        description="快捷预设: default/male/female/deep_male/loli/fast",
    )

    # IndexTTS2 engine parameters (indextts backend only)
    master_style: str | None = Field(
        default=None,
        pattern=r"^(calm|excited|relaxed)$",
        description="IndexTTS2 主音色风格 (calm/excited/relaxed)",
    )
    do_sample: bool | None = Field(default=None, description="IndexTTS2 是否采样 (None=服务器默认 True)")
    top_p: float | None = Field(default=None, ge=0.1, le=1.0, description="IndexTTS2 top_p")
    top_k: int | None = Field(default=None, ge=1, le=100, description="IndexTTS2 top_k")
    temperature: float | None = Field(default=None, ge=0.1, le=1.5, description="IndexTTS2 温度")
    max_text_tokens_per_segment: int | None = Field(
        default=None, ge=20, le=600, description="IndexTTS2 单段最大 token 数"
    )


class VoiceTestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    params: VoiceParams | None = None


class VoiceCarnivalRequest(BaseModel):
    """疯狂抽卡: 生成 N 个版本供用户挑选"""

    text: str = Field(..., min_length=1, max_length=500)
    params: VoiceParams | None = None
    count: int = Field(default=5, ge=3, le=20, description="生成个数 (3-20)")


class VoiceSetReferenceRequest(BaseModel):
    """将某段音频及其文本设为音色的固定参考音锚点"""

    audio_path: str = Field(
        ..., min_length=1, max_length=1024, description="选定音频的文件路径 (绝对路径)"
    )
    audio_text: str = Field(
        ..., min_length=1, max_length=500, description="该音频对应的准确文本"
    )


# ---------------------------------------------------------------------------
# ComfyUI / Role schemas (角色一致性 / 多视图定型)
# ---------------------------------------------------------------------------
class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    reference_image: str
    description: str | None
    view_groups: list[dict[str, Any]] = []
    views: dict[str, Any]
    workflow_used: str
    seed: int | None
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    reference_image: str = Field(..., min_length=1, max_length=512, description="参考图绝对路径")
    description: str = Field(default="", max_length=1000)
    workflow_used: str = Field(default="character_three_view", max_length=64)
    seed: int | None = Field(default=None, ge=0, le=2147483647)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    seed: int | None = Field(default=None, ge=0, le=2147483647)


class GenerateViewsRequest(BaseModel):
    """角色多视图生成请求 — 提交 ComfyUI workflow"""

    seed: int | None = Field(default=None, ge=0, le=2147483647)
    description_override: str | None = Field(
        default=None, max_length=1000, description="覆盖角色描述(留空使用角色自身 description)"
    )
    reference_image: str | None = Field(
        default=None, max_length=512, description="覆盖参考图路径(留空使用角色自身 reference_image)"
    )


class GenerateViewsResponse(BaseModel):
    """角色多视图生成响应"""

    role_id: str
    prompt_id: str | None
    status: str  # submitted / running / completed / failed
    views: dict[str, str]
    error: str | None = None


class ApplyRoleResponse(BaseModel):
    """角色应用到主流水线 — 当前仅返回入参结构(留接口位)"""

    applied: bool
    role_id: str
    mainstream_input: dict[str, Any]
    note: str


class WorkflowSyncOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_name: str
    source_sha256: str | None
    runtime_sha256: str | None
    synced: bool
    reason: str
    synced_at: datetime


class ComfyUIWorkflowInfo(BaseModel):
    """manifest.yaml 中的 workflow 元数据"""

    name: str
    source: str
    runtime_path: str
    auto_sync: bool
    description: str | None = None
    output_count: int | None = None
    output_view_order: list[str] | None = None


class ComfyUISubmitRequest(BaseModel):
    """通用 workflow 提交(测试 / 调试用)"""

    workflow_name: str = Field(default="character_three_view", max_length=64)
    inputs: dict[str, Any] = Field(default_factory=dict, description="要注入的 inputs 字典")
    role_id: str | None = Field(default=None, description="可选:产物落盘目标角色目录")


class ComfyUISubmitResponse(BaseModel):
    prompt_id: str | None
    status: str
    views: dict[str, str] = Field(default_factory=dict)
    elapsed_sec: float | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# DigitalHumanVideo schemas (LTX23 音频→视频)
# ---------------------------------------------------------------------------
class StoryboardItem(BaseModel):
    """单张分镜图输入 — 与 lt_video_builder.LTXVAddGuide 节点 1:1 映射."""

    filename: str = Field(..., description="ComfyUI 上传后的 image filename")
    frame_idx: int = Field(default=0, ge=0, description="该图锚定的帧下标")
    strength: float = Field(default=0.85, ge=0.0, le=1.0, description="条件强度 0-1")


class DigitalHumanVideoCreate(BaseModel):
    """创建 DigitalHumanVideo 行 (status=pending)."""

    role_id: str | None = Field(default=None, max_length=36)
    audio_source_paths: list[str] = Field(
        default_factory=list,
        description="从 /api/audio 已生成的 wav 路径列表 (绝对路径)",
    )
    storyboard_prompts: list[str] = Field(default_factory=list, max_length=20)
    target_duration_sec: float = Field(default=10.0, ge=5.0, le=60.0)
    fps: int = Field(default=24, ge=12, le=60)
    width: int = Field(default=576, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    seed: int | None = Field(default=None, ge=0, le=2147483647)


class DigitalHumanVideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role_id: str | None
    workflow_name: str
    audio_source_paths: list[str]
    aggregated_audio_path: str | None
    aggregated_duration_sec: float | None
    storyboard_paths: list[str]
    storyboard_prompts: list[str]
    target_duration_sec: float
    fps: int
    width: int
    height: int
    seed: int | None
    status: str
    prompt_id: str | None
    output_video_path: str | None
    duration_actual: float | None
    fps_actual: float | None
    has_audio_stream: bool
    frame_count: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class EligibleAudioItem(BaseModel):
    """可聚合的音频候选 — /api/audio 已生成的 wav."""

    label: str
    path: str
    duration_sec: float | None
    sample_rate: int | None
    source_job_id: str | None
    source_segment_id: str | None


class EligibleAudioResponse(BaseModel):
    items: list[EligibleAudioItem]
    total_duration_sec: float


class StoryboardUploadResponse(BaseModel):
    video_id: str
    uploaded_paths: list[str]
    storyboard_prompts: list[str]


class GenerateVideoResponse(BaseModel):
    """生成完成响应 — 含 ffprobe 验证结果."""

    video_id: str
    status: str
    prompt_id: str | None
    output_video_path: str | None
    aggregated_audio_path: str | None
    aggregated_duration_sec: float | None
    duration_actual: float | None
    fps_actual: float | None
    has_audio_stream: bool
    frame_count: int | None
    validation_issues: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    elapsed_sec: float | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Director 2.0 schemas
# ---------------------------------------------------------------------------
class DirectorSlotPlan(BaseModel):
    """导演 Agent 输出的单个 slot 计划(落 plan_json 前 schema 校验)."""

    slot_index: int = Field(..., ge=0)
    start_sec: float = Field(..., ge=0)
    end_sec: float = Field(..., ge=0)
    duration_sec: float | None = None
    text_context: str | None = None
    segment_id: str | None = None
    visual_type: Literal[
        "host",
        "broll_pexels",
        "broll_local",
        "hf_chart",
        "hf_title",
        "mixed_host_broll",
    ]
    workflow: Literal[
        "host",
        "broll_pexels",
        "broll_local",
        "hf_chart",
        "hf_title",
        "mixed_host_broll",
    ]
    params: dict[str, Any] = Field(default_factory=dict)
    camera_angle: int = Field(default=1, ge=1, le=4)
    view_group_index: int = Field(default=0, ge=0)


class DirectorPlan(BaseModel):
    """导演 Agent 输出的完整工序单."""

    slots: list[DirectorSlotPlan]
    title: str | None = None
    reasoning: str | None = None


class DirectorJobCreate(BaseModel):
    """手动创建导演任务(通常由 /scripts/{id}/direct 自动创建)."""

    script_id: str
    audio_file_id: str | None = None
    view_group_index: int = 0
    pipelines: str | None = None  # 逗号分隔启用的管线, e.g. "c,h". 默认全开.


class DirectorSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    director_job_id: str
    slot_index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    text_context: str | None
    segment_id: str | None
    visual_type: str
    workflow: str
    params_json: dict[str, Any]
    camera_angle: int = 1
    view_group_index: int = 0
    status: str
    output_path: str | None
    error_code: str | None
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class DirectorJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_id: str
    audio_file_id: str | None
    title: str | None = None
    video_format: str = "portrait"
    pipelines: str | None = None
    view_group_index: int = 0
    status: str
    plan_json: dict[str, Any]
    total_duration_sec: float | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    slots: list[DirectorSlotOut] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed")


class DirectorDirectResponse(BaseModel):
    job_id: str
    status: str
    slot_count: int
    message: str


class RetrySlotResponse(BaseModel):
    slot_id: str
    status: str
    message: str


class ComposeResponse(BaseModel):
    job_id: str
    status: str
    output_path: str | None = None
    duration_sec: float | None = None
    message: str


# ── Visual render (HF) ──────────────────────────────────────────────────

class VisualRenderJobCreate(BaseModel):
    """Body for ``POST /api/visual-render/jobs``.

    ``input_data`` is validated server-side against the template's jsonschema.
    """
    template_id: str = Field(default="news-data-v1", min_length=1, max_length=64)
    input_data: dict[str, Any]


class VisualRenderJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    template_version: str
    composition_id: str
    status: str
    input_path: str | None = None
    output_path: str | None = None
    manifest_path: str | None = None
    preview_frames: dict[str, str] = Field(default_factory=dict)
    media: dict[str, Any] = Field(default_factory=dict)
    warnings: list[Any] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    render_seconds: float | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @computed_field  # type: ignore[misc]
    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")


class TemplateInfo(BaseModel):
    template_id: str
    version: str
    composition_id: str
    duration_sec_range: list[int]
    required_input: list[str]
    json_schema: dict[str, Any]


class GenerateVisualResponse(BaseModel):
    job_id: str
    status: str
    output_path: str | None = None
    manifest_path: str | None = None
    media: dict[str, Any] = Field(default_factory=dict)
    render_seconds: float | None = None
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Video asset library schemas (素材库多维标签体系)
# ---------------------------------------------------------------------------

VIDEO_ORIENTATION_CHOICES = ("landscape", "portrait")
VIDEO_SOURCE_TYPE_CHOICES = ("footage", "creative")
VIDEO_LOCATION_CHOICES = ("domestic", "foreign")
VIDEO_PEOPLE_CHOICES = ("people", "none")
VIDEO_PREFERENCE_CHOICES = ("like", "neutral", "dislike")

VIDEO_SCENE_CHOICES = (
    "城市", "自然", "商业", "科技", "财经", "生活", "美食", "医疗", "教育", "工业",
)
VIDEO_SHOT_TYPE_CHOICES = (
    "航拍", "空镜", "建筑", "交通", "人像", "特写",
)


class VideoAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_no: str
    source: str
    pexels_id: int | None
    file_path: str
    orientation: str
    width: int
    height: int
    duration_sec: float
    description_en: str | None
    description_zh: str | None
    photographer: str | None
    source_url: str | None
    raw_query: str | None
    source_type: str
    location: str
    scenes: list[str]
    shot_types: list[str]
    people: str
    preference: str
    tags: list[str]
    ai_tagged_at: datetime | None = None
    ai_tag_model: str | None = None
    ai_confidence: dict | None = None
    ai_tags_extra: dict | None = None
    used_count: int
    created_at: datetime
    updated_at: datetime


class VideoAssetUpdate(BaseModel):
    """用户可手动修正的字段(asset_no 不可改)."""

    source_type: Literal["footage", "creative"] | None = None
    location: Literal["domestic", "foreign"] | None = None
    scenes: list[str] | None = None
    shot_types: list[str] | None = None
    people: Literal["people", "none"] | None = None
    preference: Literal["like", "neutral", "dislike"] | None = None
    description_en: str | None = Field(default=None, max_length=2000)
    description_zh: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = None


class VideoAssetPreferenceRequest(BaseModel):
    preference: Literal["like", "neutral", "dislike"]


# ---------------------------------------------------------------------------
# AI 素材打标 schemas
# ---------------------------------------------------------------------------

class TaggingRunRequest(BaseModel):
    """批量打标请求."""
    asset_ids: list[str] | None = Field(
        default=None, description="指定素材 ID 列表；为空则全量打标"
    )


class TaggingProgressOut(BaseModel):
    job_id: str
    status: str  # pending / running / completed / failed / cancelled
    total: int
    done: int
    failed: int
    current_asset_no: str | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


# ---------------------------------------------------------------------------
# Pexels material resolve schemas (ID-003)
# ---------------------------------------------------------------------------

class ResolveItem(BaseModel):
    """Pexels resolve 单条结果 — 本地/远程均可,必须含合规署名."""

    id: int | None = Field(default=None, description="本地 material_assets.id")
    local_path: str | None = Field(default=None, description="本地缓存路径")
    source_url: str | None = Field(default=None, description="Pexels 原片 URL")
    degraded: bool = Field(default=False, description="未下到本地,仅元数据")
    reason: str | None = Field(default=None, description="降级原因")
    duration_sec: int
    width: int
    height: int
    fps: int | None = None
    photographer: str
    photographer_url: str
    pexels_url: str
    tags: list[str] = Field(default_factory=list)


class ResolveResponse(BaseModel):
    items: list[ResolveItem] = Field(default_factory=list)
    degraded: bool = Field(default=False)
    reason: str | None = None


class ResolveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=256)
    max_results: int | None = Field(default=None, ge=1, le=20)
    min_duration_sec: int | None = Field(default=None, ge=1, le=300)
    prefer_resolution: str | None = Field(default=None, pattern=r"^(UHD|FHD|HD|SD)$")
    orientation: str | None = Field(default="any", pattern=r"^(landscape|portrait|any)$")


class MaterialAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pexels_id: int
    source_url: str
    pexels_url: str
    photographer: str
    photographer_url: str
    local_path: str | None
    duration_sec: int
    width: int
    height: int
    fps: int | None
    resolution: str
    tags: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Persona schemas (人物关联: 提示词模板 + 音色 + 形象)
# ---------------------------------------------------------------------------
class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    prompt_template: str = Field(..., min_length=1, max_length=128, description="config/*.txt 文件名(不含 .txt)")
    voice_id: str | None = None
    role_id: str | None = None


class PersonaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    prompt_template: str | None = Field(default=None, min_length=1, max_length=128)
    voice_id: str | None = None
    role_id: str | None = None


class PersonaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    prompt_template: str
    voice_id: str | None
    role_id: str | None
    voice: VoiceOut | None = None
    role: RoleOut | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Video format specifications
# ---------------------------------------------------------------------------

VIDEO_FORMAT_SPECS: dict[str, dict[str, Any]] = {
    "portrait": {
        "width": 1080, "height": 1920,
        "comfyui_w": 576, "comfyui_h": 1024,
        "pexels_orientation": "portrait",
        "label": "竖屏 9:16",
    },
    "landscape": {
        "width": 1920, "height": 1080,
        "comfyui_w": 1024, "comfyui_h": 576,
        "pexels_orientation": "landscape",
        "label": "横屏 16:9",
    },
    "square": {
        "width": 1080, "height": 1080,
        "comfyui_w": 768, "comfyui_h": 768,
        "pexels_orientation": "square",
        "label": "方形 1:1",
    },
}


def get_video_format_spec(video_format: str | None) -> dict[str, Any]:
    """Return spec dict for the given format, defaulting to portrait."""
    return VIDEO_FORMAT_SPECS.get(video_format or "portrait", VIDEO_FORMAT_SPECS["portrait"])

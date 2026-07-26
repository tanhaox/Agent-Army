"""Pydantic schemas for API requests/responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ArticleCreate(BaseModel):
    title: str | None = None
    source_url: str | None = None
    raw_text: str = Field(..., min_length=1, max_length=15000)


class RewriteRequest(BaseModel):
    model: Literal["flash", "pro"] | None = None
    prompt_template: str | None = None


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


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    article_id: str
    host_id: str | None
    version: int
    script_text: str
    project_dir: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentOut]


class ScriptUpdate(BaseModel):
    script_text: str | None = Field(default=None, min_length=1)
    status: str | None = None
    project_dir: str | None = None


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
    elapsed_sec: float | None = None
    error: str | None = None

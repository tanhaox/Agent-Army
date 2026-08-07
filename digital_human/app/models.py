"""SQLAlchemy database models for digital human pipeline.

Tables support:
- articles: raw input articles (manual or crawler)
- scripts: rewritten broadcast scripts with versioning
- segments: per-line segments (core table for director/anchor selection)
- hosts: digital anchors/personas
- voices: voice configs including local TTS endpoints
- audio_jobs: async TTS job tracking
- audio_files: per-segment WAV outputs
- crawl_tasks: future crawler integration
- roles: digital human character profiles (ComfyUI multi-view)
- workflow_syncs: SSOT sync audit (startup)
- digital_human_videos: 数字人说话视频(LTX23 音频→视频)产物档案
- visual_render_jobs: HF 视觉渲染产物档案(独立管线,不接 ComfyUI / 不占 GPU)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------
class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    persona_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    fixed_opening: Mapped[str | None] = mapped_column(Text, default=None)
    fixed_ending: Mapped[str | None] = mapped_column(Text, default=None)
    reference_image: Mapped[str | None] = mapped_column(String(512), default=None)
    default_voice_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("voices.id"), default=None)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    voices: Mapped[list["Voice"]] = relationship(
        "Voice",
        back_populates="host",
        foreign_keys="Voice.host_id",
        lazy="selectin",
    )
    default_voice: Mapped["Voice | None"] = relationship(
        "Voice",
        foreign_keys=[default_voice_id],
        lazy="selectin",
    )


class Voice(Base):
    __tablename__ = "voices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    host_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("hosts.id"), default=None)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    backend: Mapped[str] = mapped_column(String(32), default="fish")  # fish / f5 / elevenlabs
    reference_audio_path: Mapped[str | None] = mapped_column(String(512), default=None)
    reference_text: Mapped[str | None] = mapped_column(Text, default=None)
    base_url_fish: Mapped[str | None] = mapped_column(String(256), default=None)
    base_url_f5: Mapped[str | None] = mapped_column(String(256), default=None)
    master_audio_path: Mapped[str | None] = mapped_column(String(512), default=None)
    master_text: Mapped[str | None] = mapped_column(Text, default=None)
    base_url_indextts: Mapped[str | None] = mapped_column(String(256), default=None)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    host: Mapped["Host | None"] = relationship(
        "Host",
        back_populates="voices",
        foreign_keys=[host_id],
    )


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    title: Mapped[str | None] = mapped_column(String(512), default=None)
    source_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    perspective_1: Mapped[str | None] = mapped_column(Text, default=None)  # 洗稿前的补充观点
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending / rewritten / generated / failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    scripts: Mapped[list["Script"]] = relationship(
        "Script",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    crawl_task: Mapped["CrawlTask | None"] = relationship(
        "CrawlTask",
        back_populates="article",
        uselist=False,
    )


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("articles.id"), nullable=False)
    host_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("hosts.id"), default=None)
    version: Mapped[int] = mapped_column(Integer, default=1)
    prompt_template: Mapped[str | None] = mapped_column(String(128), default=None)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    project_dir: Mapped[str | None] = mapped_column(String(1024), default=None)
    video_format: Mapped[str] = mapped_column(String(16), default="portrait")  # portrait / landscape / square
    perspective_2: Mapped[str | None] = mapped_column(Text, default=None)  # 洗稿后的修正观点
    status: Mapped[str] = mapped_column(
        String(32), default="drafting"
    )  # drafting / approved / generated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    article: Mapped["Article"] = relationship("Article", back_populates="scripts")
    host: Mapped["Host | None"] = relationship("Host", lazy="selectin")
    segments: Mapped[list["Segment"]] = relationship(
        "Segment",
        back_populates="script",
        cascade="all, delete-orphan",
        order_by="Segment.line_index",
        lazy="selectin",
    )
    audio_jobs: Mapped[list["AudioJob"]] = relationship(
        "AudioJob",
        back_populates="script",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id"), nullable=False)
    line_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    control_chars: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    segment_type: Mapped[str | None] = mapped_column(
        String(32), default="body"
    )  # opening / hook / body / cta / ending
    selected_for_host: Mapped[bool] = mapped_column(Boolean, default=True)
    host_order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_duration: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    script: Mapped["Script"] = relationship("Script", back_populates="segments")
    audio_files: Mapped[list["AudioFile"]] = relationship(
        "AudioFile",
        back_populates="segment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AudioJob(Base):
    __tablename__ = "audio_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id"), nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("voices.id"), default=None)
    output_dir: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending / running / completed / failed
    total_segments: Mapped[int] = mapped_column(Integer, default=0)
    completed_segments: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    script: Mapped["Script"] = relationship("Script", back_populates="audio_jobs")
    voice: Mapped["Voice | None"] = relationship("Voice", lazy="selectin")
    audio_files: Mapped[list["AudioFile"]] = relationship(
        "AudioFile",
        back_populates="audio_job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AudioFile(Base):
    __tablename__ = "audio_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    audio_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("audio_jobs.id"), nullable=False)
    segment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("segments.id"), default=None)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration: Mapped[float | None] = mapped_column(Float, default=None)
    sample_rate: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    audio_job: Mapped["AudioJob"] = relationship("AudioJob", back_populates="audio_files")
    segment: Mapped["Segment | None"] = relationship("Segment", back_populates="audio_files")


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    source_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    source_type: Mapped[str] = mapped_column(String(32), default="url")  # rss / url / api
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending / fetched / failed
    article_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("articles.id"), default=None)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    article: Mapped["Article | None"] = relationship("Article", back_populates="crawl_task")


class Role(Base):
    """数字人角色档案 — 多组多机位形象管理.

    reference_image: 用户上传的主参考图(兼容旧逻辑)
    view_groups: 形象组列表, 每组含 4 个机位图:
        [
          {"name": "演播室正装", "cameras": {"1": "/path/cam1.png", "2": ..., "3": ..., "4": ...}},
          {"name": "户外休闲", "cameras": {...}},
        ]
    机位定义:
        1 = 正面半身  2 = 左侧45度半身  3 = 右侧45度半身  4 = 正面特写
    """
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    reference_image: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    view_groups: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    # 兼容旧字段(逐步废弃)
    views: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    workflow_used: Mapped[str] = mapped_column(String(64), default="character_three_view")
    seed: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class WorkflowSync(Base):
    """workflows/ 同步审计 — 每次启动期记一行.

    synced: True=已覆盖 False=未覆盖
    reason: skipped / missing / diff / conflict
    """
    __tablename__ = "workflow_syncs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sha256: Mapped[str | None] = mapped_column(String(64), default=None)
    runtime_sha256: Mapped[str | None] = mapped_column(String(64), default=None)
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String(128), default="")
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DigitalHumanVideo(Base):
    """数字人说话视频 — 聚合多段音频 + 分镜图 → ComfyUI LTX23 → MP4.

    状态机: pending → aggregating → running → completed / failed
    输入: audio_source_paths (N 段 wav) + storyboard_paths (1-N 张分镜图)
    产物: output_video_path (mp4) + 验证元数据 (duration_actual/fps_actual/frame_count/has_audio_stream)
    """
    __tablename__ = "digital_human_videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    role_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("roles.id"), default=None
    )
    workflow_name: Mapped[str] = mapped_column(String(64), default="digital_human_video_ltx23")

    # ── Inputs ──
    audio_source_paths: Mapped[list[str]] = mapped_column(JSON, default=list)
    aggregated_audio_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    aggregated_duration_sec: Mapped[float | None] = mapped_column(Float, default=None)
    storyboard_paths: Mapped[list[str]] = mapped_column(JSON, default=list)
    storyboard_prompts: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_duration_sec: Mapped[float] = mapped_column(Float, default=10.0)
    fps: Mapped[int] = mapped_column(Integer, default=24)
    width: Mapped[int] = mapped_column(Integer, default=576)
    height: Mapped[int] = mapped_column(Integer, default=1024)
    seed: Mapped[int | None] = mapped_column(Integer, default=None)

    # ── Outputs / state ──
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending / aggregating / running / completed / failed
    prompt_id: Mapped[str | None] = mapped_column(String(64), default=None)
    output_video_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    duration_actual: Mapped[float | None] = mapped_column(Float, default=None)
    fps_actual: Mapped[float | None] = mapped_column(Float, default=None)
    has_audio_stream: Mapped[bool] = mapped_column(Boolean, default=False)
    frame_count: Mapped[int | None] = mapped_column(Integer, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    comfy_log: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    role: Mapped["Role | None"] = relationship("Role", lazy="selectin")


class VisualRenderJob(Base):
    """HF 视觉渲染任务 — 标准 JSON 入参 → HF npx 渲染 → MP4 + 关键帧 + manifest.

    独立管线:不接 ComfyUI / 不占 GPU / 与 DigitalHumanVideo 状态机解耦.
    状态机: queued → preparing → rendering → validating → completed / failed / cancelled.
    产物: output_path (mp4) + preview_frames (first/middle/final png) + manifest_path.
    """
    __tablename__ = "visual_render_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    template_id: Mapped[str] = mapped_column(String(64), default="news-data-v1")
    template_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    composition_id: Mapped[str] = mapped_column(String(64), default="news_main")

    # ── Inputs ──
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    input_path: Mapped[str | None] = mapped_column(String(1024), default=None)

    # ── State ──
    status: Mapped[str] = mapped_column(String(32), default="queued")
    # queued / preparing / rendering / validating / completed / failed / cancelled
    error_code: Mapped[str | None] = mapped_column(String(64), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    warnings: Mapped[list[Any]] = mapped_column(JSON, default=list)

    # ── Outputs ──
    output_dir: Mapped[str | None] = mapped_column(String(1024), default=None)
    output_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    manifest_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    preview_frames: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    media: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    render_seconds: Mapped[float | None] = mapped_column(Float, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class DirectorJob(Base):
    """视觉导演 2.0 任务 — 整段 TTS 音频生成后触发,输出 slot 工序单.

    状态机: planning → executing → reviewing → completed / failed
    """

    __tablename__ = "director_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id"), nullable=False)
    audio_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("audio_files.id"), default=None
    )

    video_format: Mapped[str] = mapped_column(String(16), default="portrait")
    # 启用的管线约束 (规范化字符串: "c,p,h" 升序; None=全启用).
    # create/execute/retry 缺省时回退到此列, 避免重启/重试丢约束 → 全启用.
    pipelines: Mapped[str | None] = mapped_column(String(32), default=None)
    title: Mapped[str | None] = mapped_column(String(256), default=None)
    view_group_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(32), default="planning"
    )  # planning / executing / reviewing / completed / failed
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    total_duration_sec: Mapped[float | None] = mapped_column(Float, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    script: Mapped["Script"] = relationship("Script", lazy="selectin")
    audio_file: Mapped["AudioFile | None"] = relationship("AudioFile", lazy="selectin")
    slots: Mapped[list["DirectorSlot"]] = relationship(
        "DirectorSlot",
        back_populates="director_job",
        cascade="all, delete-orphan",
        order_by="DirectorSlot.slot_index",
        lazy="selectin",
    )


class DirectorSlot(Base):
    """视觉导演 2.0 时间槽位 — 每个 slot 由下游工作流独立执行.

    状态机: queued → running → completed / failed / replaced
    """

    __tablename__ = "director_slots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    director_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("director_jobs.id"), nullable=False
    )
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)

    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    text_context: Mapped[str | None] = mapped_column(Text, default=None)
    segment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("segments.id"), default=None
    )

    visual_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # host / broll_pexels / broll_local / hf_chart / hf_title / mixed_host_broll
    workflow: Mapped[str] = mapped_column(String(32), nullable=False)
    params_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    camera_angle: Mapped[int] = mapped_column(Integer, default=1)  # 1-4 机位
    view_group_index: Mapped[int] = mapped_column(Integer, default=0)  # 形象组索引

    status: Mapped[str] = mapped_column(
        String(32), default="queued"
    )  # queued / running / completed / failed / replaced / skipped
    output_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    error_code: Mapped[str | None] = mapped_column(String(64), default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    director_job: Mapped["DirectorJob"] = relationship("DirectorJob", back_populates="slots")
    segment: Mapped["Segment | None"] = relationship("Segment", lazy="selectin")


class MaterialAsset(Base):
    """Pexels 视频素材本地缓存表.

    视觉导演调用 pexels_service.resolve() 时优先命中本地行,避免重复下载.
    degraded 行 (local_path is None) 用于 quota 超限/下载失败时仍返回元数据.
    """

    __tablename__ = "material_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pexels_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    pexels_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    photographer: Mapped[str] = mapped_column(String(256), nullable=False)
    photographer_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    local_path: Mapped[str | None] = mapped_column(String(1024), default=None)
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[int | None] = mapped_column(Integer, default=None)
    resolution: Mapped[str] = mapped_column(String(16), nullable=False)
    tags: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DownloadLog(Base):
    """Pexels 下载配额审计 — 按自然日重置."""

    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    pexels_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (Index("idx_download_logs_date", "date"),)


class Persona(Base):
    """数字人物关联 — 提示词模板 + 音色 + 形象 三维绑定.

    流水线选定提示词模板后, 关联的音色和形象自动锁定不可更改.
    """
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_template: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True
    )  # config/*.txt 文件名 (不含 .txt)
    voice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("voices.id"), default=None
    )
    role_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("roles.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    voice: Mapped["Voice | None"] = relationship("Voice", lazy="selectin")
    role: Mapped["Role | None"] = relationship("Role", lazy="selectin")


# ---------------------------------------------------------------------------
# 视频素材库 — Pexels / 本地 / 手动上传的 B-roll 片段
# ---------------------------------------------------------------------------

class VideoAsset(Base):
    """B-roll 素材库条目 — 给导演 slot 选用的视频片段.

    来源: pexels 下载 / 本地导入 / 手动上传
    支持: 唯一编号、多维标签(方向/来源/画面/场景/镜头/人物/偏好)、使用计数
    """

    __tablename__ = "video_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    asset_no: Mapped[str] = mapped_column(
        String(16), nullable=False, unique=True, index=True
    )  # 自动生成的唯一编号, e.g. V20260802-0001
    source: Mapped[str] = mapped_column(String(16), default="pexels")  # pexels / local / manual
    pexels_id: Mapped[int | None] = mapped_column(Integer, default=None, unique=True)  # Pexels video ID 去重
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # 方向(从宽高比自动推断)
    orientation: Mapped[str] = mapped_column(String(16), default="landscape")  # portrait / landscape
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    # 描述 — 中英对照(不再被台词污染)
    description_en: Mapped[str | None] = mapped_column(Text, default=None)
    description_zh: Mapped[str | None] = mapped_column(Text, default=None)
    # 元数据
    photographer: Mapped[str | None] = mapped_column(String(128), default=None)
    source_url: Mapped[str | None] = mapped_column(String(512), default=None)
    raw_query: Mapped[str | None] = mapped_column(String(512), default=None)  # 入库时的原始搜索 query
    # 多维标签体系
    source_type: Mapped[str] = mapped_column(String(16), default="footage")  # footage 实拍 / creative 创意
    location: Mapped[str] = mapped_column(String(16), default="foreign")  # domestic 国内 / foreign 国外
    scenes: Mapped[list[str]] = mapped_column(JSON, default=list)  # 场景(多选)
    shot_types: Mapped[list[str]] = mapped_column(JSON, default=list)  # 镜头类型(多选)
    people: Mapped[str] = mapped_column(String(16), default="none")  # people 有人 / none 无人
    preference: Mapped[str] = mapped_column(String(16), default="neutral")  # like / neutral / dislike
    # 旧标签字段保留,用于兼容未重新下载的素材;新素材使用多维标签
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    # AI 打标追踪字段
    ai_tagged_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    ai_tag_model: Mapped[str | None] = mapped_column(String(64), default=None)
    ai_confidence: Mapped[dict | None] = mapped_column(JSON, default=None)
    ai_tags_extra: Mapped[dict | None] = mapped_column(JSON, default=None)
    # 使用统计
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    __table_args__ = (
        Index("idx_video_assets_asset_no", "asset_no"),
        Index("idx_video_assets_orientation", "orientation"),
        Index("idx_video_assets_source_type", "source_type"),
        Index("idx_video_assets_location", "location"),
        Index("idx_video_assets_people", "people"),
        Index("idx_video_assets_preference", "preference"),
    )


# ---------------------------------------------------------------------------
# 成品视频库 — 导演台合成后的完整视频
# ---------------------------------------------------------------------------

class VideoOutput(Base):
    """成品视频登记 — 导演台合成后的最终 MP4.

    简单登记: 标题/日期/画幅/路径/时长
    """
    __tablename__ = "video_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    job_id: Mapped[str | None] = mapped_column(String(36), default=None)  # 关联导演任务
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    orientation: Mapped[str] = mapped_column(String(16), default="portrait")
    duration_sec: Mapped[float | None] = mapped_column(Float, default=None)
    video_format: Mapped[str | None] = mapped_column(String(16), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

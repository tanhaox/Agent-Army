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
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
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
    estimated_duration: Mapped[float | None] = mapped_column(default=None)
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
    duration: Mapped[float | None] = mapped_column(default=None)
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
    """数字人角色档案 — ComfyUI 多视图定型 + 主流水线入参.

    reference_image: 用户上传的参考图,绝对路径 (E:/数字人计划/roles/<id>/ref.png)
    views: 生成结果 {front/side/full} → 绝对路径
    workflow_used: 绑定的 workflow 名 (manifest.yaml 中的 key)
    seed: 锁定 seed 让 3 张视图可复现
    """
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    reference_image: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
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

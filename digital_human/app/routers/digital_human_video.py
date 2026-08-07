"""DigitalHumanVideo router — LTX 2.3 音频+分镜图 → MP4.

8 端点:
  GET  /api/dhv/eligible-audio          列已生成 wav 候选
  GET  /api/dhv/videos                  列任务
  POST /api/dhv/videos                  创建任务 (status=pending, 仅校验参数)
  GET  /api/dhv/videos/{id}             详情
  POST /api/dhv/videos/{id}/upload-storyboard  上传分镜图 → 行内 storyboard_paths
  POST /api/dhv/videos/{id}/generate    同步: 聚合音频 → 构造 workflow → ComfyUI → ffprobe 校验 → 落盘
  GET  /api/dhv/videos/{id}/download   下载产物 mp4 (FileResponse)
  DELETE /api/dhv/videos/{id}           删除任务

设计要点:
  - 与 IndexTTS2 一致: 同步生成 + 后台 SSE 模式备选 (本任务选同步, 5-10s 音频对应 1-3min 出视频)
  - 视频落盘到 E:/数字人计划/dhv/<video_id>/<video_id>.mp4
  - ComfyUI 产物拷贝路径复用 _persist_outputs 思路
  - ffprobe 验证三件套 (用户禁忌: 不要跳过音频流/时长/帧率)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import get_config
from ..database import get_db
from ..models import AudioFile, DigitalHumanVideo, Role
from ..schemas import (
    DigitalHumanVideoCreate,
    DigitalHumanVideoOut,
    EligibleAudioItem,
    EligibleAudioResponse,
    GenerateVideoResponse,
    StoryboardUploadResponse,
)
from ..services.audio_aggregator import aggregate_segments
from ..services.lit_video_builder import build_ltx23_video_workflow
from ..services.video_validator import validate_mp4
from ..services.file_utils import safe_trash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dhv", tags=["digital_human_video"])


def _dhv_root() -> Path:
    cfg = get_config()
    return Path(r"E:/数字人计划/dhv")


# ---------------------------------------------------------------------------
# 1. 列候选音频
# ---------------------------------------------------------------------------
@router.get("/eligible-audio", response_model=EligibleAudioResponse)
def eligible_audio(limit: int = 50, db: Session = Depends(get_db)):
    """扫 AudioFile 中 duration ≥ 0.5s 且 file_path 存在的 wav."""
    rows = (
        db.query(AudioFile)
        .order_by(AudioFile.created_at.desc())
        .limit(limit * 3)  # 多取一些, 再过滤
        .all()
    )
    items: list[EligibleAudioItem] = []
    total = 0.0
    for af in rows:
        p = Path(af.file_path)
        if not p.exists():
            continue
        if af.duration is not None and af.duration < 0.5:
            continue
        items.append(
            EligibleAudioItem(
                label=f"{af.filename} ({af.duration:.1f}s)"
                if af.duration
                else af.filename,
                path=str(p),
                duration_sec=af.duration,
                sample_rate=af.sample_rate,
                source_job_id=af.audio_job_id,
                source_segment_id=af.segment_id,
            )
        )
        total += af.duration or 0.0
        if len(items) >= limit:
            break
    return EligibleAudioResponse(items=items, total_duration_sec=round(total, 2))


# ---------------------------------------------------------------------------
# 2. 列表
# ---------------------------------------------------------------------------
@router.get("/videos", response_model=list[DigitalHumanVideoOut])
def list_videos(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(DigitalHumanVideo)
        .order_by(DigitalHumanVideo.created_at.desc())
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# 3. 创建
# ---------------------------------------------------------------------------
@router.post("/videos", response_model=DigitalHumanVideoOut, status_code=201)
def create_video(body: DigitalHumanVideoCreate, db: Session = Depends(get_db)):
    if not body.audio_source_paths:
        raise HTTPException(status_code=400, detail="audio_source_paths 不能为空")
    if body.role_id:
        role = db.query(Role).filter(Role.id == body.role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
    # audio path 实际校验留给 generate 时 (先给 404 太严格)
    vid = DigitalHumanVideo(
        role_id=body.role_id,
        workflow_name="digital_human_video_ltx23",
        audio_source_paths=list(body.audio_source_paths),
        storyboard_prompts=list(body.storyboard_prompts),
        target_duration_sec=body.target_duration_sec,
        fps=body.fps,
        width=body.width,
        height=body.height,
        seed=body.seed,
        status="pending",
    )
    db.add(vid)
    db.commit()
    db.refresh(vid)
    return vid


# ---------------------------------------------------------------------------
# 4. 详情
# ---------------------------------------------------------------------------
@router.get("/videos/{video_id}", response_model=DigitalHumanVideoOut)
def get_video(video_id: str, db: Session = Depends(get_db)):
    v = db.query(DigitalHumanVideo).filter(DigitalHumanVideo.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="DigitalHumanVideo not found")
    return v


# ---------------------------------------------------------------------------
# 5. 上传分镜图
# ---------------------------------------------------------------------------
@router.post("/videos/{video_id}/upload-storyboard", response_model=StoryboardUploadResponse)
async def upload_storyboard(
    video_id: str,
    files: list[UploadFile] = File(...),
    prompts: str = Form(default=""),
    db: Session = Depends(get_db),
):
    v = db.query(DigitalHumanVideo).filter(DigitalHumanVideo.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="DigitalHumanVideo not found")
    if v.status not in ("pending",):
        raise HTTPException(status_code=409, detail=f"video status={v.status} 不允许上传分镜")

    storyboard_dir = _dhv_root() / video_id / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    uploaded: list[str] = []
    for f in files:
        suffix = Path(f.filename or "img.png").suffix or ".png"
        dest = storyboard_dir / f"{uuid.uuid4().hex[:8]}{suffix}"
        dest.write_bytes(await f.read())
        uploaded.append(str(dest))

    prompt_list = [p.strip() for p in prompts.split("\n") if p.strip()] if prompts else []
    v.storyboard_paths = list(v.storyboard_paths) + uploaded
    v.storyboard_prompts = list(v.storyboard_prompts) + prompt_list
    db.commit()
    db.refresh(v)
    return StoryboardUploadResponse(
        video_id=v.id,
        uploaded_paths=uploaded,
        storyboard_prompts=list(v.storyboard_prompts),
    )


# ---------------------------------------------------------------------------
# 6. 生成 (核心)
# ---------------------------------------------------------------------------
@router.post("/videos/{video_id}/generate", response_model=GenerateVideoResponse)
async def generate_video(video_id: str, db: Session = Depends(get_db)):
    """同步: 聚合音频 → 构造 workflow → ComfyUI /prompt → 轮询 → 落盘 → ffprobe 校验."""
    v = db.query(DigitalHumanVideo).filter(DigitalHumanVideo.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="DigitalHumanVideo not found")
    if v.status in ("completed", "running"):
        raise HTTPException(status_code=409, detail=f"video status={v.status}")

    if not v.storyboard_paths:
        raise HTTPException(status_code=400, detail="storyboard_paths 为空, 请先 upload-storyboard")

    cfg = get_config()
    t0 = time.time()

    v.status = "running"
    v.error_message = None
    db.commit()
    db.refresh(v)

    issues: list[str] = []
    try:
        # ── Step A: 聚合音频 ──
        out_root = _dhv_root() / video_id
        out_root.mkdir(parents=True, exist_ok=True)
        agg_path = out_root / "audio_aggregated.wav"
        agg = aggregate_segments(
            v.audio_source_paths,
            target_duration_sec=v.target_duration_sec,
            min_duration_sec=5.0,
            output_path=agg_path,
            silence_gap_sec=0.3,
        )
        if not agg["ok"]:
            v.status = "failed"
            v.error_message = " | ".join(agg["issues"])
            db.commit()
            return GenerateVideoResponse(
                video_id=video_id, status="failed", prompt_id=None,
                output_video_path=None, aggregated_audio_path=None,
                aggregated_duration_sec=None, duration_actual=None,
                fps_actual=None, has_audio_stream=False, frame_count=None,
                validation_issues=agg["issues"],
                validation_warnings=[],
                elapsed_sec=time.time() - t0,
                error=v.error_message,
            )
        v.aggregated_audio_path = str(agg_path)
        v.aggregated_duration_sec = agg["actual_duration_sec"]
        db.commit()

        # ── Step B: 构造 workflow dict ──
        # 把绝对路径的 audio + storyboard 拷贝到 ComfyUI input/
        comfy_input = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/input")
        comfy_input.mkdir(parents=True, exist_ok=True)

        audio_dst = comfy_input / f"dhv_{video_id}_{Path(agg_path).name}"
        shutil.copy2(str(agg_path), str(audio_dst))

        storyboard_for_wf: list[dict[str, Any]] = []
        for i, src in enumerate(v.storyboard_paths):
            src_p = Path(src)
            if not src_p.exists():
                issues.append(f"storyboard file missing: {src}")
                continue
            img_dst = comfy_input / f"dhv_{video_id}_sb{i}_{src_p.name}"
            shutil.copy2(str(src_p), str(img_dst))
            storyboard_for_wf.append({
                "filename": img_dst.name,
                "frame_idx": i * 60,
                "strength": 0.85,
            })
        if not storyboard_for_wf:
            raise RuntimeError("no storyboard images available")

        orientation = "landscape" if v.width > v.height else "portrait"
        workflow = build_ltx23_video_workflow(
            audio_filename=audio_dst.name,
            storyboard=storyboard_for_wf,
            duration_sec=v.target_duration_sec,
            fps=v.fps, orientation=orientation,
            seed=v.seed,
            filename_prefix=f"dhv_{video_id}_",
        )

        # ── Step C: 提交 ComfyUI /prompt ──
        base_url = cfg.defaults.base_url_comfyui.rstrip("/")
        prompt_id: str | None = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            client_id = str(uuid.uuid4())
            try:
                resp = await client.post(
                    f"{base_url}/prompt",
                    json={"prompt": workflow, "client_id": client_id},
                )
            except httpx.RequestError as exc:
                raise RuntimeError(f"ComfyUI 不可达: {exc}") from exc
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"ComfyUI /prompt HTTP {resp.status_code}: {resp.text[:300]}"
                )
            try:
                prompt_id = resp.json()["prompt_id"]
            except (KeyError, ValueError) as exc:
                raise RuntimeError(f"ComfyUI 响应异常: {exc}") from exc

        v.prompt_id = prompt_id
        v.comfy_log = {"submitted_at": time.time(), "client_id": client_id}
        db.commit()
        logger.info("[dhv %s] submitted prompt_id=%s", video_id, prompt_id)

        # ── Step D: 轮询 /history/{prompt_id} ──
        deadline = time.time() + cfg.defaults.comfyui_timeout_sec
        history_entry: dict[str, Any] | None = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.time() < deadline:
                await asyncio.sleep(2.0)
                try:
                    h = await client.get(f"{base_url}/history/{prompt_id}")
                except httpx.RequestError:
                    continue
                if h.status_code >= 400:
                    continue
                entry = (h.json() or {}).get(prompt_id)
                if not entry:
                    continue
                status_dict = entry.get("status") or {}
                if status_dict.get("completed"):
                    history_entry = entry
                    break
                if status_dict.get("errored"):
                    raise RuntimeError(
                        f"ComfyUI task errored: {(status_dict.get('error') or 'unknown')[:500]}"
                    )

        if history_entry is None:
            raise RuntimeError(
                f"ComfyUI task timeout after {cfg.defaults.comfyui_timeout_sec}s"
            )

        # ── Step E: 落盘 mp4 ──
        mp4_src = _find_mp4(history_entry)
        if not mp4_src or not mp4_src.exists():
            raise RuntimeError(f"ComfyUI outputs 中无 mp4: {history_entry.get('outputs')}")
        mp4_dst = out_root / f"{video_id}.mp4"
        try:
            os.replace(str(mp4_src), str(mp4_dst))
        except OSError:
            shutil.copy2(str(mp4_src), str(mp4_dst))
            mp4_src.unlink(missing_ok=True)
        v.output_video_path = str(mp4_dst)

        # ── Step F: ffprobe 校验 ──
        val = validate_mp4(
            mp4_dst,
            expected_duration=v.target_duration_sec,
            expected_fps=v.fps,
            min_duration=5.0,
        )
        issues = list(val["issues"])
        warnings = list(val.get("warnings") or [])
        v.duration_actual = (val["meta"] or {}).get("duration_actual")
        v.fps_actual = (val["meta"] or {}).get("fps_actual")
        v.has_audio_stream = bool((val["meta"] or {}).get("has_audio_stream"))
        v.frame_count = (val["meta"] or {}).get("frame_count")
        if warnings:
            v.comfy_log = {**(v.comfy_log or {}), "validation_warnings": warnings}

        # 关键硬约束: 视频有 audio stream 才算真正成功
        if val["ok"]:
            v.status = "completed"
            v.completed_at = _now()
        else:
            v.status = "validation_failed"
            v.error_message = " | ".join(issues)
        db.commit()
        db.refresh(v)

        return GenerateVideoResponse(
            video_id=video_id,
            status=v.status,
            prompt_id=prompt_id,
            output_video_path=v.output_video_path,
            aggregated_audio_path=v.aggregated_audio_path,
            aggregated_duration_sec=v.aggregated_duration_sec,
            duration_actual=v.duration_actual,
            fps_actual=v.fps_actual,
            has_audio_stream=v.has_audio_stream,
            frame_count=v.frame_count,
            validation_issues=issues,
            validation_warnings=warnings,
            elapsed_sec=time.time() - t0,
            error=v.error_message if v.status != "completed" else None,
        )

    except Exception as exc:
        logger.exception("[dhv %s] generate failed", video_id)
        v.status = "failed"
        v.error_message = str(exc)[:1000]
        db.commit()
        db.refresh(v)
        return GenerateVideoResponse(
            video_id=video_id, status="failed", prompt_id=v.prompt_id,
            output_video_path=v.output_video_path,
            aggregated_audio_path=v.aggregated_audio_path,
            aggregated_duration_sec=v.aggregated_duration_sec,
            duration_actual=v.duration_actual,
            fps_actual=v.fps_actual,
            has_audio_stream=v.has_audio_stream,
            frame_count=v.frame_count,
            validation_issues=issues,
            validation_warnings=[],
            elapsed_sec=time.time() - t0,
            error=v.error_message,
        )


# ---------------------------------------------------------------------------
# 7. 下载
# ---------------------------------------------------------------------------
@router.get("/videos/{video_id}/download")
def download_video(video_id: str, db: Session = Depends(get_db)):
    v = db.query(DigitalHumanVideo).filter(DigitalHumanVideo.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="DigitalHumanVideo not found")
    if not v.output_video_path:
        raise HTTPException(status_code=409, detail="video 未生成产物")
    p = Path(v.output_video_path)
    if not p.exists():
        raise HTTPException(status_code=410, detail="video 文件丢失")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)


# ---------------------------------------------------------------------------
# 8. 删除
# ---------------------------------------------------------------------------
@router.delete("/videos/{video_id}", status_code=204)
def delete_video(video_id: str, db: Session = Depends(get_db)):
    v = db.query(DigitalHumanVideo).filter(DigitalHumanVideo.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="DigitalHumanVideo not found")
    # 删除产物目录 — 优先走回收站 (CLAUDE.md 铁律)
    out_dir = _dhv_root() / video_id
    if out_dir.exists():
        safe_trash(out_dir)
    db.delete(v)
    db.commit()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _find_mp4(history_entry: dict[str, Any]) -> Path | None:
    """从 ComfyUI /history outputs 找到第一个 .mp4 产物.

    VHS_VideoCombine 的产物形态:
      outputs: {"800": {"gifs": [{"filename": "xxx.mp4", "type": "output", "subfolder": ""}]}}
    """
    comf_output = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/output")
    outputs = history_entry.get("outputs") or {}
    for _nid, payload in outputs.items():
        for key in ("gifs", "images", "files"):
            for f in payload.get(key) or []:
                fn = f.get("filename", "")
                if fn.lower().endswith((".mp4", ".mov", ".webm")):
                    sub = f.get("subfolder", "")
                    t = f.get("type", "output")
                    base = (
                        comf_output
                        if t == "output"
                        else Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/input")
                        if t == "input"
                        else Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/temp")
                    )
                    cand = base / sub / fn if sub else base / fn
                    if cand.exists():
                        return cand
    return None


def _now():
    from datetime import datetime
    return datetime.utcnow()
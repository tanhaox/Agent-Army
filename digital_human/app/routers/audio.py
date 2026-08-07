"""Audio router: TTS generation and downloads."""
from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db, get_session_maker
from ..models import AudioFile, AudioJob, Host, Script, Segment, Voice
from ..schemas import AudioFileOut, AudioJobOut
from ..services.gpu_service_manager import get_gpu_service_manager
from ..services.tts_service import TTSService
from .jobs import _publish

router = APIRouter(prefix="/api/audio", tags=["audio"])


def get_tts() -> TTSService:
    from ..config import get_config

    cfg = get_config()
    return TTSService(cfg.defaults)


@router.post("/scripts/{script_id}/generate-audio", response_model=AudioJobOut)
def generate_audio(
    script_id: str,
    voice_id: str | None = None,
    selected_only: bool = True,
    background_tasks: BackgroundTasks = ...,
    db: Session = Depends(get_db),
    tts: TTSService = Depends(get_tts),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    voice = None
    if voice_id:
        voice = db.query(Voice).filter(Voice.id == voice_id).first()
    # 未显式选音色 → 优先用 host.default_voice_id (2026-08-07: 老陈默认=大学教授 indextts),
    # 而非 host 下第一条 voice (旧逻辑会取到已弃用的 fish laochen_default)。
    if not voice and script.host_id:
        host = db.query(Host).filter(Host.id == script.host_id).first()
        if host and host.default_voice_id:
            voice = db.query(Voice).filter(Voice.id == host.default_voice_id).first()
    if not voice and script.host_id:
        voice = db.query(Voice).filter(Voice.host_id == script.host_id).first()

    query = db.query(Segment).filter(Segment.script_id == script_id)
    if selected_only:
        query = query.filter(Segment.selected_for_host == True)
    segments = query.order_by(Segment.host_order).all()

    if not segments:
        raise HTTPException(status_code=400, detail="No segments to synthesize")

    project_root = Path(__file__).resolve().parents[2]
    if script.project_dir:
        output_dir = Path(script.project_dir) / "audio"
    else:
        today = datetime.date.today().isoformat()
        voice_label = voice.name if voice else "default"
        voice_id_short = voice.id[:8] if voice else "default"
        output_dir = Path(r"E:\数字人计划\outputs\audio") / today / voice_label / f"{voice_id_short}_{int(time.time())}"
    output_dir.mkdir(parents=True, exist_ok=True)

    job = AudioJob(
        script_id=script_id,
        voice_id=voice.id if voice else None,
        output_dir=str(output_dir),
        status="pending",
        total_segments=len(segments),
        completed_segments=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_do_tts, job.id)
    return job


def _do_tts(job_id: str):
    Session = get_session_maker()
    if Session is None:
        _publish(job_id, {"type": "tts_error", "error": "Database not initialized"})
        return
    db = Session()
    try:
        job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
        if not job:
            _publish(job_id, {"type": "tts_error", "error": "Audio job not found"})
            return

        script = db.query(Script).filter(Script.id == job.script_id).first()
        voice = None
        if job.voice_id:
            voice = db.query(Voice).filter(Voice.id == job.voice_id).first()

        query = db.query(Segment).filter(Segment.script_id == job.script_id)
        query = query.filter(Segment.selected_for_host == True)
        segments = query.order_by(Segment.host_order).all()

        if not segments:
            job.status = "failed"
            job.error_message = "No segments to synthesize"
            db.commit()
            _publish(job_id, {"type": "tts_error", "error": "No segments to synthesize"})
            return

        job.status = "running"
        job.total_segments = len(segments)
        db.commit()

        tts = get_tts()

        def _progress(completed: int, total: int, text: str | None, audio_file: AudioFile | None = None) -> None:
            job.completed_segments = completed
            db.commit()
            event: dict = {
                "type": "tts_progress",
                "completed": completed,
                "total": total,
                "text": text,
            }
            if audio_file:
                db.add(audio_file)
                db.commit()
                db.refresh(audio_file)
                event["audio_file"] = {
                    "id": audio_file.id,
                    "filename": audio_file.filename,
                    "duration": audio_file.duration,
                    "segment_id": audio_file.segment_id,
                }
            _publish(job_id, event)

        # ── GPU 服务托管: 排队 + 按需拉起 TTS 后端 + 空闲自动关停腾显存 ──
        from ..config import get_config

        backend = (voice.backend if voice and voice.backend else get_config().defaults.backend)

        def _svc_notify(message: str) -> None:
            _publish(job_id, {"type": "tts_service", "message": message})

        manager = get_gpu_service_manager()
        with manager.session(backend, status_callback=_svc_notify):
            result = tts.generate(job, segments, voice, progress_callback=_progress)
        # audio_files rows are already committed one-by-one inside _progress,
        # so no add_all here — a second add would double-insert (P0-1 related).

        for af in result["audio_files"]:
            if af.segment_id and af.duration:
                seg = db.query(Segment).filter(Segment.id == af.segment_id).first()
                if seg:
                    seg.estimated_duration = af.duration

        # ── Save combined paragraph audio as AudioFile ──
        combined_info = result.get("combined_file")
        combined_audio_file = None
        if combined_info and combined_info.get("file_path"):
            combined_audio_file = AudioFile(
                audio_job_id=job.id,
                segment_id=None,
                filename=combined_info["file"],
                file_path=combined_info["file_path"],
                duration=combined_info.get("duration"),
                sample_rate=combined_info.get("sample_rate"),
            )
            db.add(combined_audio_file)

        job.status = "completed"
        job.completed_segments = len(segments)
        db.commit()

        output_dir = Path(job.output_dir)
        done_event: dict = {"type": "tts_done", "job_id": job.id, "output_dir": str(output_dir)}
        if combined_audio_file:
            done_event["combined_audio"] = {
                "id": combined_audio_file.id,
                "filename": combined_audio_file.filename,
                "duration": combined_audio_file.duration,
            }
        _publish(job_id, done_event)
    except Exception as exc:
        try:
            job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
            if job:
                job.status = "failed"
                # P0-1 方案 1: 失败不删盘 → 已生成 wav 保留, 可重试续传
                job.error_message = f"{exc}（已生成的音频已保留，重新生成将从断点继续）"
                db.commit()
        except Exception:
            pass
        _publish(job_id, {"type": "tts_error", "error": str(exc)})
    finally:
        db.close()


@router.get("/jobs", response_model=list[AudioJobOut])
def list_audio_jobs(
    script_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """查询音频任务，支持按 script_id / status 过滤."""
    query = db.query(AudioJob)
    if script_id:
        query = query.filter(AudioJob.script_id == script_id)
    if status:
        query = query.filter(AudioJob.status == status)
    return query.order_by(AudioJob.created_at.desc()).limit(limit).all()


@router.get("/jobs/{job_id}", response_model=AudioJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    return job


@router.get("/jobs/{job_id}/files", response_model=list[AudioFileOut])
def list_job_files(job_id: str, db: Session = Depends(get_db)):
    return db.query(AudioFile).filter(AudioFile.audio_job_id == job_id).order_by(AudioFile.filename).all()


@router.get("/files/{file_id}/download")
def download_file(file_id: str, db: Session = Depends(get_db)):
    af = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not af:
        raise HTTPException(status_code=404, detail="Audio file not found")
    path = Path(af.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="audio/wav", filename=af.filename)


@router.get("/jobs/{job_id}/manifest")
def download_manifest(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    manifest_path = Path(job.output_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(manifest_path, media_type="application/json", filename="manifest.json")

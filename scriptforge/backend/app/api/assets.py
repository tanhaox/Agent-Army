"""Assets API — manage intermediate pipeline artifacts (videos, audio, transcripts)."""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete


def _venv_python() -> str:
    """Return the venv python executable, falling back to sys.executable."""
    venv = Path(__file__).resolve().parent.parent.parent / ".venv-py312" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_factory
from app.models.asset import Asset, AssetType
from app.models.task_record import TaskRecord
from app.models.persona import Persona

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["Assets"])


def _merge_speaker_lines(segments: list[dict]) -> str:
    """Merge consecutive segments from the same speaker into one paragraph.

    Output format:
        【主播】第一句第二句第三句
        【连线观众】第四句第五句
        【主播】第六句
    """
    lines = []
    prev_speaker = None
    buf = []
    for s in segments:
        sp = s.get("speaker", "")
        txt = s.get("text", "").strip()
        if not txt:
            continue
        if sp != prev_speaker:
            if buf:
                lines.append(f"【{prev_speaker}】{''.join(buf)}")
                buf = []
            prev_speaker = sp
        buf.append(txt)
    if buf and prev_speaker:
        lines.append(f"【{prev_speaker}】{''.join(buf)}")
    return "\n".join(lines)


# ── Startup: recover orphaned batch-retranscribe tasks ──
import threading as _threading

def _start_batch_recovery():
    """On startup, mark orphaned 'running' batch_retranscribe tasks as failed."""
    import asyncpg as _apg
    from app.core.config import settings
    import asyncio as _aio

    async def _check():
        url = settings.DATABASE_URL.replace("+asyncpg", "")
        conn = await _apg.connect(url)
        try:
            result = await conn.execute("""
                UPDATE task_records SET status = 'failed', error_message = '服务重启，任务中断'
                WHERE status = 'running' AND trigger = 'batch_retranscribe'
            """)
            logger.info("[BatchRecovery] Cleaned orphaned tasks: %s", result)
        finally:
            await conn.close()

    try:
        _aio.run(_check())
    except Exception as e:
        logger.error("[BatchRecovery] Error: %s", e)

_recovery_thread = _threading.Thread(target=_start_batch_recovery, daemon=True)
_recovery_thread.start()


# ── Schemas ──

class AssetOut(BaseModel):
    id: str
    task_id: str
    anchor_name: str
    video_title: str
    asset_type: str
    file_path: str
    file_size: int
    duration: float
    transcription_text: str | None = None
    video_url: str | None = None

    class Config:
        from_attributes = True


class AssetDetailOut(AssetOut):
    pass


class AssetListOut(BaseModel):
    items: list[AssetOut]
    total: int
    page: int
    page_size: int


class AssetUpdateIn(BaseModel):
    transcription_text: str


class GroupStatsItem(BaseModel):
    anchor_name: str
    persona_id: str | None = None
    persona_name: str | None = None
    video_count: int = 0
    audio_count: int = 0
    transcript_count: int = 0
    total_size: int = 0


# ── Helpers ──

_VIDEO_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "videos"


def _make_video_url(file_path: str) -> str | None:
    """If the file exists locally, return a /uploads/videos/... URL for preview."""
    if not file_path:
        return None
    p = Path(file_path)
    # Try absolute path first, then relative to _VIDEO_DIR
    if p.is_absolute() and p.exists():
        return f"/uploads/videos/{p.name}"
    abs_path = _VIDEO_DIR / p.name
    if abs_path.exists():
        return f"/uploads/videos/{p.name}"
    # Also try the full relative path under backend/
    from app.core.database import async_session_factory
    backend_dir = Path(__file__).resolve().parent.parent.parent
    candidate = backend_dir / file_path
    if candidate.exists():
        return f"/uploads/videos/{p.name}"
    return None


# ── Endpoints ──

# Voice profile endpoints (MUST be before /{asset_id} to avoid route conflict)

@router.post("/build-voice-profile")
async def build_voice_profile(
    anchor_name: str = Query(..., description="Anchor name to build profile for"),
    persona_id: str | None = Query(None, description="Persona ID for profile naming"),
    db: AsyncSession = Depends(get_db),
):
    """Build a voice profile from all audio assets of the given anchor."""
    if not anchor_name.strip():
        raise HTTPException(status_code=400, detail="anchor_name 不能为空")

    rows = (
        await db.execute(
            select(Asset).where(
                Asset.anchor_name == anchor_name,
                Asset.asset_type == AssetType.audio,
            )
        )
    ).scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"未找到主播 '{anchor_name}' 的音频资产")

    backend_dir = Path(__file__).resolve().parent.parent.parent
    audio_paths = []
    for r in rows:
        p = Path(r.file_path)
        if not p.is_absolute():
            p = backend_dir / r.file_path
        if p.exists():
            audio_paths.append(str(p))

    if not audio_paths:
        raise HTTPException(status_code=404, detail="音频文件在磁盘上不存在")

    def _build():
        from app.services.voice_profile_builder import build_voice_profile
        return build_voice_profile(anchor_name, audio_paths, persona_id=persona_id)

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _build)
        return {"status": "ok", **result}
    except Exception as e:
        logger.error("Voice profile build failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"声纹构建失败: {e}")


@router.get("/voice-profiles")
async def list_voice_profiles():
    """List all available voice profiles."""
    from app.services.voice_profile_builder import list_voice_profiles as _list
    return {"profiles": _list()}


@router.delete("/voice-profiles/{anchor_name}")
async def delete_voice_profile(anchor_name: str):
    """Delete a voice profile."""
    from app.services.voice_profile_builder import _PROFILE_DIR
    safe_name = anchor_name.replace("/", "_").replace("\\", "_")
    path = _PROFILE_DIR / f"{safe_name}.npy"
    if not path.exists():
        raise HTTPException(status_code=404, detail="声纹档案不存在")
    path.unlink()
    return {"deleted": True, "anchor_name": anchor_name}


# ── Guard: only one batch retranscribe at a time ──
_batch_retranscribe_running = False

@router.post("/batch-retranscribe")
async def batch_retranscribe(
    anchor_name: str = Query(..., description="Anchor name to retranscribe"),
    db: AsyncSession = Depends(get_db),
):
    """Kick off async batch re-transcription. Returns task_id immediately."""
    global _batch_retranscribe_running
    if _batch_retranscribe_running:
        raise HTTPException(status_code=409, detail="已有批量转写任务在执行中，请等待完成后再试")

    # Find persona_id from task_records for this anchor
    from app.models.task_record import TaskRecord as _TR
    persona_id = None
    tr_row = (await db.execute(
        select(_TR.persona_id).where(_TR.anchor_name == anchor_name, _TR.persona_id.isnot(None)).limit(1)
    )).scalar_one_or_none()
    if tr_row:
        persona_id = str(tr_row)

    from app.services.voice_profile_builder import load_voice_profile
    profile = await asyncio.get_event_loop().run_in_executor(None, lambda: load_voice_profile(anchor_name, persona_id=persona_id))

    rows = (
        await db.execute(
            select(Asset).where(
                Asset.anchor_name == anchor_name,
                Asset.asset_type == AssetType.audio,
            )
        )
    ).scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"未找到主播 '{anchor_name}' 的音频资产")

    backend_dir = Path(__file__).resolve().parent.parent.parent
    audio_items = []
    for r in rows:
        p = Path(r.file_path)
        if not p.is_absolute():
            p = backend_dir / r.file_path
        if p.exists():
            audio_items.append({"asset_id": str(r.id), "file_path": str(p), "title": r.video_title, "task_id": r.task_id})

    if not audio_items:
        raise HTTPException(status_code=404, detail="音频文件在磁盘上不存在")

    task_id = str(uuid.uuid4())
    tr = TaskRecord(
        task_id=task_id,
        trigger="batch_retranscribe",
        url="",
        anchor_name=anchor_name,
        status="running",
        video_count=len(audio_items),
    )
    db.add(tr)
    await db.commit()

    # Snapshot items for the background thread (detached from session)
    import copy
    items_snapshot = copy.deepcopy(audio_items)

    def _bg_run():
        """Background thread: process audios one at a time (GPU-safe)."""
        global _batch_retranscribe_running
        try:
            total = len(items_snapshot)
            progress_counter = [0]
            progress_lock = _threading.Lock()

            def _process_one(idx: int, item: dict):
                try:
                    logger.info("[BatchRetranscribe] [%d/%d] Starting: %s", idx + 1, total, item["title"][:40])
                    audio_path = item["file_path"]

                    from app.services.audio_processor import separate_vocals
                    vocals_path = separate_vocals(audio_path)
                    if vocals_path != audio_path:
                        audio_path = vocals_path

                    worker = Path(__file__).resolve().parent.parent / "services" / "asr_worker.py"
                    proc = subprocess.Popen(
                        [_venv_python(), str(worker), audio_path],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        encoding="utf-8", errors="replace",
                    )
                    result_data = None
                    last_progress = {}
                    try:
                        for line in proc.stdout:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                d = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            phase = d.get("phase")
                            if phase == "done":
                                result_data = d
                            elif phase == "transcribing":
                                last_progress = d
                                pct = d.get("progress_pct", 0)
                                msg = d.get("message", "")
                                _update_task_result_summary(task_id, {
                                    "current_step": "transcribing",
                                    "message": f"[{idx + 1}/{total}] {msg}",
                                    "progress_pct": min(10 + round(pct * 0.8), 90),
                                })
                            elif phase == "loading_model":
                                _update_task_result_summary(task_id, {
                                    "current_step": "loading_model",
                                    "message": f"[{idx + 1}/{total}] 加载语音模型...",
                                    "progress_pct": 5,
                                })
                            elif d.get("error"):
                                raise RuntimeError(d["error"])
                        proc.wait(timeout=600)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                        raise RuntimeError("ASR worker timed out after 600s")

                    stderr_output = proc.stderr.read() if proc.stderr else ""
                    if proc.returncode != 0:
                        err_msg = stderr_output[:300] if stderr_output else f"exit code {proc.returncode}"
                        logger.error("[BatchRetranscribe] Worker failed: %s", err_msg)
                        raise RuntimeError(f"ASR worker failed: {err_msg}")

                    if not result_data:
                        if stderr_output:
                            logger.warning("[BatchRetranscribe] No result, stderr: %s", stderr_output[:200])
                        raise RuntimeError("ASR 返回空结果")

                    segments = result_data.get("segments", [])

                    from app.services.audio_processor import SpeakerDiarizer
                    sd = SpeakerDiarizer()
                    dia_segs = sd.diarize(audio_path, anchor_name=anchor_name, persona_id=persona_id)
                    if dia_segs:
                        ref_used = sd.last_mode == "reference"
                        speaker_map = sd.map_speakers(dia_segs, reference_used=ref_used)
                        segments = sd.assign_speakers(dia_segs, segments, speaker_map)

                    labeled = [s for s in segments if s.get("speaker")]
                    if labeled:
                        text = _merge_speaker_lines(labeled)
                    else:
                        text = result_data["text"]

                    _update_transcript(item["asset_id"], item["task_id"], item["title"], text)
                    logger.info("[BatchRetranscribe] [%d/%d] Done: %s (%d chars)",
                                idx + 1, total, item["title"][:30], len(text))

                except Exception as e:
                    logger.error("[BatchRetranscribe] [%d/%d] Failed: %s - %s", idx + 1, total, item["title"][:30], e)

                finally:
                    with progress_lock:
                        progress_counter[0] += 1
                        _update_task_progress(task_id, progress_counter[0], total)

            # Sequential execution — GPU can only handle one model at a time
            for idx, item in enumerate(items_snapshot):
                _process_one(idx, item)

            _update_task_progress(task_id, total, total, done=True)
        finally:
            _batch_retranscribe_running = False

    def _update_transcript(asset_id: str, task_id: str, title: str, text: str):
        """Update transcript in DB — create transcript asset if none exists."""
        try:
            import asyncio as _aio
            import asyncpg as _apg
            from app.core.config import settings

            async def _do():
                url = settings.DATABASE_URL.replace("+asyncpg", "")
                conn = await _apg.connect(url)
                try:
                    # Find audio asset's task_id and video_title
                    row = await conn.fetchrow(
                        "SELECT task_id, video_title, anchor_name FROM assets WHERE id = $1::uuid",
                        asset_id,
                    )
                    if not row:
                        logger.warning("[BatchRetranscribe] Asset not found: %s", asset_id)
                        return
                    tid, vtitle, anchor = row["task_id"], row["video_title"], row["anchor_name"]

                    # Look for existing transcript asset
                    existing = await conn.fetchrow(
                        "SELECT id FROM assets WHERE task_id = $1 AND video_title = $2 AND asset_type = 'transcript'",
                        tid, vtitle,
                    )
                    if existing:
                        await conn.execute(
                            "UPDATE assets SET transcription_text = $1 WHERE id = $2::uuid",
                            text, str(existing["id"]),
                        )
                        logger.info("[BatchRetranscribe] Updated existing transcript: %s (%d chars)", vtitle[:30], len(text))
                    else:
                        # Create new transcript asset
                        await conn.execute(
                            """INSERT INTO assets (id, task_id, anchor_name, video_title, asset_type, file_path, file_size, duration, transcription_text)
                               VALUES (gen_random_uuid(), $1, $2, $3, 'transcript', '', 0, 0, $4)""",
                            tid, anchor, vtitle, text,
                        )
                        logger.info("[BatchRetranscribe] Created new transcript: %s (%d chars)", vtitle[:30], len(text))
                finally:
                    await conn.close()

            _aio.run(_do())
        except Exception as e:
            logger.error("[BatchRetranscribe] DB update failed: %s", e)

    def _update_task_progress(tid: str, current: int, total: int, done: bool = False):
        """Update TaskRecord progress using asyncpg directly."""
        try:
            import asyncio as _aio
            import asyncpg as _apg
            from app.core.config import settings

            async def _do():
                url = settings.DATABASE_URL.replace("+asyncpg", "")
                conn = await _apg.connect(url)
                try:
                    status = "completed" if done else "running"
                    summary = {"current_step": "done" if done else "transcribing",
                               "message": f"已完成 {current}/{total}" if done else f"正在处理 {current}/{total}",
                               "progress_pct": 100 if done else min(10 + round((current / max(total, 1)) * 85), 95)} if total > 0 else None
                    await conn.execute(
                        "UPDATE task_records SET downloaded_count = $1, transcribed_count = $2, status = $3, result_summary = $4 WHERE task_id = $5",
                        current, current, status, json.dumps(summary) if summary else None, tid,
                    )
                finally:
                    await conn.close()

            _aio.run(_do())
        except Exception as e:
            logger.error("[BatchRetranscribe] Progress update failed: %s", e)

    def _update_task_result_summary(tid: str, summary: dict):
        """Update TaskRecord result_summary using asyncpg."""
        try:
            import asyncio as _aio
            import asyncpg as _apg
            from app.core.config import settings

            async def _do():
                url = settings.DATABASE_URL.replace("+asyncpg", "")
                conn = await _apg.connect(url)
                try:
                    await conn.execute(
                        "UPDATE task_records SET result_summary = $1 WHERE task_id = $2",
                        json.dumps(summary), tid,
                    )
                finally:
                    await conn.close()

            _aio.run(_do())
        except Exception as e:
            logger.error("[BatchRetranscribe] Result summary update failed: %s", e)

    # Launch background thread
    _batch_retranscribe_running = True
    import threading
    t = threading.Thread(target=_bg_run, daemon=True)
    t.start()

    return {
        "status": "started",
        "task_id": task_id,
        "anchor_name": anchor_name,
        "total": len(audio_items),
        "voice_profile_used": profile is not None,
    }


@router.get("/batch-retranscribe-status")
async def batch_retranscribe_status(
    task_id: str = Query(..., description="Task ID from batch-retranscribe"),
    db: AsyncSession = Depends(get_db),
):
    """Poll batch retranscription progress."""
    row = (await db.execute(
        select(TaskRecord).where(TaskRecord.task_id == task_id)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": row.task_id,
        "status": row.status,
        "anchor_name": row.anchor_name,
        "total": row.video_count,
        "progress": row.downloaded_count or 0,
        "error_message": row.error_message,
        "result_summary": row.result_summary,
    }


# ── Asset CRUD ──

@router.get("", response_model=AssetListOut)
async def list_assets(
    keyword: str = Query(default="", description="Search anchor_name, video_title, transcription_text"),
    anchor_name: str = Query(default="", description="Filter by anchor name (partial match)"),
    task_id: str = Query(default="", description="Filter by task ID"),
    asset_type: str = Query(default="", description="Filter: video / audio / transcript"),
    date_from: str = Query(default="", description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(default="", description="End date (YYYY-MM-DD)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all assets with optional filters and pagination."""
    q = select(Asset)
    count_q = select(func.count(Asset.id))

    if keyword:
        kw = f"%{keyword}%"
        q = q.where(
            (Asset.anchor_name.ilike(kw))
            | (Asset.video_title.ilike(kw))
            | (Asset.transcription_text.ilike(kw))
        )
        count_q = count_q.where(
            (Asset.anchor_name.ilike(kw))
            | (Asset.video_title.ilike(kw))
            | (Asset.transcription_text.ilike(kw))
        )
    if anchor_name:
        q = q.where(Asset.anchor_name.ilike(f"%{anchor_name}%"))
        count_q = count_q.where(Asset.anchor_name.ilike(f"%{anchor_name}%"))
    if task_id:
        q = q.where(Asset.task_id == task_id)
        count_q = count_q.where(Asset.task_id == task_id)
    if asset_type:
        q = q.where(Asset.asset_type == asset_type)
        count_q = count_q.where(Asset.asset_type == asset_type)
    if date_from:
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d")
            q = q.where(Asset.created_at >= df)
            count_q = count_q.where(Asset.created_at >= df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            q = q.where(Asset.created_at < dt)
            count_q = count_q.where(Asset.created_at < dt)
        except ValueError:
            pass

    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        (await db.execute(
            q.order_by(Asset.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ))
        .scalars()
        .all()
    )

    items = []
    for r in rows:
        d = {
            "id": str(r.id),
            "task_id": r.task_id,
            "anchor_name": r.anchor_name,
            "video_title": r.video_title,
            "asset_type": r.asset_type.value if hasattr(r.asset_type, "value") else str(r.asset_type),
            "file_path": r.file_path,
            "file_size": r.file_size,
            "duration": r.duration,
            "transcription_text": r.transcription_text,
            "video_url": _make_video_url(r.file_path),
        }
        items.append(AssetOut(**d))

    return AssetListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=AssetDetailOut)
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single asset with full transcription text."""
    try:
        uid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的资产 ID")

    row = (await db.execute(select(Asset).where(Asset.id == uid))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    return AssetDetailOut(
        id=str(row.id),
        task_id=row.task_id,
        anchor_name=row.anchor_name,
        video_title=row.video_title,
        asset_type=row.asset_type.value if hasattr(row.asset_type, "value") else str(row.asset_type),
        file_path=row.file_path,
        file_size=row.file_size,
        duration=row.duration,
        transcription_text=row.transcription_text,
        video_url=_make_video_url(row.file_path),
    )


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an asset and its file, then return the deleted asset info."""
    try:
        uid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的资产 ID")

    row = (await db.execute(select(Asset).where(Asset.id == uid))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    # Delete file from disk — only if no other asset references the same file
    if row.file_path:
        try:
            from sqlalchemy import func as sa_func
            ref_count = (await db.execute(
                select(func.count()).select_from(Asset).where(
                    Asset.file_path == row.file_path,
                    Asset.id != uid,
                )
            )).scalar() or 0

            if ref_count > 0:
                logger.info("文件被其他资产引用(%d条)，保留: %s", ref_count, row.file_path)
            else:
                file_p = Path(row.file_path)
                if file_p.exists():
                    file_p.unlink()
                    logger.info("已删除文件: %s", row.file_path)
                else:
                    logger.warning("文件不存在，跳过删除: %s", row.file_path)
                # Also clean up companion files (e.g., .mp4 for .wav, or .wav for .mp4)
                for companion in [file_p.with_suffix(".mp4"), file_p.with_suffix(".wav")]:
                    if companion != file_p and companion.exists():
                        companion.unlink()
        except OSError as e:
            logger.warning("Failed to delete asset file: %s", e)

    result = {
        "id": str(row.id),
        "task_id": row.task_id,
        "asset_type": row.asset_type.value if hasattr(row.asset_type, "value") else str(row.asset_type),
        "deleted": True,
    }

    await db.execute(delete(Asset).where(Asset.id == uid))
    await db.commit()
    _invalidate_group_stats_cache()

    return result


@router.post("/cleanup-orphan-files")
async def cleanup_orphan_files(db: AsyncSession = Depends(get_db)):
    """Scan uploads/ and delete files not referenced by any asset record."""
    uploads_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
    if not uploads_dir.exists():
        return {"deleted_count": 0, "freed_bytes": 0, "errors": []}

    # Collect all file_path values from DB
    rows = (await db.execute(select(Asset.file_path))).scalars().all()
    db_paths = set()
    for p in rows:
        if p:
            db_paths.add(str(Path(p).resolve()))

    deleted_count = 0
    freed_bytes = 0
    errors: list[str] = []

    for fp in uploads_dir.rglob("*"):
        if not fp.is_file():
            continue
        resolved = str(fp.resolve())
        if resolved in db_paths:
            continue
        # Skip lock/temp files
        if fp.suffix in (".lock", ".tmp", ".bak"):
            continue
        try:
            size = fp.stat().st_size
            fp.unlink()
            deleted_count += 1
            freed_bytes += size
            logger.info("Cleaned orphan file: %s (%d bytes)", fp, size)
        except OSError as e:
            errors.append(f"{fp}: {e}")

    return {"deleted_count": deleted_count, "freed_bytes": freed_bytes, "errors": errors}


# ── In-memory cache for group-stats (TTL 60s) ──
_group_stats_cache: tuple[float, list[GroupStatsItem]] | None = None
_GROUP_STATS_TTL = 60.0


def _invalidate_group_stats_cache():
    global _group_stats_cache
    _group_stats_cache = None


@router.get("/stats/group-stats", response_model=list[GroupStatsItem])
async def group_stats(db: AsyncSession = Depends(get_db)):
    """Return asset counts grouped by anchor_name, enriched with persona info."""
    global _group_stats_cache
    if _group_stats_cache and (time.monotonic() - _group_stats_cache[0]) < _GROUP_STATS_TTL:
        return _group_stats_cache[1]

    # Group assets by anchor_name with type counts and total size
    rows = (
        await db.execute(
            select(
                Asset.anchor_name,
                func.count().filter(Asset.asset_type == AssetType.video).label("video_count"),
                func.count().filter(Asset.asset_type == AssetType.audio).label("audio_count"),
                func.count().filter(Asset.asset_type == AssetType.transcript).label("transcript_count"),
                func.sum(Asset.file_size).label("total_size"),
            )
            .where(Asset.anchor_name != "")
            .group_by(Asset.anchor_name)
            .order_by(Asset.anchor_name)
        )
    ).all()

    # Build persona lookup: anchor_name -> (persona_id, persona_name)
    # via TaskRecord.persona_id -> Persona
    persona_map: dict[str, tuple[str | None, str | None]] = {}
    tr_rows = (
        await db.execute(
            select(TaskRecord.anchor_name, TaskRecord.persona_id, TaskRecord.persona_name)
            .where(TaskRecord.persona_id.isnot(None))
            .distinct(TaskRecord.anchor_name)
        )
    ).all()
    for tr in tr_rows:
        persona_map.setdefault(tr.anchor_name, (tr.persona_id, tr.persona_name))

    # Also check Persona.source_anchor_name
    p_rows = (
        await db.execute(
            select(Persona.id, Persona.name, Persona.source_anchor_name)
            .where(Persona.source_anchor_name.isnot(None))
        )
    ).all()
    for p in p_rows:
        if p.source_anchor_name and p.source_anchor_name not in persona_map:
            persona_map[p.source_anchor_name] = (str(p.id), p.name)

    result = []
    for r in rows:
        pid, pname = persona_map.get(r.anchor_name, (None, None))
        result.append(GroupStatsItem(
            anchor_name=r.anchor_name,
            persona_id=pid,
            persona_name=pname,
            video_count=r.video_count or 0,
            audio_count=r.audio_count or 0,
            transcript_count=r.transcript_count or 0,
            total_size=int(r.total_size or 0),
        ))

    _group_stats_cache = (time.monotonic(), result)
    return result


@router.patch("/{asset_id}", response_model=AssetDetailOut)
async def update_asset(
    asset_id: str,
    body: AssetUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    """Update transcription_text of an asset."""
    try:
        uid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的资产 ID")

    row = (await db.execute(select(Asset).where(Asset.id == uid))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")

    row.transcription_text = body.transcription_text
    await db.commit()
    _invalidate_group_stats_cache()
    await db.refresh(row)

    return AssetDetailOut(
        id=str(row.id),
        task_id=row.task_id,
        anchor_name=row.anchor_name,
        video_title=row.video_title,
        asset_type=row.asset_type.value if hasattr(row.asset_type, "value") else str(row.asset_type),
        file_path=row.file_path,
        file_size=row.file_size,
        duration=row.duration,
        transcription_text=row.transcription_text,
        video_url=_make_video_url(row.file_path),
    )


@router.post("/{asset_id}/retranscribe")
async def retranscribe_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Re-run vocal separation + ASR on an audio asset, update linked transcript.
    Returns task_id immediately; progress is polled via GET /api/task-records/{task_id}.
    """
    try:
        uid = uuid.UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的资产 ID")

    row = (await db.execute(select(Asset).where(Asset.id == uid))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="资产不存在")
    if row.asset_type != AssetType.audio:
        raise HTTPException(status_code=400, detail="仅支持对音频资产重新识别")

    file_path = Path(row.file_path)
    if not file_path.is_absolute():
        backend_dir = Path(__file__).resolve().parent.parent.parent
        file_path = backend_dir / row.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"音频文件不存在: {row.file_path}")

    tr = TaskRecord(
        task_id=str(uuid.uuid4()),
        trigger="retranscribe",
        url="",
        anchor_name=row.anchor_name,
        status="running",
        video_count=1,
    )
    db.add(tr)
    await db.commit()
    _invalidate_group_stats_cache()
    task_id = tr.task_id
    anchor_name = row.anchor_name
    video_title = row.video_title
    existing_task_id = row.task_id

    asyncio.create_task(
        _retranscribe_background(task_id, asset_id, anchor_name, video_title, existing_task_id, file_path)
    )

    return {"task_id": task_id}


async def _retranscribe_background(
    task_id: str, asset_id: str, anchor_name: str, video_title: str, existing_task_id: str, file_path: Path,
):
    """Background coroutine that runs retranscription with live progress updates."""
    loop = asyncio.get_event_loop()

    async def _update_progress(progress: dict):
        async with async_session_factory() as session:
            tr = (await session.execute(select(TaskRecord).where(TaskRecord.task_id == task_id))).scalar_one_or_none()
            if tr:
                tr.result_summary = progress
                await session.commit()

    def _run() -> dict:
        audio_path = str(file_path)
        logger.info("[Retranscribe] Starting for %s", audio_path)

        # Step 1: vocal separation
        from app.services.audio_processor import separate_vocals
        vocals_path = separate_vocals(audio_path)
        if vocals_path != audio_path:
            logger.info("[Retranscribe] Using vocals: %s", vocals_path)
            audio_path = vocals_path

        # Step 2: ASR subprocess
        logger.info("[Retranscribe] Starting ASR...")
        worker = Path(__file__).resolve().parent.parent / "services" / "asr_worker.py"
        proc = subprocess.Popen(
            [_venv_python(), str(worker), audio_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",
        )
        result_data = None
        last_progress = {}
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                phase = d.get("phase")
                if phase == "transcribing":
                    last_progress = {
                        "step": "transcribing",
                        "progress_pct": d.get("progress_pct", 0),
                        "eta_seconds": d.get("eta_seconds"),
                        "segment_count": d.get("segment_count"),
                        "total_duration": d.get("total_duration"),
                        "message": d.get("message", ""),
                    }
                    asyncio.run_coroutine_threadsafe(_update_progress(last_progress), loop).result(timeout=5)
                elif phase == "loading_model":
                    asyncio.run_coroutine_threadsafe(
                        _update_progress({"step": "loading_model", "message": "正在加载语音模型..."}), loop
                    ).result(timeout=5)
                if phase == "done":
                    result_data = d
                elif d.get("error"):
                    raise RuntimeError(d["error"])
            proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise RuntimeError("ASR worker timed out after 600s")

        stderr_output = proc.stderr.read() if proc.stderr else ""
        if proc.returncode != 0:
            err_msg = stderr_output[:300] if stderr_output else f"exit code {proc.returncode}"
            logger.error("[Retranscribe] Worker failed: %s", err_msg)
            raise RuntimeError(f"ASR worker failed: {err_msg}")

        if not result_data:
            raise RuntimeError("ASR 返回空结果")

        segments = result_data.get("segments", [])

        # Step 3: speaker diarization
        try:
            from app.services.audio_processor import SpeakerDiarizer
            sd = SpeakerDiarizer()
            dia_segs = sd.diarize(audio_path, anchor_name=anchor_name)
            if dia_segs:
                ref_used = sd.last_mode == "reference"
                speaker_map = sd.map_speakers(dia_segs, reference_used=ref_used)
                segments = sd.assign_speakers(dia_segs, segments, speaker_map)
                logger.info("[Retranscribe] Speaker diarization (%s): %s", sd.last_mode, speaker_map)
        except Exception as _e:
            logger.warning("[Retranscribe] Speaker diarization skipped: %s", _e)

        labeled_segments = [s for s in segments if s.get("speaker")]
        if labeled_segments:
            text = _merge_speaker_lines(labeled_segments)
        else:
            text = result_data["text"]

        logger.info("[Retranscribe] Returning text_len=%d, segments=%d", len(text), len(segments))
        return {"text": text, "duration": result_data.get("duration", 0), "segments": segments}

    try:
        result = await loop.run_in_executor(None, _run)
        logger.info("[Retranscribe] _run completed, text_len=%d", len(result.get("text", "")))

        async with async_session_factory() as session:
            transcript_row = (
                await session.execute(
                    select(Asset).where(
                        Asset.task_id == existing_task_id,
                        Asset.video_title == video_title,
                        Asset.asset_type == AssetType.transcript,
                    )
                )
            ).scalar_one_or_none()

            if transcript_row:
                transcript_row.transcription_text = result["text"]
                logger.info("[Retranscribe] Updated existing transcript asset")
            else:
                new_transcript = Asset(
                    task_id=existing_task_id,
                    anchor_name=anchor_name,
                    video_title=video_title,
                    asset_type=AssetType.transcript,
                    file_path="",
                    file_size=0,
                    duration=result.get("duration", 0),
                    transcription_text=result["text"],
                )
                session.add(new_transcript)
                logger.info("[Retranscribe] Created new transcript asset")

            tr = (await session.execute(select(TaskRecord).where(TaskRecord.task_id == task_id))).scalar_one_or_none()
            if tr:
                tr.status = "completed"
                tr.downloaded_count = 1
                tr.transcribed_count = 1
                tr.result_summary = {
                    "step": "done",
                    "progress_pct": 100,
                    "transcription_text": result["text"],
                    "duration": result["duration"],
                }
            await session.commit()
        logger.info("[Retranscribe] All saved successfully")
    except Exception as e:
        logger.error("[Retranscribe] Failed: %s", e)
        async with async_session_factory() as session:
            tr = (await session.execute(select(TaskRecord).where(TaskRecord.task_id == task_id))).scalar_one_or_none()
            if tr:
                tr.status = "failed"
                tr.error_message = str(e)
                tr.result_summary = {"step": "failed", "message": str(e)}
                await session.commit()
# force reload

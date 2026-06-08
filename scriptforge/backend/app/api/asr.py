import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asr", tags=["ASR"])

UPLOAD_DIR = Path("./uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...), language: str | None = None):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 500MB)")

    file_id = uuid.uuid4().hex
    suffix = Path(file.filename or "audio.mp3").suffix
    save_path = UPLOAD_DIR / f"{file_id}{suffix}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from app.services.asr import asr_engine
        result = await asyncio.to_thread(asr_engine.transcribe, str(save_path), language=language)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        save_path.unlink(missing_ok=True)

    return {
        "text": result.text,
        "segments": result.segments,
        "duration": result.duration,
    }


async def _batch_transcribe_background(task_id: str, file_paths: list[str], language: str | None):
    """Background task for batch transcription."""
    from app.core.database import async_session_factory
    from app.models.task_record import TaskRecord
    from sqlalchemy import select

    results = []
    for i, path in enumerate(file_paths):
        try:
            from app.services.asr import asr_engine
            result = await asyncio.to_thread(asr_engine.transcribe, path, language=language)
            results.append({
                "file": path,
                "text": result.text,
                "segments": result.segments,
                "duration": result.duration,
            })
        except Exception as e:
            logger.error("Failed to transcribe %s: %s", path, e)
            results.append({"file": path, "error": str(e)})
        finally:
            Path(path).unlink(missing_ok=True)

        # Update progress
        try:
            async with async_session_factory() as session:
                row = (await session.execute(
                    select(TaskRecord).where(TaskRecord.task_id == task_id)
                )).scalar_one_or_none()
                if row:
                    row.result_summary = {"current": i + 1, "total": len(file_paths)}
                    await session.commit()
        except Exception:
            pass

    # Mark completed
    try:
        async with async_session_factory() as session:
            row = (await session.execute(
                select(TaskRecord).where(TaskRecord.task_id == task_id)
            )).scalar_one_or_none()
            if row:
                row.status = "completed"
                row.result_summary = {"results": results}
                await session.commit()
    except Exception:
        pass


@router.post("/batch")
async def batch_transcribe(files: list[UploadFile] = File(...), language: str | None = None):
    from app.core.database import async_session_factory
    from app.models.task_record import TaskRecord

    file_paths: list[str] = []
    saved_files: list[Path] = []

    for upload in files:
        file_id = uuid.uuid4().hex
        suffix = Path(upload.filename or "audio.mp3").suffix
        save_path = UPLOAD_DIR / f"{file_id}{suffix}"
        with open(save_path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        file_paths.append(str(save_path))
        saved_files.append(save_path)

    task_id = str(uuid.uuid4())

    # Create TaskRecord
    async with async_session_factory() as session:
        record = TaskRecord(task_id=task_id, trigger="batch_transcribe", url="", status="running")
        session.add(record)
        await session.commit()

    asyncio.create_task(_batch_transcribe_background(task_id, file_paths, language))

    return {"task_id": task_id, "status": "pending", "file_count": len(files)}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    from sqlalchemy import select
    from app.core.database import get_db
    from app.models.task_record import TaskRecord

    async for db in get_db():
        row = (await db.execute(
            select(TaskRecord).where(TaskRecord.task_id == task_id)
        )).scalar_one_or_none()
        break

    if not row:
        return {"task_id": task_id, "status": "not_found"}

    if row.status == "running":
        rs = row.result_summary or {}
        return {
            "task_id": task_id,
            "status": "PROCESSING",
            "current": rs.get("current"),
            "total": rs.get("total"),
        }
    elif row.status == "completed":
        rs = row.result_summary or {}
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": rs.get("results", []),
        }
    else:
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": row.error_message or "任务失败",
        }

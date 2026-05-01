import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings

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


@router.post("/batch")
async def batch_transcribe(files: list[UploadFile] = File(...), language: str | None = None):
    from app.core.celery import celery_app
    from app.tasks.asr_tasks import batch_transcribe_task

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

    task = batch_transcribe_task.delay(file_paths, language=language)

    return {"task_id": task.id, "status": "pending", "file_count": len(files)}


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    from app.core.celery import celery_app

    result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)
    return response

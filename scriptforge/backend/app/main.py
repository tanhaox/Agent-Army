import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded as SlowAPIRateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from app.api import router
from app.core.limiter import limiter
from app.core.logger import setup_logging

setup_logging()
logger = logging.getLogger("scriptforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ScriptForge starting up")

    # Clean up zombie tasks left from previous run
    try:
        from app.core.database import async_session_factory
        from app.models.task_record import TaskRecord
        from sqlalchemy import update
        async with async_session_factory() as db:
            result = await db.execute(
                update(TaskRecord)
                .where(TaskRecord.status == "running")
                .values(status="failed", error_message="服务重启，任务中断")
            )
            await db.commit()
            if result.rowcount:
                logger.info("Cleaned %d zombie tasks from previous run", result.rowcount)
    except Exception as e:
        logger.warning("Zombie task cleanup skipped: %s", e)

    try:
        from app.services.vector_store import vector_store
        vector_store.ensure_collection()
    except Exception as e:
        logger.warning("ChromaDB init skipped: %s", e)

    # Model pre-checks (non-blocking)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(backend_dir, "models")
    whisper_dir = os.path.join(models_dir, "whisper")
    hf_dir = os.path.join(models_dir, "huggingface")
    if not os.path.isdir(whisper_dir):
        logger.warning("Whisper model directory not found: %s — ASR will download on first use", whisper_dir)
    else:
        logger.info("Whisper model directory OK: %s", whisper_dir)
    if not os.path.isdir(hf_dir):
        logger.warning("HuggingFace cache directory not found: %s — embedding may download on first use", hf_dir)

    # Start watchdog daemon — kills zombie tasks/orphan processes every 30 min
    try:
        from app.core.watchdog import start_watchdog
        start_watchdog()
    except Exception as e:
        logger.warning("Watchdog start failed: %s", e)

    yield
    logger.info("ScriptForge shutting down")
    try:
        from app.services.deepseek_client import close_deepseek_client
        await close_deepseek_client()
    except Exception as e:
        logger.warning("DeepSeek client shutdown failed: %s", e)


app = FastAPI(title="ScriptForge", version="0.3.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.security import ApiKeyMiddleware
app.add_middleware(ApiKeyMiddleware)

app.include_router(router, prefix="/api")

# Serve uploaded video/audio files
_uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(os.path.join(_uploads_dir, "videos"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


# ── Error handlers ─────────────────────────────────────────────

@app.exception_handler(SlowAPIRateLimitExceeded)
async def rate_limit_handler(request: Request, exc: SlowAPIRateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试"},
    )


@app.get("/api")
@app.get("/api/")
async def api_index():
    return {
        "name": "ScriptForge API",
        "version": "0.3.0",
        "endpoints": {
            "health": "GET /api/health",
            "asr": {
                "transcribe": "POST /api/asr/transcribe",
                "batch": "POST /api/asr/batch",
                "task_status": "GET /api/asr/task/{task_id}",
            },
            "persona": {
                "analyze": "POST /api/persona/analyze",
                "get": "GET /api/persona/{persona_id}",
                "list": "GET /api/persona/",
            },
            "scripts": {
                "generate": "POST /api/scripts/generate",
                "get": "GET /api/scripts/{script_id}",
                "list": "GET /api/scripts/",
                "update": "PATCH /api/scripts/{script_id}",
                "archive": "DELETE /api/scripts/{script_id}",
                "regenerate": "POST /api/scripts/{script_id}/regenerate",
            },
            "docs": "GET /docs",
        },
    }

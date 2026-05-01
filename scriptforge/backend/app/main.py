import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
    try:
        from app.services.vector_store import vector_store
        vector_store.ensure_collection()
    except Exception as e:
        logger.warning("ChromaDB init skipped: %s", e)
    yield
    logger.info("ScriptForge shutting down")
    try:
        from app.services.deepseek_client import close_deepseek_client
        await close_deepseek_client()
    except Exception as e:
        logger.warning("DeepSeek client shutdown failed: %s", e)


app = FastAPI(title="ScriptForge", version="0.2.0", lifespan=lifespan)

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
        "version": "0.2.0",
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

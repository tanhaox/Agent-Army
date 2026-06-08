"""
FastAPI 应用入口。

所有路由在此注册，中间件在此配置。
"""

import logging
from contextlib import asynccontextmanager

import sqlalchemy as sa
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.characters import router as characters_router
from app.api.composition import router as composition_router
from app.api.narrative_trees import router as narrative_trees_router
from app.api.projects import router as projects_router
from app.api.scripts import router as scripts_router
from app.api.storyboards import router as storyboards_router
from app.api.system_settings import router as system_settings_router
from app.api.reference_images import router as reference_images_router
from app.api.tts import router as tts_router
from app.api.video_tasks import router as video_tasks_router
from app.api.visual_styles import router as visual_styles_router
from app.api.visual_templates import router as visual_templates_router
from app.core.config import get_settings
from app.core.rate_limit import limiter

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()


async def _check_deepseek() -> dict[str, str]:
    """检查 DeepSeek API 是否可达。"""
    if not settings.DEEPSEEK_API_KEY:
        return {"status": "not_configured", "detail": "API Key 未设置"}

    try:
        from openai import AsyncOpenAI
        async_client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=10.0,
        )
        await async_client.models.list()
        return {"status": "ok", "model": settings.DEEPSEEK_MODEL}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


@asynccontextmanager
async def lifespan(application: FastAPI):
    """应用生命周期：启动时确保静态文件目录存在，检查 DeepSeek 连接。"""
    from pathlib import Path

    # 确保静态文件目录
    static_dir = Path("static/characters")
    static_dir.mkdir(parents=True, exist_ok=True)
    Path("static/characters/candidates").mkdir(parents=True, exist_ok=True)
    Path("static/characters/angles").mkdir(parents=True, exist_ok=True)
    Path("static/compositions").mkdir(parents=True, exist_ok=True)
    Path("static/storyboards").mkdir(parents=True, exist_ok=True)
    Path("static/tts_cache").mkdir(parents=True, exist_ok=True)
    Path("static/videos").mkdir(parents=True, exist_ok=True)
    application.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("静态文件目录已挂载: /static")

    logger.info("LLM Provider: %s", settings.LLM_PROVIDER)

    if settings.DEEPSEEK_API_KEY:
        logger.info("DeepSeek 已配置: model=%s", settings.DEEPSEEK_MODEL)
    else:
        logger.warning("DeepSeek API Key 未配置，请在 .env 中设置 DEEPSEEK_API_KEY")

    yield

    # 关闭全局 HTTP 客户端
    from app.core.http_client import close_http_client
    await close_http_client()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI短剧批量生产系统后端API",
    lifespan=lifespan,
)

# 限流
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS：从配置读取允许的域名
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects_router)
app.include_router(scripts_router)
app.include_router(characters_router)
app.include_router(storyboards_router)
app.include_router(system_settings_router)
app.include_router(tts_router)
app.include_router(video_tasks_router)
app.include_router(reference_images_router)
app.include_router(composition_router)
app.include_router(narrative_trees_router)
app.include_router(visual_styles_router)
app.include_router(visual_templates_router)


# 全局异常处理器：捕获未处理的 SQLAlchemy 和通用异常
from sqlalchemy.exc import SQLAlchemyError


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    """数据库异常统一处理。"""
    logger.error("数据库异常: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "数据库操作失败，请稍后重试"})


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """未捕获异常统一处理，防止 uvicorn 崩溃。"""
    logger.exception("未处理异常: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


@app.get("/health")
async def health(request: Request) -> dict:
    """健康检查端点，检查数据库和 Redis 连接。"""
    result = {
        "status": "ok",
        "service": "shortfilm-factory",
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
    }

    # 数据库检查
    try:
        from app.core.database import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
        result["database"] = "ok"
    except Exception as e:
        result["database"] = f"error: {e}"
        result["status"] = "degraded"

    # Redis 检查
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        r.ping()
        r.close()
        result["redis"] = "ok"
    except Exception as e:
        result["redis"] = f"error: {e}"
        result["status"] = "degraded"

    # DeepSeek 检查（非阻塞）
    result["deepseek"] = await _check_deepseek()

    return result


@app.get("/api/visual-presets")
async def list_visual_presets() -> list[dict]:
    """获取内置视觉预设风格列表。"""
    from app.services.visual_presets import list_presets
    return list_presets()


@app.get("/api/visual-presets/{preset_id}")
async def get_visual_preset(preset_id: str) -> dict:
    """获取单个视觉预设详情。"""
    from app.services.visual_presets import get_preset
    preset = get_preset(preset_id)
    if preset is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")
    return preset

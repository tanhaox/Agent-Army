"""FastAPI application entry point."""
from __future__ import annotations

import logging
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
# (BaseHTTPMiddleware removed — 纯 ASGI 中间件不需要它)

from .config import Config, load_config, set_config
from .database import init_db
from .models import AudioJob, Host, Voice, DirectorJob
from .routers import (
    articles, audio, comfyui, digital_human_video, director, hosts, jobs, library, personas, roles,
    scripts, tagging, tts_services, visual_render, voices,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    set_config(cfg)
    _config = cfg
    init_db(_config.app.database_url)
    # 注册 event loop 给 director_events 跨线程安全调度
    import asyncio
    from .services.director_events import set_event_loop
    set_event_loop(asyncio.get_running_loop())
    _seed_defaults()
    _cleanup_zombie_jobs()
    _cleanup_zombie_audio_jobs()
    _auto_cleanup_stale_jobs()
    # workflow SSOT 同步 (项目 → ComfyUI 运行时)
    try:
        from .services.workflow_sync import sync_workflows_on_startup

        results = sync_workflows_on_startup()
        logger.info("[lifespan] workflow_sync: %d entries", len(results))
    except Exception as exc:
        logger.warning("[lifespan] workflow_sync failed: %s", exc)
    yield
    # 退出时杀掉托管的 TTS 进程, 不留孤儿占显存
    try:
        from .services import gpu_service_manager

        if gpu_service_manager._manager is not None:
            gpu_service_manager._manager.shutdown()
    except Exception as exc:
        logger.warning("[lifespan] gpu_service_manager shutdown failed: %s", exc)


def _seed_defaults():
    """Seed default host and voice if they do not exist.

    2026-08-07 主路径转正: 默认音色 = 带 master 的 indextts 音色 (大学教授 2267aeae),
    fish laochen_default 已弃用不再重建。host 无 default_voice_id 或指向孤儿时,
    自动绑定到第一个带 master 的 indextts 音色 (保证 generate_audio 不落到 voice=None)。
    """
    from .database import get_session_maker

    Session = get_session_maker()
    if Session is None:
        return
    db = Session()
    try:
        host = db.query(Host).filter(Host.persona_key == "laochen").first()
        if not host:
            host = Host(
                name="老陈聊财经",
                persona_key="laochen",
                fixed_opening="大家好，欢迎收看老陈聊财经。",
                fixed_ending="关注我，看懂财经。",
            )
            db.add(host)
            db.flush()

        # 已弃用: fish laochen_default 不再自动重建。
        # 旧库若已存在同名 fish 音色(带 host_id), 删除以切断"默认走 fish"路径。
        stale_voice = db.query(Voice).filter(Voice.name == "laochen_default").first()
        if stale_voice and stale_voice.backend == "fish":
            db.delete(stale_voice)

        # host 默认音色自愈: 孤儿引用 / 未设置 → 绑定到带 master 的 indextts 音色
        needs_fix = host.default_voice_id is None
        if host.default_voice_id and not db.query(Voice).filter(Voice.id == host.default_voice_id).first():
            needs_fix = True
        if needs_fix:
            default_voice = (
                db.query(Voice)
                .filter(Voice.backend == "indextts", Voice.master_audio_path.isnot(None))
                .order_by(Voice.created_at)
                .first()
            )
            if default_voice:
                host.default_voice_id = default_voice.id

        db.commit()
    finally:
        db.close()


def _cleanup_zombie_jobs():
    """Reset zombie director jobs left in executing/planning after a restart.

    - planning → failed (alignment/LLM was interrupted)
    - executing with slots → reviewing (slots were planned but execution thread died)
    - executing without slots → failed
    """
    from .database import get_session_maker

    Session = get_session_maker()
    if Session is None:
        return
    db = Session()
    try:
        zombies = (
            db.query(DirectorJob)
            .filter(DirectorJob.status.in_(["executing", "planning"]))
            .all()
        )
        if not zombies:
            return
        for job in zombies:
            has_slots = len(job.slots) > 0
            if job.status == "planning":
                job.status = "failed"
                job.error_message = "服务重启时规划未完成，请重新创建任务"
            elif has_slots:
                job.status = "reviewing"
                job.error_message = None
            else:
                job.status = "failed"
                job.error_message = "服务重启时执行未完成，无 slots 可恢复"
        db.commit()
        logger.info("[lifespan] cleaned %d zombie director job(s)", len(zombies))
    finally:
        db.close()


def _cleanup_zombie_audio_jobs():
    """Reset zombie audio jobs stuck in pending/running after a restart.

    背景: 后端重启会杀掉 _do_tts 后台线程, 但 DB 里 AudioJob 仍标记
    pending/running → 永不完成, 前端 restoreAudioJobs 会一直"恢复订阅"
    这个死任务而不是新建, 且 director 台看不到音频 → 永远卡死.

    策略: 重启时把残留的 pending/running 复位为 failed (附错误原因),
    让用户重新触发生成. 不删记录, 保留可追溯的失败历史.
    """
    from .database import get_session_maker

    Session = get_session_maker()
    if Session is None:
        return
    db = Session()
    try:
        zombies = (
            db.query(AudioJob)
            .filter(AudioJob.status.in_(["pending", "running"]))
            .all()
        )
        if not zombies:
            return
        for job in zombies:
            job.status = "failed"
            job.error_message = "服务重启中断 TTS 任务，已标记失效，请重新生成音频"
        db.commit()
        logger.info("[lifespan] cleaned %d zombie audio job(s)", len(zombies))
    finally:
        db.close()


def _auto_cleanup_stale_jobs():
    """Auto-delete director jobs that never produced any video and are older than N days.

    Criteria:
    - No slot with status 'completed'
    - created_at older than config.defaults.job_auto_cleanup_days
    - Status in (failed, planning, reviewing) — not executing (safety)
    """
    from datetime import datetime, timezone, timedelta
    from .database import get_session_maker
    from .config import get_config

    cfg = get_config()
    days = cfg.defaults.job_auto_cleanup_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    Session = get_session_maker()
    if Session is None:
        return
    db = Session()
    try:
        candidates = (
            db.query(DirectorJob)
            .filter(
                DirectorJob.created_at < cutoff,
                DirectorJob.status.in_(["failed", "planning", "reviewing"]),
            )
            .all()
        )
        deleted = 0
        for job in candidates:
            # 检查是否有任何 completed slot
            has_completed = any(s.status == "completed" for s in job.slots)
            if not has_completed:
                db.delete(job)
                deleted += 1
                # 同步清理磁盘产物
                try:
                    comp_dir = Path(cfg.defaults.composition_output_root) / job.id
                    if comp_dir.exists():
                        shutil.rmtree(comp_dir, ignore_errors=True)
                    legacy_dir = Path(cfg.defaults.director_output_root) / job.id
                    if legacy_dir.exists():
                        shutil.rmtree(legacy_dir, ignore_errors=True)
                except Exception:
                    pass
        if deleted:
            db.commit()
            logger.info("[lifespan] auto-cleaned %d stale director job(s) (no output, >%d days)", deleted, days)
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Digital Human Pipeline", lifespan=lifespan)

    # Force no-cache on /web/ static files so browser always gets latest HTML
    # NOTE: 不能用 BaseHTTPMiddleware — 它会缓冲请求体导致大文件上传失败。
    # 改用纯 ASGI 中间件，仅修改响应头，不触碰请求体。
    class NoCacheWebMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or not scope.get("path", "").startswith("/web/"):
                await self.app(scope, receive, send)
                return

            async def send_with_no_cache(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"cache-control", b"no-store, no-cache, must-revalidate, max-age=0"))
                    headers.append((b"pragma", b"no-cache"))
                    headers.append((b"expires", b"0"))
                    message = {**message, "headers": headers}
                await send(message)

            await self.app(scope, receive, send_with_no_cache)

    app.add_middleware(NoCacheWebMiddleware)
    app.include_router(articles.router)
    app.include_router(scripts.router)
    app.include_router(audio.router)
    app.include_router(jobs.router)
    app.include_router(hosts.router)
    app.include_router(voices.router)
    app.include_router(comfyui.router)
    app.include_router(roles.router)
    app.include_router(digital_human_video.router)
    app.include_router(visual_render.router)
    app.include_router(director.router)
    app.include_router(library.router)
    app.include_router(tagging.router)
    app.include_router(personas.router)
    app.include_router(tts_services.router)

    # Convenience redirect: /api/templates → /api/visual-render/templates
    @app.get("/api/templates")
    def _redirect_templates():
        return RedirectResponse(url="/api/visual-render/templates", status_code=307)

    # favicon — 阻止浏览器每次请求都打 404
    @app.get("/favicon.ico")
    def _favicon():
        from fastapi.responses import Response
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<circle cx="16" cy="16" r="14" fill="#3b82f6"/>'
            '<text x="16" y="22" text-anchor="middle" font-size="18" fill="#fff">DH</text>'
            '</svg>'
        )
        return Response(content=svg, media_type="image/svg+xml")

    # parents[0] == app/, parents[1] == project root (digital_human/)
    web_dir = Path(__file__).absolute().parents[1] / "web"
    app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")
    return app


app = create_app()


# 默认端口由 54321 改为 54323 — 看板 P0-1 修复
# (2026-07-26 自检发现 54321 是 orphan socket,真实生产服务在 54323)
DEFAULT_PORT = 54323


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=DEFAULT_PORT,
        log_level="info",
    )

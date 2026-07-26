"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import Config, load_config, set_config
from .database import init_db
from .models import Host, Voice
from .routers import (
    articles, audio, comfyui, digital_human_video, hosts, jobs, roles, scripts, voices,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    set_config(cfg)
    _config = cfg
    init_db(_config.app.database_url)
    _seed_defaults()
    # workflow SSOT 同步 (项目 → ComfyUI 运行时)
    try:
        from .services.workflow_sync import sync_workflows_on_startup

        results = sync_workflows_on_startup()
        logger.info("[lifespan] workflow_sync: %d entries", len(results))
    except Exception as exc:
        logger.warning("[lifespan] workflow_sync failed: %s", exc)
    yield


def _seed_defaults():
    """Seed default host and voice if they do not exist."""
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

        voice = db.query(Voice).filter(Voice.name == "laochen_default").first()
        if not voice:
            voice = Voice(
                host_id=host.id,
                name="laochen_default",
                backend="fish",
                base_url_fish="http://127.0.0.1:7860",
                base_url_f5="http://127.0.0.1:7861",
            )
            db.add(voice)
            db.commit()

            if host.default_voice_id is None:
                host.default_voice_id = voice.id
                db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Digital Human Pipeline", lifespan=lifespan)
    app.include_router(articles.router)
    app.include_router(scripts.router)
    app.include_router(audio.router)
    app.include_router(jobs.router)
    app.include_router(hosts.router)
    app.include_router(voices.router)
    app.include_router(comfyui.router)
    app.include_router(roles.router)
    app.include_router(digital_human_video.router)

    # parents[0] == app/, parents[1] == project root (digital_human/)
    web_dir = Path(__file__).absolute().parents[1] / "web"
    app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")
    return app


app = create_app()

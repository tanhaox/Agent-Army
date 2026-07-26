"""Article router: CRUD + trigger rewrite."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db, get_session_maker
from ..models import Article, Host, Script
from ..schemas import ArticleCreate, ArticleOut, ArticleUpdate, RewriteRequest
from ..services.llm_service import LLMService
from ..services.script_parser import parse_script
from .jobs import _publish

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _project_dir_name(script_id: str, now: datetime | None = None) -> str:
    """Generate project directory name: YYYYMMDD_HHMMSS_{last6}."""
    now = now or datetime.now(timezone.utc)
    suffix = re.sub(r"[^a-zA-Z0-9]", "", script_id)[-6:]
    return now.strftime("%Y%m%d_%H%M%S_") + suffix


def _create_project_dirs(script_id: str, project_root: Path) -> Path:
    """Create project folder with audio/clips/materials subdirs."""
    projects_dir = project_root / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    project_dir = projects_dir / _project_dir_name(script_id)
    for sub in ("audio", "clips", "materials", "tmp"):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)
    return project_dir


def get_llm() -> LLMService:
    from ..main import get_config

    cfg = get_config()
    return LLMService(cfg.deepseek)


@router.post("", response_model=ArticleOut)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    article = Article(
        title=payload.title,
        source_url=payload.source_url,
        raw_text=payload.raw_text,
        status="pending",
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("", response_model=list[ArticleOut])
def list_articles(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.put("/{article_id}", response_model=ArticleOut)
def update_article(article_id: str, payload: ArticleUpdate, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if payload.title is not None:
        article.title = payload.title
    if payload.source_url is not None:
        article.source_url = payload.source_url
    if payload.raw_text is not None:
        article.raw_text = payload.raw_text
    db.commit()
    db.refresh(article)
    return article


@router.post("/{article_id}/rewrite")
def rewrite_article(
    article_id: str,
    request: RewriteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    job_id = article_id
    model_alias = request.model
    prompt_template = request.prompt_template or "laochen_default"

    def _do_rewrite():
        Session = get_session_maker()
        if Session is None:
            _publish(job_id, {"type": "rewrite_error", "error": "Database not initialized"})
            return
        db2 = Session()
        try:
            article = db2.query(Article).filter(Article.id == article_id).first()
            if not article:
                _publish(job_id, {"type": "rewrite_error", "error": "Article not found"})
                return

            host = db2.query(Host).filter(Host.persona_key == "laochen").first()
            host_id = host.id if host else None

            chunks: list[str] = []

            def _cb(chunk: str) -> None:
                chunks.append(chunk)
                _publish(job_id, {"type": "rewrite_chunk", "chunk": chunk})

            script_text = llm.rewrite_article(
                article.raw_text,
                prompt_template=prompt_template,
                model=model_alias,
                stream=True,
                chunk_callback=_cb,
            )

            script = Script(
                article_id=article.id,
                host_id=host_id,
                version=1,
                prompt_template=prompt_template,
                script_text=script_text,
                status="drafting",
            )
            db2.add(script)
            db2.commit()
            db2.refresh(script)

            project_root = Path(__file__).resolve().parents[2]
            project_dir = _create_project_dirs(script.id, project_root)
            script.project_dir = str(project_dir)
            db2.commit()
            db2.refresh(script)

            fixed_opening = host.fixed_opening if host else None
            fixed_ending = host.fixed_ending if host else None
            segments_data = parse_script(script_text, fixed_opening, fixed_ending)
            for seg_data in segments_data:
                from ..models import Segment

                db2.add(Segment(script_id=script.id, **seg_data))
            db2.commit()

            article.status = "rewritten"
            db2.commit()

            _publish(job_id, {"type": "rewrite_done", "script_id": script.id, "project_dir": str(project_dir)})
        except Exception as exc:
            try:
                article = db2.query(Article).filter(Article.id == article_id).first()
                if article:
                    article.status = "failed"
                    db2.commit()
            except Exception:
                pass
            _publish(job_id, {"type": "rewrite_error", "error": str(exc)})
        finally:
            db2.close()

    background_tasks.add_task(_do_rewrite)
    return {"job_id": job_id, "status": "started", "model": model_alias or "default"}

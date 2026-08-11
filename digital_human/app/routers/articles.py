"""Article router: CRUD + trigger rewrite."""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import db_session, get_db, get_session_maker
from ..models import Article, Host, Persona, Script

logger = logging.getLogger(__name__)
from ..schemas import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    FetchUrlRequest,
    FetchUrlResponse,
    RewriteRequest,
)
from ..services.llm_service import LLMService
from ..services.script_parser import parse_script
from ..services.url_fetcher import fetch_url
from .jobs import _publish

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ---------------------------------------------------------------------------
# List available rewrite prompt templates
# ---------------------------------------------------------------------------
@router.get("/prompt-templates")
def list_prompt_templates():
    """返回 config/ 下可用的洗稿提示词模板列表."""
    config_dir = Path(__file__).resolve().parents[2] / "config"
    templates = []
    if config_dir.exists():
        for f in sorted(config_dir.glob("*.txt")):
            # 排除非洗稿模板（如视觉导演）
            if f.stem.startswith("visual_director"):
                continue
            templates.append({
                "id": f.stem,
                "name": f.stem,
                "size": f.stat().st_size,
            })
    return templates


# ---------------------------------------------------------------------------
# Upload a new prompt template
# ---------------------------------------------------------------------------
@router.post("/prompt-templates/upload")
async def upload_prompt_template(
    name: str = Form(..., min_length=1, max_length=64),
    file: UploadFile = File(...),
):
    """上传新的洗稿提示词模板 .txt 文件到 config/ 目录."""
    # Sanitize name: only allow alphanumeric, underscore, hyphen
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip())
    if not safe_name:
        raise HTTPException(status_code=400, detail="模板名称无效")

    config_dir = Path(__file__).resolve().parents[2] / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    target = config_dir / f"{safe_name}.txt"

    if target.exists():
        raise HTTPException(status_code=409, detail=f"模板 '{safe_name}' 已存在，请先删除旧版")

    content = await file.read()
    # Ensure it's text
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件必须是 UTF-8 文本")

    target.write_text(text, encoding="utf-8")
    return {"id": safe_name, "name": safe_name, "size": target.stat().st_size}


# ---------------------------------------------------------------------------
# Rename a prompt template
# ---------------------------------------------------------------------------
@router.put("/prompt-templates/{template_id}")
def rename_prompt_template(template_id: str, new_name: str):
    """重命名洗稿提示词模板."""
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", template_id)
    if not safe_id:
        raise HTTPException(status_code=400, detail="模板 ID 无效")

    safe_new = re.sub(r"[^a-zA-Z0-9_\-]", "_", new_name.strip())
    if not safe_new:
        raise HTTPException(status_code=400, detail="新名称无效")

    config_dir = Path(__file__).resolve().parents[2] / "config"
    old_path = config_dir / f"{safe_id}.txt"
    new_path = config_dir / f"{safe_new}.txt"

    if not old_path.exists():
        raise HTTPException(status_code=404, detail=f"模板 '{safe_id}' 不存在")
    if new_path.exists():
        raise HTTPException(status_code=409, detail=f"模板 '{safe_new}' 已存在")

    old_path.rename(new_path)
    return {"ok": True, "old": safe_id, "new": safe_new}


# ---------------------------------------------------------------------------
# Delete a prompt template
# ---------------------------------------------------------------------------
@router.delete("/prompt-templates/{template_id}")
def delete_prompt_template(template_id: str):
    """删除指定的洗稿提示词模板."""
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", template_id)
    if not safe_id:
        raise HTTPException(status_code=400, detail="模板 ID 无效")

    config_dir = Path(__file__).resolve().parents[2] / "config"
    target = config_dir / f"{safe_id}.txt"

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"模板 '{safe_id}' 不存在")

    # Don't allow deleting built-in templates accidentally
    if safe_id == "laochen_default":
        raise HTTPException(status_code=403, detail="不允许删除内置模板")

    target.unlink()
    return {"ok": True, "deleted": safe_id}


@router.post("/fetch-url", response_model=FetchUrlResponse)
def fetch_url_endpoint(payload: FetchUrlRequest):
    result = fetch_url(payload.url)
    return result


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
    from ..config import get_config

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

    job_id = str(uuid.uuid4())
    model_alias = request.model
    prompt_template = request.prompt_template or "laochen_default"
    video_format = request.video_format or "portrait"
    perspective = request.perspective

    def _do_rewrite():
        if get_session_maker() is None:
            _publish(job_id, {"type": "rewrite_error", "error": "Database not initialized"})
            return
        with db_session() as db2:
            try:
                article = db2.query(Article).filter(Article.id == article_id).first()
                if not article:
                    _publish(job_id, {"type": "rewrite_error", "error": "Article not found"})
                    return

                # 数字人绑定 (2026-08-08): 洗稿不再强制 laochen.
                # 人物即账号: 前端显式 persona_id → host_id → config 默认 → 首个 host 回退.
                # persona_id 解析出的 host 同时带出品牌/开结尾, 随 script.host_id 贯通
                # audio / HF 品牌注入 / C 线出镜.
                host = None
                persona: Persona | None = None
                if request.persona_id:
                    persona = db2.query(Persona).filter(Persona.id == request.persona_id).first()
                    if not persona:
                        _publish(job_id, {"type": "rewrite_error", "error": "Persona not found"})
                        return
                    host = db2.query(Host).filter(Host.id == persona.host_id).first() if persona.host_id else None
                    # 人物即账号: persona 自带提示词模板, 覆盖请求里的 prompt_template
                    # (选"老谭聊科技" → 用 laotan-tech, 而不是前端模板下拉的独立值)
                    if persona.prompt_template:
                        prompt_template = persona.prompt_template
                if host is None and request.host_id:
                    host = db2.query(Host).filter(Host.id == request.host_id).first()
                    if not host:
                        _publish(job_id, {"type": "rewrite_error", "error": "Host not found"})
                        return
                if host is None and request.persona_id:
                    # persona 已显式指定但未绑 host: 视为绑定失败, 不让老陈兜底冒名顶替
                    _publish(job_id, {"type": "rewrite_error", "error": "Persona has no bound host"})
                    return
                if host is None:
                    from ..config import get_config

                    try:
                        cfg = get_config()
                        default_key = cfg.defaults.host_id if cfg.defaults else "laochen"
                    except Exception:
                        default_key = "laochen"
                    host = (
                        db2.query(Host).filter(Host.persona_key == default_key).first()
                        or db2.query(Host).order_by(Host.created_at).first()
                    )
                host_id = host.id if host else None

                chunks: list[str] = []

                def _cb(chunk: str) -> None:
                    chunks.append(chunk)
                    _publish(job_id, {"type": "rewrite_chunk", "chunk": chunk})

                # 保存补充观点到 article
                if perspective and perspective.strip():
                    article.perspective_1 = perspective.strip()
                    db2.commit()

                # 解构层 (2026-08-11): 洗稿前先解构新闻, 产出"伪用户评论"注入,
                # 让 laotan 从观众疑问出发成稿 (而非裸洗原文). 失败回退普通洗稿.
                decon_result = None
                raw_for_rewrite = article.raw_text
                try:
                    from ..services.boost_service import deconstruct_article, format_pseudo_comments

                    _publish(job_id, {"type": "deconstruct_start", "script_id": script.id, "msg": "解构层：复刻观众反应"})
                    decon_result = deconstruct_article(article.raw_text)
                    if decon_result:
                        pseudo = format_pseudo_comments(decon_result)
                        if pseudo:
                            # 伪用户评论追加到原文后, 作为 laotan 输入的一部分
                            raw_for_rewrite = article.raw_text + "\n\n" + pseudo
                            _publish(job_id, {"type": "deconstruct_done", "script_id": script.id, "msg": f"解构完成：{len(decon_result['reactions'])} 条观众反应"})
                except Exception as decon_exc:
                    logger.warning("[deconstruct] failed, fallback to normal rewrite: %s", decon_exc)

                script_text = llm.rewrite_article(
                    raw_for_rewrite,
                    prompt_template=prompt_template,
                    model=model_alias,
                    stream=True,
                    chunk_callback=_cb,
                    perspective=perspective,
                )

                script = Script(
                    article_id=article.id,
                    host_id=host_id,
                    version=1,
                    prompt_template=prompt_template,
                    script_text=script_text,
                    video_format=video_format,
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

                # 开结尾: 人物(persona)显式编辑优先, 其次 host 兼容老数据 (2026-08-08)
                fixed_opening = (persona.fixed_opening if persona else None) or (host.fixed_opening if host else None)
                fixed_ending = (persona.fixed_ending if persona else None) or (host.fixed_ending if host else None)
                segments_data = parse_script(script_text, fixed_opening, fixed_ending)
                for seg_data in segments_data:
                    from ..models import Segment

                    db2.add(Segment(script_id=script.id, **seg_data))
                db2.commit()

                # 爆品改造改为手动触发 (2026-08-11): 洗稿只产出底稿, 用户看稿/改观点后
                # 再点独立"爆品改造"端点 (POST /scripts/{id}/boost) 触发 P1-P3.
                # 不再洗稿后自动跑, 给人工控制点.
                _publish(job_id, {
                    "type": "boost_done",
                    "script_id": script.id,
                    "boosted": False,
                    "msg": "洗稿完成, 可手动触发爆品改造",
                })

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

    background_tasks.add_task(_do_rewrite)
    return {"job_id": job_id, "status": "started", "model": model_alias or "default"}

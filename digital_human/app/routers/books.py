# -*- coding: utf-8 -*-
"""拆书项目端点 (2026-08-19) — 5 步创作流 + 级联重跑 + 挂车清单.

方案: docs/拆书项目-实施方案.md。同步端点 (P1): 单书人工确认节奏, 无需异步队列。
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import get_db
from app.models import BookProject, Episode
from app.services.book_service import orchestrator as orch
from app.services.book_service.persona import ensure_book_account
from app.services.book_service.reader import scan_book_sources

logger = logging.getLogger(__name__)

router = APIRouter(tags=["books"])

__all__ = ["router"]


class BookCreate(BaseModel):
    book_title: str
    author: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    cart_url: str | None = None
    cover_url: str | None = None
    selling_point: str | None = None
    source_path: str | None = None  # L0 精华/原书; 空则 UI 从书库选
    source_url: str | None = None  # 知海书页: 爬元数据/简介/目录当 L1


class EpisodeEdit(BaseModel):
    script_text: str | None = None
    title: str | None = None
    target_duration_sec: float | None = None


class ProduceRequest(BaseModel):
    """进产线请求: 可选指定人设 (人物即账号)."""
    persona_id: str | None = None
    # 强制重跑 (2026-08-20): 删旧 Script/segments 重建 — 发现错误/换新产线时用
    force: bool = False


class RoadmapRow(BaseModel):
    """总纲单行: 可编辑 6 字段 (与 build_roadmap 生成结构对齐)."""
    ep: int
    主题: str = ""
    对应书中内容: str = ""
    核心任务: str = ""
    承上: str = ""
    启下: str = ""
    概念: list[str] = []


class RoadmapUpdate(BaseModel):
    """总纲批量编辑请求 (6 集全量提交)."""
    episodes: list[RoadmapRow]


def _book_or_404(db: Session, book_id: str) -> BookProject:
    b = db.get(BookProject, book_id)
    if not b:
        raise HTTPException(404, f"书不存在: {book_id}")
    return b


def _ep_or_404(db: Session, book_id: str, n: int) -> Episode:
    ep = db.query(Episode).filter(
        Episode.book_id == book_id, Episode.ep_index == n).first()
    if not ep:
        raise HTTPException(404, f"第 {n} 集不存在")
    return ep


@router.get("/book-sources")
def list_book_sources():
    """书库目录扫描 (精华/原书/蒸馏, 文件名=书名)."""
    from app.services.book_service import distiller
    srcs = scan_book_sources(get_config().defaults.book_source_dir)
    for s in srcs:
        s["kind"] = ("distilled" if distiller.DISTILL_SUFFIX in s["filename"]
                     else "full" if (s["ext"] == "epub" or s["size"] > distiller._FULL_TEXT_MIN * 3)
                     else "essence")
    return {"sources": srcs}


# ── 离线蒸馏 (本地 Gemma 批量, 批次结束全杀腾卡) ─────────────────
@router.get("/distill/pending")
def distill_pending():
    from app.services.book_service import distiller
    return {"pending": distiller.pending_distill_books(
        scan_book_sources(get_config().defaults.book_source_dir))}


@router.post("/distill/start")
def distill_start():
    from app.services.book_service import distiller
    try:
        distiller.start_batch(get_config().defaults.book_source_dir)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    return {"started": True}


@router.post("/distill/start-single")
def distill_start_single(path: str):
    """单本书蒸馏 (2026-08-20): 拉起本地 Gemma 对指定书蒸馏.

    路径限定 book_source_dir 内防穿越; 该 book 须是可蒸馏形态 (全书/大txt 且无 .蒸馏).
    """
    from app.services.book_service import distiller
    root = Path(get_config().defaults.book_source_dir).resolve()
    p = Path(path).resolve()
    if p.parent != root or not p.exists():
        raise HTTPException(404, f"文件不存在: {path}")
    # 校验可蒸馏: 复用 pending_distill_books 判定 (全书/大txt 且无同名 .蒸馏)
    from app.services.book_service.reader import scan_book_sources
    matching = [s for s in scan_book_sources(root) if s["path"] == str(p)]
    if not matching:
        raise HTTPException(404, f"书库中无此文件: {path}")
    if not distiller.pending_distill_books(matching):
        raise HTTPException(409, "该书已有蒸馏精华, 或不是全书形态")
    try:
        distiller.start_single(p, str(root))
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    return {"started": True, "book": p.stem}


@router.get("/distill/status")
def distill_status():
    from app.services.book_service import distiller
    return distiller.batch_status()


@router.post("/distill/clear")
def distill_clear():
    """清空蒸馏状态/事件缓冲 (2026-08-20): 前端确认完成后恢复页面."""
    from app.services.book_service import distiller
    try:
        distiller.clear_state()
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    return {"cleared": True}


@router.get("/distill/events")
async def distill_events(request: Request):
    """SSE: 蒸馏批次关键节点实时推送 (启动/每书/每章/完成/腾卡)."""
    import asyncio as _aio
    import json as _json
    from fastapi.responses import StreamingResponse
    from app.services.director_events import subscribe, unsubscribe

    queue = subscribe("distill")

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await _aio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {_json.dumps(data, ensure_ascii=False)}\n\n"
                    if data.get("type") in ("distill_done", "distill_error"):
                        break
                except _aio.TimeoutError:
                    yield f"data: {_json.dumps({'level': 'info', 'msg': '…'}, ensure_ascii=False)}\n\n"
        finally:
            unsubscribe("distill", queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/book-sources/preview")
def book_source_preview(filename: str):
    """书库文件预览 (前 1500 字). 路径限定 book_source_dir 防穿越."""
    root = Path(get_config().defaults.book_source_dir).resolve()
    p = (root / filename).resolve()
    if p.parent != root or not p.exists():
        raise HTTPException(404, f"文件不存在: {filename}")
    return {"filename": filename, "preview": p.read_text(encoding="utf-8", errors="replace")[:1500]}


@router.post("/books")
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    ensure_book_account(db)  # 幂等建书账号人设
    book = BookProject(**body.model_dump(exclude_none=True))
    db.add(book)
    db.commit()
    db.refresh(book)
    return {"id": book.id, "status": book.status}


@router.get("/books")
def list_books(db: Session = Depends(get_db)):
    books = db.query(BookProject).order_by(BookProject.created_at.desc()).all()
    return {"books": [
        {"id": b.id, "book_title": b.book_title, "author": b.author,
         "status": b.status, "created_at": b.created_at.isoformat(),
         "progress": _book_progress(b),
         "episodes": [{"ep": e.ep_index, "title": e.title, "status": e.status}
                      for e in b.episodes]}
        for b in books]}


_STEP_LABELS = ["输入补全", "评论层+素材", "多集总纲", "逐集确认", "进产线"]


def _book_progress(b: BookProject) -> dict:
    """流程进度: 5 步布尔完成度 + 当前步骤 + 下一步动作提示.

    供前端渲染顶部流程条与"下一步入口", 单一事实源在后端状态机.
    """
    inp = b.input_json or {}
    eps = sorted(b.episodes, key=lambda e: e.ep_index)
    # 步骤完成判定 (状态机派生的保守布尔)
    step_done = [
        bool(inp.get("书籍类型") or inp.get("全书核心主张")),          # 1 输入补全
        bool(inp.get("comment_layer")) and bool(inp.get("materials")),  # 2 评论层+素材
        b.status in ("roadmap_review", "writing", "done") and bool(eps),  # 3 多集总纲
        bool(eps) and all(e.status == "confirmed" for e in eps),        # 4 逐集确认
        any(e.script_id for e in eps),                                  # 5 进产线
    ]
    current = 1
    for i, done in enumerate(step_done, 1):
        if not done:
            current = i
            break
    else:
        current = 5

    # 下一步动作: 当前步骤首个待办 → 对应按钮 + 提示
    next_action: dict[str, str] | None = None
    if current == 1:
        next_action = {"button": "complete", "label": "补全输入",
                       "hint": "补全书的核心字段 (类型/主张/读者画像)"}
    elif current == 2:
        next_action = {"button": "confirm-input", "label": "确认1 → 评论层+素材",
                       "hint": "生成读者反应清单 + 素材包"}
    elif current == 3:
        next_action = {"button": "roadmap", "label": "生成总纲 (pro)",
                       "hint": "生成 6 集拆解路线图, 约 1-3 分钟"}
    elif current == 4:
        nxt = next((e for e in eps if e.status != "confirmed"), None)
        if nxt:
            next_action = (
                {"button": f"episodes/{nxt.ep_index}/generate", "label": f"生成第 {nxt.ep_index} 集稿",
                 "hint": f"第 {nxt.ep_index} 集: {nxt.title or ''}"}
                if nxt.status in ("pending", "generating") else
                {"button": f"episodes/{nxt.ep_index}/confirm", "label": f"确认第 {nxt.ep_index} 集",
                 "hint": "稿子已生成, 人工过稿后确认定稿"})
    else:
        nxt = next((e for e in eps if e.script_id), None)
        next_action = {"button": "produce", "label": "进产线 →",
                       "hint": "已确认集 → 生成 Script/TTS/导演任务"} if nxt else None

    return {"steps": _STEP_LABELS, "done": step_done, "current": current,
            "next_action": next_action}


@router.get("/books/{book_id}")
def get_book(book_id: str, db: Session = Depends(get_db)):
    b = _book_or_404(db, book_id)
    return {
        "id": b.id, "book_title": b.book_title, "author": b.author,
        "status": b.status, "input_json": b.input_json,
        "source_path": b.source_path, "cart_url": b.cart_url,
        "cover_url": b.cover_url, "selling_point": b.selling_point,
        "progress": _book_progress(b),
        "episodes": [
            {"ep": e.ep_index, "title": e.title, "status": e.status,
             "script_text": e.script_text, "coverage": e.coverage_json,
             "roadmap": e.roadmap_json, "target_duration_sec": e.target_duration_sec,
             "script_id": e.script_id, "director_job_id": e.director_job_id}
            for e in b.episodes],
    }


@router.post("/books/{book_id}/complete")
def complete(book_id: str, db: Session = Depends(get_db)):
    """步骤1: 输入补全 (flash) →【确认1】."""
    b = orch.complete_input(db, _book_or_404(db, book_id))
    return {"status": b.status,
            "needs_supplement": (b.input_json or {}).get("needs_supplement", [])}


@router.post("/books/{book_id}/assess")
def assess(book_id: str, db: Session = Depends(get_db)):
    """Gate 0 预评估 (蒸馏前): 丢书名定档 🟢/🟡/🔴, 防蒸馏浪费."""
    b = _book_or_404(db, book_id)
    meta = (b.input_json or {}).get("book_meta")
    if not meta and getattr(b, "source_url", None):
        from app.services.book_service.reader import fetch_zhihailib_meta
        meta = fetch_zhihailib_meta(b.source_url)
    r = orch.assess_book_risk(b.book_title, b.author, meta)
    inp = dict(b.input_json or {})
    inp["risk_assessment"] = r
    b.input_json = inp
    db.commit()
    return r


@router.post("/books/{book_id}/confirm-input")
def confirm_input(book_id: str, db: Session = Depends(get_db)):
    """确认1 通过 → 步骤2∥3 评论层+素材 (轻确认)."""
    b = _book_or_404(db, book_id)
    orch.build_comment_layer(db, b)
    orch.build_materials(db, b)
    return {"status": b.status,
            "comment_layer": len((b.input_json or {}).get("comment_layer") or []),
            "materials": len((b.input_json or {}).get("materials") or [])}


@router.post("/books/{book_id}/roadmap")
def roadmap(book_id: str, db: Session = Depends(get_db)):
    """步骤4: 多集总纲 (pro) + 追溯自检 →【确认2】."""
    b, issues = orch.build_roadmap(db, _book_or_404(db, book_id))
    return {"status": b.status, "trace_issues": issues,
            "episodes": [{"ep": e.ep_index, "title": e.title} for e in b.episodes]}


@router.post("/books/{book_id}/confirm-roadmap")
def confirm_roadmap(book_id: str, db: Session = Depends(get_db)):
    b = _book_or_404(db, book_id)
    b.status = "writing"
    db.commit()
    return {"status": b.status}


@router.put("/books/{book_id}/roadmap")
def update_roadmap(book_id: str, body: RoadmapUpdate, db: Session = Depends(get_db)):
    """总纲批量编辑 (2026-08-20): 加入个人视角. 6 集全量提交, 校验 ep 完整性.

    roadmap_json 结构保持 {ep,主题,对应书中内容,核心任务,承上,启下,概念} 不变,
    兼容 generate_episode 的 prompt 注入与主题自检; 编辑后清 _issues/_checks 防误导.
    """
    b = _book_or_404(db, book_id)
    eps = {e.ep_index: e for e in b.episodes}
    if not eps:
        raise HTTPException(400, "还没有总纲, 先点【生成总纲】")
    if len(body.episodes) != len(eps):
        raise HTTPException(400, f"总纲须为 {len(eps)} 集全量提交, 实际 {len(body.episodes)}")
    valid_eps = set(eps)
    for row in body.episodes:
        if row.ep not in valid_eps:
            raise HTTPException(400, f"ep={row.ep} 不在本书记录的集数 {sorted(valid_eps)} 中")

    for row in body.episodes:
        ep = eps[row.ep]
        cur = dict(ep.roadmap_json or {})
        cur.update({
            "ep": row.ep,
            "主题": row.主题,
            "对应书中内容": row.对应书中内容,
            "核心任务": row.核心任务,
            "承上": row.承上,
            "启下": row.启下,
            "概念": row.概念 or [],
        })
        # 编辑后旧自检/校验结果失效, 清空防误导
        cur.pop("_issues", None)
        cur.pop("_checks", None)
        ep.roadmap_json = cur
        ep.title = row.主题 or ep.title  # 与 build_roadmap 的 title=主题 对齐
    db.commit()
    return {"updated": len(body.episodes), "status": b.status}


@router.put("/books/{book_id}/episodes/{n}")
def edit_episode(book_id: str, n: int, body: EpisodeEdit, db: Session = Depends(get_db)):
    """人工修稿 (确认节点内)."""
    ep = _ep_or_404(db, book_id, n)
    for f in ("script_text", "title", "target_duration_sec"):
        v = getattr(body, f)
        if v is not None:
            setattr(ep, f, v)
    db.commit()
    return {"ep": ep.ep_index, "status": ep.status}


@router.post("/books/{book_id}/episodes/{n}/generate")
def generate(book_id: str, n: int, db: Session = Depends(get_db)):
    """步骤5: 逐集生成 (pro) + 硬校验 + 人设注入 →【确认3】."""
    ep = orch.generate_episode(db, _ep_or_404(db, book_id, n))
    return {"ep": ep.ep_index, "status": ep.status,
            "issues": (ep.roadmap_json or {}).get("_issues", []),
            "checks": (ep.roadmap_json or {}).get("_checks", {})}


@router.post("/books/{book_id}/episodes/{n}/confirm")
def confirm_episode(book_id: str, n: int, db: Session = Depends(get_db)):
    ep = orch.confirm_episode(db, _ep_or_404(db, book_id, n))
    return {"ep": ep.ep_index, "status": ep.status, "book_status": ep.book.status}


@router.post("/books/{book_id}/episodes/{n}/rerun")
def rerun(book_id: str, n: int, db: Session = Depends(get_db)):
    """级联重跑: 重跑 N 作废 N..6."""
    b = orch.rerun_cascade(db, _book_or_404(db, book_id), n)
    return {"status": b.status,
            "reset": [e.ep_index for e in b.episodes if e.status == "pending"]}


@router.post("/books/{book_id}/episodes/{n}/produce")
def produce(book_id: str, n: int, body: ProduceRequest | None = None,
            db: Session = Depends(get_db)):
    """进产线桥接 (2026-08-19): 确认集 → Article 占位 + Script + segments.

    复用新闻线后半段: 返回 script_id 后 UI 调
    POST /audio/scripts/{id}/generate-audio → POST /api/director/jobs → director.html。
    人设可选 (2026-08-20): body.persona_id 指定人物即账号; 缺省回退静读书.
    """
    from app.models import Article, Host, Persona, Script, Segment
    from app.services.book_service.persona import ensure_book_account
    from app.services.script_parser import parse_script

    b = _book_or_404(db, book_id)
    ep = _ep_or_404(db, book_id, n)
    if ep.status != "confirmed" or not ep.script_text:
        raise HTTPException(409, f"第{n}集未确认或无稿 (先走 确认3)")
    force = bool(body.force) if body else False
    if ep.script_id and db.get(Script, ep.script_id) and not force:
        return {"script_id": ep.script_id, "already": True}
    if force and ep.script_id:
        # 重跑: 删旧 Script + 其 segments (级联), 再重建
        old = db.get(Script, ep.script_id)
        if old:
            logger.info("[book] 第%d集 重跑进产线, 删旧 script %s", n, old.id)
            db.delete(old)  # segments cascade
        ep.script_id = None

    inp = dict(b.input_json or {})
    # 人设解析 (人物即账号, 仿 articles._do_rewrite): 显式 body → 上次记住 → 回退静读书
    persona, host = None, None
    pid = (body.persona_id if body else None) or (inp.get("persona_id") or None)
    if pid:
        persona = db.query(Persona).filter(Persona.id == pid).first()
        if not persona:
            raise HTTPException(404, f"人物不存在: {pid}")
        if not persona.host_id:
            raise HTTPException(400, f"人物 {persona.name} 未绑定账号 (host)")
        host = db.query(Host).filter(Host.id == persona.host_id).first()
    if host is None:
        host = ensure_book_account(db)
        persona = db.query(Persona).filter(Persona.host_id == host.id).first()
    inp["persona_id"] = persona.id if persona else None  # 记住所选, 后续集默认复用
    b.input_json = inp

    article = db.get(Article, inp.get("article_id") or "") if inp.get("article_id") else None
    if not article:
        article = Article(
            title=f"[拆书]《{b.book_title}》",
            raw_text=(ep.script_text or b.book_title)[:20000],
            track="tech",
        )
        db.add(article)
        db.flush()
        inp["article_id"] = article.id
        b.input_json = inp

    # ── 拆书稿清洗 (2026-08-20): 剥离【A-B秒｜段名】时间标签 + 校验六段完整.
    # 标签是结构标记, 进音频会读出"零到二十二秒,钩子" → 必须剥离后再 parse_script.
    from app.services.script_parser import clean_episode_script
    cleaned_text, clean_issues = clean_episode_script(ep.script_text)
    if clean_issues:
        logger.warning("[book] 第%d集 清洗告警: %s", n, "; ".join(clean_issues))

    script = Script(
        article_id=article.id,
        host_id=host.id,
        script_text=cleaned_text,  # 清洗后文本 (无时间标签), TTS/导演用
        video_format="landscape",
        prompt_template=persona.prompt_template if persona else "jingshu-book",
    )
    db.add(script)
    db.flush()
    fixed_opening = persona.fixed_opening if persona else None
    fixed_ending = persona.fixed_ending if persona else None
    for seg_data in parse_script(cleaned_text, fixed_opening, fixed_ending):
        db.add(Segment(script_id=script.id, **seg_data))
    ep.script_id = script.id
    db.commit()
    seg_count = db.query(Segment).filter(Segment.script_id == script.id).count()
    return {"script_id": script.id, "article_id": article.id, "segments": seg_count,
            "persona_id": persona.id if persona else None,
            "clean_issues": clean_issues}


@router.get("/books/{book_id}/cart-checklist")
def cart_checklist(book_id: str, db: Session = Depends(get_db)):
    """发布挂车提醒清单 (挂车动作在抖音侧人工)."""
    b = _book_or_404(db, book_id)
    lines = [f"发布挂车清单 《{b.book_title}》 商品链接: {b.cart_url or '(未填)'}"]
    for e in b.episodes:
        if e.status == "confirmed":
            lines.append(f"第{e.ep_index}集 {e.title or ''} → 挂车 + 卖点口播: {b.selling_point or '(未填)'}")
    return {"checklist": "\n".join(lines)}


@router.delete("/books/{book_id}")
def delete_book(book_id: str, db: Session = Depends(get_db)):
    """删除拆书项目 (2026-08-20): 级联删 6 集 + 连带清理已进产线的 Script/Article.

    BookProject.episodes 有 cascade=all, delete-orphan; 若已 produce 进产线,
    关联的 Script 与 Article 一并删除, 避免孤儿记录。
    """
    from app.models import Article, Script

    b = _book_or_404(db, book_id)
    title = b.book_title

    # 收集产线产物: 各集 script_id + book 级 article_id
    script_ids = {e.script_id for e in b.episodes if e.script_id}
    article_id = (b.input_json or {}).get("article_id")

    if script_ids:
        db.query(Script).filter(Script.id.in_(script_ids)).delete(synchronize_session=False)
    if article_id:
        art = db.get(Article, article_id)
        if art:
            # 该 Article 名下的其他 Script (非本拆书集) 不受影响; 仅删本书建的那条
            db.delete(art)

    db.delete(b)  # episodes 级联删除
    db.commit()
    logger.info("[book] 已删除拆书项目: %s (%s)", title, book_id)
    return {"deleted": book_id, "book_title": title}

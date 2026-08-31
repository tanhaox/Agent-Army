# -*- coding: utf-8 -*-
"""PPT 出片产线 router (2026-08-20) — 纯 PPT 视频 MVP.

流程:
  上传 pptx → 解析每页 {文字, 图, 备注台词}
  → 逐页备注台词建 Script (每页台词 = 一个 segment)
  → 复用 TTS (audio 链路) 合成语音
  → 对齐 (TTS 时长快路径) 得每页 start/end
  → 逐页 Chrome+ffmpeg 渲染 mp4
  → concat 拼接 + 主音轨合成 → 成片

2026-09-01 拆包: 编排/任务状态/SSE 事件下沉 app/services/ppt_pipeline.py
(函数体原样搬运零行为变更), 本文件只留 HTTP handler.
"""
from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse

from app.config import get_config
from app.services.ppt_pipeline import (
    _JOBS,
    _evt,
    _job_workdir,
    _run_ppt_pipeline,
)

router = APIRouter(prefix="/api/ppt", tags=["ppt"])

__all__ = ["router"]


@router.post("/upload")
async def upload_ppt(
    file: UploadFile = File(...),
    book_id: str | None = Form(None),
    ep_index: int | None = Form(None),
    voice_id: str | None = Form(None),
):
    """上传 pptx → 解析 → 返回 {job_id, slides 概要}.

    book_id/ep_index (2026-08-21): 绑定拆书系列, 供系列皮肤包对齐.
    voice_id (2026-08-22): 前端选的音色, 传入产线 TTS (此前固定用书账号音色静姐).
    """
    if not file.filename.lower().endswith(".pptx"):
        raise HTTPException(400, "仅支持 .pptx 文件")

    job_id = str(uuid.uuid4())
    workdir = _job_workdir(job_id)
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / "source.pptx"
    content = await file.read()
    src.write_bytes(content)

    from app.services.ppt_service import parse_pptx
    try:
        slides = parse_pptx(src)
    except Exception as exc:
        raise HTTPException(400, f"PPT 解析失败: {exc}")

    _JOBS[job_id] = {
        "status": "uploaded", "slides": len(slides),
        "book_id": book_id, "ep_index": ep_index, "voice_id": voice_id,
        "events": [{"ts": time.strftime("%H:%M:%S"), "level": "ok",
                    "msg": f"解析成功: {len(slides)} 页"}],
    }
    preview = [
        {"index": s.index, "notes_len": len(s.notes), "text_preview": (s.texts[0] if s.texts else "")[:30]}
        for s in slides
    ]
    # 查同书是否已有母本皮肤包
    has_master = False
    master_ep = None
    if book_id:
        from app.services.skin_pack_service import load_skin
        skin = load_skin(book_id)
        if skin:
            has_master = True
            master_ep = skin.master_ep
    return {"job_id": job_id, "slides": len(slides), "preview": preview,
            "book_id": book_id, "ep_index": ep_index,
            "has_master": has_master, "master_ep": master_ep}


@router.post("/{job_id}/mark-master")
def mark_master(job_id: str):
    """把本 job 的 pptx 定为该 book 的母本, 抽系列皮肤包落盘."""
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, f"任务不存在: {job_id}")
    book_id = j.get("book_id")
    ep_index = j.get("ep_index")
    if not book_id or ep_index is None:
        raise HTTPException(400, "未绑定 book_id/ep_index, 无法定为母本 (从拆书讲书页进产线上传)")
    from app.services.skin_pack_service import extract_master
    try:
        pack = extract_master(_job_workdir(job_id), book_id, ep_index)
    except Exception as exc:
        raise HTTPException(400, f"母本抽取失败: {exc}")
    return {"book_id": book_id, "master_ep": ep_index,
            "color_tokens": pack.color_tokens[:5],
            "fontsize_tokens": pack.fontsize_tokens[:6],
            "background": pack.background_path}


@router.get("/series-skin/{book_id}")
def series_skin(book_id: str):
    """查询书系列是否已有母本皮肤包 (前端展示用)."""
    from app.services.skin_pack_service import load_skin
    skin = load_skin(book_id)
    if not skin:
        return {"has_master": False}
    return {"has_master": True, "master_ep": skin.master_ep,
            "color_tokens": skin.color_tokens[:5]}


@router.post("/{job_id}/render")
def render(job_id: str, render_mode: str = Form("jy2")):
    """触发 PPT 产线后台线程 (TTS → 对齐 → 渲染 → 拼片).

    render_mode (2026-08-21):
      - jy2 默认: 元素级拆解 → 剪映多轨草稿 (逐元素动画/字幕/音效/音频)
      - jy        : 整页静态帧 → 剪映草稿 (旧)
      - auto      : 整页静态帧 → zoompan mp4 → 自动拼片 ppt_final.mp4
      - anim      : 旧路径 Playwright 逐帧捕获 (每页 N 帧, 慢, 短片才值得)
    """
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, f"任务不存在: {job_id}")
    if j["status"] == "running":
        raise HTTPException(409, "任务运行中")
    mode = render_mode if render_mode in ("jy2", "jy", "auto", "anim") else "jy2"
    j.update(status="running", done=[], error=None, progress={}, cancel=False,
             render_mode=mode)
    threading.Thread(target=_run_ppt_pipeline, args=(job_id,), daemon=True).start()
    return {"job_id": job_id, "status": "running", "render_mode": mode}


@router.post("/{job_id}/cancel")
def cancel(job_id: str):
    """取消运行中产线 (TTS 完成/逐页渲染间检查 cancel 标志)."""
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, f"任务不存在: {job_id}")
    j["cancel"] = True
    _evt(job_id, "取消请求已接收, 将在本页渲染完成后停止", "warn")
    return {"job_id": job_id, "status": "cancelling"}


@router.get("/{job_id}/status")
def status(job_id: str):
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, f"任务不存在: {job_id}")
    return j


@router.get("/{job_id}/events")
async def events(job_id: str, request: Request):
    """SSE: PPT 产线进度推送."""
    import asyncio as _aio
    import json as _json
    from fastapi.responses import StreamingResponse
    from app.services.director_events import subscribe, unsubscribe

    queue = subscribe(job_id)
    async def stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await _aio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {_json.dumps(data, ensure_ascii=False)}\n\n"
                    if data.get("type") in ("ppt_done", "ppt_error"):
                        break
                except _aio.TimeoutError:
                    yield "data: {\"level\":\"info\",\"msg\":\"…\"}\n\n"
        finally:
            unsubscribe(job_id, queue)
    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/{job_id}/download")
def download(job_id: str):
    """下载成片."""
    j = _JOBS.get(job_id)
    if not j or not j.get("output"):
        raise HTTPException(404, "成片不存在")
    path = Path(j["output"])
    if not path.exists():
        raise HTTPException(404, "成片文件缺失")
    return FileResponse(path, media_type="video/mp4",
                        filename=path.name)


@router.post("/{job_id}/export-jy-draft")
def export_jy(job_id: str):
    """PPT 出片 → 剪映草稿 (2026-08-20): 复用 J 线, 打开剪映审片/调BGM/导出."""
    from app.services.jy_draft_service import export_ppt_draft
    try:
        result = export_ppt_draft(job_id, get_config().defaults.ppt_work_root)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return result

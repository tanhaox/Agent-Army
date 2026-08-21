# -*- coding: utf-8 -*-
"""PPT 出片产线 router (2026-08-20) — 纯 PPT 视频 MVP.

流程:
  上传 pptx → 解析每页 {文字, 图, 备注台词}
  → 逐页备注台词建 Script (每页台词 = 一个 segment)
  → 复用 TTS (audio 链路) 合成语音
  → 对齐 (TTS 时长快路径) 得每页 start/end
  → 逐页 Chrome+ffmpeg 渲染 mp4
  → concat 拼接 + 主音轨合成 → 成片
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import db_session, get_db
from app.models import AudioFile, AudioJob, Script, Segment, Voice

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ppt", tags=["ppt"])

__all__ = ["router"]

# 在跑任务: job_id → 状态 (与蒸馏 _BATCH 同模式, 供轮询 + SSE)
_JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


class _Cancelled(Exception):
    """产线取消信号 (cancel 标志检查抛出)."""


def _evt(job_id: str, msg: str, level: str = "info", **extra) -> None:
    from app.services.director_events import publish
    e = {"ts": time.strftime("%H:%M:%S"), "level": level, "msg": msg, **extra}
    j = _JOBS.setdefault(job_id, {})
    j.setdefault("events", []).append(e)
    if len(j["events"]) > 500:
        j["events"] = j["events"][-500:]
    publish(job_id, e)


def _job_workdir(job_id: str) -> Path:
    root = Path(get_config().defaults.ppt_work_root)
    return root / job_id


@router.post("/upload")
async def upload_ppt(
    file: UploadFile = File(...),
    book_id: str | None = Form(None),
    ep_index: int | None = Form(None),
):
    """上传 pptx → 解析 → 返回 {job_id, slides 概要}.

    book_id/ep_index (2026-08-21): 绑定拆书系列, 供系列皮肤包对齐.
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
        "book_id": book_id, "ep_index": ep_index,
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


# ── 后台产线 ─────────────────────────────────────────────────
def _run_ppt_pipeline(job_id: str) -> None:
    """PPT → 逐页台词 TTS → 对齐 → 渲染 → 拼片."""
    try:
        with db_session() as db:
            from app.models import Article, Host, Persona
            from app.services.book_service.persona import ensure_book_account
            from app.services.ppt_service import (parse_pptx, build_slide_html,
                                                  render_slide_png, png_to_zoompan_mp4,
                                                  render_slide_mp4)
            from app.services.director_service._alignment import _align_fast_or_whisper

            cfg = get_config()
            workdir = _job_workdir(job_id)
            slides = parse_pptx(workdir / "source.pptx")
            _evt(job_id, f"解析完成 {len(slides)} 页, 开始建稿", "ok")

            # ── 1. 建 Script: 每页备注台词 = 一个 segment ──
            host = ensure_book_account(db)
            persona = db.query(Persona).filter(Persona.host_id == host.id).first()
            article = Article(title="[拆书PPT]", raw_text="", track="tech")
            db.add(article); db.flush()
            script = Script(
                article_id=article.id, host_id=host.id,
                script_text="\n".join(s.notes for s in slides if s.notes),
                video_format="landscape",
                prompt_template=persona.prompt_template if persona else "jingshu-book",
            )
            db.add(script); db.flush()

            # 每页一个 Segment (selected_for_host=True 全部参与 TTS)
            segments: list[Segment] = []
            for s in slides:
                seg = Segment(
                    script_id=script.id, line_index=s.index - 1,
                    text=s.notes or f"(第{s.index}页无台词)", segment_type="body",
                    selected_for_host=True, host_order=s.index - 1,
                )
                db.add(seg)
                segments.append(seg)
            db.commit()
            # refresh 拿每个 segment id (对齐按 segment_id 匹配)
            for seg in segments:
                db.refresh(seg)
            db.refresh(script)

            # ── 2. TTS: 复用 audio 链路 ──
            voice = None
            persona_v = db.query(Persona).filter(Persona.host_id == host.id).first()
            if persona_v and persona_v.voice_id:
                voice = db.get(Voice, persona_v.voice_id)
            if not voice:
                voice = db.query(Voice).filter(Voice.host_id == host.id).first()
            voice_id = voice.id if voice else None

            _evt(job_id, f"开始 TTS ({len(segments)} 段, 音色={voice.name if voice else '默认'})", "info")
            from app.services.tts_service import TTSService
            from app.services.gpu_service_manager import get_gpu_service_manager
            tts = TTSService(cfg.defaults)
            job = AudioJob(
                script_id=script.id, voice_id=voice_id,
                output_dir=str(workdir / "audio"), status="pending",
                total_segments=len(segments), completed_segments=0,
            )
            db.add(job); db.commit(); db.refresh(job)
            audio_files: list[AudioFile] = []

            def _progress(completed, total, text, af):
                if _JOBS.get(job_id, {}).get("cancel"):
                    raise _Cancelled()
                audio_files.append(af)
                # 落库: 分段 wav 需进 AudioFile 表, 对齐快路径按 segment_id 匹配
                if af:
                    job.completed_segments = completed
                    db.add(af)
                    db.commit()
                    db.refresh(af)
                _evt(job_id, f"TTS {completed}/{total}: {text[:20]}…", "info",
                     type="tts_progress", progress=f"{completed}/{total}")

            # 用 GPU 服务管理器会话: 自动拉起 IndexTTS (与 audio 端点一致)
            backend = voice.backend if voice and voice.backend else cfg.defaults.backend
            manager = get_gpu_service_manager()
            with manager.session(backend, status_callback=lambda m: _evt(job_id, m, "info")):
                result = tts.generate(job, segments, voice, progress_callback=_progress)
            # 整段拼接: tts.generate 已产出 full_paragraph.wav (combined_file)
            combined = result.get("combined_file") or {}
            combined_path = combined.get("file_path")
            job.status = "completed"
            job.completed_segments = len(segments)
            db.commit()
            _evt(job_id, f"TTS 完成: {len(audio_files)} 段, 整段 {combined.get('duration') or '?'}s", "ok",
                 type="tts_done")

            # ── 3. 对齐: 每页台词 → start/end (TTS 时长快路径) ──
            db.commit()
            _evt(job_id, "开始对齐 (TTS 时长快路径)", "info")
            # audio 参数应为 AudioFile (combined); 用 AudioFile 对象
            combined_af = None
            if combined_path and Path(combined_path).exists():
                combined_af = db.query(AudioFile).filter(
                    AudioFile.audio_job_id == job.id,
                    AudioFile.segment_id.is_(None),
                ).order_by(AudioFile.id.desc()).first()
                if combined_af is None:
                    combined_af = AudioFile(
                        audio_job_id=job.id, segment_id=None,
                        filename=Path(combined_path).name, file_path=str(combined_path),
                        duration=combined.get("duration"), sample_rate=24000,
                    )
                    db.add(combined_af); db.commit()
            aligned = _align_fast_or_whisper(
                db, combined_af, script.id,
                [{"id": seg.id, "segment_id": seg.id, "text": seg.text, "line_index": seg.line_index} for seg in segments],
                job_id=job_id,
            )
            timings = aligned.get("segment_timings") or []
            _evt(job_id, f"对齐完成: {len(timings)} 段", "ok")

            # ── 4. 逐页渲染 ──
            # 系列皮肤对齐 (2026-08-21): 非母本集 apply 母本皮肤 (背景/色/字号)
            bound = _JOBS.get(job_id, {})
            skin = None
            if bound.get("book_id"):
                from app.services.skin_pack_service import load_skin, apply_skin_to_slides
                skin = load_skin(bound["book_id"])
                if skin and bound.get("ep_index") == skin.master_ep:
                    skin = None  # 母本自身是源, 不 apply
                if skin:
                    apply_skin_to_slides(slides, skin)
                    _evt(job_id, f"已套用母本皮肤 (第{bound['ep_index']}集对齐第{bound['book_id']}母本)", "ok")
            clips_dir = workdir / "clips"
            clips_dir.mkdir(parents=True, exist_ok=True)
            mode = bound.get("render_mode", "jy2")
            clip_paths: list[Path] = []
            clip_meta: list[dict] = []  # {path, image, start_sec, duration_sec, notes}
            # 段→wav (元素级草稿逐页音频)
            seg_wav_map = {af.segment_id: af.file_path for af in audio_files
                           if af.segment_id and af.file_path and Path(af.file_path).exists()}
            element_pages: list[dict] = []  # jy2: 逐页层+编排数据
            for i, s in enumerate(slides):
                if bound.get("cancel"):
                    raise _Cancelled()
                seg_id = segments[i].id
                timing = next((t for t in timings if t.get("segment_id") == seg_id), None)
                start = timing.get("start", 0.0) if timing else 0.0
                dur = (timing.get("end") - timing.get("start")) if timing else 6.0
                html = build_slide_html(s, skin=skin)
                page_dir = workdir / f"page_{s.index:02d}"
                png = clips_dir / f"page_{s.index:02d}.png"
                if mode == "anim":
                    # 旧路径: Playwright 逐帧捕获分层入场 (慢, 短片才值得)
                    out = clips_dir / f"page_{s.index:02d}.mp4"
                    render_slide_mp4(html, page_dir, out, dur)
                    clip_paths.append(out)
                    clip_meta.append({"path": str(out), "image": str(png), "start_sec": round(start, 3),
                                      "duration_sec": round(dur, 3), "notes": s.notes})
                elif mode == "jy2":
                    # 元素级拆解: 每页 base+文字/图透明层 → 剪映多轨草稿
                    from app.services.ppt_frame_capture import capture_element_png
                    from app.services.ppt_service import (build_base_html, build_text_element_html,
                                                          build_image_element_html)
                    from app.services.jy_draft_service import compute_page_timing
                    pd = workdir / "layers" / f"p{s.index:02d}"
                    pd.mkdir(parents=True, exist_ok=True)

                    def _cap(name: str, html_txt: str) -> Path:
                        (pd / f"{name}.html").write_text(html_txt, encoding="utf-8")
                        return capture_element_png(pd / f"{name}.html", pd / f"{name}.png")

                    _cap("base", build_base_html(s))
                    pg_layers: list[dict] = [{"kind": "base", "file": str(pd / "base.png")}]
                    for ti, tb in enumerate(s.text_blocks):
                        _cap(f"t{ti}", build_text_element_html(tb))
                        pg_layers.append({"kind": "text", "file": str(pd / f"t{ti}.png"),
                                          "text": tb.text, "order": tb.shape_id,
                                          "left": tb.left, "top": tb.top,
                                          "pt": tb.font_size_pt, "bold": tb.bold})
                    for ii, ib in enumerate(s.image_blocks):
                        _cap(f"im{ii}", build_image_element_html(ib))
                        pg_layers.append({"kind": "image", "file": str(pd / f"im{ii}.png"),
                                          "order": 100 + ib.shape_id, "left": ib.left, "top": ib.top})
                    timed = compute_page_timing(pg_layers, s.notes or "", start, dur)
                    base_l = [l for l in pg_layers if l["kind"] == "base"]
                    element_pages.append({
                        "start_sec": round(start, 3), "duration_sec": round(dur, 3),
                        "audio_file": seg_wav_map.get(seg_id), "narration": s.notes or "",
                        "layers": base_l + timed,
                    })
                    _evt(job_id, f"元素层 {s.index}/{len(slides)} ({dur:.1f}s)", "info",
                         progress=f"{s.index}/{len(slides)}")
                    continue
                else:
                    # 整页静态帧 (jy/auto), 动画交给渲染层 (剪映/zoompan)
                    render_slide_png(html, page_dir, png)
                    if mode == "auto":
                        out = clips_dir / f"page_{s.index:02d}.mp4"
                        png_to_zoompan_mp4(png, out, dur)
                        clip_paths.append(out)
                    clip_meta.append({"path": str(png), "image": str(png), "start_sec": round(start, 3),
                                      "duration_sec": round(dur, 3), "notes": s.notes})
                _evt(job_id, f"渲染页 {s.index}/{len(slides)} ({dur:.1f}s)", "info",
                     progress=f"{s.index}/{len(slides)}")

            # 存元数据: 供剪映草稿导出 / 后续复用
            meta = {"slides": len(slides), "clips": clip_meta, "audio": combined_path,
                    "video_format": "landscape", "render_mode": mode,
                    "book_id": bound.get("book_id"), "ep_index": bound.get("ep_index"),
                    "skin_applied": bool(skin),
                    "master_ep": skin.master_ep if skin else None}
            (workdir / "ppt_manifest.json").write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            _JOBS[job_id]["manifest"] = meta

            if bound.get("cancel"):
                raise _Cancelled()

            # ── 5. 成片出口 ──
            if mode == "jy2":
                # 元素级剪映草稿: 逐元素动画/动态字幕/音效/逐页音频 (实验验证)
                if not element_pages:
                    raise RuntimeError("jy2: 无元素层产出")
                from app.services.jy_draft_service import export_element_draft
                # 首帧免责字幕 (视觉化): 从书线合规配置读, 不上口播
                disclaimer = ""
                try:
                    from app.services.book_service.distiller import load_book_rules
                    disclaimer = (load_book_rules().get("opening_disclaimer") or "")
                except Exception:
                    disclaimer = ""
                draft_name = f"PPT_{time.strftime('%Y%m%d_%H%M')}_{job_id[:8]}"
                _evt(job_id, f"元素级编排 {len(element_pages)} 页 → 剪映草稿…", "info")
                # 系列角标: 书名 + 集数 (左上角呼吸闪烁)
                book_title = ""
                ep_index = bound.get("ep_index")
                if bound.get("book_id"):
                    try:
                        from app.models import BookProject
                        bk = db.query(BookProject).filter(BookProject.id == bound["book_id"]).first()
                        if bk:
                            book_title = bk.book_title or ""
                    except Exception:
                        book_title = ""
                try:
                    draft = export_element_draft(draft_name, element_pages, canvas=(1920, 1080),
                                                 disclaimer=disclaimer,
                                                 book_title=book_title, ep_index=ep_index)
                    _JOBS[job_id]["draft"] = draft
                    _evt(job_id, f"元素级剪映草稿就绪: {draft['draft_name']} "
                                 f"(base{draft['base_segments']}+元素{draft['element_segments']}"
                                 f"+字幕{draft['caption_segments']}+音效{draft['sfx_segments']})", "ok",
                         type="ppt_done")
                except Exception as exc:
                    _evt(job_id, f"元素级草稿导出失败: {exc}", "error", type="ppt_error")
                    raise
            elif mode == "auto":
                _evt(job_id, "拼接成片…", "info")
                final_mp4 = _concat_with_audio(clip_paths, combined_path, workdir)
                _JOBS[job_id]["output"] = str(final_mp4)
                _evt(job_id, f"成片完成: {final_mp4.name} ({final_mp4.stat().st_size/1024/1024:.1f}MB)", "ok",
                     type="ppt_done")
            elif mode == "jy":
                # 剪映草稿 (入场动画/转场/动效字幕由剪映给, 打开即审/导出)
                from app.services.jy_draft_service import export_ppt_draft
                try:
                    draft = export_ppt_draft(job_id, cfg.defaults.ppt_work_root)
                    _JOBS[job_id]["draft"] = draft
                    _evt(job_id, f"剪映草稿就绪: {draft['draft_name']} "
                                 f"({draft['video_segments']} 页, 入场动画+转场)", "ok",
                         type="ppt_done")
                except Exception as exc:
                    _evt(job_id, f"剪映草稿导出失败(可重试 /export-jy-draft): {exc}", "warn",
                         type="ppt_done")
    except _Cancelled:
        _JOBS[job_id]["error"] = "用户取消"
        _evt(job_id, "产线已取消", "warn", type="ppt_error")
    except Exception as exc:
        logger.exception("[ppt %s] 产线失败", job_id)
        _JOBS[job_id]["error"] = str(exc)
        _evt(job_id, f"产线失败: {exc}", "error", type="ppt_error")
    finally:
        j = _JOBS[job_id]
        j["status"] = "cancelled" if j.get("error") == "用户取消" else (
            "done" if not j.get("error") else "failed")


def _concat_with_audio(clip_paths: list[Path], audio_path: str | None,
                       workdir: Path) -> Path:
    """拼接各页 mp4 + 主音轨 (若有). 用 concat demuxer + 音轨叠加."""
    from app.infrastructure.ffmpeg import run_ffmpeg
    concat_file = workdir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in clip_paths), encoding="utf-8")

    out_raw = workdir / "concat_raw.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(concat_file),
           "-c", "copy", str(out_raw)]
    try:
        run_ffmpeg(cmd, timeout=120)
    except RuntimeError:
        if not out_raw.exists():
            raise

    # 加主音轨 (音频时长 > 视频则裁剪; 视频更长则保持静音)
    final = workdir / "ppt_final.mp4"
    if audio_path and Path(audio_path).exists():
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-i", str(out_raw), "-i", str(audio_path),
               "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac",
               "-shortest", str(final)]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-i", str(out_raw),
               "-c", "copy", str(final)]
    try:
        run_ffmpeg(cmd, timeout=120)
    except RuntimeError:
        if not final.exists():
            raise
    return final

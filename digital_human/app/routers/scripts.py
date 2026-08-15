"""Script and segment router (director endpoints included)."""
from __future__ import annotations

import logging
import os
import subprocess
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import db_session, get_db, get_session_maker
from ..models import Script, Segment, AudioJob, AudioFile, DirectorJob, Host, Persona
from ..schemas import ScriptOut, ScriptUpdate, SegmentOut, SegmentUpdate, CorrectRequest
from ..services.llm_service import LLMService
from ..services.script_parser import parse_script
from .jobs import _publish

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("", response_model=list[ScriptOut])
def list_scripts(limit: int = 50, db: Session = Depends(get_db)):
    """List scripts ordered by last-save time (newest first).

    2026-08-12: 由 created_at 改为 updated_at —— 标题大量重复时, 用户
    需要按"最后保存时间"找最新那篇, 而非按首次创建时间。
    """
    return (
        db.query(Script)
        .options(selectinload(Script.article))
        .order_by(Script.updated_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(script_id: str, db: Session = Depends(get_db)):
    script = (
        db.query(Script)
        .options(selectinload(Script.article))
        .filter(Script.id == script_id)
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


def _reparse_segments(db, script, text):
    """删旧 segments + 全新建 (2026-08-14, 替代 line_index 增量匹配).

    旧增量匹配在编辑改句数/标点时 line_index 错位 → segments.text 不更新 → 音频老稿 bug.
    删旧建新保证 segments.text = 新稿; parse_script 默认 selected_for_host=True (全选).
    编辑后勾选重置为全选 (内容已变, 重勾选合理).
    """
    from ..services.script_parser import parse_script
    for seg in list(script.segments):
        db.delete(seg)
    db.flush()
    for p in parse_script(text):
        db.add(Segment(script_id=script.id, **p))


@router.put("/{script_id}", response_model=ScriptOut)
def update_script(script_id: str, payload: ScriptUpdate, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if payload.script_text is not None:
        script.script_text = payload.script_text
        _reparse_segments(db, script, script.script_text)

    # 爆品改造最终稿编辑 (2026-08-11→2026-08-14): 更新 boosted_text + 删旧建新 segments
    if payload.boosted_text is not None:
        script.boosted_text = payload.boosted_text
        _reparse_segments(db, script, payload.boosted_text)

    if payload.status is not None:
        script.status = payload.status

    # ── 音频过期标记 (方案A, 2026-08-12) ──
    # 文稿/最终稿改动 → 旧 completed AudioJob 标记 stale (不删磁盘, 保留历史)。
    # 下次点"生成音频"时 (generate_audio 端点) 会清空 stale job 的磁盘 wav
    # 并删除记录 → 强制重新合成, 杜绝 `_skip_batch` 断点续传误复用旧音频。
    if payload.script_text is not None or payload.boosted_text is not None:
        from ..models import AudioJob

        stale = (
            db.query(AudioJob)
            .filter(AudioJob.script_id == script_id, AudioJob.status == "completed")
            .update({"status": "stale"}, synchronize_session=False)
        )
        if stale:
            logger.info(
                "script %s 文稿已改动, 标记 %d 个旧 AudioJob 为 stale (音频需重新生成)",
                script_id[:8], stale,
            )

    db.commit()

    # 2026-08-14: 编辑最终稿后后台重跑 P5 情绪标注
    # (boosted_text 改了, 旧 emotion_annotations 基于旧稿, TTS 情绪会对不上; 后台跑不阻塞保存)
    if payload.boosted_text is not None:
        import threading
        _new_text = payload.boosted_text
        _sid = script_id

        def _rerun_p5() -> None:
            import logging
            _lg = logging.getLogger(__name__)
            with db_session() as _db:
                try:
                    _s = _db.query(Script).filter(Script.id == _sid).first()
                    _persona = "老谭"
                    if _s and _s.host:
                        _persona = (getattr(_s.host, "stamp_name", None) or _s.host.name) or "老谭"
                    from ..services.boost_service import annotate_emotions
                    _emo = annotate_emotions(_new_text, _persona)
                    if _s:
                        _s.emotion_annotations = _emo
                        _db.commit()
                    _lg.info("[p5-rerun] script %s emotion 重标注完成 (len=%d)", _sid[:8], len(_emo or ""))
                except Exception as _e:
                    _lg.warning("[p5-rerun] script %s failed: %s", _sid[:8], _e)

        threading.Thread(target=_rerun_p5, name=f"p5-rerun-{_sid[:8]}", daemon=True).start()

    db.refresh(script)
    return script


@router.put("/segments/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    if payload.text is not None:
        segment.text = payload.text
    if payload.selected_for_host is not None:
        segment.selected_for_host = payload.selected_for_host
    if payload.host_order is not None:
        segment.host_order = payload.host_order
    if payload.segment_type is not None:
        segment.segment_type = payload.segment_type
    db.commit()
    db.refresh(segment)
    return segment


@router.post("/{script_id}/segments/reorder")
def reorder_segments(script_id: str, segment_ids: list[str], db: Session = Depends(get_db)):
    """Batch update host_order by ordered list of segment ids."""
    segments = db.query(Segment).filter(Segment.script_id == script_id).all()
    seg_map = {s.id: s for s in segments}
    if len(segment_ids) != len(seg_map):
        raise HTTPException(status_code=400, detail="Segment ids mismatch")
    for order, seg_id in enumerate(segment_ids):
        seg_map[seg_id].host_order = order
    db.commit()
    return {"updated": len(segment_ids)}


@router.get("/{script_id}/director-segments", response_model=list[SegmentOut])
def get_director_segments(script_id: str, db: Session = Depends(get_db)):
    """Return segments selected for host, ordered by host_order."""
    segments = (
        db.query(Segment)
        .filter(Segment.script_id == script_id, Segment.selected_for_host == True)
        .order_by(Segment.host_order)
        .all()
    )
    return segments


@router.get("/{script_id}/audio-files")
def list_script_audio_files(script_id: str, db: Session = Depends(get_db)):
    """Return completed combined audio files for a script (whole-audio only, not per-segment)."""
    jobs = (
        db.query(AudioJob)
        .filter(AudioJob.script_id == script_id, AudioJob.status == "completed")
        .order_by(AudioJob.created_at.desc())
        .all()
    )
    results = []
    for job in jobs:
        for af in sorted(job.audio_files, key=lambda f: f.created_at, reverse=True):
            # Only combined whole-audio (segment_id is None), skip per-segment files
            if af.segment_id is not None:
                continue
            if af.duration and af.duration >= 1.0:
                results.append({
                    "id": af.id,
                    "filename": af.filename,
                    "duration": round(af.duration, 1),
                    "created_at": af.created_at.isoformat() if af.created_at else None,
                })
    return results


def _recycle_file(path: str) -> bool:
    """Move a single file to the Windows recycle bin (never permanent delete).

    CLAUDE.md 红线: 禁止直接删除用户数据, 必须走回收站.
    `app/services/file_utils.py::safe_trash` 不可用 — send2trash 未安装时它
    回退到 shutil.rmtree 永久删除. 这里用 PowerShell 的 Microsoft.VisualBasic
    实现, 满足红线且不引入新依赖.

    Args:
        path: Windows 绝对路径 (可为 E:\\数字人计划\\... 或 F:\\AI-Agent-Local\\...).

    Returns:
        True 若文件已移入回收站 (或路径不存在视为无需处理), False 若失败.
    """
    if not path or not os.path.exists(path):
        return False
    # PowerShell 单引号字面量内唯一需要转义的字符是单引号本身 ('' 转义)
    escaped = path.replace("'", "''")
    cmd = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
        f"'{escaped}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
    )
    try:
        # 列表传参 (shell=False) 不经 cmd.exe, 反斜杠/中文路径均为字面量
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("recycle failed for %s: %s", path, exc)
        return False


@router.delete("/{script_id}", status_code=204)
def delete_script(script_id: str, db: Session = Depends(get_db)):
    """Cascade-delete a script and all its artifacts (recycle-bin the audio files).

    - scripts → segments → audio_files (via both segment & audio_job paths)
    - scripts → audio_jobs → audio_files
    - director_jobs → director_slots (no ORM cascade on Script, explicit delete)
    - Article source is preserved.
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # 阻止删除执行中的导演任务 (避免半删除 + 正在写文件的竞态)
    executing = (
        db.query(DirectorJob)
        .filter(DirectorJob.script_id == script_id, DirectorJob.status == "executing")
        .first()
    )
    if executing:
        raise HTTPException(status_code=409, detail="任务执行中，无法删除该脚本")

    # DirectorJob 无 ORM 级联 (Script 无 director_jobs 关系), 显式删除
    for dj in db.query(DirectorJob).filter(DirectorJob.script_id == script_id).all():
        for slot in list(dj.slots):
            db.delete(slot)
        db.delete(dj)

    # DB 删除前收集磁盘路径, 用于删除成功后移入回收站
    audio_paths: set[str] = set()
    for job in script.audio_jobs:
        for af in job.audio_files:
            if af.file_path:
                audio_paths.add(af.file_path)

    # AudioFile 同时被 Segment.audio_files 和 AudioJob.audio_files 双
    # delete-orphan 持有, 直接依赖级联会冲突 — 显式先删, 规避竞态
    for job in script.audio_jobs:
        for af in job.audio_files:
            db.delete(af)
    db.flush()

    # 此时 segments/audio_jobs 已无 audio_files, 双级联无冲突
    db.delete(script)
    db.commit()

    # 回收站 best-effort: 失败只 warn 不阻断; 先 DB 后回收站,
    # DB 删除失败时绝不先移走用户文件 (与 visual_render.delete_job 一致)
    for p in sorted(audio_paths):
        _recycle_file(p)
    return None


def _get_llm() -> LLMService:
    from ..config import get_config

    cfg = get_config()
    return LLMService(cfg.deepseek)


def _run_boost_background(script_id: str, job_id: str) -> None:
    """爆品改造后台线程 (模块级, 显式传参 — 照抄 director._plan_in_background 模式)."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[boost] _run_boost_background STARTED script=%s job=%s", script_id, job_id)
    with db_session() as db2:
        try:
            script2 = db2.query(Script).filter(Script.id == script_id).first()
            if not script2:
                _publish(job_id, {"type": "boost_error", "error": "Script not found"})
                return

            def _emit(evt: str, msg: str) -> None:
                _publish(job_id, {"type": evt, "script_id": script2.id, "msg": msg})

            from ..services.boost_service import run_boost

            boost = run_boost(
                db2, script2.id,
                title=script2.article.title if script2.article else None,
                emit=_emit,
            )
            script2.boosted_text = boost["boosted_text"]
            script2.boost_titles = boost["boost_titles"] or None
            # P5 情绪标注 (2026-08-13): 紧随 P4, 存 emotion_annotations 供 TTS 情绪合成/导演配画面
            # 2026-08-14: 修 key bug — run_boost 返回 p5_annotated, 原 emotion_annotations 恒 None
            script2.emotion_annotations = boost.get("p5_annotated")
            db2.commit()

            # 重建 segments (TTS 读 segments, 改造后内容需落到 segments)
            host = db2.query(Host).filter(Host.id == script2.host_id).first() if script2.host_id else None
            persona = (
                db2.query(Persona).filter(Persona.host_id == script2.host_id).first()
                if script2.host_id else None
            )
            fixed_opening = (persona.fixed_opening if persona else None) or (host.fixed_opening if host else None)
            fixed_ending = (persona.fixed_ending if persona else None) or (host.fixed_ending if host else None)
            for seg in list(script2.segments):
                db2.delete(seg)
            db2.flush()
            boosted_segments = parse_script(boost["boosted_text"], fixed_opening, fixed_ending)
            for seg_data in boosted_segments:
                db2.add(Segment(script_id=script2.id, **seg_data))
            db2.commit()
            _publish(job_id, {
                "type": "boost_done",
                "script_id": script2.id,
                "boosted": True,
                "p1_ok": boost.get("p1_ok"),
                "p2_ok": boost.get("p2_ok"),
                "p3_ok": boost.get("p3_ok"),
                "p4_ok": boost.get("p4_ok"),
                "p5_ok": bool(boost.get("p5_annotated")),
            })
        except Exception as exc:
            logger.exception("[boost] background failed for %s: %s", script_id, exc)
            try:
                _publish(job_id, {"type": "boost_error", "error": str(exc)})
            except Exception:
                pass


@router.post("/{script_id}/boost")
def boost_script(
    script_id: str,
    db: Session = Depends(get_db),
):
    """爆品改造 (2026-08-11 手动触发): P1开场→P2预埋→P3节奏.

    洗稿后用户看稿/改观点, 再点此端点触发爆品改造.
    基于当前 script_text (可能被 correct 修正过) 生成 boosted_text.
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    job_id = str(uuid.uuid4())
    import threading

    t = threading.Thread(
        target=_run_boost_background,
        args=(script_id, job_id),
        daemon=True,
        name=f"boost-{job_id[:8]}",
    )
    t.start()
    return {"job_id": job_id, "status": "started"}


@router.post("/{script_id}/correct")
def correct_script(
    script_id: str,
    request: CorrectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(_get_llm),
):
    """根据修正观点调整已洗稿脚本（可选步骤）。

    洗稿完成后，用户可提交修正观点触发二次 LLM 微调。
    无修正观点时跳过此步骤，直接走生成音频。
    """
    script = (
        db.query(Script)
        .options(selectinload(Script.article))
        .filter(Script.id == script_id)
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    if not script.script_text:
        raise HTTPException(status_code=400, detail="Script text is empty")

    job_id = str(uuid.uuid4())

    def _do_correct():
        if get_session_maker() is None:
            _publish(job_id, {"type": "correct_error", "error": "Database not initialized"})
            return
        with db_session() as db2:
            try:
                script2 = db2.query(Script).filter(Script.id == script_id).first()
                if not script2:
                    _publish(job_id, {"type": "correct_error", "error": "Script not found"})
                    return

                chunks: list[str] = []

                def _cb(chunk: str) -> None:
                    chunks.append(chunk)
                    _publish(job_id, {"type": "correct_chunk", "chunk": chunk})

                # 修正目标: 洗稿稿(script_text)。(2026-08-11 改回: 半自动流程下,
                # correct 在 boost 之前, 改的是洗稿稿; 之后 boost 基于改好的稿改造)
                target_text = script2.script_text
                corrected_text = llm.correct_article(
                    target_text,
                    perspective=request.perspective,
                    prompt_template=script2.prompt_template,
                    model=request.model,
                    stream=True,
                    chunk_callback=_cb,
                )

                # 保存修正观点
                script2.perspective_2 = request.perspective.strip()
                script2.script_text = corrected_text

                # 重新分段: 开结尾取人物(persona)显式值, 其次 host 兼容老数据 (2026-08-08)
                host = db2.query(Host).filter(Host.id == script2.host_id).first()
                persona = (
                    db2.query(Persona).filter(Persona.host_id == script2.host_id).first()
                    if script2.host_id else None
                )
                fixed_opening = (persona.fixed_opening if persona else None) or (host.fixed_opening if host else None)
                fixed_ending = (persona.fixed_ending if persona else None) or (host.fixed_ending if host else None)
                segments_data = parse_script(corrected_text, fixed_opening, fixed_ending)

                # 清除旧分段，重新写入
                for seg in list(script2.segments):
                    db2.delete(seg)
                db2.flush()
                for seg_data in segments_data:
                    db2.add(Segment(script_id=script2.id, **seg_data))

                db2.commit()

                _publish(job_id, {"type": "correct_done", "script_id": script2.id})
            except Exception as exc:
                _publish(job_id, {"type": "correct_error", "error": str(exc)})

    background_tasks.add_task(_do_correct)
    return {"job_id": job_id, "status": "started"}
"""Director Agent 2.0 — public API for plan creation, slot replacement, job lifecycle.

Internal logic is split into:
- director_prompt: prompt loading and building
- director_parser: LLM output parsing and rule enforcement
"""
from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import DirectorJob, DirectorSlot
from app.services.alignment_service import align_script_segments
from app.services.director_events import PlanCancelled, publish as _evt
from app.services.director_parser import _HOST_FAMILY, _best_fallback_workflow, parse_llm_plan
from app.services.director_prompt import build_director_prompt
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job trace — 环节级轨迹 (复用 plan_json 里的 "trace" 数组, 无需新增 DB 列)
# 记录每个环节的起止/状态/详情, 出问题时按 trace 顺序快速锁定出错的环节。
# ---------------------------------------------------------------------------

def append_trace(
    db: Session,
    job: DirectorJob,
    step: str,
    status: str,
    detail: str = "",
    *,
    _json: dict | None = None,
) -> None:
    """Append one trace entry to job.plan_json["trace"] and commit.

    Args:
        step: 环节名, e.g. "alignment" / "plan_llm" / "execute_phase" / "fallback" / "compose".
        status: "start" | "done" | "error" | "skip" | "warn".
        detail: 简短说明 (保留可读性, 不塞长堆栈)。
    """
    if _json is not None:
        plan = _json
    else:
        # deepcopy 必须: plan_json 已非空时 (job.plan_json or {}) 返回的是对象本身,
        # 就地 append + 自赋值不会触发 SQLAlchemy 脏标记, commit 不 flush 导致该条丢失
        # (正是 plan_llm 埋点丢失的根因; alignment 埋点时 plan_json 为空 {} 走 or {} 新 dict 才碰巧成功).
        plan = copy.deepcopy(job.plan_json or {})
    trace = plan.setdefault("trace", [])
    trace.append({
        "n": len(trace) + 1,  # 序号基于既有 trace 长度, 幂等、跨重启不乱序
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "step": step,
        "status": status,
        "detail": detail[:400],
    })
    if _json is None:
        job.plan_json = plan
        db.commit()


def get_trace(db: Session, job: DirectorJob) -> list[dict[str, Any]]:
    """Read job trace (empty list if none yet)."""
    return list((job.plan_json or {}).get("trace", []) or [])


# ---------------------------------------------------------------------------
# Alignment: fast path (TTS durations) or fallback (Whisper re-transcription)
# ---------------------------------------------------------------------------

def _align_fast_or_whisper(
    db: Session,
    audio: Any,
    script_id: str,
    segments: list[dict[str, Any]],
    *,
    job_id: str | None = None,
    language: str = "zh",
    is_cancelled: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Align script segments to audio — prefer TTS durations, fall back to Whisper.

    ID-024: the TTS pass already produced one wav per segment with a known
    duration in ``audio_files``. When every selected host segment has an audio
    file with a duration, we lay out the timeline as a concatenation and skip
    faster-whisper entirely (planning drops from minutes to seconds). If any
    segment is missing a duration, fall back to Whisper re-transcription so the
    timeline stays complete.
    """
    from app.models import AudioFile, Segment
    from app.services.alignment_service import (
        align_from_tts_durations,
        align_script_segments,
    )

    if job_id:
        _evt(job_id, {"type": "alignment_progress", "msg": "检查 TTS 段落时长…"})

    # 1. Fast path: every host segment has a TTS wav duration.
    tts_segments = _collect_tts_segment_durations(db, script_id, segments)
    if tts_segments is not None:
        logger.info(
            "[director %s] fast path: %d segments aligned from TTS durations",
            job_id, len(tts_segments),
        )
        return align_from_tts_durations(
            tts_segments,
            on_event=lambda data: _evt(job_id, data) if job_id else None,
            is_cancelled=is_cancelled,
        )

    # 2. Fallback: full Whisper re-transcription of the paragraph audio.
    logger.info("[director %s] fast path unavailable, falling back to Whisper", job_id)
    if job_id:
        _evt(job_id, {"type": "alignment_progress", "msg": "段落时长不完整，改用 Whisper 转录…"})
    return align_script_segments(
        audio.file_path,
        segments,
        language=language,
        on_event=lambda data: _evt(job_id, data) if job_id else None,
        is_cancelled=is_cancelled,
    )


def _collect_tts_segment_durations(
    db: Session,
    script_id: str,
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    """Map each host segment to its TTS wav duration, or None if incomplete.

    Uses the latest completed AudioJob's audio_files for the script, keyed by
    segment_id. Returns None when any segment is missing a duration (caller
    should fall back to Whisper).
    """
    from app.models import AudioFile, AudioJob, Segment

    job = (
        db.query(AudioJob)
        .filter(AudioJob.script_id == script_id, AudioJob.status == "completed")
        .order_by(AudioJob.completed_at.desc())
        .first()
    )
    if job is None:
        return None

    dur_by_segment: dict[str, float] = {}
    for af in job.audio_files:
        if af.segment_id is not None and af.duration is not None:
            dur_by_segment[af.segment_id] = float(af.duration)

    result: list[dict[str, Any]] = []
    for seg in segments:
        seg_id = str(seg.get("id") or "")
        if seg_id not in dur_by_segment:
            return None  # incomplete → fall back to Whisper
        result.append(
            {
                "id": seg_id,
                "text": seg.get("text") or "",
                "duration": dur_by_segment[seg_id],
            }
        )
    return result if result else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_director_plan(
    db: Session,
    script_id: str,
    audio_file_id: str,
    *,
    job_id: str | None = None,
    material_catalog: dict[str, Any] | None = None,
    language: str = "zh",
    is_cancelled: Callable[[], bool] | None = None,
    enabled_pipelines: set[str] | None = None,
) -> tuple[DirectorJob, dict[str, Any]]:
    """Run Whisper alignment + LLM slot plan on an existing or new DirectorJob.

    If *job_id* is provided, updates that job in-place (created by router layer).
    Otherwise creates a new DirectorJob (legacy path).

    Args:
        enabled_pipelines: 启用的管线集合 (e.g. {"c","p","h"}). None=全部启用.

    Returns:
        (DirectorJob, alignment_result_dict)
    """
    from app.models import AudioFile, Script

    audio = db.get(AudioFile, audio_file_id)
    if audio is None:
        raise ValueError(f"AudioFile {audio_file_id} not found")
    script = db.get(Script, script_id)
    if script is None:
        raise ValueError(f"Script {script_id} not found")

    # Build alignment input from script segments
    segments = [
        {"id": seg.id, "text": seg.text}
        for seg in sorted(script.segments, key=lambda s: s.line_index)
        if seg.selected_for_host
    ]
    if not segments:
        segments = [{"id": None, "text": script.script_text}]

    if job_id:
        _evt(job_id, {"type": "alignment_progress", "msg": f"对齐 {len(segments)} 段…"})

    if is_cancelled and is_cancelled():
        raise PlanCancelled

    alignment = _align_fast_or_whisper(
        db,
        audio,
        script_id,
        segments,
        job_id=job_id,
        language=language,
        is_cancelled=is_cancelled,
    )

    # 环节轨迹: alignment 完成
    if job_id:
        _j = db.get(DirectorJob, job_id)
        if _j:
            ok_detail = (
                f"对齐完成 {alignment.get('total_duration_sec', 0):.1f}s / {len(segments)} 段"
                if alignment.get("ok")
                else f"对齐失败: {alignment.get('error')}"
            )
            append_trace(db, _j, "alignment", "done" if alignment.get("ok") else "error", ok_detail)

    if job_id:
        _evt(job_id, {"type": "alignment_done", "msg": f"对齐完成: {alignment.get('total_duration_sec', 0):.1f}s", "ok": alignment.get("ok")})

    if is_cancelled and is_cancelled():
        raise PlanCancelled

    if not alignment.get("ok"):
        if job_id:
            job = db.get(DirectorJob, job_id)
            if job:
                job.status = "failed"
                job.error_message = f"alignment failed: {alignment.get('error')}"
                db.commit()
                return job, alignment
        job = DirectorJob(
            script_id=script_id,
            audio_file_id=audio_file_id,
            video_format=script.video_format or "portrait",
            status="failed",
            error_message=f"alignment failed: {alignment.get('error')}",
        )
        db.add(job)
        db.commit()
        return job, alignment

    total_duration = float(alignment.get("total_duration_sec") or 0.0)

    if job_id:
        job = db.get(DirectorJob, job_id)
        if job:
            job.total_duration_sec = total_duration
            job.video_format = script.video_format or "portrait"
            db.commit()
        else:
            job = DirectorJob(
                id=job_id,
                script_id=script_id,
                audio_file_id=audio_file_id,
                video_format=script.video_format or "portrait",
                status="planning",
                total_duration_sec=total_duration,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
    else:
        job = DirectorJob(
            script_id=script_id,
            audio_file_id=audio_file_id,
            video_format=script.video_format or "portrait",
            status="planning",
            total_duration_sec=total_duration,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

    if job_id:
        _evt(job_id, {"type": "llm_start", "msg": "LLM 生成工序单中…"})

    if is_cancelled and is_cancelled():
        raise PlanCancelled

    cfg = get_config()
    llm = LLMService(cfg.deepseek)
    script_title = script.article.title if script.article else None
    prompt = build_director_prompt(
        script_text=script.script_text,
        segment_timings=alignment["segment_timings"],
        material_catalog=material_catalog,
        video_format=job.video_format if job else script.video_format,
        script_title=script_title,
        enabled_pipelines=enabled_pipelines,
    )

    try:
        raw_output = llm.rewrite_article(
            raw_text=prompt,
            model="pro",
            stream=False,
        )
        if is_cancelled and is_cancelled():
            raise PlanCancelled
        plan = parse_llm_plan(
            raw_output,
            alignment["segment_timings"],
            total_duration,
            enabled_pipelines=enabled_pipelines,
        )
        # 环节轨迹: LLM 规划完成
        append_trace(
            db, job, "plan_llm", "done",
            f"LLM 工序单完成: {len(plan.slots)} slots (prompt ~{len(prompt)//1024}KB)",
        )
    except PlanCancelled:
        raise
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"director agent failed: {type(exc).__name__}: {exc}"
        append_trace(db, job, "plan_llm", "error", f"LLM 规划失败: {str(exc)[:200]}")
        db.commit()
        if job_id:
            _evt(job_id, {"type": "llm_error", "msg": str(exc)[:200]})
        return job, alignment

    if job_id:
        _evt(job_id, {"type": "llm_done", "msg": f"LLM 工序单完成: {len(plan.slots)} slots"})

    if is_cancelled and is_cancelled():
        raise PlanCancelled

    # Validate against total duration
    for slot in plan.slots:
        slot.start_sec = max(0.0, min(slot.start_sec, total_duration))
        slot.end_sec = max(slot.start_sec + 0.1, min(slot.end_sec, total_duration))
        slot.duration_sec = round(slot.end_sec - slot.start_sec, 3)

    # Auto-append references card if script has reference segments
    ref_segments = [
        seg for seg in script.segments
        if seg.segment_type == "references"
    ]
    if ref_segments:
        from app.schemas import DirectorSlotPlan
        ref_text = "\n".join(seg.text for seg in ref_segments[:6])
        ref_duration = 15.0
        ref_slot = DirectorSlotPlan(
            slot_index=len(plan.slots),
            start_sec=round(total_duration, 3),
            end_sec=round(total_duration + ref_duration, 3),
            duration_sec=ref_duration,
            text_context=ref_text[:500],
            segment_id=ref_segments[0].id,
            visual_type="hf_title",
            workflow="hf_title",
            params={
                "render_config": {
                    "title": "参考来源",
                    "subtitle": ref_text[:200],
                    "style": "references",
                },
                "intensity": "low",
                "emotion": "closing",
                "no_voiceover": True,
            },
        )
        plan.slots.append(ref_slot)
        logger.info("[director] appended references hf_title slot (%.0fs)", ref_duration)

    # 保留既有 trace (alignment/plan_llm 已写入), 再覆盖 plan 主体, 避免 trace 被 model_dump 清空
    prev_trace = list((job.plan_json or {}).get("trace", []) or [])
    job.plan_json = plan.model_dump()
    if prev_trace:
        job.plan_json["trace"] = prev_trace
    job.title = plan.title or script_title
    job.status = "reviewing"
    append_trace(db, job, "plan", "done", f"规划完成, {len(plan.slots)} slots 进入 reviewing")
    db.commit()

    # Persist slots
    for slot_plan in plan.slots:
        slot = DirectorSlot(
            director_job_id=job.id,
            slot_index=slot_plan.slot_index,
            start_sec=slot_plan.start_sec,
            end_sec=slot_plan.end_sec,
            duration_sec=slot_plan.duration_sec,
            text_context=slot_plan.text_context,
            segment_id=slot_plan.segment_id,
            visual_type=slot_plan.visual_type,
            workflow=slot_plan.workflow,
            params_json=slot_plan.params,
            camera_angle=slot_plan.camera_angle,
            view_group_index=job.view_group_index or 0,
            status="queued",
        )
        db.add(slot)
    db.commit()
    db.refresh(job)

    return job, alignment


def replace_failed_slot(
    db: Session,
    slot: DirectorSlot,
    fallback_chain: list[str] | None = None,
    enabled_pipelines: set[str] | None = None,
) -> DirectorSlot:
    """Replace a failed slot with the next-best workflow in the fallback chain.

    Args:
        fallback_chain: 显式链; None 时由 *enabled_pipelines* 决定.
        enabled_pipelines: 启用的管线集合 (e.g. {"c","p","h"}).
            None=全部启用 → 保留 legacy 固定链 (不感知开关, 向后兼容).
            非 None → 按启用管线动态构造替代链, 只回退到启用管线内的工作流
            (slot.workflow 置首, 避免 host 失败时 current=链首 跳过最佳替代).
    """
    if fallback_chain is None:
        if enabled_pipelines is None:
            # 字幕体系已砍掉(2026-08-01): 兜底不再用黑底白字 black_subtitle, 直接黑屏。
            fallback_chain = ["broll_pexels", "broll_local", "black_placeholder"]
        else:
            if slot.workflow in ("broll_local", "black_placeholder"):
                # 无管线兜底: 固定链, black_placeholder 恒在末尾 → 走到尽头即返回
                # (若 prepend slot.workflow 再加兜底, black_placeholder↔broll_local 会循环)
                fallback_chain = ["broll_local", "black_placeholder"]
            else:
                family_priorities: list[tuple[str, str]]
                if slot.workflow in _HOST_FAMILY:
                    family_priorities = [("c", "host"), ("h", "hf_title"), ("p", "broll_pexels")]
                elif slot.workflow in ("hf_chart", "hf_title"):
                    family_priorities = [("h", "hf_chart"), ("c", "host"), ("p", "broll_pexels")]
                elif slot.workflow == "broll_pexels":
                    family_priorities = [("p", "broll_pexels"), ("c", "host"), ("h", "hf_chart")]
                else:
                    family_priorities = []
                # 只保留启用管线内的工作流 (head 过滤), slot.workflow 置首避免跳过最佳替代
                head = [wf for pl, wf in family_priorities if pl in enabled_pipelines]
                fallback_chain = list(dict.fromkeys([slot.workflow, *head, "broll_local", "black_placeholder"]))

    current = slot.workflow
    if current not in fallback_chain:
        current = fallback_chain[0]
    idx = fallback_chain.index(current)
    if idx + 1 >= len(fallback_chain):
        return slot

    next_workflow = fallback_chain[idx + 1]

    slot.status = "replaced"
    slot.error_code = slot.error_code or "FALLBACK"
    slot.error_message = (slot.error_message or "") + f" | fallback to {next_workflow}"

    new_slot = DirectorSlot(
        director_job_id=slot.director_job_id,
        slot_index=slot.slot_index,
        start_sec=slot.start_sec,
        end_sec=slot.end_sec,
        duration_sec=slot.duration_sec,
        text_context=slot.text_context,
        segment_id=slot.segment_id,
        visual_type=next_workflow,
        workflow=next_workflow,
        params_json={"replaced_from": current, **slot.params_json},
        status="queued",
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    logger.info("Slot %s replaced: %s -> %s", slot.id, current, next_workflow)
    return new_slot


def mark_job_reviewed(db: Session, job_id: str) -> DirectorJob:
    job = db.get(DirectorJob, job_id)
    if job is None:
        raise ValueError(f"DirectorJob {job_id} not found")
    job.status = "reviewing"
    db.commit()
    db.refresh(job)
    return job


def complete_job_if_slots_done(db: Session, job_id: str) -> DirectorJob:
    job = db.get(DirectorJob, job_id)
    if job is None:
        raise ValueError(f"DirectorJob {job_id} not found")
    terminal = {"completed", "failed", "replaced", "skipped"}
    all_done = all(s.status in terminal for s in job.slots)
    if all_done:
        any_failed = any(s.status == "failed" for s in job.slots)
        job.status = "completed" if not any_failed else "failed"
        job.completed_at = datetime.now(timezone.utc)
        if any_failed:
            failed = [s for s in job.slots if s.status == "failed"]
            job.error_message = f"{len(failed)} slot(s) ultimately failed"
        db.commit()
        db.refresh(job)
    return job

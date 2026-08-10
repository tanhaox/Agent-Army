"""Director Agent 2.0 — 规划后处理 (clamp / references 卡 / 落库).

slot 时长钳制、references 来源卡追加、plan 落库 + slots 持久化。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models import DirectorJob, DirectorSlot
from app.services.director_service._trace import append_trace

logger = logging.getLogger(__name__)

__all__ = ["_clamp_slot_durations", "_append_references_slot", "_persist_plan"]


def _clamp_slot_durations(plan: Any, total_duration: float) -> None:
    """Validate against total duration."""
    for slot in plan.slots:
        slot.start_sec = max(0.0, min(slot.start_sec, total_duration))
        slot.end_sec = max(slot.start_sec + 0.1, min(slot.end_sec, total_duration))
        slot.duration_sec = round(slot.end_sec - slot.start_sec, 3)


def _append_references_slot(plan: Any, script: Any, total_duration: float) -> None:
    """Auto-append references card if script has reference segments."""
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


def _persist_plan(
    db: Session,
    job: DirectorJob,
    plan: Any,
    script_title: str | None,
) -> None:
    """plan 落库 (保留既有 trace) + slots 持久化."""
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

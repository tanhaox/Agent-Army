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


# 质量钳制参数 (2026-08-15): 实测 53 slots/5min、broll 0.9s 闪切、21 张 hf_title → 硬兜底
_MIN_DUR = {
    "broll_pexels": 2.5,
    "broll_local": 2.5,
    "hf_title": 3.0,
    "hf_chart": 3.0,
    "hf_quote": 3.0,
}
_HF_TITLE_CAP = 5  # 含尾部参考卡(clamp 后追加, 不占此额度)
_PROTECTED = {"host", "mixed_host_broll", "hf_opening"}


def _clamp_slot_durations(plan: Any, total_duration: float) -> None:
    """质量钳制: 重叠去重 + 最小时长 + hf_title 数量上限 + 时序重排.

    LLM 规划实测三种劣化 (2026-08-15): broll 碎片闪切 (0.9~1.8s)、
    hf_title 滥用 (单片 21 张)、同秒重叠 slot。此处为不可协商的硬底线。
    """
    slots = sorted(plan.slots, key=lambda s: (s.start_sec, s.slot_index))
    kept: list[Any] = []
    hf_title_seen = 0
    cursor = 0.0
    dropped = 0
    for slot in slots:
        dur = slot.end_sec - slot.start_sec
        if dur <= 0.05:
            dropped += 1
            continue  # 空 slot
        # hf_title 数量上限: 超限丢弃 (尾部参考卡在 clamp 之后追加, 不受影响)
        if slot.workflow == "hf_title":
            hf_title_seen += 1
            if hf_title_seen > _HF_TITLE_CAP:
                logger.info("[director] drop excess hf_title (cap %d)", _HF_TITLE_CAP)
                dropped += 1
                continue
        min_dur = _MIN_DUR.get(slot.workflow, 0.0)
        if dur < min_dur:
            if slot.workflow in _PROTECTED or slot.workflow.startswith("hf"):
                dur = min_dur  # hf 卡/出镜拉长到下限
            elif kept and kept[-1].workflow == slot.workflow:
                # broll 碎片并入前一相邻同类型 slot (顺延其 end)
                kept[-1].end_sec = round(kept[-1].end_sec + dur, 3)
                kept[-1].duration_sec = round(kept[-1].end_sec - kept[-1].start_sec, 3)
                cursor = kept[-1].end_sec
                continue
            else:
                dur = min_dur
        # 重叠去重: 起点 = max(原起点, 上一 slot 结束)
        start = max(slot.start_sec, cursor)
        end = start + dur
        if total_duration:
            end = min(end, total_duration)
        slot.start_sec = round(start, 3)
        slot.end_sec = round(end, 3)
        slot.duration_sec = round(slot.end_sec - slot.start_sec, 3)
        if slot.duration_sec <= 0.05 and slot.workflow not in _PROTECTED:
            dropped += 1
            continue
        cursor = slot.end_sec
        kept.append(slot)
    for i, slot in enumerate(kept):
        slot.slot_index = i
    # 时间轴满铺 (2026-08-15): LLM 规划偶发漏铺中段 (实测 323s 音频在 223s 处
    # 有 8.7s 空洞 → 成片音轨错位+截断, 观众听感"整段消失/念一半没了")。
    # 任何 >0.5s 的 slot 间隙, 一律用前一个 slot 延伸填满; 片尾同理。
    filled = 0
    for cur, nxt in zip(kept, kept[1:]):
        gap = nxt.start_sec - cur.end_sec
        if gap > 0.5:
            cur.end_sec = round(nxt.start_sec, 3)
            cur.duration_sec = round(cur.end_sec - cur.start_sec, 3)
            filled += 1
    if kept and total_duration and kept[-1].end_sec < total_duration - 0.5:
        gap = total_duration - kept[-1].end_sec
        kept[-1].end_sec = round(total_duration, 3)
        kept[-1].duration_sec = round(kept[-1].end_sec - kept[-1].start_sec, 3)
        filled += 1
        logger.info("[director] tail coverage: extended last slot by %.1fs to audio end (%.1fs)",
                    gap, total_duration)
    if filled:
        logger.info("[director] timeline tiling: filled %d gap(s), slots now tile audio fully", filled)
    plan.slots = kept
    if dropped:
        logger.info("[director] quality clamp: kept %d slots, dropped %d (碎片/超限/重叠)",
                    len(kept), dropped)


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

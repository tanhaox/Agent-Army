"""Director LLM output parsing and slot rule enforcement."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.schemas import DirectorPlan, DirectorSlotPlan

logger = logging.getLogger(__name__)

_VALID_WORKFLOWS = {"host", "broll_pexels", "broll_local", "hf_chart", "hf_title", "mixed_host_broll"}


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def map_visual_type_to_workflow(visual_type: str, material_source: dict[str, Any]) -> str:
    """Legacy bridge for old prompt output format."""
    if visual_type in _VALID_WORKFLOWS:
        return visual_type
    if visual_type == "出镜":
        return "host"
    if visual_type == "混合":
        return "mixed_host_broll"
    mtype = (material_source or {}).get("type")
    category = (material_source or {}).get("category") or ""
    if mtype == "dynamic":
        if "标题" in category or "title" in category.lower():
            return "hf_title"
        return "hf_chart"
    if (material_source or {}).get("file"):
        return "broll_local"
    return "broll_pexels"


def map_intensity(value: str) -> str:
    return value if value in {"low", "medium", "high"} else "medium"


def map_emotion(value: str) -> str:
    return value if value in {"opening", "rising", "climax", "falling", "closing"} else "rising"


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> Any:
    """Extract the first JSON object or array from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # LLM 可能把 JSON 混在解释文字里，尝试提取第一个对象或数组
    for start_ch, pattern in (("{", r"\{.*\}"), ("[", r"\[.*\]")):
        idx = text.find(start_ch)
        if idx == -1:
            continue
        match = re.search(pattern, text[idx:], re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return json.loads(text)


# ---------------------------------------------------------------------------
# Row parsers
# ---------------------------------------------------------------------------

def parse_legacy_row(row: dict[str, Any], line_id_to_timing: dict[int, dict[str, Any]],
                     total_duration: float) -> DirectorSlotPlan | None:
    """Convert a legacy v2 prompt row (line_id + material_source) into a slot."""
    line_id = int(row.get("line_id", 0))
    timing = line_id_to_timing.get(line_id)
    if timing is None:
        return None
    start = max(0.0, float(timing.get("start", 0.0)))
    end = min(float(total_duration), float(timing.get("end", total_duration)))
    if end <= start:
        end = start + 0.5
    material_source = row.get("material_source") or {}
    visual_type_raw = row.get("visual_type", "出镜")
    workflow = map_visual_type_to_workflow(visual_type_raw, material_source)

    params: dict[str, Any] = {
        "intensity": map_intensity(row.get("intensity", "medium")),
        "emotion": map_emotion(row.get("emotion", "rising")),
        "effect": row.get("effect") or "无",
        "sound": row.get("sound") or "无",
        "category": material_source.get("category"),
    }
    if material_source.get("type") == "static":
        params["file"] = material_source.get("file")
        params["fallback_file"] = material_source.get("fallback_file")
    elif material_source.get("type") == "dynamic":
        params["render_config"] = material_source.get("render_config") or {}

    return DirectorSlotPlan(
        slot_index=line_id - 1,
        start_sec=round(start, 3),
        end_sec=round(end, 3),
        text_context=row.get("text"),
        segment_id=timing.get("segment_id"),
        visual_type=workflow,  # type: ignore[arg-type]
        workflow=workflow,  # type: ignore[arg-type]
        params=params,
    )


def parse_new_row(row: dict[str, Any], total_duration: float) -> DirectorSlotPlan | None:
    """Convert a new v2 prompt row (direct slot fields) into a slot."""
    workflow = row.get("workflow") or row.get("visual_type") or "host"
    if workflow not in _VALID_WORKFLOWS:
        workflow = map_visual_type_to_workflow(workflow, row.get("material_source") or {})

    try:
        slot_index = int(row.get("slot_index", 0))
        start = float(row.get("start_sec", 0))
        end = float(row.get("end_sec", start + 0.5))
    except (TypeError, ValueError):
        return None

    start = max(0.0, min(start, total_duration))
    end = max(start + 0.1, min(end, total_duration))

    params = dict(row.get("params") or {})
    params.setdefault("intensity", map_intensity(row.get("intensity", "medium")))
    params.setdefault("emotion", map_emotion(row.get("emotion", "rising")))

    # 机位: LLM 输出 camera 字段, 仅 host/mixed 有效
    cam = row.get("camera") or row.get("camera_angle")
    try:
        camera_angle = max(1, min(4, int(cam))) if cam else 1
    except (TypeError, ValueError):
        camera_angle = 1
    if workflow not in ("host", "mixed_host_broll"):
        camera_angle = 1

    return DirectorSlotPlan(
        slot_index=slot_index,
        start_sec=round(start, 3),
        end_sec=round(end, 3),
        text_context=row.get("text_context") or row.get("text"),
        segment_id=row.get("segment_id"),
        visual_type=workflow,  # type: ignore[arg-type]
        workflow=workflow,  # type: ignore[arg-type]
        params=params,
        camera_angle=camera_angle,
    )


def is_new_schema(rows: list[dict[str, Any]]) -> bool:
    """Heuristic: new prompt uses workflow/start_sec/end_sec directly."""
    if not rows:
        return False
    sample = rows[0]
    return "workflow" in sample or "start_sec" in sample


# ---------------------------------------------------------------------------
# Plan assembly
# ---------------------------------------------------------------------------

def parse_llm_plan(
    raw_output: str,
    segment_timings: list[dict[str, Any]],
    total_duration: float,
    enabled_pipelines: set[str] | None = None,
) -> DirectorPlan:
    """Parse director LLM output and align with real segment timings.

    兼容两种 LLM 输出:
    - 新格式: {"video_title": "...", "slots": [...]}
    - 旧格式/兜底: [...] 纯数组

    Args:
        enabled_pipelines: 启用的管线集合. None=全部启用.
    """
    parsed = extract_json(raw_output)

    title: str | None = None
    rows: list[dict[str, Any]]
    if isinstance(parsed, dict):
        title = parsed.get("video_title") or parsed.get("title")
        rows = parsed.get("slots") or []
        if not isinstance(rows, list):
            raise ValueError("Director response 'slots' is not a list")
    elif isinstance(parsed, list):
        rows = parsed
    else:
        raise ValueError("Director response is not a JSON object or array")

    timings_by_index = {i + 1: t for i, t in enumerate(segment_timings)}
    slots: list[DirectorSlotPlan] = []

    if is_new_schema(rows):
        for row in rows:
            slot = parse_new_row(row, total_duration)
            if slot is not None:
                slots.append(slot)
    else:
        for row in rows:
            slot = parse_legacy_row(row, timings_by_index, total_duration)
            if slot is not None:
                slots.append(slot)

    slots.sort(key=lambda s: (s.start_sec, s.slot_index))
    for i, slot in enumerate(slots):
        slot.slot_index = i

    slots = enforce_host_rules(slots, total_duration, enabled_pipelines)
    return DirectorPlan(title=title, slots=slots)


# ---------------------------------------------------------------------------
# Rule enforcement
# ---------------------------------------------------------------------------

_HOST_FAMILY = {"host", "mixed_host_broll"}


def _best_fallback_workflow(enabled_pipelines: set[str] | None, *,
                            prefer: str = "host") -> str:
    """Pick the best available fallback workflow given enabled pipelines.

    Priority chains:
      host/mixed_host_broll → hf_title → broll_pexels → broll_local
      hf_chart/hf_title     → host → broll_pexels → broll_local
      broll_pexels          → host → hf_chart → broll_local
    """
    if enabled_pipelines is None:
        return prefer  # All enabled

    c_ok = "c" in enabled_pipelines
    p_ok = "p" in enabled_pipelines
    h_ok = "h" in enabled_pipelines

    if prefer in _HOST_FAMILY:
        if c_ok:
            return prefer
        if h_ok:
            return "hf_title"
        if p_ok:
            return "broll_pexels"
        return "broll_local"

    if prefer in ("hf_chart", "hf_title"):
        if h_ok:
            return prefer
        if c_ok:
            return "host"
        if p_ok:
            return "broll_pexels"
        return "broll_local"

    if prefer == "broll_pexels":
        if p_ok:
            return prefer
        if c_ok:
            return "host"
        if h_ok:
            return "hf_chart"
        return "broll_local"

    # broll_local / black_placeholder — always available
    return prefer


def enforce_host_rules(slots: list[DirectorSlotPlan], total_duration: float,
                       enabled_pipelines: set[str] | None = None) -> list[DirectorSlotPlan]:
    """Guarantee: first and last slots are host; if none in middle add one.

    When C线 (host pipeline) is disabled, host-family slots are downgraded
    to the best available alternative instead of being forced.
    """
    if not slots:
        return slots

    slots[-1].end_sec = min(slots[-1].end_sec, total_duration)

    c_enabled = enabled_pipelines is None or "c" in enabled_pipelines

    if not c_enabled:
        # C线禁用: 将所有 host/mixed_host_broll 降级, 不强制首尾 host
        for i, s in enumerate(slots):
            if s.workflow in _HOST_FAMILY:
                old_wf = s.workflow
                alt = _best_fallback_workflow(enabled_pipelines, prefer=old_wf)
                s.workflow = alt
                s.visual_type = alt
                s.params = {"fallback_reason": "c_pipeline_disabled", **s.params}
                logger.info("[director] slot %d downgraded %s→%s (C线禁用)", i, old_wf, alt)

        slots = enforce_adjacency_rules(slots)
        from app.config import get_config
        max_host = get_config().defaults.max_host_slots
        slots = cap_host_count(slots, max_host=max_host, enabled_pipelines=enabled_pipelines)
        return slots

    # C线启用: 原有逻辑 — 强制首尾至少一个 host, 中间至少一个 host
    if slots[0].workflow != "host":
        slots[0].workflow = "host"
        slots[0].visual_type = "host"
        slots[0].params = {"fallback_reason": "forced_host_opening", **slots[0].params}

    if slots[-1].workflow != "host":
        slots[-1].workflow = "host"
        slots[-1].visual_type = "host"
        slots[-1].params = {"fallback_reason": "forced_host_ending", **slots[-1].params}

    middle_hosts = [s for s in slots[1:-1] if s.workflow == "host"]
    if not middle_hosts and len(slots) >= 3:
        pivot = len(slots) // 2
        slots[pivot].workflow = "host"
        slots[pivot].visual_type = "host"
        slots[pivot].params = {"fallback_reason": "forced_host_middle", **slots[pivot].params}

    slots = enforce_adjacency_rules(slots)
    from app.config import get_config
    max_host = get_config().defaults.max_host_slots
    slots = cap_host_count(slots, max_host=max_host, enabled_pipelines=enabled_pipelines)
    return slots


def cap_host_count(slots: list[DirectorSlotPlan], max_host: int = 4,
                   enabled_pipelines: set[str] | None = None) -> list[DirectorSlotPlan]:
    """Hard cap: at most *max_host* host-family slots (host + mixed_host_broll).

    Planning-time enforcement: the executor should never need to downgrade slots.
    When downgrading excess host slots, picks the best available pipeline as fallback.
    """
    host_indices = [i for i, s in enumerate(slots) if s.workflow in _HOST_FAMILY]
    if len(host_indices) <= max_host:
        return slots

    c_enabled = enabled_pipelines is None or "c" in enabled_pipelines

    # Enforce opening/closing host before capping (redundant but defensive).
    if c_enabled:
        if slots[0].workflow not in _HOST_FAMILY:
            slots[0].workflow = "host"
            slots[0].visual_type = "host"
            slots[0].params = {"fallback_reason": "forced_host_opening", **slots[0].params}
        if slots[-1].workflow not in _HOST_FAMILY:
            slots[-1].workflow = "host"
            slots[-1].visual_type = "host"
            slots[-1].params = {"fallback_reason": "forced_host_ending", **slots[-1].params}

    # Pick fallback: prefer Pexels if P线 enabled, else HF if H线 enabled, else local
    p_enabled = enabled_pipelines is None or "p" in enabled_pipelines
    h_enabled = enabled_pipelines is None or "h" in enabled_pipelines
    if p_enabled:
        fallback_wf = "broll_pexels"
    elif h_enabled:
        fallback_wf = "hf_chart"
    else:
        fallback_wf = "broll_local"

    keep = {host_indices[0], host_indices[-1]}
    middle = [i for i in host_indices if i not in keep]
    slots_to_keep = max_host - len(keep)
    if slots_to_keep > 0 and middle:
        step = max(1, len(middle) / slots_to_keep)
        for k in range(slots_to_keep):
            idx = middle[min(int(k * step), len(middle) - 1)]
            keep.add(idx)

    for i in host_indices:
        if i not in keep:
            slots[i].workflow = fallback_wf
            slots[i].visual_type = fallback_wf
            slots[i].params = {"fallback_reason": "host_cap_exceeded", **slots[i].params}
            logger.info("[director] slot %d downgraded host-family→%s (cap=%d)", i, fallback_wf, max_host)

    return slots


def enforce_adjacency_rules(slots: list[DirectorSlotPlan]) -> list[DirectorSlotPlan]:
    """No two adjacent host slots, no two adjacent HF slots."""
    _HF = {"hf_chart", "hf_title"}

    def _same_family(a: DirectorSlotPlan, b: DirectorSlotPlan) -> str | None:
        if a.workflow == "host" and b.workflow == "host":
            return "host"
        if a.workflow in _HF and b.workflow in _HF:
            return "hf"
        return None

    def _would_conflict(slots_list: list[DirectorSlotPlan], idx: int, wf: str) -> bool:
        for j in (idx - 1, idx + 1):
            if 0 <= j < len(slots_list):
                if wf == "host" and slots_list[j].workflow == "host":
                    return True
                if wf in _HF and slots_list[j].workflow in _HF:
                    return True
        return False

    for _ in range(2):
        for i in range(len(slots) - 1):
            family = _same_family(slots[i], slots[i + 1])
            if family is None:
                continue
            for j in range(i + 2, min(i + 6, len(slots))):
                if _same_family(slots[i], slots[j]):
                    continue
                if _would_conflict(slots, j, slots[i + 1].workflow):
                    continue
                slots[i + 1], slots[j] = slots[j], slots[i + 1]
                break
    return slots

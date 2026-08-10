"""规则执行 — host 边界强制 / 相邻家族去重 / cap 超限降级.

行为逐字迁移自原 director_parser.py (2026-08-08 包化重构).
"""
from __future__ import annotations

import logging

from app.schemas.director import DirectorSlotPlan

logger = logging.getLogger(__name__)

__all__ = [
    "_HOST_FAMILY",
    "_best_fallback_workflow",
    "enforce_host_rules",
    "cap_host_count",
    "enforce_adjacency_rules",
]

_HOST_FAMILY = {"host", "mixed_host_broll"}
_HF_WORKFLOWS = {"hf_chart", "hf_title", "hf_opening", "hf_quote"}


def _chain_for(prefer: str) -> tuple[tuple[str, str | None], ...]:
    """prefer 类别的降级优先级链: (候选 workflow, 所需管线 key | None=始终可用).

    Priority chains:
      host/mixed_host_broll → hf_title → broll_pexels → broll_local
      hf_chart/hf_title     → host → broll_pexels → broll_local
      broll_pexels          → host → hf_chart → broll_local
    """
    if prefer in _HOST_FAMILY:
        return ((prefer, "c"), ("hf_title", "h"), ("broll_pexels", "p"), ("broll_local", None))
    if prefer in _HF_WORKFLOWS:
        return ((prefer, "h"), ("host", "c"), ("broll_pexels", "p"), ("broll_local", None))
    if prefer == "broll_pexels":
        return ((prefer, "p"), ("host", "c"), ("hf_chart", "h"), ("broll_local", None))
    # broll_local / black_placeholder — always available
    return ((prefer, None),)


def _best_fallback_workflow(enabled_pipelines: set[str] | None, *,
                            prefer: str = "host") -> str:
    """Pick the best available fallback workflow given enabled pipelines."""
    if enabled_pipelines is None:
        return prefer  # All enabled
    # 链末恒为 (wf, None) → next() 必命中, 无 StopIteration
    return next(wf for wf, pipeline in _chain_for(prefer)
                if pipeline is None or pipeline in enabled_pipelines)


def _downgrade_hosts_c_disabled(slots: list[DirectorSlotPlan],
                                enabled_pipelines: set[str] | None) -> None:
    """C线禁用: 将所有 host/mixed_host_broll 降级, 不强制首尾 host."""
    for i, s in enumerate(slots):
        if s.workflow in _HOST_FAMILY:
            old_wf = s.workflow
            alt = _best_fallback_workflow(enabled_pipelines, prefer=old_wf)
            s.workflow = alt
            s.visual_type = alt
            s.params = {"fallback_reason": "c_pipeline_disabled", **s.params}
            logger.info("[director] slot %d downgraded %s→%s (C线禁用)", i, old_wf, alt)


def _force_host_boundaries(slots: list[DirectorSlotPlan]) -> None:
    """C线启用: 强制首尾至少一个 host, 中间至少一个 host."""
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


def _force_opening_card(slots: list[DirectorSlotPlan], enabled_pipelines: set[str] | None) -> None:
    """无人出镜(C线禁用): 强制第 1 个 slot 为 hf_opening (开场字幕卡).

    前 5 秒视觉兜听觉: 用户可能没听清配音, 开场台词必须贴成大字.
    仅当 H 线(hf)可用时生效; 否则回退 broll (至少不能是空卡).
    """
    if not slots:
        return
    first = slots[0]
    # 已是 hf_opening: 仅校准时长
    if first.workflow == "hf_opening":
        first.end_sec = min(first.end_sec, first.start_sec + 8)
        return
    # H 线可用 → 强制 hf_opening (从口播提取台词在渲染层做)
    h_enabled = enabled_pipelines is None or "h" in enabled_pipelines
    if h_enabled:
        first.workflow = "hf_opening"
        first.visual_type = "hf_opening"
        first.params = {"fallback_reason": "forced_opening_card", **first.params}
        first.end_sec = min(first.end_sec, first.start_sec + 8)


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
        _downgrade_hosts_c_disabled(slots, enabled_pipelines)
        # 强制开场字幕卡 (前 5 秒视觉兜听觉)
        _force_opening_card(slots, enabled_pipelines)
        slots = enforce_adjacency_rules(slots)
        from app.config import get_config
        max_host = get_config().defaults.max_host_slots
        return cap_host_count(slots, max_host=max_host, enabled_pipelines=enabled_pipelines)

    _force_host_boundaries(slots)
    slots = enforce_adjacency_rules(slots)
    from app.config import get_config
    max_host = get_config().defaults.max_host_slots
    return cap_host_count(slots, max_host=max_host, enabled_pipelines=enabled_pipelines)


def _force_host_ends(slots: list[DirectorSlotPlan]) -> None:
    """超限兜底: 强制首尾为 host-family (C线启用时)."""
    if slots[0].workflow not in _HOST_FAMILY:
        slots[0].workflow = "host"
        slots[0].visual_type = "host"
        slots[0].params = {"fallback_reason": "forced_host_opening", **slots[0].params}
    if slots[-1].workflow not in _HOST_FAMILY:
        slots[-1].workflow = "host"
        slots[-1].visual_type = "host"
        slots[-1].params = {"fallback_reason": "forced_host_ending", **slots[-1].params}


def _pick_fallback_wf(enabled_pipelines: set[str] | None) -> str:
    """超限 host 的降级目标: 优先 Pexels, 否则 HF, 否则 local."""
    p_enabled = enabled_pipelines is None or "p" in enabled_pipelines
    h_enabled = enabled_pipelines is None or "h" in enabled_pipelines
    if p_enabled:
        return "broll_pexels"
    if h_enabled:
        return "hf_chart"
    return "broll_local"


def _sample_middle_hosts(host_indices: list[int], keep: set[int],
                         slots_to_keep: int) -> list[int]:
    """在中间 host 下标里均匀采样保留 (间距 step, 与原文一致)."""
    middle = [i for i in host_indices if i not in keep]
    if slots_to_keep <= 0 or not middle:
        return []
    step = max(1, len(middle) / slots_to_keep)
    return [middle[min(int(k * step), len(middle) - 1)] for k in range(slots_to_keep)]


def _downgrade_excess_hosts(slots: list[DirectorSlotPlan], host_indices: list[int],
                            keep: set[int], fallback_wf: str, max_host: int) -> None:
    """把 keep 之外的 host-family slot 降级为 fallback_wf."""
    for i in host_indices:
        if i not in keep:
            slots[i].workflow = fallback_wf
            slots[i].visual_type = fallback_wf
            slots[i].params = {"fallback_reason": "host_cap_exceeded", **slots[i].params}
            logger.info("[director] slot %d downgraded host-family→%s (cap=%d)", i, fallback_wf, max_host)


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
        _force_host_ends(slots)

    fallback_wf = _pick_fallback_wf(enabled_pipelines)

    keep = {host_indices[0], host_indices[-1]}
    slots_to_keep = max_host - len(keep)
    keep.update(_sample_middle_hosts(host_indices, keep, slots_to_keep))

    _downgrade_excess_hosts(slots, host_indices, keep, fallback_wf, max_host)
    return slots


def _same_family(a: DirectorSlotPlan, b: DirectorSlotPlan) -> str | None:
    if a.workflow == "host" and b.workflow == "host":
        return "host"
    if a.workflow in _HF_WORKFLOWS and b.workflow in _HF_WORKFLOWS:
        return "hf"
    return None


def _would_conflict(slots_list: list[DirectorSlotPlan], idx: int, wf: str) -> bool:
    for j in (idx - 1, idx + 1):
        if 0 <= j < len(slots_list):
            if wf == "host" and slots_list[j].workflow == "host":
                return True
            if wf in _HF_WORKFLOWS and slots_list[j].workflow in _HF_WORKFLOWS:
                return True
    return False


def _swap_away_conflict(slots: list[DirectorSlotPlan], i: int) -> None:
    """相邻同家族冲突: 在 [i+2, i+6) 窗口内找异家族无冲突槽位换入."""
    for j in range(i + 2, min(i + 6, len(slots))):
        if _same_family(slots[i], slots[j]):
            continue
        if _would_conflict(slots, j, slots[i + 1].workflow):
            continue
        slots[i + 1], slots[j] = slots[j], slots[i + 1]
        break


def enforce_adjacency_rules(slots: list[DirectorSlotPlan]) -> list[DirectorSlotPlan]:
    """No two adjacent host slots, no two adjacent HF slots."""
    for _ in range(2):
        for i in range(len(slots) - 1):
            if _same_family(slots[i], slots[i + 1]) is not None:
                _swap_away_conflict(slots, i)
    return slots

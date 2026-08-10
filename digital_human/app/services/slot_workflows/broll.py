"""Broll local 线: 精确文件 → 语义匹配 → 在线降级.

对应 _EXECUTION_PHASES 的 L 线 (broll_local)。pexels 在线搜索见
broll_pexels.py, black 兜底见 fallback.py, 均由 broll.py 聚合转发。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_config
from app.infrastructure import render_scale_pad
from app.models import DirectorSlot
from app.schemas import get_video_format_spec
from app.services.asset_matcher import (
    MIN_HIT_RATIO,
    match_local_assets,
    register_asset_usage,
)
from app.services.slot_workflows.broll_pexels import execute_broll_pexels_slot
from app.services.slot_workflows.common import ensure_slot_dir

logger = logging.getLogger(__name__)

__all__ = [
    "execute_broll_local_slot",
    "_build_local_keywords",
    "_match_local",
    "_try_exact_file",
    "_strategy_semantic_match",
    "_render_broll_local",
]


def _build_local_keywords(slot: DirectorSlot, params: dict) -> list[str] | None:
    """Return effective keywords: params.keywords, or tokenized category."""
    keywords = params.get("keywords")
    if keywords:
        return keywords if isinstance(keywords, list) else [str(keywords)]
    category = params.get("category") or slot.text_context
    if not category:
        return None
    return [w.strip() for w in re.split(r"[,，\s]+", category) if w.strip()]


def _match_local(db: Session, slot: DirectorSlot, spec: dict, keywords: list[str]):
    """Run asset_matcher semantic matching; returns best result or None.

    精确时长防护 (2026-08-09): render_scale_pad 无 loop, 素材短于 slot 时长
    会黑尾截断, 因此按 slot 精确时长过滤, 只返回时长足够的素材。
    """
    duration = round(slot.end_sec - slot.start_sec, 3)
    location = (slot.params_json or {}).get("location")
    people = (slot.params_json or {}).get("people")
    return match_local_assets(
        db,
        keywords=keywords,
        scenes=(slot.params_json or {}).get("scenes"),
        shot_types=(slot.params_json or {}).get("shot_types"),
        tone=(slot.params_json or {}).get("tone"),
        motion_level=(slot.params_json or {}).get("motion_level"),
        content_density=(slot.params_json or {}).get("content_density"),
        time_of_day=(slot.params_json or {}).get("time_of_day"),
        orientation=spec.get("pexels_orientation") if spec else None,
        location=location,
        people=people,
        min_duration_sec=duration,
        limit=1,
    )


def _try_exact_file(cfg, params: dict) -> Path | None:
    """策略 1: params.file 精确文件名直接定位; 找不到返回 None."""
    file_name = params.get("file")
    if not file_name:
        return None
    candidates = [Path(cfg.materials_dir) / file_name]
    src = next((p for p in candidates if p.exists()), None)
    if src is not None:
        logger.info("[broll_local] exact match: %s", file_name)
    else:
        logger.warning("[broll_local] params.file=%s not found, falling back to keywords match", file_name)
    return src


def _strategy_semantic_match(
    db: Session, slot: DirectorSlot, spec: dict, keywords: list[str],
) -> Path | None:
    """策略 2-3: asset_matcher 语义匹配, 命中率不足时返回 None 走降级.

    ID-034 (2026-08-07): location/people 硬维度硬过滤; 软维度命中率
    不足 MIN_HIT_RATIO(75%) 或结果为 0 → 返回 None, 由调用方降级 pexels。
    """
    results = _match_local(db, slot, spec, keywords)
    if not results:
        return None
    best = results[0]
    hit_ratio = best.get("hit_ratio")
    if hit_ratio is not None and hit_ratio < MIN_HIT_RATIO:
        logger.info(
            "[broll_local] slot %d: local hit_ratio=%.2f < %.0f%%, degrading to pexels download",
            slot.slot_index, hit_ratio, MIN_HIT_RATIO * 100,
        )
        return None
    fp = best.get("file_path")
    if not fp:
        return None
    src = Path(fp)
    if not src.exists():
        return None
    # 素材不复用 (2026-08-09): 命中即登记, 后续 slot 的 used_count.asc() 排序
    # 自然降低其优先级 (与 P 线本地碰撞共用登记语义)。
    register_asset_usage(db, best.get("file_path"))
    logger.info(
        "[broll_local] keyword match: %s (score=%d, hit_ratio=%s)",
        src.name, best.get("score", 0), hit_ratio,
    )
    return src


def _render_broll_local(
    src: Path, root: Path, slot: DirectorSlot, spec: dict,
) -> str:
    """ffmpeg trim + scale + pad → output mp4."""
    duration = round(slot.end_sec - slot.start_sec, 3)
    out_path = root / f"broll_local_{slot.slot_index:03d}.mp4"
    render_scale_pad(
        src, out_path,
        width=spec["width"], height=spec["height"], duration=duration,
    )
    return str(out_path)


def execute_broll_local_slot(db: Session, slot: DirectorSlot) -> str:
    """Pick local material file, trim/pad to target aspect, return mp4 path.

    匹配策略（按优先级）:
    1. params.file 精确文件名 → 直接定位（向后兼容）
    2. params.keywords + 可选维度 → asset_matcher 语义匹配
    3. params.category 作为 keyword 兜底 → asset_matcher
    4. 全部失败 → 降级 broll_pexels 在线下载（避免坠入 black_placeholder）
    """
    root = ensure_slot_dir(slot)
    cfg = get_config().defaults
    spec = get_video_format_spec(slot.director_job.video_format)
    params = slot.params_json or {}

    # 策略 1: 精确文件名
    src = _try_exact_file(cfg, params)
    if src is not None:
        return _render_broll_local(src, root, slot, spec)

    # 策略 2-3: 语义匹配 (含命中率不足时的 None 返回)
    keywords = _build_local_keywords(slot, params)
    if keywords:
        src = _strategy_semantic_match(db, slot, spec, keywords)
        if src is not None:
            return _render_broll_local(src, root, slot, spec)

    # 策略 4: 本地无符合画面 → 降级在线下载 (ID-034)
    logger.warning(
        "[broll_local] slot %d: no local material matching keywords/hard dims, degrading to pexels",
        slot.slot_index,
    )
    return execute_broll_pexels_slot(db, slot)

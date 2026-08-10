"""本地素材语义匹配服务 — 基于 AI 打标数据按 keywords/tags 检索 VideoAsset.

ID-034 (2026-08-07) 匹配契约:
  - 硬维度 location / orientation / people → 独立列硬过滤, 必须全中, 否则排除
  - 软维度 scenes / shot_types / tone / motion_level / content_density / time_of_day
    → 命中率 ≥75% (6 中 ≥4, 传了 4 个需全中) 才算符合画面
  - keywords 是词表包里的画面词, 提供额外精确打分 (不与命中率绑定)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import String, or_
from sqlalchemy.orm import Session

from app.config import get_config
from app.models import VideoAsset

logger = logging.getLogger(__name__)

# 硬维度 (独立列, 硬过滤) / 软维度 (extra JSON + scenes/shot_types 列, 命中率)
HARD_DIMENSIONS = ("location", "orientation", "people")
SOFT_DIMENSIONS = (
    "scenes", "shot_types", "tone",
    "motion_level", "content_density", "time_of_day",
)
# 软维度命中率下限: ≥75% (6 中 ≥4)。已确认 (2026-08-07)。
MIN_HIT_RATIO = 0.75


def match_local_assets(
    db: Session,
    keywords: list[str] | None = None,
    scenes: list[str] | None = None,
    shot_types: list[str] | None = None,
    tone: str | None = None,
    motion_level: str | None = None,
    content_density: str | None = None,
    time_of_day: str | None = None,
    orientation: str | None = None,
    location: str | None = None,
    people: str | None = None,
    min_duration_sec: float | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """根据语义条件搜索本地素材库，返回匹配结果含 file_path 和得分。

    匹配策略 (ID-034):
    - 硬维度 location/orientation/people → 独立列硬过滤, 必须全中, 否则排除
    - 软维度 scenes/shot_types/tone/motion_level/content_density/time_of_day
      → 命中率 ≥75% 才算符合 (传了 4 个需全中)
    - keywords → description_zh/tags 精确打分 (+1 每命中)
    - scenes/shot_types 精确匹配 → +2 每命中

    按 score 降序 + ai_confidence 降序 + used_count 升序排列。
    """
    query = db.query(VideoAsset)

    # ── 硬维度硬过滤 (ID-034): 独立列精确相等, 必须全中 ──
    if orientation:
        query = query.filter(VideoAsset.orientation == orientation)
    if location:
        query = query.filter(VideoAsset.location == location)
    if people:
        query = query.filter(VideoAsset.people == people)
    # 只查本地已有文件的素材
    query = query.filter(VideoAsset.file_path.isnot(None))
    if min_duration_sec:
        # 精确时长防护 (2026-08-09): render_scale_pad 无 loop, 素材短于
        # slot 时长会黑尾截断, 因此要求素材时长 >= slot 精确时长。
        query = query.filter(VideoAsset.duration_sec >= min_duration_sec)

    # ── 软维度候选: 需满足命中率 ≥75% ──
    # scenes/shot_types 值不参与 SQL 过滤 —— SQLite JSON 数组列把中文存成
    # \\uXXXX 字面量 (如 ["城市"] → ["\\u57ce\\u5e02"]), cast(String) + ilike
    # 永远匹配不到明文 (2026-08-09 根因, 曾致本地碰撞 0 命中)。这两维交给
    # 下方 Python 层精确匹配 (asset_scenes/asset_shots), SQL 只按 keywords
    # (明文 desc_zh/en, tags 英文不转义) 与四维英文值 (extra JSON 不转义) 收窄。
    four_val = [(dim, val) for dim, val in (
        ("tone", tone), ("motion_level", motion_level),
        ("content_density", content_density), ("time_of_day", time_of_day),
    ) if val]
    kw_terms = [k for k in (keywords or []) if k]
    has_soft = bool([s for s in (scenes or []) if s]) or bool(
        [s for s in (shot_types or []) if s]) or bool(four_val) or bool(kw_terms)
    if not has_soft:
        # 全软维度 + keywords 均未指定 → 硬过滤即可 (无命中率约束)
        pass
    else:
        term_filters = []
        # keywords: 明文列 (tags/desc_zh/desc_en) 模糊匹配
        for k in kw_terms:
            t = k.lower()
            term_filters.append(or_(
                VideoAsset.tags.cast(String).ilike(f"%{t}%"),
                VideoAsset.description_zh.ilike(f"%{t}%"),
                VideoAsset.description_en.ilike(f"%{t}%"),
            ))
        # 四维英文值: extra JSON 键值对 (值不转义, 带引号匹配)
        for _dim, val in four_val:
            term_filters.append(
                VideoAsset.ai_tags_extra.cast(String).ilike(f'%"{val}"%')
            )
        if term_filters:
            query = query.filter(or_(*term_filters))

    candidates: list[VideoAsset] = query.order_by(
        VideoAsset.ai_tagged_at.desc().nullslast(),
        VideoAsset.used_count.asc(),
    ).limit(min(max(limit * 3, 60), 200)).all()  # 多取一些做精确打分

    # ── 精确打分 + 命中率校验 ──
    scored = []
    for asset in candidates:
        # 软维度命中率: 传了几个软维度, 需命中 ≥75% (6 中 ≥4; 传 4 个需全中)
        soft_requested = 0
        soft_hit = 0
        asset_scenes = [s.lower() for s in (asset.scenes or [])]
        asset_shots = [s.lower() for s in (asset.shot_types or [])]
        extra = asset.ai_tags_extra or {}

        # 先收集所有软维度请求
        soft_requests: list[tuple[str, list[str]]] = [
            ("scenes", scenes or []),
            ("shot_types", shot_types or []),
            ("tone", [tone] if tone else []),
            ("motion_level", [motion_level] if motion_level else []),
            ("content_density", [content_density] if content_density else []),
            ("time_of_day", [time_of_day] if time_of_day else []),
        ]
        for dim, vals in soft_requests:
            if vals:
                soft_requested += 1
                v = vals[0].lower()
                if dim == "scenes" and v in asset_scenes:
                    soft_hit += 1
                elif dim == "shot_types" and v in asset_shots:
                    soft_hit += 1
                elif dim in ("tone", "motion_level", "content_density", "time_of_day"):
                    # 兼容 ai_tags_extra 值为 list (如 time_of_day=["day","night"]) 的脏数据
                    ev = extra.get(dim)
                    if isinstance(ev, list):
                        ev = ev[0] if ev else ""
                    if (ev or "").lower() == v:
                        soft_hit += 1

        if soft_requested:
            ratio = soft_hit / soft_requested
            if ratio < MIN_HIT_RATIO:
                continue  # 软维度命中率不达标 → 排除

        score = 0
        # keywords 精确打分 (词表包画面词, 不与命中率绑定)
        if keywords:
            zh = (asset.description_zh or "").lower()
            en = (asset.description_en or "").lower()
            tag_str = " ".join(asset.tags or []).lower()
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in zh or kw_lower in en:
                    score += 1
                if kw_lower in tag_str:
                    score += 1
        # scenes/shot_types 精确匹配加分
        if scenes:
            for s in scenes:
                if s.lower() in asset_scenes:
                    score += 2
        if shot_types:
            for st in shot_types:
                if st.lower() in asset_shots:
                    score += 2
        # 已 AI 打标加分 (标签更可信)
        if asset.ai_tagged_at is not None:
            score += 1

        # 检查文件实际存在
        fp = Path(asset.file_path)
        if not fp.exists():
            continue

        scored.append((score, soft_hit / soft_requested if soft_requested else 0.0, asset))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, _ratio, asset in scored[:limit]:
        results.append({
            "file": fp.name,
            "file_path": asset.file_path,
            "score": score,
            # 软维度命中率; 未传软维度时返回 None (无命中率约束)
            "hit_ratio": _ratio if _ratio else None,
            "description_zh": asset.description_zh,
            "scenes": asset.scenes,
            "shot_types": asset.shot_types,
            "tags": asset.tags,
            "tone": (asset.ai_tags_extra or {}).get("tone"),
            "motion_level": (asset.ai_tags_extra or {}).get("motion_level"),
            "content_density": (asset.ai_tags_extra or {}).get("content_density"),
            "time_of_day": (asset.ai_tags_extra or {}).get("time_of_day"),
            "orientation": asset.orientation,
            "location": asset.location,
            "people": asset.people,
            "duration_sec": asset.duration_sec,
        })
    return results


def register_asset_usage(db: Session, file_path: str) -> None:
    """登记一次本地素材使用 (素材不复用).

    递增 ``used_count`` (updated_at 由 onupdate 自动刷新)。只增不减;
    不做同 job 硬排除 —— 本地库规模 (1500+) 远不足以支撑 107 slot 全去重,
    由 match_local_assets 的 ``used_count.asc()`` 排序自然把高频素材降优先级。
    """
    asset = (
        db.query(VideoAsset)
        .filter(VideoAsset.file_path == file_path)
        .first()
    )
    if asset is None:
        return
    asset.used_count = (asset.used_count or 0) + 1
    db.commit()


def pick_local_fallback() -> Path | None:
    """从 materials_dir 随机选一个可用素材文件（兜底），不依赖 DB."""
    import random

    cfg = get_config().defaults
    materials_dir = Path(cfg.materials_dir)
    if not materials_dir.exists():
        return None

    videos = sorted(
        p for p in materials_dir.rglob("*")
        if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm") and p.is_file()
    )
    if not videos:
        return None
    return random.choice(videos)

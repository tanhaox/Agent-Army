"""本地素材语义匹配服务 — 基于 AI 打标数据按 keywords/tags 检索 VideoAsset."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import String, or_
from sqlalchemy.orm import Session

from app.config import get_config
from app.models import VideoAsset

logger = logging.getLogger(__name__)


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
    limit: int = 5,
) -> list[dict[str, Any]]:
    """根据语义条件搜索本地素材库，返回匹配结果含 file_path 和得分。

    匹配策略（加权）:
    - keywords 命中 description_zh/tags → +1 每命中
    - scenes/shot_types 精确匹配 → +2 每命中
    - ai_tags_extra JSON 字段匹配 → +1 每命中
    - orientation/location → 硬过滤

    按 score 降序 + ai_confidence 降序 + used_count 升序排列。
    """
    query = db.query(VideoAsset)

    # ── 硬过滤 ──
    if orientation:
        query = query.filter(VideoAsset.orientation == orientation)
    if location:
        query = query.filter(VideoAsset.location == location)
    # 只查本地已有文件的素材
    query = query.filter(VideoAsset.file_path.isnot(None))

    # ── 关键词模糊匹配 (OR 语义，缩小候选集) ──
    if keywords:
        kw_filters = []
        for kw in keywords:
            like = f"%{kw}%"
            kw_filters.append(VideoAsset.description_zh.ilike(like))
            kw_filters.append(VideoAsset.description_en.ilike(like))
            kw_filters.append(VideoAsset.tags.cast(String).ilike(like))
            kw_filters.append(VideoAsset.scenes.cast(String).ilike(like))
            kw_filters.append(VideoAsset.shot_types.cast(String).ilike(like))
        query = query.filter(or_(*kw_filters))

    # ── 场景/镜头 交集预过滤 (至少命中一个) ──
    if scenes:
        scene_filters = []
        for s in scenes:
            scene_filters.append(VideoAsset.scenes.cast(String).ilike(f"%{s}%"))
        query = query.filter(or_(*scene_filters))
    if shot_types:
        st_filters = []
        for st in shot_types:
            st_filters.append(VideoAsset.shot_types.cast(String).ilike(f"%{st}%"))
        query = query.filter(or_(*st_filters))

    # ── ai_tags_extra JSON 过滤 (SQLite json_extract) ──
    if tone:
        query = query.filter(
            VideoAsset.ai_tags_extra.isnot(None),
        )
    if motion_level:
        query = query.filter(
            VideoAsset.ai_tags_extra.isnot(None),
        )
    if content_density:
        query = query.filter(
            VideoAsset.ai_tags_extra.isnot(None),
        )
    if time_of_day:
        query = query.filter(
            VideoAsset.ai_tags_extra.isnot(None),
        )

    candidates: list[VideoAsset] = query.order_by(
        VideoAsset.ai_tagged_at.desc().nullslast(),
        VideoAsset.used_count.asc(),
    ).limit(min(limit * 3, 50)).all()  # 多取一些做精确打分

    # ── 精确打分排序 ──
    scored = []
    for asset in candidates:
        score = 0
        # keywords 命中
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
        # scenes/shot_types 精确匹配
        asset_scenes = [s.lower() for s in (asset.scenes or [])]
        asset_shots = [s.lower() for s in (asset.shot_types or [])]
        if scenes:
            for s in scenes:
                if s.lower() in asset_scenes:
                    score += 2
        if shot_types:
            for st in shot_types:
                if st.lower() in asset_shots:
                    score += 2
        # ai_tags_extra 匹配
        extra = asset.ai_tags_extra or {}
        if tone and extra.get("tone") == tone:
            score += 1
        if motion_level and extra.get("motion_level") == motion_level:
            score += 1
        if content_density and extra.get("content_density") == content_density:
            score += 1
        if time_of_day and extra.get("time_of_day") == time_of_day:
            score += 1
        # 已 AI 打标加分 (标签更可信)
        if asset.ai_tagged_at is not None:
            score += 1

        # 检查文件实际存在
        fp = Path(asset.file_path)
        if not fp.exists():
            continue

        scored.append((score, asset))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, asset in scored[:limit]:
        results.append({
            "file": fp.name,
            "file_path": asset.file_path,
            "score": score,
            "description_zh": asset.description_zh,
            "scenes": asset.scenes,
            "shot_types": asset.shot_types,
            "tags": asset.tags,
            "tone": (asset.ai_tags_extra or {}).get("tone"),
            "motion_level": (asset.ai_tags_extra or {}).get("motion_level"),
            "content_density": (asset.ai_tags_extra or {}).get("content_density"),
            "time_of_day": (asset.ai_tags_extra or {}).get("time_of_day"),
            "orientation": asset.orientation,
            "duration_sec": asset.duration_sec,
        })
    return results


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

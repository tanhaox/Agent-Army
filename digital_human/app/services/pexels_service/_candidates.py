"""Pexels resolve — 候选视频处理与下载编排。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import MaterialAsset
from app.services.pexels_service._db import (
    increment_quota,
    register_video_asset,
    upsert_asset,
)
from app.services.pexels_service._http import download
from app.services.pexels_service._local import asset_to_item
from app.services.pexels_service.types import (
    PexelsResolveError,
    ResolveItem,
)
from app.services.pexels_utils import (
    API_DURATION, API_HEIGHT, API_ID, API_LINK, API_VIDEO_FILES, API_WIDTH,
    RESOLUTION_WIDTHS, int_duration, orientation_ok, pick_video_file,
)

logger = logging.getLogger(__name__)

__all__ = ["process_candidates"]


def _widths_sorted(prefer_resolution: str) -> list[tuple[str, int]]:
    """按与偏好分辨率宽度差的绝对值排序的 (label, width) 列表."""
    prefer_width = RESOLUTION_WIDTHS[prefer_resolution]
    return sorted(RESOLUTION_WIDTHS.items(), key=lambda x: abs(x[1] - prefer_width))


def _candidate_downloadable(
    video: dict[str, Any],
    min_duration_sec: int,
    orientation: str,
    exclude_pexels_ids: set[int],
) -> bool:
    """候选过滤 (时长/方向/pexels_id/黑名单). 返回是否可处理."""
    if int_duration(video.get(API_DURATION)) < min_duration_sec:
        return False
    width = video.get(API_WIDTH, 0)
    height = video.get(API_HEIGHT, 0)
    if not orientation_ok(width, height, orientation):
        return False
    pexels_id = video.get(API_ID)
    if not pexels_id:
        return False
    if pexels_id in exclude_pexels_ids:
        return False
    return True


def _handle_candidate(
    svc: Any, db: Session, video: dict[str, Any],
    prefer_resolution: str, min_duration_sec: int, orientation: str,
    remaining_quota: int, tags_str: str, materials_dir: str,
    exclude_pexels_ids: set[int], raw_query: str,
) -> tuple[ResolveItem | None, bool]:
    """处理单条候选: 过滤 → 复用/下载 → 入库.

    Returns: (item, consumed) — item None 表示跳过; consumed=True 表示消耗 1 下载配额."""
    if not _candidate_downloadable(video, min_duration_sec, orientation, exclude_pexels_ids):
        return None, False

    pexels_id = video.get(API_ID)
    existing = db.query(MaterialAsset).filter(MaterialAsset.pexels_id == pexels_id).first()
    if existing and existing.local_path and Path(existing.local_path).exists():
        return asset_to_item(existing), False
    if remaining_quota <= 0:
        return None, False

    chosen = pick_video_file(video.get(API_VIDEO_FILES, []), _widths_sorted(prefer_resolution))
    if chosen is None:
        return None, False
    source_url = chosen.get(API_LINK)
    if not source_url:
        return None, False

    try:
        local_path = download(svc, source_url, pexels_id, materials_dir)
    except PexelsResolveError as exc:
        logger.warning("Download failed pexels_id=%s: %s", pexels_id, exc)
        return None, False
    if local_path is None:
        return None, False

    file_size = Path(local_path).stat().st_size
    increment_quota(db, pexels_id, file_size)
    asset = upsert_asset(db, existing, video, chosen, source_url, local_path, tags_str)
    register_video_asset(db, video, chosen, local_path, tags_str, raw_query=raw_query)
    return asset_to_item(asset), True


def process_candidates(
    svc: Any, db: Session, videos: list[dict[str, Any]], needed: int,
    prefer_resolution: str, min_duration_sec: int, orientation: str,
    remaining_quota: int, tags_str: str, materials_dir: str,
    exclude_pexels_ids: set[int] | None = None,
    raw_query: str = "",
) -> list[ResolveItem]:
    """遍历候选视频, 下载并入库直到凑够 needed."""
    results: list[ResolveItem] = []
    exclude_pexels_ids = exclude_pexels_ids or set()
    if remaining_quota <= 0 or needed <= 0:
        return results

    for video in videos:
        if len(results) >= needed:
            break
        item, consumed = _handle_candidate(
            svc, db, video,
            prefer_resolution, min_duration_sec, orientation,
            remaining_quota, tags_str, materials_dir,
            exclude_pexels_ids, raw_query,
        )
        if item is None:
            continue
        results.append(item)
        if consumed:
            remaining_quota -= 1

    return results

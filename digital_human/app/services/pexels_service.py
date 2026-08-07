"""Pexels 素材 resolve 服务模块 (ID-003).

视觉导演 import-only 调用范式:

    from app.services.pexels_service import pexels_service
    materials = pexels_service.resolve("port cranes", max_results=3)

行为:
  - 本地缓存命中 → 直接返回本地路径(零网络).
  - 本地缺失 → 调 Pexels API 下载 FHD mp4 → 落 DB → 返回本地路径.
  - quota 超限 / 网络错 / 找不到 → 返回元数据并标记 degraded=True.
  - 全部失败 → 返回空列表并标记 degraded=True.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import get_config
from ..database import get_db
from ..models import DownloadLog, MaterialAsset, VideoAsset
from .asset_tagging import generate_asset_no, infer_tags
from .pexels_utils import (
    API_DURATION, API_FPS, API_HEIGHT, API_ID, API_LINK,
    API_USER, API_USER_NAME, API_USER_URL, API_VIDEO_FILES, API_WIDTH,
    RESOLUTION_WIDTHS, int_duration, int_fps, orientation_ok,
    pick_video_file, resolution_label, validate_video,
)

logger = logging.getLogger(__name__)

PEXELS_API_BASE = "https://api.pexels.com/v1"


class PexelsAuthError(RuntimeError):
    """PEXELS_API_KEY 无效或缺失时抛出(不静默)."""


class PexelsResolveError(RuntimeError):
    """可恢复的内部错误,resolve 会 catch 并降级."""


@dataclass
class ResolveItem:
    """单条 resolve 结果 — 与 app.schemas.ResolveItem 字段对齐."""

    duration_sec: int
    width: int
    height: int
    photographer: str
    photographer_url: str
    pexels_url: str
    id: int | None = None
    pexels_id: int | None = None
    local_path: str | None = None
    source_url: str | None = None
    degraded: bool = False
    reason: str | None = None
    fps: int | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "pexels_id": self.pexels_id, "local_path": self.local_path,
            "source_url": self.source_url, "degraded": self.degraded, "reason": self.reason,
            "duration_sec": self.duration_sec, "width": self.width, "height": self.height,
            "fps": self.fps, "photographer": self.photographer,
            "photographer_url": self.photographer_url, "pexels_url": self.pexels_url,
            "tags": self.tags,
        }


class PexelsService:
    """Pexels resolve 服务单例."""

    def __init__(self) -> None:
        self._session: Session | None = None
        self._api_key: str | None = None
        self._requests_session: requests.Session | None = None

    # ── 配置 / session 懒加载 ──

    def _session_factory(self) -> Session:
        return next(get_db())

    def _close_session(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            except Exception:  # noqa: BLE001
                pass
            self._session = None

    def _ensure_config(self) -> None:
        cfg = get_config()
        if self._api_key is None:
            key_env = cfg.defaults.pexels_api_key_env
            self._api_key = os.environ.get(key_env)
            if not self._api_key:
                raise PexelsAuthError(f"Missing Pexels API key in environment variable {key_env}")

    def _ensure_session(self) -> Session:
        if self._session is None:
            self._session = self._session_factory()
        return self._session

    def _http(self) -> requests.Session:
        if self._requests_session is None:
            self._requests_session = requests.Session()
            self._requests_session.headers.update({"Authorization": self._api_key or "", "Accept": "application/json"})
        return self._requests_session

    def _cfg(self):
        return get_config().defaults

    # ── 公开 API ──

    def resolve(
        self, query: str, max_results: int | None = None,
        min_duration_sec: int | None = None, prefer_resolution: str | None = None,
        orientation: str = "any", exclude_pexels_ids: set[int] | None = None,
    ) -> list[ResolveItem]:
        try:
            self._ensure_config()
        except PexelsAuthError:
            raise

        exclude_pexels_ids = exclude_pexels_ids or set()

        cfg = self._cfg()
        max_results = max_results or cfg.pexels_default_max_results
        min_duration_sec = min_duration_sec or cfg.pexels_min_duration_sec
        prefer_resolution = prefer_resolution or cfg.pexels_preferred_resolution
        if prefer_resolution not in RESOLUTION_WIDTHS:
            prefer_resolution = "FHD"

        tags = [t.strip().lower() for t in query.split() if t.strip()]
        tags_str = ",".join(tags)

        try:
            db = self._ensure_session()
            # 用户标记为厌恶的素材永久拉黑, 不再返回也不再下载
            dislike_ids = self._get_dislike_pexels_ids(db)
            exclude_pexels_ids = exclude_pexels_ids | dislike_ids

            local_items = self._query_local(
                db, tags, max_results, min_duration_sec, orientation,
                exclude_pexels_ids=exclude_pexels_ids,
            )
            if len(local_items) >= max_results:
                return local_items[:max_results]

            needed = max_results - len(local_items)
            quota = cfg.pexels_daily_download_quota
            used_today = self._get_quota_used_today(db)
            remaining_quota = max(0, quota - used_today)

            try:
                videos = self._search_pexels(query, per_page=max(needed * 3, 10), orientation=orientation)
            except PexelsAuthError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("Pexels search failed: %s", exc)
                return self._merge_with_degraded(local_items, needed, reason="search_failed")

            downloaded = self._process_candidates(
                db, videos, needed, prefer_resolution, min_duration_sec,
                orientation, remaining_quota, tags_str, cfg.materials_dir,
                exclude_pexels_ids=exclude_pexels_ids, raw_query=query,
            )
            result = local_items + downloaded
            if len(result) < max_results:
                result = self._fill_with_degraded(
                    result, videos, max_results, prefer_resolution, min_duration_sec,
                    exclude_pexels_ids=exclude_pexels_ids,
                )

            db.commit()
            return result[:max_results]

        except PexelsAuthError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pexels resolve unexpected error: %s", exc)
            return []
        finally:
            self._close_session()

    def resolve_descending(
        self, keywords: list[str], max_results: int | None = None,
        min_duration_sec: int | None = None, prefer_resolution: str | None = None,
        orientation: str = "any", exclude_pexels_ids: set[int] | None = None,
    ) -> tuple[list[ResolveItem], str | None]:
        """降维搜索 (2026-08-01, 用户指定策略, 见 [[pexels-descending-search]]).

        LLM 给出按重要性排序的关键词数组 (最多 6 个, 第 1 个是全局主体关键词).
        依次用 [全部, 去掉末尾1个, 去掉末尾2个, ...] 搜索, 命中非空即停.
        主关键词永远保留在查询里 → 保证全片画面地域/主题一致性.

        Args:
            keywords: 按重要性排序的检索词, 例如 ["china","street","busy","traffic"].
                      keywords[0] 是全局主体词, 必须出现在每次尝试中.

        Returns:
            (items, used_query): items 为降维后首个非空结果 (可能为空); used_query
            为实际命中的查询串 (供日志/调试), 全部失败时返回 ([], None).
        """
        clean = [k.strip() for k in keywords if k and k.strip()]
        if not clean:
            return [], None
        clean = clean[:6]
        items: list[ResolveItem] = []
        used_query: str | None = None
        for n in range(len(clean), 0, -1):
            sub = clean[:n]
            query = " ".join(sub)
            try:
                items = self.resolve(
                    query, max_results=max_results,
                    min_duration_sec=min_duration_sec,
                    prefer_resolution=prefer_resolution,
                    orientation=orientation,
                    exclude_pexels_ids=exclude_pexels_ids,
                )
            except PexelsAuthError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("resolve_descending attempt %r failed: %s", query, exc)
                items = []
            if items:
                used_query = query
                logger.info("resolve_descending hit at %d keyword(s): %r", n, query)
                break
        return items, used_query

    # ── 本地缓存 ──

    def _query_local(self, db: Session, tags: list[str], max_results: int, min_duration_sec: int, orientation: str = "any", exclude_pexels_ids: set[int] | None = None) -> list[ResolveItem]:
        if not tags:
            return []
        exclude_pexels_ids = exclude_pexels_ids or set()
        pattern = f"%{tags[0]}%"
        q = (
            db.query(MaterialAsset)
            .filter(MaterialAsset.tags.like(pattern))
            .filter(MaterialAsset.duration_sec >= min_duration_sec)
            .filter(MaterialAsset.local_path.isnot(None))
        )
        if exclude_pexels_ids:
            q = q.filter(~MaterialAsset.pexels_id.in_(exclude_pexels_ids))
        if orientation == "portrait":
            q = q.filter(MaterialAsset.height > MaterialAsset.width)
        elif orientation == "landscape":
            q = q.filter(MaterialAsset.width >= MaterialAsset.height)
        elif orientation == "square":
            # 近方形: 宽高比 0.75 ~ 1.33 (3:4 ~ 4:3), 与 pexels_utils.orientation_ok 一致 (2026-08-01)
            q = q.filter(
                MaterialAsset.width / MaterialAsset.height >= 0.75,
                MaterialAsset.width / MaterialAsset.height <= 1.33,
            )
        rows = q.order_by(MaterialAsset.created_at.desc()).limit(max_results).all()
        items: list[ResolveItem] = []
        for r in rows:
            if r.local_path and Path(r.local_path).exists():
                items.append(self._asset_to_item(r))
            else:
                r.local_path = None
        return items

    def _asset_to_item(self, asset: MaterialAsset) -> ResolveItem:
        return ResolveItem(
            id=asset.id, pexels_id=asset.pexels_id, local_path=asset.local_path,
            source_url=asset.source_url,
            degraded=False, duration_sec=asset.duration_sec,
            width=asset.width, height=asset.height, fps=asset.fps,
            photographer=asset.photographer, photographer_url=asset.photographer_url,
            pexels_url=asset.pexels_url, tags=[t for t in asset.tags.split(",") if t],
        )

    # ── Pexels API ──

    def _search_pexels(self, query: str, per_page: int, page: int = 1, orientation: str = "any") -> list[dict[str, Any]]:
        url = f"{PEXELS_API_BASE}/videos/search"
        params: dict[str, Any] = {"query": query, "per_page": min(per_page, 80), "page": page}
        # Pexels API 官方 orientation 只支持 portrait/landscape; square 时不下发,
        # 交给本地 orientation_ok(宽高比) 兜底过滤 (2026-08-01)。
        if orientation in ("portrait", "landscape"):
            params["orientation"] = orientation
        try:
            resp = self._http().get(url, params=params, timeout=(10, 30))
        except requests.exceptions.RequestException as exc:
            raise PexelsResolveError(f"network error: {exc}") from exc
        if resp.status_code == 401:
            raise PexelsAuthError(f"Pexels API returned 401. url={url}")
        if resp.status_code != 200:
            raise PexelsResolveError(f"Pexels API status {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise PexelsResolveError(f"invalid json: {exc}") from exc
        return data.get("videos", [])

    # ── 候选处理 / 下载 ──

    def _process_candidates(
        self, db: Session, videos: list[dict[str, Any]], needed: int,
        prefer_resolution: str, min_duration_sec: int, orientation: str,
        remaining_quota: int, tags_str: str, materials_dir: str,
        exclude_pexels_ids: set[int] | None = None,
        raw_query: str = "",
    ) -> list[ResolveItem]:
        results: list[ResolveItem] = []
        exclude_pexels_ids = exclude_pexels_ids or set()
        if remaining_quota <= 0 or needed <= 0:
            return results

        prefer_width = RESOLUTION_WIDTHS[prefer_resolution]
        widths_sorted = sorted(RESOLUTION_WIDTHS.items(), key=lambda x: abs(x[1] - prefer_width))

        for video in videos:
            if len(results) >= needed:
                break
            duration = int_duration(video.get(API_DURATION))
            if duration < min_duration_sec:
                continue
            width = video.get(API_WIDTH, 0)
            height = video.get(API_HEIGHT, 0)
            if not orientation_ok(width, height, orientation):
                continue
            pexels_id = video.get(API_ID)
            if not pexels_id:
                continue
            if pexels_id in exclude_pexels_ids:
                continue

            existing = db.query(MaterialAsset).filter(MaterialAsset.pexels_id == pexels_id).first()
            if existing and existing.local_path and Path(existing.local_path).exists():
                results.append(self._asset_to_item(existing))
                continue
            if remaining_quota <= 0:
                continue

            chosen = pick_video_file(video.get(API_VIDEO_FILES, []), widths_sorted)
            if chosen is None:
                continue
            source_url = chosen.get(API_LINK)
            if not source_url:
                continue

            try:
                local_path = self._download(source_url, pexels_id, materials_dir)
            except PexelsResolveError as exc:
                logger.warning("Download failed pexels_id=%s: %s", pexels_id, exc)
                continue
            if local_path is None:
                continue

            file_size = Path(local_path).stat().st_size
            self._increment_quota(db, pexels_id, file_size)
            remaining_quota -= 1

            asset = self._upsert_asset(db, existing, video, chosen, source_url, local_path, tags_str)
            self._register_video_asset(db, video, chosen, source_url, local_path, tags_str, raw_query=raw_query)
            results.append(self._asset_to_item(asset))

        return results

    # ── 下载 ──

    def _download(self, url: str, pexels_id: int, materials_dir: str) -> str | None:
        root = Path(materials_dir)
        root.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or ".mp4"
        if ext.lower() not in {".mp4", ".mov", ".webm"}:
            ext = ".mp4"
        dest = root / f"pexels_{pexels_id}{ext}"

        try:
            with self._http().get(url, stream=True, timeout=(10, 300)) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except requests.exceptions.RequestException as exc:
            if dest.exists():
                dest.unlink()
            raise PexelsResolveError(f"download network error: {exc}") from exc
        except OSError as exc:
            if dest.exists():
                dest.unlink()
            raise PexelsResolveError(f"disk write error: {exc}") from exc

        if not validate_video(dest):
            dest.unlink()
            raise PexelsResolveError(f"ffprobe validation failed: {dest}")
        return str(dest.resolve())

    # ── DB 写入 ──

    def _upsert_asset(self, db: Session, existing: MaterialAsset | None,
                      video: dict[str, Any], chosen: dict[str, Any],
                      source_url: str, local_path: str, tags_str: str) -> MaterialAsset:
        photographer = video.get(API_USER, {}).get(API_USER_NAME) or "Unknown Photographer"
        photographer_url = video.get(API_USER, {}).get(API_USER_URL) or "https://www.pexels.com"
        pexels_url = video.get("url") or f"https://www.pexels.com/video/{video.get(API_ID)}"
        width = chosen.get(API_WIDTH, video.get(API_WIDTH, 0))
        height = chosen.get(API_HEIGHT, video.get(API_HEIGHT, 0))
        res = resolution_label(width)

        if existing is None:
            asset = MaterialAsset(
                pexels_id=video.get(API_ID), source_url=source_url, pexels_url=pexels_url,
                photographer=photographer, photographer_url=photographer_url,
                local_path=local_path, duration_sec=int_duration(video.get(API_DURATION)),
                width=width, height=height,
                fps=int_fps(chosen.get(API_FPS) or video.get(API_FPS)),
                resolution=res, tags=tags_str,
            )
            db.add(asset)
            db.flush()
        else:
            existing.local_path = local_path
            existing.source_url = source_url
            existing.pexels_url = pexels_url
            existing.photographer = photographer
            existing.photographer_url = photographer_url
            existing.duration_sec = int_duration(video.get(API_DURATION))
            existing.width = width
            existing.height = height
            existing.fps = int_fps(chosen.get(API_FPS) or video.get(API_FPS))
            existing.resolution = res
            existing.tags = tags_str
            asset = existing
        return asset

    def _increment_quota(self, db: Session, pexels_id: int, size_bytes: int) -> None:
        db.add(DownloadLog(date=date.today(), pexels_id=pexels_id, bytes=size_bytes))

    def _register_video_asset(
        self, db: Session, video: dict[str, Any], chosen: dict[str, Any],
        source_url: str, local_path: str, tags_str: str,
        raw_query: str = "",
    ) -> None:
        """Register downloaded video into VideoAsset library (dedup by pexels_id)."""
        pexels_id = video.get(API_ID)
        if not pexels_id:
            return
        # 去重: 已存在则跳过
        if db.query(VideoAsset).filter(VideoAsset.pexels_id == pexels_id).first():
            return
        width = chosen.get(API_WIDTH, video.get(API_WIDTH, 0))
        height = chosen.get(API_HEIGHT, video.get(API_HEIGHT, 0))
        photographer = video.get(API_USER, {}).get(API_USER_NAME) or ""
        pexels_url = video.get("url") or f"https://www.pexels.com/video/{pexels_id}"

        tags = infer_tags(raw_query or tags_str, width, height)
        asset_no = generate_asset_no(db)

        va = VideoAsset(
            asset_no=asset_no,
            source="pexels",
            pexels_id=pexels_id,
            file_path=local_path,
            orientation=tags["orientation"],
            width=width,
            height=height,
            duration_sec=int_duration(video.get(API_DURATION)),
            description_en=None,
            description_zh=None,
            photographer=photographer,
            source_url=pexels_url,
            raw_query=(raw_query or tags_str)[:512],
            source_type=tags["source_type"],
            location=tags["location"],
            scenes=tags["scenes"],
            shot_types=tags["shot_types"],
            people=tags["people"],
            preference="neutral",
            tags=[t for t in tags_str.split(",") if t] if tags_str else [],
        )
        db.add(va)

    def _get_quota_used_today(self, db: Session) -> int:
        return db.query(func.count(DownloadLog.id)).filter(DownloadLog.date == date.today()).scalar() or 0

    def _get_dislike_pexels_ids(self, db: Session) -> set[int]:
        """加载用户标记为 dislike 的 pexels_id 黑名单."""
        rows = (
            db.query(VideoAsset.pexels_id)
            .filter(VideoAsset.preference == "dislike", VideoAsset.pexels_id.isnot(None))
            .all()
        )
        return {r[0] for r in rows if r[0]}

    # ── 降级补齐 ──

    def _merge_with_degraded(self, local_items: list[ResolveItem], needed: int, reason: str) -> list[ResolveItem]:
        for item in local_items:
            item.degraded = True
            item.reason = reason
        return local_items

    def _fill_with_degraded(self, current: list[ResolveItem], videos: list[dict[str, Any]],
                            max_results: int, prefer_resolution: str, min_duration_sec: int,
                            exclude_pexels_ids: set[int] | None = None) -> list[ResolveItem]:
        existing_pexels = {item.pexels_id for item in current if item.pexels_id is not None}
        seen_urls = {item.source_url for item in current if item.source_url}
        exclude_pexels_ids = exclude_pexels_ids or set()
        for video in videos:
            if len(current) >= max_results:
                break
            pexels_id = video.get(API_ID)
            if pexels_id and pexels_id in existing_pexels:
                continue
            if pexels_id in exclude_pexels_ids:
                continue
            duration = int_duration(video.get(API_DURATION))
            if duration < min_duration_sec:
                continue
            chosen = pick_video_file(video.get(API_VIDEO_FILES, []), [(prefer_resolution, RESOLUTION_WIDTHS[prefer_resolution])])
            source_url = chosen.get(API_LINK) if chosen else None
            if source_url in seen_urls:
                continue
            photographer = video.get(API_USER, {}).get(API_USER_NAME) or "Unknown Photographer"
            photographer_url = video.get(API_USER, {}).get(API_USER_URL) or "https://www.pexels.com"
            pexels_url = video.get("url") or f"https://www.pexels.com/video/{pexels_id}"
            width = chosen.get(API_WIDTH, video.get(API_WIDTH, 0)) if chosen else video.get(API_WIDTH, 0)
            height = chosen.get(API_HEIGHT, video.get(API_HEIGHT, 0)) if chosen else video.get(API_HEIGHT, 0)
            current.append(ResolveItem(
                duration_sec=duration, width=width, height=height,
                photographer=photographer, photographer_url=photographer_url,
                pexels_url=pexels_url, source_url=source_url,
                degraded=True, reason="quota_exceeded_or_unreachable",
                fps=int_fps(chosen.get(API_FPS) if chosen else video.get(API_FPS)),
            ))
        return current


# 模块级单例
pexels_service = PexelsService()

"""Pexels resolve — API 搜索与文件下载。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from app.services.pexels_service._session import http_session
from app.services.pexels_service.types import (
    PEXELS_API_BASE,
    PexelsAuthError,
    PexelsResolveError,
)
from app.services.pexels_utils import validate_video

__all__ = ["search_pexels", "download"]


def search_pexels(
    svc: Any, query: str, per_page: int, page: int = 1, orientation: str = "any",
) -> list[dict[str, Any]]:
    """调 Pexels API 搜索视频, 返回原始 video dict 列表."""
    url = f"{PEXELS_API_BASE}/videos/search"
    params: dict[str, Any] = {"query": query, "per_page": min(per_page, 80), "page": page}
    # Pexels API 官方 orientation 只支持 portrait/landscape; square 时不下发,
    # 交给本地 orientation_ok(宽高比) 兜底过滤 (2026-08-01)。
    if orientation in ("portrait", "landscape"):
        params["orientation"] = orientation
    try:
        resp = http_session(svc).get(url, params=params, timeout=(10, 30))
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


def _remove_partial(dest: Path) -> None:
    """下载中断时清理半成品文件."""
    if dest.exists():
        dest.unlink()


def download(svc: Any, url: str, pexels_id: int, materials_dir: str) -> str | None:
    """流式下载视频到 materials 目录, ffprobe 校验后返回绝对路径."""
    root = Path(materials_dir)
    root.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix or ".mp4"
    if ext.lower() not in {".mp4", ".mov", ".webm"}:
        ext = ".mp4"
    dest = root / f"pexels_{pexels_id}{ext}"

    try:
        with http_session(svc).get(url, stream=True, timeout=(10, 300)) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.RequestException as exc:
        _remove_partial(dest)
        raise PexelsResolveError(f"download network error: {exc}") from exc
    except OSError as exc:
        _remove_partial(dest)
        raise PexelsResolveError(f"disk write error: {exc}") from exc

    if not validate_video(dest):
        dest.unlink()
        raise PexelsResolveError(f"ffprobe validation failed: {dest}")
    return str(dest.resolve())

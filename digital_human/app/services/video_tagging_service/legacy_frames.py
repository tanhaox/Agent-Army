"""视频打标 — 已废弃的等间距抽帧 (保留向后兼容).

请改用 app.services.frame_extraction.smart_extract_frames() 进行智能抽帧.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = ["extract_keyframes"]


def _extract_frame_at(mp4_path: Path, png_path: Path, at_seconds: float, label: str) -> bool:
    """复用 ffmpeg 子进程提取单帧 (内部工具函数)."""
    if not shutil.which("ffmpeg"):
        logger.warning("ffmpeg not on PATH; skip frame extraction")
        return False
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{at_seconds:.3f}",
        "-i", str(mp4_path),
        "-vframes", "1",
        str(png_path),
    ]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=20, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg %s extraction timed out", label)
        return False
    ok = r.returncode == 0 and png_path.exists() and png_path.stat().st_size > 0
    if not ok:
        logger.warning("ffmpeg %s extraction failed: %s", label, r.stderr[:200])
    return ok


def extract_keyframes(video_path: str, duration: float, tmpdir: Path) -> list[Path]:
    """[已废弃] 在视频 25%/50%/75% 时间点抽取 3 帧.

    请改用 frame_extraction.smart_extract_frames() 进行智能抽帧.
    保留此函数用于向后兼容.
    """
    mp4 = Path(video_path)
    if not mp4.exists():
        logger.warning("Video file not found: %s", video_path)
        return []

    frames = []
    start_offset = min(0.5, duration * 0.05)
    positions = {
        "25%": max(start_offset, duration * 0.25),
        "50%": max(start_offset, duration * 0.50),
        "75%": max(start_offset, duration * 0.75),
    }
    for label, sec in positions.items():
        png_path = tmpdir / f"frame_{label.replace('%', 'pct')}.png"
        ok = _extract_frame_at(mp4, png_path, sec, label)
        if ok:
            frames.append(png_path)
    return frames

"""智能抽帧服务 — 场景检测 + 代表性帧选取, 替代固定 25%/50%/75%.

两阶段策略:
1. ffmpeg scdet 检测场景变化点
2. 场景变化充分时: 取变化点帧 + 段中间帧
3. 场景变化不足时: 退回到均匀采样
4. 上限 12 帧, 控制 LLM token 消耗
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FRAMES = 12
FALLBACK_FRAMES = 10


def _run_ffmpeg_scdet(video_path: Path, threshold: float = 10.0) -> list[float]:
    """运行 ffmpeg scdet 滤镜, 返回场景变化时间点列表."""
    if not shutil.which("ffmpeg"):
        logger.warning("ffmpeg not on PATH; scdet unavailable")
        return []

    cmd = [
        "ffmpeg", "-y", "-loglevel", "info",
        "-i", str(video_path),
        "-vf", f"scdet=threshold={threshold},metadata=print",
        "-an", "-f", "null", "-",
    ]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=120, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg scdet timed out for %s", video_path.name)
        return []

    # Parse stderr for "lavfi.scd.time=" lines
    times: list[float] = []
    for line in r.stderr.splitlines():
        m = re.search(r"lavfi\.scd\.time=(\d+\.?\d*)", line)
        if m:
            try:
                times.append(float(m.group(1)))
            except ValueError:
                pass
    return times


def _build_extraction_timestamps(
    scene_times: list[float],
    duration: float,
    max_frames: int = MAX_FRAMES,
) -> list[float]:
    """根据场景变化时间点构建抽帧时间戳列表.

    策略:
    - 场景变化 >= max_frames//2: 取场景变化点 (每个镜头起点), cap 到 max_frames
    - 场景变化 < 3: 退回到均匀采样 FALLBACK_FRAMES 帧
    - 适中: 场景变化点 + 段中间帧交错排列, 优先覆盖更多镜头
    """
    if not scene_times or len(scene_times) < 3:
        # 退回到均匀采样
        offset = min(0.5, duration * 0.03)
        step = (duration - offset * 2) / max(FALLBACK_FRAMES - 1, 1)
        return [round(offset + step * i, 2) for i in range(FALLBACK_FRAMES)]

    # 去重 + 排序
    unique_times = sorted(set(round(t, 2) for t in scene_times if 0 < t < duration))
    if not unique_times:
        offset = min(0.5, duration * 0.03)
        step = (duration - offset * 2) / max(FALLBACK_FRAMES - 1, 1)
        return [round(offset + step * i, 2) for i in range(FALLBACK_FRAMES)]

    # 每个场景变化点后 0.5s 取帧 (避开转场混合帧)
    extracted: list[float] = []
    skip_gap = min(0.5, duration * 0.02)

    for t in unique_times:
        ts = round(min(t + skip_gap, duration - 0.1), 2)
        # 避免重复时间点
        if not extracted or (ts - extracted[-1]) > 0.5:
            extracted.append(ts)
        if len(extracted) >= max_frames:
            break

    # 如果还太少, 在段间补充中间帧
    if len(extracted) < max_frames:
        segments = [0.0] + extracted + [duration]
        midpoints: list[float] = []
        for i in range(len(segments) - 1):
            mid = round((segments[i] + segments[i + 1]) / 2, 2)
            midpoints.append(mid)
        # 交错合并 (优先场景变化点)
        combined: list[float] = []
        for m in midpoints:
            if len(combined) >= max_frames:
                break
            # 找最近的已有点
            too_close = any(abs(m - e) < 0.8 for e in extracted)
            if not too_close:
                combined.append(m)
        extracted = sorted(extracted + combined)[:max_frames]

    # 确保至少 3 帧
    if len(extracted) < 3:
        offset = min(0.5, duration * 0.03)
        step = (duration - offset * 2) / max(FALLBACK_FRAMES - 1, 1)
        extracted = [round(offset + step * i, 2) for i in range(FALLBACK_FRAMES)]

    return extracted[:max_frames]


def _extract_frame_at(mp4_path: Path, png_path: Path, at_seconds: float, label: str = "") -> bool:
    """复用 ffmpeg 子进程提取单帧."""
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
        logger.warning("ffmpeg frame extraction timed out at %.1fs (%s)", at_seconds, label)
        return False
    ok = r.returncode == 0 and png_path.exists() and png_path.stat().st_size > 0
    if not ok:
        logger.warning("ffmpeg frame extraction failed at %.1fs (%s): %s",
                       at_seconds, label, r.stderr[:200])
    return ok


def smart_extract_frames(
    video_path: str,
    duration: float,
    tmpdir: Path,
    max_frames: int = MAX_FRAMES,
) -> list[Path]:
    """智能抽帧主入口.

    1. 先用 scdet 检测场景变化
    2. 构建抽帧时间戳列表
    3. 逐个提取 PNG

    Args:
        video_path: 视频文件路径.
        duration: 视频时长 (秒).
        tmpdir: 临时目录 (存放帧 PNG).
        max_frames: 最大帧数 (默认 12).

    Returns:
        成功抽取的 PNG 路径列表.
    """
    mp4 = Path(video_path)
    if not mp4.exists():
        logger.warning("Video file not found: %s", video_path)
        return []

    # Pass 1: 场景检测
    scene_times = _run_ffmpeg_scdet(mp4, threshold=10.0)
    logger.debug("scdet found %d scene changes for %s", len(scene_times), mp4.name)

    # Pass 2: 构建时间戳
    timestamps = _build_extraction_timestamps(scene_times, duration, max_frames)
    logger.debug("Extracting %d frames for %s at: %s", len(timestamps), mp4.name, timestamps)

    # Pass 3: 逐帧提取
    frames: list[Path] = []
    for i, ts in enumerate(timestamps):
        png_path = tmpdir / f"frame_{i:03d}.png"
        ok = _extract_frame_at(mp4, png_path, ts, label=f"#{i}@{ts:.1f}s")
        if ok:
            frames.append(png_path)

    logger.info("Smart extract: %d/%d frames extracted for %s",
                len(frames), len(timestamps), mp4.name)
    return frames

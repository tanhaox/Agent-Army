"""
FFmpeg 服务封装 - 视频拼接、字幕嵌入、格式转换。

通过 asyncio.create_subprocess_exec 调用 FFmpeg 命令行，
避免 ffmpeg-python 等包装库的额外依赖和限制。
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """FFmpeg 命令执行失败。"""


async def _run_ffmpeg(*args: str) -> str:
    """
    执行 FFmpeg 命令并等待完成。

    Args:
        *args: FFmpeg 命令参数（不含 'ffmpeg' 本身）。

    Returns:
        FFmpeg 的 stderr 输出。

    Raises:
        FFmpegError: 命令执行失败。
    """
    cmd = ["ffmpeg", *args]
    logger.debug("执行 FFmpeg: %s", " ".join(cmd))

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")[-500:]
        raise FFmpegError(f"FFmpeg 退出码 {proc.returncode}: {err_msg}")

    return stderr.decode("utf-8", errors="replace")


async def concat_videos(video_paths: list[str], output_path: str) -> str:
    """
    使用 FFmpeg concat 协议拼接多个视频。

    生成 concat 文件列表，然后调用 ffmpeg -f concat -i list.txt -c copy。

    Args:
        video_paths: 视频文件路径列表（按顺序拼接）。
        output_path: 输出文件路径。

    Returns:
        输出文件路径。

    Raises:
        FFmpegError: 拼接失败。
        FileNotFoundError: 输入文件不存在。
    """
    if not video_paths:
        raise FFmpegError("视频路径列表不能为空")

    # 检查输入文件
    for p in video_paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"视频文件不存在: {p}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # 生成 concat 文件列表
    list_fd, list_path = tempfile.mkstemp(suffix=".txt", prefix="ffmpeg_concat_")
    try:
        with os.fdopen(list_fd, "w", encoding="utf-8") as f:
            for vp in video_paths:
                # FFmpeg concat 格式要求转义特殊字符
                safe_path = vp.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        await _run_ffmpeg(
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        )
        logger.info("视频拼接完成: %d 个片段 -> %s", len(video_paths), output_path)
    finally:
        os.unlink(list_path)

    return output_path


async def embed_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str,
) -> str:
    """
    将 SRT 字幕硬嵌入视频（burn-in）。

    使用 subtitles 滤镜将字幕直接渲染到画面上。

    Args:
        video_path: 输入视频路径。
        subtitle_path: SRT 字幕文件路径。
        output_path: 输出视频路径。

    Returns:
        输出文件路径。
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not os.path.isfile(subtitle_path):
        raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # subtitles 滤镜路径需要转义
    sub_filter = f"subtitles='{subtitle_path}'"

    await _run_ffmpeg(
        "-y",
        "-i", video_path,
        "-vf", sub_filter,
        "-c:a", "copy",
        output_path,
    )
    logger.info("字幕嵌入完成: %s", output_path)
    return output_path


async def convert_format(
    video_path: str,
    output_path: str,
    target_resolution: tuple[int, int] = (1080, 1920),
    target_bitrate: str = "2M",
) -> str:
    """
    转码视频为指定格式（默认抖音竖屏 1080x1920）。

    Args:
        video_path: 输入视频路径。
        output_path: 输出视频路径。
        target_resolution: 目标分辨率 (width, height)。
        target_bitrate: 目标视频码率。

    Returns:
        输出文件路径。
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    width, height = target_resolution

    await _run_ffmpeg(
        "-y",
        "-i", video_path,
        "-s", f"{width}x{height}",
        "-b:v", target_bitrate,
        "-c:v", "libx264",
        "-preset", "medium",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path,
    )
    logger.info("转码完成: %s (%dx%d, %s)", output_path, width, height, target_bitrate)
    return output_path


async def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> str:
    """
    将音频与视频合并（替换视频原音轨）。

    Args:
        video_path: 输入视频路径。
        audio_path: 输入音频路径。
        output_path: 输出视频路径。

    Returns:
        输出文件路径。
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    await _run_ffmpeg(
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    )
    logger.info("音视频合并完成: %s", output_path)
    return output_path


def check_ffmpeg_available() -> dict[str, str]:
    """
    检查 FFmpeg 是否可用。

    Returns:
        状态字典。
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return {"status": "ok", "path": ffmpeg_path}
    return {"status": "error", "error": "FFmpeg 未安装或不在 PATH 中"}

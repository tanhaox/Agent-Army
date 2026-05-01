import logging
import shutil
import sys
from pathlib import Path

import yt_dlp

from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoImportError(Exception):
    pass


_WINDOWS_COMMON_PATHS = [
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
    Path(r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe"),
    Path(r"C:\Users\tanha\Desktop\ffmpeg.exe"),
]

_UNSUPPORTED_PLATFORMS = {
    "tiktok.com": "TikTok 视频受区域限制，可能无法直接下载。",
}

_PLATFORM_TIMEOUT = {
    "default": 120,
    "douyin.com": 60,
    "tiktok.com": 30,
    "bilibili.com": 180,
}


def _find_ffmpeg() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    if sys.platform == "win32":
        for p in _WINDOWS_COMMON_PATHS:
            if p.exists():
                return str(p)
    return None


def _check_url_support(url: str) -> None:
    url_lower = url.lower()
    for domain, message in _UNSUPPORTED_PLATFORMS.items():
        if domain in url_lower:
            raise VideoImportError(message)


def check_url_support(url: str) -> None:
    _check_url_support(url)


def _get_timeout(url: str) -> int:
    for domain, timeout in _PLATFORM_TIMEOUT.items():
        if domain != "default" and domain in url.lower():
            return timeout
    return _PLATFORM_TIMEOUT["default"]


def _is_douyin_url(url: str) -> bool:
    return "douyin.com" in url.lower()


class VideoImporter:
    def __init__(self, output_dir: str = "uploads/videos", on_progress=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = _find_ffmpeg()
        self.on_progress = on_progress

    def download_video(self, url: str) -> str:
        _check_url_support(url)

        if _is_douyin_url(url):
            return self._download_douyin(url)

        return self._download_ytdlp(url)

    def _download_douyin(self, url: str) -> str:
        from app.services.douyin_service import DouyinDownloader
        downloader = DouyinDownloader(output_dir=str(self.output_dir))
        return downloader.download_video(url)

    def _download_ytdlp(self, url: str) -> str:
        outtmpl = str(self.output_dir / "%(id)s.%(ext)s")
        timeout = _get_timeout(url)

        ydl_opts: dict = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": timeout,
            "extractor_retries": 2,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            },
        }

        if self.on_progress:
            def _progress_hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    downloaded = d.get("downloaded_bytes", 0)
                    speed = d.get("speed") or 0
                    pct = round(downloaded / total * 100, 1) if total else 0
                    self.on_progress({
                        "status": d["status"],
                        "downloaded_bytes": downloaded,
                        "total_bytes": total,
                        "speed": speed,
                        "percent": pct,
                        "filename": d.get("filename", ""),
                    })
                elif d["status"] == "finished":
                    self.on_progress({"status": "finished"})

            ydl_opts["progress_hooks"] = [_progress_hook]

        if self.ffmpeg_path:
            ydl_opts["ffmpeg_location"] = str(Path(self.ffmpeg_path).parent)
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ]
        else:
            ydl_opts["format"] = "bestaudio/best"
            logger.warning("ffmpeg not found, downloading without audio conversion")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base = ydl.prepare_filename(info)

                audio_path = Path(base).with_suffix(".wav")
                if not audio_path.exists():
                    for ext in (".mp3", ".m4a", ".ogg", ".opus", ".mp4", ".webm"):
                        candidate = Path(base).with_suffix(ext)
                        if candidate.exists():
                            audio_path = candidate
                            break

                if not audio_path.exists():
                    video_id = info.get("id", "")
                    if video_id:
                        for f in self.output_dir.iterdir():
                            if video_id in f.name:
                                audio_path = f
                                break

                if not audio_path.exists():
                    raise VideoImportError(
                        "下载完成但找不到音视频文件。"
                        "可能需要安装 ffmpeg 来处理该格式。"
                        "安装指南: https://ffmpeg.org/download.html"
                    )
                logger.info("Downloaded %s -> %s", url, audio_path)
                return str(audio_path)

        except yt_dlp.utils.DownloadError as e:
            error_str = str(e).lower()
            if "sign in" in error_str or "login" in error_str or "cookie" in error_str:
                raise VideoImportError(
                    "该视频需要登录才能下载。请手动下载视频后使用文件上传功能。"
                ) from e
            if "private" in error_str or "removed" in error_str:
                raise VideoImportError("该视频已被删除或设为私密，无法下载。") from e
            if "not found" in error_str or "404" in error_str:
                raise VideoImportError("找不到该视频，请检查链接是否正确。") from e
            raise VideoImportError(f"视频下载失败: {e}") from e
        except yt_dlp.utils.ExtractorError as e:
            raise VideoImportError(
                f"不支持该平台的视频链接。请尝试使用 YouTube/B站链接，或手动上传视频文件。"
            ) from e
        except TimeoutError:
            raise VideoImportError("下载超时，请检查网络连接或尝试其他链接。")
        except Exception as e:
            error_type = type(e).__name__
            if "connection" in error_type.lower() or "network" in str(e).lower():
                raise VideoImportError("网络连接失败，请检查网络后重试。") from e
            raise VideoImportError(f"下载异常: {e}") from e

    def import_and_transcribe(self, url: str) -> dict:
        audio_path = self.download_video(url)

        if not self.ffmpeg_path:
            return {
                "source_url": url,
                "audio_path": audio_path,
                "transcription": None,
                "warning": "ffmpeg 未安装，仅完成下载，未进行转写。请安装 ffmpeg 后重试。",
            }

        from app.services.asr import asr_engine
        result = asr_engine.transcribe(audio_path)

        return {
            "source_url": url,
            "audio_path": audio_path,
            "transcription": {
                "text": result.text,
                "segments": result.segments,
                "duration": result.duration,
            },
        }

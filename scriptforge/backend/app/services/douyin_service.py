import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_COOKIE_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "douyin_cookies.json"

_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36 Edg/147.0.0.0"
)

_FFMPEG_SEARCH_PATHS_WIN = [
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\Users\tanha\Desktop\ffmpeg.exe",
]


def _find_ffmpeg() -> str | None:
    import shutil
    found = shutil.which("ffmpeg")
    if found:
        return found
    if sys.platform == "win32":
        for p in _FFMPEG_SEARCH_PATHS_WIN:
            if Path(p).exists():
                return p
    return None


def _load_cookie_config() -> dict | None:
    if not _COOKIE_CONFIG_PATH.exists():
        return None
    try:
        with open(_COOKIE_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load douyin cookie config: %s", e)
        return None


def _extract_aweme_id(url: str) -> str | None:
    patterns = [
        r"modal_id=(\d+)",
        r"/video/(\d+)",
        r"/share/video/(\d+)",
        r"aweme_id=(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _extract_sec_uid(url: str) -> str | None:
    patterns = [
        r"/user/([A-Za-z0-9_-]+)",
        r"sec_uid=([A-Za-z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _extract_audio(video_path: str, output_path: str, ffmpeg_path: str | None) -> str:
    if ffmpeg_path:
        result = subprocess.run(
            [
                ffmpeg_path, "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                output_path, "-y",
            ],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0 and Path(output_path).exists():
            return output_path
        logger.warning("ffmpeg audio extraction failed: %s", result.stderr[-200:])
    return video_path


def _download_with_playwright(url: str, output_dir: Path) -> str:
    from playwright.sync_api import sync_playwright

    cookie_config = _load_cookie_config()
    pw_cookies = []
    if cookie_config:
        for name, value in cookie_config.get("cookies", {}).items():
            pw_cookies.append({
                "name": name,
                "value": str(value),
                "domain": ".douyin.com",
                "path": "/",
            })

    video_url = None
    page_title = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=_MOBILE_UA,
            viewport={"width": 412, "height": 915},
            is_mobile=True,
        )
        if pw_cookies:
            context.add_cookies(pw_cookies)

        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page_title = page.title()

            video_el = page.query_selector("video")
            if video_el:
                src = video_el.get_attribute("src")
                if src:
                    if src.startswith("/"):
                        video_url = f"https://m.douyin.com{src}"
                    else:
                        video_url = src
        finally:
            browser.close()

    if not video_url:
        raise RuntimeError(
            f"无法从页面提取视频地址。标题: {page_title or '未知'}。"
            "可能触发了验证码，请稍后重试或更新 cookies。"
        )

    logger.info("Playwright extracted video URL: %s", video_url[:100])

    headers = {
        "User-Agent": _MOBILE_UA,
        "Referer": "https://m.douyin.com/",
    }
    with httpx.Client(timeout=60, follow_redirects=True, headers=headers) as client:
        resp = client.get(video_url)
        if resp.status_code != 200 or len(resp.content) < 10000:
            raise RuntimeError(
                f"视频下载失败: HTTP {resp.status_code}, 大小 {len(resp.content)} bytes"
            )

        aweme_id = _extract_aweme_id(url) or "unknown"
        video_file = output_dir / f"dy_{aweme_id}.mp4"
        video_file.write_bytes(resp.content)
        logger.info("Downloaded %s -> %s (%.1f MB)", url, video_file, len(resp.content) / 1048576)

    return str(video_file)


class DouyinDownloader:
    def __init__(self, output_dir: str = "uploads/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = _find_ffmpeg()

    def download_video(self, url: str) -> str:
        aweme_id = _extract_aweme_id(url)
        if not aweme_id:
            raise ValueError(
                "无法从链接中提取视频 ID。请使用标准抖音视频链接，"
                "例如: https://www.douyin.com/video/123456789"
            )

        video_url = f"https://www.douyin.com/video/{aweme_id}"
        logger.info("Downloading douyin video: %s (id=%s)", url, aweme_id)

        mp4_path = _download_with_playwright(video_url, self.output_dir)

        wav_path = str(Path(mp4_path).with_suffix(".wav"))
        final_path = _extract_audio(mp4_path, wav_path, self.ffmpeg_path)
        return final_path

    def download_user_top_videos(self, url: str, count: int = 5) -> list[dict]:
        sec_uid = _extract_sec_uid(url)
        if not sec_uid:
            raise ValueError(
                "无法从链接中提取用户 ID。请使用完整的抖音用户主页链接，"
                "例如: https://www.douyin.com/user/MS4wLjABAAAA..."
            )

        logger.info("Fetching top %d videos for sec_uid=%s", count, sec_uid)
        video_ids = self._get_user_video_ids(sec_uid, count)

        if not video_ids:
            raise ValueError("该用户暂无公开视频或 cookies 已过期")

        results = []
        for i, vid in enumerate(video_ids):
            logger.info("Downloading %d/%d: %s", i + 1, len(video_ids), vid.get("desc", "")[:50])
            try:
                audio_path = self.download_video(vid["url"])
                results.append({
                    "index": i + 1,
                    "aweme_id": vid["aweme_id"],
                    "desc": vid["desc"],
                    "source_url": vid["url"],
                    "author": vid.get("author", ""),
                    "duration": vid.get("duration", 0),
                    "audio_path": audio_path,
                    "status": "downloaded",
                })
            except Exception as e:
                logger.error("Failed to download video %s: %s", vid["aweme_id"], e)
                results.append({
                    "index": i + 1,
                    "aweme_id": vid["aweme_id"],
                    "desc": vid["desc"],
                    "source_url": vid["url"],
                    "author": vid.get("author", ""),
                    "duration": vid.get("duration", 0),
                    "status": "failed",
                    "error": str(e),
                })

        return results

    def get_user_profile(self, url: str) -> dict:
        """用子进程运行 Playwright 提取博主信息，避免 asyncio event loop 冲突。"""
        sec_uid = _extract_sec_uid(url)
        if not sec_uid:
            raise ValueError(
                "无法从链接中提取用户 ID。请使用完整的抖音用户主页链接，"
                "例如: https://www.douyin.com/user/MS4wLjABAAAA..."
            )

        logger.info("Fetching user profile via subprocess: sec_uid=%s", sec_uid)

        worker_script = Path(__file__).parent / "douyin_profile_worker.py"

        # Open playwright.log for stderr capture
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        pw_log = log_dir / "playwright.log"

        with open(pw_log, "a", encoding="utf-8") as log_fh:
            try:
                result = subprocess.run(
                    [sys.executable, str(worker_script), url],
                    stdout=subprocess.PIPE,
                    stderr=log_fh,
                    timeout=90,
                )
            except subprocess.TimeoutExpired:
                raise RuntimeError("获取博主信息超时，请稍后重试")

        stdout = result.stdout.decode("utf-8", errors="replace").strip() if result.stdout else ""

        if result.returncode != 0:
            logger.error("Profile worker failed (exit %d), see logs/playwright.log", result.returncode)
            try:
                err_data = json.loads(stdout)
                raise RuntimeError(err_data.get("error", "获取博主信息失败"))
            except (json.JSONDecodeError, AttributeError):
                raise RuntimeError(f"获取博主信息失败，详情请查看 logs/playwright.log")

        try:
            profile = json.loads(stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"博主信息解析失败: {stdout[:200]}")

        if "error" in profile:
            raise RuntimeError(profile["error"])

        logger.info("Profile fetched: name=%s, followers=%s",
                     profile.get("anchor_name"), profile.get("follower_count"))
        return profile

    def _get_user_video_ids(self, sec_uid: str, count: int) -> list[dict]:
        from playwright.sync_api import sync_playwright

        cookie_config = _load_cookie_config()
        pw_cookies = []
        if cookie_config:
            for name, value in cookie_config.get("cookies", {}).items():
                pw_cookies.append({
                    "name": name,
                    "value": str(value),
                    "domain": ".douyin.com",
                    "path": "/",
                })

        videos = []
        user_url = f"https://www.douyin.com/user/{sec_uid}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=_MOBILE_UA,
                viewport={"width": 412, "height": 915},
                is_mobile=True,
            )
            if pw_cookies:
                context.add_cookies(pw_cookies)

            page = context.new_page()

            def handle_response(response):
                if "aweme/post" in response.url or "aweme/list" in response.url:
                    try:
                        data = response.json()
                        for item in data.get("aweme_list", []):
                            videos.append({
                                "aweme_id": item.get("aweme_id", ""),
                                "desc": item.get("desc", "")[:80],
                                "url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
                                "duration": item.get("duration", 0) / 1000 if item.get("duration") else 0,
                                "author": item.get("author", {}).get("nickname", ""),
                            })
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                page.goto(user_url, wait_until="networkidle", timeout=30000)
            finally:
                browser.close()

        return videos[:count]


# Keep backward compat alias
DouyinUserDownloader = DouyinDownloader


def is_douyin_user_url(url: str) -> bool:
    return bool(re.search(r"douyin\.com/user/", url.lower()))


def is_douyin_video_url(url: str) -> bool:
    lower = url.lower()
    return "douyin.com" in lower and not bool(re.search(r"douyin\.com/user/", lower))

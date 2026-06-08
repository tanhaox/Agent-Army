"""Subprocess worker for fetching Douyin user video list via Playwright.

Runs in complete isolation from FastAPI's asyncio event loop.
Called via: python douyin_video_list_worker.py <sec_uid> <count>
Outputs line-delimited JSON to stdout (one JSON object per line).
Each line is a progress event or the final result.

Key behavior: scrolls at least MIN_PAGES (3) times to collect enough videos
before filtering/sorting, ensuring high-play-count videos from later pages
are not missed.
"""
import json
import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("douyin_video_list_worker")
_logger.setLevel(logging.DEBUG)
_handler = TimedRotatingFileHandler(
    _LOG_DIR / "playwright.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
_logger.addHandler(_handler)

_COOKIE_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "douyin_cookies.json"
_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36 Edg/147.0.0.0"
)

# Duration filter bounds (seconds). Upper bound covers Douyin long-form videos.
MIN_DURATION = 15
MAX_DURATION = 900

# Minimum pages to scroll before stopping
MIN_PAGES = 3
MAX_PAGES = 10
SCROLL_DELAY = 2.0  # seconds between scrolls


def _emit(data: dict):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def _load_cookies():
    if not _COOKIE_CONFIG_PATH.exists():
        return []
    try:
        with open(_COOKIE_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return [
            {"name": k, "value": str(v), "domain": ".douyin.com", "path": "/"}
            for k, v in cfg.get("cookies", {}).items()
        ]
    except Exception:
        return []


def main():
    if len(sys.argv) < 3:
        _emit({"error": "Usage: douyin_video_list_worker.py <sec_uid> <count> [exclude_ids]"})
        sys.exit(1)

    sec_uid = sys.argv[1]
    count = int(sys.argv[2])
    exclude_ids = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else set()

    _logger.info("Video list worker started: sec_uid=%s, count=%d, min_pages=%d, exclude=%d",
                 sec_uid, count, MIN_PAGES, len(exclude_ids))

    pw_cookies = _load_cookies()
    all_videos = []
    user_url = f"https://www.douyin.com/user/{sec_uid}"

    try:
        from playwright.sync_api import sync_playwright

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

            page_number = 0

            def handle_response(response):
                nonlocal page_number
                if "aweme/post" in response.url or "aweme/list" in response.url:
                    try:
                        data = response.json()
                        page_number += 1
                        for item in data.get("aweme_list", []):
                            # Mobile API: statistics only has digg_count (no play_count).
                            # Use digg_count as popularity proxy for sorting.
                            stats = item.get("statistics", {})
                            play_count = stats.get("play_count") or stats.get("digg_count", 0)

                            # Duration: may be ms (e.g. 60000 for 60s) or seconds (mobile API).
                            # Heuristic: > 1000 → ms, else seconds.
                            video_obj = item.get("video") or {}
                            duration_raw = item.get("duration") or video_obj.get("duration", 0)
                            duration_s = duration_raw / 1000 if duration_raw > 1000 else (duration_raw or 0)

                            # Author: mobile API may omit author on user-page responses;
                            # try nested author, else leave empty (caller supplies profile name).
                            author = ""
                            author_obj = item.get("author")
                            if author_obj:
                                author = author_obj.get("nickname", "")

                            all_videos.append({
                                "aweme_id": item.get("aweme_id", ""),
                                "desc": item.get("desc", "")[:80],
                                "url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
                                "duration": duration_s,
                                "author": author,
                                "play_count": play_count,
                            })

                        _emit({
                            "step": "fetching_video_list",
                            "page": page_number,
                            "total_collected": len(all_videos),
                        })
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                page.goto(user_url, wait_until="networkidle", timeout=30000)
                _logger.info("Page loaded, collected %d videos in page %d", len(all_videos), page_number)

                # Scroll to trigger lazy loading — minimum MIN_PAGES API responses
                for scroll_attempt in range(MAX_PAGES):
                    if page_number >= MIN_PAGES:
                        break

                    prev_page = page_number
                    prev_count = len(all_videos)

                    # Scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    _logger.info("Scroll attempt %d (page %d, %d videos)", scroll_attempt + 1, page_number, len(all_videos))

                    # Wait for new content to load
                    time.sleep(SCROLL_DELAY)

                    # Also try waiting for network to settle
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass

                    # If nothing new loaded after this scroll, stop
                    if page_number == prev_page and len(all_videos) == prev_count:
                        _logger.info("No new content after scroll %d, stopping", scroll_attempt + 1)
                        break

                _logger.info("Scrolling complete: %d pages, %d videos", page_number, len(all_videos))

            finally:
                browser.close()

    except Exception as e:
        _logger.error("Video list worker failed: %s", e)
        _emit({"error": str(e)})
        sys.exit(1)

    # --- Phase 2: Filter by duration ---
    total_before = len(all_videos)
    filtered = [
        v for v in all_videos
        if MIN_DURATION <= v["duration"] <= MAX_DURATION
    ]
    # Fallback: if nothing matches, use all videos
    if not filtered and all_videos:
        filtered = all_videos

    _emit({
        "step": "filtering",
        "total_before_filter": total_before,
        "filtered_count": len(filtered),
    })

    # --- Phase 3: Sort by play_count and select top N ---
    filtered.sort(key=lambda v: v.get("play_count", 0), reverse=True)

    # Exclude already-processed videos (supplement mode)
    if exclude_ids:
        before = len(filtered)
        filtered = [v for v in filtered if v["aweme_id"] not in exclude_ids]
        excluded_count = before - len(filtered)
        if excluded_count:
            _logger.info("Excluded %d already-processed videos", excluded_count)
            _emit({"step": "excluded", "excluded_count": excluded_count})

    top_videos = filtered[:count]

    play_strs = []
    for v in top_videos:
        pc = v.get("play_count", 0)
        if pc >= 10000:
            play_strs.append(f"{pc / 10000:.1f}万")
        else:
            play_strs.append(str(pc))

    _emit({
        "step": "top_selected",
        "selected_count": len(top_videos),
        "total_pages": page_number,
        "total_collected": total_before,
        "filtered_count": len(filtered),
        "top_videos": [
            {"title": v["desc"], "play_count": v["play_count"], "duration": v["duration"]}
            for v in top_videos
        ],
        "play_strs": play_strs,
    })

    # --- Final output: complete video list ---
    _emit({
        "step": "done",
        "video_ids": top_videos,
    })

    _logger.info("Video list worker done: found %d, filtered %d, selected %d (pages=%d)",
                 total_before, len(filtered), len(top_videos), page_number)


if __name__ == "__main__":
    main()

"""Subprocess worker for Douyin profile extraction via Playwright.

Runs in complete isolation from FastAPI's asyncio event loop.
Called via: python douyin_profile_worker.py <url>
Outputs JSON to stdout.
"""
import json
import logging
import os
import re
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Configure file logging for this subprocess worker
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_worker_logger = logging.getLogger("douyin_profile_worker")
_worker_logger.setLevel(logging.DEBUG)
_pw_handler = TimedRotatingFileHandler(
    _LOG_DIR / "playwright.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
_pw_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
_worker_logger.addHandler(_pw_handler)

_COOKIE_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "douyin_cookies.json"
_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36 Edg/147.0.0.0"
)


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


def _extract_sec_uid(url):
    for pat in [r"/user/([A-Za-z0-9_-]+)", r"sec_uid=([A-Za-z0-9_-]+)"]:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _parse_count_text(text):
    text = text.strip().replace(",", "").replace("+", "")
    for suffix, mult in [("亿", 100000000), ("万", 10000), ("w", 10000)]:
        if suffix in text.lower():
            return int(float(text.lower().replace(suffix, "")) * mult)
    try:
        return int(text)
    except ValueError:
        return 0


def _parse_body_text(body_text: str, profile: dict) -> None:
    """Extract profile info from page body text (most reliable for mobile douyin)."""
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]
    # Mobile douyin body text structure:
    # 获赞 / 200.2万+ / 关注 / 8 / 粉丝 / 56.8万+ / 破壁狗 / 抖音号 xxx / bio...
    # OR: 破壁狗 / 获赞 / 200.2万+ / ...

    # Find counts by keyword
    for i, line in enumerate(lines):
        if line == "获赞" and i + 1 < len(lines):
            profile["like_count"] = _parse_count_text(lines[i + 1])
        elif line == "粉丝" and i + 1 < len(lines):
            profile["follower_count"] = _parse_count_text(lines[i + 1])

    # Find name: it appears after the stats section, before "抖音号"
    # Try to find it by looking for the pattern: 粉丝 <count> <name> 抖音号
    for i, line in enumerate(lines):
        if line == "粉丝":
            # Name should be a few lines after follower count
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j]
                # Skip count values (contain numbers/万/亿)
                if re.match(r"^[\d.]+[万亿w+]*$", candidate):
                    continue
                # Skip keywords
                if candidate in ("关注", "获赞", "粉丝", "喜欢", "作品"):
                    continue
                # This is likely the name
                if not candidate.startswith("抖音号") and len(candidate) < 30:
                    profile["anchor_name"] = candidate
                    break
            break

    # Find douyin ID
    for line in lines:
        if line.startswith("抖音号"):
            profile["anchor_id"] = line.replace("抖音号", "").strip()
            break

    # Find bio: text after douyin ID, before UI elements
    found_dy_id = False
    bio_parts = []
    for line in lines:
        if line.startswith("抖音号"):
            found_dy_id = True
            continue
        if found_dy_id:
            # Stop at known UI elements
            if line in ("进入橱窗", "作品", "喜欢", "打开抖音精选App看更多内容"):
                break
            bio_parts.append(line)
    if bio_parts:
        profile["bio"] = " ".join(bio_parts).strip()
        # Clean up bio - remove trailing numbers that are counts
        profile["bio"] = re.sub(r"\s*\d+\+?$", "", profile["bio"]).strip()


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "URL argument required"}))
        sys.exit(1)

    url = sys.argv[1]
    sec_uid = _extract_sec_uid(url)
    if not sec_uid:
        print(json.dumps({"error": "Cannot extract user ID from URL"}))
        sys.exit(1)

    _worker_logger.info("Worker started: url=%s, sec_uid=%s", url[:80], sec_uid)

    user_url = f"https://www.douyin.com/user/{sec_uid}"
    profile = {
        "anchor_name": "",
        "anchor_id": sec_uid,
        "sec_uid": sec_uid,
        "follower_count": 0,
        "like_count": 0,
        "homepage_url": user_url,
        "avatar_url": None,
        "bio": None,
    }

    pw_cookies = _load_cookies()

    try:
        from playwright.sync_api import sync_playwright

        captured_user = None

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
                nonlocal captured_user
                if captured_user:
                    return
                try:
                    u = response.url
                    if "aweme/post" in u or "aweme/list" in u:
                        data = response.json()
                        if isinstance(data, dict):
                            items = data.get("aweme_list", [])
                            if items:
                                author = items[0].get("author")
                                if author and isinstance(author, dict) and author.get("nickname"):
                                    captured_user = author
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                page.goto(user_url, wait_until="networkidle", timeout=30000)
            except Exception:
                pass

            # Primary: extract from captured API data
            if captured_user:
                try:
                    v = captured_user.get("nickname")
                    if v:
                        profile["anchor_name"] = v
                except Exception:
                    pass
                try:
                    v = captured_user.get("unique_id") or captured_user.get("short_id") or captured_user.get("sec_uid")
                    if v:
                        profile["anchor_id"] = v
                except Exception:
                    pass
                try:
                    profile["follower_count"] = int(captured_user.get("follower_count", 0))
                except Exception:
                    pass
                try:
                    profile["like_count"] = int(float(captured_user.get("total_favorited", 0)))
                except Exception:
                    pass
                try:
                    avatar = captured_user.get("avatar_larger")
                    if isinstance(avatar, dict):
                        urls = avatar.get("url_list", [])
                        if urls:
                            profile["avatar_url"] = urls[0]
                    elif isinstance(avatar, str):
                        profile["avatar_url"] = avatar
                except Exception:
                    pass
                try:
                    v = captured_user.get("signature")
                    if v:
                        profile["bio"] = v
                except Exception:
                    pass

            # Fallback: parse body text (most reliable for mobile douyin)
            if not profile["anchor_name"]:
                try:
                    body_text = page.inner_text("body")
                    _parse_body_text(body_text, profile)
                except Exception:
                    pass

            # Try avatar from page images
            if not profile["avatar_url"]:
                try:
                    img = page.query_selector("img[src*='aweme-avatar']")
                    if img:
                        profile["avatar_url"] = img.get_attribute("src")
                except Exception:
                    pass

            browser.close()

    except Exception as e:
        _worker_logger.error("Profile extraction failed: %s", e)
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if not profile["anchor_name"]:
        profile["anchor_name"] = f"用户{sec_uid[:8]}"

    _worker_logger.info("Profile extracted: name=%s, followers=%s",
                        profile.get("anchor_name"), profile.get("follower_count"))

    print(json.dumps(profile, ensure_ascii=False))


if __name__ == "__main__":
    main()

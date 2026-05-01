"""System settings endpoints — Douyin Cookie management and user preferences."""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

_COOKIE_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "douyin_cookies.json"


class CookieItem(BaseModel):
    name: str
    value: str
    domain: str = ".douyin.com"
    path: str = "/"


class CookieUpdateRequest(BaseModel):
    cookies: list[CookieItem] = Field(..., min_length=1, description="Cookie 列表，不可为空")


@router.get("/douyin-cookie")
async def get_douyin_cookie_status():
    """Return current cookie configuration status."""
    if not _COOKIE_PATH.exists():
        return {"status": "not_configured"}

    try:
        with open(_COOKIE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        cookies = data.get("cookies", {})
        count = len(cookies)
        if count == 0:
            return {"status": "not_configured"}
        return {"status": "configured", "cookie_count": count}
    except Exception as e:
        logger.warning("Failed to read cookie config: %s", e)
        return {"status": "not_configured"}


@router.put("/douyin-cookie")
async def update_douyin_cookies(req: CookieUpdateRequest):
    """Write new cookies to config file. Accepts EditThisCookie export format."""
    cookie_dict = {item.name: item.value for item in req.cookies}
    if not cookie_dict:
        raise HTTPException(status_code=422, detail="Cookie 列表不能为空")

    config = {
        "_comment": "Auto-updated cookies",
        "domain": ".douyin.com",
        "cookies": cookie_dict,
    }

    _COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(_COOKIE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Failed to write cookie config: %s", e)
        raise HTTPException(status_code=500, detail=f"写入配置文件失败: {e}")

    logger.info(
        "Douyin cookies updated: %d items saved to %s",
        len(cookie_dict),
        _COOKIE_PATH,
    )

    return {"status": "configured", "cookie_count": len(cookie_dict)}


# ── User preferences ─────────────────────────────────────────────

class UserSettingsSchema(BaseModel):
    emotion_curve: str = "default"
    strategy_mix: str = "conservative"
    api_base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""


@router.get("/")
async def get_user_settings(db: AsyncSession = Depends(get_db)):
    user = await get_current_user(db)
    stored = user.settings or {}
    api_key = stored.get("api_key", "")
    masked_key = ""
    if api_key:
        masked_key = f"{api_key[:4]}{'*' * 12}{api_key[-4:]}" if len(api_key) > 8 else "****"
    return {
        "emotion_curve": stored.get("emotion_curve", "default"),
        "strategy_mix": stored.get("strategy_mix", "conservative"),
        "api_base_url": stored.get("api_base_url", "https://api.deepseek.com/v1"),
        "api_key_configured": bool(api_key),
        "api_key_masked": masked_key,
        "plan_type": user.plan_type,
        "quota_total": user.quota_total,
        "quota_used": user.quota_used,
        "username": user.username,
        "email": user.email,
    }


@router.patch("/")
async def update_user_settings(
    body: UserSettingsSchema,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(db)
    stored = dict(user.settings or {})
    stored["emotion_curve"] = body.emotion_curve
    stored["strategy_mix"] = body.strategy_mix
    stored["api_base_url"] = body.api_base_url
    if body.api_key:
        stored["api_key"] = body.api_key
    user.settings = stored
    await db.commit()
    logger.info("User settings updated for %s", user.username)
    return await get_user_settings(db=db)

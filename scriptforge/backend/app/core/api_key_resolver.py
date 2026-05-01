"""Resolve effective DeepSeek API key: per-user override → env var.

All services that call DeepSeek should use resolve_api_key() instead of
reading settings.DEEPSEEK_API_KEY directly, so per-user overrides take effect.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


async def resolve_api_key(db: AsyncSession | None) -> str:
    """Return effective DeepSeek API key.

    Resolution order: user.settings.api_key → env DEEPSEEK_API_KEY → error.
    """
    if db:
        try:
            result = await db.execute(select(User).limit(1))
            user = result.scalar()
            if user and user.settings:
                user_key = user.settings.get("api_key", "")
                if user_key:
                    return user_key
        except Exception:
            logger.debug("Could not resolve per-user API key, falling back to env")

    if settings.DEEPSEEK_API_KEY:
        return settings.DEEPSEEK_API_KEY

    raise ValueError(
        "DEEPSEEK_API_KEY is not configured. Set it in .env or via Settings → API 配置."
    )

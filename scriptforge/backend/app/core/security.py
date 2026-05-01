"""API key authentication middleware.

When API_AUTH_KEY is set in config, all requests (except health/docs)
must include X-API-Key header matching the configured key.

Also provides user dependency injection for permission checks.
"""
import logging
import uuid as _uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

_SKIP_PATHS = {
    "/api/health",
    "/api/",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.API_AUTH_KEY:
            return await call_next(request)

        path = request.url.path
        if path in _SKIP_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if not api_key:
            logger.warning("Missing X-API-Key header from %s", request.client)
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-API-Key header"},
            )

        if api_key != settings.API_AUTH_KEY:
            logger.warning("Invalid API key from %s", request.client)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )

        return await call_next(request)


# ── User dependency (extensible to JWT later) ──


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: resolve the current user.

    CURRENT MODE (shared-secret): Returns the first active user,
    creating a demo user if none exists.

    FUTURE EXTENSION: Replace the body of this function to extract
    user identity from a JWT token or session cookie. All permission
    checks flow through this single dependency — the rest of the
    codebase requires no changes.
    """
    result = await db.execute(
        select(User).where(User.is_active.is_(True)).limit(1)
    )
    user = result.scalar()

    if user is None:
        user = User(
            id=_uuid.uuid4(),
            username="demo_user",
            email="demo@scriptforge.local",
            hashed_password="",
            plan_type="free",
            quota_total=5,
            quota_used=0,
        )
        db.add(user)
        await db.flush()
        logger.info("Created demo user: %s", user.id)

    return user


def check_ownership(obj, current_user: User) -> None:
    """Raise 403 if current_user does not own the given object.

    Checks created_by and uploaded_by fields. Objects without a user
    FK (or where the FK is NULL) are skipped — old data is grandfathered.
    """
    owner_id = getattr(obj, "created_by", None) or getattr(obj, "uploaded_by", None)
    if owner_id is not None and owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this resource",
        )


def set_owner(obj, current_user: User) -> None:
    """Set created_by / uploaded_by on a new object before persisting."""
    if hasattr(obj, "created_by"):
        obj.created_by = current_user.id
    if hasattr(obj, "uploaded_by"):
        obj.uploaded_by = current_user.id

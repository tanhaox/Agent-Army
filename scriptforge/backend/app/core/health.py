"""Health check with dependency verification.

Checks: DB (asyncpg), Redis, ChromaDB, DeepSeek API connectivity.
Each check is independent — one failure does not block others.
"""
import asyncio
import logging
import time

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


async def check_database() -> dict:
    """Verify PostgreSQL connectivity."""
    try:
        async with engine.connect() as conn:
            start = time.monotonic()
            await conn.execute(text("SELECT 1"))
            elapsed = round((time.monotonic() - start) * 1000)
        return {"status": "ok", "latency_ms": elapsed}
    except Exception as e:
        logger.warning("DB health check failed: %s", e)
        return {"status": "error", "detail": str(e)[:200]}


async def check_redis() -> dict:
    """Verify Redis connectivity via ping."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        start = time.monotonic()
        await r.ping()
        elapsed = round((time.monotonic() - start) * 1000)
        await r.aclose()
        return {"status": "ok", "latency_ms": elapsed}
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        return {"status": "error", "detail": str(e)[:200]}


async def check_chromadb() -> dict:
    """Verify ChromaDB connectivity."""
    try:
        import chromadb

        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST, port=settings.CHROMA_PORT
        )
        start = time.monotonic()
        heartbeat = client.heartbeat()
        elapsed = round((time.monotonic() - start) * 1000)
        return {"status": "ok", "latency_ms": elapsed, "heartbeat": heartbeat}
    except Exception as e:
        logger.warning("ChromaDB health check failed: %s", e)
        return {"status": "error", "detail": str(e)[:200]}


async def check_deepseek() -> dict:
    """Verify DeepSeek API key validity (lightweight check)."""
    if not settings.DEEPSEEK_API_KEY:
        return {"status": "skipped", "detail": "DEEPSEEK_API_KEY not configured"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.monotonic()
            response = await client.get(
                f"{settings.DEEPSEEK_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            )
            elapsed = round((time.monotonic() - start) * 1000)
            if response.status_code == 200:
                return {"status": "ok", "latency_ms": elapsed}
            elif response.status_code == 401:
                return {"status": "error", "detail": "Invalid API key"}
            else:
                return {
                    "status": "warning",
                    "detail": f"Unexpected status {response.status_code}",
                }
    except Exception as e:
        logger.warning("DeepSeek health check failed: %s", e)
        return {"status": "error", "detail": str(e)[:200]}


async def get_health_status() -> dict:
    """Aggregate all health checks. Each check is independent."""
    results = await asyncio.gather(
        check_database(),
        check_redis(),
        check_chromadb(),
        check_deepseek(),
        return_exceptions=True,
    )

    check_names = ["database", "redis", "chromadb", "deepseek"]
    checks = {}
    for name, result in zip(check_names, results):
        if isinstance(result, Exception):
            checks[name] = {"status": "error", "detail": str(result)[:200]}
        else:
            checks[name] = result

    all_ok = all(v.get("status") == "ok" for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "0.2.0",
        "checks": checks,
    }

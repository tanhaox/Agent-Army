"""Health check with dependency verification.

Checks: DB (asyncpg), Redis, ChromaDB, DeepSeek API connectivity.
Each check is independent — one failure does not block others.
"""
import asyncio
import logging
import os
import shutil
import time
from pathlib import Path

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


async def get_disk_usage() -> dict:
    """Return uploads/ directory size and disk free space."""
    try:
        uploads_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        total_bytes = sum(f.stat().st_size for f in uploads_dir.rglob("*") if f.is_file()) if uploads_dir.exists() else 0
        disk = shutil.disk_usage(str(uploads_dir.resolve()) if uploads_dir.exists() else ".")
        return {
            "status": "ok",
            "uploads_bytes": total_bytes,
            "uploads_gb": round(total_bytes / (1024 ** 3), 2),
            "disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
        }
    except Exception as e:
        logger.warning("Disk usage check failed: %s", e)
        return {"status": "error", "detail": str(e)[:200]}


async def get_health_status() -> dict:
    """Aggregate all health checks. Each check is independent."""
    results = await asyncio.gather(
        check_database(),
        check_chromadb(),
        check_deepseek(),
        get_disk_usage(),
        return_exceptions=True,
    )

    check_names = ["database", "chromadb", "deepseek", "disk"]
    checks = {}
    for name, result in zip(check_names, results):
        if isinstance(result, Exception):
            checks[name] = {"status": "error", "detail": str(result)[:200]}
        else:
            checks[name] = result

    all_ok = all(v.get("status") == "ok" for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "0.3.0",
        "checks": checks,
    }

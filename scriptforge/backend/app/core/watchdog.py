"""Background watchdog — kills zombie tasks and orphan processes every 30 minutes."""

import asyncio
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("scriptforge.watchdog")

# Tasks with no progress update for this long are considered dead
_STALE_MINUTES = 60
_INTERVAL_SECONDS = 1800  # 30 minutes


def _get_uploads_dir() -> Path:
    return Path(os.getenv("UPLOAD_DIR", Path(__file__).resolve().parent.parent.parent / "uploads"))


def _kill_orphan_workers():
    """Kill asr_worker processes that have been running longer than 2 hours."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*asr_worker*' -and $_.Name -eq 'python.exe' } | Select-Object ProcessId,CreationDate | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15,
        )
        if not result.stdout.strip():
            return
        import json
        procs = json.loads(result.stdout)
        if not isinstance(procs, list):
            procs = [procs]

        now = time.time()
        killed = 0
        for p in procs:
            pid = p.get("ProcessId")
            created = p.get("CreationDate")
            if not pid or not created:
                continue
            # PowerShell CreationDate is like "/Date(1746000000000)/"
            if isinstance(created, str) and "Date(" in created:
                ts_ms = int(created.split("(")[1].split(")")[0])
                age_min = (now - ts_ms / 1000) / 60
            else:
                continue
            if age_min > 120:  # 2 hours
                try:
                    os.kill(pid, 9)
                    killed += 1
                    logger.info("[Watchdog] Killed stale asr_worker PID %d (age: %.0f min)", pid, age_min)
                except (ProcessLookupError, PermissionError):
                    pass
        if killed:
            logger.info("[Watchdog] Killed %d orphan asr_worker(s)", killed)
    except Exception as e:
        logger.error("[Watchdog] Worker cleanup error: %s", e)


async def _mark_stale_tasks():
    """Mark running tasks with no recent progress update as failed."""
    try:
        import asyncpg
        from app.core.config import settings

        url = settings.DATABASE_URL.replace("+asyncpg", "")
        conn = await asyncpg.connect(url)
        try:
            result = await conn.execute("""
                UPDATE task_records
                SET status = 'failed',
                    error_message = '心跳检测：任务超时无进展，自动终止'
                WHERE status = 'running'
                  AND trigger IN ('batch_retranscribe', 'douyin_user_import')
                  AND updated_at < now() - interval '%d minutes'
            """ % _STALE_MINUTES)
            tag = result.split()[-1] if result else "0"
            if tag != "0":
                logger.info("[Watchdog] Marked %s stale task(s) as failed (no progress for %d min)", tag, _STALE_MINUTES)
        finally:
            await conn.close()
    except Exception as e:
        logger.error("[Watchdog] Task cleanup error: %s", e)


def _dir_size(p: Path) -> int:
    """Total bytes of all files under a directory."""
    if not p.exists():
        return 0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


async def _check_and_clean_disk():
    """Check disk free space and uploads/ size. Auto-clean if over critical threshold."""
    try:
        uploads_dir = _get_uploads_dir()
        target = str(uploads_dir.resolve()) if uploads_dir.exists() else "."
        disk = shutil.disk_usage(target)
        free_gb = disk.free / (1024 ** 3)

        # Disk free space alerts
        if free_gb < 10:
            logger.critical("[Watchdog] Disk free space %.1f GB — critically low!", free_gb)
        elif free_gb < 20:
            logger.warning("[Watchdog] Disk free space %.1f GB — running low", free_gb)

        # Uploads directory size check
        total_bytes = _dir_size(uploads_dir)
        total_gb = total_bytes / (1024 ** 3)
        warning_gb = settings.DISK_USAGE_WARNING_GB
        critical_gb = settings.DISK_USAGE_CRITICAL_GB

        if total_gb < warning_gb:
            return

        if total_gb < critical_gb:
            logger.warning("[Watchdog] uploads/ size %.1f GB exceeds warning threshold (%d GB)", total_gb, warning_gb)
            return

        logger.critical("[Watchdog] uploads/ size %.1f GB exceeds critical threshold (%d GB) — starting auto-clean", total_gb, critical_gb)

        import asyncpg
        url = settings.DATABASE_URL.replace("+asyncpg", "")
        conn = await asyncpg.connect(url)
        try:
            # Step 1: collect file paths of deleted assets
            deleted_rows = await conn.fetch("SELECT file_path FROM assets WHERE is_deleted = true AND file_path IS NOT NULL")
            to_delete = [r["file_path"] for r in deleted_rows]

            # Step 2: if still not enough, add oldest assets
            freed_target = 10 * 1024 ** 3  # 10 GB
            if to_delete:
                placeholders = ",".join(f"${i+1}" for i in range(len(to_delete)))
                sizes = await conn.fetch(f"SELECT id, file_path FROM assets WHERE file_path IN ({placeholders}) ORDER BY created_at ASC", *to_delete)
                for r in sizes:
                    if sum(Path(p).stat().st_size for p in to_delete if Path(p).exists()) >= freed_target:
                        break
                    # already included

            # Actually delete files
            deleted_count = 0
            freed_bytes = 0
            for fp_str in to_delete:
                fp = Path(fp_str)
                if not fp.exists():
                    continue
                try:
                    size = fp.stat().st_size
                    fp.unlink()
                    deleted_count += 1
                    freed_bytes += size
                except OSError as e:
                    logger.warning("[Watchdog] Failed to delete %s: %s", fp, e)

            # Step 3: if freed < 10GB, also clean orphan files
            if freed_bytes < freed_target:
                orphan_cleaned, orphan_freed = _clean_orphan_files(uploads_dir, set())
                deleted_count += orphan_cleaned
                freed_bytes += orphan_freed

            if deleted_count > 0:
                logger.info("[Watchdog] Auto-cleaned %d files, freed %.1f GB", deleted_count, freed_bytes / (1024 ** 3))
        finally:
            await conn.close()
    except Exception as e:
        logger.error("[Watchdog] Disk cleanup error: %s", e)


def _clean_orphan_files(uploads_dir: Path, db_paths: set) -> tuple[int, int]:
    """Delete files not in db_paths from uploads_dir. Returns (count, bytes)."""
    if not uploads_dir.exists():
        return 0, 0
    count = 0
    freed = 0
    for fp in uploads_dir.rglob("*"):
        if not fp.is_file():
            continue
        if str(fp.resolve()) in db_paths:
            continue
        if fp.suffix in (".lock", ".tmp", ".bak"):
            continue
        try:
            size = fp.stat().st_size
            fp.unlink()
            count += 1
            freed += size
        except OSError:
            pass
    return count, freed


def _watchdog_loop():
    """Main loop: runs in a daemon thread."""
    logger.info("[Watchdog] Started (interval=%ds, stale_threshold=%dm)", _INTERVAL_SECONDS, _STALE_MINUTES)
    while True:
        try:
            asyncio.run(_mark_stale_tasks())
        except Exception as e:
            logger.error("[Watchdog] DB sweep error: %s", e)

        try:
            _kill_orphan_workers()
        except Exception as e:
            logger.error("[Watchdog] Worker cleanup error: %s", e)

        try:
            asyncio.run(_check_and_clean_disk())
        except Exception as e:
            logger.error("[Watchdog] Disk check error: %s", e)

        time.sleep(_INTERVAL_SECONDS)


def start_watchdog():
    """Start the watchdog daemon thread."""
    t = threading.Thread(target=_watchdog_loop, daemon=True, name="scriptforge-watchdog")
    t.start()
    logger.info("[Watchdog] Thread started")

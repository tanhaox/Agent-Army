import asyncio
import logging
import os
import subprocess
import sys
import time

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _kill_processes_sync() -> dict:
    pids_killed = []

    # 1. Kill processes occupying port 8002
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if ':8002' in line and 'LISTENING' in line:
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit():
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True, timeout=5)
                        pids_killed.append(f"port:8002 PID:{pid}")
    except Exception as e:
        logger.warning("Failed to kill port 8002: %s", e)

    # 2. Kill uvicorn processes via wmic
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', "name='python.exe'",
             'get', 'processid,commandline'],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if 'uvicorn' in line and 'app.main' in line:
                parts = line.strip().split()
                pid = parts[-1] if parts else ''
                if pid.isdigit():
                    current_pid = str(os.getpid())
                    if pid != current_pid:
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True, timeout=5)
                        pids_killed.append(f"uvicorn PID:{pid}")
    except Exception as e:
        logger.warning("Failed to kill uvicorn via wmic: %s", e)

    # 3. Wait for port release
    time.sleep(3)

    # 4. Start new process
    DETACHED_PROCESS = 0x00000008
    try:
        subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'app.main:app',
             '--host', '0.0.0.0', '--port', '8002', '--reload'],
            cwd=BACKEND_DIR,
            creationflags=DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.error("Failed to start new uvicorn: %s", e)

    return {"killed": pids_killed}


@router.post("/restart")
async def restart_backend():
    old_pid = os.getpid()

    killed_info = await asyncio.to_thread(_kill_processes_sync)

    # Schedule self-exit after response is sent
    async def _delayed_exit():
        await asyncio.sleep(1)
        os._exit(0)

    asyncio.ensure_future(_delayed_exit())

    return {
        "status": "restarting",
        "old_pid": old_pid,
        "killed": killed_info.get("killed", []),
    }

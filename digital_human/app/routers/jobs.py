"""SSE job event streaming."""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# In-memory channels: job_id -> list of asyncio.Queue
_job_channels: dict[str, list[asyncio.Queue]] = {}
_lock = threading.Lock()


def _publish(job_id: str, data: dict[str, Any]) -> None:
    """Publish event to all subscribers of a job channel (thread-safe)."""
    with _lock:
        queues = list(_job_channels.get(job_id, []))
    for q in queues:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass


@router.get("/{job_id}/events")
async def job_events(request: Request, job_id: str):
    """Server-Sent Events endpoint for job progress."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    _job_channels.setdefault(job_id, []).append(queue)

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    if data.get("type") in ("rewrite_done", "rewrite_error", "tts_done", "tts_error", "tts_cancelled", "carnival_done", "carnival_error", "correct_done", "correct_error", "material_done", "material_error"):
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            queues = _job_channels.get(job_id, [])
            if queue in queues:
                queues.remove(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

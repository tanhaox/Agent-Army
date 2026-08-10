"""Whisper 模型加载与缓存 — 进程级单例, 规避 CTranslate2 重复构造崩溃.

行为逐字迁移自原 alignment_service.py (2026-08-08 包化重构).
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from app.config import get_config

logger = logging.getLogger(__name__)

# Local cache path for large-v3 model
_WHISPER_LOCAL_CACHE = Path(os.path.expanduser(
    "~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3"
    "/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478"
))

# Process-level model singleton — repeated WhisperModel construction in the
# same process corrupts CTranslate2 state (2nd+ load raises
# json.exception.type_error.302 in generate), and reloading costs ~70s.
_MODEL_CACHE: dict[tuple[str, str], "WhisperModel"] = {}

try:
    from faster_whisper import WhisperModel
except Exception as _exc:  # pragma: no cover
    WhisperModel = None  # type: ignore[misc,assignment]
    logger.debug("faster_whisper not importable: %s", _exc)

__all__ = ["WhisperModel", "_WHISPER_LOCAL_CACHE", "_MODEL_CACHE", "_ensure_model"]


def _start_heartbeat(
    on_event: Callable[[dict[str, Any]], None] | None,
) -> tuple[threading.Event, threading.Thread | None]:
    """模型加载可能持续 ~70s，发送可感知心跳避免日志面板长时间静默."""
    heartbeat_stop = threading.Event()
    if on_event is None:
        return heartbeat_stop, None

    def _emit_heartbeat() -> None:
        start = time.monotonic()
        while not heartbeat_stop.wait(5.0):
            elapsed = int(time.monotonic() - start)
            on_event({
                "type": "alignment_heartbeat",
                "msg": f"Whisper 模型加载中… 已 {elapsed}s",
                "elapsed_sec": elapsed,
                "stage": "model_load",
            })

    heartbeat_thread = threading.Thread(target=_emit_heartbeat, daemon=True)
    heartbeat_thread.start()
    return heartbeat_stop, heartbeat_thread


def _ensure_model(
    model_size: str | None = None,
    device: str | None = None,
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> "WhisperModel":
    if WhisperModel is None:
        raise ImportError(
            "faster-whisper is required for alignment. "
            "Install it with: pip install faster-whisper"
        )
    cfg = get_config().defaults
    size = model_size or cfg.whisper_model_size
    dev = device or cfg.whisper_device
    compute_type = "float32"  # CTranslate2 4.8.1 workaround

    cached = _MODEL_CACHE.get((size, dev))
    if cached is not None:
        return cached

    heartbeat_stop, heartbeat_thread = _start_heartbeat(on_event)

    if on_event:
        on_event({"type": "model_load_start", "msg": f"加载 Whisper 模型 {size} ({dev})… 首次约 70s"})

    try:
        # Use local cache path directly to avoid network issues
        model_path = str(_WHISPER_LOCAL_CACHE) if _WHISPER_LOCAL_CACHE.exists() else size
        logger.info("Loading Whisper model %s on %s (%s)", model_path, dev, compute_type)
        model = WhisperModel(model_path, device=dev, compute_type=compute_type)
        _MODEL_CACHE[(size, dev)] = model
    finally:
        heartbeat_stop.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=1.0)

    if on_event:
        on_event({"type": "model_load_done", "msg": f"Whisper 模型加载完成 ({size})", "device": dev})
    return model

import gc
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import torch
from faster_whisper import WhisperModel
from zhconv import convert as zhconv_convert

from app.core.config import settings

logger = logging.getLogger(__name__)

# Use HuggingFace mirror for China network
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ---------------------------------------------------------------------------
# Auto-detect best device & compute type
# ---------------------------------------------------------------------------
_device = "cuda" if torch.cuda.is_available() else "cpu"
_compute_type = "float16" if _device == "cuda" else "int8"
_model_size = "large-v3" if _device == "cuda" else "medium"
# ---------------------------------------------------------------------------


@dataclass
class TranscriptionResult:
    text: str
    segments: list[dict]
    duration: float


@dataclass
class TranscriptionProgress:
    """Segment-level progress emitted during transcription."""
    segment_index: int
    start: float
    end: float
    text: str
    total_duration_seconds: float | None = None
    estimated_total_seconds: float | None = None


# ---------------------------------------------------------------------------
# Singleton model – loaded once, reused across all calls
# ---------------------------------------------------------------------------
_model: WhisperModel | None = None
_model_lock = threading.Lock()
_gpu_lock = threading.Lock()
_model_failed = False
_model_loaded_size: str | None = None


def _get_or_load_model() -> WhisperModel:
    """Return the global WhisperModel singleton, loading it if necessary.

    Thread-safe: only one thread performs the load; others wait.
    """
    global _model, _model_failed, _model_loaded_size

    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model
        if _model_failed:
            raise RuntimeError("Whisper 模型不可用（加载失败或环境不兼容）")

        model_path = Path(settings.WHISPER_MODEL_PATH)
        if model_path.exists() and any(model_path.iterdir()):
            logger.info("Loading Whisper model from local path: %s (device=%s, compute=%s)",
                        model_path, _device, _compute_type)
            try:
                _model = WhisperModel(
                    str(model_path),
                    device=_device,
                    compute_type=_compute_type,
                )
                _model_loaded_size = str(model_path)
            except Exception as e:
                logger.error("Failed to load local Whisper model: %s", e)
                _model_failed = True
                raise
        else:
            for size in [_model_size, "medium", "small", "base"]:
                try:
                    logger.info("Downloading/loading Whisper model: %s (device=%s, compute=%s)",
                                size, _device, _compute_type)
                    _model = WhisperModel(
                        size,
                        device=_device,
                        compute_type=_compute_type,
                    )
                    _model_loaded_size = size
                    logger.info("Whisper model %s loaded successfully on %s", size, _device)
                    break
                except Exception as e:
                    logger.warning("Failed to load Whisper model %s: %s", size, e)
            if _model is None:
                _model_failed = True
                raise RuntimeError("无法加载任何 Whisper 模型")

        return _model


def _cleanup_gpu() -> None:
    """Release GPU memory after a transcription run (thread-safe)."""
    with _gpu_lock:
        gc.collect()
        if _device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()


# ---------------------------------------------------------------------------
# Public API (backward-compatible class kept as thin wrapper)
# ---------------------------------------------------------------------------
class WhisperASR:
    """Thin wrapper around the module-level singleton model.

    All instances share the same underlying WhisperModel so we never
    load the model twice.
    """

    def __init__(self, model_size: str | None = None, device: str | None = None,
                 compute_type: str | None = None):
        # Accept but ignore legacy params – we always use auto-detected values.
        self.model_size = model_size or _model_size
        self.device = device or _device
        self.compute_type = compute_type or _compute_type

    def _load_model(self) -> WhisperModel:
        return _get_or_load_model()

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        on_progress: Callable[[TranscriptionProgress], None] | None = None,
    ) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {audio_path}")

        model = self._load_model()
        # Force Simplified Chinese — Whisper randomly outputs Traditional even with language="zh"
        if language is None:
            language = "zh"
        segments_iter, info = model.transcribe(
            str(path),
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                threshold=0.5,
            ),
        )

        segments: list[dict] = []
        total_duration = 0.0
        seg_count = 0
        for seg in segments_iter:
            seg_count += 1
            text = zhconv_convert(seg.text.strip(), "zh-cn")
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": text,
            })
            total_duration = seg.end

            if on_progress:
                on_progress(TranscriptionProgress(
                    segment_index=seg_count,
                    start=seg.start,
                    end=seg.end,
                    text=text,
                    total_duration_seconds=total_duration,
                    estimated_total_seconds=info.duration,
                ))

        full_text = " ".join(s["text"] for s in segments)
        logger.info("Transcribed %s: %.1fs audio, %d segments", audio_path, info.duration, len(segments))

        _cleanup_gpu()

        return TranscriptionResult(
            text=full_text,
            segments=segments,
            duration=info.duration,
        )

    def batch_transcribe(
        self,
        audio_paths: list[str],
        language: str | None = None,
        on_file_progress: Callable[[int, int, str], None] | None = None,
    ) -> list[TranscriptionResult]:
        results: list[TranscriptionResult] = []
        total = len(audio_paths)
        for i, path in enumerate(audio_paths):
            if on_file_progress:
                on_file_progress(i + 1, total, path)
            try:
                result = self.transcribe(path, language=language)
                results.append(result)
            except (FileNotFoundError, ValueError) as e:
                logger.error("Failed to transcribe %s: %s", path, e)
                results.append(TranscriptionResult(text="", segments=[], duration=0.0))
            finally:
                _cleanup_gpu()
        return results


# Module-level engine instance for backward compat
asr_engine = WhisperASR()

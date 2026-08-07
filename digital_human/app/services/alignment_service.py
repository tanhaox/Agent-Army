"""Whisper forced alignment — map script segments to real audio timings.

Pipeline:
1. faster-whisper transcribe the whole audio with word timestamps.
2. Greedily group word-level timestamps into segments by matching segment text.
3. Return word_segments + per-segment start/end/duration.

This is intentionally a backend service (no HTTP client here).
"""
from __future__ import annotations

import logging
import os
import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.config import get_config

logger = logging.getLogger(__name__)

# Force HuggingFace Hub offline — model is cached locally, network is unreliable
os.environ["HF_HUB_OFFLINE"] = "1"

# Auto-patch tokenizer.json before faster_whisper loads it
# (adds 1609 Whisper special tokens to fix token_to_id() returning None)
from .tokenizer_fix import apply_tokenizer_fix  # noqa: E402,F401

from .director_events import PlanCancelled  # noqa: E402,F401  (shared sentinel)

try:
    from faster_whisper import WhisperModel
except Exception as _exc:  # pragma: no cover
    WhisperModel = None  # type: ignore[misc,assignment]
    logger.debug("faster_whisper not importable: %s", _exc)

# Local cache path for large-v3 model
_WHISPER_LOCAL_CACHE = Path(os.path.expanduser(
    "~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3"
    "/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478"
))

# Process-level model singleton — repeated WhisperModel construction in the
# same process corrupts CTranslate2 state (2nd+ load raises
# json.exception.type_error.302 in generate), and reloading costs ~70s.
_MODEL_CACHE: dict[tuple[str, str], "WhisperModel"] = {}


@dataclass
class WordSegment:
    text: str
    start: float
    end: float
    probability: float


@dataclass
class SegmentTiming:
    segment_id: str
    text: str
    start: float
    end: float
    duration: float
    words: list[WordSegment]


def _normalize(text: str) -> str:
    """Strip whitespace and collapse internal spaces."""
    return " ".join(text.split())


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

    # 模型加载可能持续 ~70s，发送可感知心跳避免日志面板长时间静默
    heartbeat_stop = threading.Event()
    heartbeat_thread: threading.Thread | None = None
    if on_event:
        def _emit_heartbeat():
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


def _transcribe_words(
    audio_path: Path,
    model: "WhisperModel" | None = None,
    language: str = "zh",
    vad_filter: bool = True,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> list[WordSegment]:
    """Transcribe audio and return segment-level timestamps as coarse "words".

    WORKAROUND: word_timestamps=False to avoid CTranslate2 4.6.0 align() bug
    (nlohmann JSON type_error in Whisper::align). Each Whisper segment is
    treated as a single coarse "word" — downstream _match_segments uses
    proportional character-count distribution instead of greedy word matching.
    """
    if model is None:
        model = _ensure_model()

    if on_event:
        on_event({"type": "alignment_progress", "msg": "Whisper 转录开始…"})

    # NOTE: word_timestamps=False to avoid CTranslate2 4.6.0 align() bug
    # (nlohmann JSON type_error in Whisper::align). Each Whisper segment is
    # treated as a single coarse "word" — downstream _match_segments uses
    # proportional character-count distribution instead of greedy word matching.
    #
    # suppress_tokens is NOT passed (defaults to [-1]) because passing an
    # empty list crashes CTranslate2 4.6.0's generate() with int8 models.
    segments, _info = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=False,  # ← CTranslate2 4.6.0 workaround
        vad_filter=vad_filter,
        vad_parameters={
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 30.0,
        },
    )

    words: list[WordSegment] = []
    last_emit = 0
    for idx, seg in enumerate(segments):
        if is_cancelled and is_cancelled():
            raise PlanCancelled
        text = _normalize(seg.text)
        if not text:
            continue
        if seg.start is None or seg.end is None:
            continue
        words.append(
            WordSegment(
                text=text,
                start=round(float(seg.start), 3),
                end=round(float(seg.end), 3),
                probability=1.0,  # segment-level, no per-word probability
            )
        )
        # 每收到 10 个 Whisper 段回传一次进度，避免长音频全程静默
        if on_event and len(words) - last_emit >= 10:
            on_event({
                "type": "alignment_progress",
                "msg": f"Whisper 转录中… ({len(words)} segments)",
                "segments_seen": len(words),
            })
            last_emit = len(words)

    if on_event:
        on_event({
            "type": "alignment_progress",
            "msg": f"Whisper 转录完成: {len(words)} segments",
            "segments_seen": len(words),
        })
    return words


def _match_segments(
    words: list[WordSegment],
    segments: list[dict[str, Any]],
    on_event: Callable[[dict[str, Any]], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> list[SegmentTiming]:
    """Distribute script segments proportionally across the audio timeline.

    With word_timestamps disabled (CTranslate2 4.6.0 workaround), each "word"
    is actually a coarse Whisper segment. Instead of greedy word-by-word
    matching, we distribute time proportionally by character count — a
    reliable approximation for Chinese TTS where speaking duration is roughly
    proportional to text length.
    """
    if on_event:
        on_event({"type": "alignment_progress", "msg": f"文本-音频匹配中… ({len(segments)} 个脚本段)"})

    timings: list[SegmentTiming] = []

    if not words or not segments:
        for seg in segments:
            timings.append(
                SegmentTiming(
                    segment_id=str(seg.get("id", "")),
                    text=_normalize(seg.get("text") or ""),
                    start=0.0, end=0.0, duration=0.0, words=[],
                )
            )
        return timings

    total_start = words[0].start
    total_end = words[-1].end
    total_duration = max(0.001, total_end - total_start)

    # Calculate total character count across all segments
    total_chars = sum(len(_normalize(s.get("text") or "")) for s in segments)

    if total_chars == 0:
        total_chars = len(segments)  # fallback: equal distribution

    current_time = total_start
    for i, seg in enumerate(segments):
        if is_cancelled and is_cancelled():
            raise PlanCancelled
        seg_text = _normalize(seg.get("text") or "")
        seg_id = str(seg.get("id", ""))
        char_count = len(seg_text)

        if char_count == 0:
            seg_duration = 0.0
        else:
            seg_duration = (char_count / total_chars) * total_duration

        seg_end = min(current_time + seg_duration, total_end)
        duration = max(0.0, round(seg_end - current_time, 3))

        timings.append(
            SegmentTiming(
                segment_id=seg_id,
                text=seg_text,
                start=round(current_time, 3),
                end=round(seg_end, 3),
                duration=duration,
                words=[],
            )
        )
        current_time = seg_end

        # 每处理 20 个脚本段回传一次进度
        if on_event and (i + 1) % 20 == 0:
            on_event({
                "type": "alignment_progress",
                "msg": f"文本-音频匹配中… ({i + 1}/{len(segments)})",
                "matched": i + 1,
                "total": len(segments),
            })

    if on_event:
        on_event({
            "type": "alignment_progress",
            "msg": f"文本-音频匹配完成 ({len(timings)} timings)",
            "matched": len(timings),
            "total": len(segments),
        })
    return timings


def align_from_tts_durations(
    segments: list[dict[str, Any]],
    *,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Fast path — build segment timings straight from TTS audio durations.

    ID-024: the TTS pass already produced one wav per script segment with a
    known ``duration``. Whisper re-transcription of the whole paragraph is pure
    waste, so when every segment has a duration we lay out the timeline as a
    simple concatenation (each segment starts where the previous one ended) and
    skip faster-whisper entirely. Word-level sub-segment timing is unavailable
    here (slots are segment-aligned anyway), so ``words`` is empty.

    Returns the same shape as :func:`align_script_segments`.
    """
    if on_event:
        on_event({
            "type": "alignment_progress",
            "msg": f"使用 TTS 段落时长建时间轴… ({len(segments)} segments)",
        })

    timings: list[SegmentTiming] = []
    current = 0.0
    for i, seg in enumerate(segments):
        if is_cancelled and is_cancelled():
            raise PlanCancelled
        seg_id = str(seg.get("id") or "")
        seg_text = _normalize(seg.get("text") or "")
        dur = float(seg.get("duration") or 0.0)
        end = current + dur
        timings.append(
            SegmentTiming(
                segment_id=seg_id,
                text=seg_text,
                start=round(current, 3),
                end=round(end, 3),
                duration=round(dur, 3),
                words=[],
            )
        )
        current = end
        # 每处理 20 个脚本段回传一次进度
        if on_event and (i + 1) % 20 == 0:
            on_event({
                "type": "alignment_progress",
                "msg": f"文本-音频匹配中… ({i + 1}/{len(segments)})",
                "matched": i + 1,
                "total": len(segments),
            })

    total_duration = round(current, 3)
    if on_event:
        on_event({
            "type": "alignment_progress",
            "msg": f"对齐完成: {total_duration:.1f}s (TTS 时长快路径)",
            "matched": len(timings),
            "total": len(segments),
        })

    return {
        "ok": True,
        "error": None,
        "word_segments": [],
        "segment_timings": [
            {
                "segment_id": t.segment_id,
                "text": t.text,
                "start": t.start,
                "end": t.end,
                "duration": t.duration,
            }
            for t in timings
        ],
        "total_duration_sec": total_duration,
        "model": "tts-durations",
        "device": "n/a",
    }


def align_script_segments(
    audio_path: Path | str,
    segments: list[dict[str, Any]],
    *,
    model_size: str | None = None,
    device: str | None = None,
    language: str = "zh",
    on_event: Callable[[dict[str, Any]], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Align script segments to audio.

    Args:
        audio_path: path to the complete generated audio (wav/mp3).
        segments: list of dicts with keys ``id`` and ``text``.
        model_size: override whisper model size.
        device: override whisper device.
        language: audio language (default zh).
        on_event: optional callback for progress events during alignment.

    Returns:
        {
            "ok": bool,
            "word_segments": [{"text": str, "start": float, "end": float}],
            "segment_timings": [{"segment_id": str, "text": str,
                                 "start": float, "end": float,
                                 "duration": float}],
            "total_duration_sec": float,
            "model": str,
            "device": str,
            "error": str | None,
        }
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return {"ok": False, "error": f"audio not found: {audio_path}", "word_segments": [], "segment_timings": []}
    if not shutil.which("ffmpeg"):
        return {"ok": False, "error": "ffmpeg not on PATH", "word_segments": [], "segment_timings": []}

    cfg = get_config().defaults
    size = model_size or cfg.whisper_model_size
    dev = device or cfg.whisper_device

    try:
        model = _ensure_model(size, dev, on_event=on_event)
        words = _transcribe_words(audio_path, model=model, language=language, on_event=on_event, is_cancelled=is_cancelled)
        timings = _match_segments(words, segments, on_event=on_event, is_cancelled=is_cancelled)
    except PlanCancelled:
        raise
    except Exception as exc:
        logger.exception("alignment failed for %s", audio_path)
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "word_segments": [],
            "segment_timings": [],
            "total_duration_sec": None,
            "model": size,
            "device": dev,
        }

    total_duration = round(words[-1].end if words else 0.0, 3)

    word_segments = [
        {"text": w.text, "start": w.start, "end": w.end, "probability": w.probability}
        for w in words
    ]
    segment_timings = [
        {
            "segment_id": t.segment_id,
            "text": t.text,
            "start": t.start,
            "end": t.end,
            "duration": t.duration,
        }
        for t in timings
    ]

    return {
        "ok": True,
        "error": None,
        "word_segments": word_segments,
        "segment_timings": segment_timings,
        "total_duration_sec": total_duration,
        "model": size,
        "device": dev,
    }

"""TTS 编排层: 单段合成 + 自动回退调度 (策略模式).

synthesize(): 单段文本 → WAV, 可选分段拼接; _synthesize_single(): 按
backend 策略表依次尝试引擎, 失败即回退。行为红线 (回退顺序 auto→fish→f5、
错误消息 "<engine>: <exc>" 与 "All TTS backends failed:..."、indextts 缺
master_audio 抛错) 与旧 tts_client.py 逐字一致 — 只改结构, 不改语义。
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Literal

from .audio import _ensure_dir, apply_ffmpeg_params
from .constants import (
    DEFAULT_F5_URL,
    DEFAULT_FISH_URL,
    DEFAULT_INDEXTTS_URL,
    DEFAULT_OUTPUT_DIR,
)
from .engines import f5_tts, fish_speech_tts, indextts_tts
from .segments import _synthesize_segments

logger = logging.getLogger(__name__)
Backend = Literal["fish", "f5", "indextts", "auto"]

_BACKEND_ORDER: dict[Backend, tuple[str, ...]] = {
    "auto": ("fish", "f5"),
    "fish": ("fish",),
    "f5": ("f5",),
    "indextts": ("indextts",),
}

__all__ = ["synthesize", "_synthesize_single", "Backend"]


def synthesize(
    text: str,
    output_path: Path | None = None,
    backend: Backend = "auto",
    voice_id: str = "default",
    reference_audio: Path | None = None,
    reference_text: str = "",
    base_url_fish: str = DEFAULT_FISH_URL,
    base_url_f5: str = DEFAULT_F5_URL,
    base_url_indextts: str = DEFAULT_INDEXTTS_URL,
    master_audio: Path | None = None,
    master_text: str = "",
    master_style: str = "calm",
    segment: bool = False,
    segment_max_chars: int = 120,
    params: dict[str, Any] | None = None,
) -> Path:
    """Generate a WAV file from text. See tts_lib/__init__ docstring for args."""
    _ensure_dir(DEFAULT_OUTPUT_DIR)
    if output_path is None:
        ts = int(time.time())
        safe_voice = "".join(c if c.isalnum() else "_" for c in voice_id) or "default"
        output_path = DEFAULT_OUTPUT_DIR / f"{safe_voice}_{ts}.wav"
    output_path = Path(output_path)
    _ensure_dir(output_path.parent)

    kwargs = _single_kwargs(
        text, backend, voice_id, reference_audio, reference_text,
        base_url_fish, base_url_f5, base_url_indextts, master_audio,
        master_text, master_style, params,
    )
    if not segment:
        return _synthesize_single(output_path=output_path, **kwargs)
    return _synthesize_segments(
        synth_fn=_synthesize_single, output_path=output_path,
        segment_max_chars=segment_max_chars, **kwargs,
    )


def _single_kwargs(
    text: str,
    backend: Backend,
    voice_id: str,
    reference_audio: Path | None,
    reference_text: str,
    base_url_fish: str,
    base_url_f5: str,
    base_url_indextts: str,
    master_audio: Path | None,
    master_text: str,
    master_style: str,
    params: dict[str, Any] | None,
) -> dict[str, Any]:
    """聚合 synthesize → _synthesize_single/_synthesize_segments 的公共参数."""
    return {
        "text": text, "backend": backend, "voice_id": voice_id,
        "reference_audio": reference_audio, "reference_text": reference_text,
        "base_url_fish": base_url_fish, "base_url_f5": base_url_f5,
        "base_url_indextts": base_url_indextts, "master_audio": master_audio,
        "master_text": master_text, "master_style": master_style,
        "params": params,
    }


def _synthesize_single(
    text: str,
    output_path: Path,
    backend: Backend,
    voice_id: str,
    reference_audio: Path | None,
    reference_text: str,
    base_url_fish: str,
    base_url_f5: str,
    base_url_indextts: str = DEFAULT_INDEXTTS_URL,
    master_audio: Path | None = None,
    master_text: str = "",
    master_style: str = "calm",
    params: dict[str, Any] | None = None,
    emo_vector: list[float] | None = None,
    emo_alpha: float = 1.0,
) -> Path:
    """按 backend 策略表依次尝试引擎 (含 "fish"/"f5"/"indextts"), 全败抛 RuntimeError."""
    p = _extract_engine_params(params)
    # 与原版逐字一致: indextts 专属参数在主音频/主文本兜底解析后原位提取。
    p["indextts_master_audio"] = master_audio or reference_audio
    p["indextts_master_text"] = master_text or reference_text or ""
    p["master_style"] = master_style
    p.update(_extract_indextts_params(params))
    # 情绪参数 (2026-08-13, P5): 仅 indextts 消费; fish/f5 无情绪维度, 传了也忽略.
    p["emo_vector"] = emo_vector
    p["emo_alpha"] = emo_alpha

    callbacks = _make_engine_callbacks(
        p, text, output_path, reference_audio, reference_text,
        base_url_fish, base_url_f5, base_url_indextts,
    )

    errors: list[str] = []
    for engine in _BACKEND_ORDER[backend]:
        try:
            return _run_engine(engine, callbacks, p)
        except Exception as exc:
            errors.append(f"{engine}: {exc}")
            if backend == engine:
                raise

    raise RuntimeError("All TTS backends failed:\n" + "\n".join(errors))


def _extract_engine_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Flatten raw params into per-engine kwargs with the old defaults."""
    return {
        "speed": params.get("speed", 1.0) if params else 1.0,
        "pitch": params.get("pitch", 0) if params else 0,
        "volume": params.get("volume", 1.0) if params else 1.0,
        "bass_gain": params.get("bass_gain", 0) if params else 0,
        "presence_gain": params.get("presence_gain", 0) if params else 0,
        "air_gain": params.get("air_gain", 0) if params else 0,
        # fish 后端: 显式 None 表示使用引擎默认值
        "temperature": params.get("temperature") if params else None,
        "top_p": params.get("top_p") if params else None,
        "repetition_penalty": params.get("repetition_penalty") if params else None,
        "seed": params.get("seed") if params else None,
    }


def _extract_indextts_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """indextts 分支专用参数 (与原版 indextts 分支内提取逐字一致)."""
    return {
        "do_sample": params.get("do_sample", True) if params else True,
        "indextts_top_p": params.get("top_p", 0.8) if params else 0.8,
        "indextts_top_k": params.get("top_k", 30) if params else 30,
        "indextts_temperature": params.get("temperature", 0.8) if params else 0.8,
        "indextts_max_text_tokens": (
            params.get("max_text_tokens_per_segment", 120) if params else 120
        ),
    }


def _make_engine_callbacks(
    p: dict[str, Any],
    text: str,
    output_path: Path,
    reference_audio: Path | None,
    reference_text: str,
    base_url_fish: str,
    base_url_f5: str,
    base_url_indextts: str,
) -> dict[str, Callable[[], Path]]:
    """策略表: 每个引擎一个零参数回调, 由 _run_engine 统一执行."""
    return {
        "fish": lambda: fish_speech_tts(
            text=text, output_path=output_path, base_url=base_url_fish,
            reference_audio=reference_audio, reference_text=reference_text,
            temperature=p["temperature"], top_p=p["top_p"],
            repetition_penalty=p["repetition_penalty"], seed=p["seed"]),
        "f5": lambda: f5_tts(
            text=text, output_path=output_path, base_url=base_url_f5,
            ref_audio=reference_audio, ref_text=reference_text),
        "indextts": lambda: indextts_tts(
            text=text, output_path=output_path, base_url=base_url_indextts,
            master_audio=p["indextts_master_audio"],
            master_text=p["indextts_master_text"], master_style=p["master_style"],
            do_sample=p["do_sample"], top_p=p["indextts_top_p"],
            top_k=p["indextts_top_k"], temperature=p["indextts_temperature"],
            max_text_tokens_per_segment=p["indextts_max_text_tokens"],
            seed=p["seed"],
            emo_vector=p.get("emo_vector"), emo_alpha=p.get("emo_alpha", 1.0)),
    }


def _run_engine(
    engine: str,
    callbacks: dict[str, Callable[[], Path]],
    p: dict[str, Any],
) -> Path:
    """Execute one engine callback, then apply ffmpeg params uniformly."""
    if engine not in callbacks:
        raise ValueError(f"unknown engine: {engine}")
    result = callbacks[engine]()
    return apply_ffmpeg_params(
        result,
        speed=p["speed"], pitch=p["pitch"], volume=p["volume"],
        bass_gain=p["bass_gain"], presence_gain=p["presence_gain"],
        air_gain=p["air_gain"],
    )

"""TTS 引擎后端: fish / f5 / indextts 三个策略实现.

每个函数是一个独立的后端策略: 相同的签名 (text, output_path, ...)
返回合成的 WAV 路径。调度逻辑 (回退顺序) 在 orchestrator.py 中,
本模块不感知自动回退 — 职责单一。
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np

from .audio import _write_wav
from .constants import DEFAULT_F5_URL, DEFAULT_FISH_URL, DEFAULT_INDEXTTS_URL
from .http import _http_post_bytes, _http_post_json, _pack_msgpack, requests

__all__ = ["fish_speech_tts", "f5_tts", "indextts_tts"]


def fish_speech_tts(
    text: str,
    output_path: Path,
    base_url: str = DEFAULT_FISH_URL,
    reference_audio: Path | None = None,
    reference_text: str = "",
    temperature: float | None = None,
    top_p: float | None = None,
    repetition_penalty: float | None = None,
    seed: int | None = None,
) -> Path:
    """Call Fish Speech /v1/tts and save WAV."""
    payload = _build_fish_payload(text, reference_audio, reference_text,
                                  temperature, top_p, repetition_penalty, seed)
    url = base_url.rstrip("/") + "/v1/tts"
    packed = _pack_msgpack(payload)
    headers = {"content-type": "application/msgpack"}
    audio_bytes = _fetch_audio_bytes(
        url, packed, headers,
        requests_kwargs={"params": {"format": "msgpack"}},
    )
    if not audio_bytes or len(audio_bytes) < 44:
        raise RuntimeError("Fish Speech returned empty or invalid audio")
    output_path.write_bytes(audio_bytes)
    return output_path


def _build_fish_payload(
    text: str,
    reference_audio: Path | None,
    reference_text: str,
    temperature: float | None,
    top_p: float | None,
    repetition_penalty: float | None,
    seed: int | None,
) -> dict[str, Any]:
    """Mirror the official api_client ServeTTSRequest shape (msgpack-encoded)."""
    references: list[dict] = []
    if reference_audio and reference_audio.exists():
        audio_bytes = reference_audio.read_bytes()
        references.append({"audio": audio_bytes, "text": reference_text or text})
    return {
        "text": text,
        "references": references,
        "reference_id": None,
        "format": "wav",
        "latency": "normal",
        "max_new_tokens": 1024,
        "chunk_length": 200,
        "top_p": top_p if top_p is not None else 0.7,
        "repetition_penalty": repetition_penalty if repetition_penalty is not None else 1.5,
        "temperature": temperature if temperature is not None else 0.3,
        "streaming": False,
        "use_memory_cache": "off",
        "seed": seed,  # None = random; int = deterministic at low temperature
    }


def _fetch_audio_bytes(
    url: str, data: bytes, headers: dict, requests_kwargs: dict | None = None,
) -> bytes:
    """POST raw bytes; prefer requests (msgpack), fall back to urllib."""
    if requests is not None:
        resp = requests.post(url, data=data, headers=headers, timeout=300,
                             **(requests_kwargs or {}))
        if resp.status_code != 200:
            raise RuntimeError(f"Fish Speech HTTP {resp.status_code}: {resp.text[:500]}")
        return resp.content
    return _http_post_bytes(url, data, headers, timeout=300)


def f5_tts(
    text: str,
    output_path: Path,
    base_url: str = DEFAULT_F5_URL,
    ref_audio: Path | None = None,
    ref_text: str = "",
) -> Path:
    """Call F5-TTS Gradio API and save WAV."""
    url = base_url.rstrip("/") + "/api/predict"
    ref_audio_b64 = ""
    if ref_audio and ref_audio.exists():
        ref_audio_b64 = base64.b64encode(ref_audio.read_bytes()).decode("utf-8")
    payload = {
        "fn_index": 0,
        "data": [
            ref_text or text,  # ref_text
            text,              # gen_text
            ref_audio_b64,     # ref_audio (base64)
            "",                # remove_silence (optional)
        ],
    }
    result = _http_post_json(url, payload, timeout=300)
    if not result.get("data"):
        raise RuntimeError(f"F5-TTS returned no data: {result}")
    _decode_f5_response(result["data"][0], base_url, output_path)
    return output_path


def _decode_f5_response(audio_payload: Any, base_url: str, output_path: Path) -> None:
    """Gradio returns [sr, ndarray] or base64 string / file dict depending on version."""
    if isinstance(audio_payload, dict) and "name" in audio_payload:
        file_url = base_url.rstrip("/") + "/file=" + audio_payload["name"]
        audio_bytes = _http_post_bytes(file_url, {}, timeout=60)
        output_path.write_bytes(audio_bytes)
    elif isinstance(audio_payload, str):
        output_path.write_bytes(base64.b64decode(audio_payload))
    else:
        sr, audio_arr = audio_payload
        _write_wav(output_path, np.array(audio_arr), int(sr))


def indextts_tts(
    text: str,
    output_path: Path,
    base_url: str = DEFAULT_INDEXTTS_URL,
    master_audio: Path | None = None,
    master_text: str = "",
    master_style: str = "calm",
    do_sample: bool = True,
    top_p: float = 0.8,
    top_k: int = 30,
    temperature: float = 0.8,
    max_text_tokens_per_segment: int = 120,
    seed: int | None = None,
) -> Path:
    """调 IndexTTS2 api_server (7862) /v1/tts. 响应是 wav bytes, 持久化到 output_path."""
    if master_audio is None or not master_audio.exists():
        raise RuntimeError(
            f"indextts requires master_audio_path, got {master_audio}"
        )
    payload = _build_indextts_payload(
        text, master_audio, master_text, master_style, do_sample, top_p,
        top_k, temperature, max_text_tokens_per_segment, seed,
    )
    audio_bytes = _fetch_indextts_audio(base_url, payload)
    if not audio_bytes or len(audio_bytes) < 44:
        raise RuntimeError("IndexTTS2 returned empty or invalid wav")
    output_path.write_bytes(audio_bytes)
    return output_path


def _build_indextts_payload(
    text: str,
    master_audio: Path,
    master_text: str,
    master_style: str,
    do_sample: bool,
    top_p: float,
    top_k: int,
    temperature: float,
    max_text_tokens_per_segment: int,
    seed: int | None,
) -> dict[str, Any]:
    return {
        "text": text,
        "spk_audio_prompt": str(master_audio.resolve()),
        "master_text": master_text,
        "master_style": master_style,
        "max_text_tokens_per_segment": max_text_tokens_per_segment,
        "do_sample": do_sample,
        "top_p": top_p,
        "top_k": top_k,
        "temperature": temperature,
        "seed": seed,
    }


def _fetch_indextts_audio(base_url: str, payload: dict[str, Any]) -> bytes:
    url = base_url.rstrip("/") + "/v1/tts"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"IndexTTS2 HTTP {exc.code}: {body}") from exc

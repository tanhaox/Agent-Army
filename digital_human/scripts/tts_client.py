"""TTS client for digital human news anchor.

Default backend: Fish Speech local API (http://127.0.0.1:7860)
Fallback backend: F5-TTS local API (http://127.0.0.1:7861)

Usage:
    # Use Fish Speech venv (recommended) so ormsgpack/requests are available:
    "E:/AI/tts/fish-speech/.venv/Scripts/python.exe" scripts/tts_client.py --text "你好，这是测试。"

Fish Speech /v1/tts expects a msgpack-encoded ServeTTSRequest and returns raw
audio bytes (WAV by default).
"""
from __future__ import annotations

import argparse
import base64
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Literal

import numpy as np
import soundfile as sf

# Fish Speech uses msgpack; try the fast implementation first, fall back to msgpack.
try:
    import ormsgpack as _packer
except Exception:  # pragma: no cover
    import msgpack as _packer  # type: ignore[no-redef]

# requests is optional; urllib is the fallback.
try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore[assignment]

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "audio"

DEFAULT_FISH_URL = "http://127.0.0.1:7860"
DEFAULT_F5_URL = "http://127.0.0.1:7861"
DEFAULT_INDEXTTS_URL = "http://127.0.0.1:7862"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _concat_wavs_with_ffmpeg(wav_paths: list[Path], output_path: Path) -> Path:
    """Concatenate multiple WAV files with identical format using FFmpeg concat demuxer."""
    if not wav_paths:
        raise ValueError("No WAV files to concatenate")
    if len(wav_paths) == 1:
        shutil.copy2(wav_paths[0], output_path)
        return output_path

    concat_script = None
    try:
        concat_script = Path(tempfile.mktemp(suffix=".txt"))
        concat_script.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in wav_paths),
            encoding="utf-8",
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_script),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"FFmpeg concat failed: {exc.stderr}") from exc
    finally:
        if concat_script:
            concat_script.unlink(missing_ok=True)

    if not output_path.exists():
        raise RuntimeError("FFmpeg concat produced no output")
    return output_path


def apply_ffmpeg_params(
    wav_path: Path,
    speed: float = 1.0,
    pitch: float = 0,
    volume: float = 1.0,
    bass_gain: float = 0,
    presence_gain: float = 0,
    air_gain: float = 0,
) -> Path:
    """Apply speed/pitch/volume/timbre to a WAV file using FFmpeg audio filters.

    Uses rubberband filter for pitch (preserves formant quality, unlike asetrate)
    and atempo for speed. The pitch parameter is in SEMITONES (from UI) and is
    converted internally to a frequency ratio for rubberband.

    Timbre dimensions use FFmpeg's shelving/peak EQ filters to shape voice
    character: bass (low-shelf ~200 Hz), presence (peak EQ ~2 kHz), air
    (high-shelf ~6 kHz).

    All-default values are skipped with zero overhead.
    Returns the (possibly replaced) wav_path.
    """
    import math

    filters: list[str] = []

    # Volume (applied first)
    if abs(volume - 1.0) > 0.01:
        filters.append(f"volume={volume}")

    # Pitch via rubberband filter — preserves vocal formants, sounds natural
    # rubberband expects a FREQUENCY RATIO (1.0 = original)
    # Formula: ratio = 2^(semitones / 12)
    #   +3 semitones → 1.189, -3 semitones → 0.841
    if pitch != 0:
        pitch_ratio = 2 ** (pitch / 12.0)
        filters.append(f"rubberband=pitch={pitch_ratio}:tempo=1.0")

    # Speed via atempo (rubberband for pitch already handled above)
    if abs(speed - 1.0) > 0.01:
        filters.append(f"atempo={speed}")

    # ── Timbre / EQ shaping ────────────────────────────────────────────
    # bass: low-shelf filter at 200 Hz, Q=0.7 (gradual slope)
    if abs(bass_gain) > 0.5:
        filters.append(f"lowshelf=f=200:width_type=o:width=0.7:g={bass_gain}")

    # presence: peak EQ at 2 kHz, Q=1.0 (mid-range clarity/body)
    if abs(presence_gain) > 0.5:
        filters.append(f"equalizer=f=2000:width_type=o:width=1.0:g={presence_gain}")

    # air: high-shelf filter at 6 kHz, Q=0.7 (brightness/air)
    if abs(air_gain) > 0.5:
        filters.append(f"highshelf=f=6000:width_type=o:width=0.7:g={air_gain}")
    # ──────────────────────────────────────────────────────────────────

    if not filters:
        return wav_path

    filter_str = ",".join(filters)
    tmp = Path(tempfile.mktemp(suffix=".wav"))

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(wav_path),
            "-filter_complex", filter_str,
            str(tmp),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        shutil.move(str(tmp), str(wav_path))
    except subprocess.CalledProcessError as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"FFmpeg filter failed ({filter_str}): {exc.stderr[:500]}"
        ) from exc

    return wav_path


def _merge_lines_for_batch(lines: list[str], max_chars: int = 300) -> list[list[int]]:
    """Group line indices into batches where each batch total ≤ max_chars.

    Lines are grouped purely by character count. Each group is synthesized as
    a single TTS call, then split back into individual segments by silence detection.

    Args:
        lines: List of text lines (one per segment).
        max_chars: Soft cap — a batch that ends exactly at max_chars is fine;
            a single line longer than max_chars gets its own batch.

    Returns:
        List of index groups, e.g. [[0, 1], [2, 3, 4], [5]]
    """
    batches: list[list[int]] = []
    current: list[int] = []
    current_chars = 0
    for idx, line in enumerate(lines):
        if current_chars + len(line) > max_chars and current:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(idx)
        current_chars += len(line)
    if current:
        batches.append(current)
    return batches


def _split_wav_by_silence(
    wav_path: Path,
    expected_count: int,
    output_dir: Path,
    stem: str,
    line_texts: list[str],
) -> list[Path]:
    """Split a WAV into per-segment files using FFmpeg silence detection.

    The input WAV was generated from lines joined with '||' markers, which
    produce natural ~0.3-0.5s pauses. Silence detection at -30dB / 0.2s
    locates the boundaries.

    If detection finds fewer splits than expected, falls back to proportional
    division by character count (each segment's share of total chars).

    Args:
        wav_path: The group WAV to split.
        expected_count: Number of segments expected.
        output_dir: Where to write split WAVs.
        stem: Output filename stem (e.g. '003' for batch 3).
        line_texts: Original line texts for proportional fallback.

    Returns:
        List of Paths: [[output_dir/003_0.wav, output_dir/003_1.wav, ...].
    """
    import re as _re
    import math as _math

    # ── Step 1: detect silence ──
    try:
        cmd = [
            "ffmpeg", "-i", str(wav_path),
            "-af", "silencedetect=noise=-30dB:d=0.2",
            "-f", "null", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # Parse silence_end timestamps
        splits = []
        for line in result.stderr.split("\n"):
            m = _re.search(r"silence_end:\s*([\d.]+)", line)
            if m:
                splits.append(float(m.group(1)))
    except Exception:
        splits = []

    # ── Step 2: get total duration ──
    try:
        info = sf.info(str(wav_path))
        total_dur = round(info.duration, 3)
    except Exception:
        total_dur = 0.0

    # ── Step 3: decide split points ──
    # Filter splits that are reasonable boundaries (not too close to edges)
    min_split = 0.3
    valid_splits = [s for s in splits if min_split < s < total_dur - min_split]

    # We need expected_count-1 split points for expected_count segments
    if len(valid_splits) >= expected_count - 1:
        # Use the best N-1 splits (take from middle of each gap)
        use_splits = valid_splits[: expected_count - 1]
    else:
        # Fallback: proportional by char count
        total_chars = sum(len(t) for t in line_texts) or 1
        use_splits = []
        cum = 0.0
        for t in line_texts[:-1]:
            cum += len(t) / total_chars * total_dur
            use_splits.append(cum)

    # ── Step 4: cut segments with FFmpeg aselect ──
    split_points = [0.0] + use_splits + [total_dur]
    out_paths: list[Path] = []

    for i in range(len(split_points) - 1):
        start = split_points[i]
        end = split_points[i + 1]
        seg_path = output_dir / f"{stem}_{i:02d}.wav"
        dur = end - start
        if dur < 0.05:
            # Sub-50ms segment — produce a minimal silent WAV
            _write_wav(seg_path, np.zeros((1,), dtype=np.float32), 24000)
            out_paths.append(seg_path)
            continue

        cmd = [
            "ffmpeg", "-y",
            "-i", str(wav_path),
            "-af", f"aselect=between(t\\,{start}\\,{end}),asetpts=N/SR/N",
            str(seg_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except Exception:
            _write_wav(seg_path, np.zeros((1,), dtype=np.float32), 24000)
        out_paths.append(seg_path)

    return out_paths


def _sanitize_for_fish(text: str) -> str:
    """Work around Fish Speech s2-pro bug: ASCII + space + Chinese triggers 500.

    Fish Speech fails on strings like "GPT-5 真的要来了" (ASCII, space, CJK).
    Removing the space between ASCII alphanumerics and CJK characters avoids the
    crash without changing pronunciation materially.
    """
    import re
    # Remove spaces between ASCII alphanumerics/punctuation and CJK.
    # Run repeatedly until no more changes because patterns can overlap.
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"([a-zA-Z0-9\-._%/+])(\s+)([一-鿿])", r"\1\3", text)
        text = re.sub(r"([一-鿿])(\s+)([a-zA-Z0-9\-._%/+])", r"\1\3", text)
    # Collapse multiple spaces to one.
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _tts_text(text: str) -> str:
    """Prepare text for TTS inference.

    ``||`` is a pipeline pause hint, not a real phoneme. Fish Speech will not
    interpret it as silence; replace it with a comma. Emotion tags such as
    ``[calm]`` and paralinguistic markers such as ``(break)`` are stripped
    because many Fish Speech builds crash when CJK immediately follows an
    ASCII tag. The original line (with tags) is preserved in the manifest.
    """
    # Strip emotion / paralinguistic control tags.
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\([^)]+\)", "", text)
    # Pipeline pause hint -> comma.
    text = text.replace("||", "，")
    text = re.sub(r"[,，]{2,}", "，", text)
    text = re.sub(r"[,，]\s*([。！？])", r"\1", text)
    return text.strip()


def _split_text(
    text: str,
    segment_delimiter: str = "||",
    max_chars: int = 120,
    sentence_delimiters: str = "。；？！\n",
) -> list[str]:
    """Split text into synthesis segments.

    Priority:
      1. Explicit segment_delimiter (e.g. '||' from scripts) produces exact segments.
      2. Falls back to sentence-level splitting by sentence_delimiters.
      3. Hard-truncates any segment exceeding max_chars.
    """
    text = text.strip()
    if not text:
        return []

    if segment_delimiter in text:
        raw_segments = [s.strip() for s in text.split(segment_delimiter) if s.strip()]
    else:
        raw_segments = []
        current = ""
        for ch in text:
            current += ch
            if ch in sentence_delimiters and current.strip():
                raw_segments.append(current.strip())
                current = ""
        if current.strip():
            raw_segments.append(current.strip())

    segments: list[str] = []
    for s in raw_segments:
        s = _sanitize_for_fish(s)
        if len(s) <= max_chars:
            if s:
                segments.append(s)
            continue
        for i in range(0, len(s), max_chars):
            chunk = s[i : i + max_chars].strip()
            if chunk:
                segments.append(chunk)
    return segments


def _pack_msgpack(payload: dict) -> bytes:
    if hasattr(_packer, "packb"):
        return _packer.packb(payload)  # type: ignore[union-attr]
    return _packer.pack(payload)


def _http_post_bytes(url: str, data: bytes, headers: dict, timeout: int = 300) -> bytes:
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _http_post_json(url: str, payload: dict, timeout: int = 300) -> dict:
    import json

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> Path:
    sf.write(str(path), audio, sample_rate)
    return path


# -----------------------------------------------------------------------------
# Fish Speech backend
# -----------------------------------------------------------------------------
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
    """Call Fish Speech /v1/tts and save WAV.

    The endpoint accepts a msgpack-encoded ServeTTSRequest and returns raw audio
    bytes. We mirror the official api_client payload shape.

    When a seed is provided (and temperature is low/None), output is
    deterministic for the same text + params combination.
    """
    references: list[dict] = []
    if reference_audio and reference_audio.exists():
        audio_bytes = reference_audio.read_bytes()
        references.append({"audio": audio_bytes, "text": reference_text or text})

    payload: dict[str, Any] = {
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

    url = base_url.rstrip("/") + "/v1/tts"
    packed = _pack_msgpack(payload)
    headers = {"content-type": "application/msgpack"}

    if requests is not None:
        resp = requests.post(url, params={"format": "msgpack"}, data=packed, headers=headers, timeout=300)
        if resp.status_code != 200:
            raise RuntimeError(f"Fish Speech HTTP {resp.status_code}: {resp.text[:500]}")
        audio_bytes = resp.content
    else:
        audio_bytes = _http_post_bytes(url, packed, headers, timeout=300)

    if not audio_bytes or len(audio_bytes) < 44:
        raise RuntimeError("Fish Speech returned empty or invalid audio")

    output_path.write_bytes(audio_bytes)
    return output_path


# -----------------------------------------------------------------------------
# F5-TTS backend (fallback)
# -----------------------------------------------------------------------------
def f5_tts(
    text: str,
    output_path: Path,
    base_url: str = DEFAULT_F5_URL,
    ref_audio: Path | None = None,
    ref_text: str = "",
) -> Path:
    """Call F5-TTS Gradio API and save WAV.

    F5-TTS Gradio predict endpoint (simplified):
        POST /api/predict with fn_index depending on app version.
    This is a best-effort fallback; endpoint may need adjustment for your F5-TTS version.
    """
    import json

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

    # Gradio returns audio as [sample_rate, ndarray] or base64 string depending on version.
    audio_payload = result["data"][0]
    if isinstance(audio_payload, dict) and "name" in audio_payload:
        file_url = base_url.rstrip("/") + "/file=" + audio_payload["name"]
        audio_bytes = _http_post_bytes(file_url, {}, timeout=60)
        output_path.write_bytes(audio_bytes)
    elif isinstance(audio_payload, str):
        output_path.write_bytes(base64.b64decode(audio_payload))
    else:
        sr, audio_arr = audio_payload
        _write_wav(output_path, np.array(audio_arr), int(sr))

    return output_path


# -----------------------------------------------------------------------------
# IndexTTS2 backend (target)
# -----------------------------------------------------------------------------
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

    payload = {
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
    import json as _json

    url = base_url.rstrip("/") + "/v1/tts"
    data = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            audio_bytes = resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"IndexTTS2 HTTP {exc.code}: {body}") from exc

    if not audio_bytes or len(audio_bytes) < 44:
        raise RuntimeError("IndexTTS2 returned empty or invalid wav")

    output_path.write_bytes(audio_bytes)
    return output_path


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def synthesize(
    text: str,
    output_path: Path | None = None,
    backend: Literal["fish", "f5", "indextts", "auto"] = "auto",
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
    """Generate a WAV file from text.

    Args:
        text: Chinese text to synthesize.
        output_path: Where to save WAV. Defaults to outputs/audio/<voice_id>_<ts>.wav
        backend: "fish", "f5", "indextts", or "auto" (try fish first, then f5).
        voice_id: Voice identifier used in filename and future voice registry.
        reference_audio: Optional reference audio for voice cloning.
        reference_text: Text corresponding to reference audio.
        base_url_fish: Fish Speech API base URL.
        base_url_f5: F5-TTS API base URL.
        base_url_indextts: IndexTTS2 API base URL (default port 7862).
        master_audio: IndexTTS2 master tape audio path; falls back to reference_audio.
        master_text: Text spoken in master_audio for IndexTTS2 prompt conditioning.
        master_style: IndexTTS2 emotion preset (calm/excited/relaxed).
        segment: If True, split long text into short segments, synthesize each,
            then concatenate with FFmpeg. This bypasses Fish Speech's long-text
            encoding bug and improves stability.
        segment_max_chars: Max characters per segment when segment=True.
    """
    _ensure_dir(DEFAULT_OUTPUT_DIR)

    if output_path is None:
        ts = int(time.time())
        safe_voice = "".join(c if c.isalnum() else "_" for c in voice_id) or "default"
        output_path = DEFAULT_OUTPUT_DIR / f"{safe_voice}_{ts}.wav"

    output_path = Path(output_path)
    _ensure_dir(output_path.parent)

    if not segment:
        return _synthesize_single(
            text=text,
            output_path=output_path,
            backend=backend,
            voice_id=voice_id,
            reference_audio=reference_audio,
            reference_text=reference_text,
            base_url_fish=base_url_fish,
            base_url_f5=base_url_f5,
            base_url_indextts=base_url_indextts,
            master_audio=master_audio,
            master_text=master_text,
            master_style=master_style,
            params=params,
        )

    segments = _split_text(text, max_chars=segment_max_chars)
    if not segments:
        raise ValueError("No text to synthesize after segmentation")

    segment_paths: list[Path] = []
    tmp_dir = _ensure_dir(output_path.parent / ".segments")
    try:
        for idx, seg in enumerate(segments):
            seg_path = tmp_dir / f"{output_path.stem}_{idx:03d}.wav"
            _synthesize_single(
                text=seg,
                output_path=seg_path,
                backend=backend,
                voice_id=voice_id,
                reference_audio=reference_audio,
                reference_text=reference_text,
                base_url_fish=base_url_fish,
                base_url_f5=base_url_f5,
                base_url_indextts=base_url_indextts,
                master_audio=master_audio,
                master_text=master_text,
                master_style=master_style,
                params=params,
            )
            segment_paths.append(seg_path)
        return _concat_wavs_with_ffmpeg(segment_paths, output_path)
    finally:
        for seg_path in segment_paths:
            seg_path.unlink(missing_ok=True)


def synthesize_lines(
    text: str,
    output_dir: Path,
    backend: Literal["fish", "f5", "indextts", "auto"] = "auto",
    voice_id: str = "default",
    reference_audio: Path | None = None,
    reference_text: str = "",
    base_url_fish: str = DEFAULT_FISH_URL,
    base_url_f5: str = DEFAULT_F5_URL,
    base_url_indextts: str = DEFAULT_INDEXTTS_URL,
    master_audio: Path | None = None,
    master_text: str = "",
    master_style: str = "calm",
    progress_callback: Callable[[int, int, str, dict[str, Any] | None], None] | None = None,
    params: dict[str, Any] | None = None,
    batch_max_chars: int = 300,
) -> dict[str, Any]:
    """Generate one WAV per non-empty line, but batch lines into ~300 char TTS calls.

    Instead of one TTS call per line (which amplifies randomness), consecutive
    lines are merged into batches of ~batch_max_chars characters. Each batch is
    synthesized as a single TTS call, then the audio is split back into per-line
    segments using FFmpeg silence detection.

    Control characters such as '||', '。', '！' inside a line are preserved because
    they drive TTS pacing/intonation.

    Returns:
        A manifest dict with voice_id, backend, sample_rate and a segments list.
        Also writes manifest.json into output_dir.
    """
    import json

    _ensure_dir(output_dir)

    lines = [line.strip() for line in text.splitlines()]
    lines = [_sanitize_for_fish(line) for line in lines if line.strip()]
    if not lines:
        raise ValueError("No non-empty lines to synthesize")

    # ── Step 1: group lines into batches ──
    # Each batch will be TTS'd as one piece, then split back.
    batch_groups = _merge_lines_for_batch(lines, max_chars=batch_max_chars)

    segment_paths: list[Path] = []
    manifest_segments: list[dict[str, Any]] = []
    completed = 0

    try:
        for batch_idx, line_indices in enumerate(batch_groups):
            batch_lines = [lines[i] for i in line_indices]

            # ── Step 2: join lines for TTS ──
            # Use a sentence separator that Fish Speech naturally pauses at.
            # The "||" marker gets replaced with "，" in _tts_text(), which
            # creates a natural ~0.3s break between lines.
            batch_text = "||".join(batch_lines)
            inference_text = _tts_text(batch_text)

            batch_path = output_dir / f"_batch_{batch_idx:03d}.wav"
            _synthesize_single(
                text=inference_text,
                output_path=batch_path,
                backend=backend,
                voice_id=voice_id,
                reference_audio=reference_audio,
                reference_text=reference_text,
                base_url_fish=base_url_fish,
                base_url_f5=base_url_f5,
                base_url_indextts=base_url_indextts,
                master_audio=master_audio,
                master_text=master_text,
                master_style=master_style,
                params=params,
            )

            # ── Step 3: split batch WAV into per-line WAVs ──
            split_paths = _split_wav_by_silence(
                wav_path=batch_path,
                expected_count=len(batch_lines),
                output_dir=output_dir,
                stem=f"{batch_idx:03d}",
                line_texts=batch_lines,
            )

            # ── Step 4: rename split files to final per-line names ──
            # The batch encompassed line_indices; each split file maps to
            # one original line.
            for offset, line_idx in enumerate(line_indices):
                # Rename to match the original {{idx:03d}}.wav pattern
                final_name = f"{line_idx:03d}.wav"
                final_path = output_dir / final_name

                if offset < len(split_paths):
                    split_paths[offset].rename(final_path)
                else:
                    # More lines than splits — produce a minimal silent WAV
                    _write_wav(final_path, np.zeros((1,), dtype=np.float32), 24000)

                segment_paths.append(final_path)

                try:
                    info = sf.info(str(final_path))
                    duration = round(info.duration, 3)
                    sample_rate = info.samplerate
                except Exception:
                    duration = 0.0
                    sample_rate = 0

                seg_entry = {
                    "index": line_idx,
                    "text": lines[line_idx],
                    "inference_text": _tts_text(lines[line_idx]),
                    "file": final_name,
                    "duration": duration,
                }
                manifest_segments.append(seg_entry)

                completed += 1
                if progress_callback:
                    progress_callback(completed, len(lines), lines[line_idx], {**seg_entry})

            # Clean up batch WAV
            batch_path.unlink(missing_ok=True)

        manifest: dict[str, Any] = {
            "voice_id": voice_id,
            "backend": backend,
            "sample_rate": manifest_segments[0].get("sample_rate", 24000) if manifest_segments else 24000,
            "segment_count": len(manifest_segments),
            "segments": manifest_segments,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return manifest
    except Exception:
        for seg_path in segment_paths:
            seg_path.unlink(missing_ok=True)
        (output_dir / "manifest.json").unlink(missing_ok=True)
        raise


def _synthesize_single(
    text: str,
    output_path: Path,
    backend: Literal["fish", "f5", "indextts", "auto"],
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
) -> Path:
    errors: list[str] = []

    # Extract FFmpeg params
    speed = params.get("speed", 1.0) if params else 1.0
    pitch = params.get("pitch", 0) if params else 0
    volume = params.get("volume", 1.0) if params else 1.0

    # Extract timbre params
    bass_gain = params.get("bass_gain", 0) if params else 0
    presence_gain = params.get("presence_gain", 0) if params else 0
    air_gain = params.get("air_gain", 0) if params else 0

    # Extract engine params (fish backend)
    temperature = params.get("temperature") if params else None
    top_p = params.get("top_p") if params else None
    repetition_penalty = params.get("repetition_penalty") if params else None
    seed = params.get("seed") if params else None

    # Resolve master_audio/master_text for IndexTTS2 (fallback to reference)
    indextts_master_audio = master_audio or reference_audio
    indextts_master_text = master_text or reference_text or ""

    if backend in ("auto", "fish"):
        try:
            result = fish_speech_tts(
                text=text,
                output_path=output_path,
                base_url=base_url_fish,
                reference_audio=reference_audio,
                reference_text=reference_text,
                temperature=temperature,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                seed=seed,
            )
            return apply_ffmpeg_params(result, speed=speed, pitch=pitch, volume=volume,
                bass_gain=bass_gain, presence_gain=presence_gain, air_gain=air_gain)
        except Exception as exc:
            errors.append(f"fish: {exc}")
            if backend == "fish":
                raise

    if backend in ("auto", "f5"):
        try:
            result = f5_tts(
                text=text,
                output_path=output_path,
                base_url=base_url_f5,
                ref_audio=reference_audio,
                ref_text=reference_text,
            )
            return apply_ffmpeg_params(result, speed=speed, pitch=pitch, volume=volume,
                bass_gain=bass_gain, presence_gain=presence_gain, air_gain=air_gain)
        except Exception as exc:
            errors.append(f"f5: {exc}")
            if backend == "f5":
                raise

    if backend == "indextts":
        try:
            # IndexTTS2-specific engine params
            do_sample = params.get("do_sample", True) if params else True
            indextts_top_p = params.get("top_p", 0.8) if params else 0.8
            indextts_top_k = params.get("top_k", 30) if params else 30
            indextts_temperature = params.get("temperature", 0.8) if params else 0.8
            indextts_max_text_tokens = (
                params.get("max_text_tokens_per_segment", 120) if params else 120
            )

            result = indextts_tts(
                text=text,
                output_path=output_path,
                base_url=base_url_indextts,
                master_audio=indextts_master_audio,
                master_text=indextts_master_text,
                master_style=master_style,
                do_sample=do_sample,
                top_p=indextts_top_p,
                top_k=indextts_top_k,
                temperature=indextts_temperature,
                max_text_tokens_per_segment=indextts_max_text_tokens,
                seed=seed,
            )
            return apply_ffmpeg_params(result, speed=speed, pitch=pitch, volume=volume,
                bass_gain=bass_gain, presence_gain=presence_gain, air_gain=air_gain)
        except Exception as exc:
            errors.append(f"indextts: {exc}")
            raise

    raise RuntimeError("All TTS backends failed:\n" + "\n".join(errors))


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="TTS client for digital human anchor")
    parser.add_argument(
        "--text",
        required=True,
        help="Text to synthesize. If prefixed with '@', read from UTF-8 file path.",
    )
    parser.add_argument("--output", "-o", help="Output WAV path")
    parser.add_argument("--backend", choices=["fish", "f5", "auto"], default="auto")
    parser.add_argument("--voice-id", default="default")
    parser.add_argument("--ref-audio", type=Path, help="Reference audio for voice cloning")
    parser.add_argument("--ref-text", default="", help="Reference text for voice cloning")
    parser.add_argument("--base-url-fish", default=DEFAULT_FISH_URL)
    parser.add_argument("--base-url-f5", default=DEFAULT_F5_URL)
    parser.add_argument("--segment", action="store_true", help="Split long text into short segments and concatenate audio")
    parser.add_argument("--segment-max-chars", type=int, default=120, help="Max chars per segment when --segment")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory: generate one WAV per non-empty line + manifest.json",
    )
    args = parser.parse_args()

    output = Path(args.output) if args.output else None
    text = args.text
    if text.startswith("@"):
        # Strip surrounding quotes that Windows/bash may leave on the path.
        text_file = text[1:].strip('"').strip("'")
        text = Path(text_file).read_text(encoding="utf-8")
    try:
        if args.output_dir:
            manifest = synthesize_lines(
                text=text,
                output_dir=Path(args.output_dir),
                backend=args.backend,
                voice_id=args.voice_id,
                reference_audio=args.ref_audio,
                reference_text=args.ref_text,
                base_url_fish=args.base_url_fish,
                base_url_f5=args.base_url_f5,
            )
            print(Path(args.output_dir) / "manifest.json")
            return 0

        path = synthesize(
            text=text,
            output_path=output,
            backend=args.backend,
            voice_id=args.voice_id,
            reference_audio=args.ref_audio,
            reference_text=args.ref_text,
            base_url_fish=args.base_url_fish,
            base_url_f5=args.base_url_f5,
            segment=args.segment,
            segment_max_chars=args.segment_max_chars,
        )
        print(path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

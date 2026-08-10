"""TTS 音频/FFmpeg 工具: 拼接 / 参数滤波 (WAV 拼接、EQ 滤波).

注意: 与 app/infrastructure/ffmpeg.py 职责不同 — 后者是集中式的
ffmpeg 命令封装; 本模块是 TTS 特有的音频后处理, 不依赖其它子系统。
按静音切分见 silence_split.py (audio → silence_split 单向依赖)。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .silence_split import _split_wav_by_silence, _write_wav

__all__ = [
    "_ensure_dir",
    "_concat_wavs_with_ffmpeg",
    "apply_ffmpeg_params",
    "_split_wav_by_silence",
    "_write_wav",
]


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
    """Apply speed/pitch/volume/timbre via FFmpeg filters; returns (possibly replaced) wav_path."""
    filters = _build_audio_filters(speed, pitch, volume, bass_gain, presence_gain, air_gain)
    if not filters:
        return wav_path

    filter_str = ",".join(filters)
    tmp = Path(tempfile.mktemp(suffix=".wav"))

    try:
        cmd = [
            "ffmpeg", "-y",
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


def _build_audio_filters(
    speed: float, pitch: float, volume: float,
    bass_gain: float, presence_gain: float, air_gain: float,
) -> list[str]:
    """Build ffmpeg filter graph for speed/pitch/volume/timbre (all-default → empty)."""
    filters: list[str] = []

    # Volume (applied first)
    if abs(volume - 1.0) > 0.01:
        filters.append(f"volume={volume}")

    # Pitch via rubberband — preserves vocal formants; expects a FREQUENCY
    # RATIO = 2^(semitones/12): +3 → 1.189, -3 → 0.841
    if pitch != 0:
        pitch_ratio = 2 ** (pitch / 12.0)
        filters.append(f"rubberband=pitch={pitch_ratio}:tempo=1.0")

    # Speed via atempo (pitch handled above)
    if abs(speed - 1.0) > 0.01:
        filters.append(f"atempo={speed}")

    # Timbre / EQ: bass low-shelf ~200Hz, presence peak ~2kHz, air high-shelf ~6kHz
    if abs(bass_gain) > 0.5:
        filters.append(f"lowshelf=f=200:width_type=o:width=0.7:g={bass_gain}")
    if abs(presence_gain) > 0.5:
        filters.append(f"equalizer=f=2000:width_type=o:width=1.0:g={presence_gain}")
    if abs(air_gain) > 0.5:
        filters.append(f"highshelf=f=6000:width_type=o:width=0.7:g={air_gain}")

    return filters

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


def _concat_wavs_with_fade(
    wav_paths: list[Path],
    output_path: Path,
    gap_sec: float = 0.25,
    fade_out_sec: float = 0.15,
    fade_in_sec: float = 0.06,
) -> Path:
    """拼接 WAV 段落: 每段尾淡出 + 段间静音 + 段首淡入.

    2026-08-13: 直接 concat (-c copy) 时, 段尾音与下段起音紧贴 → 拼接处"噗"破音.
    concat_8_9_fixed 验证: 尾淡出0.15 + 段间0.25s静音 + 首淡入0.06 → 破音消失.
    用于段落级拼接 (emotion 段/full_paragraph), 消除段间破音.
    """
    if not wav_paths:
        raise ValueError("No WAV files to concatenate")
    if len(wav_paths) == 1:
        shutil.copy2(wav_paths[0], output_path)
        return output_path
    inputs: list[str] = []
    for p in wav_paths:
        inputs += ["-i", str(p)]
    fc_parts = []
    for i in range(len(wav_paths)):
        filters: list[str] = []
        if i > 0:  # 非首段: 段首淡入
            filters.append(f"afade=t=in:d={fade_in_sec:.2f}")
        if i < len(wav_paths) - 1:  # 非末段: 段尾淡出 + 补静音
            # 2026-08-13: afade out 必须指定 st (默认 st=0 → 整段淡出成静音!)
            dur = _ffprobe_duration(wav_paths[i]) or 3.0
            st = max(0.0, dur - fade_out_sec)
            filters.append(f"afade=t=out:st={st:.3f}:d={fade_out_sec:.2f}")
            filters.append(f"apad=pad_dur={gap_sec:.2f}")
        fc_parts.append(f"[{i}:a]{','.join(filters)}[a{i}]")
    fc_parts.append(
        "".join(f"[a{i}]" for i in range(len(wav_paths)))
        + f"concat=n={len(wav_paths)}:v=0:a=1[out]"
    )
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc_parts), "-map", "[out]", str(output_path)]
    subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=True)
    return output_path


def _ffprobe_duration(wav_path: Path) -> float | None:
    """ffprobe 音频时长 (秒); 失败返回 None."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(wav_path)],
            capture_output=True, text=True, errors="replace", timeout=15,
        )
        return float(r.stdout.strip()) if r.stdout.strip() else None
    except Exception:
        return None


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
        subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=True)
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
        subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=True)
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

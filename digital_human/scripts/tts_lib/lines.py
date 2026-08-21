"""逐行合成: 批量 TTS + 静音切分回逐行 WAV + manifest 输出.

- synthesize_lines(): 每行一个 WAV, 按 ~300 字合并为 batch 一次 TTS, 再按
  静音切分回逐行文件, 写 manifest.json。
- 断点续传: 已存在非空 *_wav 跳过整批; 失败保留已有 WAV + 部分 manifest,
  仅清理进行中的 _batch_*.wav。

行为与旧 tts_client.py 逐字一致 (连接符/命名/manifest/异常消息全不变)。
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import soundfile as sf

from .audio import _ensure_dir, _split_wav_by_silence, _write_wav
from .constants import DEFAULT_F5_URL, DEFAULT_FISH_URL, DEFAULT_INDEXTTS_URL
from .orchestrator import Backend, _synthesize_single
from .text import _merge_lines_for_batch, _sanitize_for_fish, _tts_text

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str, dict[str, Any] | None], None]

__all__ = ["synthesize_lines"]


@dataclass(frozen=True)
class _SynthesisParams:
    """Immutable bundle of TTS params forwarded to _synthesize_single."""
    backend: Backend
    voice_id: str
    reference_audio: Path | None
    reference_text: str
    base_url_fish: str
    base_url_f5: str
    base_url_indextts: str
    master_audio: Path | None
    master_text: str
    master_style: str
    params: dict[str, Any] | None


def synthesize_lines(
    text: str,
    output_dir: Path,
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
    progress_callback: ProgressCallback | None = None,
    params: dict[str, Any] | None = None,
    batch_max_chars: int = 300,
    emotion_segments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate one WAV per non-empty line; writes manifest.json into output_dir.

    emotion_segments (2026-08-13, P5): 已解析的段落情绪参数
        [{"text": 段文本, "vector": 8维列表, "alpha": float}]. 提供时按段分组合成,
        段内行合并为 batch, 每批带该段情绪参数; 缺省走现状 (整篇 master_style=calm).
    """
    _ensure_dir(output_dir)
    syn = _SynthesisParams(
        backend=backend, voice_id=voice_id, reference_audio=reference_audio,
        reference_text=reference_text, base_url_fish=base_url_fish,
        base_url_f5=base_url_f5, base_url_indextts=base_url_indextts,
        master_audio=master_audio, master_text=master_text,
        master_style=master_style, params=params,
    )
    lines = _split_line_indices(text)
    if emotion_segments:
        batch_groups, batch_emos = _group_by_emotion_segments(
            lines, emotion_segments, max_chars=batch_max_chars,
        )
    else:
        batch_groups = _merge_lines_for_batch(lines, max_chars=batch_max_chars)
        batch_emos = None
    segment_paths, manifest_segments, _ = _process_batches(
        output_dir, lines, batch_groups, syn, progress_callback, batch_emos=batch_emos,
    )
    # 2026-08-21: 响度归一 (TTS 源 mean≈-39dB 偏轻) → loudnorm, 覆盖所有调用路径
    # (tts_service / 错别字替换 / CLI / e2e). app 不可用(独立 CLI)时跳过.
    try:
        from app.infrastructure.ffmpeg import normalize_audio
    except Exception:
        normalize_audio = None
    if normalize_audio is not None:
        for p in segment_paths:
            try:
                w = Path(p)
                tmp = w.with_suffix(".norm.wav")
                normalize_audio(w, tmp)
                tmp.replace(w)
            except Exception:
                pass  # 单段归一失败不阻断产线
    return _finalize_manifest(output_dir, voice_id, backend, manifest_segments)


def _group_by_emotion_segments(
    lines: list[str],
    emotion_segments: list[dict[str, Any]],
    max_chars: int = 300,
) -> tuple[list[list[int]], list[dict[str, Any] | None]]:
    """按 P5 段落分组行: 段内行合并为 batch (≤max_chars), 每批带该段情绪参数.

    行→段顺序匹配 (_map_lines_to_segments); 匹配失败的行落 calm (vector=None).
    Returns: (batch_groups, batch_emos) — batch_emos 与 batch_groups 等长.
    """
    line_emos = _map_lines_to_segments(lines, emotion_segments)
    batch_groups: list[list[int]] = []
    batch_emos: list[dict[str, Any] | None] = []
    current: list[int] = []
    current_emo: dict[str, Any] | None = None
    current_chars = 0
    for idx, emo in enumerate(line_emos):
        line = lines[idx]
        if current and (emo != current_emo or current_chars + len(line) > max_chars):
            batch_groups.append(current)
            batch_emos.append(current_emo)
            current = []
            current_chars = 0
        current.append(idx)
        current_chars += len(line)
        current_emo = emo
    if current:
        batch_groups.append(current)
        batch_emos.append(current_emo)
    return batch_groups, batch_emos


def _map_lines_to_segments(
    lines: list[str],
    emotion_segments: list[dict[str, Any]],
) -> list[dict[str, Any] | None]:
    """顺序匹配行到 P5 段: 累积行文本, 段文本被消费后前进到下一段.

    容错: 段文本匹配不上 → 该行落 calm (None). 纯字符串逻辑, 不感知段边界.
    """
    import re

    def _norm(s: str) -> str:
        return re.sub(r"\s+", "", s or "")

    anno = [dict(s, _n=_norm(s.get("text"))) for s in emotion_segments]
    result: list[dict[str, Any] | None] = []
    acc = ""
    ai = 0
    for line in lines:
        acc += _norm(line)
        cur = ai  # 匹配前段号: 本行归属匹配发生时所在段
        # 当前段文本已被累积文本消费 → 前进到下一段 (重置累积, 简单容错)
        while ai < len(anno) and anno[ai]["_n"] and anno[ai]["_n"] in acc:
            ai += 1
            acc = ""
        if cur < len(anno):
            result.append({"vector": anno[cur].get("vector"), "alpha": anno[cur].get("alpha", 1.0)})
        else:
            result.append(None)
    return result


def _process_batches(
    output_dir: Path, lines: list[str], batch_groups: list[list[int]],
    syn: _SynthesisParams, progress_callback: ProgressCallback | None,
    batch_emos: list[dict[str, Any] | None] | None = None,
) -> tuple[list[Path], list[dict[str, Any]], int]:
    """Loop batches, skipping on-disk ones; returns paths, manifest, completed."""
    segment_paths: list[Path] = []
    manifest_segments: list[dict[str, Any]] = []
    completed = 0
    try:
        for batch_idx, line_indices in enumerate(batch_groups):
            batch_lines = [lines[i] for i in line_indices]
            # Resume: only skip a whole batch — split_by_silence maps batch audio
            # → lines by position, so a batch must be rebuilt entirely.
            existing_paths = [output_dir / f"{i:03d}.wav" for i in line_indices]
            if all(p.is_file() and p.stat().st_size > 0 for p in existing_paths):
                completed = _skip_batch(
                    output_dir, lines, line_indices, existing_paths, batch_idx,
                    completed, progress_callback, segment_paths, manifest_segments,
                )
                continue
            emo = batch_emos[batch_idx] if batch_emos else None
            completed = _run_batch(
                output_dir, batch_idx, batch_lines, lines, line_indices, completed,
                syn, progress_callback, segment_paths, manifest_segments,
                emo_vector=emo["vector"] if emo else None,
                emo_alpha=emo["alpha"] if emo else 1.0,
            )
    except Exception:
        _cleanup_failed_batches(output_dir, completed, len(lines), len(segment_paths))
        raise
    return segment_paths, manifest_segments, completed


def _split_line_indices(text: str) -> list[str]:
    """Normalize input text into cleaned, non-empty lines."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [_sanitize_for_fish(line) for line in lines if line.strip()]
    if not lines:
        raise ValueError("No non-empty lines to synthesize")
    return lines


def _skip_batch(
    output_dir: Path, lines: list[str], line_indices: list[int],
    existing_paths: list[Path], batch_idx: int, completed: int,
    progress_callback: ProgressCallback | None,
    segment_paths: list[Path], manifest_segments: list[dict[str, Any]],
) -> int:
    """Resume path: reuse on-disk per-line WAVs and record manifest entries."""
    for offset, line_idx in enumerate(line_indices):
        final_path = existing_paths[offset]
        seg_entry = _build_segment_entry(final_path, line_idx, lines[line_idx])
        manifest_segments.append(seg_entry)
        segment_paths.append(final_path)
        completed += 1
        if progress_callback:
            progress_callback(completed, len(lines), lines[line_idx], {**seg_entry})
    logger.info(
        "synthesize_lines: skipped batch %d (%d line%s already on disk)",
        batch_idx, len(line_indices), "" if len(line_indices) == 1 else "s",
    )
    return completed


def _run_batch(
    output_dir: Path, batch_idx: int, batch_lines: list[str],
    lines: list[str], line_indices: list[int], completed: int,
    syn: _SynthesisParams, progress_callback: ProgressCallback | None,
    segment_paths: list[Path], manifest_segments: list[dict[str, Any]],
    emo_vector: list[float] | None = None, emo_alpha: float = 1.0,
) -> int:
    """Synthesize one batch, split to per-line WAVs, record manifest entries."""
    # "||" gets replaced with "，" in _tts_text(), creating a natural pause.
    batch_text = "||".join(batch_lines)
    inference_text = _tts_text(batch_text, keep_breaks=(syn.backend == "indextts"))
    batch_path = output_dir / f"_batch_{batch_idx:03d}.wav"
    _synth_single(syn, inference_text, batch_path,
                  emo_vector=emo_vector, emo_alpha=emo_alpha)

    split_paths = _split_wav_by_silence(
        wav_path=batch_path, expected_count=len(batch_lines),
        output_dir=output_dir, stem=f"{batch_idx:03d}", line_texts=batch_lines,
    )
    for offset, line_idx in enumerate(line_indices):
        final_path = _rename_to_final(split_paths, offset, line_idx, output_dir)
        segment_paths.append(final_path)
        seg_entry = _build_segment_entry(final_path, line_idx, lines[line_idx])
        manifest_segments.append(seg_entry)
        completed += 1
        if progress_callback:
            progress_callback(completed, len(lines), lines[line_idx], {**seg_entry})

    batch_path.unlink(missing_ok=True)
    return completed


def _synth_single(syn: _SynthesisParams, text: str, output_path: Path,
                  emo_vector: list[float] | None = None, emo_alpha: float = 1.0) -> Path:
    """Forward one synthesis call with the bundled parameters."""
    return _synthesize_single(
        text=text, output_path=output_path, backend=syn.backend,
        voice_id=syn.voice_id, reference_audio=syn.reference_audio,
        reference_text=syn.reference_text, base_url_fish=syn.base_url_fish,
        base_url_f5=syn.base_url_f5, base_url_indextts=syn.base_url_indextts,
        master_audio=syn.master_audio, master_text=syn.master_text,
        master_style=syn.master_style, params=syn.params,
        emo_vector=emo_vector, emo_alpha=emo_alpha,
    )


def _rename_to_final(
    split_paths: list[Path], offset: int, line_idx: int, output_dir: Path,
) -> Path:
    """Rename a split file to {{line_idx:03d}}.wav; pad with silence when missing."""
    final_path = output_dir / f"{line_idx:03d}.wav"
    # 目标已存在时先删 (重跑生成音频时旧 wav 残留, Windows rename 目标存在抛 WinError 183)
    if final_path.exists():
        final_path.unlink(missing_ok=True)
    if offset < len(split_paths):
        split_paths[offset].rename(final_path)
    else:
        _write_wav(final_path, np.zeros((1,), dtype=np.float32), 24000)
    return final_path


def _build_segment_entry(final_path: Path, line_idx: int, text: str) -> dict[str, Any]:
    """Build one manifest segment entry from a per-line WAV file."""
    try:
        info = sf.info(str(final_path))
        duration = round(info.duration, 3)
        sample_rate = info.samplerate
    except Exception:
        duration = 0.0
        sample_rate = 0
    return {
        "index": line_idx,
        "text": text,
        "inference_text": _tts_text(text),
        "file": final_path.name,
        "duration": duration,
        "sample_rate": sample_rate,
    }


def _finalize_manifest(
    output_dir: Path, voice_id: str, backend: str,
    manifest_segments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Write manifest.json into output_dir and return the manifest dict."""
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


def _cleanup_failed_batches(
    output_dir: Path, completed: int, total_lines: int, kept_segments: int,
) -> None:
    """Failure path: keep on-disk WAVs + partial manifest; remove in-progress batches."""
    logger.warning(
        "synthesize_lines failed after %d/%d segments; keeping %d wav file(s) "
        "and partial manifest for resumable retry",
        completed, total_lines, kept_segments,
    )
    for batch_path in output_dir.glob("_batch_*.wav"):
        try:
            batch_path.unlink(missing_ok=True)
        except OSError:
            pass

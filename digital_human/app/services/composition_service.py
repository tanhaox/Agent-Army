"""Composition service — assemble completed DirectorSlot clips into final 9:16 video.

Steps:
1. Collect all completed slots, sorted by slot_index.
2. Concatenate video streams (no crossfade, concat demuxer copy).
3. Mix master TTS audio + optional loudness normalization to -14 LUFS.
4. Validate output with ffprobe and write manifest.
5. Clean up intermediate files (normalized_*.mp4, concat_raw, with_audio, normalized.mp4).
(字幕体系已砍掉 2026-08-01 — 不再烧录 ASS 字幕)
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import DirectorJob, DirectorSlot
from app.services.video_validator import ffprobe_metadata

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _job_root(job: DirectorJob) -> Path:
    cfg = get_config().defaults
    return Path(cfg.composition_output_root) / job.id


def _ensure_root(job: DirectorJob) -> Path:
    root = _job_root(job)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cleanup_intermediates(root: Path, keep_intermediates: bool = False) -> int:
    """Delete intermediate build artifacts, keep only final output + manifest.

    Intermediate files:
        normalized_*.mp4  — re-encoded slot clips
        concat_list.txt   — concat demuxer file list
        concat_raw.mp4    — raw concatenated video
        with_audio.mp4    — mixed audio before loudnorm
        normalized.mp4    — loudnorm output (copy source for final)

    Retained:
        director_*.mp4   — final output
        composition_manifest.json — metadata

    Returns bytes freed (approximate, 0 if keep_intermediates).
    """
    if keep_intermediates:
        return 0

    patterns = [
        "concat_list.txt",
        "concat_raw.mp4",
        "with_audio.mp4",
        "normalized.mp4",
    ]
    freed = 0
    for pat in patterns:
        for f in sorted(root.glob(pat)):
            try:
                st = f.stat()
                f.unlink()
                freed += st.st_size
                logger.debug("[cleanup] deleted %s (%d bytes)", f.name, st.st_size)
            except OSError as exc:
                logger.warning("[cleanup] failed to delete %s: %s", f.name, exc)
    if freed:
        logger.info("[cleanup] freed %.1f MB from %s", freed / (1024 * 1024), root.name)
    return freed


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg and raise RuntimeError on failure."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not on PATH")
    r = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600, check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[:500]}")


def _concat_demuxer_concat(
    root: Path,
    clips: list[Path],
    crossfade_sec: float = 0.2,  # noqa: ARG001 — 已弃用: 本机 ffmpeg fade 滤镜在多段上压黑,详见下
) -> Path:
    """Concatenate clips using ffmpeg concat demuxer (no crossfade).

    修复 2026-07-31 黑屏 bug 的最终定案: 彻底去掉 fade 滤镜.
    实证 (digital_human/scripts/diag_*_tmp.py):
      1) 旧写法 fade=t=out:st=0:d=0.2:alpha=0,fade=t=in:st=0:d=0.2 在时间0压黑全片
      2) 本机 ffmpeg 的 fade=t=out 不带 alpha=1 会把画面叠成黑底 (亮度0.0)
      3) fade=t=in 带 st>0 会把该 fade 之前的所有帧压黑 → 逐段淡入淡出在多段
         concat 上只剩最后一段可见
    crossfade_sec 参数保留仅为兼容调用方,不再生效 (0.2s 的 MVP 点缀不值得为
    它承担黑屏风险).
    """
    list_path = root / "concat_list.txt"
    lines = [f"file '{p.resolve().as_posix()}'" for p in clips]
    list_path.write_text("\n".join(lines), encoding="utf-8")

    concat_path = root / "concat_raw.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(concat_path),
    ]
    _run_ffmpeg(cmd)
    return concat_path


# ---------------------------------------------------------------------------
# Subtitle handling — 字幕体系已砍掉 (2026-08-01): 合成不再烧录 ASS 字幕。
# 原 _clean_subtitle_text / _split_subtitle / _write_ass_subtitles /
# _sec_to_ass / _burn_subtitles 已全部移除。
# ---------------------------------------------------------------------------

def _has_audio_stream(video_path: Path) -> bool:
    """Quick check whether *video_path* contains at least one audio stream."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=index", "-of", "csv=p=0",
             str(video_path)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30, check=False,
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _loudnorm(video_path: Path, out_path: Path, target_lufs: float = -14.0) -> None:
    """Two-pass loudnorm to target integrated LUFS."""
    # Pre-check: if there is no audio stream, just copy the video.
    if not _has_audio_stream(video_path):
        logger.warning("loudnorm skipped: input has no audio stream")
        os.replace(video_path, out_path)
        return

    # Pass 1: measure — must use -loglevel info so loudnorm JSON appears in stderr
    cmd1 = [
        "ffmpeg", "-y", "-loglevel", "info",
        "-i", str(video_path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    r = subprocess.run(
        cmd1, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600, check=False,
    )
    # Parse JSON from stderr tail (loudnorm writes JSON at AV_LOG_INFO)
    json_str = ""
    if r.stderr:
        lines = r.stderr.strip().splitlines()
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "{":
                json_str = "\n".join(lines[i:])
                break
    measured: dict[str, Any] = {}
    if json_str:
        try:
            measured = json.loads(json_str)
        except json.JSONDecodeError:
            measured = {}

    # Detect silence / inaudible audio (input_i == "-inf" or below -70 LUFS)
    input_i = measured.get("input_i", "-inf")
    try:
        if float(input_i) < -70:
            logger.warning("loudnorm: audio appears silent (input_i=%s), skipping normalization", input_i)
            os.replace(video_path, out_path)
            return
    except (ValueError, TypeError):
        pass

    if not measured:
        logger.warning("loudnorm pass 1 returned no JSON, copying audio without normalization")
        os.replace(video_path, out_path)
        return

    # Pass 2: apply
    filter_str = (
        f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:"
        f"measured_I={measured.get('input_i', -23.0)}:"
        f"measured_TP={measured.get('input_tp', -1.0)}:"
        f"measured_LRA={measured.get('input_lra', 1.0)}:"
        f"measured_thresh={measured.get('input_thresh', -30.0)}:"
        f"offset={measured.get('target_offset', 0.0)}"
    )
    cmd2 = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path),
        "-af", filter_str,
        "-c:v", "copy",
        str(out_path),
    ]
    _run_ffmpeg(cmd2)


# ---------------------------------------------------------------------------
# Master audio mixing
# ---------------------------------------------------------------------------

def _mix_master_audio(
    root: Path,
    video_path: Path,
    audio_path: Path,
    duration_sec: float,
    out_path: Path,
    *,
    slot_segments: list[tuple[float, float, bool]] | None = None,
) -> None:
    """Mix the master TTS audio into the concat video.

    If *slot_segments* is provided (list of ``(start, end, is_host)`` in
    timeline order), the function builds an audio track segment-by-segment:
    host segments → silence matching the slot duration (ComfyUI video
    already carries the synced audio); non-host segments → TTS audio
    trimmed from the master.  The resulting track is then amix-ed with the
    concat video.  This avoids the cumulative alignment drift that a
    single ``volume=enable='between(...)'`` mute approach would produce.
    """
    audio_ok = audio_path.exists()

    if not audio_ok:
        logger.warning("master audio %s missing, generating silence", audio_path)
        silence = root / "silence_fallback.wav"
        cmd_silence = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-t", f"{duration_sec:.3f}",
            "-c:a", "aac", "-b:a", "192k",
            str(silence),
        ]
        _run_ffmpeg(cmd_silence)
        audio_path = silence
        audio_ok = True  # fallback is usable

    if slot_segments:
        # Build per-segment audio: host=aevalsrc (silence), non-host=atrim (TTS)
        seg_filters: list[str] = []
        seg_labels: list[str] = []
        for i, (start, end, is_host) in enumerate(slot_segments):
            dur = end - start
            if is_host:
                seg_filters.append(
                    f"aevalsrc=0:duration={dur:.6f}:s=48000[s{i}]"
                )
            else:
                seg_filters.append(
                    f"[1:a]atrim={start:.6f}:duration={dur:.6f},asetpts=PTS-STARTPTS[s{i}]"
                )
            seg_labels.append(f"[s{i}]")

        concat_labels = "".join(seg_labels)
        filter_complex = (
            ";".join(seg_filters)
            + f";{concat_labels}concat=n={len(slot_segments)}:v=0:a=1[tts]"
            + f";[0:a][tts]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[outa]"
        )
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", filter_complex,
            "-map", "0:v:0", "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-t", f"{duration_sec:.3f}",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
    _run_ffmpeg(cmd)


def compose_director_job(
    db: Session,
    job_id: str,
    *,
    crossfade_sec: float = 0.2,
    target_lufs: float = -14.0,
    keep_intermediates: bool = False,
    evt: Any = None,
) -> dict[str, Any]:
    """Compose all completed slots of a DirectorJob into final 9:16 MP4.

    Args:
        keep_intermediates: If True, retain intermediate build files
            (normalized_*.mp4, concat_raw.mp4, etc.) for debugging.
            Default False — only final output + manifest are kept.
        evt: Optional callback ``evt(data: dict)`` for SSE progress events.

    Returns:
        {"ok": bool, "output_path": str|None, "duration_sec": float|None,
         "error": str|None, "manifest_path": str|None}
    """
    job = db.get(DirectorJob, job_id)
    if job is None:
        return {"ok": False, "error": f"DirectorJob {job_id} not found"}

    # ── 幂等重入保护 (2026-08-07) ──────────────────────────────────────
    # 首次合成成功后, slots/ 目录会被自清理 (shutil.rmtree)。若同一 job 再次
    # 触发 compose, 所有 slot 输出已不存在 → 必然 "slot N output missing"。
    # 这里在 job 已 completed 且成片存在时直接幂等返回, 不再重跑。
    # 注意: job.completed_at 是时区感知 UTC, 不能与 naive 时间直接比较,
    #       因此只依据 status + 成片文件存在性判断。
    # 例外: 若自上次合成后有 slot 被重跑 (updated_at > 成片时间), 说明用户
    #       想重制素材后重新合成 → 不允许幂等跳过, 继续走真实合成路径。
    final_candidate = _job_root(job) / f"director_{job.id}.mp4"
    slots_changed_since_compose = False
    if job.status == "completed" and job.completed_at is not None:
        for sl in job.slots:
            if sl.updated_at is not None and sl.updated_at > job.completed_at:
                slots_changed_since_compose = True
                break
    if (
        job.status == "completed"
        and final_candidate.exists()
        and not slots_changed_since_compose
    ):
        logger.info(
            "[compose] job %s already completed with existing output, skip re-compose (idempotent)",
            job_id,
        )
        return {
            "ok": True,
            "output_path": str(final_candidate),
            "duration_sec": None,
            "manifest_path": str(_job_root(job) / "composition_manifest.json"),
            "error": None,
        }

    completed = [s for s in job.slots if s.status == "completed"]
    # Dedupe: one clip per slot_index — fallback chain creates new DirectorSlot
    # rows for the same slot_index. Pick the HIGHEST quality workflow first,
    # then by most-recent updated_at within the same quality tier.
    # Quality tiers (lower = better):
    #   0: host / mixed  (primary GPU-rendered content)
    #   1: broll_pexels / broll_local / hf_*  (secondary content)
    #   9: black_placeholder (fallback placeholder — 无字幕纯黑屏, 字幕体系已砍)
    _WF_TIER = {
        "host": 0, "mixed_host_broll": 0,
        "broll_pexels": 1, "broll_local": 1,
        "hf_chart": 1, "hf_title": 1,
        "black_placeholder": 9,
    }
    by_index: dict[int, Any] = {}
    for s in completed:
        cur = by_index.get(s.slot_index)
        s_tier = _WF_TIER.get(s.workflow, 5)
        if cur is None:
            by_index[s.slot_index] = s
        else:
            cur_tier = _WF_TIER.get(cur.workflow, 5)
            if s_tier < cur_tier:
                by_index[s.slot_index] = s  # better quality
            elif s_tier == cur_tier and s.updated_at and cur.updated_at and s.updated_at > cur.updated_at:
                by_index[s.slot_index] = s  # same tier, newer
    completed = sorted(by_index.values(), key=lambda s: s.slot_index)
    if not completed:
        return {"ok": False, "error": "no completed slots"}

    # SSE: report dedup result so user can see workflow distribution
    if evt:
        from collections import Counter
        wf_counts = Counter(s.workflow for s in completed)
        evt({"type": "compose_step", "step": "dedup",
             "msg": f"去重结果: {dict(wf_counts)}",
             "workflow_counts": dict(wf_counts)})

    if evt:
        evt({"type": "compose_start", "msg": f"开始合成 {len(completed)} 个片段"})

    # Detect time gaps / overlaps between slots
    issues: list[str] = []
    for i in range(1, len(completed)):
        prev_end = completed[i - 1].end_sec
        cur_start = completed[i].start_sec
        if abs(cur_start - prev_end) > 0.5:
            issues.append(f"gap between slot {i-1} and {i}: {cur_start - prev_end:.2f}s")

    root = _ensure_root(job)

    # Build per-segment timeline so _mix_master_audio can build the TTS track
    # segment-by-segment: host slots get silence (ComfyUI audio is already in
    # the concat video), non-host slots get atrim'd TTS audio.
    _HOST_WF = {"host", "mixed_host_broll"}
    slot_segments: list[tuple[float, float, bool]] = [
        (float(s.start_sec), float(s.end_sec), s.workflow in _HOST_WF)
        for s in completed
    ]
    logger.info("[compose] slot_segments=%s", slot_segments)

    try:
        # Step 1: Validate slot outputs exist + build metadata
        # (不再 re-encode — 各 workflow 已在源头输出统一分辨率/帧率/48kHz 音轨)
        slot_meta: list[dict[str, Any]] = []
        src_paths: list[Path] = []
        for i, slot in enumerate(completed):
            src = Path(slot.output_path) if slot.output_path else None
            if src is None or not src.exists():
                # ── 缺失 slot 输出自动补齐 (2026-08-07) ──────────────────────
                # 首轮合成成功后 slots/ 会被自清理 (shutil.rmtree)。若之后重跑
                # 部分 slot 再重新合成 (如【重试同类】), 其余 completed slot 的
                # 输出文件已删除 → 按 workflow 重新执行该 slot 补回素材。
                logger.warning(
                    "[compose] slot %d output missing: %s — re-execute workflow %s",
                    slot.slot_index, src, slot.workflow,
                )
                if evt:
                    evt({"type": "compose_step", "step": "repair",
                         "msg": f"补齐缺失片段 #{slot.slot_index} ({slot.workflow})…"})
                from ..services.slot_workflows import WORKFLOW_HANDLERS
                handler = WORKFLOW_HANDLERS.get(slot.workflow)
                if handler is None:
                    raise RuntimeError(
                        f"slot {slot.slot_index} output missing (no handler for {slot.workflow})"
                    )
                try:
                    if slot.workflow in ("hf_chart", "hf_title"):
                        new_out = handler(db, slot, slot.workflow)
                    else:
                        new_out = handler(db, slot)
                except Exception as exc:
                    raise RuntimeError(
                        f"slot {slot.slot_index} repair failed ({slot.workflow}): {exc}"
                    ) from exc
                if not new_out or not Path(new_out).exists():
                    raise RuntimeError(
                        f"slot {slot.slot_index} repaired output missing: {new_out}"
                    )
                slot.output_path = new_out
                db.commit()
                logger.info("[compose] slot %d repaired -> %s", slot.slot_index, new_out)
                src = Path(new_out)
            src_paths.append(src)
            slot_meta.append({
                "slot_index": slot.slot_index,
                "start_sec": slot.start_sec,
                "end_sec": slot.end_sec,
                "workflow": slot.workflow,
                "text_context": slot.text_context,
                "source_path": str(src),
            })
        if evt:
            evt({"type": "compose_step", "step": "validate", "msg": f"校验 {len(completed)} 个片段…"})

        # Step 2: Concat — -c copy (各 slot 已在源头输出统一格式)
        if evt:
            evt({"type": "compose_step", "step": "concat", "msg": "拼接视频…"})
        concat_video = _concat_demuxer_concat(root, src_paths, crossfade_sec=crossfade_sec)

        # Step 3: Mix master TTS audio
        master_audio: Path | None = None
        if job.audio_file and job.audio_file.file_path:
            master_audio = Path(job.audio_file.file_path)
        # Compute total video duration from slot timeline
        total_duration = completed[-1].end_sec if completed else 0.0
        logger.info("[compose] audio: path=%s exists=%s duration=%.1fs",
                    master_audio, master_audio.exists() if master_audio else False, total_duration)
        if evt:
            if master_audio and master_audio.exists():
                audio_msg = f"混入 TTS 主音轨 ({master_audio.name}, {total_duration:.0f}s)…"
            elif master_audio:
                audio_msg = f"TTS 音频文件缺失 ({master_audio.name})，生成静音…"
            else:
                audio_msg = "无 TTS 音频，生成静音…"
            evt({"type": "compose_step", "step": "audio", "msg": audio_msg})
        with_audio = root / "with_audio.mp4"
        _mix_master_audio(
            root, concat_video,
            master_audio or Path("__missing__"),
            total_duration, with_audio,
            slot_segments=slot_segments or None,
        )
        # Post-mix sanity: verify audio stream was embedded
        if not _has_audio_stream(with_audio):
            logger.warning("[compose] with_audio.mp4 has NO audio stream after mixing!")
            if evt:
                evt({"type": "compose_step", "step": "audio",
                     "msg": "⚠ 混音后无音频流，请检查音频文件"})

        # Step 4: Loudness normalization on the mixed audio.
        # 字幕体系已砍掉(2026-08-01): 不再烧录 ASS 字幕, 直接响度归一.
        if evt:
            evt({"type": "compose_step", "step": "loudnorm", "msg": "响度归一化…"})
        final_normalized = root / "normalized.mp4"
        _loudnorm(with_audio, final_normalized, target_lufs=target_lufs)

        # Step 5: Validate
        if evt:
            evt({"type": "compose_step", "step": "validate", "msg": "校验输出…"})

        probe = ffprobe_metadata(final_normalized)
        if not probe.get("available"):
            raise RuntimeError("ffprobe unavailable for final validation")
        if probe.get("error"):
            raise RuntimeError(f"ffprobe error: {probe['error']}")

        fmt = probe.get("format", {})
        duration_actual = float(fmt.get("duration", 0))

        final_name = f"director_{job.id}.mp4"
        final_path = root / final_name
        os.replace(final_normalized, final_path)

        manifest = {
            "schema_version": "1.0",
            "job_id": job_id,
            "status": "completed",
            "output_path": str(final_path),
            "duration_sec": duration_actual,
            "target_lufs": target_lufs,
            "crossfade_sec": crossfade_sec,
            "slots": slot_meta,
            "warnings": issues,
            "created_at": _now().isoformat(),
        }
        manifest_path = root / "composition_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        job.status = "completed"
        job.completed_at = _now()
        job.error_message = None  # 成功路径清掉历史失败残留
        db.commit()
        db.refresh(job)

        if evt:
            evt({"type": "compose_done", "msg": f"合成完成: {duration_actual:.1f}s",
                 "duration_sec": duration_actual, "output_path": str(final_path)})

        # Step 6: Clean up intermediate build artifacts
        freed_bytes = _cleanup_intermediates(root, keep_intermediates=keep_intermediates)
        if freed_bytes and evt:
            evt({"type": "compose_cleanup", "msg": f"清理中间文件释放 {freed_bytes / (1024*1024):.1f} MB"})

        # Step 7: Delete slots/ directory — slot outputs consumed by concat, no longer needed
        slots_dir = root / "slots"
        if slots_dir.exists():
            shutil.rmtree(slots_dir, ignore_errors=True)
            logger.info("[compose] removed slots dir: %s", slots_dir)

        return {
            "ok": True,
            "output_path": str(final_path),
            "duration_sec": duration_actual,
            "manifest_path": str(manifest_path),
            "error": None,
        }
    except Exception as exc:
        logger.exception("Composition failed for job %s", job_id)
        job.status = "failed"
        job.error_message = f"composition failed: {exc}"
        job.completed_at = _now()
        db.commit()
        if evt:
            evt({"type": "compose_error", "msg": f"合成失败: {exc}"})
        # 失败但旧成片仍在: 保留旧成片供用户继续使用/下载 (不覆盖磁盘文件)
        old_output = str(final_candidate) if final_candidate.exists() else None
        return {
            "ok": False,
            "error": str(exc),
            "output_path": old_output,
            "duration_sec": None,
        }

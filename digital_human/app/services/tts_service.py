"""TTS service wrapping tts_client for pipeline use."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

import soundfile as sf

# Ensure digital_human/ is on sys.path so that "from scripts import tts_client" works
# even when uvicorn loads app.main with digital_human/ as the working directory.
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts import tts_client
from ..config import DefaultsConfig
from ..models import AudioFile, AudioJob, Segment, Voice


class TTSService:
    def __init__(self, defaults: DefaultsConfig):
        self.defaults = defaults

    def generate(
        self,
        job: AudioJob,
        segments: list[Segment],
        voice: Voice | None,
        progress_callback: Callable[[int, int, str | None, AudioFile], None] | None = None,
        emotion_annotations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate per-line WAV files and manifest.

        Args:
            job: AudioJob ORM instance (status updated in-place but caller commits).
            segments: List of Segment instances to synthesize.
            voice: Voice configuration.
            progress_callback: Called with (completed, total, current_text, audio_file) after each line.
        """
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        backend = voice.backend if voice and voice.backend else self.defaults.backend
        voice_id = voice.name if voice else self.defaults.voice_id
        ref_audio = Path(voice.reference_audio_path) if voice and voice.reference_audio_path else None
        ref_text = voice.reference_text or "" if voice else ""
        master_audio = (
            Path(voice.master_audio_path)
            if voice and voice.master_audio_path
            else (Path(voice.reference_audio_path) if voice and voice.reference_audio_path else None)
        )
        master_text = (
            voice.master_text
            or (voice.reference_text or "")
            if voice
            else ""
        )
        base_url_fish = voice.base_url_fish or self.defaults.base_url_fish if voice else self.defaults.base_url_fish
        base_url_f5 = voice.base_url_f5 or self.defaults.base_url_f5 if voice else self.defaults.base_url_f5
        base_url_indextts = (
            voice.base_url_indextts or self.defaults.base_url_indextts
            if voice
            else self.defaults.base_url_indextts
        )

        # Read saved voice params from config_json
        voice_params: dict[str, Any] | None = None
        if voice and voice.config_json and isinstance(voice.config_json, dict):
            saved = voice.config_json.get("params")
            if saved and isinstance(saved, dict):
                voice_params = saved

        # Build text preserving line breaks and control chars.
        text = "\n".join(seg.text for seg in segments)

        # Collect the AudioFile rows created as synthesis progresses. Each
        # completed segment yields exactly one row (via _manifest_callback),
        # committed through progress_callback so DB and disk stay in sync even
        # if the job later fails.
        audio_files: list[AudioFile] = []

        def _manifest_callback(completed: int, total: int, text: str, manifest_seg: dict[str, Any] | None) -> None:
            if not progress_callback or not manifest_seg:
                return
            seg = segments[completed - 1]
            file_path = output_dir / manifest_seg["file"]
            audio_file = AudioFile(
                audio_job_id=job.id,
                segment_id=seg.id,
                filename=manifest_seg["file"],
                file_path=str(file_path),
                duration=manifest_seg.get("duration"),
                sample_rate=manifest_seg.get("sample_rate"),
            )
            audio_files.append(audio_file)
            progress_callback(completed, total, text, audio_file)

        # P5 情绪标注 (2026-08-13): 段落情绪 → 已解析段参数 (text/vector/alpha),
        # 传给 synthesize_lines 按段合成. 缺省 → 现状 (整篇 calm).
        emotion_segments: list[dict[str, Any]] | None = None
        # 2026-08-14: P5 产的 emotion_annotations 是 "[情绪/强度] 文本\n..." 字符串 (DB 存储),
        # TTS 需 list[dict]. 入口解析兼容 (str → list[dict]); 解析失败回退 None (整篇 calm).
        if emotion_annotations and isinstance(emotion_annotations, str):
            from .boost_service import _parse_emotion_annotations
            emotion_annotations = _parse_emotion_annotations(emotion_annotations)
        if emotion_annotations:
            from .emotion_dict import resolve_emotion

            emotion_segments = []
            for ann in emotion_annotations:
                try:
                    r = resolve_emotion(ann.get("emotion", "calm"), ann.get("strength", "中"))
                except KeyError:
                    continue
                emotion_segments.append({
                    "text": ann.get("text", ""),
                    "vector": r["vector"],
                    "alpha": r["alpha"],
                })

        manifest = tts_client.synthesize_lines(
            text=text,
            output_dir=output_dir,
            backend=backend,
            voice_id=voice_id,
            reference_audio=master_audio,
            reference_text=master_text,
            base_url_fish=base_url_fish,
            base_url_f5=base_url_f5,
            base_url_indextts=base_url_indextts,
            master_audio=master_audio,
            master_text=master_text,
            progress_callback=_manifest_callback,
            params=voice_params,
            batch_max_chars=150,
            emotion_segments=emotion_segments,
        )

        # ── Concatenate all segment WAVs into one paragraph-level file ──
        combined_path = output_dir / "full_paragraph.wav"
        existing_wavs = [af.file_path for af in audio_files if Path(af.file_path).exists()]
        if existing_wavs and len(existing_wavs) >= 1:
            # 段级响度归一已在 scripts/tts_lib/lines.synthesize_lines 内完成
            # (2026-08-21 loudnorm -16 LUFS), 此处直接拼接归一后段 wav.
            try:
                # 2026-08-13: 段落拼接用 fade(无静音gap), 消除段尾音+段首起音紧贴的破音("噗"),
                # 且停顿自然(用户验证 gap=0 最舒服).
                from scripts.tts_lib.audio import _concat_wavs_with_fade
                _concat_wavs_with_fade(
                    [Path(p) for p in existing_wavs], combined_path,
                    gap_sec=0.0, fade_out_sec=0.15, fade_in_sec=0.06,
                )
                try:
                    info = sf.info(str(combined_path))
                    combined_duration = info.duration
                    combined_sample_rate = info.samplerate
                except Exception:
                    combined_duration = sum(af.duration or 0 for af in audio_files)
                    combined_sample_rate = audio_files[0].sample_rate if audio_files else 24000
            except Exception:
                combined_path = None
                combined_duration = None
                combined_sample_rate = None
        else:
            combined_path = None
            combined_duration = None
            combined_sample_rate = None

        return {
            "manifest": manifest,
            "audio_files": audio_files,
            "output_dir": str(output_dir),
            "combined_file": {
                "file": "full_paragraph.wav",
                "file_path": str(combined_path) if combined_path else None,
                "duration": combined_duration,
                "sample_rate": combined_sample_rate,
            } if combined_path else None,
        }

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
        )

        # ── Concatenate all segment WAVs into one paragraph-level file ──
        combined_path = output_dir / "full_paragraph.wav"
        existing_wavs = [af.file_path for af in audio_files if Path(af.file_path).exists()]
        if existing_wavs and len(existing_wavs) >= 1:
            try:
                from scripts.tts_client import _concat_wavs_with_ffmpeg
                _concat_wavs_with_ffmpeg(
                    [Path(p) for p in existing_wavs], combined_path
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

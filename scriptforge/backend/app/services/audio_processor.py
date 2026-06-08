"""Audio preprocessing — vocal separation via Demucs, speaker diarization via pyannote.

Removes background music before ASR to boost transcription accuracy.
Falls back to the original audio on any failure.
"""

import gc
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import torch

logger = logging.getLogger(__name__)

# China-friendly HuggingFace mirror
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_WORKER_DIR = Path(__file__).resolve().parent


def separate_vocals(wav_path: str) -> str:
    """Separate vocals from audio using Demucs htdemucs model.

    Returns path to vocals-only WAV, or the original path on failure.
    Output is saved as ``{stem}_vocals.wav`` next to the input file.
    """
    src = Path(wav_path)
    if not src.exists():
        logger.warning("Audio file not found: %s", wav_path)
        return wav_path

    vocals_path = src.parent / f"{src.stem}_vocals.wav"
    if vocals_path.exists():
        logger.info("Vocals already exist: %s", vocals_path)
        return str(vocals_path)

    try:
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        from demucs.audio import AudioFile, save_audio
    except ImportError:
        logger.warning("Demucs not installed, skipping vocal separation")
        return wav_path

    try:
        logger.info("Loading htdemucs model on %s ...", _DEVICE)
        model = get_model("htdemucs")
        model.to(_DEVICE)
        model.eval()

        # Load audio
        af = AudioFile(str(src))
        wav = af.read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        ref = wav.mean(0)
        wav_input = (wav - ref.mean()) / ref.std()

        logger.info("Separating vocals (%.1fs audio on %s) ...",
                     wav.shape[-1] / model.samplerate, _DEVICE)

        with torch.no_grad():
            sources = apply_model(model, wav_input[None], device=_DEVICE, split=True, overlap=0.25)[0]

        sources = sources * ref.std() + ref.mean()

        # Find the vocals stem index
        vocal_idx = model.sources.index("vocals")
        vocals = sources[vocal_idx]

        # Save as 16-bit PCM WAV at model's native sample rate
        save_audio(vocals[None], str(vocals_path), model.samplerate,
                   as_float=False, bits_per_sample=16)

        logger.info("Vocal separation done: %s", vocals_path)

        # Release GPU memory immediately
        del model, wav, wav_input, sources, vocals
        gc.collect()
        if _DEVICE == "cuda":
            torch.cuda.empty_cache()

        return str(vocals_path)

    except Exception as e:
        logger.error("Vocal separation failed, using original audio: %s", e)
        gc.collect()
        if _DEVICE == "cuda":
            torch.cuda.empty_cache()
        return wav_path


# ── Speaker Diarization (subprocess isolation) ──


class SpeakerDiarizer:
    """Runs speaker diarization in an isolated subprocess.

    The worker script (diarization_worker.py) is called via subprocess
    to avoid polluting the main process's torch/ctranslate2 environment.

    Supports reference mode: when a voice profile exists for the anchor,
    uses cosine similarity matching instead of spectral clustering.
    """

    _PROFILE_DIR = Path(__file__).resolve().parent.parent.parent / "voice_profiles"

    def __init__(self):
        self.last_mode: str = ""  # "reference" or "clustering", set after diarize()

    def diarize(self, audio_path: str, anchor_name: str = "", persona_id: str | None = None) -> list[dict]:
        """Run speaker diarization on an audio file.

        If a voice profile exists (prefers persona_id, falls back to anchor_name),
        uses reference mode. Otherwise falls back to spectral clustering.
        """
        worker = _WORKER_DIR / "diarization_worker.py"
        if not worker.exists():
            logger.warning("Diarization worker not found: %s", worker)
            return []

        # Check for voice profile — prefer persona_id, then anchor_name
        reference_path = None
        if persona_id:
            candidate = self._PROFILE_DIR / f"{persona_id}.npy"
            if candidate.exists():
                reference_path = str(candidate)
                logger.info("Using voice profile (persona_id=%s): %s", persona_id, candidate)
        if not reference_path and anchor_name:
            safe_name = anchor_name.replace("/", "_").replace("\\", "_")
            candidate = self._PROFILE_DIR / f"{safe_name}.npy"
            if candidate.exists():
                reference_path = str(candidate)
                logger.info("Using voice profile (anchor='%s'): %s", anchor_name, candidate)

        try:
            cmd = [sys.executable, str(worker), audio_path]
            if reference_path:
                cmd.extend(["--reference", reference_path])

            proc = subprocess.run(
                cmd,
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=120,
            )
        except subprocess.TimeoutExpired:
            logger.warning("Diarization timed out (120s): %s", audio_path)
            return []
        except Exception as e:
            logger.warning("Diarization subprocess failed: %s", e)
            return []

        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            logger.warning("Diarization worker error: %s", stderr[:500])
            return []

        # Parse JSON output lines
        segments = []
        for line in proc.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if data.get("phase") == "done":
                segments = data.get("segments", [])
                self.last_mode = data.get("mode", "clustering")
                break
            elif data.get("error"):
                logger.warning("Diarization error: %s", data["error"])
                return []

        logger.info("Diarization returned %d segments", len(segments))
        return segments

    def map_speakers(self, segments: list[dict], reference_used: bool = False) -> dict[str, str]:
        """Map SPEAKER_XX labels to role names.

        In reference mode: SPEAKER_00 (matched) = "主播", SPEAKER_01 = "连线观众".
        In clustering mode: longest duration = "主播", others = "连线观众".
        """
        if not segments:
            return {}

        if reference_used:
            return {"SPEAKER_00": "主播", "SPEAKER_01": "连线观众"}

        durations: dict[str, float] = {}
        for seg in segments:
            spk = seg.get("speaker", "")
            dur = seg.get("end", 0) - seg.get("start", 0)
            durations[spk] = durations.get(spk, 0) + dur

        if not durations:
            return {}

        sorted_speakers = sorted(durations.items(), key=lambda x: x[1], reverse=True)
        mapping = {}
        for i, (spk, _) in enumerate(sorted_speakers):
            mapping[spk] = "主播" if i == 0 else "连线观众"

        return mapping

    def assign_speakers(
        self,
        diarization_segments: list[dict],
        asr_segments: list[dict],
        speaker_map: dict[str, str],
    ) -> list[dict]:
        """Assign speaker labels to ASR segments based on time overlap.

        For each ASR segment, finds the diarization segment with the most
        overlap and assigns the corresponding speaker label.
        """
        if not diarization_segments or not asr_segments or not speaker_map:
            return asr_segments

        result = []
        for seg in asr_segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_mid = (seg_start + seg_end) / 2

            # Find the diarization segment that contains the midpoint
            best_speaker = None
            for dseg in diarization_segments:
                d_start = dseg.get("start", 0)
                d_end = dseg.get("end", 0)
                if d_start <= seg_mid <= d_end:
                    best_speaker = dseg.get("speaker")
                    break

            # Fallback: find max overlap
            if best_speaker is None:
                max_overlap = 0
                for dseg in diarization_segments:
                    d_start = dseg.get("start", 0)
                    d_end = dseg.get("end", 0)
                    overlap = max(0, min(seg_end, d_end) - max(seg_start, d_start))
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_speaker = dseg.get("speaker")

            labeled = dict(seg)
            labeled["speaker"] = speaker_map.get(best_speaker, "主播") if best_speaker else "主播"
            result.append(labeled)

        return result

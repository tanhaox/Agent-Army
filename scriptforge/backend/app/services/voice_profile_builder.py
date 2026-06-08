"""Voice profile builder — extract and store anchor speaker embeddings.

Builds a reference voice profile from multiple audio files of the same anchor.
The profile is a 192-dim averaged embedding saved as .npy.
"""

import gc
import logging
import os
import sys
from pathlib import Path

import numpy as np
import torch

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

logger = logging.getLogger(__name__)

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_PROFILE_DIR = Path(__file__).resolve().parent.parent.parent / "voice_profiles"
_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

_SAMPLE_RATE = 16000
_WINDOW_SEC = 1.5
_SAMPLES_PER_AUDIO = 10  # number of windows to sample per audio file


def _load_classifier():
    from speechbrain.inference.speaker import EncoderClassifier

    return EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": _DEVICE},
    )


def _extract_embeddings_from_audio(classifier, audio_path: str, max_windows: int = _SAMPLES_PER_AUDIO) -> list[np.ndarray]:
    import torchaudio

    waveform, sr = torchaudio.load(audio_path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != _SAMPLE_RATE:
        waveform = torchaudio.transforms.Resample(sr, _SAMPLE_RATE)(waveform)
        sr = _SAMPLE_RATE

    total_samples = waveform.shape[1]
    window_samples = int(_WINDOW_SEC * sr)
    hop_samples = int(0.75 * sr)

    if total_samples < window_samples:
        return []

    # Evenly sample max_windows positions across the audio
    num_possible = (total_samples - window_samples) // hop_samples + 1
    if num_possible <= max_windows:
        positions = list(range(0, total_samples - window_samples + 1, hop_samples))
    else:
        step = (num_possible - 1) / max(max_windows - 1, 1)
        positions = [int(i * step) * hop_samples for i in range(max_windows)]

    embeddings = []
    for start in positions:
        end = start + window_samples
        if end > total_samples:
            break
        chunk = waveform[:, start:end]
        with torch.no_grad():
            emb = classifier.encode_batch(chunk)
        embeddings.append(emb.squeeze().cpu().numpy())

    return embeddings


def build_voice_profile(anchor_name: str, audio_paths: list[str], persona_id: str | None = None) -> dict:
    """Build a reference voice profile from multiple audio files.

    Saves as {persona_id}.npy when persona_id is provided, otherwise {anchor_name}.npy.
    Returns dict with stats: {"audio_count", "embedding_dim", "total_windows"}.
    """
    if not audio_paths:
        raise ValueError("No audio files provided")

    classifier = _load_classifier()
    all_embeddings = []
    valid_files = 0

    for path in audio_paths:
        if not Path(path).exists():
            logger.warning("Audio file not found, skipping: %s", path)
            continue
        try:
            embs = _extract_embeddings_from_audio(classifier, path)
            if embs:
                all_embeddings.extend(embs)
                valid_files += 1
        except Exception as e:
            logger.warning("Failed to extract embeddings from %s: %s", path, e)

    # Cleanup
    del classifier
    gc.collect()
    if _DEVICE == "cuda":
        torch.cuda.empty_cache()

    if not all_embeddings:
        raise RuntimeError("No valid embeddings extracted from any audio file")

    # Average all embeddings into one reference vector
    avg_embedding = np.mean(np.stack(all_embeddings), axis=0).astype(np.float32)

    # Normalize
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding /= norm

    # Save — prefer persona_id, fallback to anchor_name
    if persona_id:
        out_path = _PROFILE_DIR / f"{persona_id}.npy"
    else:
        safe_name = anchor_name.replace("/", "_").replace("\\", "_")
        out_path = _PROFILE_DIR / f"{safe_name}.npy"
    np.save(str(out_path), avg_embedding)

    logger.info(
        "Voice profile built for '%s': %d files, %d windows, dim=%d → %s",
        anchor_name, valid_files, len(all_embeddings), avg_embedding.shape[0], out_path,
    )

    return {
        "anchor_name": anchor_name,
        "persona_id": persona_id,
        "audio_count": valid_files,
        "total_windows": len(all_embeddings),
        "embedding_dim": int(avg_embedding.shape[0]),
        "profile_path": str(out_path),
    }


def load_voice_profile(anchor_name: str, persona_id: str | None = None) -> np.ndarray | None:
    """Load a voice profile. Prefers persona_id.npy over anchor_name.npy."""
    if persona_id:
        path = _PROFILE_DIR / f"{persona_id}.npy"
        if path.exists():
            return np.load(str(path))
    safe_name = anchor_name.replace("/", "_").replace("\\", "_")
    path = _PROFILE_DIR / f"{safe_name}.npy"
    if not path.exists():
        return None
    return np.load(str(path))


def list_voice_profiles() -> list[dict]:
    """List all available voice profiles."""
    result = []
    for p in sorted(_PROFILE_DIR.glob("*.npy")):
        emb = np.load(str(p))
        result.append({
            "anchor_name": p.stem,
            "embedding_dim": int(emb.shape[0]),
            "profile_path": str(p),
        })
    return result


def migrate_profiles_to_persona_id(persona_lookup: dict[str, str]) -> dict:
    """Rename voice profiles from anchor_name to persona_id.

    Args:
        persona_lookup: mapping of anchor_name -> persona_id.
            Names are sanitised (slashes replaced) before matching files.

    Returns:
        {"renamed": int, "skipped": int, "errors": list[str]}
    """
    renamed = 0
    skipped = 0
    errors = []

    for anchor_name, pid in persona_lookup.items():
        safe = anchor_name.replace("/", "_").replace("\\", "_")
        old = _PROFILE_DIR / f"{safe}.npy"
        new = _PROFILE_DIR / f"{pid}.npy"

        if not old.exists():
            skipped += 1
            continue
        if new.exists():
            logger.info("Skipping %s: target %s already exists", old.name, new.name)
            skipped += 1
            continue

        try:
            old.rename(new)
            renamed += 1
            logger.info("Migrated voice profile: %s -> %s", old.name, new.name)
        except Exception as e:
            errors.append(f"{old.name}: {e}")
            logger.warning("Failed to migrate %s: %s", old.name, e)

    return {"renamed": renamed, "skipped": skipped, "errors": errors}

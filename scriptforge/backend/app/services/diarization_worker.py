"""Speaker diarization worker — runs in an isolated subprocess.

Called via:
  python diarization_worker.py <audio_path> [--reference <npy_path>]

Outputs line-delimited JSON to stdout with speaker segments.

Supports two modes:
  1. Reference mode (--reference): cosine similarity against a known anchor profile
  2. Clustering mode (default): spectral clustering for unknown speakers

Uses speechbrain for speaker embedding.
No gated model or HF token required.
"""
import gc
import json
import logging
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("diarization_worker")
_logger.setLevel(logging.DEBUG)
from logging.handlers import TimedRotatingFileHandler
_handler = TimedRotatingFileHandler(
    _LOG_DIR / "scriptforge.log",
    when="midnight", interval=1, backupCount=7, encoding="utf-8",
)
_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
_logger.addHandler(_handler)


def _emit(data: dict):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def _cosine_similarity(a, b) -> float:
    """Compute cosine similarity between two vectors."""
    import numpy as _np
    dot = _np.dot(a, b)
    norm_a = _np.linalg.norm(a)
    norm_b = _np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def main():
    if len(sys.argv) < 2:
        _emit({"error": "Usage: diarization_worker.py <audio_path> [--reference <npy_path>]"})
        sys.exit(1)

    audio_path = sys.argv[1]

    # Parse --reference argument
    reference_path = None
    if "--reference" in sys.argv:
        idx = sys.argv.index("--reference")
        if idx + 1 < len(sys.argv):
            reference_path = sys.argv[idx + 1]

    mode = "reference" if reference_path else "clustering"
    _logger.info("Diarization worker started: %s (mode=%s)", audio_path, mode)

    if not Path(audio_path).exists():
        _emit({"error": f"File not found: {audio_path}"})
        sys.exit(1)

    _emit({"phase": "loading_model", "message": "正在加载说话人分离模型..."})

    try:
        import numpy as np
        import torch
        import torchaudio
        from sklearn.cluster import SpectralClustering
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _logger.info("Device: %s", device)

        # Load speechbrain speaker embedding model (open, no auth needed)
        from speechbrain.inference.speaker import EncoderClassifier
        _emit({"phase": "model_downloading", "message": "正在下载/加载说话人嵌入模型..."})

        classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": device},
        )

        _emit({"phase": "diarizing", "message": f"正在进行说话人分离 ({mode} mode)..."})
        start_time = time.monotonic()

        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Resample to 16kHz if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
            sample_rate = 16000

        # Split into windows (~1.5s with 0.75s hop)
        window_samples = int(1.5 * sample_rate)
        hop_samples = int(0.75 * sample_rate)
        total_samples = waveform.shape[1]

        embeddings = []
        timestamps = []

        for start in range(0, total_samples - window_samples, hop_samples):
            end = start + window_samples
            chunk = waveform[:, start:end]
            with torch.no_grad():
                emb = classifier.encode_batch(chunk)
            embeddings.append(emb.squeeze().cpu().numpy())
            timestamps.append({
                "start": round(start / sample_rate, 2),
                "end": round(end / sample_rate, 2),
            })

        if not embeddings:
            _emit({"error": "Audio too short for diarization"})
            sys.exit(1)

        X = np.stack(embeddings)

        if reference_path:
            # ── Reference mode: cosine similarity against anchor profile ──
            if not Path(reference_path).exists():
                _emit({"error": f"Reference profile not found: {reference_path}"})
                sys.exit(1)

            ref_emb = np.load(reference_path)
            _logger.info("Reference profile loaded: %s (dim=%d)", reference_path, ref_emb.shape[0])

            # Compute raw similarity scores
            raw_scores = [_cosine_similarity(emb, ref_emb) for emb in embeddings]

            # Smooth with moving average (window=3) to reduce jitter
            smoothed = []
            win_size = 3
            for i in range(len(raw_scores)):
                lo = max(0, i - win_size // 2)
                hi = min(len(raw_scores), i + win_size // 2 + 1)
                smoothed.append(sum(raw_scores[lo:hi]) / (hi - lo))

            # Dual threshold: high for confident match, low for extending nearby
            high_thresh = 0.52
            low_thresh = 0.42

            labels = [1] * len(smoothed)
            # First pass: high confidence matches
            for i, s in enumerate(smoothed):
                if s >= high_thresh:
                    labels[i] = 0

            # Second pass: extend anchor segments by one window in each direction
            # if the neighbor is above low_thresh
            changed = True
            while changed:
                changed = False
                for i in range(len(labels)):
                    if labels[i] == 0:
                        continue
                    # Check if any neighbor is anchor AND this window is above low_thresh
                    is_near_anchor = (
                        (i > 0 and labels[i - 1] == 0)
                        or (i < len(labels) - 1 and labels[i + 1] == 0)
                    )
                    if is_near_anchor and smoothed[i] >= low_thresh:
                        labels[i] = 0
                        changed = True

            _logger.info("Reference mode: high=%.2f low=%.2f, match=%d/%d",
                         high_thresh, low_thresh,
                         sum(1 for l in labels if l == 0), len(labels))
        else:
            # ── Clustering mode: spectral clustering ──
            clustering = SpectralClustering(
                n_clusters=2, affinity="nearest_neighbors", random_state=42,
            )
            labels = list(clustering.fit_predict(X))

        # Build contiguous speaker segments
        segments = []
        current_speaker = int(labels[0])
        seg_start = timestamps[0]["start"]

        for i in range(1, len(labels)):
            spk = int(labels[i])
            if spk != current_speaker:
                segments.append({
                    "start": round(seg_start, 2),
                    "end": timestamps[i]["start"],
                    "speaker": f"SPEAKER_{current_speaker:02d}",
                })
                current_speaker = spk
                seg_start = timestamps[i]["start"]

        # Last segment
        segments.append({
            "start": round(seg_start, 2),
            "end": timestamps[-1]["end"],
            "speaker": f"SPEAKER_{current_speaker:02d}",
        })

        elapsed = time.monotonic() - start_time
        _logger.info("Diarization done: %d segments, %.1fs elapsed", len(segments), elapsed)

        # Cleanup
        del classifier, waveform, embeddings, X
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

        _emit({
            "phase": "done",
            "segments": segments,
            "elapsed_seconds": round(elapsed, 1),
            "device": device,
            "mode": mode,
        })

    except Exception as e:
        _logger.error("Diarization failed: %s", e, exc_info=True)
        _emit({"error": str(e)})
        gc.collect()
        sys.exit(1)


if __name__ == "__main__":
    main()

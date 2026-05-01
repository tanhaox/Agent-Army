import logging
import os
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Use HuggingFace mirror for China network
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


@dataclass
class TranscriptionResult:
    text: str
    segments: list[dict]
    duration: float


class WhisperASR:
    def __init__(self, model_size: str = "large-v3", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: WhisperModel | None = None
        self._load_failed = False

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            if self._load_failed:
                raise RuntimeError("Whisper 模型不可用（加载失败或环境不兼容）")
            model_path = Path(settings.WHISPER_MODEL_PATH)
            if model_path.exists() and any(model_path.iterdir()):
                logger.info("Loading Whisper model from local path: %s", model_path)
                try:
                    self._model = WhisperModel(
                        str(model_path), device=self.device, compute_type=self.compute_type
                    )
                except Exception as e:
                    logger.error("Failed to load local Whisper model: %s", e)
                    self._load_failed = True
                    raise
            else:
                for size in [self.model_size, "medium", "small", "base"]:
                    try:
                        logger.info("Downloading Whisper model: %s", size)
                        self._model = WhisperModel(
                            size, device=self.device, compute_type=self.compute_type
                        )
                        logger.info("Whisper model %s loaded successfully", size)
                        break
                    except Exception as e:
                        logger.warning("Failed to load Whisper model %s: %s", size, e)
                if self._model is None:
                    self._load_failed = True
                    raise RuntimeError("无法加载任何 Whisper 模型")
        return self._model

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {audio_path}")

        model = self._load_model()
        segments_iter, info = model.transcribe(str(path), language=language, beam_size=5)

        segments = []
        total_duration = 0.0
        for seg in segments_iter:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
            total_duration = seg.end

        full_text = " ".join(s["text"] for s in segments)
        logger.info("Transcribed %s: %.1fs, %d segments", audio_path, info.duration, len(segments))

        return TranscriptionResult(
            text=full_text,
            segments=segments,
            duration=info.duration,
        )

    def batch_transcribe(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        results = []
        for path in audio_paths:
            try:
                result = self.transcribe(path, language=language)
                results.append(result)
            except (FileNotFoundError, ValueError) as e:
                logger.error("Failed to transcribe %s: %s", path, e)
                results.append(TranscriptionResult(text="", segments=[], duration=0.0))
        return results


asr_engine = WhisperASR()

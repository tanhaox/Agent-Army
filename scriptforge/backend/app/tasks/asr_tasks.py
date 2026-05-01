import logging
from pathlib import Path

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="asr.transcribe_file")
def transcribe_file_task(self, audio_path: str, language: str | None = None) -> dict:
    from app.services.asr import asr_engine

    self.update_state(state="PROCESSING", meta={"file": audio_path})
    result = asr_engine.transcribe(audio_path, language=language)

    Path(audio_path).unlink(missing_ok=True)

    return {
        "text": result.text,
        "segments": result.segments,
        "duration": result.duration,
    }


@celery_app.task(bind=True, name="asr.batch_transcribe")
def batch_transcribe_task(self, audio_paths: list[str], language: str | None = None) -> list[dict]:
    from app.services.asr import asr_engine

    total = len(audio_paths)
    results = []

    for i, path in enumerate(audio_paths):
        self.update_state(
            state="PROCESSING",
            meta={"current": i + 1, "total": total, "file": path},
        )
        try:
            result = asr_engine.transcribe(path, language=language)
            results.append({
                "file": path,
                "text": result.text,
                "segments": result.segments,
                "duration": result.duration,
            })
        except Exception as e:
            logger.error("Failed to transcribe %s: %s", path, e)
            results.append({"file": path, "error": str(e)})
        finally:
            Path(path).unlink(missing_ok=True)

    return results

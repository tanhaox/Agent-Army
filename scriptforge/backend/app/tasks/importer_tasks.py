import logging

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="import.video_import")
def import_video_task(self, url: str):
    from app.services.importer import VideoImporter, VideoImportError

    self.update_state(state="PROCESSING", meta={"stage": "downloading", "url": url})
    try:
        importer = VideoImporter()
        self.update_state(state="PROCESSING", meta={"stage": "transcribing", "url": url})
        result = importer.import_and_transcribe(url)
        return result
    except VideoImportError as e:
        logger.error("Video import error: %s", e)
        raise
    except Exception as e:
        logger.exception("Video import failed: %s", url)
        raise

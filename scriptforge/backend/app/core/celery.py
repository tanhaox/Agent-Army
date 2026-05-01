import logging

from celery import Celery
from celery.signals import after_setup_logger

from app.core.config import settings

celery_app = Celery(
    "scriptforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

celery_app.autodiscover_tasks(["app.tasks"])


@after_setup_logger.connect
def _on_celery_logger_setup(logger, **kwargs):
    """Configure Celery worker to also log to celery.log with sanitization."""
    from app.core.logger import setup_logging, _formatter, _sanitizing_filter, LOG_DIR

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    from logging.handlers import TimedRotatingFileHandler

    handler = TimedRotatingFileHandler(
        LOG_DIR / "celery.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(_formatter)
    handler.addFilter(_sanitizing_filter)
    logger.addHandler(handler)

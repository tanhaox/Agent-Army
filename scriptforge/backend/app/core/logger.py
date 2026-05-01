"""Centralized logging configuration for ScriptForge.

Provides file + console logging with daily rotation, 7-day retention,
and automatic sanitization of sensitive data (API keys, cookies, tokens).
"""
import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Patterns for sensitive data sanitization
_SENSITIVE_PATTERNS = [
    (re.compile(r"(sk-)[a-zA-Z0-9\-_]{8,}", re.IGNORECASE), r"\1***"),
    (re.compile(r"(Bearer\s+)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(sessionid[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(password[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(token[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(api[_-]?key[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(secret[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
]


class SanitizingFilter(logging.Filter):
    """Redact sensitive values from log records before output."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg and isinstance(record.msg, str):
            for pattern, replacement in _SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._sanitize(v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize(a) for a in record.args)
        return True

    @staticmethod
    def _sanitize(value) -> str:
        if not isinstance(value, str):
            return value
        for pattern, replacement in _SENSITIVE_PATTERNS:
            value = pattern.sub(replacement, value)
        return value


_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
_sanitizing_filter = SanitizingFilter()

_initialized = False


def setup_logging() -> None:
    """Initialize centralized logging. Safe to call multiple times."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Remove existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_formatter)
    console_handler.addFilter(_sanitizing_filter)
    root_logger.addHandler(console_handler)

    # Main application log file — daily rotation, keep 7 days
    app_handler = TimedRotatingFileHandler(
        LOG_DIR / "scriptforge.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    app_handler.setFormatter(_formatter)
    app_handler.addFilter(_sanitizing_filter)
    root_logger.addHandler(app_handler)

    logging.getLogger("scriptforge").info("Logging initialized — level=%s, dir=%s", LOG_LEVEL, LOG_DIR)


def get_log_dir() -> Path:
    """Return the logs directory path."""
    return LOG_DIR

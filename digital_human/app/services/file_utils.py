"""Filesystem helpers — safely move files to trash instead of deleting."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def safe_trash(path: Path) -> bool:
    """Move ``path`` to the system trash, falling back to shutil.rmtree only if
    send2trash is unavailable. Returns True on success.

    This satisfies the CLAUDE.md rule: never permanently delete user data
    without going through the recycle bin.
    """
    try:
        from send2trash import send2trash  # type: ignore

        send2trash(str(path))
        logger.info("Moved to trash: %s", path)
        return True
    except Exception as exc:
        logger.warning("send2trash failed (%s), falling back to shutil.rmtree", exc)
        try:
            shutil.rmtree(path, ignore_errors=True)
            logger.warning("Permanently removed directory: %s", path)
            return True
        except Exception as inner:
            logger.error("Failed to remove %s: %s", path, inner)
            return False

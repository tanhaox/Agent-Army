"""Database session management."""
from __future__ import annotations

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

_engine = None
_session_maker = None


def _apply_manual_migrations(engine) -> None:
    """幂等迁移: 给已有 director_jobs 表补 pipelines 列.

    Base.metadata.create_all 只建新表, 不会给已有表加列.
    旧库缺列时执行 ALTER TABLE ADD COLUMN (SQLite 支持, 非破坏性).
    """
    try:
        inspector = inspect(engine)
        if "director_jobs" not in inspector.get_table_names():
            return
        cols = {c["name"] for c in inspector.get_columns("director_jobs")}
        if "pipelines" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE director_jobs ADD COLUMN pipelines VARCHAR(32)"))
            logger.info("[db] migrated: director_jobs.pipelines column added")
    except Exception as exc:
        logger.warning("[db] pipelines column migration skipped: %s", exc)


def init_db(database_url: str) -> None:
    global _engine, _session_maker
    _engine = create_engine(database_url, connect_args={"check_same_thread": False})
    _session_maker = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)
    _apply_manual_migrations(_engine)


def get_engine():
    return _engine


def get_session_maker():
    return _session_maker


def get_db():
    if _session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = _session_maker()
    try:
        yield db
    finally:
        db.close()

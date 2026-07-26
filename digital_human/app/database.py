"""Database session management."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

_engine = None
_session_maker = None


def init_db(database_url: str) -> None:
    global _engine, _session_maker
    _engine = create_engine(database_url, connect_args={"check_same_thread": False})
    _session_maker = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)


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

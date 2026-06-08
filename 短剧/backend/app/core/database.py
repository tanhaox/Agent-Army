"""
数据库连接与会话管理。

使用 SQLAlchemy 2.0 异步模式 + asyncpg 驱动。
引擎创建延迟到首次使用，支持测试环境注入。
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型继承此类。"""


# 引擎和会话工厂延迟初始化
_engine = None
_async_session_maker: async_sessionmaker | None = None


def get_engine():
    """
    获取或创建异步引擎（延迟初始化）。

    首次调用时根据配置创建引擎，后续返回同一实例。
    """
    global _engine, _async_session_maker
    if _engine is None:
        settings = get_settings()
        db_url = settings.DATABASE_URL
        if not db_url:
            raise RuntimeError(
                "DATABASE_URL 未配置。请在 .env 文件中设置 DATABASE_URL。"
            )
        _engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine


def get_session_maker() -> async_sessionmaker:
    """获取异步会话工厂。"""
    if _async_session_maker is None:
        get_engine()  # 触发初始化
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入：提供数据库会话。

    每个请求获取独立会话，请求结束后自动关闭。
    用法::

        @router.post("/foo")
        async def foo(db: AsyncSession = Depends(get_db)):
            ...
    """
    maker = get_session_maker()
    async with maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

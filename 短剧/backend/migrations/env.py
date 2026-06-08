"""
Alembic 迁移环境配置 - 异步模式。

从应用配置中读取 DATABASE_URL，自动发现所有模型。
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.database import Base

# 导入所有模型，确保 Alembic 能发现它们
from app.models.script import Script  # noqa: F401
from app.models.character import Character  # noqa: F401
from app.models.storyboard import Storyboard  # noqa: F401
from app.models.narrative_tree import NarrativeTree  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 使用应用配置中的 DATABASE_URL 覆盖 alembic.ini 中的值
settings = get_settings()
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式：生成 SQL 脚本而不连接数据库。

    用于生成迁移脚本但不实际执行。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """执行迁移（同步回调）。"""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    在线模式：连接数据库并执行迁移。

    使用异步引擎连接数据库。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

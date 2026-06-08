"""
测试配置 - 公共 fixture。

提供异步测试客户端、内存数据库、mock LLM 客户端。
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# 使用 SQLite 内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite://"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """
    每个测试前创建表，测试后销毁。

    确保每个测试拥有干净的数据库状态。
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """测试用数据库会话（替代生产 get_db）。"""
    async with test_session_maker() as session:
        yield session


# 将 app 的数据库依赖替换为测试版本
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    异步 HTTP 测试客户端。

    通过 ASGITransport 直接调用 FastAPI，无需启动真实服务器。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Mock 数据 ---

MOCK_SCRIPT_RESPONSE = {
    "title": "契约甜妻",
    "episodes": [
        {
            "episode": 1,
            "hook": "穷女孩被迫嫁入豪门",
            "scenes": [
                {
                    "shot_type": "中景",
                    "action": "女主站在豪宅门口犹豫不决",
                    "dialogue": "我真的要进去吗？",
                    "emotion": "紧张",
                },
                {
                    "shot_type": "近景",
                    "action": "男主冷冷地看着她",
                    "dialogue": "进来，别浪费时间。",
                    "emotion": "平静",
                },
                {
                    "shot_type": "特写",
                    "action": "女主紧握拳头，下定决心",
                    "dialogue": "",
                    "emotion": "愤怒",
                },
            ],
            "cliffhanger": "她不知道契约背后藏着惊天秘密",
        },
        {
            "episode": 2,
            "hook": "契约的秘密逐渐浮出水面",
            "scenes": [
                {
                    "shot_type": "远景",
                    "action": "豪宅夜景全景",
                    "dialogue": "",
                    "emotion": "平静",
                },
                {
                    "shot_type": "中景",
                    "action": "女主偷听到男主打电话",
                    "dialogue": "那份契约...她不能知道真相。",
                    "emotion": "紧张",
                },
            ],
            "cliffhanger": "女主在门外听到了一切",
        },
    ],
    "total_episodes": 2,
}


@pytest_asyncio.fixture
def mock_llm_success():
    """Mock get_llm_client().generate 返回成功的剧本 JSON。"""
    import json

    with patch("app.services.script_generation_service.get_llm_client") as mock_factory:
        instance = mock_factory.return_value
        instance.generate = AsyncMock(return_value=json.dumps(MOCK_SCRIPT_RESPONSE))
        yield instance


@pytest_asyncio.fixture
def mock_llm_connection_error():
    """Mock get_llm_client().generate 抛出连接错误。"""
    from app.services.llm.base import LLMConnectionError

    with patch("app.services.script_generation_service.get_llm_client") as mock_factory:
        instance = mock_factory.return_value
        instance.generate = AsyncMock(side_effect=LLMConnectionError("连接失败"))
        yield instance

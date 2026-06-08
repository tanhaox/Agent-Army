"""
从剧情概要生成剧本 API 测试。

覆盖：成功生成、项目不存在、JSON 解析失败触发重试。
"""

import json

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import test_session_maker, MOCK_SCRIPT_RESPONSE


async def _create_project_directly(name: str = "测试项目") -> str:
    """直接创建项目并返回 ID。"""
    from app.models.project import Project
    async with test_session_maker() as db:
        project = Project(name=name)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return str(project.id)


class TestGenerateFromOutline:
    """从概要生成剧本测试组。"""

    @pytest.mark.asyncio
    async def test_generate_from_outline_success(self, client):
        """测试成功从概要生成剧本。"""
        project_id = await _create_project_directly()

        with patch("app.services.script_generation_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=json.dumps(MOCK_SCRIPT_RESPONSE))

            resp = await client.post(
                "/api/scripts/generate-from-outline",
                json={
                    "outline_text": "总裁隐瞒身份假装破产，女友不离不弃，最终真相大白两人相拥而泣。",
                    "style": "虐心催泪",
                    "project_id": project_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["content"]["episodes"]
        assert data["project_id"] == project_id

    @pytest.mark.asyncio
    async def test_generate_from_outline_project_not_found(self, client):
        """测试不存在的项目返回 404。"""
        project_id = await _create_project_directly()
        # 使用一个不存在但格式有效的 UUID
        fake_id = "99999999-9999-9999-9999-999999999999"
        resp = await client.post(
            "/api/scripts/generate-from-outline",
            json={
                "outline_text": "测试概要文本内容，足够长",
                "style": "虐心催泪",
                "project_id": fake_id,
            },
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_with_quality_retry(self, client):
        """测试质量不达标触发重试。"""
        project_id = await _create_project_directly()

        # 第一次：返回缺少 cliffhanger 的低质量剧本
        bad_script = {
            "title": "低质量剧本",
            "episodes": [
                {
                    "episode": 1,
                    "hook": "开篇钩子",
                    "scenes": [
                        {"shot_type": "中景", "action": "场景一", "dialogue": "你好", "emotion": "平静"},
                    ],
                    "cliffhanger": "",
                },
            ],
            "total_episodes": 1,
        }

        # 后续：返回合格剧本
        good_script = MOCK_SCRIPT_RESPONSE

        with patch("app.services.script_generation_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            # 提供4次mock返回，确保重试链路有足够的响应
            instance.generate = AsyncMock(
                side_effect=[
                    json.dumps(bad_script),     # attempt 1: 质量不通过
                    json.dumps(good_script),     # attempt 2: 应该通过
                    json.dumps(good_script),     # attempt 3 (备用)
                    json.dumps(good_script),     # attempt 4 (备用)
                ]
            )

            resp = await client.post(
                "/api/scripts/generate-from-outline",
                json={
                    "outline_text": "总裁测试女友真心，假装破产看她的反应。",
                    "style": "强反转爽文",
                    "project_id": project_id,
                },
            )

        # 应该成功（重试后通过）
        assert resp.status_code == 200
        assert resp.json()["content"]["episodes"]

    @pytest.mark.asyncio
    async def test_generate_from_outline_short_outline_rejected(self, client):
        """测试过短的概要文本被 422 拒绝。"""
        resp = await client.post(
            "/api/scripts/generate-from-outline",
            json={
                "outline_text": "太短",
                "style": "虐心催泪",
                "project_id": "some-id",
            },
        )
        assert resp.status_code == 422

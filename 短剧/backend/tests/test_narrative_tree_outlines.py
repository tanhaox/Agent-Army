"""
叙事树剧情概要生成 API 自动化测试。

覆盖：成功生成、默认风格、无效路径。
"""

import json

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import test_session_maker


# --- 测试用常量 ---

MOCK_TREE_DATA = {
    "root": {
        "id": "node_1",
        "text": "总裁测试女友真心",
        "tags": ["核心冲突"],
        "score": None,
        "pros": None,
        "cons": None,
        "children": [
            {
                "id": "node_2",
                "text": "假装破产",
                "tags": ["普通", "可控"],
                "score": 8,
                "pros": "经典套路",
                "cons": "缺乏新意",
                "children": [
                    {
                        "id": "node_5",
                        "text": "女友坚持陪伴",
                        "tags": ["甜蜜"],
                        "score": 7,
                        "pros": "暖心情节",
                        "cons": "节奏较慢",
                    },
                ],
            },
            {
                "id": "node_3",
                "text": "假装绝症",
                "tags": ["严重"],
                "score": 6,
                "pros": "情感爆发",
                "cons": "套路老旧",
                "children": [
                    {
                        "id": "node_6",
                        "text": "女友不离不弃",
                        "tags": ["虐心"],
                        "score": 8,
                        "pros": "催泪",
                        "cons": "略显刻意",
                    },
                ],
            },
        ],
    }
}

MOCK_TREE_JSON = json.dumps(MOCK_TREE_DATA, ensure_ascii=False)

# Mock 三种风格的概要
MOCK_OUTLINES = [
    "总裁隐瞒身份假装破产，女友不离不弃陪伴左右，经历重重误会与磨难，最终真相大白，两人相拥而泣。",
    "总裁假破产测试女友，结果女友比他还穷还搞笑，两人在困窘生活中产生无数甜蜜趣事。",
    "总裁假装破产后发现女友竟是隐藏的商业天才，两人联手反杀所有算计他们的反派，爽翻全场。",
]


async def _create_project_and_tree() -> tuple[str, str]:
    """创建项目和叙事树，返回 (project_id, tree_id)。"""
    from app.models.project import Project
    from app.models.narrative_tree import NarrativeTree

    async with test_session_maker() as db:
        project = Project(name="测试项目")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        pid = str(project.id)

        tree = NarrativeTree(
            project_id=pid,
            user_theme="总裁测试女友真心",
            tree_data=MOCK_TREE_DATA,
            status="confirmed",
        )
        db.add(tree)
        await db.commit()
        await db.refresh(tree)
        tid = str(tree.id)

    return pid, tid


class TestGenerateOutlines:
    """生成多版本概要测试组。"""

    @pytest.mark.asyncio
    async def test_generate_outlines_success(self, client):
        """测试成功生成三个版本概要。"""
        project_id, tree_id = await _create_project_and_tree()

        # Mock LLM.generate 依次返回三种风格
        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(side_effect=MOCK_OUTLINES)

            resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees/{tree_id}/generate-outlines",
                json={
                    "selected_branch_ids": ["node_1", "node_2", "node_5"],
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outlines"]) == 3
        assert data["storyline"]  # 主线描述非空

        # 验证三个版本
        versions = {o["version"] for o in data["outlines"]}
        assert "A" in versions
        assert "B" in versions
        assert "C" in versions

        # 验证风格
        styles = {o["style"] for o in data["outlines"]}
        assert "虐心催泪" in styles
        assert "甜宠搞笑" in styles
        assert "强反转爽文" in styles

        # 验证每个概要有文本
        for o in data["outlines"]:
            assert len(o["text"]) > 0

    @pytest.mark.asyncio
    async def test_generate_outlines_invalid_path(self, client):
        """测试无效路径返回 400。"""
        project_id, tree_id = await _create_project_and_tree()

        # 不含根节点的路径
        resp = await client.post(
            f"/api/projects/{project_id}/narrative-trees/{tree_id}/generate-outlines",
            json={
                "selected_branch_ids": ["node_2", "node_5"],
            },
        )

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_outlines_default_styles(self, client):
        """测试不传 styles 使用默认三种风格。"""
        project_id, tree_id = await _create_project_and_tree()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(side_effect=MOCK_OUTLINES)

            resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees/{tree_id}/generate-outlines",
                json={
                    "selected_branch_ids": ["node_1", "node_3", "node_6"],
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        styles = [o["style"] for o in data["outlines"]]
        assert styles == ["虐心催泪", "甜宠搞笑", "强反转爽文"]

    @pytest.mark.asyncio
    async def test_generate_outlines_custom_styles(self, client):
        """测试自定义风格。"""
        project_id, tree_id = await _create_project_and_tree()

        custom_outlines = ["悬疑版概要", "喜剧版概要"]

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockClass.return_value
            instance.generate = AsyncMock(side_effect=custom_outlines)

            resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees/{tree_id}/generate-outlines",
                json={
                    "selected_branch_ids": ["node_1", "node_2", "node_5"],
                    "styles": ["悬疑烧脑", "轻松喜剧"],
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outlines"]) == 2
        assert data["outlines"][0]["style"] == "悬疑烧脑"
        assert data["outlines"][1]["style"] == "轻松喜剧"

    @pytest.mark.asyncio
    async def test_generate_outlines_tree_not_found(self, client):
        """测试不存在的叙事树返回 404。"""
        from app.models.project import Project

        async with test_session_maker() as db:
            project = Project(name="测试")
            db.add(project)
            await db.commit()
            await db.refresh(project)
            pid = str(project.id)

        fake_tree_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/projects/{pid}/narrative-trees/{fake_tree_id}/generate-outlines",
            json={
                "selected_branch_ids": ["node_1", "node_2"],
            },
        )
        assert resp.status_code == 404

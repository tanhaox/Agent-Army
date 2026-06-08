"""
叙事树 API 自动化测试。

覆盖：生成叙事树（含评分）、列表、详情、确认分支、结构校验。
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
                "pros": "经典套路，受众广",
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
                    {
                        "id": "node_6",
                        "text": "女友趁机离去",
                        "tags": ["虐心"],
                        "score": 9,
                        "pros": "反转强烈",
                        "cons": "观众心疼",
                    },
                ],
            },
            {
                "id": "node_3",
                "text": "假装绝症",
                "tags": ["严重", "狗血"],
                "score": 6,
                "pros": "情感爆发力强",
                "cons": "套路老旧",
                "children": [
                    {
                        "id": "node_7",
                        "text": "女友不离不弃",
                        "tags": ["甜蜜", "虐心"],
                        "score": 8,
                        "pros": "催泪",
                        "cons": "略显刻意",
                    },
                ],
            },
            {
                "id": "node_4",
                "text": "找人诱惑测试",
                "tags": ["反转", "脑洞"],
                "score": 9,
                "pros": "悬念十足",
                "cons": "道德争议",
                "children": [
                    {
                        "id": "node_8",
                        "text": "女友反杀诱惑者",
                        "tags": ["反转"],
                        "score": 10,
                        "pros": "爽感拉满",
                        "cons": "需要好演员",
                    },
                ],
            },
        ],
    }
}

MOCK_TREE_JSON = json.dumps(MOCK_TREE_DATA, ensure_ascii=False)


async def _create_project_directly(name: str = "测试项目") -> str:
    """直接创建项目并返回 ID。"""
    from app.models.project import Project
    async with test_session_maker() as db:
        project = Project(name=name)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return str(project.id)


class TestGenerateNarrativeTree:
    """生成叙事树测试组。"""

    @pytest.mark.asyncio
    async def test_generate_tree_success(self, client):
        """测试成功生成叙事树（含评分）。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "总裁测试女友真心", "max_breadth": 3, "max_depth": 2},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["user_theme"] == "总裁测试女友真心"
        assert data["status"] == "draft"
        assert data["tree_data"]["root"]["id"] == "node_1"

        # 验证评分字段
        children = data["tree_data"]["root"]["children"]
        assert len(children) == 3
        assert children[0]["score"] == 8
        assert children[0]["pros"] == "经典套路，受众广"
        assert children[0]["cons"] == "缺乏新意"

    @pytest.mark.asyncio
    async def test_generate_tree_invalid_theme(self, client):
        """测试空主题返回 422。"""
        project_id = await _create_project_directly()

        resp = await client.post(
            f"/api/projects/{project_id}/narrative-trees",
            json={"theme": "", "max_breadth": 3, "max_depth": 2},
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_tree_project_not_found(self, client):
        """测试不存在的项目返回 404。"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        resp = await client.post(
            f"/api/projects/{fake_id}/narrative-trees",
            json={"theme": "测试主题", "max_breadth": 3, "max_depth": 2},
        )

        assert resp.status_code == 404


class TestNarrativeTreeListAndGet:
    """列表和详情测试组。"""

    @pytest.mark.asyncio
    async def test_list_trees(self, client):
        """测试获取叙事树列表。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )

        resp = await client.get(f"/api/projects/{project_id}/narrative-trees")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_tree_detail(self, client):
        """测试获取叙事树详情。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            create_resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )
        tree_id = create_resp.json()["id"]

        resp = await client.get(f"/api/projects/{project_id}/narrative-trees/{tree_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tree_id


class TestTreeStructureValidation:
    """叙事树结构校验测试组。"""

    @pytest.mark.asyncio
    async def test_tree_structure_has_scores(self, client):
        """验证保存的 JSON 非根节点都有 score/pros/cons。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            create_resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )

        tree_data = create_resp.json()["tree_data"]
        root = tree_data["root"]

        # 根节点无 score
        assert root["score"] is None

        # 非根节点必须有 score
        for child in root["children"]:
            assert "score" in child
            assert child["score"] is not None
            assert 1 <= child["score"] <= 10
            assert "pros" in child
            assert "cons" in child

            # 递归检查子节点
            for grandchild in child.get("children", []):
                assert "score" in grandchild
                assert "pros" in grandchild
                assert "cons" in grandchild

    @pytest.mark.asyncio
    async def test_tree_unique_node_ids(self, client):
        """验证所有节点 ID 唯一。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            create_resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )

        tree_data = create_resp.json()["tree_data"]

        all_ids: list[str] = []

        def collect_ids(node: dict) -> None:
            all_ids.append(node["id"])
            for child in node.get("children", []):
                collect_ids(child)

        collect_ids(tree_data["root"])
        assert len(all_ids) == len(set(all_ids)), "存在重复的节点 ID"


class TestConfirmBranches:
    """确认分支测试组。"""

    @pytest.mark.asyncio
    async def test_confirm_valid_path(self, client):
        """测试确认有效路径。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            create_resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )
        tree_id = create_resp.json()["id"]

        # 选择从根到叶子的路径: node_1 → node_2 → node_6
        resp = await client.put(
            f"/api/projects/{project_id}/narrative-trees/{tree_id}/confirm",
            json={"selected_branch_ids": ["node_1", "node_2", "node_6"]},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"
        assert resp.json()["selected_branch_ids"] == ["node_1", "node_2", "node_6"]

    @pytest.mark.asyncio
    async def test_confirm_discontinuous_path(self, client):
        """测试不含根节点的路径返回 400。"""
        project_id = await _create_project_directly()

        with patch("app.services.narrative_tree_service.get_llm_client") as MockFactory:
            instance = MockFactory.return_value
            instance.generate = AsyncMock(return_value=MOCK_TREE_JSON)

            create_resp = await client.post(
                f"/api/projects/{project_id}/narrative-trees",
                json={"theme": "测试", "max_breadth": 3, "max_depth": 2},
            )
        tree_id = create_resp.json()["id"]

        # 不含根节点的路径
        resp = await client.put(
            f"/api/projects/{project_id}/narrative-trees/{tree_id}/confirm",
            json={"selected_branch_ids": ["node_2", "node_5"]},
        )

        assert resp.status_code == 400


class TestBlockbusterLibrary:
    """爆款元素库测试组。"""

    def test_library_context_contains_elements(self):
        """验证知识库摘要包含各类元素。"""
        from app.services.blockbuster_library import build_library_context

        context = build_library_context()
        assert "情绪钩子" in context or "开场钩子" in context
        assert "反转模式" in context
        assert "人设原型" in context
        assert "评分参考" in context

    def test_library_data_completeness(self):
        """验证知识库数据完整性。"""
        from app.services.blockbuster_library import (
            EMOTION_HOOKS, PLOT_TWISTS,
            CHARACTER_ARCHETYPES, RHYTHM_TEMPLATES,
        )

        assert len(EMOTION_HOOKS) == 10
        assert len(PLOT_TWISTS) == 20
        assert len(CHARACTER_ARCHETYPES) == 10
        assert len(RHYTHM_TEMPLATES) == 5

        # 验证每个元素都有必要字段
        for h in EMOTION_HOOKS:
            assert "name" in h and "example" in h
        for t in PLOT_TWISTS:
            assert "name" in t and "description" in t and "scenario" in t
        for a in CHARACTER_ARCHETYPES:
            assert "name" in a and "trait" in a
        for r in RHYTHM_TEMPLATES:
            assert "name" in r and "episodes" in r and "pattern" in r

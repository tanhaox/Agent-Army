"""
项目与快照 API 自动化测试。

覆盖：项目 CRUD、创建快照、列表、恢复、对比。
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import test_session_maker


# --- 测试用常量 ---

BASE_SCRIPT_CONTENT = {
    "title": "契约甜妻",
    "episodes": [
        {
            "episode": 1,
            "hook": "穷女孩被迫嫁入豪门",
            "scenes": [
                {"shot_type": "中景", "action": "女主犹豫", "dialogue": "真的要进去吗？", "emotion": "紧张"},
            ],
            "cliffhanger": "契约背后有秘密",
        },
    ],
    "total_episodes": 1,
}

BASE_STORYBOARD = {
    "episode_no": 1,
    "shot_no": 1,
    "shot_type": "中景",
    "camera_move": "推",
    "action": "女主站在豪宅门口犹豫不决",
    "dialogue": "我真的要进去吗？",
    "emotion": "紧张",
    "environment": "豪宅大门前",
    "lighting": "逆光",
    "prompt_text": "medium shot, woman hesitating",
}


async def _create_script_directly(project_name: str, theme: str, content: dict) -> str:
    """通过测试数据库会话直接创建剧本，返回 script_id。"""
    from app.models.script import Script
    async with test_session_maker() as db:
        script = Script(project_name=project_name, theme=theme, content=content)
        db.add(script)
        await db.commit()
        await db.refresh(script)
        return str(script.id)


class TestProjectCRUD:
    """项目 CRUD 测试组。"""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient) -> None:
        """创建项目。"""
        resp = await client.post("/api/projects", json={"name": "测试项目"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "测试项目"
        assert data["description"] is None
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient) -> None:
        """列表查询。"""
        await client.post("/api/projects", json={"name": "项目A"})
        await client.post("/api/projects", json={"name": "项目B"})
        resp = await client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_get_project(self, client: AsyncClient) -> None:
        """获取详情。"""
        create_resp = await client.post("/api/projects", json={"name": "详情测试"})
        project_id = create_resp.json()["id"]

        resp = await client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "详情测试"

    @pytest.mark.asyncio
    async def test_update_project(self, client: AsyncClient) -> None:
        """更新项目。"""
        create_resp = await client.post("/api/projects", json={"name": "原名"})
        project_id = create_resp.json()["id"]

        resp = await client.put(f"/api/projects/{project_id}", json={"name": "新名称", "description": "新描述"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"
        assert resp.json()["description"] == "新描述"

    @pytest.mark.asyncio
    async def test_delete_project(self, client: AsyncClient) -> None:
        """删除项目。"""
        create_resp = await client.post("/api/projects", json={"name": "待删除"})
        project_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/projects/{project_id}")
        assert resp.status_code == 200

        get_resp = await client.get(f"/api/projects/{project_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_project_not_found(self, client: AsyncClient) -> None:
        """查询不存在的项目返回 404。"""
        resp = await client.get("/api/projects/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestSnapshots:
    """快照操作测试组。"""

    @pytest.mark.asyncio
    async def test_create_snapshot_no_script(self, client: AsyncClient) -> None:
        """项目未关联剧本时创建快照返回 400。"""
        create_resp = await client.post("/api/projects", json={"name": "无剧本项目"})
        project_id = create_resp.json()["id"]

        resp = await client.post(f"/api/projects/{project_id}/snapshots", json={})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_snapshot(self, client: AsyncClient) -> None:
        """正常创建快照。"""
        # 创建项目
        proj_resp = await client.post("/api/projects", json={"name": "快照测试"})
        project_id = proj_resp.json()["id"]

        # 直接创建剧本
        script_id = await _create_script_directly("快照测试剧本", "测试", BASE_SCRIPT_CONTENT)

        # 关联剧本到项目
        await client.put(f"/api/projects/{project_id}", json={"current_script_id": script_id})

        # 创建分镜
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "script_id": script_id})

        # 创建快照
        resp = await client.post(f"/api/projects/{project_id}/snapshots", json={
            "snapshot_name": "测试快照",
            "remark": "测试备注",
        })
        assert resp.status_code == 200, f"预期 200，实际 {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["snapshot_name"] == "测试快照"
        assert data["script_snapshot"] is not None
        assert data["storyboards_snapshot"] is not None
        assert len(data["storyboards_snapshot"]) == 1

    @pytest.mark.asyncio
    async def test_list_snapshots(self, client: AsyncClient) -> None:
        """获取快照列表。"""
        # 创建并准备项目
        proj_resp = await client.post("/api/projects", json={"name": "列表测试"})
        project_id = proj_resp.json()["id"]

        resp = await client.get(f"/api/projects/{project_id}/snapshots")
        assert resp.status_code == 200
        # 新项目无快照
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_restore_snapshot(self, client: AsyncClient) -> None:
        """恢复快照后验证新剧本和分镜被创建。"""
        # 准备项目 + 剧本 + 分镜 + 快照
        proj_resp = await client.post("/api/projects", json={"name": "恢复测试"})
        project_id = proj_resp.json()["id"]

        script_id = await _create_script_directly("恢复测试剧本", "测试", BASE_SCRIPT_CONTENT)

        await client.put(f"/api/projects/{project_id}", json={"current_script_id": script_id})
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "script_id": script_id})
        snap_resp = await client.post(f"/api/projects/{project_id}/snapshots", json={"snapshot_name": "恢复前"})
        snapshot_id = snap_resp.json()["id"]

        # 恢复快照
        restore_resp = await client.post(f"/api/projects/{project_id}/snapshots/{snapshot_id}/restore")
        assert restore_resp.status_code == 200

        restored_project = restore_resp.json()
        # current_script_id 应该改变了
        assert restored_project["current_script_id"] != script_id

    @pytest.mark.asyncio
    async def test_compare_snapshots(self, client: AsyncClient) -> None:
        """对比两个快照。"""
        proj_resp = await client.post("/api/projects", json={"name": "对比测试"})
        project_id = proj_resp.json()["id"]

        # 创建第一个版本的剧本和快照
        script1_id = await _create_script_directly("对比测试V1", "V1", BASE_SCRIPT_CONTENT)

        await client.put(f"/api/projects/{project_id}", json={"current_script_id": script1_id})
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "script_id": script1_id})
        snap1_resp = await client.post(f"/api/projects/{project_id}/snapshots", json={"snapshot_name": "V1"})
        snap1_id = snap1_resp.json()["id"]

        # 创建第二个版本（修改后的剧本）
        modified_content = {
            **BASE_SCRIPT_CONTENT,
            "title": "契约甜妻2",
            "episodes": [
                *BASE_SCRIPT_CONTENT["episodes"],
                {"episode": 2, "hook": "新集", "scenes": [{"shot_type": "远景", "action": "夜景", "dialogue": "", "emotion": "平静"}], "cliffhanger": "新悬念"},
            ],
            "total_episodes": 2,
        }

        script2_id = await _create_script_directly("对比测试V2", "V2", modified_content)

        await client.put(f"/api/projects/{project_id}", json={"current_script_id": script2_id})
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "script_id": script2_id, "episode_no": 2, "shot_no": 1, "action": "夜景全景"})
        snap2_resp = await client.post(f"/api/projects/{project_id}/snapshots", json={"snapshot_name": "V2"})
        snap2_id = snap2_resp.json()["id"]

        # 对比
        resp = await client.post(f"/api/projects/{project_id}/snapshots/compare", json={
            "snapshot_id_1": snap1_id,
            "snapshot_id_2": snap2_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_1_name"] == "V1"
        assert data["snapshot_2_name"] == "V2"
        assert data["script_diff"]["title_changed"] is True
        assert data["script_diff"]["episodes_count_1"] == 1
        assert data["script_diff"]["episodes_count_2"] == 2

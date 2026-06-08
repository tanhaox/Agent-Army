"""
分镜 API 自动化测试。

覆盖：创建、查询（含过滤）、更新、删除、提示词生成、参数校验。
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


# --- 测试用常量 ---

BASE_STORYBOARD = {
    "episode_no": 1,
    "shot_no": 1,
    "shot_type": "中景",
    "camera_move": "推",
    "action": "女主站在豪宅门口犹豫不决",
    "dialogue": "我真的要进去吗？",
    "emotion": "紧张",
    "environment": "豪宅大门前，灯光昏暗",
    "lighting": "逆光，柔和",
}


class TestCreateStoryboard:
    """POST /api/storyboards 测试组。"""

    @pytest.mark.asyncio
    async def test_create_storyboard(self, client: AsyncClient) -> None:
        """正常创建分镜，验证返回结构。"""
        resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        assert resp.status_code == 200, f"预期 200，实际 {resp.status_code}: {resp.text}"

        data = resp.json()
        assert data["episode_no"] == 1
        assert data["shot_no"] == 1
        assert data["shot_type"] == "中景"
        assert data["camera_move"] == "推"
        assert data["action"] == "女主站在豪宅门口犹豫不决"
        assert data["dialogue"] == "我真的要进去吗？"
        assert data["emotion"] == "紧张"
        assert data["approved"] is False
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_storyboard_with_script_id(self, client: AsyncClient) -> None:
        """创建分镜并关联剧本。"""
        payload = {**BASE_STORYBOARD, "script_id": "00000000-0000-0000-0000-000000000001"}
        resp = await client.post("/api/storyboards", json=payload)
        assert resp.status_code == 200
        assert resp.json()["script_id"] == "00000000-0000-0000-0000-000000000001"

    @pytest.mark.asyncio
    async def test_create_storyboard_missing_required(self, client: AsyncClient) -> None:
        """缺少必填字段时返回 422。"""
        resp = await client.post("/api/storyboards", json={"episode_no": 1})
        assert resp.status_code == 422


class TestListStoryboards:
    """GET /api/storyboards 测试组。"""

    @pytest.mark.asyncio
    async def test_list_storyboards_empty(self, client: AsyncClient) -> None:
        """无分镜时列表为空。"""
        resp = await client.get("/api/storyboards")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_storyboards_with_filter(self, client: AsyncClient) -> None:
        """按 script_id 过滤分镜列表。"""
        script_a = "00000000-0000-0000-0000-000000000001"
        script_b = "00000000-0000-0000-0000-000000000002"

        # 创建两个剧本的分镜
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "script_id": script_a})
        await client.post("/api/storyboards", json={
            **BASE_STORYBOARD, "script_id": script_b, "shot_no": 2,
        })

        # 过滤 script_a
        resp = await client.get(f"/api/storyboards?script_id={script_a}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["script_id"] == script_a

    @pytest.mark.asyncio
    async def test_list_storyboards_ordered(self, client: AsyncClient) -> None:
        """列表按集数和镜头序号排序。"""
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "episode_no": 2, "shot_no": 1})
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "episode_no": 1, "shot_no": 2})
        await client.post("/api/storyboards", json={**BASE_STORYBOARD, "episode_no": 1, "shot_no": 1})

        resp = await client.get("/api/storyboards")
        data = resp.json()
        assert data[0]["episode_no"] == 1 and data[0]["shot_no"] == 1
        assert data[1]["episode_no"] == 1 and data[1]["shot_no"] == 2
        assert data[2]["episode_no"] == 2 and data[2]["shot_no"] == 1


class TestGetStoryboard:
    """GET /api/storyboards/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_get_storyboard(self, client: AsyncClient) -> None:
        """创建后查询，验证内容一致。"""
        create_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        sb_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/storyboards/{sb_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["action"] == "女主站在豪宅门口犹豫不决"

    @pytest.mark.asyncio
    async def test_get_storyboard_not_found(self, client: AsyncClient) -> None:
        """查询不存在的 ID 返回 404。"""
        resp = await client.get("/api/storyboards/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestUpdateStoryboard:
    """PUT /api/storyboards/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_update_storyboard(self, client: AsyncClient) -> None:
        """更新分镜动作描述。"""
        create_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        sb_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/storyboards/{sb_id}",
            json={"action": "女主转身离开", "approved": True},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["action"] == "女主转身离开"
        assert data["approved"] is True


class TestDeleteStoryboard:
    """DELETE /api/storyboards/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_delete_storyboard(self, client: AsyncClient) -> None:
        """删除分镜后查询返回 404。"""
        create_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        sb_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/storyboards/{sb_id}")
        assert del_resp.status_code == 200

        get_resp = await client.get(f"/api/storyboards/{sb_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient) -> None:
        """删除不存在的分镜返回 404。"""
        resp = await client.delete("/api/storyboards/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestGeneratePrompt:
    """POST /api/storyboards/generate-prompt 测试组。"""

    @pytest.mark.asyncio
    async def test_generate_prompt(self, client: AsyncClient) -> None:
        """正常生成提示词，验证格式和内容。"""
        resp = await client.post("/api/storyboards/generate-prompt", json={
            "shot_type": "中景",
            "camera_move": "推",
            "action": "a young woman crying and clenching fist",
            "emotion": "angry",
            "environment": "dim room with backlight",
            "lighting": "soft ambient",
        })
        assert resp.status_code == 200

        prompt = resp.json()["prompt_text"]
        assert "medium shot" in prompt
        assert "camera push in" in prompt
        assert "a young woman crying and clenching fist" in prompt
        assert "angry emotion" in prompt
        assert "dim room with backlight" in prompt
        assert "cinematic, 4k" in prompt

    @pytest.mark.asyncio
    async def test_generate_prompt_missing_field(self, client: AsyncClient) -> None:
        """缺少必填字段时返回 422。"""
        resp = await client.post("/api/storyboards/generate-prompt", json={
            "shot_type": "中景",
            "action": "测试动作",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_prompt_english_passthrough(self, client: AsyncClient) -> None:
        """未映射的景别/运镜值直接透传。"""
        resp = await client.post("/api/storyboards/generate-prompt", json={
            "shot_type": "drone shot",
            "camera_move": "orbit",
            "action": "walking in park",
            "emotion": "calm",
            "environment": "sunny park",
            "lighting": "natural light",
        })
        assert resp.status_code == 200
        prompt = resp.json()["prompt_text"]
        assert "drone shot" in prompt
        assert "orbit" in prompt

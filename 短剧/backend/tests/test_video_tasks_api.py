"""
视频任务 API 自动化测试。

覆盖：创建任务、查询列表、查询详情、参数校验。
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


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
    "prompt_text": "medium shot, camera push in, woman hesitating, tense emotion, dim mansion entrance, backlight, cinematic, 4k",
}

VIDEO_TASK_PAYLOAD = {
    "prompt": "medium shot, camera push in, woman hesitating, cinematic, 4k",
    "mode": "std",
    "duration": "5",
    "aspect_ratio": "16:9",
}


class TestCreateVideoTask:
    """POST /api/video-tasks 测试组。"""

    @pytest.mark.asyncio
    async def test_create_video_task(self, client: AsyncClient) -> None:
        """正常创建视频任务，验证返回结构。"""
        # 先创建分镜
        sb_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        assert sb_resp.status_code == 200
        storyboard_id = sb_resp.json()["id"]

        # Mock Kling 客户端
        with patch("app.services.video_task_service.KlingClient") as MockKling:
            mock_instance = MockKling.return_value
            mock_instance.submit_text2video = AsyncMock(return_value="kling_task_123")

            payload = {**VIDEO_TASK_PAYLOAD, "storyboard_id": storyboard_id}
            resp = await client.post("/api/video-tasks", json=payload)
            assert resp.status_code == 200, f"预期 200，实际 {resp.status_code}: {resp.text}"

            data = resp.json()
            assert data["storyboard_id"] == storyboard_id
            assert data["status"] == "processing"
            assert data["prompt"] == VIDEO_TASK_PAYLOAD["prompt"]
            assert data["mode"] == "std"
            assert data["duration"] == "5"
            assert data["aspect_ratio"] == "16:9"
            assert "id" in data
            assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_video_task_missing_fields(self, client: AsyncClient) -> None:
        """缺少必填字段时返回 422。"""
        resp = await client.post("/api/video-tasks", json={"mode": "std"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_video_task_kling_failure(self, client: AsyncClient) -> None:
        """Kling API 调用失败时任务状态为 failed。"""
        from app.services.kling_service import KlingAPIError

        sb_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        storyboard_id = sb_resp.json()["id"]

        with patch("app.services.video_task_service.KlingClient") as MockKling:
            mock_instance = MockKling.return_value
            mock_instance.submit_text2video = AsyncMock(
                side_effect=KlingAPIError("Kling API 返回 401: Unauthorized")
            )

            payload = {**VIDEO_TASK_PAYLOAD, "storyboard_id": storyboard_id}
            resp = await client.post("/api/video-tasks", json=payload)
            assert resp.status_code == 200

            data = resp.json()
            assert data["status"] == "failed"
            assert "401" in data["error_message"]


class TestListVideoTasks:
    """GET /api/video-tasks 测试组。"""

    @pytest.mark.asyncio
    async def test_list_video_tasks_empty(self, client: AsyncClient) -> None:
        """无视频任务时列表为空。"""
        resp = await client.get("/api/video-tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_video_tasks_with_filter(self, client: AsyncClient) -> None:
        """按 storyboard_id 过滤视频任务。"""
        # 创建两个分镜
        sb1 = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        sb2 = await client.post("/api/storyboards", json={
            **BASE_STORYBOARD, "shot_no": 2,
        })
        sb1_id = sb1.json()["id"]
        sb2_id = sb2.json()["id"]

        with patch("app.services.video_task_service.KlingClient") as MockKling:
            mock_instance = MockKling.return_value
            mock_instance.submit_text2video = AsyncMock(return_value="kling_task_1")

            # 为第一个分镜创建视频任务
            await client.post("/api/video-tasks", json={
                **VIDEO_TASK_PAYLOAD, "storyboard_id": sb1_id,
            })

        # 过滤 sb1
        resp = await client.get(f"/api/video-tasks?storyboard_id={sb1_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["storyboard_id"] == sb1_id

        # 过滤 sb2（无任务）
        resp2 = await client.get(f"/api/video-tasks?storyboard_id={sb2_id}")
        assert resp2.status_code == 200
        assert resp2.json() == []


class TestGetVideoTask:
    """GET /api/video-tasks/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_get_video_task(self, client: AsyncClient) -> None:
        """创建后查询，验证内容一致。"""
        sb_resp = await client.post("/api/storyboards", json=BASE_STORYBOARD)
        storyboard_id = sb_resp.json()["id"]

        with patch("app.services.video_task_service.KlingClient") as MockKling:
            mock_instance = MockKling.return_value
            mock_instance.submit_text2video = AsyncMock(return_value="kling_task_abc")

            create_resp = await client.post("/api/video-tasks", json={
                **VIDEO_TASK_PAYLOAD, "storyboard_id": storyboard_id,
            })

        task_id = create_resp.json()["id"]
        get_resp = await client.get(f"/api/video-tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["prompt"] == VIDEO_TASK_PAYLOAD["prompt"]

    @pytest.mark.asyncio
    async def test_get_video_task_not_found(self, client: AsyncClient) -> None:
        """查询不存在的 ID 返回 404。"""
        resp = await client.get("/api/video-tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

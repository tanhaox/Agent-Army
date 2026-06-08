"""
角色参考图 AI 生成测试。

覆盖：提示词构建、正常生成流程、角度校验、ComfyUI 不可用、生成失败。
使用 mock 模拟 ComfyUI 调用，无需真实 ComfyUI 服务。
"""

import io
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200


class TestBuildCharacterPrompt:
    """提示词构建测试。"""

    def test_female_character(self) -> None:
        from app.services.character_image_service import _build_character_prompt

        traits = {"gender": "female", "age": 25, "appearance": "短发、黑眸", "personality": "外冷内热"}
        prompt = _build_character_prompt(traits, "front")
        assert "1girl" in prompt
        assert "25岁" in prompt
        assert "短发、黑眸" in prompt
        assert "正面视角" in prompt

    def test_male_character(self) -> None:
        from app.services.character_image_service import _build_character_prompt

        traits = {"gender": "male", "age": 30, "appearance": "高大、短寸"}
        prompt = _build_character_prompt(traits, "three_quarter")
        assert "1boy" in prompt
        assert "three-quarter view" in prompt

    def test_side_angle(self) -> None:
        from app.services.character_image_service import _build_character_prompt

        traits = {"age": 20}
        prompt = _build_character_prompt(traits, "side")
        assert "side view" in prompt
        assert "侧面视角" in prompt

    def test_default_to_front_angle(self) -> None:
        from app.services.character_image_service import _build_character_prompt, ANGLE_PROMPTS

        traits = {}
        prompt = _build_character_prompt(traits, "front")
        assert ANGLE_PROMPTS["front"] in prompt


class TestGenerateImageEndpoint:
    """POST /api/characters/{id}/generate-image 端点测试。"""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, client: AsyncClient) -> None:
        """正常生成参考图。"""
        # 1. 创建角色
        create_resp = await client.post(
            "/api/characters",
            json={"name": "林小夏", "traits": {"age": 25, "appearance": "短发、黑眸"}},
        )
        assert create_resp.status_code == 200
        char_id = create_resp.json()["id"]

        # 2. Mock ComfyUI 生成
        with patch(
            "app.services.character_image_service.ComfyUIClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.generate_image = AsyncMock(return_value=FAKE_PNG)

            resp = await client.post(
                f"/api/characters/{char_id}/generate-image",
                json={"angle": "front"},
            )

        assert resp.status_code == 200, f"预期 200，实际 {resp.status_code}: {resp.text}"
        data = resp.json()
        assert len(data["reference_images"]) >= 1
        assert "/static/characters/" in data["reference_images"][0]

    @pytest.mark.asyncio
    async def test_generate_image_invalid_angle(self, client: AsyncClient) -> None:
        """无效角度应返回 400。"""
        create_resp = await client.post(
            "/api/characters", json={"name": "角度测试"}
        )
        char_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/characters/{char_id}/generate-image",
            json={"angle": "back"},
        )
        assert resp.status_code == 400
        assert "不支持的角度" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_image_character_not_found(self, client: AsyncClient) -> None:
        """不存在的角色应返回 404。"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/characters/{fake_id}/generate-image",
            json={"angle": "front"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_image_comfyui_unavailable(self, client: AsyncClient) -> None:
        """ComfyUI 不可用时返回 503。"""
        from app.services.comfyui_service import ComfyUIConnectionError

        create_resp = await client.post(
            "/api/characters", json={"name": "503测试"}
        )
        char_id = create_resp.json()["id"]

        with patch(
            "app.services.character_image_service.ComfyUIClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.generate_image = AsyncMock(
                side_effect=ComfyUIConnectionError("无法连接")
            )

            resp = await client.post(
                f"/api/characters/{char_id}/generate-image",
                json={"angle": "front"},
            )

        assert resp.status_code == 503
        assert "ComfyUI" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_image_generation_failed(self, client: AsyncClient) -> None:
        """生成失败时返回 500。"""
        from app.services.comfyui_service import ComfyUIGenerationError

        create_resp = await client.post(
            "/api/characters", json={"name": "500测试"}
        )
        char_id = create_resp.json()["id"]

        with patch(
            "app.services.character_image_service.ComfyUIClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.generate_image = AsyncMock(
                side_effect=ComfyUIGenerationError("生成超时")
            )

            resp = await client.post(
                f"/api/characters/{char_id}/generate-image",
                json={"angle": "front"},
            )

        assert resp.status_code == 500
        assert "生成失败" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_image_default_angle(self, client: AsyncClient) -> None:
        """不传 angle 时默认使用 front。"""
        create_resp = await client.post(
            "/api/characters", json={"name": "默认角度"}
        )
        char_id = create_resp.json()["id"]

        with patch(
            "app.services.character_image_service.ComfyUIClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.generate_image = AsyncMock(return_value=FAKE_PNG)

            resp = await client.post(
                f"/api/characters/{char_id}/generate-image",
                json={},
            )

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_multiple_angles(self, client: AsyncClient) -> None:
        """为同一角色生成多角度图片。"""
        create_resp = await client.post(
            "/api/characters", json={"name": "多角度"}
        )
        char_id = create_resp.json()["id"]

        with patch(
            "app.services.character_image_service.ComfyUIClient"
        ) as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.generate_image = AsyncMock(return_value=FAKE_PNG)

            for angle in ["front", "three_quarter", "side"]:
                resp = await client.post(
                    f"/api/characters/{char_id}/generate-image",
                    json={"angle": angle},
                )
                assert resp.status_code == 200

        data = resp.json()
        assert len(data["reference_images"]) == 3

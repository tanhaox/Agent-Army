"""
角色 API 自动化测试。

覆盖：创建、查询、更新、上传图片、删除、文件类型校验。
"""

import io
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import MOCK_SCRIPT_RESPONSE


class TestCreateCharacter:
    """POST /api/characters 测试组。"""

    @pytest.mark.asyncio
    async def test_create_character(self, client: AsyncClient) -> None:
        """正常创建角色，验证返回结构和数据库保存。"""
        payload = {
            "name": "林小夏",
            "traits": {"age": 25, "personality": "外冷内热", "appearance": "短发、黑眸"},
            "voice_id": "voice_001",
        }
        resp = await client.post("/api/characters", json=payload)
        assert resp.status_code == 200, f"预期 200，实际 {resp.status_code}: {resp.text}"

        data = resp.json()
        assert data["name"] == "林小夏"
        assert data["traits"]["age"] == 25
        assert data["voice_id"] == "voice_001"
        assert data["reference_images"] == []
        assert data["platform_bindings"] == {}
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_character_empty_name(self, client: AsyncClient) -> None:
        """空角色名应返回 422。"""
        resp = await client.post("/api/characters", json={"name": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_character_default_traits(self, client: AsyncClient) -> None:
        """不传 traits 时应使用默认空字典。"""
        resp = await client.post("/api/characters", json={"name": "测试角色"})
        assert resp.status_code == 200
        assert resp.json()["traits"] == {}


class TestGetCharacter:
    """GET /api/characters 测试组。"""

    @pytest.mark.asyncio
    async def test_list_characters_empty(self, client: AsyncClient) -> None:
        """无角色时列表为空。"""
        resp = await client.get("/api/characters")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_character_by_id(self, client: AsyncClient) -> None:
        """创建后查询，验证内容一致。"""
        create_resp = await client.post("/api/characters", json={"name": "查询测试"})
        char_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/characters/{char_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "查询测试"

    @pytest.mark.asyncio
    async def test_get_character_not_found(self, client: AsyncClient) -> None:
        """查询不存在的 ID 返回 404。"""
        resp = await client.get("/api/characters/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestUpdateCharacter:
    """PUT /api/characters/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_update_character_name(self, client: AsyncClient) -> None:
        """更新角色名称。"""
        create_resp = await client.post("/api/characters", json={"name": "原名"})
        char_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/characters/{char_id}",
            json={"name": "新名字"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "新名字"

    @pytest.mark.asyncio
    async def test_update_character_traits(self, client: AsyncClient) -> None:
        """更新角色特征。"""
        create_resp = await client.post("/api/characters", json={"name": "特征测试"})
        char_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/characters/{char_id}",
            json={"traits": {"age": 30, "personality": "开朗"}},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["traits"]["age"] == 30


class TestUploadImage:
    """POST /api/characters/{id}/images 测试组。"""

    @pytest.mark.asyncio
    async def test_upload_image(self, client: AsyncClient) -> None:
        """上传有效图片，验证 reference_images 更新。"""
        create_resp = await client.post("/api/characters", json={"name": "图片测试"})
        char_id = create_resp.json()["id"]

        img_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # 最小 PNG 头
        files = {"file": ("test.png", io.BytesIO(img_content), "image/png")}
        upload_resp = await client.post(
            f"/api/characters/{char_id}/images",
            files=files,
        )
        assert upload_resp.status_code == 200

        data = upload_resp.json()
        assert len(data["reference_images"]) == 1
        assert "/static/characters/" in data["reference_images"][0]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient) -> None:
        """上传不支持的文件类型，返回 400。"""
        create_resp = await client.post("/api/characters", json={"name": "类型测试"})
        char_id = create_resp.json()["id"]

        files = {"file": ("test.exe", io.BytesIO(b"fake"), "application/octet-stream")}
        resp = await client.post(f"/api/characters/{char_id}/images", files=files)
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]


class TestDeleteCharacter:
    """DELETE /api/characters/{id} 测试组。"""

    @pytest.mark.asyncio
    async def test_delete_character(self, client: AsyncClient) -> None:
        """删除角色后查询返回 404。"""
        create_resp = await client.post("/api/characters", json={"name": "删除测试"})
        char_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/characters/{char_id}")
        assert del_resp.status_code == 200

        get_resp = await client.get(f"/api/characters/{char_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient) -> None:
        """删除不存在的角色返回 404。"""
        resp = await client.delete("/api/characters/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

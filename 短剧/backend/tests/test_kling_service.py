"""
Kling 服务单元测试。

覆盖：JWT 生成、任务提交、状态查询、轮询等待、错误处理。
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.kling_service import KlingAPIError, KlingAuthError, KlingClient


# --- 测试常量 ---

MOCK_ACCESS_KEY = "test_access_key_123"
MOCK_SECRET_KEY = "test_secret_key_456"
MOCK_TASK_ID = "kling_task_abc123"


@pytest.fixture
def kling_client() -> KlingClient:
    """创建测试用 KlingClient（不依赖真实配置）。"""
    return KlingClient(
        access_key=MOCK_ACCESS_KEY,
        secret_key=MOCK_SECRET_KEY,
        base_url="https://mock-api.kling.test",
        timeout=30,
        poll_interval=0.1,
    )


class TestJWTGeneration:
    """JWT Token 生成测试。"""

    def test_generate_jwt_success(self, kling_client: KlingClient) -> None:
        """正常生成 JWT Token。"""
        token = kling_client._generate_jwt()
        assert isinstance(token, str)
        # JWT 由三段 base64url 组成，以 . 分隔
        parts = token.split(".")
        assert len(parts) == 3

    def test_generate_jwt_contains_access_key(self, kling_client: KlingClient) -> None:
        """JWT payload 包含 access_key 作为 iss。"""
        import base64

        token = kling_client._generate_jwt()
        payload_b64 = token.split(".")[1]
        # 补齐 base64 padding
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        assert payload["iss"] == MOCK_ACCESS_KEY
        assert "exp" in payload
        assert "nbf" in payload

    def test_generate_jwt_missing_keys(self) -> None:
        """缺少密钥时抛出 KlingAuthError。"""
        client = KlingClient(access_key="", secret_key="")
        with pytest.raises(KlingAuthError, match="未配置"):
            client._generate_jwt()


class TestSubmitText2Video:
    """文生视频任务提交测试。"""

    @pytest.mark.asyncio
    async def test_submit_text2video_success(self, kling_client: KlingClient) -> None:
        """正常提交文生视频任务，返回 task_id。"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"task_id": MOCK_TASK_ID},
        }
        mock_response.raise_for_status = MagicMock()

        mock_post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.post = mock_post
            MockClient.return_value = mock_instance

            task_id = await kling_client.submit_text2video("A woman walking")
            assert task_id == MOCK_TASK_ID

            # 验证请求参数
            call_args = mock_post.call_args
            assert "text2video" in call_args.kwargs.get("url", call_args.args[0] if call_args.args else "")
            payload = call_args.kwargs.get("json", {})
            assert payload["prompt"] == "A woman walking"

    @pytest.mark.asyncio
    async def test_submit_text2video_api_error(self, kling_client: KlingClient) -> None:
        """API 返回错误状态码时抛出 KlingAPIError。"""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_response
            )
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.post = mock_post
            MockClient.return_value = mock_instance

            with pytest.raises(KlingAPIError, match="401"):
                await kling_client.submit_text2video("test prompt")


class TestGetTaskStatus:
    """任务状态查询测试。"""

    @pytest.mark.asyncio
    async def test_get_task_status_succeed(self, kling_client: KlingClient) -> None:
        """查询成功完成的任务。"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "task_id": MOCK_TASK_ID,
                "task_status": "succeed",
                "task_result": {
                    "videos": [
                        {"url": "https://cdn.kling.test/video1.mp4", "duration": 5}
                    ]
                },
            }
        }

        mock_get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.get = mock_get
            MockClient.return_value = mock_instance

            result = await kling_client.get_task_status(MOCK_TASK_ID)
            assert result["status"] == "succeed"
            assert result["video_url"] == "https://cdn.kling.test/video1.mp4"
            assert result["video_duration"] == 5

    @pytest.mark.asyncio
    async def test_get_task_status_processing(self, kling_client: KlingClient) -> None:
        """查询处理中的任务。"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "task_id": MOCK_TASK_ID,
                "task_status": "processing",
            }
        }

        mock_get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.get = mock_get
            MockClient.return_value = mock_instance

            result = await kling_client.get_task_status(MOCK_TASK_ID)
            assert result["status"] == "processing"
            assert result["video_url"] is None


class TestWaitForCompletion:
    """轮询等待完成测试。"""

    @pytest.mark.asyncio
    async def test_wait_succeed_on_first_poll(self, kling_client: KlingClient) -> None:
        """第一次轮询就返回成功。"""
        mock_result = {
            "task_id": MOCK_TASK_ID,
            "status": "succeed",
            "video_url": "https://cdn.test/video.mp4",
            "video_duration": None,
        }

        with patch.object(kling_client, "get_task_status", return_value=mock_result):
            result = await kling_client.wait_for_completion(MOCK_TASK_ID, timeout=5)
            assert result["status"] == "succeed"
            assert result["video_url"] == "https://cdn.test/video.mp4"

    @pytest.mark.asyncio
    async def test_wait_fails(self, kling_client: KlingClient) -> None:
        """任务失败时抛出 KlingAPIError。"""
        mock_result = {
            "task_id": MOCK_TASK_ID,
            "status": "failed",
            "video_url": None,
            "video_duration": None,
        }

        with patch.object(kling_client, "get_task_status", return_value=mock_result):
            with pytest.raises(KlingAPIError, match="生成失败"):
                await kling_client.wait_for_completion(MOCK_TASK_ID, timeout=5)

    @pytest.mark.asyncio
    async def test_wait_timeout(self, kling_client: KlingClient) -> None:
        """超时时抛出 KlingAPIError。"""
        mock_result = {
            "task_id": MOCK_TASK_ID,
            "status": "processing",
            "video_url": None,
            "video_duration": None,
        }

        with patch.object(kling_client, "get_task_status", return_value=mock_result):
            with pytest.raises(KlingAPIError, match="超时"):
                await kling_client.wait_for_completion(MOCK_TASK_ID, timeout=0.2)


class TestCheckHealth:
    """健康检查测试。"""

    @pytest.mark.asyncio
    async def test_health_ok(self, kling_client: KlingClient) -> None:
        """密钥配置正确时返回 ok。"""
        result = await kling_client.check_health()
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_missing_keys(self) -> None:
        """缺少密钥时返回 error。"""
        client = KlingClient(access_key="", secret_key="")
        result = await client.check_health()
        assert result["status"] == "error"
        assert "未配置" in result["error"]

"""
Kling AI 视频生成客户端 - 封装可灵 API 的鉴权、任务提交和轮询逻辑。

支持 text2video（文生视频）和 image2video（图生视频）两种模式。
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.core.retry import async_retry

logger = logging.getLogger(__name__)


class KlingAuthError(Exception):
    """Kling API 鉴权失败。"""


class KlingAPIError(Exception):
    """Kling API 调用失败。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class KlingClient:
    """
    Kling AI 视频生成客户端。

    用法::

        client = KlingClient()
        # 文生视频
        task_id = await client.submit_text2video("A woman walking in the park")
        # 轮询结果
        result = await client.wait_for_completion(task_id)
        video_url = result["video_url"]
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> None:
        settings = get_settings()
        self._access_key = access_key or settings.KLING_ACCESS_KEY
        self._secret_key = secret_key or settings.KLING_SECRET_KEY
        self._base_url = (base_url or settings.KLING_API_BASE).rstrip("/")
        self._timeout = timeout or settings.KLING_TIMEOUT
        self._poll_interval = poll_interval or settings.KLING_POLL_INTERVAL

    def _generate_jwt(self) -> str:
        """
        生成 Kling API 所需的 JWT Token。

        使用 HMAC-SHA256 签名，有效期 1800 秒。

        Returns:
            JWT Token 字符串。

        Raises:
            KlingAuthError: 密钥未配置。
        """
        if not self._access_key or not self._secret_key:
            raise KlingAuthError("KLING_ACCESS_KEY 或 KLING_SECRET_KEY 未配置")

        import base64

        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        payload = {
            "iss": self._access_key,
            "exp": now + 1800,
            "nbf": now,
        }

        def _b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{header_b64}.{payload_b64}"

        signature = hmac.new(
            self._secret_key.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature_b64 = _b64url(signature)

        return f"{signing_input}.{signature_b64}"

    def _get_headers(self) -> dict[str, str]:
        """构建带鉴权的请求头。"""
        token = self._generate_jwt()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def submit_text2video(
        self,
        prompt: str,
        negative_prompt: str = "",
        duration: str = "5",
        aspect_ratio: str = "16:9",
        mode: str = "std",
        seed: int = -1,
    ) -> str:
        """
        提交文生视频任务。

        Args:
            prompt: 正向提示词（英文）。
            negative_prompt: 反向提示词。
            duration: 视频时长，"5" 或 "10" 秒。
            aspect_ratio: 画面比例，如 "16:9"、"9:16"。
            mode: 生成模式，"std"（标准）或 "pro"（专业）。
            seed: 随机种子，-1 为随机。

        Returns:
            Kling 返回的任务 ID。

        Raises:
            KlingAPIError: API 调用失败。
        """
        actual_seed = seed if seed >= 0 else int(uuid.uuid4().int % 2**32)

        payload: dict[str, Any] = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "seed": actual_seed,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        return await self._submit_task("/kling/v1/videos/text2video", payload)

    async def submit_image2video(
        self,
        prompt: str,
        image_url: str,
        negative_prompt: str = "",
        duration: str = "5",
        mode: str = "std",
        seed: int = -1,
    ) -> str:
        """
        提交图生视频任务。

        Args:
            prompt: 提示词。
            image_url: 参考图片 URL。
            negative_prompt: 反向提示词。
            duration: 视频时长。
            mode: 生成模式。
            seed: 随机种子。

        Returns:
            任务 ID。
        """
        actual_seed = seed if seed >= 0 else int(uuid.uuid4().int % 2**32)

        payload: dict[str, Any] = {
            "prompt": prompt,
            "image_url": image_url,
            "duration": duration,
            "mode": mode,
            "seed": actual_seed,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        return await self._submit_task("/kling/v1/videos/image2video", payload)

    @async_retry()
    async def _submit_task(self, endpoint: str, payload: dict[str, Any]) -> str:
        """
        通用任务提交方法。

        Args:
            endpoint: API 路径。
            payload: 请求体。

        Returns:
            任务 ID。
        """
        url = f"{self._base_url}{endpoint}"
        headers = self._get_headers()

        try:
            client = get_http_client()
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            task_id = data["data"]["task_id"]
            logger.info("Kling 任务已提交: endpoint=%s, task_id=%s", endpoint, task_id)
            return task_id
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:500]
            raise KlingAPIError(
                f"Kling API 返回 {e.response.status_code}: {detail}",
                status_code=e.response.status_code,
            ) from e
        except httpx.ConnectError as e:
            raise KlingAPIError(f"无法连接 Kling API ({self._base_url})") from e
        except KeyError as e:
            raise KlingAPIError(f"Kling API 响应格式异常: 缺少 {e}") from e

    @async_retry()
    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        查询任务状态。

        Args:
            task_id: Kling 任务 ID。

        Returns:
            包含 status、video_url 等字段的字典。
            status 值: "submitted" | "processing" | "succeed" | "failed"
        """
        url = f"{self._base_url}/kling/v1/videos/text2video/{task_id}"
        headers = self._get_headers()

        try:
            client = get_http_client()
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_task_response(data)
        except httpx.HTTPStatusError as e:
            raise KlingAPIError(
                f"查询任务状态失败: {e.response.status_code} {e.response.text[:200]}",
                status_code=e.response.status_code,
            ) from e

    def _parse_task_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        解析 Kling API 任务状态响应。

        Args:
            data: API 返回的 JSON。

        Returns:
            标准化的任务状态字典。
        """
        task_data = data.get("data", {})
        status = task_data.get("task_status", "unknown")

        result: dict[str, Any] = {
            "task_id": task_data.get("task_id", ""),
            "status": status,
            "video_url": None,
            "video_duration": None,
        }

        # 从任务结果中提取视频信息
        task_result = task_data.get("task_result", {})
        videos = task_result.get("videos", [])
        if videos:
            video = videos[0]
            result["video_url"] = video.get("url", "")
            result["video_duration"] = video.get("duration", None)

        return result

    async def wait_for_completion(
        self,
        task_id: str,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        轮询等待视频生成完成。

        使用指数退避策略：初始间隔 poll_interval，每次翻倍，最大 30 秒。

        Args:
            task_id: 任务 ID。
            timeout: 超时秒数，默认使用配置值。

        Returns:
            完成后的任务状态字典（包含 video_url）。

        Raises:
            KlingAPIError: 超时或任务失败。
        """
        deadline = time.time() + (timeout or self._timeout)
        interval = self._poll_interval

        while time.time() < deadline:
            result = await self.get_task_status(task_id)
            status = result["status"]

            if status == "succeed":
                logger.info("Kling 视频生成完成: task_id=%s, url=%s", task_id, result.get("video_url", "")[:80])
                return result

            if status == "failed":
                raise KlingAPIError(f"Kling 视频生成失败: task_id={task_id}")

            # submitted 或 processing，继续等待
            logger.debug("Kling 任务 %s 状态: %s，等待 %.1f 秒", task_id, status, interval)
            await asyncio.sleep(interval)
            interval = min(interval * 2, 30)

        raise KlingAPIError(
            f"Kling 视频生成超时 ({self._timeout}s): task_id={task_id}"
        )

    async def check_health(self) -> dict[str, str]:
        """
        检查 Kling API 是否可用（通过鉴权测试）。

        Returns:
            状态字典。
        """
        if not self._access_key or not self._secret_key:
            return {"status": "error", "error": "KLING_ACCESS_KEY 或 KLING_SECRET_KEY 未配置"}
        try:
            self._generate_jwt()
            return {"status": "ok", "base_url": self._base_url}
        except Exception as e:
            return {"status": "error", "error": str(e)}

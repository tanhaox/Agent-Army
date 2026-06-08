"""
火山引擎 Doubao Seedance 2.0 视频生成客户端。

支持多模态输入（文本、图片、视频、音频），异步任务创建与轮询。
API 文档: https://www.volcengine.com/docs/6791/1399849
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.core.retry import async_retry

logger = logging.getLogger(__name__)

# Seedance 任务状态
SEEDANCE_STATUS_RUNNING = "running"
SEEDANCE_STATUS_SUCCEEDED = "succeeded"
SEEDANCE_STATUS_FAILED = "failed"


class SeedanceError(Exception):
    """Seedance API 调用失败。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SeedanceClient:
    """
    火山引擎 Seedance 2.0 视频生成客户端。

    用法::

        client = SeedanceClient()
        task_id = await client.create_task(
            prompt="一个女孩在公园漫步",
            image_urls=["http://example.com/bg.jpg"],
            duration=5,
        )
        result = await client.wait_for_completion(task_id)
        video_url = result["video_url"]
    """

    API_BASE = "https://ark.cn-beijing.volces.com/api/v3"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        poll_interval: float | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.SEEDANCE_API_KEY
        self._model = model or settings.SEEDANCE_MODEL
        self._timeout = timeout or settings.SEEDANCE_TIMEOUT
        self._poll_interval = poll_interval or settings.SEEDANCE_POLL_INTERVAL

    def _get_headers(self) -> dict[str, str]:
        if not self._api_key:
            raise SeedanceError("SEEDANCE_API_KEY 未配置")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @async_retry()
    async def create_task(
        self,
        prompt: str,
        negative_prompt: str = "",
        image_urls: list[str] | None = None,
        video_urls: list[str] | None = None,
        audio_urls: list[str] | None = None,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        seed: int = -1,
        generate_audio: bool = False,
        watermark: bool = False,
    ) -> str:
        """
        创建 Seedance 视频生成任务。

        Args:
            prompt: 视频生成提示词。
            negative_prompt: 负面提示词（暂未使用）。
            image_urls: 参考图片 URL 列表（最多 9 张）。
            video_urls: 参考视频 URL 列表（最多 3 个）。
            audio_urls: 参考音频 URL 列表（最多 3 个）。
            duration: 视频时长（秒）。
            aspect_ratio: 画面比例，如 "9:16"、"16:9"。
            seed: 随机种子。
            generate_audio: 是否同时生成音频。
            watermark: 是否添加水印。

        Returns:
            Seedance 返回的任务 ID。

        Raises:
            SeedanceError: API 调用失败。
        """
        content_items: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

        # 添加参考图片（带 role 标记）
        for url in (image_urls or [])[:9]:
            content_items.append({
                "type": "image_url",
                "image_url": {"url": url},
                "role": "reference_image",
            })

        # 添加参考视频（带 role 标记）
        for url in (video_urls or [])[:3]:
            content_items.append({
                "type": "video_url",
                "video_url": {"url": url},
                "role": "reference_video",
            })

        # 添加参考音频（带 role 标记，放在 content 内）
        for url in (audio_urls or [])[:3]:
            content_items.append({
                "type": "audio_url",
                "audio_url": {"url": url},
                "role": "reference_audio",
            })

        payload: dict[str, Any] = {
            "model": self._model,
            "content": content_items,
            "ratio": aspect_ratio or "9:16",
            "duration": duration or 5,
            "watermark": watermark,
        }

        if generate_audio:
            payload["generate_audio"] = True

        if seed >= 0:
            payload.setdefault("response_format", {})["seed"] = seed

        url = f"{self.API_BASE}/contents/generations/tasks"
        headers = self._get_headers()

        try:
            client = get_http_client()
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            task_id = data["id"]
            logger.info("Seedance 任务已提交: model=%s, task_id=%s", self._model, task_id)
            return task_id
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:500]
            raise SeedanceError(
                f"Seedance API 返回 {e.response.status_code}: {detail}",
                status_code=e.response.status_code,
            ) from e
        except httpx.ConnectError as e:
            raise SeedanceError(f"无法连接 Seedance API") from e
        except KeyError as e:
            raise SeedanceError(f"Seedance API 响应格式异常: 缺少 {e}") from e

    @async_retry()
    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        查询 Seedance 任务状态。

        Args:
            task_id: Seedance 任务 ID。

        Returns:
            包含 status、video_url 等字段的字典。
        """
        url = f"{self.API_BASE}/contents/generations/tasks/{task_id}"
        headers = self._get_headers()

        try:
            client = get_http_client()
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            raise SeedanceError(
                f"查询 Seedance 任务状态失败: {e.response.status_code} {e.response.text[:200]}",
                status_code=e.response.status_code,
            ) from e

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """解析 Seedance API 任务状态响应。"""
        status = data.get("status", "unknown")
        error_code = data.get("error", {}).get("code", "")
        error_msg = data.get("error", {}).get("message", "")

        result: dict[str, Any] = {
            "task_id": data.get("id", ""),
            "status": status,
            "video_url": None,
            "error": error_msg if error_msg else None,
        }

        # Seedance 成功响应: content.video_url 直接在 content 下
        content = data.get("content", {})
        if isinstance(content, dict):
            video_url = content.get("video_url", "")
            if video_url:
                result["video_url"] = video_url

        return result

    async def wait_for_completion(
        self,
        task_id: str,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        轮询等待视频生成完成。

        Args:
            task_id: 任务 ID。
            timeout: 超时秒数。

        Returns:
            完成后的任务状态字典。

        Raises:
            SeedanceError: 超时或任务失败。
        """
        deadline = time.time() + (timeout or self._timeout)
        interval = self._poll_interval

        while time.time() < deadline:
            result = await self.get_task_status(task_id)
            status = result["status"]

            if status == SEEDANCE_STATUS_SUCCEEDED:
                logger.info(
                    "Seedance 视频生成完成: task_id=%s, url=%s",
                    task_id, str(result.get("video_url", ""))[:80],
                )
                return result

            if status == SEEDANCE_STATUS_FAILED:
                error_detail = result.get("error", "未知错误")
                raise SeedanceError(f"Seedance 视频生成失败: task_id={task_id}, error={error_detail}")

            logger.debug("Seedance 任务 %s 状态: %s，等待 %.1f 秒", task_id, status, interval)
            await asyncio.sleep(interval)
            interval = min(interval * 1.8, 30)

        raise SeedanceError(f"Seedance 视频生成超时 ({self._timeout}s): task_id={task_id}")

    async def check_health(self) -> dict[str, str]:
        """检查 Seedance API 是否可用。"""
        if not self._api_key:
            return {"status": "error", "error": "SEEDANCE_API_KEY 未配置"}
        return {"status": "ok", "model": self._model}

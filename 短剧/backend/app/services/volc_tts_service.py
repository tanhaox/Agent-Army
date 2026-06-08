"""
火山引擎豆包 TTS 大模型语音合成客户端。

使用异步长文本接口（v3），支持最长 10 万字符。
API 文档: https://www.volcengine.com/docs/6561/1829010

流程：submit 提交任务 → query 轮询结果 → 获取 audio_url
"""

import asyncio
import logging
import time
import uuid
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.core.retry import async_retry

logger = logging.getLogger(__name__)

RESOURCE_ID = "volc.service_type.10029"
SUCCESS_CODE = 20000000
TASK_RUNNING = 1
TASK_SUCCESS = 2
TASK_FAILED = 3


class VolcTTSError(Exception):
    """TTS API 调用失败。"""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class VolcTTSClient:
    """
    火山引擎豆包 TTS 异步合成客户端。

    用法::

        client = VolcTTSClient()
        task_id = await client.submit_task("你好世界")
        result = await client.wait_for_completion(task_id)
        audio_url = result["audio_url"]
    """

    BASE_URL = "https://openspeech.bytedance.com"

    def __init__(
        self,
        app_id: str | None = None,
        access_key: str | None = None,
        default_voice: str | None = None,
        fmt: str | None = None,
        sample_rate: int | None = None,
    ) -> None:
        settings = get_settings()
        self._app_id = app_id or settings.VOLC_TTS_APP_ID
        self._access_key = access_key or settings.VOLC_TTS_TOKEN
        self._default_voice = default_voice or settings.VOLC_TTS_DEFAULT_VOICE
        self._format = fmt or settings.VOLC_TTS_FORMAT
        self._sample_rate = sample_rate or settings.VOLC_TTS_SAMPLE_RATE
        self._timeout = settings.VOLC_TTS_TIMEOUT
        self._poll_interval = settings.VOLC_TTS_POLL_INTERVAL

    def _get_headers(self, request_id: str | None = None) -> dict[str, str]:
        if not self._app_id or not self._access_key:
            raise VolcTTSError("VOLC_TTS_APP_ID 和 VOLC_TTS_TOKEN 未配置")
        return {
            "X-Api-App-Id": self._app_id,
            "X-Api-Access-Key": self._access_key,
            "X-Api-Resource-Id": RESOURCE_ID,
            "Content-Type": "application/json",
            **({"X-Api-Request-Id": request_id} if request_id else {}),
        }

    @async_retry()
    async def submit_task(
        self,
        text: str,
        voice_type: str | None = None,
        speed: float = 1.0,
        volume: float = 1.0,
        emotion: str | None = None,
    ) -> str:
        """
        提交异步 TTS 合成任务。

        Args:
            text: 合成文本（最长 10 万字符）。
            voice_type: 音色 ID，默认使用配置中的默认音色。
            speed: 语速倍率 (0.5~2.0)。
            volume: 音量倍率 (0.5~2.0)。
            emotion: 情感（仅部分音色支持），如 "happy", "sad", "angry"。

        Returns:
            任务 ID 字符串。
        """
        speaker = voice_type or self._default_voice
        # 语速/音量映射：1.0 → 0, 2.0 → 100, 0.5 → -50
        speech_rate = round((speed - 1.0) * 100)
        loudness_rate = round((volume - 1.0) * 100)

        audio_params: dict[str, Any] = {
            "format": self._format,
            "sample_rate": self._sample_rate,
            "speech_rate": speech_rate,
            "loudness_rate": loudness_rate,
        }
        if emotion:
            audio_params["emotion"] = emotion

        payload = {
            "user": {"uid": "shortfilm-ai"},
            "req_params": {
                "text": text,
                "speaker": speaker,
                "audio_params": audio_params,
            },
        }

        url = f"{self.BASE_URL}/api/v3/tts/submit"
        headers = self._get_headers(request_id=str(uuid.uuid4()))

        try:
            client = get_http_client()
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise VolcTTSError(f"TTS submit HTTP {e.response.status_code}: {e.response.text[:200]}") from e
        except httpx.ConnectError as e:
            raise VolcTTSError("无法连接火山引擎 TTS 服务") from e

        code = data.get("code")
        if code != SUCCESS_CODE:
            raise VolcTTSError(f"TTS submit 失败: code={code}, msg={data.get('message', '')}", code=code)

        task_id = data["data"]["task_id"]
        logger.info("TTS 任务已提交: task_id=%s, voice=%s, text_len=%d", task_id, speaker, len(text))
        return task_id

    @async_retry(max_attempts=2)
    async def query_task(self, task_id: str) -> dict[str, Any]:
        """
        查询 TTS 任务状态。

        Returns:
            {"status": "running"|"success"|"failed", "audio_url": "...", "task_id": "..."}
        """
        url = f"{self.BASE_URL}/api/v3/tts/query"
        headers = self._get_headers(request_id=str(uuid.uuid4()))
        payload = {"task_id": task_id}

        try:
            client = get_http_client()
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise VolcTTSError(f"TTS query HTTP {e.response.status_code}: {e.response.text[:200]}") from e

        code = data.get("code")
        if code != SUCCESS_CODE:
            raise VolcTTSError(f"TTS query 失败: code={code}, msg={data.get('message', '')}", code=code)

        d = data.get("data", {})
        task_status = d.get("task_status", TASK_FAILED)
        status_map = {TASK_RUNNING: "running", TASK_SUCCESS: "success", TASK_FAILED: "failed"}
        status = status_map.get(task_status, "unknown")

        result: dict[str, Any] = {
            "status": status,
            "task_id": d.get("task_id", task_id),
            "audio_url": d.get("audio_url"),
        }

        if status == "success":
            logger.info("TTS 合成完成: task_id=%s", task_id)
        elif status == "failed":
            logger.error("TTS 合成失败: task_id=%s", task_id)

        return result

    async def wait_for_completion(self, task_id: str, timeout: int | None = None) -> dict[str, Any]:
        """
        轮询等待 TTS 任务完成。

        Args:
            task_id: 任务 ID。
            timeout: 超时秒数。

        Returns:
            成功后的结果字典，包含 audio_url。

        Raises:
            VolcTTSError: 超时或合成失败。
        """
        deadline = time.time() + (timeout or self._timeout)
        interval = self._poll_interval

        while time.time() < deadline:
            result = await self.query_task(task_id)

            if result["status"] == "success":
                return result

            if result["status"] == "failed":
                raise VolcTTSError(f"TTS 合成失败: task_id={task_id}")

            await asyncio.sleep(interval)
            interval = min(interval * 1.3, 10)

        raise VolcTTSError(f"TTS 合成超时 ({self._timeout}s): task_id={task_id}")

    async def generate_speech(
        self,
        text: str,
        voice_type: str | None = None,
        speed: float = 1.0,
        volume: float = 1.0,
    ) -> str:
        """
        同步生成语音（提交 + 轮询）。

        Returns:
            音频下载 URL。
        """
        task_id = await self.submit_task(text, voice_type, speed, volume)
        result = await self.wait_for_completion(task_id)
        audio_url = result.get("audio_url")
        if not audio_url:
            raise VolcTTSError(f"TTS 合成完成但无 audio_url: task_id={task_id}")
        return audio_url

    async def check_health(self) -> dict[str, str]:
        """检查 TTS 配置是否完整。"""
        if not self._app_id or not self._access_key:
            return {"status": "error", "error": "VOLC_TTS_APP_ID 或 VOLC_TTS_TOKEN 未配置"}
        return {"status": "ok", "app_id": self._app_id[:8] + "...", "default_voice": self._default_voice}

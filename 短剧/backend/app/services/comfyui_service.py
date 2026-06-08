"""
ComfyUI 客户端封装 - 通过 HTTP API 调用本地 ComfyUI 生成图片。

ComfyUI 以独立进程运行，后端通过 /prompt + /history 轮询模式获取结果。
"""

import asyncio
import logging
import time
import uuid
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ComfyUIConnectionError(Exception):
    """ComfyUI 服务不可用时抛出。"""


class ComfyUIGenerationError(Exception):
    """图片生成失败时抛出。"""


class ComfyUIClient:
    """
    ComfyUI API 客户端。

    通过提交 workflow JSON 到 /prompt 端点，然后轮询 /history 获取结果。

    用法::
        client = ComfyUIClient()
        image_bytes = await client.generate_image("1girl, high quality")
    """

    def __init__(self, base_url: str | None = None, timeout: int | None = None) -> None:
        settings = get_settings()
        self._base_url: str = (base_url or settings.COMFYUI_BASE_URL).rstrip("/")
        self._timeout: int = timeout or settings.COMFYUI_TIMEOUT

    def _build_txt2img_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 768,
        height: int = 1024,
        seed: int = -1,
    ) -> dict[str, Any]:
        """
        构建标准 txt2img 工作流 JSON。

        使用 SDXL 基础模型的标准节点链：
        KSampler → CLIPTextEncode → VAEDecode → SaveImage

        Args:
            prompt: 正向提示词。
            negative_prompt: 反向提示词。
            width: 图片宽度。
            height: 图片高度。
            seed: 随机种子，-1 为随机。

        Returns:
            ComfyUI 可执行的 workflow JSON。
        """
        actual_seed = seed if seed >= 0 else int(uuid.uuid4().int % 2**32)

        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 7.0,
                    "denoise": 1.0,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": actual_seed,
                    "steps": 20,
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors",
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": height,
                    "width": width,
                },
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": prompt,
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative_prompt,
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2],
                },
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "shortfilm",
                    "images": ["8", 0],
                },
            },
        }

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=8),
    )
    async def _submit_prompt(self, workflow: dict[str, Any]) -> str:
        """
        提交工作流到 ComfyUI。

        Args:
            workflow: 完整的工作流 JSON。

        Returns:
            ComfyUI 返回的 prompt_id。

        Raises:
            ComfyUIConnectionError: 连接失败。
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self._base_url}/prompt",
                    json={"prompt": workflow},
                )
                resp.raise_for_status()
                data = resp.json()
                prompt_id: str = data["prompt_id"]
                logger.info("ComfyUI 任务已提交: prompt_id=%s", prompt_id)
                return prompt_id
        except httpx.ConnectError as e:
            raise ComfyUIConnectionError(
                f"无法连接 ComfyUI ({self._base_url})，请确认已启动"
            ) from e

    async def _poll_result(self, prompt_id: str) -> dict[str, Any]:
        """
        轮询 ComfyUI 历史记录，等待生成完成。

        Args:
            prompt_id: 任务 ID。

        Returns:
            完成后的历史记录 JSON。

        Raises:
            ComfyUIGenerationError: 生成超时或失败。
        """
        start = time.time()
        poll_interval = 2

        while time.time() - start < self._timeout:
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    resp = await client.get(f"{self._base_url}/history/{prompt_id}")
                    if resp.status_code == 200:
                        history = resp.json()
                        if prompt_id in history:
                            status = history[prompt_id].get("status", {})
                            if status.get("completed", False) or status.get("status_str") == "success":
                                logger.info(
                                    "ComfyUI 生成完成: prompt_id=%s, 耗时=%.1fs",
                                    prompt_id,
                                    time.time() - start,
                                )
                                return history[prompt_id]
                            # 检查是否出错
                            if status.get("status_str") == "error":
                                msgs = status.get("messages", [])
                                raise ComfyUIGenerationError(
                                    f"ComfyUI 生成出错: {msgs[:200]}"
                                )
                except httpx.ConnectError:
                    pass

            await asyncio.sleep(poll_interval)

        raise ComfyUIGenerationError(
            f"ComfyUI 生成超时 ({self._timeout}s): prompt_id={prompt_id}"
        )

    async def _download_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """
        从 ComfyUI 输出目录下载生成的图片。

        Args:
            filename: 图片文件名。
            subfolder: 子目录。
            folder_type: 目录类型。

        Returns:
            图片二进制数据。
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self._base_url}/view",
                params={"filename": filename, "subfolder": subfolder, "type": folder_type},
            )
            resp.raise_for_status()
            return resp.content

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 768,
        height: int = 1024,
        seed: int = -1,
    ) -> bytes:
        """
        调用 ComfyUI 生成图片（完整流程）。

        流程：构建工作流 → 提交 → 轮询等待 → 下载图片

        Args:
            prompt: 正向提示词。
            negative_prompt: 反向提示词。
            width: 图片宽度（默认 768，竖屏比例）。
            height: 图片高度（默认 1024）。
            seed: 随机种子。

        Returns:
            图片二进制数据（PNG 格式）。

        Raises:
            ComfyUIConnectionError: 连接失败。
            ComfyUIGenerationError: 生成失败。
        """
        logger.info("ComfyUI 开始生成: prompt前50字=%s", prompt[:50])

        workflow = self._build_txt2img_workflow(prompt, negative_prompt, width, height, seed)
        prompt_id = await self._submit_prompt(workflow)
        history = await self._poll_result(prompt_id)

        # 从历史记录中提取输出图片信息
        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img_info in node_output["images"]:
                    image_data = await self._download_image(
                        filename=img_info["filename"],
                        subfolder=img_info.get("subfolder", ""),
                        folder_type=img_info.get("type", "output"),
                    )
                    logger.info("图片已下载: %d bytes", len(image_data))
                    return image_data

        raise ComfyUIGenerationError("ComfyUI 输出中未找到图片数据")

    async def check_health(self) -> dict[str, str]:
        """
        检查 ComfyUI 服务是否可用。

        Returns:
            包含状态信息的字典。
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/system_stats")
                resp.raise_for_status()
                return {"status": "ok", "url": self._base_url}
        except Exception as e:
            return {"status": "error", "url": self._base_url, "error": str(e)}

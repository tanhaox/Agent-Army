"""
Seedream 5.0 图像生成服务 - 火山引擎 Ark API 封装。

支持：
- text_to_image: 纯文本生成图片
- image_to_image: 参考图 + 文本生成图片（保持角色一致性）
"""

import base64
import logging
import time
from typing import Any

import httpx
from volcenginesdkarkruntime import Ark

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SeedreamConnectionError(Exception):
    """Seedream API 不可用。"""


class SeedreamGenerationError(Exception):
    """图片生成失败。"""


class SeedreamClient:
    """Seedream 5.0 API 客户端。"""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.ARK_API_KEY
        self._model = settings.SEEDREAM_MODEL
        self._size = settings.SEEDREAM_SIZE
        if not self._api_key:
            raise SeedreamConnectionError("ARK_API_KEY 未配置")

    def _get_ark(self) -> Ark:
        return Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=self._api_key,
        )

    def _download(self, url: str) -> bytes:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content

    def _encode_image(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    async def text_to_image(
        self,
        prompt: str,
        size: str | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """
        文本生成图片。

        Returns:
            (图片字节, 元数据字典)
        """
        ark = self._get_ark()
        size = size or self._size
        logger.info("Seedream txt2img: prompt前60字=%s", prompt[:60])
        start = time.time()
        try:
            resp = ark.images.generate(
                model=self._model,
                prompt=prompt,
                sequential_image_generation="disabled",
                response_format="url",
                size=size,
                watermark=False,
                stream=False,
            )
            if not resp.data:
                raise SeedreamGenerationError("无图片返回")
            img = resp.data[0]
            gen_time = time.time() - start
            logger.info("Seedream txt2img 完成: %.2fs, size=%s", gen_time, img.size)
            image_bytes = self._download(img.url)
            metadata = {"generation_time": gen_time, "size": img.size, "model": self._model, "method": "text_to_image"}
            return image_bytes, metadata
        except (SeedreamGenerationError, SeedreamConnectionError):
            raise
        except Exception as e:
            logger.error("Seedream txt2img 失败: %s", e)
            raise SeedreamGenerationError(f"文本生成图片失败: {e}") from e

    async def image_to_image(
        self,
        prompt: str,
        base_image_bytes: bytes,
        size: str | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """
        图片参考生成图片（保持角色一致性）。

        Returns:
            (图片字节, 元数据字典)
        """
        ark = self._get_ark()
        size = size or self._size
        base_b64 = self._encode_image(base_image_bytes)
        logger.info("Seedream img2img: prompt前60字=%s", prompt[:60])
        start = time.time()
        try:
            resp = ark.images.generate(
                model=self._model,
                prompt=prompt,
                image=base_b64,
                sequential_image_generation="disabled",
                response_format="url",
                size=size,
                watermark=False,
                stream=False,
            )
            if not resp.data:
                raise SeedreamGenerationError("无图片返回")
            img = resp.data[0]
            gen_time = time.time() - start
            logger.info("Seedream img2img 完成: %.2fs, size=%s", gen_time, img.size)
            image_bytes = self._download(img.url)
            metadata = {"generation_time": gen_time, "size": img.size, "model": self._model, "method": "image_to_image"}
            return image_bytes, metadata
        except (SeedreamGenerationError, SeedreamConnectionError):
            raise
        except Exception as e:
            logger.error("Seedream img2img 失败: %s", e)
            raise SeedreamGenerationError(f"图片参考生成失败: {e}") from e

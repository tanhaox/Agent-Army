"""
DeepSeek LLM 客户端实现。

使用 OpenAI 兼容 API 调用 DeepSeek 服务，
支持 JSON 模式和自动重试。
"""

import logging

from openai import AsyncOpenAI, APIConnectionError, APIStatusError

from app.core.config import get_settings
from app.services.llm.base import BaseLLMClient, LLMConnectionError, LLMGenerateError

logger = logging.getLogger(__name__)


class DeepSeekClient(BaseLLMClient):
    """
    DeepSeek API 客户端。

    使用 OpenAI SDK 兼容接口调用 DeepSeek。
    支持 JSON 输出模式和指数退避重试。
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            max_retries=2,
            timeout=120.0,
        )
        self._model: str = settings.DEEPSEEK_MODEL

    async def generate(self, prompt: str, system: str = "") -> str:
        """
        调用 DeepSeek 生成文本。

        Args:
            prompt: 用户提示词。
            system: 系统提示词（可选）。

        Returns:
            模型生成的文本内容。
        """
        logger.info("调用 DeepSeek 生成: model=%s, prompt长度=%d", self._model, len(prompt))

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except APIConnectionError as e:
            logger.error("DeepSeek 连接失败: %s", e)
            raise LLMConnectionError(
                f"无法连接 DeepSeek 服务 ({self._model})，请检查网络和 API Key"
            ) from e
        except APIStatusError as e:
            logger.error("DeepSeek 返回错误: status=%s, message=%s", e.status_code, e.message)
            raise LLMGenerateError(
                f"DeepSeek 返回 HTTP {e.status_code}: {e.message[:200]}"
            ) from e

        content = response.choices[0].message.content or ""

        if not content:
            logger.warning("DeepSeek 返回空响应, model=%s", self._model)
            raise LLMGenerateError("DeepSeek 返回了空响应")

        # 过滤可能的 <think/> 思考标签（部分模型会输出）
        import re
        content = re.sub(r"<think[\s\S]*?</think\s*>", "", content).strip()

        logger.info(
            "DeepSeek 生成完成: model=%s, 响应长度=%d",
            response.model or self._model,
            len(content),
        )
        return content

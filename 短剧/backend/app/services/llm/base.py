"""
统一 LLM 客户端抽象基类。

所有 LLM 实现均继承 BaseLLMClient，
服务层通过 get_llm_client() 工厂方法获取具体实现。
"""

from abc import ABC, abstractmethod


class LLMError(Exception):
    """LLM 调用通用错误。"""


class LLMConnectionError(LLMError):
    """无法连接 LLM 服务时抛出。"""


class LLMGenerateError(LLMError):
    """LLM 生成失败时抛出。"""


class BaseLLMClient(ABC):
    """
    LLM 客户端抽象基类。

    所有具体实现必须提供 generate 方法。
    用法::

        client = get_llm_client()
        result = await client.generate("写一段话", system="你是编剧")
    """

    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """
        调用 LLM 生成文本。

        Args:
            prompt: 用户提示词。
            system: 系统提示词（可选）。

        Returns:
            模型生成的文本内容。

        Raises:
            LLMConnectionError: 连接失败。
            LLMGenerateError: 生成失败。
        """

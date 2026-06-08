"""
统一 LLM 客户端包。

提供 get_llm_client() 工厂方法和统一错误类型。
"""

from app.services.llm.base import (
    BaseLLMClient,
    LLMConnectionError,
    LLMError,
    LLMGenerateError,
)
from app.services.llm.factory import get_llm_client, reset_llm_client

__all__ = [
    "BaseLLMClient",
    "get_llm_client",
    "reset_llm_client",
    "LLMError",
    "LLMConnectionError",
    "LLMGenerateError",
]

"""
LLM 客户端工厂。

根据环境变量 LLM_PROVIDER 返回对应的 LLM 客户端实例。
当前仅支持 DeepSeek。
"""

import logging

from app.core.config import get_settings
from app.services.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)

# 模块级缓存，避免每次调用都创建新实例
_client_cache: dict[str, BaseLLMClient] = {}


def get_llm_client() -> BaseLLMClient:
    """
    返回 DeepSeek LLM 客户端实例（带缓存）。

    Returns:
        BaseLLMClient 实例。
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER

    if provider in _client_cache:
        return _client_cache[provider]

    from app.services.llm.deepseek_client import DeepSeekClient
    client = DeepSeekClient()
    logger.info("LLM 客户端: DeepSeek (model=%s)", settings.DEEPSEEK_MODEL)

    _client_cache[provider] = client
    return client


def reset_llm_client() -> None:
    """清除缓存的 LLM 客户端（用于测试或配置热更新）。"""
    _client_cache.clear()

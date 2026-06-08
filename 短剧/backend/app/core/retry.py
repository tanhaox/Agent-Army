"""
异步重试工具 — 基于 tenacity，用于外部 API 调用。

使用方式:
    from app.core.retry import async_retry

    @async_retry
    async def call_external_api(): ...

    # 或自定义配置
    @async_retry(max_attempts=5, max_wait=30)
    async def call_external_api(): ...
"""

import logging

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

import httpx

logger = logging.getLogger(__name__)

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.ConnectTimeout,
    ConnectionError,
    OSError,
)


def async_retry(
    max_attempts: int = 3,
    min_wait: float = 2,
    max_wait: float = 10,
    retryable: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
):
    """
    异步重试装饰器。

    Args:
        max_attempts: 最大重试次数（含首次调用）。
        min_wait: 最小等待时间（秒）。
        max_wait: 最大等待时间（秒）。
        retryable: 可重试的异常类型元组。
    """
    return retry(
        retry=retry_if_exception_type(retryable),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )

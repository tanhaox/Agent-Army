"""
全局 HTTP 客户端单例 — 避免每次请求新建 httpx.AsyncClient。

使用方式:
    from app.core.http_client import get_http_client

    client = get_http_client()
    resp = await client.get(url)
"""

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """获取全局共享的 httpx.AsyncClient 实例。"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=120,
            ),
            follow_redirects=True,
        )
    return _client


async def close_http_client() -> None:
    """关闭全局 HTTP 客户端（在 FastAPI lifespan 中调用）。"""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None

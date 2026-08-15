# -*- coding: utf-8 -*-
"""智谱联网搜索客户端 (2026-08-15) — 素材聚合定向补搜专用.

独立 /web_search 端点 (非旧版 /tools 工具调用):
    POST {base_url}/web_search   Bearer ZHIPU_API_KEY
    {search_query ≤70字符, search_engine, search_intent:false,
     count, content_size, search_recency_filter}

免费额度有到期时间 (config: zhipu.free_quota_expires) — 到期/额度耗尽时
抛出明确中文提示, 不让用户"用着用着忘了"。
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

import requests

from ..config import get_config

logger = logging.getLogger(__name__)

__all__ = ["ZhipuSearchError", "ZhipuUnavailableError", "zhipu_web_search"]

_QUERY_MAX = 70              # OpenAPI maxLength
_RETRYABLE_CODES = {"1701"}  # 并发上限 → 退避重试
_MAX_ATTEMPTS = 3
# 错误信息含这些关键词 → 认定额度/到期问题, 翻译成明确提示
_QUOTA_KEYWORDS = ("额度", "次数", "到期", "余额", "欠费", "套餐", "资源包", "expired")


class ZhipuSearchError(Exception):
    """搜索失败 (网络 / 业务错误码等, 调用方可逐条跳过)."""


class ZhipuUnavailableError(ZhipuSearchError):
    """搜索功能不可用 (key 未配置 / 免费额度到期或耗尽) — 致命中断, 必须提示用户."""


def _quota_message(expires: str) -> str:
    return (
        f"智谱搜索免费额度已用尽或已于 {expires} 到期，"
        "请到 open.bigmodel.cn 控制台查看额度或充值后更换 ZHIPU_API_KEY"
    )


def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return any(kw in message or kw in lowered for kw in _QUOTA_KEYWORDS)


def _parse_search_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    """双形态解析: 优先独立端点 search_result, 回退旧 /tools choices 形态."""
    raw_items = data.get("search_result")
    if not isinstance(raw_items, list):
        # 旧形态防御: choices[0].message.content 里 type=="search_result" 块
        raw_items = []
        choices = data.get("choices") or []
        if choices:
            msg = (choices[0] or {}).get("message") or {}
            content = msg.get("content")
            if isinstance(content, list):
                raw_items = [b for b in content if isinstance(b, dict) and b.get("type") == "search_result"]
    results: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        link = str(item.get("link") or item.get("url") or "").strip()
        if not link:
            # refer 多为引用占位符(ref_1), 只认 http 开头的真 URL
            refer = str(item.get("refer") or "").strip()
            if refer.startswith("http"):
                link = refer
        if not content and not link:
            continue
        results.append({
            "title": str(item.get("title") or "").strip()[:512],
            "link": link[:2048],
            "content": content[:4000],
            "media": str(item.get("media") or "").strip()[:128],
            "publish_date": str(item.get("publish_date") or "").strip()[:32],
        })
    return results


def zhipu_web_search(
    query: str,
    *,
    count: int | None = None,
    content_size: str | None = None,
    recency: str | None = None,
) -> list[dict[str, Any]]:
    """联网搜索, 返回 [{title, link, content, media, publish_date}].

    失败 raise ZhipuSearchError (含 key 未配置/免费额度到期的明确中文提示),
    无结果返回 []. 参数缺省读 config zhipu 节.
    """
    cfg = get_config().zhipu
    if not cfg.api_key:
        raise ZhipuUnavailableError(
            "ZHIPU_API_KEY 未配置，请在 digital_human/.env 填写后重启服务"
            "（open.bigmodel.cn/usercenter/apikeys）"
        )
    # 到期拦截 (用户 2026-08-15 要求: 到期必须明确提示, 防遗忘)
    try:
        if date.today() > date.fromisoformat(cfg.free_quota_expires):
            raise ZhipuUnavailableError(_quota_message(cfg.free_quota_expires))
    except ValueError:
        pass  # 配置日期格式异常不拦截, 走正常调用由服务端裁决

    q = query.strip()[:_QUERY_MAX]
    if not q:
        return []
    url = f"{cfg.base_url.rstrip('/')}/web_search"
    payload = {
        "search_query": q,
        "search_engine": cfg.search_engine,
        "search_intent": False,
        "count": count or cfg.count,
        "content_size": content_size or cfg.content_size,
        "search_recency_filter": recency or cfg.recency,
    }
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }

    last_error = ""
    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_sec)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            last_error = str(exc)
            logger.warning("[zhipu] network error (attempt %d/%d): %s", attempt + 1, _MAX_ATTEMPTS, exc)
            continue
        except ValueError as exc:
            raise ZhipuSearchError(f"智谱搜索响应解析失败: {exc}") from exc

        err = data.get("error")
        if isinstance(err, dict):
            code = str(err.get("code", ""))
            message = str(err.get("message", ""))
            last_error = f"{code}: {message}"
            if _is_quota_error(message):
                raise ZhipuUnavailableError(_quota_message(cfg.free_quota_expires))
            if code in _RETRYABLE_CODES and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise ZhipuSearchError(f"智谱搜索失败: {last_error}")
        return _parse_search_result(data)

    raise ZhipuSearchError(f"智谱搜索网络失败（已重试 {_MAX_ATTEMPTS} 次）: {last_error}")

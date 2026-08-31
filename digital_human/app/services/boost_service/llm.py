# -*- coding: utf-8 -*-
"""通用 LLM 通道 — DeepSeek 主用 / 硅基流动回退, 空 thinking 兜底重试.

被 6+ 模块 lazy import (material_service / entity_extractor / shot_contract /
material_ingest_service / backfill_yt_tags / pipeline) — 事实上的 LLM 基础设施.
拆包自 boost_service.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["_call", "_extract_json", "_resolve_llm_cfg"]


def _resolve_llm_cfg():
    """获取 LLM 配置. 首选 DeepSeek, fallback 硅基流动 (2026-08-22).

    2026-08-22: 硅基流动余额不足返 402 (解构报"解析失败"根因), 弃用为默认;
    与 llm_service / director_service 的 deepseek 主用对齐.
    """
    from app.config import get_config, load_config
    try:
        cfg = get_config()
    except RuntimeError:
        cfg = load_config()
    # DeepSeek 优先
    if cfg.deepseek.api_key:
        return cfg.deepseek
    return cfg.siliconflow


def _post_chat(cfg, model: str, prompt: str, *, json_mode: bool, max_tokens: int,
               temperature: float, enable_thinking: bool) -> str:
    """单次 LLM 请求 → content 文本. 抛异常由调用方处理."""
    import requests
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "stream": False,
        "max_tokens": max_tokens,
        "enable_thinking": enable_thinking,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call(prompt: str, *, json_mode: bool = False, max_tokens: int = 4000, retries: int = 2,
          model: str | None = None, temperature: float = 0.5,
          enable_thinking: bool | None = None) -> str:
    """调用 LLM. 默认 flash; 传 model="pro" 或用洗稿模板时外部指定 model.
    返回文本; 抛异常由调用方处理.

    重试: reasoning 模型偶发空输出/截断, 空响应时重试 up to retries 次.
    temperature: 判定/审计类任务 (素材审计) 传 0.2 求稳定 (2026-08-15).
    2026-08-22: 大 prompt(素材审计~40K)+thinking 关闭 → DeepSeek reasoning 模型
    返回空 content (flash/pro 实测全空; enable_thinking=True 才正常, ~48s)。
    - enable_thinking=True: 单次带 thinking 请求 (素材审计直接用, 跳过空重试)。
    - None (默认): 先 thinking 关 (快路径), 普通重试仍空则补一轮 thinking 开启兜底。
    """
    import time

    cfg = _resolve_llm_cfg()
    resolved = cfg.model_flash if model is None else (cfg.model_pro if model == "pro" else model)
    last_err: Exception | None = None

    if enable_thinking is not None:
        # 显式 thinking 开关: 单次调用 (调用方自带重试, 如审计 3 次循环)
        content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                             max_tokens=max_tokens, temperature=temperature,
                             enable_thinking=enable_thinking)
        if content and content.strip():
            return content
        raise RuntimeError("empty LLM response")

    for attempt in range(retries + 1):
        try:
            content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                                 max_tokens=max_tokens, temperature=temperature,
                                 enable_thinking=False)
            if content and content.strip():
                return content
            last_err = RuntimeError("empty LLM response")
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    # 兜底: 空响应 (thinking 关导致) → 带 thinking 再试一轮, max_tokens 放大
    # (thinking 的 reasoning 占预算, 原 max_tokens 会被耗尽 → content 空; 2026-08-22)
    if last_err is not None and "empty LLM response" in str(last_err):
        try:
            content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                                 max_tokens=max(8000, max_tokens), temperature=temperature,
                                 enable_thinking=True)
            if content and content.strip():
                return content
        except Exception:
            pass
    if last_err:
        raise last_err
    return ""


def _extract_json(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中提取 JSON (容忍前后缀)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None

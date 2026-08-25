"""LLM service for article rewriting."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Literal

import requests

from ..config import DeepSeekConfig

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "你是一位资深财经短视频编剧。"
    "请将用户提供的财经新闻改写成适合数字人口播的短视频脚本，"
    "要求语言口语化、有节奏感、适合中文 TTS 朗读。"
)


def _load_prompt_template(prompt_template: str | None) -> str:
    """Load prompt template from config/ if a name is provided, otherwise return as-is."""
    if not prompt_template:
        return DEFAULT_SYSTEM_PROMPT
    # If it contains instructions already, use directly.
    if len(prompt_template) > 80 and ("你" in prompt_template or "请" in prompt_template):
        return prompt_template
    from ..config import PROJECT_ROOT

    candidate = PROJECT_ROOT / "config" / f"{prompt_template}.txt"
    if candidate.exists():
        base = candidate.read_text(encoding="utf-8").strip()
        # 2026-08-22: 全系统统一限流词注入 (config/compliance_common.json — 拆书/新闻线/未来系统共用)
        try:
            from .compliance import build_redline_prompt
            base += "\n\n" + build_redline_prompt()
        except Exception:
            pass
        return base
    return prompt_template


class LLMService:
    """LLM 客户端: 包装 DeepSeek chat/completions.

    connection-level 重试只针对 "请求还没发出去/连接建立失败" 的错误
    (requests.ConnectionError / 超时), 不重试 HTTP 4xx/5xx — 后者
    在 stream=True 时可能已吐出部分内容, 重发会重复。
    """
    # 远端连接抖动/长连接被重置时重试 (10054/10060/11001 等)
    _RETRYABLE = (requests.ConnectionError, requests.Timeout)
    _MAX_RETRIES = 2
    _BACKOFF_SEC = 2.0

    def __init__(self, cfg):
        self.cfg = cfg

    def _post_with_retry(self, url, *, headers, json, stream, timeout=120):
        """POST with connection-level retry. 见类 docstring 的重试范围约定."""
        last_exc = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                return requests.post(url, headers=headers, json=json, stream=stream, timeout=timeout)
            except self._RETRYABLE as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    delay = self._BACKOFF_SEC * (2 ** attempt)
                    logger.warning(
                        "[llm] connection error (attempt %d/%d): %s — retry in %.1fs",
                        attempt + 1, self._MAX_RETRIES + 1, exc, delay,
                    )
                    time.sleep(delay)
        raise last_exc

    def _resolve_model(self, model: str | None) -> str:
        """Resolve 'flash'/'pro' aliases or pass through a concrete model name."""
        if model is None:
            model = self.cfg.default_model
        aliases = {"flash": self.cfg.model_flash, "pro": self.cfg.model_pro}
        return aliases.get(model, model)

    def chat(self, system: str, user: str, model: str | None = None,
             temperature: float = 0.7, timeout: int = 300,
             max_tokens: int | None = None,
             response_format: dict[str, Any] | None = None) -> str:
        """通用单轮对话 (非流式) — 拆书编排等结构化调用入口.

        timeout 默认 300s: pro 长稿生成常超 120s。
        max_tokens/response_format (2026-08-25): 可选注入 — 结构化调用方(director 工序单)
        此前不设上限, 长稿输出截断 = JSON 解析失败 = job 报废。
        """
        if not self.cfg.api_key:
            raise RuntimeError(
                "DeepSeek API key is not configured. "
                "Set the DEEPSEEK_API_KEY environment variable before starting the server."
            )
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        response = self._post_with_retry(url, headers=headers, json=payload,
                                         stream=False, timeout=timeout)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def rewrite_article(
        self,
        raw_text: str,
        prompt_template: str | None = None,
        model: str | None = None,
        stream: bool = True,
        chunk_callback: Callable[[str], None] | None = None,
        perspective: str | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Rewrite raw article into broadcast script.

        Args:
            raw_text: The original article text.
            prompt_template: Optional override prompt template name or raw prompt.
            model: 'flash', 'pro', or a concrete model name.
            stream: Whether to stream response.
            chunk_callback: Called with each content chunk when streaming.
            perspective: Optional user perspective injected before rewrite.
            max_tokens/response_format (2026-08-25): 可选注入, 供结构化调用方(director 工序单)防截断。
        """
        system = _load_prompt_template(prompt_template)

        # 构建 user message: 有观点时前置补充观点
        if perspective and perspective.strip():
            user_content = f"【原作者补充观点】\n{perspective.strip()}\n\n【原文】\n{raw_text}"
        else:
            user_content = raw_text

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }

        if not self.cfg.api_key:
            raise RuntimeError(
                "DeepSeek API key is not configured. "
                "Set the DEEPSEEK_API_KEY environment variable before starting the server."
            )
        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        response = self._post_with_retry(url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        if not stream:
            data = response.json()
            return data["choices"][0]["message"]["content"]

        full_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[len("data: "):].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                full_text += delta
                if chunk_callback:
                    chunk_callback(delta)
        return full_text

    def correct_article(
        self,
        rewritten_text: str,
        perspective: str,
        prompt_template: str | None = None,
        model: str | None = None,
        stream: bool = True,
        chunk_callback: Callable[[str], None] | None = None,
    ) -> str:
        """根据用户修正观点调整已洗稿脚本。

        与 rewrite 不同: 输入是洗稿结果 + 修正观点，目标是微调而非重写。
        """
        system = _load_prompt_template(prompt_template)
        # 在 system 后追加修正指令 (2026-08-11 加强: 防止 LLM 重写导致内容缩水)
        system += (
            "\n\n【重要】用户对洗稿结果提出了修正意见。"
            "你的任务是**在保留完整稿子的前提下，只修改与修正观点相关的句子**。"
            "\n\n【硬性约束】"
            "\n1. 必须输出【修正后的完整稿】，一行都不能少，禁止删段、禁止压缩、禁止精简。"
            "\n2. 只改与修正观点直接相关的句子（措辞/语气/事实），其余句子**原样保留**，一字不改。"
            "\n3. 全文句数、段落数必须与输入稿**一致**，不得合并或拆分句子。"
            "\n4. 保持原有的语言风格、节奏和结构。"
            "\n5. 若修正观点与稿子无关，直接原样输出输入稿，不做任何改动。"
        )

        user_content = f"【修正观点】\n{perspective.strip()}\n\n【洗稿结果】\n{rewritten_text}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": stream,
            "temperature": 0.6,  # 修正用稍低温度，保持连贯
        }

        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }

        if not self.cfg.api_key:
            raise RuntimeError(
                "DeepSeek API key is not configured. "
                "Set the DEEPSEEK_API_KEY environment variable before starting the server."
            )
        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        response = self._post_with_retry(url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()

        if not stream:
            data = response.json()
            return data["choices"][0]["message"]["content"]

        full_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[len("data: "):].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                full_text += delta
                if chunk_callback:
                    chunk_callback(delta)
        return full_text

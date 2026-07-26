"""LLM service for article rewriting."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Literal

import requests

from ..config import DeepSeekConfig


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
        return candidate.read_text(encoding="utf-8").strip()
    return prompt_template


class LLMService:
    def __init__(self, cfg: DeepSeekConfig):
        self.cfg = cfg

    def _resolve_model(self, model: str | None) -> str:
        """Resolve 'flash'/'pro' aliases or pass through a concrete model name."""
        if model is None:
            model = self.cfg.default_model
        aliases = {"flash": self.cfg.model_flash, "pro": self.cfg.model_pro}
        return aliases.get(model, model)

    def rewrite_article(
        self,
        raw_text: str,
        prompt_template: str | None = None,
        model: str | None = None,
        stream: bool = True,
        chunk_callback: Callable[[str], None] | None = None,
    ) -> str:
        """Rewrite raw article into broadcast script.

        Args:
            raw_text: The original article text.
            prompt_template: Optional override prompt template name or raw prompt.
            model: 'flash', 'pro', or a concrete model name.
            stream: Whether to stream response.
            chunk_callback: Called with each content chunk when streaming.
        """
        system = _load_prompt_template(prompt_template)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": raw_text},
        ]

        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        response = requests.post(url, headers=headers, json=payload, stream=stream, timeout=120)
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

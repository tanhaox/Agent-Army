"""JSON 提取 — 从 LLM 输出中抽取第一个 JSON 对象/数组.

行为逐字迁移自原 director_parser.py (2026-08-08 包化重构).
"""
from __future__ import annotations

import json
import re
from typing import Any

__all__ = ["extract_json"]


def _strip_code_fence(text: str) -> str:
    """移除首尾 ``` 代码围栏(若有)."""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_json(text: str) -> Any:
    """Extract the first JSON object or array from LLM output."""
    text = _strip_code_fence(text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # LLM 可能把 JSON 混在解释文字里，尝试提取第一个对象或数组
    for start_ch, pattern in (("{", r"\{.*\}"), ("[", r"\[.*\]")):
        idx = text.find(start_ch)
        if idx == -1:
            continue
        match = re.search(pattern, text[idx:], re.DOTALL)
        if match:
            return json.loads(match.group(0))
    return json.loads(text)

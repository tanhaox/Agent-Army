# -*- coding: utf-8 -*-
"""全系统统一禁用词/限流词服务 (2026-08-22) — 拆书/新闻线/未来衍生系统共用.

唯一事实源: config/compliance_common.json (categories: 绝对化/医疗/迷信/金融/引流/承诺).
入口:
- load_common_rules()       读词库
- build_redline_prompt()    组装成生成提示词注入块 (源头规避, LLM 生成时就避开)
- check_text(text)          检测文本命中违禁词 (生成后检查兜底)

用法示例:
- 拆书: orchestrator.GateB / facing-units prompt 注入 build_redline_prompt()
- 新闻线: articles.rewrite 加载模板后注入
- 未来系统: 直接 import compliance 服务, 禁止词功能自动赋能
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_COMMON_PATH = Path(__file__).resolve().parents[2] / "config" / "compliance_common.json"

_cache: dict | None = None


def load_common_rules() -> dict:
    """读 config/compliance_common.json (带缓存)."""
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_COMMON_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("[compliance] 公共限流词库加载失败: %s", exc)
            _cache = {"categories": {}}
    return _cache


def _all_banned(categories: list[str] | None = None) -> list[str]:
    """聚合指定类别(默认全部)的禁用词."""
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    out: list[str] = []
    for k in keys:
        ban = (rules.get(k) or {}).get("ban") or []
        out.extend(str(w) for w in ban)
    return list(dict.fromkeys(out))  # 去重保序


def _all_replaces(categories: list[str] | None = None) -> dict[str, str]:
    """类别 → 替换建议."""
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    return {k: (rules.get(k) or {}).get("replace", "") for k in keys}


def build_redline_prompt(categories: list[str] | None = None) -> str:
    """组装成生成提示词注入块 — LLM 生成时就规避 (源头).

    返回多行文本, 可直接拼到任何生成 prompt (拆书 facing/逐集、新闻线洗稿).
    """
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    lines = ["【平台禁用词 · 全系统红线 · 生成时必规避, 出现即违规】"]
    for k in keys:
        cat = rules.get(k) or {}
        ban = "、".join(str(w) for w in (cat.get("ban") or [])[:12])
        repl = cat.get("replace", "")
        lines.append(f"- 禁{cat.get('label', k)}: {ban}（→ {repl}）")
    lines.append("- 全篇用'个人感受+参考建议'的温和表达, 禁绝对化/医疗承诺/迷信/金融收益/站外引流。")
    return "\n".join(lines)


def check_text(text: str, categories: list[str] | None = None) -> list[str]:
    """检测文本命中违禁词 (生成后检查兜底). 返回命中词列表."""
    if not text:
        return []
    banned = _all_banned(categories)
    hits = [w for w in banned if w and w in text]
    return hits


def build_check_prompt(categories: list[str] | None = None) -> str:
    """组装成审计/检测 prompt — 供 LLM 或代码检查生成内容."""
    return build_redline_prompt(categories)

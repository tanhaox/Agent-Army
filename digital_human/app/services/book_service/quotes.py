# -*- coding: utf-8 -*-
"""书摘金句选句 (2026-09-05, B-Q1 卡内容层).

规则 (用户令):
- 每集 3 句, 全书 6 集共 18 句不重复;
- 句长 ≥12 字 (L0 池最短 9 字, ≥12 字 92 句 — 调查在册);
- 句子必须逐字来自 L0 蒸馏「可引用原句」池 (零幻觉, 不经 LLM 改写)。

选法 = 确定性: 集脚本文本与池句的字符二元组重合度打分 (集口播引用/讨论过的
句子天然高分 = 主题契合), 已被其他集用过的句子排除。锈红关键短语 = 句内
首个 5~14 字子句 (无则不高亮) — 不依赖 LLM。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import BookProject, Episode

logger = logging.getLogger(__name__)

__all__ = ["load_quote_pool", "ensure_episode_quotes", "_QUOTE_MIN_CHARS"]

_QUOTE_MIN_CHARS = 12
_POOL_SECTION_RE = re.compile(r"###\s*可引用原句(.*?)\n## ", re.S)
_SENT_SPLIT = re.compile(r"[。！？；]")


def _visible_len(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def load_quote_pool(book: BookProject) -> list[str]:
    """L0 蒸馏 txt「可引用原句」节 → 去空白校验后的句池 (≥12 字, 去重)."""
    src = book.source_path
    if not src or not Path(src).exists():
        logger.warning("[book-quotes] L0 源缺失: %s", src)
        return []
    text = Path(src).read_text(encoding="utf-8", errors="ignore")
    m = _POOL_SECTION_RE.search(text)
    if not m:
        logger.warning("[book-quotes] 蒸馏txt 无「可引用原句」节: %s", src)
        return []
    quotes: list[str] = []
    seen: set[str] = set()
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("*"):
            continue
        q = line.lstrip("* ").strip()
        if _visible_len(q) < _QUOTE_MIN_CHARS:
            continue
        key = re.sub(r"[\s，。、；：！？''\"\"]", "", q)
        if key in seen:
            continue
        seen.add(key)
        quotes.append(q)
    return quotes


def _bigrams(s: str) -> set[str]:
    s = re.sub(r"\s", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _pick_key_phrase(q: str) -> str:
    """锈红关键短语: 首个 5~14 字子句 (确定性, 无则空)."""
    for clause in re.split(r"[，。！？；、]", q):
        c = clause.strip()
        if 5 <= len(c) <= 14:
            return c
    return ""


def _score(quote: str, script_bg: set[str]) -> float:
    qbg = _bigrams(quote)
    if not qbg:
        return 0.0
    return len(qbg & script_bg) / len(qbg)


def ensure_episode_quotes(db: Session, book: BookProject, ep: Episode) -> list[dict[str, Any]]:
    """取/选本集 3 句金句 (quotes_json 已有直接返回; 缺则确定性选取落库)."""
    existing = ep.quotes_json or []
    if isinstance(existing, list) and len(existing) >= 3:
        return existing[:3]
    pool = load_quote_pool(book)
    if not pool:
        return []
    used: set[str] = set()
    for other in db.query(Episode).filter(Episode.book_id == book.id).all():
        if other.id == ep.id:
            continue
        for item in (other.quotes_json or []):
            if isinstance(item, dict) and item.get("text"):
                used.add(re.sub(r"\s", "", str(item["text"])))
    script_text = ep.script_text or ""
    sbg = _bigrams(script_text) if script_text else set()
    ranked = sorted(
        ((q, _score(q, sbg)) for q in pool if re.sub(r"\s", "", q) not in used),
        key=lambda t: t[1], reverse=True,
    )
    if len(ranked) < 3:
        logger.warning("[book-quotes] 池可用句不足 3 (剩 %d)", len(ranked))
        return []
    picked = [{"text": q, "key": _pick_key_phrase(q)} for q, _ in ranked[:3]]
    ep.quotes_json = picked
    db.commit()
    logger.info("[book-quotes] ep%d 选句完成: %s", ep.ep_index,
                " / ".join(q["text"][:12] for q in picked))
    return picked

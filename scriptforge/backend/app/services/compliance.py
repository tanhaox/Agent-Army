import ahocorasick
import asyncio
import logging
import re
import unicodedata

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.sensitive_word import SensitiveWord

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """全角转半角、去除零宽字符，统一用于匹配。"""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"[​‌‍﻿]", "", text)


class ComplianceChecker:
    def __init__(self):
        self._automaton: ahocorasick.Automaton | None = None
        self._words_meta: dict[str, dict] = {}
        self._loaded = False

    async def _ensure_loaded(self):
        if not self._loaded:
            await self.reload()

    async def reload(self):
        """从数据库重新加载敏感词并构建自动机。"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(SensitiveWord).where(SensitiveWord.is_active.is_(True))
            )
            words = result.scalars().all()

        auto = ahocorasick.Automaton()
        meta: dict[str, dict] = {}

        for w in words:
            key = _normalize(w.word).lower()
            auto.add_word(key, key)
            meta[key] = {
                "original": w.word,
                "category": w.category or "未分类",
                "severity": w.severity,
            }

        auto.make_automaton()
        self._automaton = auto
        self._words_meta = meta
        self._loaded = True
        logger.info("ComplianceChecker loaded %d sensitive words", len(meta))

    def check(self, text: str) -> dict:
        """扫描文本，返回命中结果。"""
        if not self._loaded or self._automaton is None:
            return {"passed": True, "hits": [], "hit_count": 0, "suggestion": ""}

        normalized = _normalize(text).lower()
        hits: list[dict] = []

        for end_idx, key in self._automaton.iter(normalized):
            meta = self._words_meta[key]
            start_idx = end_idx - len(key) + 1
            hits.append({
                "word": meta["original"],
                "category": meta["category"],
                "severity": meta["severity"],
                "position": start_idx,
            })

        # 去重（同一词在同一位置可能重复匹配）
        seen: set[tuple[str, int]] = set()
        unique_hits = []
        for h in hits:
            k = (h["word"], h["position"])
            if k not in seen:
                seen.add(k)
                unique_hits.append(h)

        passed = len(unique_hits) == 0
        high_severity = [h for h in unique_hits if h["severity"] == "high"]

        suggestion = ""
        if not passed:
            if high_severity:
                suggestion = f"检测到 {len(high_severity)} 个高危违禁词，强烈建议修改后再使用"
            else:
                suggestion = f"检测到 {len(unique_hits)} 个敏感词，建议酌情修改"

        return {
            "passed": passed,
            "hits": unique_hits,
            "hit_count": len(unique_hits),
            "suggestion": suggestion,
        }

    def filter(self, text: str) -> str:
        """将命中的敏感词替换为 ***。"""
        if not self._loaded or self._automaton is None:
            return text

        normalized = _normalize(text).lower()
        # 收集所有命中的原词及其在原文本中的位置
        replace_ranges: list[tuple[int, int]] = []

        for end_idx, key in self._automaton.iter(normalized):
            start_idx = end_idx - len(key) + 1
            replace_ranges.append((start_idx, end_idx + 1))

        if not replace_ranges:
            return text

        # 合并重叠区间
        replace_ranges.sort()
        merged = [replace_ranges[0]]
        for start, end in replace_ranges[1:]:
            if start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        # 按从后往前的顺序替换，避免偏移
        result = list(text)
        offset = 0
        # 映射到原文本需要使用 normalized 版本的索引
        # 简化处理：直接在原文本上按字符索引替换
        norm_chars = list(normalized)
        orig_chars = list(text)

        # 使用 normalized 文本重建（简化方案）
        parts = []
        last = 0
        for start, end in merged:
            parts.append(text[last:start])
            parts.append("*" * (end - start))
            last = end
        parts.append(text[last:])

        return "".join(parts)


compliance_checker = ComplianceChecker()

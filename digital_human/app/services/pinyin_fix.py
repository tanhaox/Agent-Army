"""TTS 拼音纠音 (2026-08-25) — 两类读音问题, 两种机制:

1. **永久词表** (config/tts_pinyin_map.json): TTS **恒定读错**的字 — 生僻字/专名
   (磷化铟的"铟"、昇腾的"昇")。零语境歧义, 记词表一劳永逸。
2. **临时标注**: 多音字 ("行"/"着"/"卡") 依赖语境, 模型偶发读错 — **不进词表**
   (会把偶发错误固化成系统性错误), 需要时在稿子里手写 ``<行|HANG2>`` 当次生效,
   由 ``strip_pinyin_marks`` 在字幕/显示层剥离, 只有 TTS 读到标注。

- 注入点: tts_service 拼 TTS 输入时 ``apply_pinyin_marks`` (词表 + 手写标注透传
  + 型号连字符守卫 GPT-6→GPT六, 2026-09-04)
- 引擎边界 (tts_lib/engines.py, 2026-09-03): IndexTTS2 只认**裸内联拼音** (拼音代替
  字, 官方测例 "受不liao3你了"), 不认 <字|PINYIN> — 协议原样发会被 BPE 切成
  [字, |, PINYIN] 字拼音各读一遍 (蛤蟆先生 PPT 实听实锤)。indextts 边界转
  ``<蛤|HA2> → HA2 ``; fish/f5 无拼音能力剥回裸字。repo 内部协议不变。
- 剥离点: wash_subtitle_text (J线字幕) / hf_extract / 文稿导出 — 观众可见文本全剥离
- 审计点: boost (爆品改造) 尾部 ``scan_pinyin_hits`` — SSE 提示命中词
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = ["apply_pinyin_marks", "normalize_model_hyphens", "scan_pinyin_hits", "strip_pinyin_marks"]

_MAP_PATH = Path(__file__).resolve().parents[2] / "config" / "tts_pinyin_map.json"

# 已标注形态 <字|PINYIN> (1~4 个非空白字符 + | + 拼音声调)
_MARKED_RE = re.compile(r"<(\S{1,4})\|[A-Z]+[1-5]>")

# ── 型号连字符守卫 (2026-09-04): GPT-6 → GPT六 ──
# IndexTTS2 把字母↔数字之间的连字符读成「负」(GPT-6 → GPT负六)。词表是字级拼音
# 标注管不了符号; 洗稿/适配提示词有禁令但 LLM 常把 GPT-6 归入"英文品牌名 1:1 保留"
# 漏转。此处 TTS 输入侧确定性兜底: 删连字符 + 数字转逐位中文 (B-52→B五二 同口径)。
# 只动字母↔数字接合处: 日期区间 (2024-2025)、中文词 (A-B→A到B)、纯英文短语
# (state-of-the-art) 均不碰, 归 LLM 适配层。
_HYPHEN_MODEL_RE = re.compile(r"([A-Za-z])-([0-9](?:[0-9.]*[0-9])?)")   # GPT-6 / B-52 / GLM-4.5
_HYPHEN_DIGIT_LETTER_RE = re.compile(r"([0-9])-([A-Za-z])")             # o3-mini → o三mini
_CN_DIGITS = {str(d): cn for d, cn in enumerate("零一二三四五六七八九")} | {".": "点"}


def normalize_model_hyphens(text: str) -> str:
    """删除型号连字符并把紧邻数字转逐位中文 (仅字母↔数字接合处); 无连字符原样返回."""
    if "-" not in text:
        return text
    text = _HYPHEN_MODEL_RE.sub(lambda m: m.group(1) + _digits_to_cn(m.group(2)), text)
    text = _HYPHEN_DIGIT_LETTER_RE.sub(lambda m: _CN_DIGITS[m.group(1)] + m.group(2), text)
    return text


def _digits_to_cn(s: str) -> str:
    return "".join(_CN_DIGITS.get(c, c) for c in s)


@lru_cache(maxsize=1)
def _rules() -> dict[str, str]:
    """加载词表 {原词: 标注写法}; 文件缺失/损坏返回空表 (功能静默降级)."""
    try:
        data = json.loads(_MAP_PATH.read_text(encoding="utf-8"))
        rules = data.get("rules") or {}
        if isinstance(rules, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in rules.items()):
            return rules
    except Exception:
        logger.warning("[pinyin_fix] 词表加载失败, 跳过纠音: %s", _MAP_PATH, exc_info=True)
    return {}


def scan_pinyin_hits(text: str) -> list[str]:
    """返回文本中命中的易错词列表 (去重保序), 供 boost 审计提示."""
    seen: list[str] = []
    for word in _rules():
        if word in text and word not in seen:
            seen.append(word)
    return seen


def apply_pinyin_marks(text: str) -> str:
    """TTS 输入终态规整: 先型号连字符守卫 (GPT-6→GPT六), 再词表命中替换为标注写法.

    已含标注 (含手写临时标注, 防重入) 时跳过词表替换; 未命中原样返回."""
    if not text:
        return text
    text = normalize_model_hyphens(text)
    if _MARKED_RE.search(text):
        return text
    out = text
    for word, marked in _rules().items():
        if word in out:
            out = out.replace(word, marked)
    return out


def strip_pinyin_marks(text: str) -> str:
    """剥离 ``<字|PINYIN>`` 标注还原裸字 — 字幕/显示层出口用, 观众只见纯文本."""
    if not text:
        return text
    return _MARKED_RE.sub(r"\1", text)

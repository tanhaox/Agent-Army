"""HF 口播文本提取: 标题/副题/metrics/chart 从分句中抽取.

对应 H 线 (hf_chart / hf_title) 的文本侧; 图表归一化见 hf_chart.py。
"""
from __future__ import annotations

import re

__all__ = [
    "_extract_hf_content",
    "_clean_fragment",
    "_pick_title",
    "_extract_numbers",
    "_score_metrics",
]

# 情绪标签 (用于从分句中剥离 [情绪] 标记)
_EMOTION = r"(?:情绪|serious|calm|happy|sad|angry|opening|rising|climax|falling|closing)"
# 开场白/口头禅前缀 (host 段文本误喂给标题卡时, 不让"大家好"上屏)
_OPENING_PREFIX = r"^(?:大家好|各位朋友|各位观众|哈喽|你好|hello|我是老陈|老陈)[，,。\.、]?"


def _clean_fragment(s: str) -> str:
    """Strip [情绪] markers and whitespace from a text fragment."""
    s = re.sub(rf"\[{_EMOTION}\]", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def _pick_title(chunks: list[str], title_max: int) -> str:
    """Pick a title from chunks: first, or first non-prefix later chunk."""
    title = _clean_fragment(chunks[0])
    title = re.sub(_OPENING_PREFIX, "", title)
    # 若首句只剩开场白(去前缀后为空), 顺延用后续分句做标题
    if not title:
        for nxt in chunks[1:]:
            cand = _clean_fragment(nxt)
            cand = re.sub(_OPENING_PREFIX, "", cand)
            if cand:
                title = cand
                break
    # 截断: 优先停在完整分句(最后一个不超上限的标点), 避免"叫生存空"式残句
    if len(title) > title_max:
        last = 0
        for m in re.finditer(r"[，。！？,\.!?]", title):
            if m.end() <= title_max:
                last = m.end()
            else:
                break
        title = title[:last] if last else title[:title_max]
    return title


def _extract_numbers(chunks: list[str]) -> tuple[list[dict], list[dict]]:
    """Extract (metrics, chart_items) across all text chunks.

    metric: {label, value, priority}; chart item: {label, value(float)}.
    Only %-valued numbers become chart items; all numbers become metrics.
    label is the chunk prefix (up to 20 chars); metrics dedup by label+value.
    """
    metrics: list[dict] = []
    chart_items: list[dict] = []
    seen: set[str] = set()
    for c in chunks:
        nums = re.findall(r"(-?\d+(?:\.\d+)?)\s*(%|万亿|亿|万|千|元|倍|个|点|岁)?", c)
        for val, unit in nums:
            label = c[:20]
            value_text = f"{val}{unit}".strip()
            if unit == "%":
                chart_items.append({"label": label, "value": float(val)})
            dedup = f"{label}|{value_text}"
            if dedup not in seen:
                seen.add(dedup)
                metrics.append({"label": label, "value": value_text, "priority": 1 if unit == "%" else 0})
            if len(metrics) >= 4 and len(chart_items) >= 5:
                return metrics, chart_items
        if len(metrics) >= 4 and len(chart_items) >= 5:
            break
    return metrics, chart_items


def _score_metrics(metrics: list[dict]) -> list[dict]:
    """Sort by priority (%-values first) and set emphasis on the %-leader."""
    metrics.sort(key=lambda m: -m.pop("priority", 0))
    for m in metrics:
        m.setdefault("emphasis", False)
    if metrics and metrics[0].get("value") and "%" in metrics[0]["value"]:
        metrics[0]["emphasis"] = True
    return metrics


def _extract_hf_content(text: str, title_max: int = 16) -> dict:
    """从口播文本提取标题卡内容 (2026-08-01, 修复黑底白字标题卡根因).

    HF 标题卡模板 (news-magazine-v1) 有大标题/副题/metrics/chart 设计,但此前
    把整句口播(含 || 停顿符)硬塞进 title,metrics/chart 用口播占位垃圾填充,
    导致渲染结果=黑底一行白字。本函数:
      - title: 只取首个分句,压到 title_max 字内(模板 108px 标题,过长会溢出);
      - subtitle: 取第 2 个分句(有内容时),替代空副题;
      - metrics: 抽取分句中的真实数字(优先),抽不到则跳过(模板 layout 会删空行);
                带 % 的数值也进 metrics(2026-08-01 问题1修复: 无图表数据时也有文字展示);
      - chart: 带 % 的数值构造图表 items,与 metrics 互补(文字+图表双轨).

    返回 dict: {title, subtitle, metrics, chart} 全部为模板友好结构。
    """
    text = (text or "").strip()
    chunks = [c.strip() for c in re.split(r"\|\||\n", text) if c.strip()]
    if not chunks:
        return {"title": "数据展示", "subtitle": "", "metrics": [], "chart": {"type": "bar", "items": []}}

    title = _pick_title(chunks, title_max)
    subtitle = _clean_fragment(chunks[1])[:32] if len(chunks) > 1 else ""

    metrics, chart_items = _extract_numbers(chunks)

    return {
        "title": title or "数据展示",
        "subtitle": subtitle,
        "metrics": _score_metrics(metrics)[:4],
        "chart": {"type": "bar", "unit": "", "items": chart_items[:5]},
    }

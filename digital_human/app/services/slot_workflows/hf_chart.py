"""HF 图表归一化: render_config 数据 → 统一 chart 结构.

对应 H 线 (hf_chart) 的图表侧; 口播文本提取见 hf_extract.py。
"""
from __future__ import annotations

import re

__all__ = [
    "_normalize_chart_input",
    "_coerce_items",
    "_chart_fallback",
    "_apply_chart_metadata",
]


def _coerce_items(data) -> list[dict]:
    """Coerce render_config.data (dict-value / bare-number lists) → items."""
    items: list[dict] = []
    if not isinstance(data, list):
        return items
    for i, d in enumerate(data, start=1):
        if isinstance(d, dict) and d.get("value") is not None:
            try:
                items.append({"label": str(d.get("label") or f"数据{i}")[:20], "value": float(d["value"])})
            except (ValueError, TypeError):
                continue
        else:
            try:
                items.append({"label": f"数据{i}", "value": float(d)})
            except (ValueError, TypeError):
                continue
    return items


def _chart_fallback(render_config: dict, chart: dict) -> list[dict]:
    """Fallback items: render_config.chart.items → extracted chart items."""
    items: list[dict] = []
    rc_chart = render_config.get("chart")
    src_items = rc_chart.get("items") if isinstance(rc_chart, dict) else None
    if not src_items:
        src_items = chart.get("items") or []
    for it in src_items:
        if isinstance(it, dict) and it.get("value") is not None:
            try:
                items.append({"label": str(it.get("label") or "数据")[:20], "value": float(it["value"])})
            except (ValueError, TypeError):
                continue
    return items


def _apply_chart_metadata(chart: dict, render_config: dict) -> dict:
    """补全 unit/growth/color_scheme/label; pie 单扇区时补"其他"扇区."""
    for k in ("unit", "growth", "color_scheme"):
        if render_config.get(k):
            chart[k] = str(render_config[k])
        elif not chart.get(k):
            chart[k] = ""
    if render_config.get("label"):
        chart["label"] = str(render_config["label"])
    elif not chart.get("label"):
        chart["label"] = ""

    # pie 至少保留 2 扇区: 若只有 1 项, 补 growth 对应的"其他"扇区
    if chart["type"] == "pie" and len(chart["items"]) == 1:
        growth = chart.get("growth") or ""
        m = re.search(r"(-?\d+(?:\.\d+)?)", growth)
        other = float(m.group(1)) if m else 100.0
        chart["items"].append({"label": "其他", "value": other})
    return chart


def _normalize_chart_input(render_config: dict, extracted: dict) -> dict:
    """归一化 LLM render_config + 口播提取结果 → 统一 chart 结构 (2026-08-01).

    兼容旧格式:
      - chart_type: "pie_chart"→pie, "bar_chart"/"line_chart"/其他→bar;
      - data: [{label,value}] 直接可用; [number] 旧格式按 label="数据N" 补全;
      - 缺 chart 字段时用 extracted.chart (口播提取的 bar items) 兜底。

    返回 {type, unit, growth, label, color_scheme, items:[{label,value}]}。
    """
    chart = dict(extracted.get("chart") or {})
    chart_type = render_config.get("chart_type") or chart.get("type") or "bar"
    if not isinstance(chart_type, str):
        chart_type = "bar"
    chart_type = chart_type.lower()
    if chart_type in ("pie", "pie_chart"):
        chart["type"] = "pie"
    else:
        chart["type"] = "bar"

    items = _coerce_items(render_config.get("data"))
    # data 缺失/无效时依次兜底: render_config.chart.items → 口播提取 items
    if not items:
        items = _chart_fallback(render_config, chart)
    chart["items"] = items[:5]

    return _apply_chart_metadata(chart, render_config)

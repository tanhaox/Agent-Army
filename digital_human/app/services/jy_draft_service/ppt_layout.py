# -*- coding: utf-8 -*-
"""元素级 PPT 布局分析 — 分带/分列/信息块聚类/宫格锚点检测.

拆包自 jy_draft_service.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

__all__ = ["_split_bands", "_content_columns", "_group_into_blocks",
           "_grid_anchors", "_detect_grid_anchors", "_dist2"]


def _split_bands(
    elems: list[dict], height_emu: float = 6858000,
) -> tuple[list[dict], list[dict], list[dict]]:
    """按纵向位置分带: (页头 top<12%, 内容带, 页脚 top>85%)."""
    header, body, footer = [], [], []
    for l in elems:
        tr = float(l.get("top", 0)) / height_emu if height_emu else 0
        if tr < 0.12:
            header.append(l)
        elif tr > 0.85:
            footer.append(l)
        else:
            body.append(l)
    return header, body, footer


def _content_columns(layers: list[dict], height_emu: float = 6858000) -> int:
    """内容带列数 (结构化判定): 剔除页头/页脚后按 left 聚类得几列."""
    _, body, _ = _split_bands(layers, height_emu)
    cols: list[list] = []
    for l in sorted(body, key=lambda x: float(x.get("left", 0))):
        if cols and abs(float(l.get("left", 0)) - float(cols[-1][0].get("left", 0))) <= 320000:
            cols[-1].append(l)
        else:
            cols.append([l])
    return len(cols)


def _group_into_blocks(
    elems: list[dict],
    height_emu: float = 6858000,
    left_tol: float = 320000,
) -> list[list[dict]]:
    """按 PPT 版式把元素聚成信息块 (2026-08-21).

    - 页头 (top<12%高) → 独立块, 先显示
    - 页脚 (top>85%高) → 独立块, 后显示
    - 内容带按 left 聚类成列 (块): 三栏 PPT 的 01/02/03 各占一列
    - 图片随其列; 独立图作单块
    返回块列表, 每块内元素无序 (排序由调用方).
    """
    header, body, footer = _split_bands(elems, height_emu)
    cols: list[list[dict]] = []
    for l in sorted(body, key=lambda x: float(x.get("left", 0))):
        if cols and abs(float(l.get("left", 0)) - float(cols[-1][0].get("left", 0))) <= left_tol:
            cols[-1].append(l)
        else:
            cols.append([l])
    blocks: list[list[dict]] = []
    if header:
        blocks.append(header)
    blocks.extend(cols)
    if footer:
        blocks.append(footer)
    return blocks


def _grid_anchors(elems: list[dict], height_emu: float = 6858000) -> list[dict]:
    """宫格锚点候选 (2026-08-21): 数字标记(01/02/03) 或 短粗体标题(≥14pt≤20字),
    排除页头带. 返回锚点列表 (须再经行聚类判定是否真为宫格)."""
    import re as _re
    anchors = []
    for l in elems:
        if l["kind"] != "text":
            continue
        tr = float(l.get("top", 0)) / height_emu if height_emu else 0
        if tr < 0.12:
            continue
        text = (l.get("text") or "").strip()
        if not text:
            continue
        is_num = bool(_re.match(r"^\d{1,2}$", text))
        pt = float(l.get("pt") or 0)
        is_title = bool(l.get("bold")) and pt >= 14 and len(text) <= 20
        if is_num or is_title:
            anchors.append(l)
    return anchors


def _detect_grid_anchors(elems: list[dict], height_emu: float = 6858000) -> list[dict] | None:
    """宫格判定: 锚点按行聚类 (top 差≤600000 EMU), 任一行≥2 锚 → 宫格.

    优先数字标记(01), 其次短粗体标题. 返回最终锚点集; 非宫格返回 None.
    """
    anchors = _grid_anchors(elems, height_emu)
    if len(anchors) < 2:
        return None
    num_markers = [a for a in anchors if (a.get("text") or "").strip().isdigit()]
    pool = num_markers if len(num_markers) >= 2 else anchors
    pool_sorted = sorted(pool, key=lambda l: float(l.get("top", 0)))
    rows: list[list[dict]] = []
    for a in pool_sorted:
        if rows and abs(float(a.get("top", 0)) - float(rows[-1][0].get("top", 0))) <= 600000:
            rows[-1].append(a)
        else:
            rows.append([a])
    if any(len(r) >= 2 for r in rows):
        return pool
    return None


def _dist2(a: dict, b: dict) -> float:
    return (float(a.get("left", 0)) - float(b.get("left", 0))) ** 2 + \
           (float(a.get("top", 0)) - float(b.get("top", 0))) ** 2

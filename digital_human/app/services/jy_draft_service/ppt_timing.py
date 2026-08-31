# -*- coding: utf-8 -*-
"""元素级 PPT 时序编排 — 口播匹配 / 宫格 / 块级三种策略 + 统一分发.

拆包自 jy_draft_service.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

from app.services.jy_draft_service.ppt_layout import (
    _content_columns,
    _detect_grid_anchors,
    _dist2,
    _group_into_blocks,
)

__all__ = ["split_narration", "compute_element_timing", "compute_cell_timing",
           "compute_block_timing", "compute_page_timing"]

# 每页 = 1 base 层 (背景+装饰, 无动画) + 逐元素透明 PNG 层 (文字/前景图).
# 每元素独立 video 轨, 按角色序错峰渐显入场. base 轨页间加转场.
_ROLE_PRIORITY = {"title": 0, "subtitle": 1, "emphasis": 1.5,
                  "body": 2, "caption": 3, "other": 4}
# 句子停顿加权: 每句结束后额外停顿时长 (秒), 模拟 TTS 换气停顿
_SENT_PAUSE = 0.35
# 动效完成后的静止阅读窗口: 所有元素最晚入场 ≤ 页末 - 此值
_READ_WINDOW = 5.0


def _safe_deadline(page_dur: float) -> float:
    """元素最晚入场时刻: 长页留 5s 阅读窗; 短页至少留 0.5s 且不超页长."""
    return max(0.5, min(page_dur - _READ_WINDOW, page_dur - 0.5))


def split_narration(text: str) -> list[str]:
    """口播稿按句切分 (中文句末标点 .!?。！？;； 及换行)."""
    import re as _re
    text = (text or "").strip()
    if not text:
        return []
    parts = _re.split(r"(?<=[。！？；.!?])\s*|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _char_weight(sent: str) -> float:
    """句子权重: 字符数 (标点略降权)."""
    return sum(0.5 if c in "，、：；。！？,.!?;: " else 1.0 for c in sent)


def _match_score(el_text: str, sent: str) -> float:
    """元素文本 ↔ 口播句 匹配分.

    子串出现 → 1.0 (逐字吻合); 否则最长公共子串占比 (连续才算, 防短句
    靠共同常用字假阳性, 如 '其实是小麦驯化了我们' 与 '咱们...小麦的手下败将').
    """
    el = (el_text or "").strip()
    if not el:
        return 0.0
    if el in sent:
        return 1.0
    import difflib
    m = difflib.SequenceMatcher(None, el, sent).find_longest_match(0, len(el), 0, len(sent))
    return m.size / max(1, len(el))


def compute_element_timing(
    narration: str,
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
    group_gap: float = 0.25,
    match_threshold: float = 0.6,
) -> list[dict]:
    """按口播稿时序分配每个元素的入场时刻 (2026-08-21 v3).

    近似法 (TTS 合成音语速稳定, 无需 whisper): 口播按句切分, 每句时长
    ∝ 字符权重 + 停顿加权, 累计得句窗口.
    - 高置信匹配 (覆盖率≥0.6): 元素在该句说到时入场, 且**句内偏移**
      (元素文本在句中的位置 → 精确到该句内部时刻, 而非句首).
      同句多元素按角色序微错峰 0.25s.
    - 未匹配元素 (屏上文字与口播不逐字吻合): 补到已匹配之后的
      空闲句窗口, 保持逐级显示且不跳到已播内容之前.
    """
    sents = split_narration(narration)
    elems = [l for l in layers if l["kind"] != "base"]
    if not sents or page_dur <= 0 or not elems:
        return []
    # 句窗口 (字符权重比例 + 句尾停顿)
    weights = [_char_weight(s) + _SENT_PAUSE for s in sents]
    total_w = sum(weights)
    acc = first_delay
    sent_wins = []
    for i, w in enumerate(weights):
        sent_wins.append({"idx": i, "start": acc, "dur": page_dur * w / total_w})
        acc += page_dur * w / total_w
    sent_wins.sort(key=lambda x: x["start"])

    # 角色序 (title 优先占句)
    elems.sort(key=lambda l: (_ROLE_PRIORITY.get(l.get("role", "other"), 4), l.get("order", 0)))
    assigned: dict[int, float] = {}
    group_count: dict[int, int] = {}
    last_assign = first_delay

    # Phase 1: 高置信匹配 (同句最多 2 元素成组微错峰 — 标题副题常一口气说出)
    for ei, l in enumerate(elems):
        if l["kind"] != "text" or not l.get("text"):
            continue
        cand = [(w["idx"], _match_score(l["text"], sents[w["idx"]])) for w in sent_wins]
        cand.sort(key=lambda x: -x[1])
        for si, score in cand:
            if score < match_threshold:
                break
            if group_count.get(si, 0) >= 2:
                continue
            group_count[si] = group_count.get(si, 0) + 1
            win = next(w for w in sent_wins if w["idx"] == si)
            pos = sents[si].find(l["text"][:6]) if len(l["text"]) >= 2 else 0
            rel = max(0.0, pos) / max(1, len(sents[si]))
            t = win["start"] + win["dur"] * rel + (group_count[si] - 1) * group_gap
            assigned[ei] = t
            last_assign = max(last_assign, t)
            break

    # 动效完成窗口: 所有元素最晚入场 ≤ 页长安全线 (长页留 5s 阅读, 短页不超页长)
    safe_deadline = _safe_deadline(page_dur)

    # Phase 2: 未匹配 → 均匀铺满 [first_delay, safe_deadline]
    # 消除"尾部密集 + 前段空白": 未匹配元素按阅读序均布, 不与口播吻合元素争位
    # (不同轨共存, 时间可穿插, 无冲突).
    unmatched = [ei for ei in range(len(elems)) if ei not in assigned]
    if unmatched:
        n_u = len(unmatched)
        span = max(0.5, safe_deadline - first_delay)
        for j, ei in enumerate(unmatched):
            assigned[ei] = first_delay + (j + 1) * span / (n_u + 1)

    # 全局钳制: 匹配元素若落在安全窗内/后, 一并压到 safe_deadline
    for ei in assigned:
        if assigned[ei] > safe_deadline:
            assigned[ei] = safe_deadline

    out: list[dict] = []
    for ei, l in enumerate(elems):
        rel = min(assigned.get(ei, safe_deadline), safe_deadline)
        out.append({**l, "start_sec": round(page_start + rel, 3)})
    return out


def compute_cell_timing(
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
) -> list[dict] | None:
    """宫格布局逐格显示 (2026-08-21): 每格 图+标题同现 → 正文, 格按行优先.

    非宫格返回 None (调用方回退块级/口播). 页头先出, 页脚/游离元素后置.
    """
    elems = [l for l in layers if l["kind"] != "base"]
    anchors = _detect_grid_anchors(elems)
    if anchors is None:
        return None
    safe = _safe_deadline(page_dur)
    anchor_ids = {id(a) for a in anchors}

    # 非锚元素 → 最近锚点 (内容格); 游离元素(远)单独成块
    cells: dict[int, list[dict]] = {id(a): [a] for a in anchors}
    loose: list[dict] = []
    for l in elems:
        if id(l) in anchor_ids:
            continue
        tr = float(l.get("top", 0)) / 6858000
        if tr < 0.12 or tr > 0.85:  # 页头/页脚不入格、不入 loose (单独组)
            continue
        best = min(anchors, key=lambda a: _dist2(a, l))
        if _dist2(best, l) > (1.2e6) ** 2:  # 距锚点过远 → 游离
            loose.append(l)
        else:
            cells[id(best)].append(l)

    # 宫格语义只在"格内有图"(图+标题同现)时有意义; 纯文字列块(如 01/02/03
    # 三栏)回退给块级编排 — 否则 P3 这类会被错拆.
    if not any(any(l["kind"] == "image" for l in c) for c in cells.values()):
        return None

    # 行优先序
    ordered_cells: list[list[dict]] = []
    anchors_sorted = sorted(anchors, key=lambda a: float(a.get("top", 0)))
    rows: list[list[dict]] = []
    for a in anchors_sorted:
        if rows and abs(float(a.get("top", 0)) - float(rows[-1][0].get("top", 0))) <= 600000:
            rows[-1].append(a)
        else:
            rows.append([a])
    for row in sorted(rows, key=lambda r: float(r[0].get("top", 0))):
        for a in sorted(row, key=lambda x: float(x.get("left", 0))):
            ordered_cells.append(cells[id(a)])

    # 时序: 页头 → 宫格 → 游离(位置序) → 页脚
    header = sorted([l for l in elems if float(l.get("top", 0)) / 6858000 < 0.12],
                    key=lambda l: float(l.get("top", 0)))
    footer = sorted([l for l in elems if float(l.get("top", 0)) / 6858000 > 0.85],
                    key=lambda l: float(l.get("top", 0)))
    groups: list[list[dict]] = []
    if header:
        groups.append(header)
    groups.extend(ordered_cells)
    if loose:
        groups.append(sorted(loose, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0)))))
    if footer:
        groups.append(footer)

    total = sum(len(g) for g in groups)
    span = max(0.5, safe - first_delay)
    cursor = first_delay
    out: list[dict] = []
    for g in groups:
        n = max(len(g), 1)
        g_span = span * n / total
        has_img = any(l["kind"] == "image" for l in g)
        # 格内序: 有图 → 图+锚同现后正文; 无图 → 顶部序
        if len(anchors) == 1 and has_img:
            seq = [l for l in g if l["kind"] != "body"] + [l for l in g if l["kind"] == "body"]
        else:
            seq = sorted(g, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0))))
        if has_img:
            # 图+标题同现: 同时间戳
            img = [l for l in seq if l["kind"] == "image"]
            tit = [l for l in seq if l["kind"] == "text" and id(l) in anchor_ids]
            body = [l for l in seq if l["kind"] == "text" and id(l) not in anchor_ids]
            steps = []
            if img or tit:
                steps.append(img + tit)  # 同现
            steps.extend([[b] for b in body])
            # 展开: 同现组内同 start
            group_times: list[tuple[float, list[dict]]] = []
            t_cursor = cursor
            for st in steps:
                group_times.append((t_cursor, st))
                t_cursor += g_span / max(1, len(steps))
            for t, st in group_times:
                for l in st:
                    out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        else:
            for i, l in enumerate(seq):
                t = cursor + i * g_span / n
                out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        cursor += g_span
    return out


def compute_block_timing(
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
) -> list[dict]:
    """按信息块逐级显示 (2026-08-21): 页头 → 列块(左→右) → 页脚.

    每块一个时间片 (按元素数比例分配), 块内元素 top→bottom 错峰.
    全局保证: 最晚入场 ≤ 页长 - 5 (留 5s 静止阅读). 确定性, 不依赖口播匹配
    (块序是版式语义, 三栏稿口播常一次提及所有块).
    """
    elems = [l for l in layers if l["kind"] != "base"]
    if not elems:
        return []
    safe = _safe_deadline(page_dur)
    blocks = _group_into_blocks(elems)
    total = sum(len(b) for b in blocks)
    span = max(0.5, safe - first_delay)
    cursor = first_delay
    out: list[dict] = []
    for block in blocks:
        n = len(block)
        block_span = span * n / total
        block_elems = sorted(block, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0))))
        for i, l in enumerate(block_elems):
            t = cursor + (i * block_span / max(1, n))
            out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        cursor += block_span
    return out


def compute_page_timing(
    layers: list[dict],
    narration: str,
    page_start: float,
    page_dur: float,
) -> list[dict]:
    """统一入场编排 (2026-08-21):
    - 宫格布局 (数字标记/短粗体标题形成≥2格) → 逐格: 图+标题同现→正文
    - 结构化页 (内容带 ≥2 列, 如三栏信息块稿) → 块级逐级 (页头→列→页脚)
    - 单列/简单页 → 口播匹配 (标题随口播说到时入场)
    """
    cell = compute_cell_timing(layers, page_start, page_dur)
    if cell is not None:
        return cell
    if _content_columns(layers) >= 2:
        return compute_block_timing(layers, page_start, page_dur)
    timed = compute_element_timing(narration, layers, page_start, page_dur)
    if timed:
        return timed
    return compute_block_timing(layers, page_start, page_dur)  # 空口播兜底

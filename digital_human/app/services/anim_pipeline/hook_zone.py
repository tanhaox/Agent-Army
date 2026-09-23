"""60s 特区 (0919 用户令): 正文音频轴 [0, 60s) = 首分钟流量池特区。

口径 (定死): "1分钟" = 正文 60s (音频轴 0-60), 不含剪辑开头 opening_sec;
全集轴特区 = [tc, tc+60] (ep3 即 5.5-65.5s)。

- 所有视频的前 60s 都需要 — 平台推荐机制锁定, 冲平均在线时长。
- 镜槽系统预装 (DP): 目标带 3-6s (偏好 ≤5), 弹性带 [2.8, 6.3];
  >6.5s 长句句内逗号切 + 静音吸附。时间轴零 LLM — 导演只填画面。
- 特区跨场不打散场结构 (A1/A2 界不动); 场窗与特区相交的部分按窗裁块装包。
- 页面特区横幅 (anim.html) 与规划注入 (director2.plan_scene) 共用本模块。
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

ZONE_END = 60.0        # 特区右界 (音频轴, 正文秒)
SLOT_LO, SLOT_HI = 3.0, 6.0      # 目标带 (0919 用户令: 3s 底线, 5s 可放宽到 6s)
ELASTIC_LO, ELASTIC_HI = 2.8, 6.3  # 弹性带 (每集 ~1 镜落此, 实测概率)
SPLIT_SENT = 6.5       # 超此长的句 → 句内逗号切

# 特区宪法 (注入 plan_scene user prompt; 覆盖宪法中"场内共享场景"等冲突条款)
ZONE_RULES = """【🔥 60s 特区条款 — 本场开头与正文 0-60s 相交的部分适用, 覆盖宪法中冲突条款】
特区 = 正文前 60 秒流量池 (平台推荐机制锁定), 目标 = 每一镜都把观众按在屏幕前:
1. 镜界 = 槽界: 一槽一镜, 槽数/时长已由系统定死 (3-6s/镜), 你只填画面, 禁增删并镜、禁改镜界。
2. 组内场景禁重复 (用户铁令, 系统硬校验): 每镜必须给 "scene_tag": "2-6字场景名" (地点/环境,
   如 深夜书房/印刷车间/董事会议室/街边报刊亭/地铁站台) — **组内 scene_tag 禁重复, 重复=废稿重做**;
   相邻镜换的是"在哪、画什么" (场景整体换新), 只换机位=废稿; 画风/色调/质感仍锁美术圣经。
3. 母题轮换 (a1 实弹教训: scene_tag 各异但每镜都是"桌面+稿纸+红笔"换房间 = 构图骨架同源):
   每镜用**不同的隐喻载体** (立意 visual_motifs 挨个轮换, 一镜一母题); 同一物件组合
   (如 桌面+稿纸+红笔) 不得出现在两镜以上; 批评轮带构图相似度审计, 同源对会被点名。
4. 场景先行: 动笔前先给全部槽各配一个互不相同的 scene_tag, 再逐镜写画面 — N 槽 = N 个不同场景;
   旧版画面仅作反面教材, 旧版的场景串一律不得沿用。
5. 首帧复杂度下限: 每镜画面必须"满" — 前中后三层景深 + ≥3 组叙事元素 + ≥2 个可动点
   (H3 要有事干); 简单首帧 = 简单动画 = 观众划走。
6. 每镜首拍 1s 内必须有可见动作/光效 (宪法原有, 特区内加倍执行)。
7. 特区组 keyframe_zh 写「蒙太奇主题」(这串多场景镜共同讲的逻辑线), 不锁单一场景。"""


def zone_scene_issues(tags: list[str | None]) -> list[str]:
    """特区 scene_tag 审计 (确定性执法): 缺标/组内重复 → 问题列表 (硬校验拒稿)。"""
    issues: list[str] = []
    seen: dict[str, int] = {}
    for i, tag in enumerate(tags):
        t = str(tag or "").strip()
        if not t:
            issues.append(f"特区镜{i + 1} 缺 scene_tag (2-6字场景名)")
            continue
        if t in seen:
            issues.append(f"特区镜{i + 1} scene_tag「{t}」与镜{seen[t] + 1}重复 — 组内场景禁一致")
        else:
            seen[t] = i
    return issues


_STRIP_RE = re.compile(
    r"1988赛璐璐风格|赛璐璐|卡通大头|固定机位|平视|俯瞰|特写|中景|全景|空拍|远景|近景"
    r"|镜头|极轻微推近|极轻微拉远|明亮|深夜|，|。|、|；|：|\s")


def zone_composition_issues(zone_shots: list[dict[str, Any]],
                            ratio_hi: float = 0.52) -> list[str]:
    """特区构图同源软审计 (0919 a1 实弹教训: scene_tag 各异但骨架全是"桌面+稿纸+红笔")。

    keyframe 剥风格/机位词后逐对相似度, ≥ratio_hi 点名 — 走批评轮 (软), 不硬拒。
    """
    import difflib
    txts = [_STRIP_RE.sub("", str(s.get("keyframe_zh") or ""))[:220]
            for s in zone_shots]
    issues: list[str] = []
    for i in range(len(txts)):
        for j in range(i + 1, len(txts)):
            if not txts[i] or not txts[j]:
                continue
            r = difflib.SequenceMatcher(None, txts[i], txts[j]).ratio()
            if r >= ratio_hi:
                issues.append(
                    f"{zone_shots[i].get('shot_id')}↔{zone_shots[j].get('shot_id')} "
                    f"构图相似度 {r:.0%} — 母题未轮换 (同一物件组合换房间)")
    return issues


def _seg_cost(d: float) -> float:
    """DP 段成本: 命中带 0 / 放宽带轻罚 / 弹性带中罚 / 越界重罚 (不可切时硬吃)。"""
    if d <= 0:
        return 1e9
    if SLOT_LO <= d <= 5.0:
        return 0.02            # 命中目标带 (含每槽基线 → 同分偏好少镜)
    if 5.0 < d <= SLOT_HI:
        return 0.6
    if ELASTIC_LO <= d < SLOT_LO:
        return 1.2
    if SLOT_HI < d <= ELASTIC_HI:
        return 1.5
    if 2.5 <= d < ELASTIC_LO:
        return 4.0
    if ELASTIC_HI < d <= 7.5:
        return 4.5
    if 1.5 <= d < 2.5:
        return 6.0
    # 0923 根修: >7.5s 改比例罚 — 旧平顶 12.0 导致 1槽60s(cost 12) 比 3槽20s(cost 36) "便宜",
    # DP 永远选巨槽; 比例罚 d*0.8 → 8s=6.4, 12s=9.6, 20s=16, 60s=48 (多小槽恒优于巨槽)
    return max(12.0, d * 0.8)


def _slice_text_frac(text: str, f0: float, f1: float) -> str:
    """跨窗句的窗内份额文本: 字符比例切 (narration 用, 连续子串即可)。"""
    if not text:
        return ""
    n = len(text)
    return text[max(0, int(n * f0)):max(1, int(n * f1))]


def _comma_split(u: dict[str, Any]) -> list[dict[str, Any]]:
    """>SPLIT_SENT 句 → 句内子句切 (逗/分/冒), 时间 = 字数比例 + 静音吸附。

    静音候选取自所在包 wav (sent_table 需带 file/pack_t0); 无 wav/无候选回退纯比例。
    返回子句 pieces (递归无必要: 子句级再超限概率≈0)。
    """
    text = str(u.get("text") or "")
    t0, t1 = float(u["t_start"]), float(u["t_end"])
    dur = t1 - t0
    parts = [p for p in re.split(r"(?<=[，,；;：:])", text) if p.strip()]
    if len(parts) < 2 or dur <= SPLIT_SENT:
        return [u]
    weights = [len(p) + 0.6 for p in parts]  # 句读处小停顿加成
    total_w = sum(weights) or 1.0
    # 静音候选 (包内绝对秒)
    cands: list[float] = []
    wav = str(u.get("file") or "")
    pack_t0 = float(u.get("pack_t0") or -1e9)
    if wav and pack_t0 > -1e8:
        try:
            from pathlib import Path

            from scripts.tts_lib.silence_split import (
                _detect_silences,
                _silence_candidates,
            )
            cands = _silence_candidates(_detect_silences(Path(wav)), dur + (t0 - pack_t0))
        except Exception:  # noqa: BLE001 — 吸附失败回退比例
            cands = []
    pieces: list[dict[str, Any]] = []
    cum_t = t0
    cum_w = 0.0
    for p, w in zip(parts[:-1], weights[:-1]):
        cum_w += w
        exp_abs = t0 + dur * (cum_w / total_w)
        cut = exp_abs
        if cands:
            rel = exp_abs - pack_t0
            near = min(cands, key=lambda c: abs(c - rel)) if cands else None
            if near is not None and abs(near - rel) <= 1.2:
                cut = pack_t0 + near
        cut = min(max(cut, cum_t + 0.3), t1 - 0.3)
        if cut <= cum_t + 0.05:
            continue
        pieces.append({"t_start": round(cum_t, 2), "t_end": round(cut, 2),
                       "text": p, "file": u.get("file"), "pack_t0": u.get("pack_t0")})
        cum_t = cut
    pieces.append({"t_start": round(cum_t, 2), "t_end": round(t1, 2),
                   "text": parts[-1] if cum_w + weights[-1] else text,
                   "file": u.get("file"), "pack_t0": u.get("pack_t0")})
    # 兜底: 切完仍有超限 piece 且子句≥2 → 不再递归 (概率≈0), 原样交付
    return pieces


def _absorb_short_units(units: list[dict[str, Any]],
                        min_u: float = 2.5) -> list[dict[str, Any]]:
    """短单元 (<min_u) 并邻, 但并后不超 7.5s (0923 修: 级联合并毁掉 DP 切点).

    旧版无条件并邻 → 级联后单元巨长 → DP 无切点 → 1 槽 60s (A1 实锤).
    修 = 并邻前检查合并后时长, 超过 CAP 则不并 (保留切点, 让 DP 弹性带处理)."""
    CAP = 7.5  # 并后上限 (超过则不并, 保留 DP 切点)
    out = [dict(u) for u in units]
    for _round in range(2):
        i = 0
        while i < len(out):
            d = float(out[i]["t_end"]) - float(out[i]["t_start"])
            if d >= min_u or len(out) == 1:
                i += 1
                continue
            if i > 0:
                prev_d = float(out[i - 1]["t_end"]) - float(out[i - 1]["t_start"])
                merged_d = float(out[i]["t_end"]) - float(out[i - 1]["t_start"])
                if merged_d <= CAP:  # 0923: 并后不超 CAP 才并
                    out[i - 1]["t_end"] = out[i]["t_end"]
                    out[i - 1]["text"] = str(out[i - 1]["text"]) + str(out[i]["text"])
                    out.pop(i)
                else:
                    i += 1  # 不并, 保留切点
            else:
                out[1]["t_start"] = out[0]["t_start"]
                out[1]["text"] = str(out[0]["text"]) + str(out[1]["text"])
                out.pop(0)
        # 终切: 并后超带 (>ELASTIC_HI, 与 DP 弹性上界对齐 — SPLIT_SENT=6.5 会漏
        # 6.3-6.5 缝: DP 罚 4.5 但切不触发, A2 全并 29.6s 巨槽实锤) 逗号切一遍,
        # 切出的短片 (<min_u) 并回大侧
        final: list[dict[str, Any]] = []
        for u in out:
            if float(u["t_end"]) - float(u["t_start"]) > ELASTIC_HI:
                final.extend(_comma_split(u) or [u])
            else:
                final.append(u)
        k = 0
        while k < len(final):
            d = float(final[k]["t_end"]) - float(final[k]["t_start"])
            if d >= min_u or len(final) == 1:
                k += 1
                continue
            if k > 0 and (k + 1 >= len(final)
                          or float(final[k - 1]["t_end"]) - float(final[k - 1]["t_start"])
                          <= float(final[k + 1]["t_end"]) - float(final[k + 1]["t_start"])):
                final[k - 1]["t_end"] = final[k]["t_end"]
                final[k - 1]["text"] = str(final[k - 1]["text"]) + str(final[k]["text"])
                final.pop(k)
            elif k + 1 < len(final):
                final[k + 1]["t_start"] = final[k]["t_start"]
                final[k + 1]["text"] = str(final[k]["text"]) + str(final[k + 1]["text"])
                final.pop(k)
            else:
                k += 1
        if not any(float(f["t_end"]) - float(f["t_start"]) > ELASTIC_HI
                   for f in final) and \
           not any(float(f["t_end"]) - float(f["t_start"]) < min_u
                   for f in final):
            return final  # 收敛: 无超带无短片
        out = final
    return out


def pack_zone_slots(sent_table: list[dict[str, Any]] | None,
                    a0: float, a1: float,
                    zone_end: float = ZONE_END) -> list[dict[str, Any]]:
    """场窗 [a0, a1] ∩ 特区 [0, zone_end) → 镜槽列表 (音频轴)。

    单元 = 句级表条目按窗裁块 (跨窗句取窗内份额); 超长句逗号切; DP 装包
    目标带 [3,6] 弹性 [2.8,6.3]。首槽起 = a0, 末槽止 = min(a1, zone_end)。
    """
    w_end = min(a1, zone_end)
    if w_end - a0 < 0.1:
        return []
    units: list[dict[str, Any]] = []
    for s in sent_table or []:
        t0, t1 = float(s.get("t_start") or 0), float(s.get("t_end") or 0)
        if t1 <= a0 + 0.01 or t0 >= w_end - 0.01:
            continue
        p0, p1 = max(t0, a0), min(t1, w_end)
        if p1 - p0 < 0.05:
            continue
        text = str(s.get("text") or "")
        if t0 < p0 - 0.01 or t1 > p1 + 0.01:
            span = max(t1 - t0, 1e-6)
            text = _slice_text_frac(text, (p0 - t0) / span, (p1 - t0) / span)
        u = {"t_start": round(p0, 2), "t_end": round(p1, 2), "text": text,
             "file": s.get("file"), "pack_t0": s.get("pack_t0")}
        units.extend(_comma_split(u) if p1 - p0 > SPLIT_SENT else [u])
    if not units:
        return []
    # 贴窗 (首单元起点钉 a0, 末单元终点钉 w_end — 跨窗块已裁, 直接兜底)
    units[0]["t_start"] = a0
    units[-1]["t_end"] = w_end
    units = _absorb_short_units(units)
    # 0923 修: 吸收后再切长单元 — 级联合并/强制补尾会造出 >SPLIT_SENT 的巨单元,
    # DP 丢失切点只能出 1 槽 (A1 前60s 一镜实锤); 逗号切恢复切点
    _re_split = []
    for u in units:
        d = float(u["t_end"]) - float(u["t_start"])
        _re_split.extend(_comma_split(u) if d > SPLIT_SENT else [u])
    units = _re_split
    n = len(units)
    t0s = [float(u["t_start"]) for u in units]
    t1s = [float(u["t_end"]) for u in units]
    INF = 1e18
    dp = [INF] * (n + 1)
    dp[0] = 0.0
    cut = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            if dp[i] >= INF:
                continue
            d = t1s[j - 1] - t0s[i]
            c = dp[i] + _seg_cost(d)
            if c < dp[j] - 1e-9:
                dp[j] = c
                cut[j] = i
    slots: list[dict[str, Any]] = []
    j = n
    while j > 0:
        i = cut[j]
        slots.append({"t_start": t0s[i], "t_end": t1s[j - 1],
                      "text": "".join(str(u["text"]) for u in units[i:j])})
        j = i
    slots.reverse()
    viol = [round(s["t_end"] - s["t_start"], 2) for s in slots
            if not ELASTIC_LO <= s["t_end"] - s["t_start"] <= ELASTIC_HI]
    logger.info("[hook-zone] 窗 [%.1f,%.1f] %d 单元 → %d 槽 (总成本 %.2f)%s",
                a0, w_end, n, len(slots), dp[n],
                f" 越带槽: {viol}" if viol else "")
    return slots


def enforce_zone_shots(groups: list[dict[str, Any]], slots: list[dict[str, Any]],
                       ) -> list[dict[str, Any]]:
    """LLM 输出执法: slot 标记镜 ↔ 槽位一一对应, 回填时间/口播/特区标。

    槽数不符 → ValueError (调用方重试网接住, 不落盘)。返回原 groups (原位改)。
    """
    got = sum(1 for g in groups for r in (g.get("shots") or [])
              if r.get("slot") is not None and int(r.get("slot") or 0) <= len(slots))
    if got != len(slots):
        raise ValueError(f"特区镜数 {got} ≠ 槽位数 {len(slots)} — slot 标记需逐槽一镜")
    cursor = 0
    for g in groups:
        inner = g.get("shots") or []
        ordered = sorted([r for r in inner
                          if r.get("slot") is not None
                          and int(r.get("slot") or 0) <= len(slots)],
                         key=lambda r: int(r.get("slot") or 0))
        for raw in ordered:
            sl = slots[cursor]
            cursor += 1
            raw.pop("slot", None)
            raw["t_start"] = sl["t_start"]
            raw["t_end"] = sl["t_end"]
            raw["narration"] = sl["text"][:300]
            raw["zone"] = "hook60"
    return groups


def enforce_scene_shots(groups: list[dict[str, Any]],
                        scene_slots: list[dict[str, Any]],
                        slot_offset: int = 0,
                        ) -> list[dict[str, Any]]:
    """普通镜槽执法 (0919 全片装包制): slot 标镜 (槽号 > offset) ↔ 普通槽一一对应.

    回填时间/口播, 打 packed 标 (后续对齐链路保护 — 槽位=句包边, 禁 needle 重切).
    槽数不符 → ValueError (调用方重试网接住)."""
    marked = sorted(
        (r for g in groups for r in (g.get("shots") or [])
         if r.get("slot") is not None and int(r.get("slot") or 0) > slot_offset),
        key=lambda r: int(r.get("slot") or 0))
    if len(marked) != len(scene_slots):
        raise ValueError(f"普通槽镜数 {len(marked)} ≠ 槽位数 {len(scene_slots)} — "
                         f"slot 标记需逐槽一镜")
    for raw, sl in zip(marked, scene_slots):
        raw.pop("slot", None)
        raw["t_start"] = sl["t_start"]
        raw["t_end"] = sl["t_end"]
        raw["narration"] = str(sl["text"])[:300]
        raw["packed"] = True
    return groups

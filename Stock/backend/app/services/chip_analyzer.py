"""筹码吸收率分析引擎 — 锁死区间 vs 套牢区间的成交量对比.

核心问题: 一只股票横盘锁死了 40 天, 它吃掉了上方多少套牢盘?

三个区间:
  Z_LOCK  (锁死区间): 当前横盘范围, 由锁死检测提供的区间
  Z_OVER  (套牢区):   锁死区间上方, 历史密集成交区, 被套的人在扛
  Z_BELOW (支撑区):   锁死区间下方, 极端低点范围

核心指标 — 吸收率 (Absorption Rate):
  AR_lock = Z_LOCK 成交量 / (Z_LOCK + Z_OVER) 总成交量
  吸收率高 → 套牢盘在被吃掉 → 开锁后抛压小
  吸收率趋势上升 → 筹码在加速下沉 → 快启动了

随时间追踪:
  按 10 天切片段, 计算每段的 AR_lock + AR_over 变化趋势
  如果 AR_lock 从 0.3 → 0.5 → 0.7, 说明割肉在加速
  如果 AR_lock 一直在 0.2~0.3 徘徊, 说明上方还在死扛
"""
import asyncio, logging, numpy as np
from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import text
from app.core.database import async_session_factory
from app.services.minute_data import fetch_5min_bars

try:
    from dotenv import load_dotenv
    load_dotenv('C:/AI-Agent-Local/Stock/backend/.env')
except Exception:
    pass

logger = logging.getLogger("chip_analyzer")

SEGMENT_DAYS = 10     # 每段 10 个交易日
LOCK_LOOKBACK = 60     # 回看 60 天的日线


def define_zones(lock_bottom: float, lock_top: float,
                 daily_highs_60d: np.ndarray,
                 daily_lows_60d: np.ndarray) -> dict:
    """定义三个价格区间.

    当锁死区间给定时 (来自锁死检测):
      Z_LOCK  = [lock_bottom, lock_top]  当前横盘范围
      Z_OVER  = [lock_top, 60日最高]    上方套牢区
      Z_BELOW = [60日最低, lock_bottom]  下方支撑区

    如果锁死区间未知, 基于 60 日数据自动推断:
      锁死区间 = 最近 30 日的高低点 (横盘范围)
    """
    h_60 = float(np.max(daily_highs_60d)) if len(daily_highs_60d) > 0 else lock_top * 1.3
    l_60 = float(np.min(daily_lows_60d)) if len(daily_lows_60d) > 0 else lock_bottom * 0.8

    return {
        "Z_LOCK":  {"low": round(lock_bottom, 2), "high": round(lock_top, 2)},
        "Z_OVER":  {"low": round(lock_top, 2), "high": round(h_60, 2)},
        "Z_BELOW": {"low": round(l_60, 2), "high": round(lock_bottom, 2)},
    }


def compute_absorption(bars_5min: list[dict], zones: dict) -> dict:
    """计算吸收率 — 锁死区间成交量 vs 总吸收相关成交量.

    对每根 5 分钟 K 线, 按其价格区间归类:
      - 如果 K 线完全在 Z_LOCK 内 → vol_lock
      - 如果 K 线完全在 Z_OVER 内 → vol_over
      - 跨区间的按比例分拆

    Returns:
      {total_vol, vol_lock, vol_over, vol_below,
       ar_lock, ar_over_ratio, verdict, segments: [...]}
    """
    if len(bars_5min) < 100:
        return {"error": "数据不足"}

    zl = zones["Z_LOCK"]
    zo = zones["Z_OVER"]
    zb = zones["Z_BELOW"]

    vol_lock = 0.0
    vol_over = 0.0
    vol_below = 0.0

    # 按日期分组, 用于分时段追踪
    by_date = defaultdict(lambda: {"vol_lock": 0.0, "vol_over": 0.0, "vol_below": 0.0})

    for b in bars_5min:
        bar_high = b["high"]
        bar_low = b["low"]
        vol = b["vol"]

        # K 线中点在哪个区间, 整个 K 线的量归给哪个区间
        # (对于跨区间 K 线用中点近似)
        mid = (bar_high + bar_low) / 2

        day = b.get("time", "")[:10] if "time" in b else b.get("trade_time", "")[:10]

        if mid >= zl["low"] and mid <= zl["high"]:
            vol_lock += vol
            by_date[day]["vol_lock"] += vol
        elif mid > zl["high"]:
            vol_over += vol
            by_date[day]["vol_over"] += vol
        elif mid < zl["low"]:
            vol_below += vol
            by_date[day]["vol_below"] += vol

    # ── 吸收率计算 ──
    total = vol_lock + vol_over + vol_below
    if total <= 0:
        return {"error": "无成交量"}

    # 核心指标: 锁死区吸收了多少总成交量?
    ar_lock = vol_lock / total

    # 核心指标: 锁死 vs 上方的比值 (越高越说明套牢盘在被消化)
    absorb_total = vol_lock + vol_over
    if absorb_total > 0:
        ar_ratio = vol_lock / absorb_total  # 锁/(锁+上), 越大越好
    else:
        ar_ratio = 0

    # ── 分时段趋势 ──
    sorted_dates = sorted(by_date.keys())
    segments = []
    segment_window = SEGMENT_DAYS

    for seg_start in range(0, len(sorted_dates), segment_window):
        seg_dates = sorted_dates[seg_start:seg_start + segment_window]
        if len(seg_dates) < 3:
            continue
        seg_lock = sum(by_date[d]["vol_lock"] for d in seg_dates)
        seg_over = sum(by_date[d]["vol_over"] for d in seg_dates)
        seg_below = sum(by_date[d]["vol_below"] for d in seg_dates)
        seg_total = seg_lock + seg_over + seg_below

        if seg_total > 0:
            seg_ar = seg_lock / seg_total
            seg_ratio = seg_lock / max(seg_lock + seg_over, 1)
            segments.append({
                "start_date": seg_dates[0],
                "end_date": seg_dates[-1],
                "days": len(seg_dates),
                "vol_lock_pct": round(seg_lock / seg_total * 100, 1),
                "vol_over_pct": round(seg_over / seg_total * 100, 1),
                "vol_below_pct": round(seg_below / seg_total * 100, 1),
                "ar_lock": round(seg_ar, 3),
                "ar_ratio": round(seg_ratio, 3),
            })

    # ── 趋势判定 ──
    if len(segments) >= 2:
        recent_ars = [s["ar_ratio"] for s in segments[-3:]]
        earlier_ars = [s["ar_ratio"] for s in segments[:3]]

        recent_avg = float(np.mean(recent_ars)) if recent_ars else ar_ratio
        earlier_avg = float(np.mean(earlier_ars)) if earlier_ars else ar_ratio

        if recent_avg > earlier_avg * 1.3:
            trend = "加速吸收"   # 锁死区在加速吃套牢盘
        elif recent_avg > earlier_avg * 1.1:
            trend = "缓慢吸收"
        elif recent_avg < earlier_avg * 0.8:
            trend = "吸收减弱"   # 套牢盘在死扛, 没割肉
        else:
            trend = "吸收稳定"
    else:
        trend = "数据不足"

    # ── 综合判定 ──
    if ar_ratio >= 0.60 and trend in ("加速吸收", "缓慢吸收"):
        verdict = "强吸收"     # 已吃掉 60%+ 相关筹码, 还在加速
        quality = 10
    elif ar_ratio >= 0.50:
        verdict = "中等吸收"   # 过半, 在消化
        quality = 7
    elif ar_ratio >= 0.35:
        verdict = "弱吸收"     # 三分之一, 还需时间
        quality = 4
    else:
        verdict = "套牢死扛"   # 上方套牢盘不割, 压力大
        quality = 2

    return {
        "total_vol": round(total, 0),
        "vol_lock": round(vol_lock, 0),
        "vol_over": round(vol_over, 0),
        "vol_below": round(vol_below, 0),
        "vol_lock_pct": round(vol_lock / total * 100, 1),
        "vol_over_pct": round(vol_over / total * 100, 1),
        "vol_below_pct": round(vol_below / total * 100, 1),
        "ar_lock": round(ar_lock, 3),         # 锁死占总成交
        "ar_ratio": round(ar_ratio, 3),        # 锁/(锁+上)
        "trend": trend,
        "verdict": verdict,
        "quality": quality,
        "segments": segments,
    }


async def analyze_chip_absorption(
    ts_code: str,
    lock_bottom: float = None,
    lock_top: float = None,
) -> dict | None:
    """一站式筹码吸收率分析.

    自动获取锁死区间(从 lock-detail) + 拉分钟线 + 算吸收率.

    Args:
        ts_code: 股票代码
        lock_bottom, lock_top: 锁死区间 (可选, 否则从 DB 自动推断)

    Returns:
        {zones, absorption, summary}
    """
    # 加载日线数据
    async with async_session_factory() as s:
        r = await s.execute(text("""
            SELECT close, high, low FROM daily_kline
            WHERE ts_code = :c ORDER BY trade_date DESC LIMIT 120
        """), {"c": ts_code})
        rows = list(reversed(r.fetchall()))

    if len(rows) < 30:
        return {"error": "日线数据不足"}

    closes = np.array([float(r[0] or 0) for r in rows])
    highs = np.array([float(r[1] or closes[i]) for i, r in enumerate(rows)])
    lows = np.array([float(r[2] or closes[i]) for i, r in enumerate(rows)])
    n = len(closes)
    current_price = float(closes[-1])

    # 如果没提供锁死区间, 自动推断: 最近 30 天的范围就是锁死区间
    if lock_bottom is None or lock_top is None:
        h_30 = float(np.max(highs[-30:]))
        l_30 = float(np.min(lows[-30:]))
        lock_top = h_30
        lock_bottom = l_30

    # 定义三个区间
    zones = define_zones(lock_bottom, lock_top,
                         highs[-LOCK_LOOKBACK:], lows[-LOCK_LOOKBACK:])

    # 拉分钟线
    bars = await fetch_5min_bars(ts_code, lookback_days=LOCK_LOOKBACK)
    if not bars or len(bars) < 100:
        return {"zones": zones, "absorption": {"error": "分钟数据不足"}}

    # 算吸收率
    abs_data = compute_absorption(bars, zones)

    if "error" in abs_data:
        return {"zones": zones, "absorption": abs_data}

    # 摘要
    zl = zones["Z_LOCK"]
    zo = zones["Z_OVER"]
    ar = abs_data["ar_ratio"]
    trend = abs_data["trend"]
    verdict = abs_data["verdict"]

    # 用自然语言表述
    lines = []
    lines.append(f"锁死区间 ¥{zl['low']}-{zl['high']} | 上方套牢区 ¥{zo['low']}-{zo['high']}")
    lines.append(f"吸收率 {ar*100:.0f}% ({verdict}) — "
                 f"锁死区吃了 {ar*100:.0f}% 的相关筹码")

    if trend == "加速吸收":
        lines.append(f"趋势: {trend} — 近段吸收率显著高于早期, 割肉在加速, 筹码在下沉")
    elif trend == "缓慢吸收":
        lines.append(f"趋势: {trend} — 套牢盘在缓慢割肉, 还需时间消化")
    elif trend == "吸收稳定":
        lines.append(f"趋势: {trend} — 锁死区稳定吃进上方筹码")
    elif trend == "吸收减弱":
        lines.append(f"趋势: {trend} — 上方套牢盘在死扛, 还没人割肉。开锁后一涨就会有人跑")

    if ar >= 0.60:
        lines.append("结论: 套牢盘已被消化大半, 上方压力轻 — 开锁后容易涨")
    elif ar >= 0.50:
        lines.append("结论: 筹码在转移中, 但还有相当套牢盘未割 — 还需观察")
    elif ar >= 0.35:
        lines.append("结论: 锁死区还没吃够, 如果突然放量突破锁死上沿, 追高小心套牢盘砸盘")
    else:
        lines.append("结论: 套牢盘仍在死扛, 开锁后上方抛压重 — 建议等吸收率超过 40% 再参与")

    return {
        "zones": zones,
        "current_price": round(current_price, 2),
        "absorption": abs_data,
        "summary": " | ".join(lines),
    }

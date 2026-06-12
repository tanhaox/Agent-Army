"""Deep scorer — 14-dimension composite scoring pipeline (v4.4).

Phase 14: 5-phase pipeline decomposition.
Phases: preload → score → enrich → normalize → persist
"""
import json as _json
import logging
import numpy as np
from datetime import date as dt_date, timedelta
from sqlalchemy import text
from app.core.database import async_session_factory
from app.utils.numpy_utils import sanitize_for_json

logger = logging.getLogger(__name__)

# ═══════════ Re-exports from scoring modules ═══════════
from app.scoring.technical_scorers import (
    score_technical, score_kline_game, score_vol_ratio, score_arbr,
    score_bbi, score_trend_deviation, score_downside_risk, score_weekly_resonance,
)
from app.scoring.fundamental_scorers import (
    score_sector_alpha, score_toplist_sector, score_market_relative,
    score_fund_flow, score_valuation,
    get_fundamental_score, preload_fundamental_scores, get_fundamental_score_cached,
    FUNDA_RULES,
)
from app.scoring.structure_scorers import (
    score_ma_trend, score_pattern_signal, score_multi_box,
)

# ═══════════ Constants ═══════════
DEFAULT_WEIGHTS = {
    "tech_weight": 3.0, "kline_weight": 3.0, "fund_weight": 2.5,
    "tg_momentum_weight": 2.5, "vol_ratio_weight": 2.0, "arbr_weight": 1.5,
    "sector_alpha_weight": 1.5, "market_relative_weight": 1.5,
    "valuation_weight": 1.0,
    "ma_trend_weight": 1.5, "pattern_weight": 1.5,
    "trend_deviation_weight": 1.5, "bbi_weight": 1.5, "box_weight": 2.0,
    "fundamentals_weight": 1.5,
    # Phase 73: 之前遗漏的子维度 — 已在 _deep_score_phase 计算, 补入加权和
    "dist_low_weight": 1.0, "j_value_weight": 1.5,
    "downside_risk_weight": 1.0,
    # v4.8: 筹码维度 (Tushare cyq_perf)
    "chip_winner_weight": 2.0, "chip_cost_weight": 1.5,
    # Phase 73: 之前硬编码 0.5 的 extra dimensions → 可训练
    "weekly_resonance_weight": 0.5,
    "toplist_sector_weight": 0.5,
    "ambush_weight": 0.5,
    "sector_bonus_l2": 0.5, "sector_bonus_l3": 1.5,

    # ── M-4: 三级宏观权重 (Tier1 大盘14 + Tier2 板块18 + Tier3 个股11) ──
    # Tier 1: 大盘级宏观
    "macro_m2_yoy": 1.0, "macro_m1_m2_scissor": 0.5,
    "macro_shibor_spread": 1.0, "macro_shibor_3m_chg": 0.5,
    "macro_lpr_1y": 0.5, "macro_lpr_5y": 0.3,
    "macro_bond_3m_yield": 0.5, "macro_bond_10y_yield": 0.5,
    "macro_pmi_manufacturing": 1.0, "macro_pmi_new_order": 1.0,
    "macro_pmi_export_order": 0.5,
    "macro_cpi_ppi_gap": 0.5, "macro_ppi_mom": 0.5, "macro_gdp_gap": 0.3,
    # Tier 2: 板块级 (商品+行业+概念)
    "macro_crude_oil": 1.0, "macro_copper": 1.0, "macro_aluminum": 0.8,
    "macro_rebar": 0.8, "macro_iron_ore": 0.5, "macro_coke_coal": 0.5,
    "macro_lithium": 1.0, "macro_silicon": 0.8,
    "macro_gold": 0.8, "macro_natural_rubber": 0.5,
    "macro_methanol": 0.5, "macro_pvc": 0.5,
    "macro_sector_sw_5d": 1.0, "macro_sector_sw_20d": 0.8,
    "macro_concept_chg_5d": 1.0, "macro_concept_chg_20d": 0.8,
    "macro_sector_turnover": 0.5, "macro_concept_rank": 0.3,
    # Tier 3: 个股级
    "macro_big_order_net": 0.8, "macro_margin_balance_chg": 0.5,
    "macro_north_hold_chg": 0.8, "macro_north_hold_ratio": 0.5,
    "macro_block_trade_premium": 0.3, "macro_pledge_ratio": 0.3,
    "macro_roe": 1.0, "macro_roe_yoy": 0.8,
    "macro_revenue_yoy": 0.5, "macro_gross_margin": 0.5,
    "macro_forecast_surprise": 0.5,
}

_ARCH_RULES = {
    "large_bluechip": ["银行","保险","证券","金融","信托","白酒","食品","饮料","家电"],
    "growth_tech": ["半导体","芯片","元器件","通信","计算机设备","机械","机器人","光刻","PCB","制药","生物","医疗","医药","中药","创新药","CRO","器械","软件","互联网","IT服务","电信","传媒","游戏","数据","AI"],
    "cyclical_resource": ["石油","煤炭","有色","钢铁","化工","化纤","造纸","稀土","锂"],
    "value_defensive": ["电力","水务","供气","路桥","港口","房产","建筑","建材","环保","家居","纺织","旅游","酒店","农林牧渔","农业","乳业","食品","饮料"],
    "small_speculative": ["综合"],
}


def _arch_for_industry(industry_name: str) -> str:
    """Map industry name to archetype."""
    if not industry_name:
        return "small_speculative"
    for arch, keywords in _ARCH_RULES.items():
        for kw in keywords:
            if kw in (industry_name or ""):
                return arch
    return "small_speculative"


def _derive_strategy_label(r: dict) -> str | None:
    """从原型推导 strategy_label (S1/S2/S3)."""
    arch = r.get("archetype", "")
    if not arch:
        return None
    if "bluechip" in arch or "defensive" in arch:
        return "S1"
    if "growth" in arch or "cyclical" in arch:
        return "S2"
    if "speculative" in arch or "small" in arch:
        return "S3"
    return None


derive_strategy_label = _derive_strategy_label


def _normalize_within_archetype(results: list[dict]) -> list[dict]:
    """Normalize composite scores within each archetype group (0-100 scale).

    安全阀:
      - 单只股票同组: 跳过归一化, 直接取 raw_total clamp
      - 组内 range=0 (所有分数相同): 统一打 50 分
      - 2-4 只的小组: 用 softmax 替代 min-max (不会因为一头一尾极端值
        使中间股票被打到 0 或 100)
    """
    groups: dict[str, list[dict]] = {}
    for r in results:
        arch = r.get("archetype", "small_speculative")
        groups.setdefault(arch, []).append(r)

    for arch, group in groups.items():
        scores = [r.get("raw_total", 0) for r in group]
        if not scores:
            continue
        mn, mx = min(scores), max(scores)

        if len(group) <= 1:
            # 只有 1 只: raw_total clamp 到 0-100
            for r in group:
                r["composite_score"] = round(float(np.clip(r.get("raw_total", 50), 0, 100)), 1)
            continue

        rng = mx - mn
        if rng <= 0.01:
            # 全组相同: 统一 50
            for r in group:
                r["composite_score"] = 50.0
            continue

        if len(group) <= 4:
            # 小组: softmax 归一化 + clamp 到 0-100
            import numpy as _np
            arr = _np.array(scores, dtype=float)
            arr_centered = arr - _np.mean(arr)
            # 用同比放大而不是 min-max, 保留组内差距但不允许极端
            std = _np.std(arr)
            if std > 0.1:
                normalized = (arr_centered / std) * 15 + 50
            else:
                normalized = _np.full_like(arr, 50.0)
            for i, r in enumerate(group):
                r["composite_score"] = round(float(np.clip(normalized[i], 0, 100)), 1)
            continue

        # 大组 (5+): 标准 min-max
        for r in group:
            raw = r.get("raw_total", 0)
            normalized = (raw - mn) / rng * 100
            r["composite_score"] = round(float(np.clip(normalized, 0, 100)), 1)
    return results


# ═══════════ Phase 1: Data Preload ═══════════

async def _deep_preload_phase(session, symbols: list[str], scan_date) -> dict:
    """Load all prerequisite data: fundamental, patterns, ambush, fingerprints, beliefs.

    v4.13: 预加载使用独立 session, 避免缺表/缺列导致主事务 abort.

    Returns ctx dict with keys: symbols, scan_rows, scan_date_str, archetype_map,
    weights_map, beliefs_map, industry_map, kline_batch, patterns, ambush,
    sector_toplist_flow, market_state
    """
    from app.core.database import async_session_factory as _asf
    scan_date_str = str(scan_date)

    # 1. Preload fundamental scores (batch)
    try:
        await preload_fundamental_scores(symbols)
    except Exception as e:
        logger.warning(f"Fundamental preload failed: {e}")

    # 2. Preload pattern signals (独立 session)
    try:
        from app.services.data_preloader import preload_patterns
        async with _asf() as ps:
            await preload_patterns(symbols, scan_date_str)
    except Exception as e:
        logger.warning(f"Pattern preload failed: {e}")

    # 3. Preload ambush signals (独立 session)
    try:
        from app.services.data_preloader import preload_ambush
        async with _asf() as ps:
            await preload_ambush(symbols, scan_date_str)
    except Exception as e:
        logger.warning(f"Ambush preload failed: {e}")

    # 4. Load scan_rows
    r = await session.execute(text(
        "SELECT symbol, name, level, tg_momentum, dist_low, j_value, vol_ratio, "
        "buy_strength, close_price, composite_score, industry, trigger_path, "
        "COALESCE(resonance_type,'') as resonance_type, "
        "COALESCE(weekly_tg_momentum,0) as weekly_tg_momentum "
        "FROM scan_results WHERE scan_date=:d AND symbol=ANY(:syms)"
    ), {"d": scan_date, "syms": symbols})
    scan_rows = {row[0]: row for row in r.fetchall()}

    # 5. Build fingerprints + classify
    # v4.5: 用代码前缀 + 名称关键词做主分类 (fingerprint/stock_basic均缺失)
    archetype_map: dict[str, str] = {}
    try:
        from app.services.fingerprint_builder import build_fingerprints
        from app.services.archetype_classifier import classify_stocks
        fingerprints = await build_fingerprints(symbols)
        archetype_map = await classify_stocks(symbols, fingerprints)
        unique_archs = set(archetype_map.values())
        if len(unique_archs) <= 1:
            raise ValueError("Need diverse archetypes")
    except Exception as e:
        # 所有symbols去重后用代码前缀+名称分类
        r = await session.execute(text(
            "SELECT DISTINCT ON (symbol) symbol, name, industry FROM scan_results WHERE symbol=ANY(:syms) ORDER BY symbol, scan_date DESC"
        ), {"syms": symbols})
        name_map = {row[0]: (row[1] or "", row[2] or "") for row in r.fetchall()}

        for s in symbols:
            name, ind = name_map.get(s, ("", ""))
            code = s[:3] if s else ""

            # 按代码前缀 + 名称关键词分类
            if code.startswith("8") or code.startswith("4"):
                arch = "small_speculative"  # 北交所/新三板
            elif code.startswith("688"):
                arch = "growth_tech"  # 科创板
            elif code.startswith("300") or code.startswith("301"):
                arch = "growth_tech"  # 创业板
            elif name and any(kw in name for kw in ["银行","保险","证券","金融","信托","白酒","食品","饮料","家电","乳业"]):
                arch = "large_bluechip"
            elif name and any(kw in name for kw in ["石油","石化","煤炭","有色","钢铁","化工","稀土","锂业","矿业","黄金","铜","铝","水泥","玻璃","纸","化纤","能源","燃气","港口","公路","铁路","航空"]):
                arch = "cyclical_resource"
            elif name and any(kw in name for kw in ["电力","水务","环保","建材","建筑","地产","农林","农业","纺织","旅游","酒店","百货","超市","医药","医疗","中药","制药","生物"]):
                arch = "value_defensive"
            elif name and any(kw in name for kw in ["科技","电子","半导体","芯片","通信","软件","互联网","机器人","光电","精密","智能","数字","数据","网络","信息","计算机","自动化"]):
                arch = "growth_tech"
            elif name and any(kw in name for kw in ["汽车","新能源","光伏","风能","电池","储能","材料"]):
                arch = "growth_tech"
            elif code.startswith("6") or code.startswith("0"):
                arch = "large_bluechip"  # 主板默认
            else:
                arch = "growth_tech"
            archetype_map[s] = arch

        logger.info(f"Code+name archetype distribution: {dict((a, list(archetype_map.values()).count(a)) for a in set(archetype_map.values()))}")

    # 6. Resolve weights + beliefs per archetype
    weights_map: dict[str, dict] = {}
    beliefs_map: dict[str, dict] = {}
    try:
        from app.services.archetype_param_resolver import resolve_scoring_weights
        from app.services.bayesian_optimizer import get_beliefs
        seen_arch = set(archetype_map.values())
        for arch in seen_arch:
            beliefs = await get_beliefs(arch)
            beliefs_map[arch] = beliefs
            weights_map[arch] = resolve_scoring_weights(arch, beliefs)
    except Exception as e:
        logger.warning(f"Weight/belief resolution failed: {e}")

    # 7. Build industry map
    industry_map: dict[str, str] = {}
    try:
        r = await session.execute(text(
            "SELECT ts_code, industry FROM ths_member WHERE out_date IS NULL AND ts_code=ANY(:syms)"
        ), {"syms": symbols})
        for row in r.fetchall():
            if row[1]:
                industry_map[row[0]] = row[1]
    except Exception:
        try: await session.rollback()
        except Exception: pass
        pass

    # 8. Batch-load K-line data（上界约束防止回扫时引入未来数据）
    kline_batch: dict[str, dict] = {}
    try:
        r = await session.execute(text(
            "SELECT ts_code, trade_date, open, high, low, close, volume "
            "FROM daily_kline WHERE ts_code=ANY(:syms) AND trade_date >= :cut AND trade_date <= :scan_date "
            "ORDER BY ts_code, trade_date"
        ), {"syms": symbols, "cut": scan_date - timedelta(days=250), "scan_date": scan_date})
        import pandas as pd
        rows = r.fetchall()
        for row in rows:
            code = row[0]
            if code not in kline_batch:
                kline_batch[code] = {"trade_date": [], "Open": [], "High": [],
                                      "Low": [], "Close": [], "Volume": []}
            for i, col in enumerate(["trade_date", "Open", "High", "Low", "Close", "Volume"]):
                if col == "trade_date":
                    kline_batch[code]["trade_date"].append(row[i+1])
                else:
                    kline_batch[code][col].append(float(row[i+1] or 0))
        # Convert to DataFrame
        for code in kline_batch:
            d = kline_batch[code]
            if d["Close"]:
                kline_batch[code] = pd.DataFrame(d)
            else:
                kline_batch[code] = None
    except Exception as e:
        logger.warning(f"K-line batch load failed: {e}")
        try: await session.rollback()
        except Exception: pass

    # 9. Preload sector toplist flow
    sector_toplist_flow: dict[str, float] = {}
    try:
        r = await session.execute(text(
            "SELECT sector, SUM(net_amount) as total_net FROM toplist_daily "
            "WHERE trade_date=:d GROUP BY sector"
        ), {"d": scan_date})
        for row in r.fetchall():
            sector_toplist_flow[row[0]] = float(row[1] or 0)
    except Exception:
        try: await session.rollback()
        except Exception: pass
        pass

    # 10. Market state
    market_state = {}
    try:
        from app.services.market_gate import get_market_state
        market_state = await get_market_state()
    except Exception:
        pass

    # 11. Preload chip perf (Tushare cyq_perf batch)
    chip_batch: dict[str, dict] = {}
    try:
        from app.services.chip_service import get_cyq_perf_batch
        chip_batch = await get_cyq_perf_batch(symbols, scan_date)
        if chip_batch:
            logger.info(f"Chip perf preloaded: {len(chip_batch)}/{len(symbols)} stocks")
    except Exception as e:
        logger.debug(f"Chip perf preload skipped: {e}")

    return {
        "symbols": symbols,
        "scan_rows": scan_rows,
        "scan_date_str": scan_date_str,
        "archetype_map": archetype_map,
        "weights_map": weights_map,
        "beliefs_map": beliefs_map,
        "industry_map": industry_map,
        "kline_batch": kline_batch,
        "chip_batch": chip_batch,
        "patterns": getattr(__import__('app.services.data_preloader', fromlist=['_pattern_cache']), '_pattern_cache', {}),
        "ambush": getattr(__import__('app.services.data_preloader', fromlist=['_ambush_cache']), '_ambush_cache', {}),
        "sector_toplist_flow": sector_toplist_flow,
        "market_state": market_state,
    }


# ═══════════ Phase 2: Per-Stock Scoring ═══════════

async def _deep_score_phase(session, ctx: dict) -> list[dict]:
    """Score each stock on 13+ dimensions using scoring/ modules.

    Returns list of dicts with dimension_scores filled.
    """
    symbols = ctx["symbols"]
    scan_rows = ctx["scan_rows"]
    kline_batch = ctx["kline_batch"]
    chip_batch = ctx.get("chip_batch", {})
    industry_map = ctx["industry_map"]
    sector_toplist_flow = ctx["sector_toplist_flow"]
    market_state = ctx["market_state"]
    results = []

    for sym in symbols:
        row = scan_rows.get(sym)
        if not row:
            continue

        symbol, name, level, tg_momentum, dist_low, j_value, vol_ratio_sr = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        buy_strength, close_price, composite_score_sr, industry, trigger_path = row[7], row[8], row[9], row[10], row[11]
        resonance_type = row[12] if len(row) > 12 else ""
        weekly_tg_momentum = row[13] if len(row) > 13 else 0

        kline_df = kline_batch.get(sym)
        sector_name = industry_map.get(sym, industry or "")

        dims = {}
        # Archetype
        arch = ctx["archetype_map"].get(sym, _arch_for_industry(sector_name))

        # TG momentum dimension (from scan)
        tg_score = round(float(np.clip((tg_momentum or 0) / 10, 0, 10)), 1)
        dims["tg_momentum"] = {"score": tg_score, "raw": tg_momentum or 0}

        # Distance from low
        dist_score = round(float(np.clip(10 - abs(dist_low or 0) * 0.5, 0, 10)), 1)
        dims["dist_low"] = {"score": dist_score, "raw": dist_low or 0}

        # J-value (KDJ — 0-100. J>80=超买风险低分, J<20=超卖机会高分)
        j_val = j_value or 0
        if j_val > 80:
            j_score = round(float(np.clip((100 - j_val) / 20 * 5, 0, 10)), 1)  # 80→5, 100→0
        elif j_val < 20:
            j_score = round(float(np.clip((20 - j_val) / 20 * 5 + 5, 5, 10)), 1)  # 0→10, 20→5
        else:
            j_score = round(float(np.clip(10 - abs(j_val - 50) / 5, 0, 10)), 1)  # 50→10, 远离50降分
        dims["j_value"] = {"score": j_score, "raw": j_value or 0}

        # K-line based scores
        if kline_df is not None and len(kline_df) >= 20:
            tech_r = score_technical(kline_df)
            if tech_r:
                dims["technical"] = {"score": round(float(np.clip((tech_r["score"] + 10) / 2, 0, 10)), 1), "raw": tech_r["score"], "detail": tech_r.get("detail", "")}

            kline_r = score_kline_game(kline_df)
            if kline_r:
                dims["kline_game"] = {"score": round(float(np.clip((kline_r["score"] + 10) / 2, 0, 10)), 1), "raw": kline_r["score"]}

            vol_r = score_vol_ratio(kline_df)
            if vol_r:
                dims["vol_ratio"] = {"score": round(float(np.clip(vol_r["score"], 0, 10)), 1), "raw": vol_r["score"]}

            arbr_r = score_arbr(kline_df)
            if arbr_r:
                dims["arbr"] = {"score": round(float(np.clip((arbr_r["score"] + 10) / 2, 0, 10)), 1), "raw": arbr_r["score"]}

            bbi_r = score_bbi(kline_df)
            if bbi_r:
                dims["bbi"] = {"score": bbi_r["score"], "raw": bbi_r.get("bbi_deviation", 0)}

            trend_r = score_trend_deviation(kline_df)
            if trend_r:
                dims["trend_deviation"] = {"score": trend_r["score"], "raw": trend_r.get("deviation_pct", 0)}

            risk_r = score_downside_risk(kline_df)
            if risk_r:
                dims["downside_risk"] = {"score": round(float(np.clip((risk_r["score"] + 10) / 2, 0, 10)), 1), "raw": risk_r["score"], "risk_level": risk_r.get("risk_level", "normal")}

            ma_r = score_ma_trend(kline_df)
            if ma_r:
                dims["ma_trend"] = {"score": round(float(np.clip((ma_r["score"] + 10) / 2, 0, 10)), 1), "raw": ma_r["score"]}

            box_r = score_multi_box(kline_df)
            if box_r is not None:
                dims["multi_box"] = {"score": box_r["score"], "raw": box_r.get("raw_score", 0), "detail": box_r.get("detail", "")}

            # Market relative
            market_pct = market_state.get("sh_index_change_pct", 0)
            mkt_r = score_market_relative(kline_df, market_pct)
            if mkt_r:
                dims["market_relative"] = {"score": round(float(np.clip((mkt_r["score"] + 10) / 2, 0, 10)), 1), "raw": mkt_r["score"]}

            # Fund flow
            fund_r = score_fund_flow(kline_df)
            if fund_r:
                dims["fund_flow"] = {"score": round(float(np.clip((fund_r["score"] + 10) / 2, 0, 10)), 1), "raw": fund_r["score"]}

            # Sector alpha
            sector_change = market_state.get("sector_change_pct", 0)
            sec_r = score_sector_alpha(kline_df, sector_change)
            if sec_r:
                dims["sector_alpha"] = {"score": round(float(np.clip((sec_r["score"] + 10) / 2, 0, 10)), 1), "raw": sec_r["score"]}

        # Fundamental score (from cache)
        try:
            funda_score, funda_detail, pb, pe = await get_fundamental_score_cached(sym)
            dims["fundamentals"] = {"score": round(float(np.clip((funda_score + 20) / 4, 0, 10)), 1), "raw": funda_score, "detail": funda_detail}
        except Exception:
            logger.warning(f"Fundamental score unavailable for {sym}")
            dims["fundamentals"] = {"score": 0.0, "raw": 0}

        # Valuation
        try:
            _, _, pb, pe = await get_fundamental_score_cached(sym)
            val_r = score_valuation(pb, pe)
            dims["valuation"] = {"score": round(float(np.clip((val_r["score"] + 10) / 2, 0, 10)), 1), "raw": val_r["score"]}
        except Exception:
            logger.warning(f"Valuation score unavailable for {sym}")
            dims["valuation"] = {"score": 0.0, "raw": 0}

        # Pattern signal
        patterns = ctx.get("patterns", {}).get(sym, "")
        pat_r = score_pattern_signal(patterns)
        if pat_r:
            dims["pattern"] = {"score": round(float(np.clip((pat_r["score"] + 10) / 2, 0, 10)), 1), "raw": pat_r["score"]}

        # Weekly resonance
        if resonance_type:
            wk_r = score_weekly_resonance(resonance_type, weekly_tg_momentum or 0)
            dims["weekly_resonance"] = {"score": wk_r["score"], "detail": wk_r["detail"]}

        # Toplist sector
        tl_r = score_toplist_sector(sym, sector_toplist_flow, industry_map)
        dims["toplist_sector"] = {"score": round(float(np.clip((tl_r["score"] + 5) / 1.5, 0, 10)), 1), "raw": tl_r["score"]}

        # Ambush score
        ambush_score = ctx.get("ambush", {}).get(sym, 0)
        dims["ambush"] = {"score": round(float(np.clip(ambush_score, 0, 10)), 1), "raw": ambush_score}

        # ── v4.8: 筹码维度 (Tushare cyq_perf) ──
        chip = chip_batch.get(sym, {})
        if chip:
            # winner_rate: 获利盘比例 → 30-50% 最优 (底部吸筹区间)
            # v4.10: 强化底部/顶部惩罚
            wr = float(chip.get("winner_rate", 50))
            if 30 <= wr <= 50:
                wr_score = 10.0 - abs(wr - 40) / 5  # 40→10, 30→8, 50→8: 黄金区间
            elif 15 <= wr < 30:
                wr_score = (wr - 15) / 15 * 5 + 2  # 15→2, 30→7: 底部吸筹中
            elif wr < 15:
                wr_score = (wr / 15) * 2  # 0→0, 15→2: 深套无底洞
            elif 50 < wr <= 70:
                wr_score = 8.0 - (wr - 50) / 20 * 3  # 50→8, 70→5: 获利区但尚可
            elif 70 < wr <= 85:
                wr_score = 5.0 - (wr - 70) / 15 * 3  # 70→5, 85→2: 高位风险
            else:
                wr_score = max(0.0, 2.0 - (wr - 85) / 15 * 2)  # 85→2, 100→0: 庄家出货
            dims["chip_winner"] = {"score": round(float(np.clip(wr_score, 0, 10)), 1),
                                    "raw": wr}

            # cost_50pct vs current_price: 成本支撑强度
            cost50 = float(chip.get("cost_50pct", 0))
            if cost50 > 0 and close_price > 0:
                cost_dist = (close_price - cost50) / cost50 * 100  # 当前价距中位成本%
                if -10 <= cost_dist <= 10:
                    cost_score = 8.0 - abs(cost_dist) * 0.6  # 价在成本线附近→高支撑
                elif cost_dist < -20:
                    cost_score = 3.0  # 暴跌远离成本区, 无支撑
                elif cost_dist > 20:
                    cost_score = 5.0 - (cost_dist - 20) * 0.2  # 涨幅过大远离成本
                else:
                    cost_score = 6.0 - abs(cost_dist - (10 if cost_dist > 0 else -10)) * 0.3
                dims["chip_cost"] = {"score": round(float(np.clip(cost_score, 0, 10)), 1),
                                     "raw": round(cost_dist, 2)}
        else:
            # 无筹码数据: 默认 5 分, 等数据
            dims["chip_winner"] = {"score": 5.0, "raw": 0}
            dims["chip_cost"] = {"score": 5.0, "raw": 0}

        results.append({
            "symbol": sym,
            "name": name,
            "archetype": arch,
            "close_price": close_price,
            "industry": sector_name,
            "level": level,
            "tg_momentum": tg_momentum or 0,
            "resonance_type": resonance_type,
            "dimension_scores": dims,
        })

    return results


# ═══════════ Phase 3: Enrich (gates + weights + bonuses) ═══════════

async def _deep_enrich_phase(session, results: list[dict], ctx: dict) -> list[dict]:
    """Apply fundamental gate, archetype weights, sector bonuses, multi-timeframe, toplist, event impact."""
    weights_map = ctx.get("weights_map", {})
    scan_date_str = ctx.get("scan_date_str", "")
    market_state = ctx.get("market_state", {})

    # ── ★ P0: Macro impact (Tier 1, precomputed once for all stocks) ──
    macro_adj = 0.0
    try:
        from app.services.macro_data import score_macro_impact
        macro_adj, _ = await score_macro_impact()
    except Exception:
        pass
    logger.info(f"Macro impact this scan: {macro_adj:+.1f}")

    # ── ★ v4.10: 原型历史胜率加权 — 避免低胜率原型持续打出高分 ──
    proto_wr_map: dict[str, float] = {}
    try:
        from sqlalchemy import text as _text
        from app.core.database import async_session_factory as _asf
        async with _asf() as wr_sess:
            r = await wr_sess.execute(_text("""
                SELECT archetype,
                       COUNT(*) FILTER(WHERE outcome_label IN ('strong_win','weak_win'))::float
                       / NULLIF(COUNT(*) FILTER(WHERE outcome_label IS NOT NULL), 0) * 100 as wr
                FROM signal_history
                WHERE archetype IS NOT NULL
                  AND scan_date >= :cut
                GROUP BY archetype
            """), {"cut": scan_date_str})
            for row in r.fetchall():
                proto_wr_map[row[0]] = float(row[1]) if row[1] else 50.0
        logger.info(f"Prototype win rates: {', '.join(f'{k}={v:.0f}%' for k,v in sorted(proto_wr_map.items()))}")
    except Exception:
        pass

    for r in results:
        sym = r["symbol"]
        arch = r["archetype"]
        dims = r.get("dimension_scores", {})
        weights = weights_map.get(arch, dict(DEFAULT_WEIGHTS))

        # ── Fundamental gate adjustment ──
        funda_score = dims.get("fundamentals", {}).get("raw", 0)
        funda_adj = 0.0
        if funda_score < -10:
            funda_adj = -2.0
        elif funda_score < -5:
            funda_adj = -1.0
        elif funda_score < 0:
            funda_adj = -0.5
        r["fundamental_adjustment"] = round(funda_adj, 1)

        # ── Archetype weight synthesis ──
        dim_keys_map = {
            "technical": "tech_weight", "kline_game": "kline_weight",
            "fund_flow": "fund_weight", "tg_momentum": "tg_momentum_weight",
            "vol_ratio": "vol_ratio_weight", "arbr": "arbr_weight",
            "sector_alpha": "sector_alpha_weight", "market_relative": "market_relative_weight",
            "valuation": "valuation_weight", "ma_trend": "ma_trend_weight",
            "pattern": "pattern_weight", "trend_deviation": "trend_deviation_weight",
            "bbi": "bbi_weight", "multi_box": "box_weight",
            "fundamentals": "fundamentals_weight",
            # Phase 73: 补入之前遗漏的子维度
            "dist_low": "dist_low_weight", "j_value": "j_value_weight",
            "downside_risk": "downside_risk_weight",
            # v4.8: 筹码维度 (Tushare cyq_perf)
            "chip_winner": "chip_winner_weight", "chip_cost": "chip_cost_weight",
        }
        weighted_sum = 0.0
        weight_total = 0.0
        for dim_key, weight_key in dim_keys_map.items():
            if dim_key in dims:
                w = weights.get(weight_key, DEFAULT_WEIGHTS.get(weight_key, 1.5))
                s = dims[dim_key].get("score", 5.0)
                weighted_sum += w * s
                weight_total += w
        # Phase 73: extra dimensions 也变为可训练权重
        for extra_dim in ["weekly_resonance", "toplist_sector", "ambush"]:
            if extra_dim in dims:
                wk = f"{extra_dim}_weight"
                w = weights.get(wk, DEFAULT_WEIGHTS.get(wk, 0.5))
                weighted_sum += w * dims[extra_dim].get("score", 5.0)
                weight_total += w

        raw_total = weighted_sum / weight_total * 10 if weight_total > 0 else 50
        r["raw_total"] = round(raw_total, 1)
        r["weight_snapshot"] = {k: round(v, 2) for k, v in weights.items()}

        # ── ★ v4.10: 原型胜率折扣 — 低胜率原型全组成绩打折 ──
        proto_wr = proto_wr_map.get(arch, 50)
        if proto_wr < 30:
            proto_discount = 0.65  # 原型胜率<30% → 几乎不可能盈利，强折扣
        elif proto_wr < 35:
            proto_discount = 0.78
        elif proto_wr < 40:
            proto_discount = 0.88
        elif proto_wr >= 45:
            proto_discount = 1.05  # 高胜率原型微幅奖励
        else:
            proto_discount = 1.0
        r["proto_win_rate"] = round(proto_wr, 1)
        r["proto_discount"] = round(proto_discount, 2)

        # ── Sector bonus ──
        sector_bonus = 0.0
        try:
            from app.services.sector_heat_engine import get_stock_sector_factor
            sf = await get_stock_sector_factor(sym)
            if sf:
                if sf.get("heat_level") == "hot":
                    sector_bonus = weights.get("sector_bonus_l3", 1.5)
                elif sf.get("heat_level") == "warm":
                    sector_bonus = weights.get("sector_bonus_l2", 0.5)
        except Exception:
            pass
        r["sector_bonus"] = round(sector_bonus, 1)

        # ── ✦ Macro impact (precomputed Tier 1, shared by all stocks) ──
        r["macro_adjustment"] = round(float(macro_adj), 1)

        # ── Event impact ──
        event_impact = 0.0
        try:
            from app.services.event_detector import score_event_impact
            event_impact = await score_event_impact(sym)
        except Exception:
            pass
        r["event_impact"] = round(float(event_impact), 1)

        # ── Market correction (含宏观调整) ──
        regime = market_state.get("regime", "unknown")
        risk = market_state.get("risk", "unknown")
        r["market_correction"] = f"regime={regime} risk={risk} macro={macro_adj:+.1f}"

        # ── Adjustment reasons ──
        reasons = []
        if funda_adj != 0:
            reasons.append(f"基本面调整{funda_adj:+.1f}")
        if sector_bonus > 0:
            reasons.append(f"板块加成+{sector_bonus:.1f}")
        if abs(event_impact) > 1:
            reasons.append(f"事件影响{event_impact:+.1f}")
        if abs(macro_adj) > 0.5:
            reasons.append(f"宏观调整{macro_adj:+.1f}")
        r["adjustment_reasons"] = reasons

    # ── 基建层注入: 三层相对强弱 (Phase 26e) ──
    try:
        from app.services.sector_context import load_sector_context
        from app.core.database import async_session_factory as _asf
        scan_date_val = ctx.get("scan_date_str", "")
        if scan_date_val:
            from datetime import date as _dt
            sd = _dt.fromisoformat(scan_date_val) if isinstance(scan_date_val, str) else scan_date_val
        else:
            sd = None

        if sd:
            async with _asf() as fresh_session:  # 独立 session 避免管线事务污染
                ctx_sector = await load_sector_context(fresh_session, sd, [r["symbol"] for r in results])
            market_5d = ctx_sector.get("market_5d", 0)
            stock_sector_map = ctx_sector.get("stock_sector", {})

            for r in results:
                sym = r["symbol"]
                si = stock_sector_map.get(sym, {})
                stock_5d = si.get("stock_5d", 0)
                sector_5d = si.get("pct_5d", market_5d)
                sector_dir = si.get("direction", "震荡")
                lifecycle = si.get("lifecycle", "正常")
                rank_5d = si.get("rank_5d", 16)

                # ── 8 种相对位置判定 ──
                sector_up = sector_5d > 0.5
                market_up = market_5d > 0.3
                stock_beats_sector = stock_5d > sector_5d + 1.0

                if sector_up and market_up and stock_beats_sector:
                    position, adjustment = "领涨龙头", 5
                elif sector_up and market_up and not stock_beats_sector:
                    position, adjustment = "跟涨", 0
                elif sector_up and market_up and stock_5d < -1:
                    position, adjustment = "主力出货", -5
                elif sector_up and not market_up and stock_beats_sector:
                    position, adjustment = "独立走强", 8
                elif not sector_up and market_up and stock_beats_sector:
                    position, adjustment = "逆势抗跌", 2
                elif not sector_up and not market_up and stock_5d < sector_5d - 1:
                    position, adjustment = "领跌", -8
                elif not sector_up and not market_up and stock_beats_sector:
                    position, adjustment = "逆势拉升", 5
                else:
                    position, adjustment = "抗跌", 0

                # 修正 composite_score (含 v4.10 原型胜率折扣)
                adj = r.get("proto_discount", 1.0)
                r["composite_score"] = round(max(0, min(100, (r.get("composite_score", 50) + adjustment) * adj)), 1)
                r["relative_position"] = position
                r["sector_direction"] = sector_dir
                r["sector_lifecycle"] = lifecycle
                r["sector_rank_5d"] = rank_5d
                r["market_5d"] = round(market_5d, 1)

                # 板块退潮 + 个股领跌 → risk_label 升级
                if lifecycle == "退潮" and position in ("领跌", "主力出货"):
                    if r.get("risk_label", "") in ("", "warn"):
                        r["risk_label"] = "danger"
    except Exception as e:
        logger.warning(f"Sector context unavailable, skipping: {e}")

    # ── Phase 49a/52: 新闻信号加权 (news_aggregated → composite_score, 三级门控) ──
    try:
        import json
        from datetime import date as _dt
        from app.core.database import async_session_factory as _asf2
        _scan_d = _dt.fromisoformat(scan_date_str) if isinstance(scan_date_str, str) else scan_date_str

        async with _asf2() as ns_session:  # 独立 session 避免管线事务污染
            # 加载已验证的有效映射
            active_map: set[tuple[str, str, str]] = set()
            try:
                r_nv = await ns_session.execute(text(
                    "SELECT commodity, direction, symbol FROM news_verify WHERE is_active = TRUE"
                ))
                for nv_row in r_nv.fetchall():
                    active_map.add((nv_row[0], nv_row[1], nv_row[2]))
            except Exception:
                pass

            r_news = await ns_session.execute(text("""
                SELECT na.commodity, na.direction, na.intensity, na.stocks_json, na.category
                FROM news_aggregated na WHERE na.date = :d
            """), {"d": _scan_d})
            news_rows = r_news.fetchall()

            if not news_rows:
                return results  # clean exit — no news to inject

            # 构建 symbol → news adjustments 快速查找表
            news_adj: dict[str, list[tuple[str, float, str, str]]] = {}
            tier_counts = {"verified": 0, "commodity": 0, "minimal": 0}
            for row in news_rows:
                commodity = row[0]
                direction = row[1]
                intensity = float(row[2])
                stocks_json = row[3]
                category = row[4]
                if not stocks_json:
                    continue
                try:
                    stocks = json.loads(stocks_json) if isinstance(stocks_json, str) else stocks_json
                except Exception:
                    continue
                multiplier = 3 if category in ("policy", "macro") else 1
                for sym in stocks:
                    key = (commodity, direction, sym)
                    # Phase 52: 三级门控
                    if active_map and key in active_map:
                        tier = 1.0;   tier_counts["verified"] += 1
                    elif category == "commodity":
                        tier = 0.3;   tier_counts["commodity"] += 1
                    else:
                        tier = 0.1;   tier_counts["minimal"] += 1

                    adj = round(intensity * multiplier * tier * (3 if direction == "利好" else -3), 1)
                    label = f"{commodity}{direction}×{intensity:.2f}"
                    news_adj.setdefault(sym, []).append((adj, intensity, label, category))

            # 应用到 results
            applied = 0
            for r in results:
                sym = r["symbol"]
                sym_adjs = news_adj.get(sym, [])
                if sym_adjs:
                    best = max(sym_adjs, key=lambda x: abs(x[0]))
                    adj_val, intensity, label, category = best
                    r["composite_score"] = round(max(0, min(100, r.get("composite_score", 50) + adj_val)), 1)
                    r["news_signal"] = label
                    applied += 1

            if applied:
                logger.info(f"Phase 52: news applied to {applied}/{len(results)} stocks "
                           f"(v={tier_counts['verified']} c={tier_counts['commodity']} "
                           f"m={tier_counts['minimal']})")
    except Exception as e:
        logger.debug(f"News signals unavailable: {e}")

    return results


# ═══════════ Phase 4: Normalize ═══════════

def _deep_normalize_phase(results: list[dict]) -> list[dict]:
    """Normalize within archetype, compute composite_score, calibrate probability."""
    if not results:
        return results

    # Normalize within archetype
    results = _normalize_within_archetype(results)

    # Apply market gate corrections + sector bonus
    for r in results:
        raw_total = r.get("raw_total", 50)
        sector_bonus = r.get("sector_bonus", 0)
        event_impact = r.get("event_impact", 0)
        funda_adj = r.get("fundamental_adjustment", 0)

        # Composite = normalized base + sector bonus + event impact + fundamental adj
        composite = r.get("composite_score", raw_total) + sector_bonus * 1.5 + event_impact * 0.3 + funda_adj
        r["composite_score"] = round(float(np.clip(composite, 0, 100)), 1)

        # Probability calibration
        try:
            from app.services.probability_calibrator import calibrate_with_regime
            wp = calibrate_with_regime(r["composite_score"], r.get("archetype", "unknown"), signal_quality=None)
            r["win_probability"] = round(float(wp), 4) if wp is not None else 0.35
        except Exception:
            r["win_probability"] = round(float(np.clip(r["composite_score"] / 200 + 0.05, 0.05, 0.65)), 4)

        # Signal quality — 基于综合分和胜率估算
        r["signal_quality"] = round(float(np.clip(r.get("composite_score", 50) / 100 * 0.8 + r.get("win_probability", 0.3) * 0.4, 0.1, 0.95)), 3)
        r["strategy_label"] = derive_strategy_label(r)

        # Tech score / kline score / fund score for API compatibility
        dims = r.get("dimension_scores", {})
        r["tech_score"] = dims.get("technical", {}).get("score", 5.0)
        r["kline_score"] = dims.get("kline_game", {}).get("score", 5.0)
        r["fund_score"] = dims.get("fund_flow", {}).get("score", 5.0)
        r["trend_score"] = dims.get("ma_trend", {}).get("score", 5.0)
        r["entry_score"] = dims.get("multi_box", {}).get("score", 5.0)
        r["downside_risk"] = dims.get("downside_risk", {}).get("score", 5.0)

    return results


# ═══════════ Phase 5: Persist ═══════════

async def _deep_persist_phase(session, results: list[dict], session_date) -> None:
    """UPSERT analysis_scores + INSERT recommendation_tracking.

    v4.12: 每个 INSERT 用 savepoint 隔离，一行失败不影响其他行.
    v4.13: 如果 session 事务已被 abort，回滚并重新开始.
    """
    import json

    for r in results:
        sym = r["symbol"]
        try:
            # UPSERT analysis_scores
            await session.execute(text("""
                INSERT INTO analysis_scores (
                    scan_date, symbol, name, tech_score, kline_score, fund_score,
                    sector_bonus, composite_score, fundamental_adjustment,
                    market_correction, details, archetype, weight_snapshot,
                    adjustment_reasons, dimension_scores, win_probability, downside_risk,
                    signal_quality, trend_score, entry_score, signal_count, strategy_label
                ) VALUES (
                    :sd, :sym, :name, :ts, :ks, :fs,
                    :sb, :cs, :fa,
                    :mc, :det, :arch, :ws,
                    :ar, :dim, :wp, :dr,
                    :sq, :tsc, :esc, :sc, :sl
                ) ON CONFLICT (scan_date, symbol) DO UPDATE SET
                    name=EXCLUDED.name, tech_score=EXCLUDED.tech_score,
                    kline_score=EXCLUDED.kline_score, fund_score=EXCLUDED.fund_score,
                    sector_bonus=EXCLUDED.sector_bonus, composite_score=EXCLUDED.composite_score,
                    fundamental_adjustment=EXCLUDED.fundamental_adjustment,
                    market_correction=EXCLUDED.market_correction,
                    details=EXCLUDED.details, archetype=EXCLUDED.archetype,
                    weight_snapshot=EXCLUDED.weight_snapshot,
                    adjustment_reasons=EXCLUDED.adjustment_reasons,
                    dimension_scores=EXCLUDED.dimension_scores,
                    win_probability=EXCLUDED.win_probability,
                    downside_risk=EXCLUDED.downside_risk,
                    signal_quality=EXCLUDED.signal_quality,
                    trend_score=EXCLUDED.trend_score,
                    entry_score=EXCLUDED.entry_score,
                    signal_count=EXCLUDED.signal_count,
                    strategy_label=EXCLUDED.strategy_label
            """), {
                "sd": session_date,
                "sym": sym,
                "name": r.get("name", sym),
                "ts": r.get("tech_score", 5.0),
                "ks": r.get("kline_score", 5.0),
                "fs": r.get("fund_score", 5.0),
                "sb": r.get("sector_bonus", 0),
                "cs": r.get("composite_score", 50),
                "fa": r.get("fundamental_adjustment", 0),
                "mc": r.get("market_correction", ""),
                "det": json.dumps(sanitize_for_json({
                    "dimension_scores": r.get("dimension_scores", {}),
                    "predicted_return": r.get("predicted_return"),
                    "predicted_win_prob": r.get("predicted_win_prob"),
                    "macro_adjustment": r.get("macro_adjustment", 0),
                    # Phase 26e: 三层相对强弱
                    "relative_position": r.get("relative_position"),
                    "sector_direction": r.get("sector_direction"),
                    "sector_lifecycle": r.get("sector_lifecycle"),
                    "sector_rank_5d": r.get("sector_rank_5d"),
                    "market_5d": r.get("market_5d"),
                    # Phase 49a: 新闻信号
                    "news_signal": r.get("news_signal"),
                    "limit_up_flag": r.get("limit_up_flag"),
                    # Phase 55: 排序分
                    "rank_score": r.get("rank_score"),
                })),
                "arch": r.get("archetype", "small_speculative"),
                "ws": json.dumps(sanitize_for_json(r.get("weight_snapshot", {}))),
                "ar": json.dumps(sanitize_for_json(r.get("adjustment_reasons", []))),
                "dim": json.dumps(sanitize_for_json(r.get("dimension_scores", {}))),
                "wp": r.get("win_probability", 0.35),
                "dr": r.get("downside_risk", 5.0),
                "sq": r.get("signal_quality", 0.5),
                "tsc": r.get("trend_score", 5),
                "esc": r.get("entry_score", 5),
                "sc": r.get("signal_count", 0),
                "sl": r.get("strategy_label", None),
            })

            # INSERT recommendation_tracking
            await session.execute(text("""
                INSERT INTO recommendation_tracking (scan_date, symbol, rank, composite_score, close_price)
                VALUES (:sd, :sym, :rank, :cs, :cp)
                ON CONFLICT (scan_date, symbol) DO UPDATE SET
                    composite_score=EXCLUDED.composite_score, close_price=EXCLUDED.close_price
            """), {
                "sd": session_date,
                "sym": sym,
                "rank": 0,
                "cs": r.get("composite_score", 50),
                "cp": r.get("close_price", 0),
            })
        except Exception as e:
            logger.error(f"Persist failed for {sym}: {e}")
            try:
                await session.rollback()  # 回滚 abort 的事务
            except Exception:
                pass  # 事务已清
            continue  # 下一行重建连接

    try:
        await session.commit()
        logger.info(f"Persisted {len(results)} analysis scores for {session_date}")
    except Exception as e:
        logger.error(f"Commit failed: {e}")
        await session.rollback()


# ═══════════ Main Orchestrator ═══════════

async def deep_analyze(session, scan_date=None, session_date=None, min_composite_score=0, progress_cb=None):
    """14-dimension deep scoring pipeline — 5-phase orchestration.

    Phase 1: Preload all prerequisite data
    Phase 2: Score each stock on 13+ dimensions
    Phase 3: Enrich with gates, weights, bonuses
    Phase 4: Normalize within archetype + calibrate
    Phase 5: Persist to analysis_scores + recommendation_tracking

    Returns list of scored result dicts.
    """
    if scan_date is None:
        r = await session.execute(text("SELECT MAX(scan_date) FROM scan_results"))
        scan_date = r.scalar()
        if not scan_date:
            return []

    if session_date is None:
        session_date = scan_date

    # Phase 1: Preload
    if progress_cb: await progress_cb("preload", 1, 5, "加载指纹+K线+基本面...")
    # Phase 47: count L1 before filtering
    r = await session.execute(text(
        "SELECT COUNT(*) FILTER(WHERE COALESCE(level,'L1')='L1'), COUNT(*)"
        " FROM scan_results WHERE scan_date=:d"
    ), {"d": scan_date})
    l1_count, total_count = r.fetchone()
    if l1_count:
        logger.info(f"Phase 47: filtering {l1_count}/{total_count} L1 weak signals")
    r = await session.execute(text(
        "SELECT symbol FROM scan_results "
        "WHERE scan_date=:d AND COALESCE(level,'L1') != 'L1' ORDER BY symbol"
    ), {"d": scan_date})
    symbols = [row[0] for row in r.fetchall()]
    if not symbols:
        logger.warning(f"No scan results for {scan_date}")
        return []

    # ── Phase 69: 涨跌停入口过滤 — 涨停封板股直接排除, 不进评分管线 ──
    r_chg = await session.execute(text("""
        WITH latest AS (
            SELECT DISTINCT ON (ts_code) ts_code, close,
                   LAG(close, 1) OVER (PARTITION BY ts_code ORDER BY trade_date) AS prev_close
            FROM daily_kline
            WHERE ts_code = ANY(:syms) AND trade_date <= :d
            ORDER BY ts_code, trade_date DESC
        )
        SELECT ts_code, close, prev_close FROM latest WHERE prev_close > 0
    """), {"syms": symbols, "d": scan_date})
    sealed_syms: set[str] = set()
    for row in r_chg.fetchall():
        sym = row[0]; c = float(row[1]); pc = float(row[2])
        if pc <= 0: continue
        pct = round((c - pc) / pc * 100, 2)
        if sym.startswith('30') or sym.startswith('688'):    limit = 20.0
        elif sym.startswith('8') or sym.startswith('4'):     limit = 30.0
        else:                                                 limit = 10.0
        if pct >= limit * 0.95:
            sealed_syms.add(sym)

    if sealed_syms:
        symbols = [s for s in symbols if s not in sealed_syms]
        logger.info(f"Phase 69: excluding {len(sealed_syms)} limit-up stocks before scoring "
                    f"(remaining: {len(symbols)})")
    if not symbols:
        logger.warning(f"All symbols excluded by limit-up gate")
        return []

    ctx = await _deep_preload_phase(session, symbols, scan_date)

    # Phase 2: Score
    if progress_cb: await progress_cb("score", 2, 5, f"逐股评分 {len(symbols)}只...")
    results = await _deep_score_phase(session, ctx)
    if not results:
        logger.warning("No stocks passed scoring phase")
        return []

    # Phase 3: Enrich
    if progress_cb: await progress_cb("enrich", 3, 5, f"行业对比+板块门控 {len(results)}只...")
    results = await _deep_enrich_phase(session, results, ctx)

    # Phase 4: Normalize
    if progress_cb: await progress_cb("normalize", 4, 5, "组内归一化+模型预测...")
    results = _deep_normalize_phase(results)

    # ★ Predictive model blend (v4.8): 仅在 <=300 条时启用 (scan 路径样本太多)
    if len(results) <= 300:
        try:
            from app.services.predictive_scorer import batch_predict
            symbols_to_predict = [r["symbol"] for r in results]
            if symbols_to_predict and results:
                preds = await batch_predict(symbols_to_predict, scan_date, session)
                for r in results:
                    pred = preds.get(r["symbol"])
                    if pred:
                        r["predicted_return"] = pred["predicted_return"]
                        r["predicted_win_prob"] = pred["win_probability"]
                        if pred["predicted_return"] > 5:
                            r["composite_score"] = round(min(100, r["composite_score"] + 10), 1)
                        elif pred["predicted_return"] > 0:
                            r["composite_score"] = round(min(100, r["composite_score"] + 5), 1)
                        elif pred["predicted_return"] < -3:
                            r["composite_score"] = round(max(0, r["composite_score"] - 5), 1)
        except Exception as e:
            logger.warning(f"Predictive model unavailable: {e}")

    # ★ Phase 55: 排序学习注入 — 模型学会"同批中谁更强"
    if len(results) >= 10:
        try:
            from app.services.predictive_scorer import rank_stocks
            symbols_to_rank = [r["symbol"] for r in results]
            rank_scores = await rank_stocks(symbols_to_rank, scan_date, session)
            if rank_scores:
                for r in results:
                    rs = rank_scores.get(r["symbol"])
                    if rs is not None:
                        r["rank_score"] = round(rs, 3)
                        # 排序分 ≥ 0.7 → 排序器高度确信该股在同批中更强
                        if rs >= 0.7:
                            r["composite_score"] = round(min(100, r["composite_score"] + 5), 1)
                        elif rs <= 0.3:
                            r["composite_score"] = round(max(0, r["composite_score"] - 5), 1)
        except Exception as e:
            logger.debug(f"Ranker unavailable: {e}")

    # ── Phase 68: 去重 — 全局 100 分只能有一个，98+ 按 raw_total 微调拉开 ──
    if len(results) >= 2:
        sorted_all = sorted(results, key=lambda r: (r.get("composite_score", 0), r.get("raw_total", 0)), reverse=True)
        dup_count: dict[float, int] = {}
        for r in sorted_all:
            cs = round(r.get("composite_score", 0), 1)
            if cs >= 98:
                n = dup_count.get(cs, 0)
                if n >= 1:
                    penalty = n * 0.8
                    r["composite_score"] = round(max(85.0, cs - penalty), 1)
                dup_count[cs] = n + 1

    # Phase 5: Persist
    if progress_cb: await progress_cb("persist", 5, 5, f"写入数据库 {len(results)}条...")
    await _deep_persist_phase(session, results, session_date)

    # Filter by min quality gate
    filtered = [r for r in results if r.get("composite_score", 0) >= min_composite_score]

    logger.info(f"deep_analyze complete: {len(results)} scored, {len(filtered)} passed gate")
    return filtered

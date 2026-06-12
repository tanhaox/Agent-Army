"""LLM 深度分析 — 提示词生成 + 反馈解析.

流程:
  选中股票 → 生成含11维上下文的提示词 → 用户复制到DeepSeek网页版
  → 得到回复 → 浏览器扩展一键反哺 → feedback_parser解析
"""
import json, logging, re
from app.core.database import async_session_factory
from sqlalchemy import text

logger = logging.getLogger(__name__)

SIGNAL_ADJUSTMENTS = {
    "valuation": {"score_modifier": -8, "weight_factor": 0.9},
    "financial_risk": {"score_modifier": -15, "weight_factor": 0.8},
    "fund_flow": {"score_modifier": -10, "weight_factor": 0.85},
    "technical_risk": {"score_modifier": -6, "weight_factor": 0.95},
    "sentiment_risk": {"score_modifier": -12, "weight_factor": 0.8},
    "opportunity": {"score_modifier": +10, "weight_factor": 1.05},
    "other": {"score_modifier": 0, "weight_factor": 1.0},
}


async def get_stock_context(symbol: str) -> dict:
    """获取股票的完整上下文：快照 + 11维评分 + 原型 + ★技术面价格."""
    async with async_session_factory() as s:
        r = await s.execute(text("""
            SELECT roe, revenue_yoy, profit_yoy, debt_to_assets, current_ratio,
                   ocflow_net, pb, pe_ttm
            FROM stock_fundamental_snapshot WHERE symbol=:sym
        """), {"sym": symbol})
        row = r.fetchone()
        snapshot = {}
        if row:
            cols = ["roe","revenue_yoy","profit_yoy","debt_to_assets","current_ratio","ocflow_net","pb","pe_ttm"]
            snapshot = {c: (round(float(row[i]), 2) if row[i] is not None else None) for i, c in enumerate(cols)}

        r = await s.execute(text("""
            SELECT a.composite_score, a.tech_score, a.kline_score, a.fund_score,
                   a.fundamental_adjustment, a.archetype, a.adjustment_reasons,
                   s.tg_momentum, s.level, s.trigger_path, s.dist_low, s.j_value,
                   s.vol_ratio, s.buy_strength
            FROM analysis_scores a
            LEFT JOIN scan_results s ON s.symbol=a.symbol AND s.scan_date=a.scan_date
            WHERE a.symbol=:sym AND a.scan_date=(SELECT MAX(scan_date) FROM analysis_scores)
        """), {"sym": symbol})
        row = r.fetchone()
        scoring = {}
        if row:
            scoring = {
                "composite_score": float(row[0]) if row[0] else 0,
                "tech_score": float(row[1]) if row[1] else 0,
                "kline_score": float(row[2]) if row[2] else 0,
                "fund_score": float(row[3]) if row[3] else 0,
                "fundamental_adjustment": float(row[4]) if row[4] else 0,
                "archetype": row[5] or "unknown",
                "adjustment_reasons": row[6] if row[6] else [],
                "tg_momentum": float(row[7]) if row[7] else 0,
                "level": row[8] or "",
                "trigger_path": row[9] or "",
                "dist_low": float(row[10]) if row[10] else 0,
                "j_value": float(row[11]) if row[11] else 0,
                "vol_ratio": float(row[12]) if row[12] else 0,
                "buy_strength": float(row[13]) if row[13] else 0,
            }

    # ★ 技术面价格数据
    price_info = await _get_price_context(symbol)

    return {"snapshot": snapshot, "scoring": scoring, "price": price_info}


async def _get_price_context(symbol: str) -> dict:
    """获取实际价格数据：MA均线、近期高低点、支撑/压力."""
    from datetime import date as dt_date
    try:
        async with async_session_factory() as s:
            r = await s.execute(text("""
                SELECT trade_date, close, high, low, volume
                FROM daily_kline WHERE ts_code=:s
                ORDER BY trade_date DESC LIMIT 120
            """), {"s": symbol})
            rows = list(reversed(r.fetchall()))

        if len(rows) < 20:
            return {"error": "K线数据不足"}

        import numpy as np
        closes = np.array([float(r[1] or 0) for r in rows])
        highs = np.array([float(r[2] or closes[i]) for i, r in enumerate(rows)])
        lows = np.array([float(r[3] or closes[i]) for i, r in enumerate(rows)])
        vols = np.array([float(r[4] or 0) for r in rows])

        n = len(closes)
        current = float(closes[-1])

        # MA均线
        def _ma(arr, p):
            if n >= p: return round(float(np.mean(arr[-p:])), 2)
            return None
        ma5 = _ma(closes, 5); ma10 = _ma(closes, 10)
        ma20 = _ma(closes, 20); ma60 = _ma(closes, 60) if n >= 60 else None

        # 近期高低点
        h20 = float(np.max(highs[-20:])); l20 = float(np.min(lows[-20:]))
        h60 = float(np.max(highs[-60:])) if n >= 60 else h20
        l60 = float(np.min(lows[-60:])) if n >= 60 else l20

        # 均线排列
        mas = [m for m in [ma5, ma10, ma20, ma60] if m is not None]
        if len(mas) >= 3:
            if all(mas[i] > mas[i+1] for i in range(len(mas)-1)):
                ma_arrange = "多头排列(↑)"
            elif all(mas[i] < mas[i+1] for i in range(len(mas)-1)):
                ma_arrange = "空头排列(↓)"
            else:
                ma_arrange = "交织(震荡)"
        else:
            ma_arrange = "数据不足"

        # 量比 (5日 vs 20日)
        vol5 = float(np.mean(vols[-5:])) if n >= 5 else 0
        vol20 = float(np.mean(vols[-20:]))
        vol_ratio_local = round(vol5 / vol20, 2) if vol20 > 0 else 1.0

        # 5日涨幅
        chg5 = round((closes[-1] / closes[-5] - 1) * 100, 2) if n >= 5 else 0
        chg20 = round((closes[-1] / closes[-20] - 1) * 100, 2) if n >= 20 else 0

        # 支撑/压力
        from app.services.ma_scorer import calc_support_resistance
        try:
            sr = await calc_support_resistance(symbol, dt_date.today())
        except Exception:
            sr = None

        return {
            "current": round(current, 2),
            "ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60,
            "ma_arrange": ma_arrange,
            "high_20d": round(h20, 2), "low_20d": round(l20, 2),
            "high_60d": round(h60, 2), "low_60d": round(l60, 2),
            "vol_ratio_5v20": vol_ratio_local,
            "chg_5d_pct": chg5, "chg_20d_pct": chg20,
            "support": sr.get("support") if sr else None,
            "support2": sr.get("support2") if sr else None,
            "resistance": sr.get("resistance") if sr else None,
            "resistance2": sr.get("resistance2") if sr else None,
            "data_points": n,
        }
    except Exception as e:
        return {"error": str(e)}


def build_analysis_prompt(symbol: str, name: str, context: dict,
                          macro_context: str = "") -> str:
    """生成发送给 DeepSeek 的完整分析提示词.

    包含: ★ 宏观环境(v4.3) + ★实际价格/均线/支撑压力位 + ★筹码分布 + T+2胜率 + 14维分解 + 基本面 + 策略原型.
    """
    snap = context.get("snapshot", {})
    sc = context.get("scoring", {})
    px = context.get("price", {})
    chip = context.get("chip", {})

    archetype_labels = {
        "large_bluechip": "大盘蓝筹(基本面权重高,技术面权重低)",
        "small_speculative": "小盘题材(技术面权重高,基本面权重低)",
        "growth_tech": "成长科技(成长性+创新驱动)",
        "value_defensive": "价值防御(低估值+高股息+低波动)",
        "cyclical_resource": "周期资源(商品联动+高杠杆)",
    }
    arch_label = archetype_labels.get(sc.get("archetype", ""), sc.get("archetype", "未知"))

    # ★ 技术面价格段 (精确到分)
    if px and "error" not in px:
        current = px.get("current") or px.get("close") or 0
        lines = [f"  现价: ¥{current}"]
        if px.get("ma5"):
            lines.append(f"  MA5: ¥{px['ma5']} | MA10: ¥{px.get('ma10','—')} | MA20: ¥{px.get('ma20','—')} | MA60: ¥{px.get('ma60','—')}")
            lines.append(f"  均线排列: {px.get('ma_arrange', '—')}")
        if px.get("high_20d"):
            lines.append(f"  20日最高: ¥{px['high_20d']} | 20日最低: ¥{px['low_20d']}")
        if px.get("chg_5d_pct") is not None:
            lines.append(f"  5日涨幅: {px['chg_5d_pct']:+.1f}% | 20日涨幅: {px.get('chg_20d_pct',0):+.1f}%")
            lines.append(f"  量比(5日/20日): {px.get('vol_ratio_5v20', '—')}")
        if px.get("support"):
            s2 = f", 次: ¥{px['support2']}" if px.get("support2") else ""
            lines.append(f"  ▲ 支撑位: ¥{px['support']}{s2} (系统计算)")
        if px.get("resistance"):
            r2 = f", 次: ¥{px['resistance2']}" if px.get("resistance2") else ""
            lines.append(f"  ▼ 压力位: ¥{px['resistance']}{r2} (系统计算)")
        price_str = "\n".join(lines)
    else:
        price_str = "  价格数据暂不可用"

    # 基本面 (稀疏友好)
    snap_has_data = any(v is not None for v in snap.values())
    if snap_has_data:
        snap_lines = []
        for k, v in snap.items():
            labels = {"roe": "ROE(%)", "revenue_yoy": "营收增速(%)", "profit_yoy": "利润增速(%)",
                      "debt_to_assets": "资产负债率(%)", "current_ratio": "流动比率",
                      "ocflow_net": "经营现金流(元)", "pb": "PB", "pe_ttm": "PE_TTM"}
            if v is not None:
                snap_lines.append(f"  {labels.get(k, k)}: {v}")
            else:
                snap_lines.append(f"  {labels.get(k, k)}: — (季报未披露/非报告期,非暴雷)")
        snap_str = "\n".join(snap_lines)
    else:
        snap_str = "暂无基本面快照(非财报披露窗口属于正常现象,不代表暴雷)"

    # 权重调整理由
    reasons = sc.get("adjustment_reasons", [])
    reasons_str = "\n".join(f"  - {r}" for r in reasons[:5]) if reasons else "  无(使用该原型默认权重)"

    wp = sc.get("win_probability")
    wp_str = f"{wp*100:.0f}%" if wp is not None else "未校准"
    wp_note = ""
    if wp is not None:
        if wp >= 0.45: wp_note = " (高置信度)"
        elif wp >= 0.35: wp_note = " (中等)"
        else: wp_note = " (偏低,需谨慎)"

    dr = sc.get("downside_risk")
    dr_str = f"{dr:.0f}" if dr is not None else "?"
    dr_note = ""
    if dr is not None:
        if dr < -5: dr_note = " ⚠ 高风险"
        elif dr < -2: dr_note = " 偏高"

    dims = sc.get("dimension_scores", {})
    dim_lines = []
    dim_labels = {
        "tech_score": "技术面", "kline_score": "K线博弈", "fund_score": "资金面",
        "tg_momentum_score": "TG动量", "vol_ratio_score": "量比", "arbr_score": "ARBR情绪",
        "sector_alpha_score": "行业Alpha", "market_relative_score": "大盘相对强度",
        "valuation_score": "估值", "ma_trend_score": "均线趋势", "pattern_score": "形态",
        "trend_deviation_score": "趋势偏离", "bbi_score": "BBI多空", "box_score": "箱体结构",
    }
    for key, label in dim_labels.items():
        val = dims.get(key)
        if val is not None:
            emoji = "+" if val > 3 else ("-" if val < -3 else "~")
            dim_lines.append(f"  {emoji} {label}: {val:+.1f}")

    dim_str = "\n".join(dim_lines[:10]) if dim_lines else "暂无维度分解"

    return f"""{macro_context}请对A股 {symbol}({name})进行深度投资分析。系统已从14个维度完成量化评分。

【★ 实际价格与均线】
{price_str}

{_build_chip_section(chip)}

【核心预测指标】
  T+2胜率预估: {wp_str}{wp_note}(系统预测T+2日上涨的概率)
  综合评分: {sc.get('composite_score', '?')}/100
  下跌风险分: {dr_str}{dr_note}(负值=高风险,正值=低风险)
  大盘相对强度: {dims.get('market_relative_score', '?')}(正值=跑赢上证,负值=跑输)
  行业Alpha: {dims.get('sector_alpha_score', '?')}(正值=跑赢同行,负值=跑输)

【策略原型】
  {arch_label}
  该原型决定评分权重分配: {reasons_str}

【TG技术信号】
  级别: {sc.get('level', '?')} | 动量: {sc.get('tg_momentum', '?')}
  距低点: {sc.get('dist_low', '?')}% | J值: {sc.get('j_value', '?')} | 量比: {sc.get('vol_ratio', '?')}
  买入强度: {sc.get('buy_strength', '?')}

【14维评分分解】(+加分/-减分/~中性)
{dim_str}

【基本面数据】(最近一期财报, —=非报告期正常空值)
{snap_str}

分析要求 (你是量化基金经理，以盈亏视角冷静判断，拒绝讨好):
1. 技术面: 基于实际价格/均线/支撑压力位,给出具体支撑和压力价格(精确到分)。下跌信号必须标注风险
2. 筹码面: 基于筹码分布数据,分析主力成本区和获利盘比例。套牢盘>60%必须标注为重大减分项
3. 资金面: 主力动向、量价配合。主力净流出且量价背离时,必须打≤3分
4. 基本面: 财务健康度、成长性、估值。标注为"—"的指标属于季报未披露,请勿判为暴雷
5. 风险: 下跌风险、行业相对弱势等需警惕的信号。必须给出**具体**风险点,不得用"需关注"等模糊表达
6. 操作建议: 短期(1-4周)和中期(1-3月)两维度。**必须是盈亏视角的操作建议**(买入/持有/卖出/观望+具体价位+理由),不得写"建议关注/适当参与"
7. ★ 综合宏观环境【见上方】和个股技术数据，利润导向判断该股在当前市场背景下的机会与风险
8. ★ 默认不打高分——A股长期胜率不足40%，只有明确的多重信号共振才给≥7分。大部分股票应在3-6分之间

请在最后用JSON格式输出信号摘要:
{{"stock_code":"{symbol}","positive_signals":[{{"type":"opportunity/financial/technical","description":"描述","confidence":0.0-1.0}}],"negative_signals":[{{"type":"valuation/financial_risk/fund_flow/technical_risk/sentiment_risk","description":"描述","confidence":0.0-1.0}}],"suggested_score":0-100,"t2_target":"目标价","stop_loss":"止损价"}}

[SA:{symbol}]"""


def _build_chip_section(chip: dict) -> str:
    """格式化筹码吸收率数据为提示词段落."""
    if not chip or not chip.get("zones") or not chip.get("absorption"):
        return ""
    zones = chip["zones"]
    ab = chip["absorption"]
    if "error" in ab:
        return ""

    zl = zones["Z_LOCK"]
    zo = zones["Z_OVER"]
    zb = zones["Z_BELOW"]

    lines = []
    lines.append("【★ 筹码吸收率分析】")
    lines.append(f"  三区间划分:")
    lines.append(f"    锁死区间(当前横盘): ¥{zl['low']:.2f} - ¥{zl['high']:.2f}")
    lines.append(f"    上方套牢区:         ¥{zo['low']:.2f} - ¥{zo['high']:.2f}")
    lines.append(f"    下方支撑区:         ¥{zb['low']:.2f} - ¥{zb['high']:.2f}")
    lines.append(f"  筹码集中度: "
                 f"锁死区{ab.get('chips_lock_pct', ab.get('vol_lock_pct', 0)):.0f}% | "
                 f"套牢区{ab.get('chips_over_pct', ab.get('vol_over_pct', 0)):.0f}% | "
                 f"支撑区{ab.get('chips_below_pct', ab.get('vol_below_pct', 0)):.0f}%")
    lines.append(f"  集中度比率: {ab['ar_ratio']*100:.0f}% "
                 f"(锁死区筹码 / (锁死区+套牢区)筹码)")

    trend = ab.get('trend', '?')
    lines.append(f"  趋势: {trend} ({ab.get('verdict', '?')})")

    # 分时段 (cyq 趋势 — 新段格式含 winner_rate/cost_50pct)
    segs = ab.get('segments', [])
    if len(segs) >= 2:
        # 旧 ar_ratio 段 → 新 cyq winner_rate 段
        if 'ar_ratio' in segs[-1]:
            ar_timeline = " → ".join(
                f"{s['ar_ratio']*100:.0f}%" for s in segs[-5:]
            )
            lines.append(f"  分段吸收趋势: {ar_timeline}")
        elif 'winner_rate' in segs[-1]:
            wr_timeline = " → ".join(
                f"{s['winner_rate']:.0f}%" for s in segs[-5:]
            )
            lines.append(f"  获利盘趋势: {wr_timeline}")

    lines.append(f"  {chip.get('summary', '')}")

    return "\n".join(lines) + "\n"


async def _build_rich_macro_context() -> str:
    """Build comprehensive macro snapshot for LLM prompt.

    Groups indicators from macro_cache into logical sections:
    monetary · inflation · PMI · GDP · rates/bonds · credit · forex · commodities · hot concepts.
    All data-driven — no LLM fabrication.
    """
    try:
        from app.services.macro_data import get_macro_snapshot
        from app.core.database import async_session_factory
        from sqlalchemy import text
        snap = await get_macro_snapshot()

        def _v(name: str, default: str = "?") -> str:
            entry = snap.get(name, {})
            val = entry.get("value")
            if val is None or val == 0:
                return default
            unit = entry.get("unit", "")
            direction = entry.get("direction", "")
            d = "↑" if direction == "bullish" else ("↓" if direction == "bearish" else "")
            return f"{val}{unit}{d}"

        sections = []

        # ── 货币 ──
        sections.append("货币: "
            f"M2={_v('m2_yoy')} M1={_v('m1_yoy')} 剪刀差={_v('m1_m2_scissor')}")

        # ── 通胀 ──
        sections.append("通胀: "
            f"CPI={_v('cpi_yoy')} 核心CPI={_v('cpi_core')} PPI={_v('ppi_yoy')} 产端PPI={_v('ppi_producer')}")

        # ── PMI ──
        sections.append("景气: "
            f"PMI={_v('pmi')} 新订单={_v('pmi_new_order')} 出口订单={_v('pmi_export_order')} "
            f"生产={_v('pmi_production')} 就业={_v('pmi_employment')}")

        # ── GDP ──
        sections.append("GDP: "
            f"GDP={_v('gdp_yoy')} 一产={_v('gdp_pi_yoy')} 二产={_v('gdp_si_yoy')} 三产={_v('gdp_ti_yoy')}")

        # ── 利率/债券 ──
        sections.append("利率: S O/N=" + _v('shibor_on') + " 1W=" + _v('shibor_1w') +
            " 3M=" + _v('shibor_3m') + " 1Y=" + _v('shibor_1y') +
            " 利差=" + _v('shibor_spread', '0bp') +
            " | LPR 1Y=" + _v('lpr_1y') + " 5Y=" + _v('lpr_5y') +
            " | 国债 3M=" + _v('bond_3m_yield') + " 10Y=" + _v('bond_10y_yield'))

        # ── 信贷/杠杆 (格式化为易读单位) ──
        mb = snap.get("margin_balance", {}).get("value", 0) or 0
        mb_str = f"{mb/1e8:.0f}亿" if mb > 1e7 else "?"
        sb = snap.get("short_balance", {}).get("value", 0) or 0
        sb_str = f"{sb/1e8:.0f}亿" if sb > 1e7 else "?"
        nh = snap.get("north_hold_vol", {}).get("value", 0) or 0
        nh_str = f"{nh/1e8:.0f}亿股" if nh > 1e7 else "?"
        sections.append(f"杠杆: 融资={mb_str} 融券={sb_str} 北向={nh_str}")

        # ── 汇率 ──
        sections.append("汇率: " + f"USDCNY={_v('cny_usd')}")

        # ── 商品期货 (从 macro_cache 查, 不在 INDICATORS 里) ──
        comm_map = {
            "commodity:crude_oil": "原油", "commodity:copper": "沪铜",
            "commodity:aluminum": "沪铝", "commodity:rebar": "螺纹钢",
            "commodity:iron_ore": "铁矿石", "commodity:coke_coal": "焦煤",
            "commodity:gold": "沪金", "commodity:natural_rubber": "橡胶",
            "commodity:methanol": "甲醇", "commodity:pvc": "PVC",
        }
        try:
            async with async_session_factory() as s:
                r = await s.execute(text("""
                    SELECT indicator, value FROM macro_cache
                    WHERE indicator IN ('commodity:crude_oil','commodity:copper','commodity:aluminum',
                        'commodity:rebar','commodity:iron_ore','commodity:coke_coal','commodity:gold',
                        'commodity:natural_rubber','commodity:methanol','commodity:pvc')
                    AND (indicator, period) IN (SELECT indicator, MAX(period) FROM macro_cache GROUP BY indicator)
                """))
                comm_vals = {row[0]: float(row[1]) for row in r.fetchall() if row[1] is not None}
            if comm_vals:
                comm_lines = []
                for key, label in comm_map.items():
                    val = comm_vals.get(key)
                    if val:
                        comm_lines.append(f"{label}={val:.1f}")
                if comm_lines:
                    sections.append("商品: " + " | ".join(comm_lines))
        except Exception:
            pass

        # ── 热门概念 (最近5日涨跌幅) ──
        try:
            async with async_session_factory() as s:
                r = await s.execute(text("""
                    SELECT indicator, value FROM macro_cache
                    WHERE (indicator LIKE 'concept:AI%' OR indicator LIKE 'concept:%%白酒%%'
                        OR indicator LIKE 'concept:%%军工%%' OR indicator LIKE 'concept:%%医药%%'
                        OR indicator LIKE 'concept:%%新能源%%')
                    AND (indicator, period) IN (SELECT indicator, MAX(period) FROM macro_cache GROUP BY indicator)
                """))
                conc_vals = {row[0]: float(row[1]) for row in r.fetchall() if row[1] is not None}
            if conc_vals:
                conc_lines = []
                for prefix, label in [("concept:AI","AI"),("concept:白酒","白酒"),
                                       ("concept:军工","军工"),("concept:医药","医药"),
                                       ("concept:新能源","新能源")]:
                    match = next((v for k, v in conc_vals.items() if k.startswith(prefix)), None)
                    if match is not None:
                        conc_lines.append(f"{label}{match:+.1f}%")
                if conc_lines:
                    sections.append("概念5日: " + " · ".join(conc_lines))
        except Exception:
            pass

        # ── 综合判读 ──
        from app.services.macro_data import score_macro_impact
        adj, _ = await score_macro_impact()
        verdict = "偏多(利好股市)" if adj > 0.8 else ("偏空(打压股市)" if adj < -0.8 else "中性")
        sections.append(f"综合判读: score={adj:.1f} {verdict}")

        return "\n\n[宏观环境 — 数据驱动, 无需猜测]\n" + "\n".join(sections) + "\n[/宏观环境]\n"

    except Exception as e:
        logger.warning(f"Rich macro context failed: {e}")
        return ""


async def generate_prompts(symbols: list[str]) -> list[dict]:
    """为一组股票生成分析提示词(批量查询，避免逐股阻塞)."""
    if not symbols:
        return []

    # ★ v4.7: 富宏观上下文 — 商品/汇率/利率/景气 全覆盖
    macro_context = await _build_rich_macro_context()

    # 批量加载所有上下文(快照+评分+★价格)
    contexts = await _batch_get_stock_contexts(symbols)
    names = await _batch_get_stock_names(symbols)

    # ★ 批量加载价格/支撑压力 (并发)
    try:
        from app.services.ma_scorer import calc_support_resistance
        import asyncio as _aio
        price_tasks = [calc_support_resistance(sym) for sym in symbols]
        price_results = await _aio.gather(*price_tasks, return_exceptions=True)
        for i, sym in enumerate(symbols):
            sr = price_results[i]
            if sr and not isinstance(sr, Exception):
                contexts.setdefault(sym, {})["price"] = sr
    except Exception:
        pass

    # ★ 批量筹码分析 (并发, LLM 分析的自然输入)
    try:
        from app.services.chip_analyzer import analyze_chip_absorption
        import asyncio as _aio
        chip_tasks = [analyze_chip_absorption(sym) for sym in symbols]
        chip_results = await _aio.gather(*chip_tasks, return_exceptions=True)
        for i, sym in enumerate(symbols):
            cr = chip_results[i]
            if cr and not isinstance(cr, Exception):
                contexts.setdefault(sym, {})["chip"] = cr
    except Exception:
        pass

    results = []
    for sym in symbols:
        ctx = contexts.get(sym, {"snapshot": {}, "scoring": {}})
        name = names.get(sym, sym)
        prompt = build_analysis_prompt(sym, name, ctx, macro_context)
        results.append({
            "symbol": sym, "name": name, "prompt": prompt,
            "context": {
                "composite_score": ctx.get("scoring", {}).get("composite_score"),
                "archetype": ctx.get("scoring", {}).get("archetype"),
                "level": ctx.get("scoring", {}).get("level"),
                "tg_momentum": ctx.get("scoring", {}).get("tg_momentum"),
                "win_probability": ctx.get("scoring", {}).get("win_probability"),
                "downside_risk": ctx.get("scoring", {}).get("downside_risk"),
            },
        })
    return results


async def _batch_get_stock_contexts(symbols: list[str]) -> dict[str, dict]:
    """批量加载股票上下文(快照+评分)."""
    if not symbols:
        return {}
    async with async_session_factory() as s:
        # 批量快照
        r = await s.execute(text(
            "SELECT symbol, roe, revenue_yoy, profit_yoy, debt_to_assets, current_ratio, ocflow_net, pb, pe_ttm "
            "FROM stock_fundamental_snapshot WHERE symbol = ANY(:syms)"
        ), {"syms": symbols})
        snap_cols = ["roe", "revenue_yoy", "profit_yoy", "debt_to_assets", "current_ratio", "ocflow_net", "pb", "pe_ttm"]
        snapshots = {}
        for row in r.fetchall():
            snapshots[row[0]] = {c: (round(float(row[i+1]), 2) if row[i+1] is not None else None) for i, c in enumerate(snap_cols)}

        # 批量评分 (Phase E: 增加 win_probability, downside_risk, dimension_scores)
        r = await s.execute(text("""
            SELECT a.symbol, a.composite_score, a.tech_score, a.kline_score, a.fund_score,
                   a.fundamental_adjustment, a.archetype, a.adjustment_reasons,
                   a.win_probability, a.downside_risk, a.dimension_scores,
                   s.tg_momentum, s.level, s.trigger_path, s.dist_low, s.j_value,
                   s.vol_ratio, s.buy_strength
            FROM analysis_scores a
            LEFT JOIN scan_results s ON s.symbol=a.symbol AND s.scan_date=a.scan_date
            WHERE a.symbol = ANY(:syms) AND a.scan_date=(SELECT MAX(scan_date) FROM analysis_scores)
        """), {"syms": symbols})
        scorings = {}
        for row in r.fetchall():
            scorings[row[0]] = {
                "composite_score": float(row[1]) if row[1] else 0,
                "tech_score": float(row[2]) if row[2] else 0, "kline_score": float(row[3]) if row[3] else 0,
                "fund_score": float(row[4]) if row[4] else 0, "fundamental_adjustment": float(row[5]) if row[5] else 0,
                "archetype": row[6] or "unknown", "adjustment_reasons": row[7] if row[7] else [],
                "win_probability": float(row[8]) if row[8] is not None else None,
                "downside_risk": float(row[9]) if row[9] is not None else None,
                "dimension_scores": row[10] if row[10] else {},
                "tg_momentum": float(row[11]) if row[11] else 0, "level": row[12] or "",
                "trigger_path": row[13] or "", "dist_low": float(row[14]) if row[14] else 0,
                "j_value": float(row[15]) if row[15] else 0, "vol_ratio": float(row[16]) if row[16] else 0,
                "buy_strength": float(row[17]) if row[17] else 0,
            }

    return {sym: {"snapshot": snapshots.get(sym, {}), "scoring": scorings.get(sym, {})} for sym in symbols}


async def _batch_get_stock_names(symbols: list[str]) -> dict[str, str]:
    """批量加载股票名称."""
    if not symbols:
        return {}
    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT DISTINCT ON (symbol) symbol, name FROM scan_results WHERE symbol = ANY(:syms) ORDER BY symbol, scan_date DESC"
        ), {"syms": symbols})
        return {row[0]: row[1] for row in r.fetchall()}


async def get_candidates_for_llm(limit: int = 15) -> list[dict]:
    """获取适合 LLM 分析的候选股列表."""
    async with async_session_factory() as s:
        r = await s.execute(text("""
            SELECT a.symbol, s.name, a.composite_score, a.archetype, s.level,
                   a.tech_score, a.kline_score, a.fund_score
            FROM analysis_scores a
            LEFT JOIN scan_results s ON s.symbol=a.symbol AND s.scan_date=a.scan_date
            WHERE a.scan_date=(SELECT MAX(scan_date) FROM analysis_scores)
            ORDER BY a.composite_score DESC
            LIMIT :lim
        """), {"lim": limit})
        return [{
            "symbol": row[0], "name": row[1], "composite_score": float(row[2] or 0),
            "archetype": row[3] or "unknown", "level": row[4] or "",
            "tech_score": float(row[5] or 0), "kline_score": float(row[6] or 0),
            "fund_score": float(row[7] or 0),
        } for row in r.fetchall()]


# ── 以下为反馈解析(保留，供浏览器扩展使用)──────

def parse_signals(text: str) -> list[dict]:
    """从 DeepSeek 回复中提取结构化信号."""
    _fix_keys = re.compile(r'(?<=[\{\[,\n\r])\s*(\w+)\s*:')
    _fix_sq = re.compile(r"'(?P<val>[^']*)'")
    patterns = [r'\{.*"negative_signals".*"positive_signals".*\}', r'```json\s*(\{.*\})\s*```', r'```\s*(\{.*\})\s*```']
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            js = m.group(1) if m.lastindex else m.group(0)
            try:
                data = json.loads(js)
            except Exception:
                try:
                    data = json.loads(_fix_keys.sub(r'"\1":', js))
                except Exception:
                    try:
                        data = json.loads(_fix_sq.sub(r'"\g<val>"', _fix_keys.sub(r'"\1":', js)))
                    except Exception:
                        continue
            signals = []
            for s in data.get("negative_signals", []) + data.get("positive_signals", []):
                if isinstance(s, dict) and s.get("confidence", 0) >= 0.6:
                    direction = "negative" if s in data.get("negative_signals", []) else "positive"
                    signals.append({"direction": direction, **s})
            return signals
    return []


def adjust_score(original: float, signals: list[dict]) -> float:
    """根据 LLM 信号调整评分."""
    score = float(original)
    for sig in signals:
        adj = SIGNAL_ADJUSTMENTS.get(sig.get("type", "other"), SIGNAL_ADJUSTMENTS["other"])
        score = score * adj["weight_factor"] + adj["score_modifier"]
    return round(max(0, min(100, score)), 1)


# ── 共享函数：自动分析流程复用 ──────

async def process_and_store_deepseek_response(
    ts_code: str, trade_date, raw_response: str, user_id: str = "auto-analyze"
) -> dict:
    """解析 DeepSeek 回复 → 存储 stock_deep_feedback + experience_replay.

    同时被 feedback.py:_parse_later 和 llm_analysis:auto_analyze 使用.
    """
    parsed = None
    # 提取 JSON 块
    json_match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', raw_response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
        except Exception:
            pass
    if not parsed and raw_response.strip().startswith('{'):
        try:
            parsed = json.loads(raw_response.strip())
        except Exception:
            pass

    if not parsed or not ('positive_signals' in parsed or 'negative_signals' in parsed):
        return {"status": "no_json", "positive": 0, "negative": 0}

    pos_signals = parsed.get('positive_signals', [])
    neg_signals = parsed.get('negative_signals', [])
    hidden_risks = [s.get('description', '') for s in neg_signals]
    catalysts = [s.get('description', '') for s in pos_signals]

    TYPE_DIM_MAP = {
        'technical_risk': ['tech', 'kline', 'ma_trend'],
        'fund_flow': ['fund', 'vol_ratio'],
        'financial': ['valuation', 'fundamental'],
        'financial_risk': ['valuation', 'fundamental'],
        'opportunity': ['sector_alpha', 'arbr'],
        'valuation': ['valuation'],
        'sentiment_risk': ['sentiment'],
        'other': [],
    }

    async with async_session_factory() as s:
        await s.execute(text("""
            INSERT INTO stock_deep_feedback (ts_code, trade_date, user_id, source_type, raw_response,
                suggested_score, hidden_risks, catalysts, generated_at)
            VALUES (:ts, :td, :uid, 'auto_analyze', :raw, :ss, CAST(:hr AS jsonb), CAST(:ct AS jsonb), NOW())
            ON CONFLICT (ts_code, trade_date, user_id) DO UPDATE SET
                raw_response=EXCLUDED.raw_response, suggested_score=EXCLUDED.suggested_score,
                hidden_risks=EXCLUDED.hidden_risks, catalysts=EXCLUDED.catalysts, generated_at=NOW()
        """), {
            "ts": ts_code, "td": trade_date, "uid": user_id, "raw": raw_response[:50000],
            "ss": None, "hr": json.dumps(hidden_risks), "ct": json.dumps(catalysts),
        })

        for sig in neg_signals:
            dims = TYPE_DIM_MAP.get(sig.get('type', ''), [])
            conf = float(sig.get('confidence', 0.5))
            await s.execute(text("""
                INSERT INTO experience_replay (event_type, recorded_at, reward, meta_info, archetype, category_tags)
                VALUES ('deepseek_feedback', CURRENT_DATE, :rew, CAST(:mi AS jsonb), '__global__', CAST(:tags AS jsonb))
            """), {
                "rew": round(-conf, 3),
                "mi": json.dumps({"symbol": ts_code, "signal_type": sig.get('type'), "description": sig.get('description', '')[:500]}),
                "tags": json.dumps(dims),
            })
        for sig in pos_signals:
            dims = TYPE_DIM_MAP.get(sig.get('type', ''), [])
            conf = float(sig.get('confidence', 0.5))
            await s.execute(text("""
                INSERT INTO experience_replay (event_type, recorded_at, reward, meta_info, archetype, category_tags)
                VALUES ('deepseek_feedback', CURRENT_DATE, :rew, CAST(:mi AS jsonb), '__global__', CAST(:tags AS jsonb))
            """), {
                "rew": round(conf, 3),
                "mi": json.dumps({"symbol": ts_code, "signal_type": sig.get('type'), "description": sig.get('description', '')[:500]}),
                "tags": json.dumps(dims),
            })
        await s.commit()

    logger.info(f"DeepSeek auto-analyze stored for {ts_code}: {len(pos_signals)}pos + {len(neg_signals)}neg signals")
    return {
        "status": "success",
        "positive": len(pos_signals),
        "negative": len(neg_signals),
        "positive_signals": pos_signals,
        "negative_signals": neg_signals,
    }

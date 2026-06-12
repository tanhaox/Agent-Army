"""Daily background tasks — extracted from background_sync.py (Phase 7).

Each function is a standalone task, independently callable.
Originally part of the monolithic daily_task() orchestrator.
"""
import asyncio
import logging
from datetime import date, datetime, timedelta
from sqlalchemy import text
from app.core.database import async_session_factory

logger = logging.getLogger("scheduler.daily")


async def task_refresh_fundamental():
    """Step 1: Refresh fundamental snapshots for stocks scanned in last 30 days."""
    from sqlalchemy import text as sql_text

    async with async_session_factory() as s:
        cutoff = date.today() - timedelta(days=30)
        r = await s.execute(sql_text(
            """SELECT DISTINCT symbol FROM scan_results WHERE scan_date>=:c
               UNION SELECT DISTINCT symbol FROM ambush_signals WHERE scan_date>=:c"""
        ), {"c": cutoff})
        symbols = [row[0] for row in r.fetchall()]

    if not symbols:
        return {"status": "empty", "count": 0}

    r = await s.execute(sql_text(
        """SELECT DISTINCT ON (ts_code) ts_code, roe, or_yoy, profit_dedt, debt_to_assets, current_ratio, end_date
           FROM fina_indicator WHERE ts_code = ANY(:syms)
           ORDER BY ts_code, end_date DESC"""
    ), {"syms": symbols})
    fina_map = {row[0]: {"roe": float(row[1]) if row[1] else None,
                         "or_yoy": float(row[2]) if row[2] else None,
                         "profit_dedt": float(row[3]) if row[3] else None,
                         "debt": float(row[4]) if row[4] else None,
                         "cr": float(row[5]) if row[5] else None,
                         "end_date": row[6]}
                for row in r.fetchall()}

    r = await s.execute(sql_text(
        """SELECT DISTINCT ON (ts_code) ts_code, trade_date, pb, pe_ttm
           FROM daily_basic WHERE ts_code = ANY(:syms)
           ORDER BY ts_code, trade_date DESC"""
    ), {"syms": symbols})
    db_map = {row[0]: {"trade_date": row[1], "pb": float(row[2]) if row[2] else None,
                       "pe_ttm": float(row[3]) if row[3] else None}
              for row in r.fetchall()}

    r = await s.execute(sql_text(
        """SELECT ts_code, profit_dedt FROM fina_indicator
           WHERE ts_code = ANY(:syms) AND EXTRACT(YEAR FROM end_date)=EXTRACT(YEAR FROM CURRENT_DATE)-1
           AND EXTRACT(MONTH FROM end_date)=12"""
    ), {"syms": symbols})
    prev_profit_map = {row[0]: float(row[1]) if row[1] else None for row in r.fetchall()}

    try:
        r = await s.execute(sql_text(
            """SELECT DISTINCT ON (ts_code) ts_code, n_cashflow_act
               FROM cashflow WHERE ts_code = ANY(:syms)
               ORDER BY ts_code, end_date DESC"""
        ), {"syms": symbols})
        ocf_map = {row[0]: float(row[1]) if row[1] else None for row in r.fetchall()}
    except Exception:
        ocf_map = {}

    inserted = 0
    async with async_session_factory() as s2:
        for sym in symbols:
            fi = fina_map.get(sym); db = db_map.get(sym)
            if not fi and not db: continue
            td = db["trade_date"] if db else date.today()
            roe = fi["roe"] if fi else None
            revenue_yoy = fi["or_yoy"] if fi else None
            debt = fi["debt"] if fi else None
            cr = fi["cr"] if fi else None
            pb = db["pb"] if db else None
            pe_ttm = db["pe_ttm"] if db else None
            profit_yoy = None
            profit_cur = fi["profit_dedt"] if fi else None
            if profit_cur is not None:
                prev = prev_profit_map.get(sym)
                if prev and prev != 0:
                    profit_yoy = round((profit_cur - prev) / abs(prev) * 100, 2)
            ocflow_net = ocf_map.get(sym)
            await s2.execute(sql_text(
                """INSERT INTO stock_fundamental_snapshot
                   (symbol, trade_date, roe, revenue_yoy, profit_yoy, debt_to_assets, current_ratio, ocflow_net, pb, pe_ttm, updated_at)
                   VALUES (:s, :td, :roe, :ry, :py, :da, :cr, :ocf, :pb, :pe, NOW())
                   ON CONFLICT(symbol) DO UPDATE SET
                   trade_date=EXCLUDED.trade_date, roe=EXCLUDED.roe, revenue_yoy=EXCLUDED.revenue_yoy,
                   profit_yoy=EXCLUDED.profit_yoy, debt_to_assets=EXCLUDED.debt_to_assets,
                   current_ratio=EXCLUDED.current_ratio, ocflow_net=EXCLUDED.ocflow_net,
                   pb=EXCLUDED.pb, pe_ttm=EXCLUDED.pe_ttm, updated_at=NOW()"""
            ), {"s": sym, "td": td, "roe": roe, "ry": revenue_yoy, "py": profit_yoy,
                "da": debt, "cr": cr, "ocf": ocflow_net, "pb": pb, "pe": pe_ttm})
            inserted += 1
        await s2.commit()
    return {"status": "success", "inserted": inserted}


async def task_sync_toplist():
    """Step 2: Sync toplist (dragon-tiger board) data for last 5 days."""
    from app.services.sector_heat_engine import sync_recent_days
    result = await sync_recent_days(days=5)
    new_syncs = sum(1 for r in result if r.get("status") == "success")
    logger.info(f"Toplist: {len(result)}d checked, {new_syncs}d new")
    return result


async def task_sync_commodity_futures():
    """Step 3: Sync commodity futures data."""
    from app.services.tushare_common import call_tushare
    from datetime import date as dt_date, timedelta
    today = dt_date.today()
    start = (today - timedelta(days=7)).strftime('%Y%m%d')
    end = today.strftime('%Y%m%d')
    codes = 'CU2605.SHF,AL2605.SHF,ZN2605.SHF,RB2610.SHF,HC2610.SHF,FU2609.SHF,RU2609.SHF,AU2606.SHF,AG2606.SHF'
    rows = await call_tushare('fut_daily', {'ts_code': codes, 'start_date': start, 'end_date': end},
                               'ts_code,trade_date,open,high,low,close,vol')
    if not rows: return {"status": "empty"}
    inserted = 0
    async with async_session_factory() as s:
        for r in rows:
            td_str = r['trade_date']
            td = dt_date(int(td_str[:4]), int(td_str[4:6]), int(td_str[6:8]))
            await s.execute(text("""INSERT INTO commodity_futures (ts_code,trade_date,open,high,low,close,volume)
                VALUES (:ts,:td,:o,:h,:l,:c,:v) ON CONFLICT (ts_code,trade_date) DO UPDATE SET
                open=EXCLUDED.open,high=EXCLUDED.high,low=EXCLUDED.low,close=EXCLUDED.close,volume=EXCLUDED.volume"""),
                {'ts': r['ts_code'], 'td': td, 'o': float(r.get('open',0) or 0),
                 'h': float(r.get('high',0) or 0), 'l': float(r.get('low',0) or 0),
                 'c': float(r.get('close',0) or 0), 'v': float(r.get('vol',0) or 0)})
            inserted += 1
        await s.commit()
    logger.info(f"Futures: {inserted} records")
    return {"status": "success", "inserted": inserted}


async def task_sync_margin_trading():
    """Step 3b: Sync margin trading data."""
    from app.services.tushare_common import call_tushare
    from datetime import date as dt_date, timedelta
    today = dt_date.today()
    start = (today - timedelta(days=7)).strftime('%Y%m%d')
    end = today.strftime('%Y%m%d')
    rows = await call_tushare('margin', {'start_date': start, 'end_date': end},
                               'trade_date,rzye,rzmre,rqye')
    if not rows: return {"status": "empty"}
    inserted = 0
    async with async_session_factory() as s:
        for r in rows:
            td_str = r['trade_date']
            td = dt_date(int(td_str[:4]), int(td_str[4:6]), int(td_str[6:8]))
            await s.execute(text("""INSERT INTO margin_trading (ts_code,trade_date,rzye,rzmre,rqye)
                VALUES ('000001.SH',:td,:rze,:rzm,:rqe) ON CONFLICT (ts_code,trade_date) DO UPDATE SET
                rzye=EXCLUDED.rzye,rzmre=EXCLUDED.rzmre,rqye=EXCLUDED.rqye"""),
                {'td': td, 'rze': float(r.get('rzye',0) or 0)/1e8,
                 'rzm': float(r.get('rzmre',0) or 0)/1e8,
                 'rqe': float(r.get('rqye',0) or 0)/1e8})
            inserted += 1
        await s.commit()
    logger.info(f"Margin: {inserted} records")
    return {"status": "success", "inserted": inserted}


async def task_daily_backtest():
    """Step 4: Rolling backtest + Bayesian update."""
    from app.services.learning_engine import run_rolling_backtest
    from app.services.bayesian_optimizer import ensure_beliefs_initialized
    await ensure_beliefs_initialized()
    result = await run_rolling_backtest(lookback_days=60)
    try:
        async with async_session_factory() as s:
            await s.execute(text(
                """INSERT INTO sync_log (task_name, status, detail, started_at, completed_at)
                   VALUES ('daily_backtest', :st, CAST(:dt AS jsonb), NOW(), NOW())"""
            ), {"st": result["status"], "dt": __import__("json").dumps({
                "days_tested": result.get("days_tested"),
                "avg_discrimination": result.get("avg_discrimination"),
                "avg_hit_rate": result.get("avg_hit_rate"),
            })})
            await s.commit()
    except Exception as e:
        logger.warning(f"sync_log: {e}")
    logger.info(f"Backtest: days={result.get('days_tested')}")
    return result


async def task_shadow_training():
    """Step 5: Shadow training + contextual bandit selection."""
    from app.services.shadow_trainer import train_shadow
    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT archetype FROM archetype_profiles WHERE is_trainable=true ORDER BY sample_count DESC"
        ))
        archs = [row[0] for row in r.fetchall()]
    for arch in archs:
        for st in ["S1", "S2", "S3"]:
            async def _run_safe(a=arch, s=st, iters=3):
                try: await train_shadow(a, s, n_iterations=iters)
                except Exception as e: logger.error(f"Shadow {a}/{s}: {e}", exc_info=True)
            asyncio.create_task(_run_safe())
    async def _bandit_select():
        try:
            await asyncio.sleep(30)
            from app.services.contextual_bandit import select_arm, get_arm_stats
            for arch in archs:
                best = select_arm({"archetype": arch})
                logger.info(f"Bandit: {arch} -> {best.get('arm','S2')}")
        except Exception as be:
            logger.debug(f"Bandit: {be}")
    asyncio.create_task(_bandit_select())
    logger.info(f"Shadow: {len(archs)} archs scheduled")
    return {"status": "scheduled", "archs": len(archs)}


async def task_self_learning():
    """P3: Self-learning incremental training + mark loss signals."""
    from app.services.self_learning_bootstrap import daily_incremental_train, mark_loss_signals
    train_r = await daily_incremental_train()
    mark_r = await mark_loss_signals(days_back=30)
    logger.info(f"Self-learning: train={train_r.get('trained',0)}, marked={mark_r}")
    return {"trained": train_r.get("trained", 0), "marked": mark_r}


async def task_increment_holding_days():
    """Step 5.5: Increment holding days."""
    async with async_session_factory() as s:
        r = await s.execute(text("UPDATE holdings SET holding_days = holding_days + 1, updated_at = NOW()"))
        n = r.rowcount
        await s.commit()
    if n > 0: logger.info(f"Holding days: +1 for {n} positions")
    return {"updated": n}


async def task_sync_min_kline():
    """Step 5.8: Sync minute kline for pool + holdings."""
    from scripts.sync_min_kline import sync_pool_min_kline
    await sync_pool_min_kline()
    return {"status": "done"}


async def task_sync_index_daily():
    """Step 5.9: Sync index daily via idx_mins API (5min bars → daily OHLCV)."""
    from scripts.sync_index_daily import main
    return await main()


async def task_sync_sw_sector():
    """Step 5.10: Incremental sync of sw_sector_index (latest trading day only)."""
    from datetime import date as dt_date, timedelta
    from app.services.tushare_common import call_tushare as _ts
    from sqlalchemy import text as _text

    today = dt_date.today().strftime('%Y%m%d')
    total = 0
    for code, name in [
        ("801010.SI","农林牧渔"),("801020.SI","采掘"),("801030.SI","化工"),
        ("801040.SI","钢铁"),("801050.SI","有色金属"),("801080.SI","电子"),
        ("801110.SI","家用电器"),("801120.SI","食品饮料"),("801130.SI","纺织服装"),
        ("801140.SI","轻工制造"),("801150.SI","医药生物"),("801160.SI","公用事业"),
        ("801170.SI","交通运输"),("801180.SI","房地产"),("801200.SI","商业贸易"),
        ("801210.SI","休闲服务"),("801230.SI","综合"),("801710.SI","建筑材料"),
        ("801720.SI","建筑装饰"),("801730.SI","电气设备"),("801740.SI","国防军工"),
        ("801750.SI","计算机"),("801760.SI","传媒"),("801770.SI","通信"),
        ("801780.SI","银行"),("801790.SI","非银金融"),("801880.SI","汽车"),
        ("801890.SI","机械设备"),
    ]:
        try:
            rows = await _ts('sw_daily', {'ts_code': code, 'start_date': today, 'end_date': today},
                             'ts_code,trade_date,open,high,low,close,vol,amount,pe,pb,pct_change')
            if not rows:
                continue
            async with async_session_factory() as s:
                for item in rows:
                    td_str = item.get("trade_date", "")
                    td = dt_date(int(td_str[:4]), int(td_str[4:6]), int(td_str[6:8])) if len(str(td_str)) == 8 else dt_date.today()
                    await s.execute(_text(
                        "INSERT INTO sw_sector_index (index_code,trade_date,open,high,low,close,vol,amount,pe,pb,pct_chg,name) "
                        "VALUES (:c,:d,:o,:h,:l,:cl,:v,:a,:pe,:pb,:pct,:nm) "
                        "ON CONFLICT (index_code,trade_date) DO UPDATE SET "
                        "open=EXCLUDED.open,high=EXCLUDED.high,low=EXCLUDED.low,close=EXCLUDED.close,"
                        "vol=EXCLUDED.vol,amount=EXCLUDED.amount,pe=EXCLUDED.pe,pb=EXCLUDED.pb,"
                        "pct_chg=EXCLUDED.pct_chg,name=EXCLUDED.name"
                    ), {"c":code,"d":td,"o":float(item.get("open",0)or 0),"h":float(item.get("high",0)or 0),
                        "l":float(item.get("low",0)or 0),"cl":float(item.get("close",0)or 0),
                        "v":float(item.get("vol",0)or 0),"a":float(item.get("amount",0)or 0),
                        "pe":float(item.get("pe",0)or 0),"pb":float(item.get("pb",0)or 0),
                        "pct":round(float(item.get("pct_change",0)or 0),2),"nm":name})
                    total += 1
                await s.commit()
        except Exception:
            pass
    if total > 0:
        logger.info(f"SW sector: +{total} rows")
    return {"inserted": total}


async def task_cleanup_old_data():
    """Step 6: Cleanup expired events (news preserved permanently per Phase 48)."""
    from app.services.event_detector import cleanup_expired_events
    # Phase 48: 新闻永久保留, 取消 48h 清理
    await cleanup_expired_events()
    return {"status": "done"}


async def task_build_news_signals():
    """Phase 48: 新闻规则匹配 → news_signals (商品×股票映射)."""
    from scripts.build_news_signals import build_news_signals
    result = await build_news_signals()
    logger.info(f"News signals: {result['matched']} matched, {result['inserted']} inserted")
    return result


async def task_verify_news_signals():
    """Phase 50: 回溯验证新闻信号方向命中率, 标记 is_active."""
    from scripts.verify_news_signals import verify_news_signals
    result = await verify_news_signals(lookback_days=30, min_age_days=5)
    logger.info(f"News verify: {result['upserted']} rows, {result['activated']} active")
    return result


async def task_system_health():
    """Step 6.5: System health check + anomaly detection."""
    from app.services.system_health import check_and_upgrade_components
    from app.services.anomaly_detector import check_signal_distribution
    health = await check_and_upgrade_components()
    anomaly = await check_signal_distribution()
    if health.get("activated"):
        logger.info(f"Health: activated={health['activated']}")
    if anomaly.get("status") == "anomaly":
        logger.warning(f"Anomaly: {anomaly.get('warnings', [])}")
    return {"health": health, "anomaly": anomaly}


async def task_holdings_sector_warning():
    """Holdings sector flow warning check."""
    import json as _json
    try:
        async with async_session_factory() as s:
            r = await s.execute(text("""
                SELECT DISTINCT h.symbol, COALESCE(tm.ths_name, 'unknown')
                FROM holdings h
                LEFT JOIN ths_member tm ON tm.ts_code = h.symbol AND tm.out_date IS NULL
                WHERE h.qty > 0
            """))
            holdings_sector = [(row[0], row[1]) for row in r.fetchall()]
        if not holdings_sector: return {"status": "no_holdings"}
        holding_sectors = set(s[1] for s in holdings_sector)
        async with async_session_factory() as s:
            r = await s.execute(text("""
                SELECT COALESCE(tm.ths_name, 'unknown'),
                       SUM(COALESCE(tl.l_buy, 0) - COALESCE(tl.l_sell, 0))
                FROM toplist_daily tl
                LEFT JOIN ths_member tm ON tm.ts_code = tl.ts_code AND tm.out_date IS NULL
                WHERE tl.trade_date = CURRENT_DATE AND tm.ths_name IS NOT NULL
                GROUP BY tm.ths_name
            """))
            sector_flow = {row[0]: float(row[1] or 0) for row in r.fetchall()}
        if not sector_flow: return {"status": "no_toplist"}
        for sector_name in holding_sectors:
            net_flow = 0.0
            for flow_sec, flow_val in sector_flow.items():
                if flow_sec and (flow_sec in sector_name or sector_name in flow_sec):
                    net_flow = flow_val; break
            if net_flow < -100_000_000:
                affected = [s[0] for s in holdings_sector if s[1] == sector_name]
                msg = f"Holdings sector [{sector_name}] outflow {abs(net_flow)/1e8:.1f}B, affecting {len(affected)}"
                logger.warning(msg)
                try:
                    async with async_session_factory() as s:
                        await s.execute(text("""INSERT INTO sync_log (task_name, status, detail, started_at, completed_at)
                            VALUES ('holdings_sector_warning', 'warning', CAST(:dt AS jsonb), NOW(), NOW())"""),
                            {"dt": _json.dumps({"sector": sector_name, "net_flow": net_flow,
                                                 "affected_stocks": affected, "message": msg})})
                        await s.commit()
                except Exception as e:
                    logger.debug(f"sync_log write skipped: {e}")
    except Exception as e:
        logger.debug(f"Sector warning: {e}")
    return {"status": "done"}


async def task_build_sector_trend():
    """Step 7: Build/update sector_trend (incremental, today only)."""
    from scripts.build_sector_trend import build_today
    await build_today()
    return {"status": "done"}


async def task_sync_sector_min_kline():
    """Step 7.5: Sync sector-level 5-min kline (incremental, today only)."""
    from scripts.sync_sector_min_kline import sync_today
    await sync_today()
    return {"status": "done"}


async def task_sync_chip_perf():
    """Step 8.5: Sync Tushare cyq_perf to daily_chip_perf table (daily, after kline)."""
    from scripts.sync_chip_perf import sync_day
    today_str = date.today().strftime("%Y%m%d")
    n = await sync_day(today_str)
    if n > 0:
        logger.info(f"Chip perf: +{n} rows")
    return {"inserted": n}


async def task_sync_limit_list():
    """Step 8.6: Sync Tushare limit_list (daily limit-up/limit-down/broken-board)."""
    from scripts.sync_limit_list import sync_day
    today_str = date.today().strftime("%Y%m%d")
    n = await sync_day(today_str)
    if n > 0:
        logger.info(f"Limit list: +{n} records")
    return {"inserted": n}


async def task_verify_recommendations():
    """Step 8: Backfill real T+2/T+5/T+15 returns from daily_kline for unverified recommendations."""
    from scripts.verify_recommendations import main
    await main(daily=True)
    return {"status": "done"}


async def task_sync_daily_kline():
    """Step 0.5: Download latest daily kline for all 5500+ stocks via Tushare."""
    from app.services.tg_engine import download_latest_kline
    n = await download_latest_kline()
    if n > 0:
        logger.info(f"Daily kline: +{n} rows")
    return {"inserted": n}


async def task_update_market_status():
    """Step 0.8: Record daily market state into market_status_log."""
    from app.services.market_gate import get_market_state
    from datetime import date as dt_date
    ms = await get_market_state()
    regime = ms.get("regime", "unknown")
    risk = ms.get("risk", "normal")
    async with async_session_factory() as s:
        await s.execute(text("""
            INSERT INTO market_status_log (trade_date, index_code, status, notes)
            VALUES (:d, '000001.SH', :st, :nt)
            ON CONFLICT (trade_date, index_code) DO UPDATE SET
                status=EXCLUDED.status, notes=EXCLUDED.notes
        """), {
            "d": dt_date.today(),
            "st": f"{regime}({risk})",
            "nt": f"regime={regime} risk={risk} breadth={ms.get('breadth',{}).get('advance_pct','?')}%",
        })
        await s.commit()
    logger.info(f"Market status: {regime}({risk})")
    return {"status": "done"}

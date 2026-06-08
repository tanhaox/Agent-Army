"""TG scan API.

扫描状态: 优先使用 Redis 共享 (支持多 worker), Redis 不可用时降级到进程内存.
"""
import json, asyncio, logging
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, async_session_factory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan", tags=["scan"])

# ── 内存降级状态 (Redis 不可用时使用) ──
_active_scan: asyncio.Task | None = None
_active_scan_state: dict = {"running": False, "phase": "", "current": 0, "total": 0, "pct": 0, "extra": "", "result": None}
_scan_lock = asyncio.Lock()


async def _set_scan_state(state: dict):
    """写入扫描状态 (Redis 优先, 内存降级)."""
    global _active_scan_state
    _active_scan_state = state  # 始终保持内存同步
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            await r.hset("scan:state", mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in state.items()})
            await r.expire("scan:state", 3600)
    except Exception:
        pass


async def _get_scan_state() -> dict:
    """读取扫描状态 (Redis 优先, 内存降级)."""
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            raw = await r.hgetall("scan:state")
            if raw:
                state = {}
                for k, v in raw.items():
                    try:
                        state[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        state[k] = v
                return state
    except Exception:
        pass
    return _active_scan_state


async def _is_scan_running() -> bool:
    """检查是否有扫描在运行 (Redis 优先)."""
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            lock = await r.get("scan:lock")
            if lock:
                return True
    except Exception:
        pass
    return bool(_active_scan and not _active_scan.done())


async def _acquire_scan_lock() -> bool:
    """获取扫描锁 (Redis SET NX EX 优先)."""
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            ok = await r.set("scan:lock", "1", nx=True, ex=3600)
            if ok:
                return True
            return False
    except Exception:
        pass
    # 内存降级
    if _active_scan and not _active_scan.done():
        return False
    return True


async def _release_scan_lock():
    """释放扫描锁."""
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            await r.delete("scan:lock")
    except Exception:
        pass

@router.get("/results")
async def get_scan_results(
    limit: int = Query(500),
    min_score: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        SELECT s.symbol, COALESCE(nc.name, s.name, s.symbol) as name, s.level,
               s.tg_momentum, s.dist_low, s.j_value,
               s.vol_ratio, s.buy_strength, s.close_price, s.composite_score,
               s.trigger_path, s.industry, COALESCE(s.market, '主板') as market,
               COALESCE(s.resonance_type,'daily_only') as resonance_type,
               COALESCE(s.weekly_tg_momentum,0) as weekly_tg_momentum
        FROM scan_results s
        LEFT JOIN stock_name_cache nc ON nc.symbol = s.symbol
        WHERE s.scan_date = (SELECT MAX(scan_date) FROM scan_results)
          AND s.composite_score >= :ms
        ORDER BY s.composite_score DESC LIMIT :lim
    """), {"ms": min_score, "lim": limit})
    data = [{"symbol": r[0], "name": r[1], "level": r[2], "tg_momentum": float(r[3] or 0),
             "dist_low": float(r[4] or 0), "j_value": float(r[5] or 0), "vol_ratio": float(r[6] or 0),
             "buy_strength": float(r[7] or 0), "close_price": float(r[8] or 0),
             "composite_score": float(r[9] or 0), "trigger_path": r[10], "industry": r[11], "market": r[12],
             "resonance_type": r[13], "weekly_tg_momentum": float(r[14] or 0)}
            for r in result.fetchall()]
    return {"status": "success", "data": data, "count": len(data)}

@router.get("/dates")
async def get_scan_dates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT DISTINCT scan_date FROM scan_results ORDER BY scan_date DESC LIMIT 10"))
    dates = [str(r[0]) for r in result.fetchall()]
    return {"status": "success", "dates": dates}

@router.get("/status")
async def get_scan_status():
    """查询当前扫描状态(客户端断线后可重新获取进度)."""
    state = await _get_scan_state()
    return {"status": "success", "data": state}


@router.post("/trigger")
async def trigger_scan(skip_download: bool = Query(default=False)):
    global _active_scan, _active_scan_state

    if not await _acquire_scan_lock():
        return {"status": "error", "detail": "扫描已在运行中"}

    await _set_scan_state({"running": True, "phase": "", "current": 0, "total": 0, "pct": 0, "extra": "", "result": None})

    async def sse_gen():
        queue = asyncio.Queue()

        async def progress_cb(phase, current, total, extra=None):
            pct = min(99, int(current / max(total, 1) * 100))
            await _set_scan_state({"running": True, "phase": phase, "current": current, "total": total, "pct": pct, "extra": str(extra) if extra else ""})
            try:
                await asyncio.wait_for(queue.put({"phase": phase, "current": current, "total": total, "pct": pct, "extra": extra}), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                pass  # 客户端未连接也继续扫描

        async def run_scan():
            import logging; _logger = logging.getLogger(__name__)
            try:
                # 智能龙虎榜同步(16:00前跳过，16:00后拉取，不重复)
                await progress_cb("toplist", 0, 1, extra="检查龙虎榜数据...")
                try:
                    from app.services.sector_heat_engine import ensure_toplist_fresh
                    tl_status = await ensure_toplist_fresh()
                    await progress_cb("toplist", 1, 1, extra=f"龙虎榜: {tl_status.get('reason', tl_status.get('status', ''))}")
                except Exception as e:
                    _logger.warning(f"龙虎榜检查失败: {e}")

                from app.services.tg_engine import scan_all_stocks
                async with async_session_factory() as s:
                    results, sd = await scan_all_stocks(s, progress_callback=progress_cb, skip_download=skip_download)
                l3_count = sum(1 for _, r in results.iterrows() if r.get("level") == "L3")
                l2_count = sum(1 for _, r in results.iterrows() if r.get("level") == "L2")

                # ── 并行扫描：潜伏猎手 ──────────────────
                await progress_cb("ambush_scan", 0, 1, extra="TG扫描完成，开始潜伏猎手...")
                try:
                    from app.services.ambush_scanner import run_ambush_scan
                    from datetime import date as dt_date
                    async with async_session_factory() as s:
                        r = await s.execute(text("SELECT MAX(scan_date) FROM analysis_scores"))
                        amb_scan_date = r.scalar() or dt_date.today()
                    amb = await run_ambush_scan(scan_date=amb_scan_date)
                    await progress_cb("ambush_scan", 1, 1,
                                      extra=f"潜伏猎手完成: {amb.get('signals', 0)} 个信号")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Ambush scan failed: {e}")

                # ── 并行扫描：形态识别 ──────────────────
                await progress_cb("pattern_scan", 0, 1, extra="开始形态识别...")
                try:
                    from app.services.pattern_engine import run_pattern_scan
                    pat_result = await run_pattern_scan()
                    await progress_cb("pattern_scan", 1, 1,
                                      extra=f"形态识别完成: {pat_result['total_patterns']} 个形态")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Pattern scan failed: {e}")
                    await progress_cb("pattern_scan", 1, 1, extra=f"形态识别异常: {e}")

                # ── 自动串联：12维深度评分 ────────────────
                await progress_cb("deep_score", 0, 1, extra="开始12维深度评分...")
                try:
                    from app.services.deep_scorer import deep_analyze
                    async def deep_cb(step, total, label):
                        await progress_cb("deep_score", step, total, extra=label)
                    async with async_session_factory() as s:
                        scored = await deep_analyze(s, scan_date=sd, progress_cb=deep_cb)
                    await progress_cb("deep_score", 1, 1,
                                      extra=f"12维评分完成: {len(scored)} 只通过基本面过滤")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Deep scoring failed: {e}", exc_info=True)
                    await progress_cb("deep_score", 1, 1, extra=f"11维评分异常: {e}")

                # ── 分钟线防伪防火墙 ★ ──────────────────
                await progress_cb("nm_defense", 0, 1, extra="分钟线防伪验证中...")
                try:
                    from app.services.signal_quality_scorer import run_nm_defense
                    nm_result = await run_nm_defense(str(sd))
                    await progress_cb("nm_defense", 1, 1,
                        extra=f"防伪: 验{nm_result['scanned']}只 "
                              f"拦截{nm_result['penalized']}只假信号 "
                              f"确认{nm_result['boosted']}只真信号 "
                              f"(N型{nm_result['n_type']}/M型{nm_result['m_type']})")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"NM defense failed: {e}", exc_info=True)

                # ── 龙虎榜同步 ──────────────────
                await progress_cb("toplist_sync", 0, 1, extra="同步龙虎榜数据...")
                try:
                    from app.services.sector_heat_engine import sync_recent_days
                    tl_result = await sync_recent_days(days=5)
                    new_syncs = sum(1 for r in tl_result if r.get("status") == "success")
                    await progress_cb("toplist_sync", 1, 1, extra=f"龙虎榜同步完成: {new_syncs}天新数据")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Toplist sync failed: {e}")
                    await progress_cb("toplist_sync", 1, 1, extra=f"龙虎榜同步异常: {e}")

                # ── 推荐准确率验证+闭环反馈 ──────────
                await progress_cb("accuracy_feedback", 0, 1, extra="验证历史推荐准确率...")
                try:
                    from app.services.accuracy_tracker import verify_all_periods, apply_accuracy_feedback
                    verify_result = await verify_all_periods()
                    fb_result = await apply_accuracy_feedback()
                    await progress_cb("accuracy_feedback", 1, 1,
                        extra=f"准确率验证完成 (反馈: {fb_result.get('action','?')})")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Accuracy feedback failed: {e}")
                    await progress_cb("accuracy_feedback", 1, 1, extra=f"准确率验证异常: {e}")

                result_data = {"phase": "done", "count": len(results), "scan_date": str(sd),
                               "l3_count": l3_count, "l2_count": l2_count,
                               "scored_count": len(results)}
                await _set_scan_state({"running": False, "phase": "done", "current": 0, "total": 0, "pct": 100, "extra": "", "result": result_data})
                await _release_scan_lock()
                await queue.put(result_data)
            except Exception as e:
                import logging
                logging.getLogger("scan").error(f"Scan failed: {e}", exc_info=True)
                await _set_scan_state({"running": False, "phase": "error", "current": 0, "total": 0, "pct": 0, "extra": str(e), "result": None})
                await _release_scan_lock()
                await queue.put({"phase": "error", "message": str(e)})

        _active_scan = asyncio.ensure_future(run_scan())

        while True:
            event = await asyncio.wait_for(queue.get(), timeout=600)
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("phase") in ("done", "error"):
                break

    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@router.post("/tail-market")
async def trigger_tail_market_scan():
    """触发隔天战法尾盘扫描 — SSE 流式返回进度和结果."""
    import asyncio as _asyncio

    async def sse_gen():
        queue = _asyncio.Queue()

        async def progress_cb(phase, current, total, extra=None):
            try:
                await _asyncio.wait_for(queue.put({
                    "phase": phase, "current": current, "total": total, "extra": extra or ""
                }), timeout=1.0)
            except (_asyncio.TimeoutError, _asyncio.QueueFull):
                pass

        async def run_scan():
            try:
                from app.services.tail_market_scanner import scan_tail_market
                results = await scan_tail_market(progress_cb=progress_cb)
                await queue.put({"phase": "done", "results": results, "count": len(results)})
            except Exception as e:
                logger = __import__("logging").getLogger("scan")
                logger.error(f"Tail market scan failed: {e}", exc_info=True)
                await queue.put({"phase": "error", "message": str(e)})

        _asyncio.ensure_future(run_scan())

        while True:
            event = await _asyncio.wait_for(queue.get(), timeout=300)
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("phase") in ("done", "error"):
                break

    return StreamingResponse(sse_gen(), media_type="text/event-stream")

@router.post("/sync-toplist")
async def sync_toplist(days: int = 5):
    """同步龙虎榜数据."""
    from app.services.sector_heat_engine import sync_recent_days
    results = await sync_recent_days(days=days)
    return {"status": "success", "data": results}

@router.get("/sector-heat")
async def get_sector_heat(days: int = 5, use_ai: bool = False):
    """板块热度分析."""
    from app.services.sector_heat_engine import get_full_sector_report, get_sector_heat
    if use_ai:
        result = await get_full_sector_report()
    else:
        result = {"local": await get_sector_heat(days=days), "deepseek": None}
    return {"status": "success", "data": result}


@router.get("/toplist-analysis")
async def get_toplist_analysis(date: str = "", market: str = ""):
    """龙虎榜分析: 个股合力 + 板块共振. market=主板/创业板/全部."""
    from datetime import date as _dt
    td = _dt.fromisoformat(date) if date else _dt.today()
    from app.services.toplist_analyzer import analyze_daily_all, analyze_sector_resonance
    stocks = await analyze_daily_all(td)
    sectors = await analyze_sector_resonance(td)
    # 按板块过滤
    if market and market != "全部":
        stocks = [s for s in stocks if s.get("market", "主板") == market]
    return {"status": "success", "data": {"stocks": stocks, "sectors": sectors.get("sectors", []),
            "total": len(stocks), "date": str(td)}}


# ── 历史回填 ─────────────────────────────────

@router.post("/backfill")
async def trigger_backfill(months: str = Query(default="")):
    """触发历史数据回填(后台异步).

    months: 逗号分隔的月份，如 202601,202602,202603。默认 202511~202605.
    """
    global _active_scan_state
    if _active_scan_state.get("running"):
        return {"status": "error", "detail": "扫描正在运行中，无法同时回填"}

    import asyncio as _asyncio
    month_list = [m.strip() for m in months.split(",") if m.strip()] if months else None

    async def _run():
        from scripts.backfill_history import run_backfill
        await run_backfill(month_list)

    _asyncio.create_task(_run())
    return {"status": "started", "message": "回填已在后台启动，查询 /scan/backfill-progress 查看进度"}


@router.get("/backfill-progress")
async def backfill_progress():
    """查询历史回填进度."""
    try:
        from scripts.backfill_history import get_progress
        return {"status": "success", "data": get_progress()}
    except ImportError:
        return {"status": "error", "detail": "回填模块未加载"}


@router.get("/data-freshness")
async def data_freshness():
    """Data freshness check — delegated to data_freshness_checker (v4.3)."""
    from app.services.data_freshness_checker import check_data_freshness
    return await check_data_freshness()


@router.post("/crawl-news")
async def crawl_news(force: bool = False):
    """手动触发: 爬取新闻 → LLM分析 → 入库 (SSE流式进度)."""
    import os, asyncio as _asyncio
    from app.core.config import settings as s
    import pathlib
    cookie = os.getenv("TUSHARE_COOKIE", "") or s.TUSHARE_COOKIE
    # 回退: 直接从.env文件读取
    if not cookie:
        env_file = pathlib.Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').split('\n'):
                if line.startswith('TUSHARE_COOKIE='):
                    cookie = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    if not cookie:
        return {"status": "error", "detail": "未配置 TUSHARE_COOKIE"}

    async def sse_gen():
        import json as _json
        import asyncio as _asyncio
        def _evt(data_dict):
            return f"data: {_json.dumps(data_dict, ensure_ascii=False)}\n\n"

        queue = _asyncio.Queue()

        async def progress_cb(phase, current, total, extra=None):
            try:
                await _asyncio.wait_for(queue.put({
                    "progress": True,
                    "phase": phase, "current": current, "total": total,
                    "msg": str(extra) if extra else f"{phase} {current}/{total}"
                }), timeout=1.0)
            except (_asyncio.TimeoutError, _asyncio.QueueFull):
                pass

        async def run_pipeline():
            try:
                from app.services.news_pipeline import run_news_pipeline
                # Delegate to news_pipeline service (v4.3)
                result = await run_news_pipeline(force=force, progress_callback=progress_cb)
                await queue.put({"step": "done", "done": True, "data": result})
            except Exception as e:
                import logging
                logging.getLogger("scan").error(f"crawl-news pipeline failed: {e}", exc_info=True)
                await queue.put({"step": 0, "msg": f"Failed: {str(e)[:120]}", "error": True})

        _asyncio.create_task(run_pipeline())

        while True:
            event = await _asyncio.wait_for(queue.get(), timeout=600)
            yield _evt(event)
            if event.get("done") or event.get("error"):
                break

    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@router.get("/news/recent")
async def get_recent_news(hours: int = 24):
    """获取最近N小时的新闻列表(供前端展示)."""
    from app.services.news_crawler import get_recent_news
    try:
        news = await get_recent_news(hours)
        return {"status": "success", "data": news, "count": len(news)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/news/events-today")
async def get_today_events():
    """Get today's news analysis results — delegated to event_aggregator (v4.3)."""
    from app.services.event_aggregator import get_aggregated_events
    return await get_aggregated_events(hours=24)


@router.get("/margin-sentiment")
async def get_margin_sentiment():
    """融资融券情绪: 近5日融资买入趋势 -> 市场温度计.

    自动处理 Tushare 数据源的三种混乱格式:
    - 格式A: ~8-11 (5月19+ 数据损毁) -> 过滤
    - 格式B: ~1400-2000 (亿元)
    - 格式C: ~174,000,000,000 (元) -> 归一化为亿元
    """
    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT trade_date, rzmre FROM margin_trading "
            "WHERE trade_date >= CURRENT_DATE - 30 "
            "ORDER BY trade_date DESC"
        ))
        all_rows = [(row[0], float(row[1] or 0)) for row in r.fetchall()]

    if len(all_rows) < 6:
        return {"status": "success", "data": {"sentiment": "neutral", "trend": 0, "detail": "数据不足"}}

    # 去重 + 单位归一化 + 过滤异常值
    seen_dates = set()
    normalized = []
    anomaly_count = 0
    for d, v in all_rows:
        if d in seen_dates:
            continue
        seen_dates.add(d)
        # 格式C: 超大值 (> 100,000) -> 元, 转换为亿元
        if v > 100_000:
            v = v / 100_000_000
        # 格式A: 值 < 100 -> 数据损毁, 跳过
        if v < 100:
            anomaly_count += 1
            continue
        normalized.append((d, v))

    if len(normalized) < 6:
        return {"status": "success", "data": {"sentiment": "neutral", "trend": 0,
                 "detail": f"有效数据不足 ({len(normalized)}条)", "anomaly_filtered": anomaly_count}}

    recent = [v for _, v in normalized[:5]]
    older = [v for _, v in normalized[5:10]]
    recent_dates = [str(d) for d, _ in normalized[:5]]

    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    change_pct = round((avg_recent - avg_older) / avg_older * 100, 1) if avg_older > 0 else 0

    if change_pct > 15: sentiment = "bullish"
    elif change_pct > 5: sentiment = "slightly_bullish"
    elif change_pct < -15: sentiment = "bearish"
    elif change_pct < -5: sentiment = "slightly_bearish"
    else: sentiment = "neutral"

    return {
        "status": "success",
        "data": {
            "sentiment": sentiment,
            "trend_pct": change_pct,
            "latest_buy_amt": round(avg_recent, 1),
            "detail": f"近5日均融资买入{avg_recent:.0f}亿 vs 前5日{avg_older:.0f}亿 ({change_pct:+.1f}%)",
            "latest_date": recent_dates[0],
            "anomaly_filtered": anomaly_count,
        }
    }


# ═══════════════════════════════════════════════════════════════
# 分钟线 N/M 反哺验证 — 长尾理论 ★ (2026-05-31)
# ═══════════════════════════════════════════════════════════════

@router.post("/verify-signals")
async def verify_signals_with_minute(
    limit: int = Query(30, description="验证前 N 只信号 (按 composite_score 排序)"),
):
    """对最新 TG 扫描信号运行分钟线 N/M 验证 + 板块联盟分析.

    调用 Tushare stk_mins API 下载 5 分钟线, 逐股检测 N/M 形态,
    然后按行业分组进行板块联盟对比, 输出调整后的信号质量。
    """
    from datetime import date as dt_date
    from app.services.signal_quality_scorer import verify_signals_with_minute_bars

    async with async_session_factory() as s:
        r = await s.execute(text("""
            SELECT s.symbol, COALESCE(nc.name, s.name, s.symbol) as name,
                   s.composite_score, s.level, s.industry, s.market
            FROM scan_results s
            LEFT JOIN stock_name_cache nc ON nc.symbol = s.symbol
            WHERE s.scan_date = (SELECT MAX(scan_date) FROM scan_results)
              AND s.composite_score >= 30
            ORDER BY s.composite_score DESC
            LIMIT :lim
        """), {"lim": limit})
        stocks = [{"symbol": row[0], "name": row[1],
                    "composite_score": float(row[2] or 0),
                    "level": row[3], "industry": row[4], "market": row[5]}
                  for row in r.fetchall()]

    if not stocks:
        return {"status": "error", "detail": "无最新扫描结果, 请先运行全市场扫描"}

    result = await verify_signals_with_minute_bars(stocks, dt_date.today(), top_n=limit)

    return {"status": "success", "data": result}


@router.post("/verify-nm-single")
async def verify_nm_single(
    symbol: str = Query(..., description="股票代码, 如 000001.SZ"),
):
    """单只股票 N/M 检测 (快速调试用)."""
    from app.services.minute_data import fetch_5min_bars
    from app.services.minute_nm_detector import detect_nm_pattern

    bars = await fetch_5min_bars(symbol, lookback_days=15)
    if len(bars) < 100:
        return {"status": "error", "detail": f"分钟数据不足 ({len(bars)} 根K线)", "bar_count": len(bars)}

    nm = detect_nm_pattern(bars)

    return {
        "status": "success",
        "data": {
            "symbol": symbol,
            "bar_count": len(bars),
            "nm_score": nm["nm_score"],
            "dominant_shape": nm["dominant_shape"],
            "n_days": nm["n_days"],
            "m_days": nm["m_days"],
            "n_ratio": nm["n_ratio"],
            "m_ratio": nm["m_ratio"],
            "verdict": nm["verdict"],
            "confidence": nm["confidence"],
            "total_days": nm["total_days"],
            "daily_shapes": nm["daily_shapes"],
        },
    }


@router.post("/verify-alliance")
async def verify_alliance(
    limit: int = Query(30, description="分析前 N 只信号的板块联盟"),
):
    """仅对最新信号运行板块联盟分析."""
    from datetime import date as dt_date
    from app.services.sector_alliance import analyze_sector_alliance

    async with async_session_factory() as s:
        r = await s.execute(text("""
            SELECT s.symbol, COALESCE(nc.name, s.name, s.symbol) as name,
                   s.composite_score, s.industry
            FROM scan_results s
            LEFT JOIN stock_name_cache nc ON nc.symbol = s.symbol
            WHERE s.scan_date = (SELECT MAX(scan_date) FROM scan_results)
              AND s.composite_score >= 30
            ORDER BY s.composite_score DESC
            LIMIT :lim
        """), {"lim": limit})
        stocks = [{"symbol": row[0], "name": row[1],
                    "composite_score": float(row[2] or 0), "industry": row[3]}
                  for row in r.fetchall()]

    if not stocks:
        return {"status": "error", "detail": "无最新扫描结果"}

    result = await analyze_sector_alliance(stocks, dt_date.today())

    return {"status": "success", "data": result}

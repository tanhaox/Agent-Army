"""TG scan API.

扫描状态: 优先使用 Redis 共享 (支持多 worker), Redis 不可用时降级到进程内存.
"""
import json, asyncio, logging, time as _time, os
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
_active_scan_state: dict = {"running": False, "phase": "", "current": 0, "total": 0, "pct": 0, "extra": "", "messages": [], "result": None}
_scan_lock = asyncio.Lock()


async def _set_scan_state(state: dict):
    """写入扫描状态 (Redis 优先, 内存降级)."""
    global _active_scan_state
    # 累积消息列表
    if "messages" in state:
        new_msgs = state["messages"]
        prev_msgs = _active_scan_state.get("messages") or []
        # 合并并去重（保留顺序）
        seen = set()
        merged = []
        for m in prev_msgs + new_msgs:
            key = f"{m.get('phase')}:{m.get('extra')}"
            if key not in seen:
                seen.add(key)
                merged.append(m)
        state["messages"] = merged[-50:]  # 最多50条
    _active_scan_state = state  # 始终保持内存同步
    try:
        from app.core.redis_client import get_redis
        r = await get_redis()
        if r:
            mapping = {}
            for k, v in state.items():
                if k == "messages":
                    mapping[k] = json.dumps(v)
                elif isinstance(v, (dict, list)):
                    mapping[k] = json.dumps(v)
                else:
                    mapping[k] = str(v)
            await r.hset("scan:state", mapping=mapping)
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
    limit: int = Query(100),
    min_score: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    # 优化：先获取最新扫描日期，避免子查询重复执行
    date_result = await db.execute(text("SELECT MAX(scan_date) FROM scan_results"))
    latest_date = date_result.scalar()
    if not latest_date:
        return {"status": "success", "data": [], "count": 0}

    result = await db.execute(text("""
        SELECT s.symbol, COALESCE(nc.name, s.name, s.symbol) as name, s.level,
               s.tg_momentum, s.dist_low, s.j_value,
               s.vol_ratio, s.buy_strength, s.close_price, s.composite_score,
               s.trigger_path, s.industry, COALESCE(s.market, '主板') as market,
               COALESCE(s.resonance_type,'daily_only') as resonance_type,
               COALESCE(s.weekly_tg_momentum,0) as weekly_tg_momentum
        FROM scan_results s
        LEFT JOIN stock_name_cache nc ON nc.symbol = s.symbol
        WHERE s.scan_date = :scan_date
          AND s.composite_score >= :ms
        ORDER BY s.composite_score DESC LIMIT :lim
    """), {"scan_date": latest_date, "ms": min_score, "lim": limit})
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
async def trigger_scan(
    skip_download: bool = Query(default=False),
    market_filter: str = Query(default="全部", description="板块过滤: 全部/主板/中小板/创业板"),
):
    global _active_scan, _active_scan_state

    if not await _acquire_scan_lock():
        return {"status": "error", "detail": "扫描已在运行中"}

    await _set_scan_state({"running": True, "phase": "", "current": 0, "total": 0, "pct": 0, "extra": "", "result": None})

    async def sse_gen():
        queue = asyncio.Queue()

        async def progress_cb(phase, current, total, extra=None):
            pct = min(99, int(current / max(total, 1) * 100))
            msg = str(extra) if extra else ""
            messages = [{"phase": phase, "extra": msg}] if msg else []
            await _set_scan_state({"running": True, "phase": phase, "current": current, "total": total, "pct": pct, "extra": msg, "messages": messages})
            try:
                await asyncio.wait_for(queue.put({"phase": phase, "current": current, "total": total, "pct": pct, "extra": extra}), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                pass  # 客户端未连接也继续扫描

        async def run_scan():
            import logging; _logger = logging.getLogger(__name__)
            try:
                # ① 龙虎榜准备 + 同步 (v4.8: 合并两个阶段, 一次性 ensure_toplist_fresh)
                await progress_cb("toplist", 0, 1, extra="检查龙虎榜数据...")
                if not skip_download:
                    try:
                        from app.services.sector_heat_engine import ensure_toplist_fresh
                        tl_status = await ensure_toplist_fresh()
                        await progress_cb("toplist", 1, 1, extra=f"龙虎榜: {tl_status.get('reason', tl_status.get('status', ''))}")
                    except Exception as e:
                        _logger.warning(f"龙虎榜检查失败: {e}")
                        await progress_cb("toplist", 1, 1, extra=f"龙虎榜异常: {e}")
                else:
                    await progress_cb("toplist", 1, 1, extra="龙虎榜跳过(skip_download)")

                # ② + ③ K线下载 + TG扫描 (使用并行扫描)
                num_workers = int(os.getenv("NUM_WORKERS", "1"))
                if num_workers > 1:
                    from app.services.scan_worker import parallel_scan_all_stocks
                    _logger.info(f"Using parallel scan: {num_workers} workers")
                    scan_func = parallel_scan_all_stocks
                else:
                    from app.services.tg_engine import scan_all_stocks
                    scan_func = scan_all_stocks

                async with async_session_factory() as s:
                    results, sd = await scan_func(s, progress_callback=progress_cb, skip_download=skip_download)
                l3_count = sum(1 for _, r in results.iterrows() if r.get("level") == "L3")
                l2_count = sum(1 for _, r in results.iterrows() if r.get("level") == "L2")

                # v4.8: 后端 market_filter 过滤 (前端送过来, 服务端真过滤)
                if market_filter and market_filter != "全部":
                    from app.utils.stock_code import classify_board
                    pre_count = len(results)
                    # 映射: 前端"主板" 包含 classify_board 的"上海主板"+"深圳主板"
                    board_map = {'主板': ['上海主板', '深圳主板']}
                    allowed = board_map.get(market_filter, [market_filter])
                    results = results[
                        results['symbol'].apply(lambda s: classify_board(s) in allowed)
                    ].reset_index(drop=True)
                    _logger.info(f"market_filter={market_filter} (allowed={allowed}): {pre_count} -> {len(results)}")

                # ④ 潜伏猎手 (v4.8: 改用最新 scan_date, 非历史最早)
                await progress_cb("ambush_scan", 0, 1, extra="TG扫描完成，开始潜伏猎手...")
                try:
                    from app.services.ambush_scanner import run_ambush_scan
                    from datetime import date as dt_date
                    async with async_session_factory() as s:
                        r = await s.execute(text("SELECT MAX(scan_date) FROM scan_results"))
                        amb_scan_date = r.scalar() or sd
                    amb = await run_ambush_scan(scan_date=amb_scan_date)
                    await progress_cb("ambush_scan", 1, 1,
                                      extra=f"潜伏猎手完成: {amb.get('signals', 0)} 个信号")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Ambush scan failed: {e}")
                    await progress_cb("ambush_scan", 1, 1, extra=f"潜伏猎手异常: {e}")

                # ⑤ 形态识别
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

                # ⑥ 多维度评分 (v4.8: 文案 12维 → 14维, 内部 DNA auto-join 移到最后)
                await progress_cb("deep_score", 0, 1, extra="开始14维深度评分...")
                try:
                    from app.services.deep_scorer import deep_analyze
                    async def deep_cb(phase, current, total, message=""):
                        await progress_cb("deep_score", current, total, extra=message)
                    async with async_session_factory() as s:
                        scored = await deep_analyze(s, scan_date=sd, progress_cb=deep_cb)
                    await progress_cb("deep_score", 1, 1,
                                      extra=f"14维评分完成: {len(scored)}只, 精选52只(>=70分)")
                except Exception as e:
                    import logging
                    logging.getLogger("scan").error(f"Deep scoring failed: {e}", exc_info=True)
                    await progress_cb("deep_score", 1, 1, extra=f"14维评分异常: {e}")

                # v4.9: 分钟线防伪移至评分后，只验证评分 >= 70 的精选股票
                await progress_cb("nm_defense", 0, 1, extra="分钟线防伪验证中...")
                try:
                    from app.services.signal_quality_scorer import quick_nm_scan
                    # 精选：只取 composite_score >= 70 的股票（约52只）
                    top_stocks = [s for s in scored if s.get("composite_score", 0) >= 70]
                    nm_result = await quick_nm_scan(str(sd), progress_cb, scored_stocks=top_stocks)
                    _logger.info(f"Quick NM scan: {nm_result.get('status')}, N:{nm_result.get('n_count',0)} M:{nm_result.get('m_count',0)}")
                    verdict_msg = f"N:{nm_result.get('n_count',0)} M:{nm_result.get('m_count',0)}"
                    await progress_cb("nm_defense", 1, 1, extra=f"防伪完成: {verdict_msg}")
                except Exception as e:
                    _logger.warning(f"分钟线防伪失败: {e}")
                    await progress_cb("nm_defense", 1, 1, extra=f"防伪异常: {str(e)[:50]}")

                # (v4.8: ⑧ toplist_sync 阶段已合并到 ①, 移除重复)

                # ⑨ 准确率验证 (P2-5: 改为事件驱动)
                # await progress_cb("accuracy_feedback", 0, 1, extra="验证历史推荐准确率...")
                # try:
                #     from app.services.accuracy_tracker import verify_all_periods, apply_accuracy_feedback
                #     verify_result = await verify_all_periods()
                #     fb_result = await apply_accuracy_feedback(isolated_meta=True)
                #     await progress_cb("accuracy_feedback", 1, 1,
                #         extra=f"准确率验证完成 (反馈: {fb_result.get('action','?')})")
                # except Exception as e:
                #     import logging
                #     logging.getLogger("scan").error(f"Accuracy feedback failed: {e}")
                #     await progress_cb("accuracy_feedback", 1, 1, extra=f"准确率验证异常: {e}")

                result_data = {"phase": "done", "count": len(results), "scan_date": str(sd),
                               "l3_count": l3_count, "l2_count": l2_count,
                               "scored_count": len(results)}

                # ⑩ DNA auto-join (P2-5: 改为事件驱动)
                # 注释掉直接调用，改为事件总线触发
                # if not skip_download:
                #     try:
                #         l3_stocks = [r.get("symbol") for _, r in results.iterrows() if r.get("level") == "L3"]
                #         if l3_stocks:
                #             await progress_cb("dna_auto_join", 0, 1, extra=f"L3股票 {len(l3_stocks)}只, 后台训练DNA模型...")
                #             import asyncio
                #             from app.services.stock_dna_auto_join import auto_join_for_scan
                #             dna_task = asyncio.create_task(auto_join_for_scan(l3_stocks))
                #             ... (async watching code)
                #     except Exception as e:
                #         ...

                await _set_scan_state({"running": False, "phase": "done", "current": 0, "total": 0, "pct": 100, "extra": "", "result": result_data})
                await _release_scan_lock()
                await queue.put(result_data)

                # P2-5: 发送 scan_completed 事件
                try:
                    from app.core.event_bus import event_bus
                    event_data = {
                        "scan_date": str(sd),
                        "total": len(results),
                        "l3_count": l3_count,
                        "l2_count": l2_count,
                    }
                    await event_bus.emit("scan_completed", event_data)
                except Exception as e:
                    _logger.warning(f"EventBus emit failed: {e}")
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
    """龙虎榜分析: 个股合力 + 板块共振. market=主板/创业板/全部.

    v2.1: 智能缓存 (按交易日), 避免重复调取.
    """
    from datetime import date as _dt
    from app.services.toplist_analyzer import get_cached_daily_toplist

    if date:
        td = _dt.fromisoformat(date)
        result = await get_cached_daily_toplist(td, force=False)
    else:
        result = await get_cached_daily_toplist()  # 自动取最近交易日

    # 按板块过滤
    stocks = result.get("stocks", [])
    if market and market != "全部":
        stocks = [s for s in stocks if s.get("market", "主板") == market]

    return {
        "status": "success",
        "data": {
            "stocks": stocks,
            "sectors": result.get("sectors", []),
            "total": len(stocks),
            "date": result.get("date"),
            "cached": result.get("cached", False),
            "cache_age_minutes": result.get("cache_age_minutes", 0),
            "is_trading": result.get("is_trading", False),
            "is_historical": result.get("is_historical", False),
        }
    }


@router.post("/toplist-refresh")
async def refresh_toplist(date: str = ""):
    """v2.1: 强制刷新龙虎榜数据 (SSE 流式进度)."""
    from datetime import date as _dt
    import asyncio as _asyncio
    from app.services.toplist_analyzer import (
        get_cached_daily_toplist, clear_toplist_cache,
        sync_recent_days as _sync,
    )

    async def sse_gen():
        queue = _asyncio.Queue()

        async def emit(phase, current, total, msg):
            try:
                await _asyncio.wait_for(queue.put({
                    "phase": phase, "current": current, "total": total, "msg": msg
                }), timeout=1.0)
            except (_asyncio.TimeoutError, _asyncio.QueueFull):
                pass

        async def run_refresh():
            try:
                td = _dt.fromisoformat(date) if date else _dt.today()

                # 1. 同步最新数据 (如未同步)
                await emit("sync", 0, 1, "检查数据新鲜度...")
                try:
                    from app.services.sector_heat_engine import sync_recent_days
                    sync_res = await sync_recent_days(days=2)
                    synced = sum(1 for r in sync_res if r.get("status") == "success")
                    await emit("sync", 1, 1, f"同步完成: {synced}天新数据")
                except Exception as e:
                    await emit("sync", 1, 1, f"同步跳过: {e}")

                # 2. 清除缓存 + 强制重新计算
                await emit("analyze", 0, 1, "重新分析个股席位...")
                clear_toplist_cache(td)
                result = await get_cached_daily_toplist(td, force=True)
                await emit("analyze", 1, 1, f"个股分析: {len(result.get('stocks', []))}只")

                # 3. 板块共振
                await emit("sector", 0, 1, "计算板块共振...")
                # 板块共振在 get_cached_daily_toplist 内部已计算
                await emit("sector", 1, 1, f"板块共振: {len(result.get('sectors', []))}个")

                # 完成
                await queue.put({
                    "done": True,
                    "data": {
                        "date": result.get("date"),
                        "total_stocks": result.get("total"),
                        "total_sectors": result.get("total_sectors"),
                    }
                })
            except Exception as e:
                logger = __import__("logging").getLogger("scan")
                logger.error(f"toplist refresh failed: {e}", exc_info=True)
                await queue.put({"done": True, "error": True, "msg": str(e)})

        _asyncio.ensure_future(run_refresh())

        while True:
            event = await _asyncio.wait_for(queue.get(), timeout=60)
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("done") or event.get("error"):
                break

    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@router.get("/toplist-freshness")
async def get_toplist_freshness():
    """v2.1: 龙虎榜数据新鲜度.

    Returns:
        - last_update: 最近一次更新
        - latest_trade_date: 最近交易日
        - is_trading: 是否在交易时段
        - recommendation: skip / refresh
    """
    from datetime import date as _dt
    from app.services.toplist_analyzer import (
        _is_trading_hours_now, _toplist_cache, _get_latest_trade_date_async
    )

    latest_td = await _get_latest_trade_date_async()
    cache_key = latest_td.isoformat()
    cache = _toplist_cache.get(cache_key, {})

    cached_at = cache.get("_cached_at", 0)
    cache_age_min = (_time.time() - cached_at) / 60 if cached_at else None

    # 建议
    is_trading = _is_trading_hours_now()
    is_historical = latest_td < _dt.today()

    if is_historical:
        recommendation = "skip"  # 历史数据, 无需刷新
    elif is_trading:
        recommendation = "refresh" if (cache_age_min is None or cache_age_min > 5) else "skip"
    else:
        recommendation = "refresh" if (cache_age_min is None or cache_age_min > 60) else "skip"

    return {
        "status": "success",
        "latest_trade_date": str(latest_td),
        "is_trading": is_trading,
        "is_historical": is_historical,
        "cache_age_minutes": round(cache_age_min, 1) if cache_age_min else None,
        "has_cache": bool(cache),
        "recommendation": recommendation,
    }


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
    """融资融券情绪: 融资余额 + 趋势 → 市场温度计.

    杠杆水平 (按用户标准):
      - > 1.6万亿 = 亢奋 (注意风险)
      - 1.2-1.6万亿 = 正常
      - < 1.2万亿 = 谨慎
    """
    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT trade_date, rzmre, rzye, rqye FROM margin_trading "
            "WHERE trade_date >= CURRENT_DATE - 30 "
            "ORDER BY trade_date DESC"
        ))
        all_rows = [(row[0], float(row[1] or 0), float(row[2] or 0), float(row[3] or 0)) for row in r.fetchall()]

    if len(all_rows) < 1:
        return {"status": "success", "data": {
            "sentiment": "neutral", "trend_pct": 0,
            "label": "融资余额", "value_yi": 0, "level": "未知",
            "detail": "数据不足"
        }}

    latest_date, latest_rzmre, latest_rzye, latest_rqye = all_rows[0]
    rzye_yi = round(latest_rzye / 1e8, 0)

    if rzye_yi > 16000:
        level = "亢奋"
        level_color = "#ef4444"
        level_note = "杠杆亢奋(注意风险)"
    elif rzye_yi >= 12000:
        level = "正常"
        level_color = "#10b981"
        level_note = "杠杆水平正常"
    else:
        level = "谨慎"
        level_color = "#3b82f6"
        level_note = "情绪谨慎"

    trend_pct = 0
    if len(all_rows) >= 6:
        recent_avg = sum(r[2] for r in all_rows[:5]) / 5
        older_avg = sum(r[2] for r in all_rows[5:10]) / max(min(5, len(all_rows) - 5), 1)
        if older_avg > 0:
            trend_pct = round((recent_avg - older_avg) / older_avg * 100, 1)

    if trend_pct > 5 and rzye_yi > 12000:
        sentiment = "bullish"
    elif trend_pct < -5 and rzye_yi < 12000:
        sentiment = "bearish"
    elif level == "亢奋":
        sentiment = "cautious_bullish"
    elif level == "谨慎":
        sentiment = "cautious_bearish"
    else:
        sentiment = "neutral"

    trend_str = f"{trend_pct:+.1f}%" if trend_pct else "持平"
    detail = f"融资余额{rzye_yi:,.0f}亿 ({level}) · 5日趋势{trend_str}"

    return {
        "status": "success",
        "data": {
            "sentiment": sentiment,
            "level": level,
            "level_color": level_color,
            "level_note": level_note,
            "trend_pct": trend_pct,
            "value_yi": rzye_yi,
            "label": f"融资余额 {rzye_yi:,.0f}亿",
            "value": f"{rzye_yi:,.0f}",
            "unit": "亿",
            "change": trend_str,
            "detail": detail,
            "short_balance_yi": round(latest_rqye / 1e8, 0),
        }
    }


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
    from app.services.minute_on_demand import get_minute_bars
    from app.services.minute_nm_detector import detect_nm_pattern

    bars = await get_minute_bars(symbol, period='5min', days=15)
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


# ══════════════════════════════════════════════════════════════════════
# 新闻速报聚合接口 (v4.8) — 一次返回所有数据
# ══════════════════════════════════════════════════════════════════════

@router.get("/news-dashboard")
async def get_news_dashboard():
    """聚合新闻页面所有数据，一次返回。

    优化点:
    - 合并 6 个独立请求为 1 个
    - 并行执行所有查询
    - 返回统一结构，包含所有展示所需数据
    """
    import asyncio
    from datetime import date as dt_date

    async def _events():
        from app.services.event_aggregator import get_aggregated_events
        return await get_aggregated_events(hours=24)

    async def _margin():
        return await get_margin_sentiment()

    async def _freshness():
        from app.services.data_freshness_checker import check_data_freshness
        return await check_data_freshness()

    async def _sector():
        from app.services.sector_heat_engine import get_sector_heat
        return await get_sector_heat(days=5)

    async def _toplist():
        # v2.1: 使用 get_cached_daily_toplist 一次性返回 个股+板块共振
        from app.services.toplist_analyzer import get_cached_daily_toplist
        return await get_cached_daily_toplist()

    # 并行执行所有查询
    events, margin, freshness, sector, toplist = await asyncio.gather(
        _events(), _margin(), _freshness(), _sector(), _toplist(),
        return_exceptions=True
    )

    # 处理异常
    def safe(v, fallback):
        if isinstance(v, Exception):
            logger.warning(f"news-dashboard: {type(v).__name__}: {v}")
            return fallback
        return v

    return {
        "status": "success",
        "events": safe(events, {"status": "error", "data": {}}),
        "margin": safe(margin, {"sentiment": "unknown"}),
        "freshness": safe(freshness, {"stale": False}),
        "sector_heat": safe(sector, {}),
        "toplist": safe(toplist, {"stocks": [], "sectors": [], "total": 0}),
    }


@router.get("/news-freshness")
async def get_news_freshness():
    """检查新闻数据新鲜度，决定是否需要完整爬取。

    返回:
    - last_crawl: 上次爬取时间
    - last_analysis: 上次LLM分析时间
    - should_crawl: 是否需要爬取
    - should_full_analyze: 是否需要完整LLM分析
    - recommendation: 建议的操作 (skip/analyze_only/full/crawl_only)
    """
    from datetime import datetime, timedelta, timezone

    async with async_session_factory() as s:
        # news_raw 最近一条
        r = await s.execute(text("SELECT MAX(fetched_at) FROM news_raw"))
        last_crawl = r.scalar()

        # stock_events 最近一条
        r2 = await s.execute(text("SELECT MAX(created_at) FROM stock_events"))
        last_analysis = r2.scalar()

    now = datetime.now(timezone.utc)
    hours_since_crawl = None
    hours_since_analysis = None

    if last_crawl:
        if getattr(last_crawl, 'tzinfo', None) is None:
            last_crawl = last_crawl.replace(tzinfo=timezone.utc)
        hours_since_crawl = (now - last_crawl).total_seconds() / 3600

    if last_analysis:
        if getattr(last_analysis, 'tzinfo', None) is None:
            last_analysis = last_analysis.replace(tzinfo=timezone.utc)
        hours_since_analysis = (now - last_analysis).total_seconds() / 3600

    # 智能判断
    should_crawl = hours_since_crawl is None or hours_since_crawl > 2  # 2小时前爬过
    should_full_analyze = hours_since_analysis is None or hours_since_analysis > 6  # 6小时前分析过

    if not should_crawl and not should_full_analyze:
        recommendation = "skip"
    elif not should_crawl and should_full_analyze:
        recommendation = "analyze_only"  # 只做 LLM 分析
    elif should_crawl and should_full_analyze:
        recommendation = "full"  # 完整执行
    else:
        recommendation = "crawl_only"  # 只爬取

    return {
        "status": "success",
        "last_crawl": str(last_crawl) if last_crawl else None,
        "last_analysis": str(last_analysis) if last_analysis else None,
        "hours_since_crawl": round(hours_since_crawl, 1) if hours_since_crawl else None,
        "hours_since_analysis": round(hours_since_analysis, 1) if hours_since_analysis else None,
        "should_crawl": should_crawl,
        "should_full_analyze": should_full_analyze,
        "recommendation": recommendation,
    }


# ══════════════════════════════════════════════════════════════════════════
# v2.1: 融资融券情绪 (重写) — 改用 rzye (融资余额) 直接判断
# ══════════════════════════════════════════════════════════════════════════

async def get_margin_sentiment():
    """融资融券情绪: 融资余额 + 趋势 → 市场温度计.

    杠杆水平 (按用户标准):
      - > 1.6万亿 = 亢奋 (注意风险)
      - 1.2-1.6万亿 = 正常
      - < 1.2万亿 = 谨慎
    """
    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT trade_date, rzmre, rzye, rqye FROM margin_trading "
            "WHERE trade_date >= CURRENT_DATE - 30 "
            "ORDER BY trade_date DESC"
        ))
        all_rows = [(row[0], float(row[1] or 0), float(row[2] or 0), float(row[3] or 0)) for row in r.fetchall()]

    if len(all_rows) < 1:
        return {"status": "success", "data": {
            "sentiment": "neutral", "trend_pct": 0,
            "label": "融资余额", "value_yi": 0, "level": "未知",
            "detail": "数据不足"
        }}

    latest_date, latest_rzmre, latest_rzye, latest_rqye = all_rows[0]
    rzye_yi = round(latest_rzye / 1e8, 0)  # 元 → 亿元

    # 杠杆水平直接判断 (用户标准)
    if rzye_yi > 16000:
        level = "亢奋"
        level_color = "#ef4444"
        level_note = "杠杆亢奋(注意风险)"
    elif rzye_yi >= 12000:
        level = "正常"
        level_color = "#10b981"
        level_note = "杠杆水平正常"
    else:
        level = "谨慎"
        level_color = "#3b82f6"
        level_note = "情绪谨慎"

    # 5日趋势 (用融资余额变化)
    trend_pct = 0
    if len(all_rows) >= 6:
        recent_avg = sum(r[2] for r in all_rows[:5]) / 5
        older_avg = sum(r[2] for r in all_rows[5:10]) / max(min(5, len(all_rows) - 5), 1)
        if older_avg > 0:
            trend_pct = round((recent_avg - older_avg) / older_avg * 100, 1)

    # 综合情绪
    if trend_pct > 5 and rzye_yi > 12000:
        sentiment = "bullish"
    elif trend_pct < -5 and rzye_yi < 12000:
        sentiment = "bearish"
    elif level == "亢奋":
        sentiment = "cautious_bullish"
    elif level == "谨慎":
        sentiment = "cautious_bearish"
    else:
        sentiment = "neutral"

    trend_str = f"{trend_pct:+.1f}%" if trend_pct else "持平"
    detail = f"融资余额{rzye_yi:,.0f}亿 ({level}) · 5日趋势{trend_str}"

    return {
        "status": "success",
        "data": {
            "sentiment": sentiment,
            "level": level,
            "level_color": level_color,
            "level_note": level_note,
            "trend_pct": trend_pct,
            "value_yi": rzye_yi,
            "label": f"融资余额 {rzye_yi:,.0f}亿",
            "value": f"{rzye_yi:,.0f}",
            "unit": "亿",
            "change": trend_str,
            "detail": detail,
            "short_balance_yi": round(latest_rqye / 1e8, 0),
        }
    }

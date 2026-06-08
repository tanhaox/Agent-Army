"""统一股票名称解析 (P0 系统级).

消除 5 处绕过缓存直接查 scan_results 的分散实现。
三级缓存: 内存 dict (L1) → DB (L2) → raw code fallback (L3).

核心函数:
  get_stock_name(ts_code)     — 单个查询
  batch_get_stock_names(list) — 批量查询 (避免 N+1)
  ensure_name_cache()         — 预加载
"""
import asyncio
import logging
from sqlalchemy import text
from app.core.database import async_session_factory

logger = logging.getLogger("name_resolver")

_cache: dict[str, str] = {}
_lock = asyncio.Lock()
_loaded = False


async def ensure_name_cache():
    """从 stock_name_cache 表预加载名称缓存 (安全并发)."""
    global _loaded, _cache
    if _loaded:
        return

    async with _lock:
        if _loaded:
            return
        try:
            async with async_session_factory() as s:
                r = await s.execute(text("SELECT symbol, name FROM stock_name_cache"))
                for row in r.fetchall():
                    if row[1]:
                        _cache[row[0]] = row[1]

            # 补充: scan_results 中最近出现的名 (覆盖新上市/改名)
            async with async_session_factory() as s:
                r = await s.execute(text("""
                    SELECT DISTINCT ON (symbol) symbol, name
                    FROM scan_results WHERE name IS NOT NULL
                    ORDER BY symbol, scan_date DESC
                """))
                for row in r.fetchall():
                    if row[0] not in _cache and row[1]:
                        _cache[row[0]] = row[1]

            _loaded = True
            logger.info(f"Name cache loaded: {len(_cache)} names")
        except Exception as e:
            logger.warning(f"Name cache load failed: {e}")


async def get_stock_name(ts_code: str) -> str:
    """获取股票名称.

    查询顺序: 内存缓存 → stock_name_cache 表 → scan_results 表 → raw code
    """
    # L1: 内存缓存
    if ts_code in _cache:
        return _cache[ts_code]

    # L2: DB 查询
    try:
        async with async_session_factory() as s:
            for tbl, col in [
                ("stock_name_cache", "name"),
                ("scan_results", "name"),
            ]:
                try:
                    r = await s.execute(text(
                        f"SELECT {col} FROM {tbl} WHERE symbol = :sym "
                        f"ORDER BY {col} LIMIT 1"
                    ), {"sym": ts_code})
                    row = r.fetchone()
                    if row and row[0]:
                        _cache[ts_code] = row[0]
                        return row[0]
                except Exception:
                    continue
    except Exception:
        pass

    # L3: Fallback
    return ts_code


async def batch_get_stock_names(symbols: list[str]) -> dict[str, str]:
    """批量获取名称 (一次 DB 查询, 避免 N+1)."""
    result = {}
    missing = []

    for sym in symbols:
        if sym in _cache:
            result[sym] = _cache[sym]
        else:
            missing.append(sym)

    if not missing:
        return result

    try:
        async with async_session_factory() as s:
            r = await s.execute(text(
                "SELECT DISTINCT ON (symbol) symbol, name FROM scan_results "
                "WHERE symbol = ANY(:syms) AND name IS NOT NULL "
                "ORDER BY symbol, scan_date DESC"
            ), {"syms": missing})
            for row in r.fetchall():
                if row[1]:
                    _cache[row[0]] = row[1]
                    result[row[0]] = row[1]
    except Exception as e:
        logger.warning(f"Batch name query failed: {e}")

    for sym in missing:
        if sym not in result:
            result[sym] = sym

    return result

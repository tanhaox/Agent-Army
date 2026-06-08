"""Event aggregation service - extracted from scan.py (v4.3)."""
import re
import logging
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import text
from app.core.database import async_session_factory

logger = logging.getLogger("event_aggregator")


def _match_hk_to_a(hk_code: str, title: str, a_names: dict[str, str]) -> str | None:
    """Try matching HK stock event to A-stock code via company name."""
    name_match = re.match(r'([一-鿿]{2,4})', title)
    if not name_match:
        return None
    company = name_match.group(1)
    skip_words = {'今日','昨日','明天','本周','上周','早盘','午盘','收盘','开盘','涨停','跌停','市场','大盘','上证','深证','创业','科创','北向','主力','游资','机构'}
    if company in skip_words:
        return None
    for a_code, a_name in a_names.items():
        if company in a_name:
            return a_code
    return None


def _norm_sector(sec: str) -> str:
    """Normalize sector name."""
    if not sec:
        return "unknown"
    return sec.strip()


async def get_aggregated_events(hours: int = 24) -> dict:
    """HK->A matching + event decay + market classification + sector dedup + macro factors + last_analysis timestamp."""
    today = date.today()
    lookback = today - timedelta(days=7)

    async with async_session_factory() as s:
        r = await s.execute(text(
            "SELECT ts_code, direction, composite_impact, title, summary, decay_days, created_at, event_date "
            "FROM stock_events WHERE event_date BETWEEN :lb AND :d "
            "AND (ts_code LIKE '%.SZ' OR ts_code LIKE '%.SH' OR (length(ts_code)=6 AND ts_code ~ '^[036]')) "
            "ORDER BY composite_impact DESC LIMIT 60"
        ), {"lb": lookback, "d": today})
        rows = r.fetchall()

        # Preload A-stock name map (for HK->A matching)
        r2 = await s.execute(text(
            "SELECT symbol, name FROM stock_name_cache WHERE symbol NOT LIKE '%.HK'"
        ))
        a_stock_names = {row[0]: row[1] for row in r2.fetchall()}

    stocks = []
    for row in rows:
        ts_code = row[0]
        impact = float(row[2] or 0)
        decay_days = int(row[5] or 3)
        created_at = row[6]
        if created_at:
            ct = created_at.replace(tzinfo=timezone.utc) if getattr(created_at, 'tzinfo', None) is None else created_at
            days_since = (datetime.now(timezone.utc) - ct).total_seconds() / 86400
        else:
            days_since = 0
        if days_since >= decay_days:
            continue
        freshness = round(max(0, 1 - days_since / max(decay_days, 1)), 2)
        display_score = round(impact * freshness, 2)
        entry = {"ts_code": ts_code, "direction": row[1],
                 "impact": impact, "title": row[3], "summary": row[4],
                 "freshness": freshness, "display_score": display_score,
                 "decay_days": decay_days, "event_date": str(row[7]),
                 "days_ago": round(days_since, 1)}
        stocks.append(entry)
    stocks.sort(key=lambda x: x["display_score"], reverse=True)

    # Market classification
    sme_stocks = [s for s in stocks if s["ts_code"].startswith('002') or s["ts_code"].startswith('003')]
    main_stocks = [s for s in stocks if not (s["ts_code"].startswith('300') or s["ts_code"].startswith('301') or s["ts_code"].startswith('688') or s["ts_code"].startswith('002') or s["ts_code"].startswith('003'))]
    chinext_stocks = [s for s in stocks if s["ts_code"].startswith('300') or s["ts_code"].startswith('301') or s["ts_code"].startswith('688')]

    # Sector events (dedup + normalize)
    sectors = []
    macro_factors = []
    last_analysis = None
    try:
        async with async_session_factory() as s:
            r_se = await s.execute(text(
                "SELECT sector, direction, composite_impact, prediction "
                "FROM sector_events WHERE event_date BETWEEN :lb AND :d "
                "ORDER BY composite_impact DESC"
            ), {"lb": lookback, "d": today})
            deduped = {}
            for row in r_se.fetchall():
                sec = _norm_sector(row[0])
                imp = float(row[2] or 0)
                if sec not in deduped or imp > deduped[sec]["impact"]:
                    deduped[sec] = {"sector": sec, "direction": row[1], "impact": imp, "prediction": row[3]}
            sectors = sorted(deduped.values(), key=lambda x: x["impact"], reverse=True)[:20]

            # Macro factors
            r_macro = await s.execute(text(
                "SELECT direction, composite_impact, prediction FROM sector_events "
                "WHERE event_date BETWEEN :lb AND :d AND sector LIKE 'macro-%' "
                "ORDER BY composite_impact DESC"
            ), {"lb": lookback, "d": today})
            for row in r_macro.fetchall():
                macro_factors.append({
                    "direction": row[0], "impact": float(row[1] or 0),
                    "summary": row[2] or "",
                })

            # Last analysis time
            r_ts = await s.execute(text("SELECT MAX(created_at) FROM stock_events"))
            last_ts = r_ts.scalar()
            if last_ts:
                if getattr(last_ts, 'tzinfo', None) is not None:
                    last_ts_utc = last_ts.astimezone(timezone.utc)
                else:
                    last_ts_utc = last_ts.replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - last_ts_utc
                hours_ago = round(delta.total_seconds() / 3600, 1)
                last_analysis = {"at": str(last_ts), "hours_ago": hours_ago,
                               "stale": hours_ago > 24}
    except Exception:
        pass

    return {
        "status": "success",
        "data": {
            "stock_events": stocks, "main_stock_events": main_stocks,
            "sme_stock_events": sme_stocks,
            "chinext_stock_events": chinext_stocks, "sector_events": sectors,
        },
        "last_analysis": last_analysis,
    }

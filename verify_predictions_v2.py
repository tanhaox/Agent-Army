#!/usr/bin/env python3
"""
verify_predictions_v2.py - 预测验证统一脚本（v2.0）

功能：
1. 查询未验证的 predictions 记录
2. 从 daily_kline 获取预测日和5日后收盘价
3. 计算实际收益，更新 actual_return_5d / actual_result / is_correct / verified
4. 支持次日方向验证（actual_result: up/down/flat）

用法：
    python3 scripts/verify_predictions_v2.py              # 验证5天前的预测
    python3 scripts/verify_predictions_v2.py --force       # 强制验证所有未验证的
    python3 scripts/verify_predictions_v2.py --dry-run     # 预览模式

Cron：每日 16:30 执行
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace')

import duckdb

PREDICTIONS_DB = '/root/.openclaw/workspace/data/predictions.db'
MARKET_DATA_DB = '/root/.openclaw/workspace/data/market_data.db'


def strip_suffix(code):
    """Convert '600887.SS'/'600887.SZ' to '600887'"""
    return code.split('.')[0] if '.' in code else code


def verify_predictions(force=False, dry_run=False, min_age_days=1):
    """验证到期预测

    Args:
        force: 强制验证所有未验证的
        dry_run: 预览模式
        min_age_days: 预测至少距今N天才验证
    """
    pred_conn = duckdb.connect(PREDICTIONS_DB)
    market_conn = duckdb.connect(MARKET_DATA_DB, read_only=True)

    cutoff = (datetime.now() - timedelta(days=min_age_days)).strftime('%Y-%m-%d')

    if force:
        query = """
            SELECT prediction_id, stock_code, analysis_date, recommendation
            FROM predictions
            WHERE verified IS NULL OR verified = false
            ORDER BY analysis_date
        """
    else:
        query = f"""
            SELECT prediction_id, stock_code, analysis_date, recommendation
            FROM predictions
            WHERE (verified IS NULL OR verified = false)
              AND analysis_date <= '{cutoff}'
            ORDER BY analysis_date
        """

    rows = pred_conn.execute(query).fetchall()

    if not rows:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 没有需要验证的预测")
        pred_conn.close()
        market_conn.close()
        return

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 找到 {len(rows)} 条待验证预测")

    updated = 0
    skipped = 0

    for pred_id, stock_code, analysis_date, recommendation in rows:
        short_code = strip_suffix(stock_code)

        # 1. 获取预测日收盘价
        base_row = market_conn.execute(
            "SELECT close FROM daily_kline WHERE stock_code = ? AND date <= ? ORDER BY date DESC LIMIT 1",
            [short_code, analysis_date]
        ).fetchone()

        if not base_row:
            print(f"  SKIP {pred_id}: {stock_code} 无K线数据 ({analysis_date})")
            skipped += 1
            continue

        base_close = base_row[0]

        # 2. 获取次日收盘价（方向验证）
        next_row = market_conn.execute(
            "SELECT close, date FROM daily_kline WHERE stock_code = ? AND date > ? ORDER BY date ASC LIMIT 1",
            [short_code, analysis_date]
        ).fetchone()

        if not next_row:
            print(f"  SKIP {pred_id}: {stock_code} 无次日数据 ({analysis_date})")
            skipped += 1
            continue

        next_close = next_row[0]
        next_date = next_row[1]

        # 计算次日方向
        next_return = (next_close - base_close) / base_close * 100
        if next_return > 0.5:
            actual_result = 'up'
        elif next_return < -0.5:
            actual_result = 'down'
        else:
            actual_result = 'flat'

        # 3. 获取5日后收盘价（收益验证）
        future_row = market_conn.execute(
            "SELECT close, date FROM daily_kline WHERE stock_code = ? AND date > ? ORDER BY date ASC LIMIT 1 OFFSET 4",
            [short_code, analysis_date]
        ).fetchone()

        actual_return_5d = None
        is_correct = None

        if future_row:
            future_close = future_row[0]
            actual_return_5d = round((future_close / base_close - 1) * 100, 4)

            # 判断预测是否正确
            if recommendation:
                rec = recommendation.lower()
                if rec in ('buy', 'strong_buy', '加仓') and actual_result == 'up':
                    is_correct = True
                elif rec in ('sell', 'strong_sell', '减仓') and actual_result == 'down':
                    is_correct = True
                elif rec == 'hold' and actual_result == 'flat':
                    is_correct = True
                else:
                    is_correct = False

        # 4. 更新数据库
        prefix = "[DRY-RUN] " if dry_run else ""
        result_str = f"{actual_result} ({next_return:+.2f}%"
        if actual_return_5d is not None:
            result_str += f", 5d={actual_return_5d:+.2f}%"
        result_str += ")"
        correct_str = f", correct={is_correct}" if is_correct is not None else ""
        print(f"  {prefix}{pred_id}: {stock_code} {analysis_date} -> {result_str}{correct_str}")

        if not dry_run:
            # actual_result is JSON type in DuckDB, need to serialize
            pred_conn.execute("""
                UPDATE predictions SET
                    actual_result = ?::JSON,
                    future_5d_return = COALESCE(?, future_5d_return),
                    actual_return_5d = COALESCE(?, actual_return_5d),
                    is_correct = ?,
                    verified = true,
                    verified_time = ?
                WHERE prediction_id = ?
            """, [json.dumps(actual_result), actual_return_5d, actual_return_5d, is_correct, datetime.now().isoformat(), pred_id])

        updated += 1

    if not dry_run and updated > 0:
        print(f"\n验证完成: 更新 {updated} 条, 跳过 {skipped} 条")
    else:
        print(f"\n预览: 将更新 {updated} 条, 跳过 {skipped} 条")

    pred_conn.close()
    market_conn.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='预测验证工具 v2.0')
    parser.add_argument('--force', action='store_true', help='强制验证所有未验证预测')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    parser.add_argument('--days', type=int, default=1, help='预测至少距今N天 (默认1)')
    args = parser.parse_args()

    verify_predictions(force=args.force, dry_run=args.dry_run, min_age_days=args.days)

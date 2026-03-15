#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经数据同步脚本（简化版）
使用yfinance和DELETE+INSERT策略
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import duckdb

# 检查yfinance
try:
    import yfinance as yf
    print('✅ yfinance已安装')
except ImportError:
    print('安装yfinance...')
    os.system('pip install yfinance -q')
    import yfinance as yf
    print('✅ yfinance安装完成')

# 数据库路径
DB_DIR = Path(__file__).parent.parent / 'data'
DB_PATH = DB_DIR / 'stock_market_v2.db'  # 使用新数据库

# 测试股票列表
TEST_STOCKS = [
    {'code': '600887', 'name': '伊利股份', 'exchange': 'SS'},
    {'code': '000001', 'name': '平安银行', 'exchange': 'SZ'},
    {'code': '601669', 'name': '中国电建', 'exchange': 'SS'},
    {'code': '002594', 'name': '比亚迪', 'exchange': 'SZ'},
    {'code': '300750', 'name': '宁德时代', 'exchange': 'SZ'}
]

def log(msg):
    """打印日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {msg}')

def sync_yahoo_kline(code, name, exchange, period='1mo'):
    """同步雅虎财经K线数据"""
    try:
        log(f'  同步 {name} ({code}) K线...')

        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        df = ticker.history(period=period)

        if df is None or len(df) == 0:
            log(f'  ⚠️ {name} 无数据')
            return False

        con = duckdb.connect(str(DB_PATH))
        inserted = 0

        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d')

            # 计算涨跌幅
            pct_change = None
            if idx != df.index[0]:
                prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
                pct_change = (row['Close'] - prev_close) / prev_close * 100

            try:
                # 完整的INSERT语句，包含所有30个字段
                con.execute('''
                    INSERT INTO stock_kline_unified
                    (source, source_type, code, name, date, time,
                     open, high, low, close, adj_close, volume,
                     dividends, stock_splits, pct_change, turnover_rate, amount,
                     pe_ratio, market_cap,
                     main_net_inflow, super_large_net_inflow, large_net_inflow,
                     medium_net_inflow, small_net_inflow,
                     crawl_time, crawl_url, crawl_status,
                     data_quality, completeness, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'yahoo', 'api', code, name, date_str, None,  # source, source_type, code, name, date, time
                    row['Open'], row['High'], row['Low'], row['Close'],  # open, high, low, close
                    row.get('Adj Close'), int(row['Volume']) if row['Volume'] else None,  # adj_close, volume
                    row['Dividends'], row['Stock Splits'], pct_change,  # dividends, stock_splits, pct_change
                    None, None, None, None,  # turnover_rate, amount, pe_ratio, market_cap（雅虎无此数据）
                    None, None, None, None, None,  # main_net_inflow...small_net_inflow（东方财富字段，预留）
                    None, None, None,  # crawl_time, crawl_url, crawl_status
                    'good', 100.0, datetime.now(), datetime.now()  # data_quality, completeness, created_at, updated_at
                ))
                inserted += 1
            except Exception as e:
                log(f'  ⚠️ {date_str} 失败: {e}')

        con.close()
        log(f'  ✅ {name}: {inserted}条')
        return True

    except Exception as e:
        log(f'  ❌ {name} 失败: {e}')
        return False

def main():
    """主函数"""
    print('=' * 100)
    print('  雅虎财经数据同步（简化版）')
    print('=' * 100)
    print()
    print(f'数据库: {DB_PATH}')
    print(f'股票: {len(TEST_STOCKS)}只')
    print()

    if not DB_PATH.exists():
        log('❌ 数据库不存在')
        return

    log('开始同步...')
    print()

    success = 0
    for stock in TEST_STOCKS:
        if sync_yahoo_kline(stock['code'], stock['name'], stock['exchange']):
            success += 1
        time.sleep(1)

    print()
    print('=' * 100)
    print(f'  完成: {success}/{len(TEST_STOCKS)}')
    print('=' * 100)

if __name__ == '__main__':
    main()

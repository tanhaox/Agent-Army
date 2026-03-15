#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经数据同步脚本（阶段1）
同步K线数据和个股信息
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import duckdb

# 检查yfinance
try:
    import yfinance as yf
    print('✅ yfinance导入成功')
except ImportError:
    print('❌ yfinance未安装，正在安装...')
    os.system('pip install yfinance -q')
    import yfinance as yf
    print('✅ yfinance安装成功')

# 数据库路径
DB_DIR = Path(__file__).parent.parent / 'data'
DB_PATH = DB_DIR / 'stock_market.db'

# 测试股票列表
TEST_STOCKS = [
    {'code': '600519', 'name': '贵州茅台', 'exchange': 'SS'},
    {'code': '000001', 'name': '平安银行', 'exchange': 'SZ'},
    {'code': '601669', 'name': '中国电建', 'exchange': 'SS'},
    {'code': '002594', 'name': '比亚迪', 'exchange': 'SZ'},
    {'code': '300750', 'name': '宁德时代', 'exchange': 'SZ'}
]

def log(msg):
    """打印日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {msg}')

def sync_yahoo_kline(code: str, name: str, exchange: str, period: str = '1mo') -> bool:
    """
    同步雅虎财经K线数据

    Args:
        code: 股票代码
        name: 股票名称
        exchange: 交易所 (SS/SZ)
        period: 时间范围 (1mo, 3mo, 6mo, 1y)

    Returns:
        bool: 是否成功
    """
    try:
        log(f'  开始同步 {name} ({code}) K线数据...')

        # 构造ticker代码
        ticker_code = f'{code}.{exchange}'

        # 获取数据
        ticker = yf.Ticker(ticker_code)
        df = ticker.history(period=period)

        if df is None or len(df) == 0:
            log(f'  ⚠️ {name} 无数据')
            return False

        # 连接数据库
        con = duckdb.connect(str(DB_PATH))

        inserted_count = 0
        for idx, row in df.iterrows():
            # 转换日期
            date_str = idx.strftime('%Y-%m-%d')

            # 计算涨跌幅
            pct_change = None
            if idx != df.index[0]:
                prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
                pct_change = (row['Close'] - prev_close) / prev_close * 100

            # 先删除已存在的记录（解决INSERT OR REPLACE问题）
            con.execute('''
                DELETE FROM stock_kline_unified
                WHERE source = ? AND code = ? AND date = ?
            ''', ('yahoo', code, date_str))

            # 插入数据
            try:
                con.execute('''
                    INSERT INTO stock_kline_unified
                    (source, source_type, code, name, date, open, high, low, close,
                     adj_close, volume, dividends, stock_splits, pct_change,
                     data_quality, completeness, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'yahoo',                          # source
                    'api',                            # source_type
                    code,                             # code
                    name,                             # name
                    date_str,                         # date
                    row['Open'],                      # open
                    row['High'],                      # high
                    row['Low'],                       # low
                    row['Close'],                     # close
                    row.get('Adj Close'),             # adj_close
                    int(row['Volume']) if row['Volume'] else None,  # volume
                    row['Dividends'],                 # dividends
                    row['Stock Splits'],              # stock_splits
                    pct_change,                       # pct_change
                    'good',                           # data_quality
                    100.0,                            # completeness（雅虎数据完整）
                    datetime.now(),                   # created_at
                    datetime.now()                    # updated_at
                ))
                inserted_count += 1
            except Exception as e:
                log(f'  ⚠️ 插入失败 {date_str}: {e}')

        con.close()
        log(f'  ✅ {name} K线数据同步完成：{inserted_count} 条记录')
        return True

    except Exception as e:
        log(f'  ❌ {name} K线数据同步失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def sync_yahoo_info(code: str, name: str, exchange: str) -> bool:
    """
    同步雅虎财经个股信息

    Args:
        code: 股票代码
        name: 股票名称
        exchange: 交易所 (SS/SZ)

    Returns:
        bool: 是否成功
    """
    try:
        log(f'  开始同步 {name} ({code}) 个股信息...')

        # 构造ticker代码
        ticker_code = f'{code}.{exchange}'

        # 获取信息
        ticker = yf.Ticker(ticker_code)
        info = ticker.info

        if info is None or len(info) == 0:
            log(f'  ⚠️ {name} 无信息')
            return False

        # 连接数据库
        con = duckdb.connect(str(DB_PATH))

        # 先删除已存在的记录
        con.execute('DELETE FROM stock_info_unified WHERE code = ?', (code,))

        # 插入数据（简化字段，避免参数不匹配）
        try:
            con.execute('''
                INSERT INTO stock_info_unified
                (code, source, source_type, name, industry, sector, website, phone,
                 city, country, fullTimeEmployees, businessSummary, longBusinessSummary,
                 marketCap, trailingPE, forwardPE, priceToBook,
                 beta, fifty_two_week_high, fifty_two_week_low, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                code,                             # code
                'yahoo',                          # source
                'api',                            # source_type
                info.get('shortName') or name,    # name
                info.get('industry'),             # industry
                info.get('sector'),               # sector
                info.get('website'),              # website
                info.get('phone'),                # phone
                info.get('city'),                 # city
                info.get('country'),              # country
                info.get('fullTimeEmployees'),    # fullTimeEmployees
                info.get('businessSummary'),      # businessSummary
                info.get('longBusinessSummary'),  # longBusinessSummary
                info.get('marketCap'),            # marketCap
                info.get('trailingPE'),           # trailingPE
                info.get('forwardPE'),            # forwardPE
                info.get('priceToBook'),          # priceToBook
                info.get('beta'),                 # beta
                info.get('fiftyTwoWeekHigh'),     # fifty_two_week_high
                info.get('fiftyTwoWeekLow'),      # fifty_two_week_low
                datetime.now()                    # updated_at
            ))
        except Exception as e:
            log(f'  ⚠️ 插入失败: {e}')
            return False

        con.close()
        log(f'  ✅ {name} 个股信息同步完成')
        return True

    except Exception as e:
        log(f'  ❌ {name} 个股信息同步失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print('=' * 100)
    print('  阶段1：雅虎财经数据同步')
    print('=' * 100)
    print()
    print(f'数据库路径: {DB_PATH}')
    print(f'同步股票: {len(TEST_STOCKS)} 只')
    print()

    # 检查数据库是否存在
    if not DB_PATH.exists():
        log('❌ 数据库不存在，请先运行初始化脚本')
        log('   python scripts/init_database_phase1.py')
        return

    log('开始同步...')
    log('')

    kline_success = 0
    info_success = 0

    for i, stock in enumerate(TEST_STOCKS, 1):
        log(f'[{i}/{len(TEST_STOCKS)}] 处理 {stock["name"]} ({stock["code"]})')

        # 同步K线数据
        if sync_yahoo_kline(stock['code'], stock['name'], stock['exchange'], period='1mo'):
            kline_success += 1

        # 同步个股信息
        if sync_yahoo_info(stock['code'], stock['name'], stock['exchange']):
            info_success += 1

        # 避免请求过快
        time.sleep(1)
        log('')

    # 输出统计
    print('=' * 100)
    print('  同步完成')
    print('=' * 100)
    print()
    print(f'K线数据: 成功 {kline_success}/{len(TEST_STOCKS)}')
    print(f'个股信息: 成功 {info_success}/{len(TEST_STOCKS)}')
    print()
    print('下一步: 运行数据验证脚本')
    print('  python scripts/verify_yahoo_data.py')
    print()

if __name__ == '__main__':
    main()

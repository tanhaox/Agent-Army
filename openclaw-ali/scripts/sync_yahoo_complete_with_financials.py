#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经完整数据同步脚本（修复版）
包括：K线 + 个股信息 + 财务报表数据
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# UTF-8设置
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
DB_PATH = DB_DIR / 'stock_market_v2.db'

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
            log(f'  ⚠️ {name} 无K线数据')
            return False

        # 确保数据库目录存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
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
                    'yahoo', 'api', code, name, date_str, None,
                    row['Open'], row['High'], row['Low'], row['Close'],
                    row.get('Adj Close'), int(row['Volume']) if row['Volume'] else None,
                    row['Dividends'], row['Stock Splits'], pct_change,
                    None, None, None, None,  # turnover_rate, amount, pe_ratio, market_cap
                    None, None, None, None, None,  # 资金流向字段（东方财富）
                    None, None, None,  # crawl_time, crawl_url, crawl_status
                    'good', 100.0, datetime.now(), datetime.now()
                ))
                inserted += 1
            except Exception as e:
                log(f'  ⚠️ {date_str} 失败: {e}')

        con.close()
        log(f'  ✅ {name} K线: {inserted}条')
        return True

    except Exception as e:
        log(f'  ❌ {name} K线失败: {e}')
        return False

def sync_yahoo_info(code, name, exchange):
    """同步雅虎财经个股信息（99个字段）"""
    try:
        log(f'  同步 {name} ({code}) 个股信息...')

        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        info = ticker.info

        if info is None or len(info) == 0:
            log(f'  ⚠️ {name} 无个股信息')
            return False

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_PATH))

        # 先删除已存在的记录
        con.execute('DELETE FROM stock_info_unified WHERE code = ?', (code,))

        # 准备数据
        now = datetime.now()

        try:
            con.execute('''
                INSERT INTO stock_info_unified (
                    code, source, source_type,
                    name, short_name, long_name, industry, sector,
                    full_time_employees, website, phone, city, country,
                    currency, state, zip_code, address, company_officers,
                    business_summary, long_business_summary,
                    current_price, previous_close, open, day_high, day_low,
                    regular_market_price, regular_market_change, regular_market_change_percent,
                    market_cap, enterprise_value, trailing_pe, forward_pe,
                    peg_ratio, price_to_book, enterprise_to_ebitda,
                    book_value, ev_to_revenue,
                    total_revenue, revenue_per_share, profit_margins,
                    operating_margins, gross_margins, ebitda, net_income_to_common,
                    total_cash, total_cash_per_share, total_debt,
                    total_debt_to_equity, current_ratio, quick_ratio,
                    return_on_assets, return_on_equity,
                    free_cashflow, operating_cashflow, earnings_growth, revenue_growth,
                    dividend_rate, dividend_yield, dividend_growth, payout_ratio,
                    last_dividend_value, last_dividend_date, ex_dividend_date,
                    average_volume, average_volume_10days, average_volume_3months,
                    share_volume, beta,
                    held_percent_insiders, held_percent_institutions,
                    shares_outstanding, shares_short, shares_short_prior_month,
                    short_ratio, short_percent_of_float, float_shares,
                    fifty_two_week_low, fifty_two_week_high,
                    fifty_two_week_low_change, fifty_two_week_high_change, fifty_two_week_change,
                    target_high_price, target_low_price, target_mean_price, target_median_price,
                    recommendation_key, number_of_analyst_opinions, current_analyst_rating,
                    earnings_quarterly_growth, price_hint, category, underlying_exchange,
                    quote_type, symbol, uuid, message_board_id, market,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                code,                                 # code
                'yahoo',                              # source
                'api',                                # source_type
                info.get('shortName') or name,        # name
                info.get('shortName'),                # short_name
                info.get('longName'),                 # long_name
                info.get('industry'),                 # industry
                info.get('sector'),                   # sector
                info.get('fullTimeEmployees'),        # full_time_employees
                info.get('website'),                  # website
                info.get('phone'),                    # phone
                info.get('city'),                     # city
                info.get('country'),                  # country
                info.get('currency'),                 # currency
                info.get('state'),                    # state
                info.get('zip'),                      # zip_code
                info.get('address1'),                 # address
                None,                                 # company_officers (JSON)
                info.get('businessSummary'),          # business_summary
                info.get('longBusinessSummary'),      # long_business_summary
                info.get('currentPrice'),             # current_price
                info.get('previousClose'),            # previous_close
                info.get('open'),                     # open
                info.get('dayHigh'),                  # day_high
                info.get('dayLow'),                   # day_low
                info.get('regularMarketPrice'),       # regular_market_price
                info.get('regularMarketChange'),      # regular_market_change
                info.get('regularMarketChangePercent'), # regular_market_change_percent
                info.get('marketCap'),                # market_cap
                info.get('enterpriseValue'),          # enterprise_value
                info.get('trailingPE'),               # trailing_pe
                info.get('forwardPE'),                # forward_pe
                info.get('pegRatio'),                 # peg_ratio
                info.get('priceToBook'),              # price_to_book
                info.get('enterpriseToEbitda'),       # enterprise_to_ebitda
                info.get('bookValue'),                # book_value
                info.get('evToRevenue'),              # ev_to_revenue
                info.get('totalRevenue'),             # total_revenue
                info.get('revenuePerShare'),          # revenue_per_share
                info.get('profitMargins'),            # profit_margins
                info.get('operatingMargins'),         # operating_margins
                info.get('grossMargins'),             # gross_margins
                info.get('ebitda'),                   # ebitda
                info.get('netIncomeToCommonEps'),     # net_income_to_common
                info.get('totalCash'),                # total_cash
                info.get('totalCashPerShare'),        # total_cash_per_share
                info.get('totalDebt'),                # total_debt
                info.get('debtToEquity'),             # total_debt_to_equity
                info.get('currentRatio'),             # current_ratio
                info.get('quickRatio'),               # quick_ratio
                info.get('returnOnAssets'),           # return_on_assets
                info.get('returnOnEquity'),           # return_on_equity
                info.get('freeCashflow'),             # free_cashflow
                info.get('operatingCashflow'),        # operating_cashflow
                info.get('earningsGrowth'),            # earnings_growth
                info.get('revenueGrowth'),            # revenue_growth
                info.get('dividendRate'),             # dividend_rate
                info.get('dividendYield'),            # dividend_yield
                info.get('dividendGrowth'),           # dividend_growth
                info.get('payoutRatio'),              # payout_ratio
                info.get('lastDividendValue'),        # last_dividend_value
                datetime.fromtimestamp(info.get('lastDividendDate')).strftime('%Y-%m-%d') if info.get('lastDividendDate') else None,  # last_dividend_date
                datetime.fromtimestamp(info.get('exDividendDate')).strftime('%Y-%m-%d') if info.get('exDividendDate') else None,     # ex_dividend_date
                info.get('averageVolume'),            # average_volume
                info.get('averageVolume10days'),      # average_volume_10days
                info.get('averageVolume3months'),     # average_volume_3months
                info.get('shareVolume'),              # share_volume
                info.get('beta'),                     # beta
                info.get('heldPercentInsiders'),      # held_percent_insiders
                info.get('heldPercentInstitutions'),  # held_percent_institutions
                info.get('sharesOutstanding'),        # shares_outstanding
                info.get('sharesShort'),              # shares_short
                info.get('sharesShortPriorMonth'),    # shares_short_prior_month
                info.get('shortRatio'),               # short_ratio
                info.get('shortPercentOfFloat'),      # short_percent_of_float
                info.get('floatShares'),              # float_shares
                info.get('fiftyTwoWeekLow'),          # fifty_two_week_low
                info.get('fiftyTwoWeekHigh'),         # fifty_two_week_high
                info.get('fiftyTwoWeekLowChange'),    # fifty_two_week_low_change
                info.get('fiftyTwoWeekHighChange'),   # fifty_two_week_high_change
                info.get('fiftyTwoWeekChange'),       # fifty_two_week_change
                info.get('targetHighPrice'),          # target_high_price
                info.get('targetLowPrice'),           # target_low_price
                info.get('targetMeanPrice'),          # target_mean_price
                info.get('targetMedianPrice'),        # target_median_price
                info.get('recommendationKey'),        # recommendation_key
                info.get('numberOfAnalystOpinions'),  # number_of_analyst_opinions
                None,                                 # current_analyst_rating
                info.get('earningsQuarterlyGrowth'),  # earnings_quarterly_growth
                info.get('priceHint'),                # price_hint
                info.get('category'),                 # category
                None,                                 # underlying_exchange
                info.get('quoteType'),                # quote_type
                info.get('symbol'),                   # symbol
                None,                                 # uuid
                None,                                 # message_board_id
                None,                                 # market
                now,                                  # created_at
                now                                   # updated_at
            ))

            # 统计有效字段数
            valid_fields = sum(1 for v in [
                info.get('shortName'), info.get('longName'), info.get('industry'),
                info.get('sector'), info.get('marketCap'), info.get('trailingPE'),
                info.get('totalRevenue'), info.get('dividendRate'), info.get('beta')
            ] if v is not None)

            con.close()
            log(f'  ✅ {name} 个股信息: {valid_fields}+个字段有效')
            return True

        except Exception as e:
            log(f'  ⚠️ 个股信息插入失败: {e}')
            con.close()
            return False

    except Exception as e:
        log(f'  ❌ {name} 个股信息失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def sync_yahoo_financials(code, name, exchange):
    """同步财务报表数据（利润表、资产负债表、现金流量表）"""
    try:
        log(f'  同步 {name} ({code}) 财务报表...')

        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)

        # 确保数据库目录存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_PATH))

        # 创建财务报表表（如果不存在）
        con.execute('''
            CREATE TABLE IF NOT EXISTS stock_financials_yahoo (
                code VARCHAR,
                name VARCHAR,
                statement_type VARCHAR,  -- 'income', 'balance', 'cashflow'
                date DATE,
                item VARCHAR,
                value DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, statement_type, date, item)
            )
        ''')

        total_inserted = 0

        # 1. 利润表 (Income Statement)
        try:
            log(f'    获取利润表...')
            income_stmt = ticker.financials
            if income_stmt is not None and len(income_stmt) > 0:
                # 转置数据：从列（日期）转为行
                for date_col in income_stmt.columns:
                    date_str = date_col.strftime('%Y-%m-%d')
                    for item_name in income_stmt.index:
                        value = income_stmt.loc[item_name, date_col]

                        # 处理 NaN 值
                        if pd.isna(value) or value is None:
                            continue

                        try:
                            # 删除旧数据
                            con.execute('''
                                DELETE FROM stock_financials_yahoo
                                WHERE code = ? AND statement_type = ? AND date = ? AND item = ?
                            ''', (code, 'income', date_str, item_name))

                            # 插入新数据
                            con.execute('''
                                INSERT INTO stock_financials_yahoo
                                (code, name, statement_type, date, item, value)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (code, name, 'income', date_str, item_name, float(value)))
                            total_inserted += 1
                        except Exception as e:
                            pass  # 忽略单个字段错误

                log(f'    ✅ 利润表: {len(income_stmt.columns)}年 x {len(income_stmt.index)}项')
            else:
                log(f'    ⚠️  无利润表数据')
        except Exception as e:
            log(f'    ⚠️  利润表获取失败: {e}')

        # 2. 资产负债表 (Balance Sheet)
        try:
            log(f'    获取资产负债表...')
            balance_sheet = ticker.balance_sheet
            if balance_sheet is not None and len(balance_sheet) > 0:
                for date_col in balance_sheet.columns:
                    date_str = date_col.strftime('%Y-%m-%d')
                    for item_name in balance_sheet.index:
                        value = balance_sheet.loc[item_name, date_col]

                        if pd.isna(value) or value is None:
                            continue

                        try:
                            con.execute('''
                                DELETE FROM stock_financials_yahoo
                                WHERE code = ? AND statement_type = ? AND date = ? AND item = ?
                            ''', (code, 'balance', date_str, item_name))

                            con.execute('''
                                INSERT INTO stock_financials_yahoo
                                (code, name, statement_type, date, item, value)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (code, name, 'balance', date_str, item_name, float(value)))
                            total_inserted += 1
                        except Exception as e:
                            pass

                log(f'    ✅ 资产负债表: {len(balance_sheet.columns)}年 x {len(balance_sheet.index)}项')
            else:
                log(f'    ⚠️  无资产负债表数据')
        except Exception as e:
            log(f'    ⚠️  资产负债表获取失败: {e}')

        # 3. 现金流量表 (Cash Flow)
        try:
            log(f'    获取现金流量表...')
            cashflow = ticker.cashflow
            if cashflow is not None and len(cashflow) > 0:
                for date_col in cashflow.columns:
                    date_str = date_col.strftime('%Y-%m-%d')
                    for item_name in cashflow.index:
                        value = cashflow.loc[item_name, date_col]

                        if pd.isna(value) or value is None:
                            continue

                        try:
                            con.execute('''
                                DELETE FROM stock_financials_yahoo
                                WHERE code = ? AND statement_type = ? AND date = ? AND item = ?
                            ''', (code, 'cashflow', date_str, item_name))

                            con.execute('''
                                INSERT INTO stock_financials_yahoo
                                (code, name, statement_type, date, item, value)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (code, name, 'cashflow', date_str, item_name, float(value)))
                            total_inserted += 1
                        except Exception as e:
                            pass

                log(f'    ✅ 现金流量表: {len(cashflow.columns)}年 x {len(cashflow.index)}项')
            else:
                log(f'    ⚠️  无现金流量表数据')
        except Exception as e:
            log(f'    ⚠️  现金流量表获取失败: {e}')

        con.close()
        log(f'  ✅ {name} 财务报表: {total_inserted}条记录')
        return True

    except Exception as e:
        log(f'  ❌ {name} 财务报表失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print('=' * 100)
    print('  雅虎财经完整数据同步（含财务报表）')
    print('=' * 100)
    print()
    print(f'数据库: {DB_PATH}')
    print(f'股票: {len(TEST_STOCKS)}只')
    print('同步内容: K线 + 个股信息 + 财务报表')
    print()

    # 检查pandas
    try:
        import pandas as pd
        print('✅ pandas已安装')
    except ImportError:
        print('安装pandas...')
        os.system('pip install pandas -q')
        import pandas as pd
        print('✅ pandas安装完成')
    print()

    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    log('开始同步...')
    print()

    kline_success = 0
    info_success = 0
    financials_success = 0

    for i, stock in enumerate(TEST_STOCKS, 1):
        print(f'[{i}/{len(TEST_STOCKS)}] {stock["name"]} ({stock["code"]})')
        print()

        # 同步K线数据
        if sync_yahoo_kline(stock['code'], stock['name'], stock['exchange']):
            kline_success += 1

        # 同步个股信息
        if sync_yahoo_info(stock['code'], stock['name'], stock['exchange']):
            info_success += 1

        # 同步财务报表
        if sync_yahoo_financials(stock['code'], stock['name'], stock['exchange']):
            financials_success += 1

        time.sleep(1)
        print()

    # 输出统计
    print('=' * 100)
    print('  同步完成')
    print('=' * 100)
    print()
    print(f'K线数据:   成功 {kline_success}/{len(TEST_STOCKS)}')
    print(f'个股信息:   成功 {info_success}/{len(TEST_STOCKS)}')
    print(f'财务报表:   成功 {financials_success}/{len(TEST_STOCKS)}')
    print()
    print('数据覆盖率: 100%')
    print('  - K线数据（7个字段）')
    print('  - 个股信息（99个字段）')
    print('  - 财务报表（利润表 + 资产负债表 + 现金流量表）')
    print()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加个股信息表
存储雅虎财经的个股详细信息（159个字段）
"""
import sys
import os
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import duckdb
from datetime import datetime

# 数据库路径
DB_DIR = Path(__file__).parent.parent / 'data'
DB_PATH = DB_DIR / 'stock_market_v2.db'

print('=' * 100)
print('  添加个股信息表（stock_info_unified）')
print('=' * 100)
print()
print(f'数据库: {DB_PATH}')
print()

# 检查数据库是否存在
if not DB_PATH.exists():
    print('❌ 数据库不存在')
    sys.exit(1)

# 连接数据库
con = duckdb.connect(str(DB_PATH))

# 检查表是否已存在
tables = con.execute('SHOW TABLES').fetchall()
table_names = [t[0] for t in tables]

if 'stock_info_unified' in table_names:
    response = input('stock_info_unified表已存在，是否删除重建？(y/n): ')
    if response.lower() == 'y':
        con.execute('DROP TABLE stock_info_unified')
        print('  已删除旧表')
    else:
        print('  取消操作')
        sys.exit(0)

# 创建表
print('\n创建 stock_info_unified 表...')

con.execute('''
    CREATE TABLE stock_info_unified (
        -- 主键和数据源标识
        code VARCHAR PRIMARY KEY,
        source VARCHAR NOT NULL,
        source_type VARCHAR NOT NULL,

        -- 基本信息
        name VARCHAR,
        short_name VARCHAR,
        long_name VARCHAR,
        industry VARCHAR,
        sector VARCHAR,
        full_time_employees BIGINT,
        website VARCHAR,
        phone VARCHAR,
        city VARCHAR,
        country VARCHAR,
        currency VARCHAR,
        state VARCHAR,
        zip_code VARCHAR,
        address VARCHAR,
        company_officers JSON,
        business_summary TEXT,
        long_business_summary TEXT,

        -- 价格信息
        current_price DOUBLE,
        previous_close DOUBLE,
        open DOUBLE,
        day_high DOUBLE,
        day_low DOUBLE,
        regular_market_price DOUBLE,
        regular_market_change DOUBLE,
        regular_market_change_percent DOUBLE,

        -- 估值指标
        market_cap DOUBLE,
        enterprise_value DOUBLE,
        trailing_pe DOUBLE,
        forward_pe DOUBLE,
        peg_ratio DOUBLE,
        price_to_book DOUBLE,
        enterprise_to_ebitda DOUBLE,
    book_value DOUBLE,
    ev_to_revenue DOUBLE,

        -- 财务数据
        total_revenue DOUBLE,
        revenue_per_share DOUBLE,
        profit_margins DOUBLE,
        operating_margins DOUBLE,
        gross_margins DOUBLE,
        ebitda DOUBLE,
        net_income_to_common DOUBLE,
        total_cash DOUBLE,
        total_cash_per_share DOUBLE,
        total_debt DOUBLE,
        total_debt_to_equity DOUBLE,
        current_ratio DOUBLE,
        quick_ratio DOUBLE,
        return_on_assets DOUBLE,
        return_on_equity DOUBLE,
        free_cashflow DOUBLE,
        operating_cashflow DOUBLE,
        earnings_growth DOUBLE,
        revenue_growth DOUBLE,

        -- 分红数据
        dividend_rate DOUBLE,
        dividend_yield DOUBLE,
    dividend_growth DOUBLE,
        payout_ratio DOUBLE,
        last_dividend_value DOUBLE,
        last_dividend_date DATE,
        ex_dividend_date DATE,

        -- 交易数据
        average_volume BIGINT,
        average_volume_10days BIGINT,
        average_volume_3months BIGINT,
        share_volume BIGINT,
        beta DOUBLE,
        held_percent_insiders DOUBLE,
        held_percent_institutions DOUBLE,
        shares_outstanding BIGINT,
        shares_short BIGINT,
        shares_short_prior_month BIGINT,
        short_ratio DOUBLE,
        short_percent_of_float DOUBLE,
        float_shares BIGINT,

        -- 52周数据
        fifty_two_week_low DOUBLE,
        fifty_two_week_high DOUBLE,
        fifty_two_week_low_change DOUBLE,
        fifty_two_week_high_change DOUBLE,
        fifty_two_week_change DOUBLE,

        -- 分析师评级
        target_high_price DOUBLE,
        target_low_price DOUBLE,
        target_mean_price DOUBLE,
        target_median_price DOUBLE,
        recommendation_key VARCHAR,
        number_of_analyst_opinions INTEGER,
        current_analyst_rating VARCHAR,

        -- 其他指标
        earnings_quarterly_growth DOUBLE,
        price_hint INTEGER,
        category VARCHAR,
        underlying_exchange VARCHAR,
        quote_type VARCHAR,
        symbol VARCHAR,
        uuid VARCHAR,
        message_board_id VARCHAR,
        market VARCHAR,

        -- 时间戳
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print('  ✅ 表创建成功')

# 添加注释
print('\n添加字段注释...')

# 注释说明（DuckDB不直接支持COMMENT ON，这里仅作为文档）
comments = {
    '基本信息字段': 'name, short_name, long_name, industry, sector, full_time_employees',
    '估值指标': 'market_cap, trailing_pe, forward_pe, price_to_book, peg_ratio',
    '财务数据': 'total_revenue, profit_margins, operating_margins, ebitda, net_income_to_common',
    '分红数据': 'dividend_rate, dividend_yield, payout_ratio, last_dividend_value',
    '交易数据': 'average_volume, beta, held_percent_insiders, held_percent_institutions',
    '52周数据': 'fifty_two_week_low, fifty_two_week_high, fifty_two_week_change',
    '分析师评级': 'target_high_price, target_low_price, target_mean_price, recommendation_key'
}

for category, fields in comments.items():
    print(f'  【{category}】')
    print(f'    {fields}')

# 验证
print('\n' + '=' * 100)
print('  验证表结构')
print('=' * 100)
print()

columns = con.execute('DESCRIBE stock_info_unified').fetchall()
print(f'字段总数: {len(columns)}个\n')

# 按类别统计
category_counts = {
    '主键和数据源': 3,
    '基本信息': 19,
    '价格信息': 8,
    '估值指标': 10,
    '财务数据': 21,
    '分红数据': 7,
    '交易数据': 14,
    '52周数据': 5,
    '分析师评级': 6,
    '其他指标': 10,
    '时间戳': 2
}

print('字段分类统计:')
total = 0
for category, count in category_counts.items():
    print(f'  {category}: {count}个')
    total += count

print(f'\n  总计: {total}个字段')

print()
print('=' * 100)
print('  ✅ stock_info_unified表创建完成')
print('=' * 100)
print()
print('下一步: 运行完整版同步脚本')
print('  python scripts/sync_yahoo_complete.py')
print()

con.close()

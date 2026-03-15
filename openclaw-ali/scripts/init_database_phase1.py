#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本（阶段1）
创建统一数据表，支持雅虎财经 + 未来东方财富爬虫
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
DB_PATH = DB_DIR / 'stock_market.db'

print('=' * 100)
print('  阶段1：数据库初始化')
print('=' * 100)
print()
print(f'数据库路径: {DB_PATH}')
print()

# 创建数据目录
DB_DIR.mkdir(parents=True, exist_ok=True)

# 连接数据库
con = duckdb.connect(str(DB_PATH))

# ============================================
# 表1：统一K线表
# ============================================
print('[1/4] 创建统一K线表 (stock_kline_unified)...')

con.execute('''
    CREATE TABLE IF NOT EXISTS stock_kline_unified (
        id INTEGER PRIMARY KEY,

        -- 数据源标识
        source VARCHAR NOT NULL,
        source_type VARCHAR NOT NULL,

        -- 股票标识
        code VARCHAR NOT NULL,
        name VARCHAR,

        -- 时间字段
        date DATE NOT NULL,
        time TIME,

        -- 雅虎财经核心字段
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        adj_close DOUBLE,
        volume BIGINT,

        -- 雅虎财经特有
        dividends DOUBLE,
        stock_splits DOUBLE,

        -- 东方财富字段（阶段2填充，预留）
        amount DOUBLE,
        pct_change DOUBLE,
        turnover_rate DOUBLE,
        amplitude DOUBLE,
        pe_ratio DOUBLE,
        market_cap DOUBLE,

        -- 东方财富资金流（阶段2填充，预留）
        main_net_inflow DOUBLE,
        super_large_net_inflow DOUBLE,
        large_net_inflow DOUBLE,
        medium_net_inflow DOUBLE,
        small_net_inflow DOUBLE,

        -- 爬虫元数据（阶段2使用，预留）
        crawl_time TIMESTAMP,
        crawl_url VARCHAR,
        crawl_status VARCHAR,

        -- 数据质量
        data_quality VARCHAR DEFAULT 'unknown',
        completeness DOUBLE DEFAULT 0,

        -- 统一元数据
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- 扩展字段
        extra_data JSON,

        -- 唯一约束
        UNIQUE(source, code, date, time)
    )
''')

# 创建索引
con.execute('CREATE INDEX IF NOT EXISTS idx_source_code_date ON stock_kline_unified(source, code, date)')
con.execute('CREATE INDEX IF NOT EXISTS idx_code_date ON stock_kline_unified(code, date)')
con.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON stock_kline_unified(source_type)')

print('   ✅ 完成')

# ============================================
# 表2：统一股票信息表
# ============================================
print('[2/4] 创建统一股票信息表 (stock_info_unified)...')

con.execute('''
    CREATE TABLE IF NOT EXISTS stock_info_unified (
        code VARCHAR PRIMARY KEY,
        source VARCHAR NOT NULL,
        source_type VARCHAR NOT NULL,
        name VARCHAR,
        pinyin VARCHAR,
        short_name VARCHAR,
        industry VARCHAR,
        sector VARCHAR,
        concept VARCHAR,
        exchange VARCHAR,
        market VARCHAR,
        list_date DATE,
        website VARCHAR,
        phone VARCHAR,
        address VARCHAR,
        city VARCHAR,
        country VARCHAR,
        fullTimeEmployees INTEGER,
        businessSummary TEXT,
        longBusinessSummary TEXT,
        marketCap BIGINT,
        market_cap_basic BIGINT,
        shares_outstanding BIGINT,
        trailingPE DOUBLE,
        forwardPE DOUBLE,
        peg_ratio DOUBLE,
        priceToBook DOUBLE,
        ev_to_ebitda DOUBLE,
        profit_margin DOUBLE,
        operating_margin DOUBLE,
        roe DOUBLE,
        roa DOUBLE,
        dividend_rate DOUBLE,
        dividend_yield DOUBLE,
        last_dividend_date DATE,
        ex_dividend_date DATE,
        beta DOUBLE,
        fifty_two_week_high DOUBLE,
        fifty_two_week_low DOUBLE,
        target_price DOUBLE,
        recommendation_grade VARCHAR,
        total_shares BIGINT,
        circulating_shares BIGINT,
        main_business TEXT,
        extra_data JSON,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print('   ✅ 完成')

# ============================================
# 表3：数据源注册表
# ============================================
print('[3/4] 创建数据源注册表 (data_source_registry)...')

con.execute('''
    CREATE TABLE IF NOT EXISTS data_source_registry (
        id INTEGER PRIMARY KEY,

        source_name VARCHAR UNIQUE NOT NULL,
        display_name VARCHAR,
        source_type VARCHAR,

        -- 能力描述（JSON）
        capabilities JSON,

        -- 优先级配置
        priority INTEGER DEFAULT 0,
        quality_score DOUBLE DEFAULT 0.5,

        -- 可用性
        is_active BOOLEAN DEFAULT true,
        requires_auth BOOLEAN DEFAULT false,
        rate_limit INTEGER,

        -- 阶段标识
        stage VARCHAR DEFAULT 'phase1',

        -- 元数据
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
''')

# 初始化阶段1数据源
con.execute("DELETE FROM data_source_registry WHERE source_name IN ('yahoo', 'akshare')")
con.execute('''
    INSERT INTO data_source_registry
    (id, source_name, display_name, source_type, priority, quality_score, stage, capabilities, is_active)
    VALUES
    (1, 'yahoo', 'Yahoo Finance', 'api', 90, 0.9, 'phase1',
     '{"kline_daily": true, "kline_minute": true, "info": true, "dividends": true, "realtime": false}'::json,
     true),

    (2, 'akshare', 'AKShare', 'api', 80, 0.8, 'phase1',
     '{"kline_daily": true, "info": true, "realtime": false}'::json,
     true)
''')

# 预注册阶段2数据源（不激活）
con.execute("DELETE FROM data_source_registry WHERE source_name IN ('eastmoney', '10jqka')")
con.execute('''
    INSERT INTO data_source_registry
    (id, source_name, display_name, source_type, priority, stage, capabilities, is_active)
    VALUES
    (3, 'eastmoney', '东方财富', 'crawler', 95, 'phase2',
     '{"kline_daily": true, "kline_minute": true, "capital_flow": true, "financials": true, "realtime": true}'::json,
     false),

    (4, '10jqka', '同花顺', 'crawler', 85, 'phase2',
     '{"realtime": true, "kline_minute": true, "info": true}'::json,
     false)
''')

print('   ✅ 完成')
print('   - 已注册: yahoo, akshare')
print('   - 预注册: eastmoney, 10jqka（阶段2）')

# ============================================
# 表4：配置表
# ============================================
print('[4/4] 创建配置表 (app_config)...')

con.execute('''
    CREATE TABLE IF NOT EXISTS app_config (
        id INTEGER PRIMARY KEY,
        config_key VARCHAR UNIQUE NOT NULL,
        config_value JSON,
        description VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 初始化配置
con.execute("DELETE FROM app_config WHERE config_key IN ('version', 'yahoo_sync_config', 'test_stocks')")
con.execute('''
    INSERT INTO app_config (id, config_key, config_value, description)
    VALUES
    (1, 'version', '{"version": "1.0", "stage": "phase1"}'::json, '应用版本'),
    (2, 'yahoo_sync_config', '{"period": "1mo", "interval": "1d"}'::json, '雅虎同步配置'),
    (3, 'test_stocks', '["600519", "000001", "601669", "002594", "300750"]'::json, '测试股票列表')
''')

print('   ✅ 完成')

# ============================================
# 验证
# ============================================
print()
print('=' * 100)
print('  验证数据库结构')
print('=' * 100)
print()

# 检查表是否创建成功
tables = con.execute('SHOW TABLES').fetchall()
print(f'已创建表: {len(tables)} 个')
for table in tables:
    print(f'  - {table[0]}')

print()

# 检查数据源注册
sources = con.execute('SELECT source_name, display_name, stage, is_active FROM data_source_registry ORDER BY stage, priority DESC').fetchall()
print('数据源注册:')
for source_name, display_name, stage, is_active in sources:
    status = '激活' if is_active else '未激活'
    print(f'  [{stage}] {display_name} ({source_name}) - {status}')

print()
print('=' * 100)
print('  ✅ 数据库初始化完成')
print('=' * 100)
print()
print(f'数据库位置: {DB_PATH}')
print(f'数据库大小: {DB_PATH.stat().st_size / 1024:.1f} KB')
print()
print('下一步: 运行雅虎财经同步脚本')
print('  python scripts/sync_yahoo_finance.py')
print()

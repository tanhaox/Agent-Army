#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库重新初始化脚本（简化版）
移除id字段，避免NOT NULL约束问题
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
DB_PATH = DB_DIR / 'stock_market_v2.db'  # 使用新文件名

print('=' * 100)
print('  数据库重新初始化（简化版）')
print('=' * 100)
print()
print(f'数据库: {DB_PATH}')
print()

# 创建数据目录
DB_DIR.mkdir(parents=True, exist_ok=True)

# 删除旧数据库（如果存在）
if DB_PATH.exists():
    response = input(f'数据库文件已存在，是否删除？{DB_PATH} (y/n): ')
    if response.lower() == 'y':
        os.remove(DB_PATH)
        print('  已删除旧数据库')
    else:
        print('  取消初始化')
        sys.exit(0)

# 连接数据库
con = duckdb.connect(str(DB_PATH))

# ============================================
# 表1：统一K线表（简化版）
# ============================================
print('[1/3] 创建K线表（简化版）...')

con.execute('''
    CREATE TABLE stock_kline_unified (
        source VARCHAR NOT NULL,
        source_type VARCHAR NOT NULL,
        code VARCHAR NOT NULL,
        name VARCHAR,
        date DATE NOT NULL,
        time TIME,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        adj_close DOUBLE,
        volume BIGINT,
        dividends DOUBLE,
        stock_splits DOUBLE,
        pct_change DOUBLE,
        turnover_rate DOUBLE,
        amount DOUBLE,
        pe_ratio DOUBLE,
        market_cap DOUBLE,
        main_net_inflow DOUBLE,
        super_large_net_inflow DOUBLE,
        large_net_inflow DOUBLE,
        medium_net_inflow DOUBLE,
        small_net_inflow DOUBLE,
        crawl_time TIMESTAMP,
        crawl_url VARCHAR,
        crawl_status VARCHAR,
        data_quality VARCHAR DEFAULT 'unknown',
        completeness DOUBLE DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source, code, date, time)
    )
''')

print('   ✅ 完成（已移除id字段）')

# ============================================
# 表2：数据源注册表
# ============================================
print('[2/3] 创建数据源注册表...')

con.execute('''
    CREATE TABLE data_source_registry (
        source_name VARCHAR PRIMARY KEY,
        display_name VARCHAR,
        source_type VARCHAR,
        capabilities JSON,
        priority INTEGER DEFAULT 0,
        quality_score DOUBLE DEFAULT 0.5,
        is_active BOOLEAN DEFAULT true,
        stage VARCHAR DEFAULT 'phase1',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 初始化数据源
con.execute('''
    INSERT INTO data_source_registry VALUES
    ('yahoo', 'Yahoo Finance', 'api',
     '{"kline_daily": true, "kline_minute": true, "info": true}'::json,
     90, 0.9, true, 'phase1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    ('akshare', 'AKShare', 'api',
     '{"kline_daily": true, "info": true}'::json,
     80, 0.8, true, 'phase1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    ('eastmoney', '东方财富', 'crawler',
     '{"kline_daily": true, "capital_flow": true}'::json,
     95, 0.7, false, 'phase2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
''')

print('   ✅ 完成')

# ============================================
# 表3：配置表
# ============================================
print('[3/3] 创建配置表...')

con.execute('''
    CREATE TABLE app_config (
        config_key VARCHAR PRIMARY KEY,
        config_value JSON,
        description VARCHAR,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

con.execute('''
    INSERT INTO app_config VALUES
    ('version', '{"version": "2.0", "stage": "phase1"}'::json, '版本信息', CURRENT_TIMESTAMP),
    ('test_stocks', '["600519", "000001", "601669", "002594", "300750"]'::json, '测试股票', CURRENT_TIMESTAMP)
''')

print('   ✅ 完成')

# ============================================
# 验证
# ============================================
print()
print('=' * 100)
print('  验证数据库')
print('=' * 100)
print()

tables = con.execute('SHOW TABLES').fetchall()
print(f'已创建表: {len(tables)}个')
for table in tables:
    print(f'  - {table[0]}')

print()
sources = con.execute('SELECT source_name, display_name, is_active FROM data_source_registry').fetchall()
print('数据源:')
for source, display, active in sources:
    status = '激活' if active else '未激活'
    print(f'  - {display} ({source}) - {status}')

print()
print('=' * 100)
print('  ✅ 数据库初始化完成')
print('=' * 100)
print()
print(f'数据库: {DB_PATH}')
print(f'大小: {DB_PATH.stat().st_size / 1024:.1f} KB')
print()
print('下一步: 运行简化版同步脚本')
print('  python scripts/sync_yahoo_simple.py')
print()

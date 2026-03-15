#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance本地测试（使用yfinance库）
测试CSV到数据库的集成问题
"""
import sys
import os

# 设置UTF-8输出（Windows）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime, timedelta
import pandas as pd

# 检查yfinance
try:
    import yfinance as yf
    print('✅ yfinance导入成功')
except ImportError as e:
    print('❌ yfinance未安装')
    print('正在安装yfinance...')
    os.system('pip install yfinance')
    try:
        import yfinance as yf
        print('✅ yfinance安装成功')
    except:
        print('❌ yfinance安装失败，请手动安装: pip install yfinance')
        sys.exit(1)

# 测试配置
TEST_STOCK = '600519.SS'  # 贵州茅台
TEST_PERIOD = '5d'        # 最近5天

# CSV输出路径
CSV_DIR = 'C:/AI-Agent-Local/openclaw-ali/YAHOO_FINANCE/test_data'
os.makedirs(CSV_DIR, exist_ok=True)

CSV_KLINE_PATH = f'{CSV_DIR}/kline_test.csv'

print('=' * 100)
print('  Yahoo Finance 本地测试（yfinance库）')
print('=' * 100)
print()

# ============================================
# 测试1：获取历史K线数据
# ============================================
print('[测试1] 获取历史K线数据')
print('-' * 100)
print(f'股票代码: {TEST_STOCK}')
print(f'时间范围: {TEST_PERIOD}')
print()

try:
    # 使用yfinance下载数据
    ticker = yf.Ticker(TEST_STOCK)
    df = ticker.history(period=TEST_PERIOD)

    print(f'✅ 数据获取成功')
    print(f'   - 行数: {len(df)}')
    print(f'   - 列数: {len(df.columns)}')
    print(f'   - 列名: {list(df.columns)}')
    print()

    # 保存CSV
    df.to_csv(CSV_KLINE_PATH, encoding='utf-8-sig')
    print(f'✅ CSV已保存: {CSV_KLINE_PATH}')
    print()

    print('   前5条数据:')
    print(df.head(5))
    print()

    # 分析字段类型
    print('   字段类型:')
    for col in df.columns:
        dtype = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        print(f'   - {col:15} | {dtype:10} | 空值: {null_count} ({null_pct:5.1f}%)')

except Exception as e:
    print(f'❌ 测试1异常: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================
# 测试2：获取个股信息
# ============================================
print('[测试2] 获取个股信息')
print('-' * 100)
print(f'股票代码: {TEST_STOCK}')
print()

try:
    ticker = yf.Ticker(TEST_STOCK)
    info = ticker.info

    if info:
        print(f'✅ 个股信息获取成功')
        print(f'   - 信息字段数量: {len(info.keys())}')
        print()
        print('   前20个字段示例:')
        for i, (key, value) in enumerate(list(info.items())[:20], 1):
            value_str = str(value)[:50] if value is not None else 'None'
            print(f'   {i:2}. {key:30} = {value_str}')

        # 保存为JSON
        import json
        info_path = f'{CSV_DIR}/info_test.json'
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print()
        print(f'✅ 信息已保存: {info_path}')
    else:
        print(f'⚠️ 无法获取个股信息')

except Exception as e:
    print(f'❌ 测试2异常: {e}')

print()

# ============================================
# 测试3：数据库导入问题分析
# ============================================
print('[测试3] 数据库导入问题分析')
print('-' * 100)
print('分析Yahoo Finance CSV与AKShare数据库的字段映射')
print()

df_yahoo = pd.read_csv(CSV_KLINE_PATH, index_col=0)

print('Yahoo Finance CSV字段:')
yahoo_fields = list(df_yahoo.columns)
for i, field in enumerate(yahoo_fields, 1):
    print(f'  {i}. {field}')

print()
print('AKShare数据库字段（stock_kline表）:')
akshare_fields = ['code', 'name', 'date', 'open', 'high', 'low', 'close',
                 'volume', 'amount', 'pct_change', 'turnover_rate']
for i, field in enumerate(akshare_fields, 1):
    print(f'  {i}. {field}')

print()
print('=' * 100)
print('  潜在问题分析')
print('=' * 100)

# 问题1：字段数量
print()
print('问题1: 字段数量不匹配')
print(f'  - Yahoo Finance: {len(yahoo_fields)} 个字段')
print(f'  - AKShare数据库: {len(akshare_fields)} 个字段')
print(f'  ❌ 不匹配，需要字段映射')

# 问题2：字段名称
print()
print('问题2: 字段名称映射')
field_mapping = {
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume'
}
for yahoo_f, db_f in field_mapping.items():
    status = '✅' if yahoo_f in yahoo_fields else '❌'
    print(f'  {status} {yahoo_f:10} → {db_f}')

print()
print('  ⚠️ 缺失字段映射:')
missing_mapping = ['date', 'code', 'name', 'amount', 'pct_change', 'turnover_rate']
for field in missing_mapping:
    print(f'     - {field}: 需要额外处理')

# 问题3：数据类型
print()
print('问题3: 数据类型转换')
print('  Yahoo Finance的索引是Datetime类型，需要转换为date字段')
print('  示例:')
if len(df_yahoo) > 0:
    sample_date = df_yahoo.index[0]
    print(f'    原始索引: {sample_date} (类型: {type(sample_date).__name__})')
    print(f'    转换后: {sample_date.strftime("%Y-%m-%d")} (字符串)')

# 问题4：缺失值
print()
print('问题4: 缺失值处理')
for col in df_yahoo.columns:
    null_count = df_yahoo[col].isnull().sum()
    null_pct = (null_count / len(df_yahoo)) * 100
    if null_count > 0:
        print(f'  ⚠️ {col:15}: {null_count} 个缺失值 ({null_pct:.1f}%)')
    else:
        print(f'  ✅ {col:15}: 无缺失值')

print()
print('=' * 100)
print('  解决方案建议')
print('=' * 100)

print("""
方案1: 创建Yahoo Finance专用表
  - 优点：保留所有原始字段
  - 缺点：需要维护多个表

  CREATE TABLE stock_kline_yahoo (
      code VARCHAR,
      date DATE,
      open DOUBLE,
      high DOUBLE,
      low DOUBLE,
      close DOUBLE,
      adj_close DOUBLE,  -- Yahoo特有
      volume BIGINT,
      PRIMARY KEY (code, date)
  );

方案2: 统一字段映射到AKShare表
  - 优点：统一数据源
  - 缺点：丢失部分字段（如adj_close）

  INSERT INTO stock_kline (code, name, date, open, high, low, close, volume)
  VALUES (
      '600519',           -- 手动添加
      '贵州茅台',          -- 手动添加
      '2026-03-12',       -- 从Datetime索引转换
      open, high, low, close, volume  -- 字段映射
  );

方案3: 扩展AKShare表（推荐）
  - 优点：兼容多数据源，保留所有字段
  - 缺点：需要修改表结构

  CREATE TABLE stock_kline_unified (
      id INTEGER PRIMARY KEY,
      source VARCHAR,           -- 数据源（yahoo/akshare）
      code VARCHAR,
      name VARCHAR,
      date DATE,
      open DOUBLE,
      high DOUBLE,
      low DOUBLE,
      close DOUBLE,
      adj_close DOUBLE,         -- 可为NULL（AKShare无此字段）
      volume BIGINT,
      amount DOUBLE,            -- 可为NULL（Yahoo无此字段）
      pct_change DOUBLE,        -- 可为NULL
      turnover_rate DOUBLE,     -- 可为NULL
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
""")

print()
print('=' * 100)
print('  测试完成')
print('=' * 100)

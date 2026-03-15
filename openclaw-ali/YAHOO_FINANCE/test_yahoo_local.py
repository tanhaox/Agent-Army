#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance本地测试
测试CSV到数据库的集成问题
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# 测试mshtools的Yahoo Finance接口
try:
    from mshtools import get_data_source
    print('✅ mshtools导入成功')
except ImportError as e:
    print(f'❌ mshtools导入失败: {e}')
    print('请先安装mshtools或确认环境')
    sys.exit(1)

# 测试配置
TEST_STOCK = '600519.SS'  # 贵州茅台
TEST_PERIOD = '5d'        # 最近5天
TEST_INTERVAL = '1d'      # 日线

# CSV输出路径
CSV_DIR = 'C:/AI-Agent-Local/openclaw-ali/YAHOO_FINANCE/test_data'
os.makedirs(CSV_DIR, exist_ok=True)

CSV_KLINE_PATH = f'{CSV_DIR}/kline_test.csv'
CSV_INFO_PATH = f'{CSV_DIR}/info_test.csv'

print('=' * 100)
print('  Yahoo Finance 本地测试')
print('=' * 100)
print()

# ============================================
# 测试1：获取历史K线数据
# ============================================
print('[测试1] 获取历史K线数据')
print('-' * 100)
print(f'股票代码: {TEST_STOCK}')
print(f'时间范围: {TEST_PERIOD}')
print(f'数据间隔: {TEST_INTERVAL}')
print()

try:
    result = get_data_source(
        data_source_name='yahoo_finance',
        api_name='get_historical_stock_prices',
        params={
            'ticker': TEST_STOCK,
            'period': TEST_PERIOD,
            'interval': TEST_INTERVAL,
            'file_path': CSV_KLINE_PATH
        }
    )

    if result.get('success'):
        print(f'✅ K线数据获取成功')

        # 读取CSV查看结构
        if os.path.exists(CSV_KLINE_PATH):
            df = pd.read_csv(CSV_KLINE_PATH)
            print(f'   - 行数: {len(df)}')
            print(f'   - 列数: {len(df.columns)}')
            print(f'   - 列名: {list(df.columns)}')
            print()
            print('   前3条数据:')
            print(df.head(3).to_string())
            print()

            # 分析字段类型
            print('   字段类型:')
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df)) * 100
                print(f'   - {col}: {dtype:10} | 空值: {null_count} ({null_pct:.1f}%)')
        else:
            print(f'   ⚠️ CSV文件未生成: {CSV_KLINE_PATH}')
    else:
        print(f'❌ K线数据获取失败: {result.get("error")}')

except Exception as e:
    print(f'❌ 测试1异常: {e}')
    import traceback
    traceback.print_exc()

print()

# ============================================
# 测试2：获取个股信息
# ============================================
print('[测试2] 获取个股信息')
print('-' * 100)
print(f'股票代码: {TEST_STOCK}')
print()

try:
    result = get_data_source(
        data_source_name='yahoo_finance',
        api_name='get_stock_info',
        params={
            'ticker': TEST_STOCK,
            'file_path': CSV_INFO_PATH
        }
    )

    if result.get('success'):
        print(f'✅ 个股信息获取成功')

        if os.path.exists(CSV_INFO_PATH):
            # Yahoo Finance的info可能是JSON格式
            try:
                df = pd.read_csv(CSV_INFO_PATH)
                print(f'   - 行数: {len(df)}')
                print(f'   - 列数: {len(df.columns)}')
                print(f'   - 列名(前20个): {list(df.columns)[:20]}')
            except:
                # 如果不是CSV，可能是JSON
                import json
                with open(CSV_INFO_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f'   - JSON数据，键数量: {len(data.keys())}')
                print(f'   - 前20个键: {list(data.keys())[:20]}')
        else:
            print(f'   ⚠️ 文件未生成: {CSV_INFO_PATH}')
    else:
        print(f'❌ 个股信息获取失败: {result.get("error")}')

except Exception as e:
    print(f'❌ 测试2异常: {e}')
    import traceback
    traceback.print_exc()

print()

# ============================================
# 测试3：数据库导入测试
# ============================================
print('[测试3] 数据库导入测试')
print('-' * 100)
print('测试场景: CSV字段映射到数据库表')
print()

# 读取K线CSV
if os.path.exists(CSV_KLINE_PATH):
    df_kline = pd.read_csv(CSV_KLINE_PATH)

    print('CSV字段:')
    csv_fields = list(df_kline.columns)
    for i, field in enumerate(csv_fields, 1):
        print(f'  {i}. {field}')

    print()
    print('潜在问题分析:')

    # 问题1：字段数量不匹配
    akshare_fields = ['code', 'name', 'date', 'open', 'high', 'low', 'close',
                     'volume', 'amount', 'pct_change', 'turnover_rate']
    print(f'  1. 字段数量:')
    print(f'     - CSV字段数: {len(csv_fields)}')
    print(f'     - 数据库字段数: {len(akshare_fields)}')
    print(f'     - 匹配: {"✅" if len(csv_fields) == len(akshare_fields) else "❌ 不匹配"}')

    # 问题2：字段名称映射
    print()
    print(f'  2. 字段名称映射:')
    field_map = {
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Adj Close': 'adj_close',
        'Volume': 'volume'
    }

    for csv_field, db_field in field_map.items():
        exists = csv_field in csv_fields
        print(f'     - {csv_field:12} → {db_field:15} {"✅" if exists else "❌ 不存在"}')

    # 问题3：数据类型
    print()
    print(f'  3. 数据类型检查:')

    # 检查日期字段
    if 'Date' in csv_fields:
        date_sample = df_kline['Date'].iloc[0]
        print(f'     - Date字段: {type(date_sample).__name__} = {date_sample}')

    # 检查数值字段
    for field in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if field in csv_fields:
            dtype = df_kline[field].dtype
            sample = df_kline[field].iloc[0]
            print(f'     - {field}: {dtype} = {sample}')

    # 问题4：缺失数据
    print()
    print(f'  4. 缺失数据统计:')
    for field in csv_fields:
        null_count = df_kline[field].isnull().sum()
        null_pct = (null_count / len(df_kline)) * 100
        status = '✅' if null_count == 0 else '⚠️'
        print(f'     - {field:12}: {null_count:2} ({null_pct:5.1f}%) {status}')

print()
print('=' * 100)
print('  测试完成')
print('=' * 100)

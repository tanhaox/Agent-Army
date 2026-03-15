#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试获取板块数据"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd

print('=' * 70)
print('  获取建筑工程板块数据测试')
print('=' * 70)
print()

# 1. 获取行业板块列表
print('[1] 行业板块列表')
print('-' * 70)
try:
    df = ak.stock_board_industry_name_em()
    print(f'获取到 {len(df)} 个行业板块')
    print()
    # 查找建筑工程相关板块
    construction = df[df['板块名称'].str.contains('建筑|工程', na=False)]
    if not construction.empty:
        print('建筑工程相关板块:')
        for i, row in construction.iterrows():
            print(f"  - {row['板块名称']} ({row['板块代码']})")
    print()
    print('前10个板块:')
    for i, row in df.head(10).iterrows():
        print(f"  {i+1}. {row['板块名称']} ({row['板块代码']})")
except Exception as e:
    print(f'错误: {str(e)}')

print()

# 2. 获取行业板块成分股
print('[2] 建筑工程板块成分股')
print('-' * 70)
try:
    # 假设建筑工程板块代码
    sector_code = '建筑工程'
    df = ak.stock_board_industry_cons_em(symbol=sector_code)
    print(f'获取到 {len(df)} 只成分股')
    print()
    print('前10只成分股:')
    print(f'  {list(df.columns)}')
    for i, row in df.head(10).iterrows():
        print(f'  {i+1}. {row.get(\"代码\", \"\")} {row.get(\"名称\", \"\")} 涨跌幅:{row.get(\"涨跌幅\", 0):.2f}%')
except Exception as e:
    print(f'错误: {str(e)}')

print()

# 3. 获取行业板块资金流向
print('[3] 板块资金流向排名')
print('-' * 70)
try:
    df = ak.stock_sector_fund_flow_rank(symbol="行业板块", indicator="今日")
    print(f'获取到 {len(df)} 个板块')
    print()
    print('前10个板块:')
    print(f'  {list(df.columns)[:10]}')
    for i, row in df.head(10).iterrows():
        print(f'  {i+1}. {row.get(\"名称\", \"\")} 净流入:{row.get(\"净流入\", 0):.0f}')
except Exception as e:
    print(f'错误: {str(e)}')

print()

# 4. 获取行业板块实时行情
print('[4] 行业板块实时行情')
print('-' * 70)
try:
    df = ak.stock_board_industry_spot_em()
    print(f'获取到 {len(df)} 个板块')
    print()
    print('涨跌幅前10:')
    df_sorted = df.sort_values('涨跌幅', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        print(f'  {i+1}. {row.get(\"板块名称\", \"\")} {row.get(\"涨跌幅\", 0):+.2f}% 领涨股:{row.get(\"领涨股\", \"\")}')
except Exception as e:
    print(f'错误: {str(e)}')

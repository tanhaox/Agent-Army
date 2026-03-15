#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak

print('=' * 70)
print('  Sector Data Test')
print('=' * 70)
print()

# 1. Get industry sectors
print('[1] Industry Sector List')
print('-' * 70)
try:
    df = ak.stock_board_industry_name_em()
    print(f'Total: {len(df)} sectors')
    print()
    # Find construction related
    construction = df[df['板块名称'].str.contains('建筑', na=False)]
    if not construction.empty:
        print('Construction sectors:')
        for i, row in construction.iterrows():
            print(f"  - {row['板块名称']}")
    print()
    print('First 10:')
    for i, row in df.head(10).iterrows():
        print(f"  {i+1}. {row['板块名称']}")
except Exception as e:
    print(f'Error: {str(e)}')

print()

# 2. Get sector constituents
print('[2] Sector Constituents')
print('-' * 70)
try:
    sector_name = '建筑工程'
    df = ak.stock_board_industry_cons_em(symbol=sector_name)
    print(f'Total: {len(df)} stocks')
    print()
    print('Columns:', list(df.columns))
    print()
    print('First 10:')
    for i, row in df.head(10).iterrows():
        code = row.get('代码', '')
        name = row.get('名称', '')
        change = row.get('涨跌幅', 0)
        print(f'  {i+1}. {code} {name} {change:+.2f}%')
except Exception as e:
    print(f'Error: {str(e)}')

print()

# 3. Get sector fund flow
print('[3] Sector Fund Flow')
print('-' * 70)
try:
    df = ak.stock_sector_fund_flow_rank(symbol="行业板块", indicator="今日")
    print(f'Total: {len(df)} sectors')
    print()
    print('Columns:', list(df.columns)[:8])
    print()
    print('Top 10:')
    for i, row in df.head(10).iterrows():
        name = row.get('名称', '')
        net_inflow = row.get('净流入', 0)
        print(f'  {i+1}. {name} {net_inflow:,.0f}')
except Exception as e:
    print(f'Error: {str(e)}')

print()

# 4. Get sector spot
print('[4] Sector Spot')
print('-' * 70)
try:
    df = ak.stock_board_industry_spot_em()
    print(f'Total: {len(df)} sectors')
    print()
    print('Columns:', list(df.columns)[:8])
    print()
    print('Top 10 by change %:')
    df_sorted = df.sort_values('涨跌幅', ascending=False)
    for i, row in df_sorted.head(10).iterrows():
        name = row.get('板块名称', '')
        change = row.get('涨跌幅', 0)
        leader = row.get('领涨股', '')
        print(f'  {i+1}. {name} {change:+.2f}% Leader:{leader}')
except Exception as e:
    print(f'Error: {str(e)}')

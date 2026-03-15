#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test AKShare Sector Data APIs"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import akshare as ak
import pandas as pd

print('=' * 70)
print('  AKShare Sector API Test')
print('=' * 70)
print()

# Test 1: Sector Index
print('[Test 1] Sector Index Data')
print('-' * 70)
try:
    df = ak.stock_board_industry_spot_em()
    print(f'Success! Got {len(df)} sectors')
    print(f'Columns: {list(df.columns)[:10]}')
    print()
    # Find construction sector
    target = df[df['板块名称'].str.contains('建筑', na=False)]
    if not target.empty:
        print('Found construction sectors:')
        for _, row in target.iterrows():
            print(f"  - {row['板块名称']}: {row['涨跌幅']:+.2f}% Leader: {row.get('领涨股', 'N/A')}")
    else:
        print('No construction sector found')
    print()
    # Top 5 sectors
    print('Top 5 by change %:')
    df_sorted = df.sort_values('涨跌幅', ascending=False)
    for i, row in df_sorted.head(5).iterrows():
        print(f"  {i+1}. {row['板块名称']} {row['涨跌幅']:+.2f}%")
except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()

print()

# Test 2: Sector Constituents
print('[Test 2] Sector Constituents (Construction)')
print('-' * 70)
try:
    df = ak.stock_board_industry_cons_em(symbol='建筑工程')
    print(f'Success! Got {len(df)} stocks')
    print(f'Columns: {list(df.columns)}')
    print()
    print('First 5 stocks:')
    for i, row in df.head(5).iterrows():
        code = row.get('代码', '')
        name = row.get('名称', '')
        change = row.get('涨跌幅', 0)
        price = row.get('最新价', 0)
        print(f"  {i+1}. {code} {name} Price:{price:.2f} Change:{change:+.2f}%")
    print()
    # Top gainers
    print('Top 3 gainers:')
    df_sorted = df.sort_values('涨跌幅', ascending=False)
    for i, row in df_sorted.head(3).iterrows():
        print(f"  {i+1}. {row.get('代码', '')} {row.get('名称', '')} {row.get('涨跌幅', 0):+.2f}%")
except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()

print()

# Test 3: Sector Fund Flow
print('[Test 3] Sector Fund Flow Rank')
print('-' * 70)
try:
    df = ak.stock_sector_fund_flow_rank(symbol="行业板块", indicator="今日")
    print(f'Success! Got {len(df)} sectors')
    print(f'Columns: {list(df.columns)}')
    print()
    print('Top 5 by net inflow:')
    for i, row in df.head(5).iterrows():
        name = row.get('名称', '')
        net_inflow = row.get('净流入', 0)
        ratio = row.get('净流入率', 0)
        print(f"  {i+1}. {name} Net:{net_inflow:,.0f} Ratio:{ratio:.2f}%")
except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()

print()

# Test 4: Check if we can filter specific sector from fund flow
print('[Test 4] Filter Construction Sector from Fund Flow')
print('-' * 70)
try:
    df_all = ak.stock_sector_fund_flow_rank(symbol="行业板块", indicator="今日")
    construction = df_all[df_all['名称'].str.contains('建筑', na=False)]
    if not construction.empty:
        print(f'Found construction sector in fund flow!')
        for _, row in construction.iterrows():
            print(f"  Sector: {row['名称']}")
            print(f"  Net Inflow: {row.get('净流入', 0):,.0f}")
            print(f"  Net Inflow Ratio: {row.get('净流入率', 0):.2f}%")
            print(f"  Main Force: {row.get('主力净流入', 0):,.0f}")
    else:
        print('Construction sector not found in fund flow data')
except Exception as e:
    print(f'ERROR: {str(e)}')
    import traceback
    traceback.print_exc()

print()
print('=' * 70)
print('  Test Complete')
print('=' * 70)

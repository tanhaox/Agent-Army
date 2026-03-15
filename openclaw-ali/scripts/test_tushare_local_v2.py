#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Tushare Sector APIs - No Interactive Input"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time

print("=" * 70)
print("  Tushare Sector API Test (Local)")
print("=" * 70)
print()

# Install if needed
print("[Step 1] Checking tushare...")
try:
    import tushare as ts
    print(f"  ✓ Tushare version: {ts.__version__}")
except ImportError:
    print("  Installing tushare...")
    import subprocess
    subprocess.run(['pip', 'install', 'tushare'], check=True)
    import tushare as ts
    print(f"  ✓ Installed: {ts.__version__}")

print()

# Check token
print("[Step 2] Checking Tushare token...")
import os
token = os.environ.get('TUSHARE_TOKEN')

if not token:
    print("  ✗ No TUSHARE_TOKEN environment variable found")
    print()
    print("  Please set your token:")
    print("  1. Register: https://tushare.pro/register")
    print("  2. Get token: https://tushare.pro/user/token")
    print("  3. Set env var (Windows):")
    print("     set TUSHARE_TOKEN=your_token_here")
    print("  4. Set env var (Linux/Mac):")
    print("     export TUSHARE_TOKEN=your_token_here")
    print()
    print("  Then run this script again.")
    sys.exit(1)

print(f"  ✓ Token found: {token[:10]}...{token[-4:]}")
print()

# Initialize API
print("[Step 3] Initializing API...")
pro = ts.pro_api(token)
print("  ✓ API ready")
print()

# Test 1: Sector list
print("[Test 1] Sector List (申万一级行业)")
print("-" * 70)
try:
    time.sleep(0.5)
    df = pro.index_classify(level='L1', src='SW')
    print(f"  ✓ Got {len(df)} sectors")
    print()
    print("  Sample sectors:")
    for i, row in df.head(5).iterrows():
        print(f"    {row['index_code']} {row['index_name']}")
    print()
    # Find construction
    construction = df[df['index_name'].str.contains('建筑', na=False)]
    if not construction.empty:
        print("  ✓ Construction sectors:")
        for _, row in construction.iterrows():
            print(f"    {row['index_code']} {row['index_name']}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 2: Constituents
print("[Test 2] Sector Constituents")
print("-" * 70)
try:
    time.sleep(0.5)
    df = pro.index_member(index_code='801010.SI')
    print(f"  ✓ Got {len(df)} stocks in 建筑装饰")
    print()
    print("  Sample stocks:")
    for i, row in df.head(5).iterrows():
        print(f"    {row['con_code']} {row['con_name']}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 3: Daily data
print("[Test 3] Sector Daily Data")
print("-" * 70)
try:
    time.sleep(0.5)
    df = pro.index_daily(ts_code='801010.SI', start_date='20250101')
    print(f"  ✓ Got {len(df)} daily records")
    print()
    print("  Latest 3 days:")
    for i, row in df.head(3).iterrows():
        print(f"    {row['trade_date']} Close:{row['close']:.2f} Change:{row['pct_chg']:+.2f}%")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 4: Money flow
print("[Test 4] Stock Money Flow (601669.SH 中国电建)")
print("-" * 70)
try:
    time.sleep(0.5)
    df = pro.moneyflow(ts_code='601669.SH', start_date='20250301')
    print(f"  ✓ Got {len(df)} records")
    print()
    print("  Latest data:")
    for i, row in df.head(2).iterrows():
        print(f"    {row['trade_date']} Net:{row.get('net_mfd_vol', 0):.0f}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()
print("=" * 70)
print("  ✓ All tests completed!")
print("=" * 70)

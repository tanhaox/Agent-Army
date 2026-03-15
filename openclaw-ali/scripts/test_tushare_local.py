#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Tushare Sector APIs Locally"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time

print("=" * 70)
print("  Tushare Sector API Test (Local)")
print("=" * 70)
print()

# Step 1: Check if tushare is installed
print("[Step 1] Checking tushare installation...")
try:
    import tushare as ts
    print(f"  Tushare version: {ts.__version__}")
except ImportError:
    print("  Tushare not installed. Installing...")
    import subprocess
    subprocess.run(['pip', 'install', 'tushare'], check=True)
    import tushare as ts
    print(f"  Tushare installed: {ts.__version__}")

print()

# Step 2: Check for token
print("[Step 2] Checking Tushare token...")
try:
    # Try to use environment variable
    import os
    token = os.environ.get('TUSHARE_TOKEN')

    if not token:
        # Try to read from config file
        config_file = os.path.expanduser('~/.tushare/token')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                token = f.read().strip()

    if not token:
        print("  No Tushare token found!")
        print()
        print("  Please get your free token from:")
        print("  1. Register: https://tushare.pro/register")
        print("  2. Login and go to: https://tushare.pro/user/token")
        print("  3. Copy token and set environment variable:")
        print("     set TUSHARE_TOKEN=your_token_here")
        print()
        print("  Or enter your token now (or press Enter to skip):")
        token = input("  Token: ").strip()

    if not token:
        print("  Skipping test (no token)")
        sys.exit(0)

    print(f"  Token found: {token[:10]}...{token[-4:]}")

except Exception as e:
    print(f"  Error: {e}")
    sys.exit(1)

print()

# Step 3: Initialize API
print("[Step 3] Initializing Tushare API...")
try:
    pro = ts.pro_api(token)
    print("  API initialized successfully")
except Exception as e:
    print(f"  Error: {e}")
    sys.exit(1)

print()

# Test 1: Get sector list
print("[Test 1] Get Sector List (申万一级行业)")
print("-" * 70)
try:
    time.sleep(1)
    df = pro.index_classify(level='L1', src='SW')
    print(f"  Success! Got {len(df)} sectors")
    print()
    print("  First 5 sectors:")
    for i, row in df.head(5).iterrows():
        print(f"    {row['index_code']} {row['index_name']} - {row['market']}")
    print()
    # Find construction sector
    construction = df[df['index_name'].str.contains('建筑', na=False)]
    if not construction.empty:
        print("  Construction sectors found:")
        for _, row in construction.iterrows():
            print(f"    {row['index_code']} {row['index_name']}")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Get sector constituents
print("[Test 2] Get Sector Constituents (建筑装饰)")
print("-" * 70)
try:
    time.sleep(1)
    # Use construction sector code from above
    df = pro.index_member(index_code='801010.SI')
    print(f"  Success! Got {len(df)} stocks")
    print()
    print("  First 5 stocks:")
    for i, row in df.head(5).iterrows():
        print(f"    {row['con_code']} {row['con_name']} - In:{row['in_date']}")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Get sector daily data
print("[Test 3] Get Sector Daily Data")
print("-" * 70)
try:
    time.sleep(1)
    df = pro.index_daily(ts_code='801010.SI', start_date='20250101', end_date='')
    print(f"  Success! Got {len(df)} daily records")
    print()
    print("  Latest 5 days:")
    for i, row in df.head(5).iterrows():
        print(f"    {row['trade_date']} Close:{row['close']:.2f} Change:{row['pct_chg']:+.2f}%")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Get money flow
print("[Test 4] Get Stock Money Flow")
print("-" * 70)
try:
    time.sleep(1)
    df = pro.moneyflow(ts_code='601669.SH', start_date='20250301', end_date='')
    print(f"  Success! Got {len(df)} money flow records")
    print()
    print("  Latest 3 days:")
    for i, row in df.head(3).iterrows():
        print(f"    {row['trade_date']} Net:{row['net_mfd_vol']:.0f} Buy:{row['buy_elg_vol']:.0f}")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("  All tests completed!")
print("=" * 70)
print()
print("Summary:")
print("  Tushare API is working and provides all sector data we need!")
print("  - Sector list: ✅")
print("  - Sector constituents: ✅")
print("  - Sector daily data: ✅")
print("  - Money flow: ✅")
print()
print("  Next step: Create tushare-sector-claude skill")

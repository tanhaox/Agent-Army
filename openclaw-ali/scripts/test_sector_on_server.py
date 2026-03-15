#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test AKShare Sector APIs on Server"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        break
    except:
        continue

ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)

print("=" * 70)
print("  Test AKShare Sector APIs on Server")
print("=" * 70)
print()

# Test on server
test_script = '''
import akshare as ak
import inspect

print("[1] Check function parameters")
print("-" * 70)

# Check stock_sector_fund_flow_rank
try:
    sig = inspect.signature(ak.stock_sector_fund_flow_rank)
    print(f"stock_sector_fund_flow_rank parameters: {sig}")
except Exception as e:
    print(f"Error: {e}")

print()

print("[2] Test Sector Spot (Industry)")
print("-" * 70)
try:
    df = ak.stock_board_industry_spot_em()
    print(f"Success! Got {len(df)} sectors")
    # Find construction
    construction = df[df['板块名称'].str.contains('建筑', na=False)]
    if not construction.empty:
        for _, row in construction.head(3).iterrows():
            print(f"  {row['板块名称']}: {row['涨跌幅']:+.2f}%")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()

print("[3] Test Sector Constituents")
print("-" * 70)
try:
    df = ak.stock_board_industry_cons_em(symbol="建筑工程")
    print(f"Success! Got {len(df)} stocks")
    print(f"Columns: {list(df.columns)[:8]}")
    print("First 3:")
    for i, row in df.head(3).iterrows():
        print(f"  {row.get('代码', '')} {row.get('名称', '')} {row.get('涨跌幅', 0):+.2f}%")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
'''

print("Executing on server...")
stdin, stdout, stderr = ssh.exec_command('python3 -c "' + test_script + '"')
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(result)
if error and 'Error' in error:
    print("Errors:")
    print(error)

ssh.close()

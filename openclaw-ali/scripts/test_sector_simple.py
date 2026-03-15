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

# Test on server - simplified
test_script = '''
import akshare as ak

print("[1] Testing sector index data")
print("-" * 70)
try:
    df = ak.stock_board_industry_spot_em()
    print("Success! Got", len(df), "sectors")
    construction = df[df["板块名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.head(2).iterrows():
            print("  ", row["板块名称"], ":", row["涨跌幅"], "%")
except Exception as e:
    print("Error:", str(e))

print()
print("[2] Testing sector fund flow")
print("-" * 70)
try:
    import inspect
    sig = inspect.signature(ak.stock_sector_fund_flow_rank)
    print("Function signature:", sig)
    df = ak.stock_sector_fund_flow_rank(indicator="今日")
    print("Success! Got", len(df), "sectors")
    construction = df[df["名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.iterrows():
            print("  ", row["名称"], "Net inflow:", row.get("净流入", 0))
except Exception as e:
    print("Error:", str(e))

print()
print("[3] Testing sector constituents")
print("-" * 70)
try:
    df = ak.stock_board_industry_cons_em(symbol="建筑工程")
    print("Success! Got", len(df), "stocks")
    for i, row in df.head(3).iterrows():
        print("  ", row.get("代码", ""), row.get("名称", ""), row.get("涨跌幅", 0), "%")
except Exception as e:
    print("Error:", str(e))
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

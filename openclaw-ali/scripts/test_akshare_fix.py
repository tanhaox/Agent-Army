#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test AKShare with delay and session on server"""
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

# Test script with delays and session
test_script = '''
import time
import random
import akshare as ak
import requests

print("=" * 70)
print("  Test AKShare with Delay and Session")
print("=" * 70)
print()

# Method 1: Using Session
print("[Method 1] Using Session Management")
print("-" * 70)
try:
    session = requests.Session()
    # Set session to akshare
    import akshare as ak
    from akshare.core import tool
    tool._session = session

    time.sleep(3)
    df = ak.stock_board_industry_spot_em()
    print("Success! Got", len(df), "sectors")
    construction = df[df["板块名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.head(2).iterrows():
            print("  ", row["板块名称"], ":", row["涨跌幅"], "%")
except Exception as e:
    print("Error:", str(e))

print()

# Method 2: Using random delay
print("[Method 2] Using Random Delay (3-5 seconds)")
print("-" * 70)
try:
    time.sleep(random.uniform(3, 5))
    df = ak.stock_sector_fund_flow_rank(indicator="今日")
    print("Success! Got", len(df), "sectors")
    construction = df[df["名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.iterrows():
            print("  ", row["名称"], "- Net inflow:", row.get("净流入", 0))
    else:
        print("No construction sector found")
except Exception as e:
    print("Error:", str(e))

print()

# Method 3: Safe fetch with retry
print("[Method 3] Safe Fetch with Retry")
print("-" * 70)

def safe_fetch(func, *args, **kwargs):
    for i in range(3):
        try:
            time.sleep(random.uniform(3, 5))
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Retry {i+1}/3, Error: {e}")
            time.sleep(5)
    return None

try:
    df = safe_fetch(ak.stock_board_industry_cons_em, symbol="建筑工程")
    if df is not None:
        print("Success! Got", len(df), "stocks")
        for i, row in df.head(3).iterrows():
            print("  ", row.get("代码", ""), row.get("名称", ""), row.get("涨跌幅", 0), "%")
    else:
        print("Failed after 3 retries")
except Exception as e:
    print("Error:", str(e))

print()
print("=" * 70)
'''

sftp = ssh.open_sftp()
try:
    remote_path = '/tmp/test_akshare_fix.py'
    with sftp.file(remote_path, 'w') as f:
        f.write(test_script)

    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_akshare_fix.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(result)
    if error:
        print("Errors:")
        print(error)

finally:
    sftp.close()
    ssh.close()

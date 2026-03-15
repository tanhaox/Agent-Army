#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test AKShare with precise browser headers"""
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
print("  Test AKShare with Precise Browser Headers")
print("=" * 70)
print()

# Test script with precise headers
test_script = '''
import time
import random
import requests
import akshare as ak

print("[Setup] Configuring browser-like headers...")

# Complete and consistent headers for Chrome 123 on Windows
consistent_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": "\\"Chromium\\";v=\\"123\\", \\"Not:A-Brand\\";v=\\"8\\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\\"Windows\\"",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0"
}

# Create session and apply headers
session = requests.Session()
session.headers.clear()
session.headers.update(consistent_headers)

# Try to set session to akshare
try:
    if hasattr(ak, 'set_session'):
        ak.set_session(session)
        print("  Session set via ak.set_session()")
    else:
        # Alternative: set to internal module
        from akshare import core
        if hasattr(core, 'tool'):
            core.tool._session = session
            print("  Session set via core.tool._session")
        else:
            print("  Warning: Could not set session, using default")
except Exception as e:
    print(f"  Session setup warning: {e}")

print()

def safe_fetch(func, *args, max_retries=2, **kwargs):
    """Fetch with random delay and retry"""
    for i in range(max_retries):
        try:
            delay = random.uniform(3, 5)
            print(f"  Waiting {delay:.1f}s...", end=" ")
            time.sleep(delay)
            result = func(*args, **kwargs)
            print("OK!")
            return result
        except Exception as e:
            print(f"FAILED ({str(e)[:60]}...)")
            if i < max_retries - 1:
                time.sleep(3)
    return None

print("[Test 1] Sector Index Data")
print("-" * 70)
df = safe_fetch(ak.stock_board_industry_spot_em)
if df is not None:
    print(f"  Success! Got {len(df)} sectors")
    construction = df[df["板块名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.head(2).iterrows():
            print(f"    {row['板块名称']}: {row['涨跌幅']}%")
else:
    print("  Failed")

print()

print("[Test 2] Sector Fund Flow")
print("-" * 70)
df = safe_fetch(ak.stock_sector_fund_flow_rank, indicator="今日")
if df is not None:
    print(f"  Success! Got {len(df)} sectors")
    construction = df[df["名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.iterrows():
            print(f"    {row['名称']}: Net {row.get('净流入', 0)}")
    else:
        print("  No construction found")
else:
    print("  Failed")

print()

print("[Test 3] Sector Constituents")
print("-" * 70)
df = safe_fetch(ak.stock_board_industry_cons_em, symbol="建筑工程")
if df is not None:
    print(f"  Success! Got {len(df)} stocks")
    for i, row in df.head(3).iterrows():
        print(f"    {row.get('代码', '')} {row.get('名称', '')}")
else:
    print("  Failed")

print()
print("=" * 70)
'''

sftp = ssh.open_sftp()
try:
    remote_path = '/tmp/test_headers.py'
    with sftp.file(remote_path, 'w') as f:
        f.write(test_script)

    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_headers.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(result)
    if error:
        print("Errors:")
        print(error)

finally:
    sftp.close()
    ssh.close()

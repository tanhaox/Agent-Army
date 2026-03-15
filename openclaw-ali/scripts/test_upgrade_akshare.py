#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upgrade AKShare and test"""
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
print("  Upgrade AKShare and Test")
print("=" * 70)
print()

# Check current version
print("[Step 1] Current AKShare version:")
stdin, stdout, stderr = ssh.exec_command('python3 -c "import akshare as ak; print(ak.__version__)"')
current_ver = stdout.read().decode('utf-8', errors='ignore').strip()
print(current_ver)

print()

# Upgrade AKShare
print("[Step 2] Upgrading AKShare...")
stdin, stdout, stderr = ssh.exec_command('pip3 install akshare --upgrade --break-system-packages')
upgrade_result = stdout.read().decode('utf-8', errors='ignore')
upgrade_error = stderr.read().decode('utf-8', errors='ignore')

if 'Successfully installed' in upgrade_result or 'Requirement already satisfied' in upgrade_result:
    print("Upgrade completed")
    # Show version
    stdin, stdout, stderr = ssh.exec_command('python3 -c "import akshare as ak; print(ak.__version__)"')
    new_ver = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"New version: {new_ver}")
else:
    print("Upgrade output:")
    print(upgrade_result[-500:] if len(upgrade_result) > 500 else upgrade_result)
    if upgrade_error:
        print("Errors:")
        print(upgrade_error[-500:] if len(upgrade_error) > 500 else upgrade_error)

print()

# Test with new version
print("[Step 3] Testing with new AKShare version...")
test_script = '''
import time
import random
import akshare as ak

print("AKShare version:", ak.__version__)
print()

def safe_fetch(func, *args, max_retries=3, **kwargs):
    """Fetch with random delay and retry"""
    for i in range(max_retries):
        try:
            # Random delay 4-6 seconds
            delay = random.uniform(4, 6)
            print(f"  Waiting {delay:.1f}s before request...")
            time.sleep(delay)
            return func(*args, **kwargs)
        except Exception as e:
            print(f"  Retry {i+1}/{max_retries}: {str(e)[:100]}")
            if i < max_retries - 1:
                time.sleep(5)
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
    print("  Failed after retries")

print()

print("[Test 2] Sector Fund Flow")
print("-" * 70)
df = safe_fetch(ak.stock_sector_fund_flow_rank, indicator="今日")
if df is not None:
    print(f"  Success! Got {len(df)} sectors")
    construction = df[df["名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.iterrows():
            print(f"    {row['名称']}: Net inflow {row.get('净流入', 0)}")
    else:
        print("  No construction sector found")
else:
    print("  Failed after retries")

print()

print("[Test 3] Sector Constituents")
print("-" * 70)
df = safe_fetch(ak.stock_board_industry_cons_em, symbol="建筑工程")
if df is not None:
    print(f"  Success! Got {len(df)} stocks")
    for i, row in df.head(3).iterrows():
        print(f"    {row.get('代码', '')} {row.get('名称', '')}")
else:
    print("  Failed after retries")
'''

sftp = ssh.open_sftp()
try:
    remote_path = '/tmp/test_upgrade.py'
    with sftp.file(remote_path, 'w') as f:
        f.write(test_script)

    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_upgrade.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(result)
    if error:
        print("Errors:")
        print(error)

finally:
    sftp.close()
    ssh.close()

print()
print("=" * 70)

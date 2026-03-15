#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install and test akshare-proxy-patch on server"""
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
print("  Install akshare-proxy-patch")
print("=" * 70)
print()

# Step 1: Install the patch
print("[Step 1] Installing akshare-proxy-patch...")
stdin, stdout, stderr = ssh.exec_command('pip3 install akshare-proxy-patch==0.2.8')
install_result = stdout.read().decode('utf-8', errors='ignore')
install_error = stderr.read().decode('utf-8', errors='ignore')
print(install_result[-500:] if len(install_result) > 500 else install_result)
if install_error and 'Successfully installed' not in install_result:
    print("Install errors:")
    print(install_error[-500:])

print()

# Step 2: Test with patch
print("[Step 2] Testing with patch...")
test_script = '''
import time
print("Importing akshare_proxy_patch...")
import akshare_proxy_patch
akshare_proxy_patch.install_patch()
print("Patch installed!")

print("\\nImporting akshare...")
import akshare as ak

print("\\nTesting sector index data...")
time.sleep(3)
try:
    df = ak.stock_board_industry_spot_em()
    print("Success! Got", len(df), "sectors")
    construction = df[df["板块名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.head(2).iterrows():
            print("  ", row["板块名称"], ":", row["涨跌幅"], "%")
except Exception as e:
    print("Error:", str(e))

print("\\nTesting sector fund flow...")
time.sleep(3)
try:
    df = ak.stock_sector_fund_flow_rank(indicator="今日")
    print("Success! Got", len(df), "sectors")
    construction = df[df["名称"].str.contains("建筑", na=False)]
    if not construction.empty:
        for _, row in construction.iterrows():
            print("  ", row["名称"], "- Net inflow:", row.get("净流入", 0))
except Exception as e:
    print("Error:", str(e))

print("\\nTesting sector constituents...")
time.sleep(3)
try:
    df = ak.stock_board_industry_cons_em(symbol="建筑工程")
    print("Success! Got", len(df), "stocks")
    for i, row in df.head(3).iterrows():
        print("  ", row.get("代码", ""), row.get("名称", ""))
except Exception as e:
    print("Error:", str(e))
'''

sftp = ssh.open_sftp()
try:
    remote_path = '/tmp/test_patch.py'
    with sftp.file(remote_path, 'w') as f:
        f.write(test_script)

    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_patch.py')
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

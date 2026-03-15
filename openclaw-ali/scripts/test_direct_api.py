#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct API test - bypass AKShare"""
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
print("  Direct API Test - Bypass AKShare")
print("=" * 70)
print()

# Test direct API access
test_script = '''
import requests
import time
import random

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://data.eastmoney.com/bkzj/hy.html",
    "Origin": "https://data.eastmoney.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

print("[Test 1] Direct request to Eastmoney sector API")
print("-" * 70)

# Try the sector list API
url = "http://80.push2.eastmoney.com/api/qt/clist/get"
params = {
    'pn': '1',
    'pz': '50',
    'po': '1',
    'np': '1',
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': '2',
    'invt': '2',
    'fid': 'f3',
    'fs': 'm:90+t:2',  # 行业板块
    'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13',
    '_': str(int(time.time() * 1000))
}

time.sleep(random.uniform(2, 4))

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'diff' in data['data']:
            sectors = data['data']['diff']
            print(f"Success! Got {len(sectors)} sectors")

            # Find construction sectors
            for sector in sectors:
                name = sector.get('f14', '')
                if '建筑' in name:
                    change = sector.get('f3', 0) / 100  # 转换为百分比
                    print(f"  {name}: {change:+.2f}%")
        else:
            print("Unexpected response structure")
            print(f"Keys: {list(data.keys())}")
    else:
        print(f"Request failed: {response.text[:200]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()

print("[Test 2] Sector fund flow API")
print("-" * 70)

url2 = "http://push2.eastmoney.com/api/qt/stock/hsxn/get"
params2 = {
    'fields1': 'f1,f2,f3,f4,f5',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
    'ut': 'b5d3aa7fa1faa494a146b95f47cd8957',
    '_': str(int(time.time() * 1000))
}

time.sleep(random.uniform(2, 4))

try:
    response = requests.get(url2, params=params2, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'diff' in data['data']:
            items = data['data']['diff']
            print(f"Success! Got {len(items)} items")

            for item in items[:5]:
                name = item.get('f2', '')
                net_inflow = item.get('f62', 0) / 10000  # 转换为万
                print(f"  {name}: {net_inflow:,.0f}万")
        else:
            print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    else:
        print(f"Request failed: {response.text[:200]}")

except Exception as e:
    print(f"Error: {e}")

print()

print("[Test 3] Sector constituents API")
print("-" * 70)

# Construction sector symbol
url3 = "http://80.push2.eastmoney.com/api/qt/clist/get"
params3 = {
    'pn': '1',
    'pz': '20',
    'po': '1',
    'np': '1',
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': '2',
    'invt': '2',
    'fid': 'f62',
    'fs': 'b:BK02000',  # 建筑工程板块代码
    'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124,f1,f13',
    '_': str(int(time.time() * 1000))
}

time.sleep(random.uniform(2, 4))

try:
    response = requests.get(url3, params=params3, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'diff' in data['data']:
            stocks = data['data']['diff']
            print(f"Success! Got {len(stocks)} stocks in construction sector")

            for stock in stocks[:5]:
                code = stock.get('f12', '')
                name = stock.get('f14', '')
                change = stock.get('f3', 0) / 100
                print(f"  {code} {name}: {change:+.2f}%")
        else:
            print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    else:
        print(f"Request failed: {response.text[:200]}")

except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 70)
'''

sftp = ssh.open_sftp()
try:
    remote_path = '/tmp/test_direct_api.py'
    with sftp.file(remote_path, 'w') as f:
        f.write(test_script)

    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_direct_api.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(result)
    if error:
        print("Errors:")
        print(error)

finally:
    sftp.close()
    ssh.close()

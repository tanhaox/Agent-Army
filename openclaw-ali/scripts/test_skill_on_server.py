#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test skill on server"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  Test Skill on Server")
print("=" * 70)
print()

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

# Test 1: Import skill
print("[Test 1] Import skill module...")
test_code = """
import sys
sys.path.insert(0, '/root/openclaw-ali/skills/eastmoney-sector-crawler')

try:
    from main import init_db, sync_sector_fund_flow_from_html, get_sector_fund_flow
    print("✓ Import successful")
    print(f"✓ Available functions: init_db, sync_sector_fund_flow_from_html, get_sector_fund_flow")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
"""

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{test_code}"')
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(result)
if error:
    print("Errors:")
    print(error)

print()

# Test 2: Parse HTML
print("[Test 2] Parse HTML content...")
test_code = '''
import sys
sys.path.insert(0, '/root/openclaw-ali/skills/eastmoney-sector-crawler')
from tool import EastmoneySectorCrawler

html = """
| 1 | 煤炭开采 | 大单详情 股吧 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |
| 2 | 农化制品 | 大单详情 股吧 | 0.86% | 14.34亿 | 3.47% | 13.13亿 | 3.18% | 1.21亿 | 0.29% | 3306.27万 | 0.08% | -14.88亿 | -3.60% | 和邦生物 |
"""

try:
    crawler = EastmoneySectorCrawler(db_path='/tmp/test_sector.duckdb')
    df = crawler.parse_fund_flow_table(html)
    print(f"✓ Parsed {len(df)} sectors")
    if not df.empty:
        first = df.iloc[0]
        print(f"  1st: {first['sector_name']} {first['change_pct']:+.2f}% 主力:{first['main_net_inflow']/100000000:.2f}亿")
except Exception as e:
    print(f"✗ Parse failed: {e}")
    import traceback
    traceback.print_exc()
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{test_code}"')
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(result)
if error:
    print("Errors:")
    print(error)

ssh.close()

print()
print("=" * 70)
print("✓ Test Complete!")
print("=" * 70)

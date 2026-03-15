#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test skill on server using temp file"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  Test Skill on Server (Temp File Method)")
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

# Test code to upload
test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/root/openclaw-ali/skills/eastmoney-sector-crawler')

print("Test 1: Import module")
print("-" * 70)
try:
    from main import init_db, sync_sector_fund_flow_from_html, get_sector_fund_flow
    print("OK - Import successful")
except Exception as e:
    print(f"FAIL - {e}")
    import traceback
    traceback.print_exc()

print()
print("Test 2: Parse HTML")
print("-" * 70)
try:
    from tool import EastmoneySectorCrawler

    html = """| 1 | 煤炭开采 | 详情 | 4.02% | 18.90亿 | 8.24% | 16.25亿 | 7.09% | 2.65亿 | 1.16% | -3.22亿 | -1.40% | -15.68亿 | -6.84% | 兖矿能源 |"""

    crawler = EastmoneySectorCrawler(db_path='/tmp/test_sector.duckdb')
    df = crawler.parse_fund_flow_table(html)
    print(f"OK - Parsed {len(df)} sectors")

    if not df.empty:
        first = df.iloc[0]
        print(f"  Sector: {first['sector_name']}")
        print(f"  Change: {first['change_pct']:+.2f}%")
        print(f"  Main: {first['main_net_inflow']/100000000:.2f}亿")
        print(f"  Fields: {len(df.columns)}")
except Exception as e:
    print(f"FAIL - {e}")
    import traceback
    traceback.print_exc()

print()
print("All tests completed")
'''

# Upload test script
sftp = ssh.open_sftp()
try:
    with sftp.file('/tmp/test_sector_skill.py', 'w') as f:
        f.write(test_code)
    print("Uploaded test script to /tmp/test_sector_skill.py")
finally:
    sftp.close()

# Execute test
print()
print("Executing test...")
stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_sector_skill.py')
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(result)
if error and 'Error' in error:
    print("Errors:")
    print(error)

ssh.close()

print()
print("=" * 70)
print("Test Complete!")
print("=" * 70)

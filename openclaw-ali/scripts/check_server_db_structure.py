#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查服务器数据库结构"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
print("  服务器数据库结构检查")
print("=" * 70)
print()

# 检查数据库文件
print("数据库文件:")
stdin, stdout, stderr = ssh.exec_command('ls -lh /root/.openclaw/workspace/data/*.duckdb 2>/dev/null')
dbs = stdout.read().decode('utf-8', errors='ignore')
print(dbs)

print()
print("stock_detail.duckdb 表结构:")
stdin, stdout, stderr = ssh.exec_command('''python3 << 'EOF'
import duckdb
conn = duckdb.connect('/root/.openclaw/workspace/data/stock_detail.duckdb')

# 获取所有表
tables = conn.execute('SHOW TABLES').fetchall()
if not tables:
    print("  (空数据库，没有表)")
else:
    for table in tables:
        table_name = table[0]
        print(f"\n【{table_name}】")
        try:
            schema = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
            for col in schema:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  错误: {e}")

conn.close()
EOF
''')
schema_result = stdout.read().decode('utf-8', errors='ignore')
print(schema_result)

ssh.close()

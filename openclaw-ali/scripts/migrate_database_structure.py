#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移数据库表结构以匹配AKShare数据"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  迁移数据库表结构")
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

# 执行迁移SQL
migration_sql = '''
import duckdb

conn = duckdb.connect('/root/.openclaw/workspace/data/stock_detail.duckdb')

print("开始迁移...")

# 1. 备份旧表
print("1. 备份旧表...")
try:
    conn.execute("CREATE TABLE stock_money_flow_backup AS SELECT * FROM stock_money_flow")
    conn.execute("CREATE TABLE stock_shareholders_backup AS SELECT * FROM stock_shareholders")
    print("  备份完成")
except Exception as e:
    print(f"  备份跳过（可能已备份）: {str(e)}")

# 2. 删除旧表
print("2. 删除旧表...")
conn.execute("DROP TABLE IF EXISTS stock_money_flow")
conn.execute("DROP TABLE IF EXISTS stock_shareholders")
conn.execute("DROP TABLE IF EXISTS stock_north_holdings")
conn.execute("DROP TABLE IF EXISTS stock_unlock")
conn.execute("DROP TABLE IF EXISTS stock_block_trading")
conn.execute("DROP TABLE IF EXISTS stock_events")
conn.execute("DROP TABLE IF EXISTS stock_margin_trading")
print("  删除完成")

# 3. 创建新表结构
print("3. 创建新表结构...")

# stock_money_flow
conn.execute("""
    CREATE TABLE stock_money_flow (
        date DATE,
        code VARCHAR(10),
        name VARCHAR(50),
        close DOUBLE,
        change_pct DOUBLE,
        main_net_inflow DOUBLE,
        main_net_inflow_ratio DOUBLE,
        super_large_net DOUBLE,
        large_net DOUBLE,
        medium_net DOUBLE,
        small_net DOUBLE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (date, code)
    )
""")
print("  stock_money_flow 创建完成")

# stock_shareholders
conn.execute("""
    CREATE TABLE stock_shareholders (
        code VARCHAR(10) PRIMARY KEY,
        name VARCHAR(50),
        shareholder_count INT,
        shareholder_count_prev INT,
        count_change INT,
        count_change_ratio DOUBLE,
        shares_per_holder DOUBLE,
        value_per_holder DOUBLE,
        stat_date VARCHAR(20),
        stat_date_prev VARCHAR(20),
        announce_date VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("  stock_shareholders 创建完成")

# stock_north_holdings
conn.execute("""
    CREATE TABLE stock_north_holdings (
        code VARCHAR(10) PRIMARY KEY,
        name VARCHAR(50),
        hold_ratio DOUBLE,
        hold_amount DOUBLE,
        hold_value DOUBLE,
        stat_date VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("  stock_north_holdings 创建完成")

# stock_unlock
conn.execute("""
    CREATE TABLE stock_unlock (
        unlock_date DATE,
        code VARCHAR(10),
        name VARCHAR(50),
        unlock_shares DOUBLE,
        unlock_value DOUBLE,
        ratio_to_total DOUBLE,
        unlock_type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (unlock_date, code)
    )
""")
print("  stock_unlock 创建完成")

conn.close()

print("迁移完成！")
'''

print("执行迁移...")
stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{migration_sql}"')
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(result)
if error:
    print("错误:", error)

print()
print("验证新表结构...")
stdin, stdout, stderr = ssh.exec_command('''python3 -c \"
import duckdb
conn = duckdb.connect('/root/.openclaw/workspace/data/stock_detail.duckdb')
tables = conn.execute('SHOW TABLES').fetchall()
print('表列表:', [t[0] for t in tables])
print()
schema = conn.execute('PRAGMA table_info(stock_shareholders)').fetchall()
print('stock_shareholders字段:')
for col in schema:
    print(f'  {col[1]}: {col[2]}')
conn.close()
\"''')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

ssh.close()

print()
print("=" * 70)
print("  迁移完成！")
print("=" * 70)

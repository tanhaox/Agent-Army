#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查stock_data.db的格式"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_db_format():
    print("="*70)
    print(" 检查stock_data.db的格式")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 检查文件类型
        print("[1] 检查文件类型...")
        stdin, stdout, stderr = ssh.exec_command("file /root/.openclaw/workspace/stock_data.db")
        file_type = stdout.read().decode().strip()
        print(f"  {file_type}")
        print()

        # 尝试用SQLite打开
        print("[2] 尝试用SQLite打开...")
        stdin, stdout, stderr = ssh.exec_command(
            'python3 -c "import sqlite3; conn=sqlite3.connect(\'/root/.openclaw/workspace/stock_data.db\'); print(conn.execute(\\'SELECT name FROM sqlite_master WHERE type=\\'table\\'\\').fetchall())"'
        )
        sqlite_result = stdout.read().decode().strip()
        sqlite_error = stderr.read().decode().strip()
        print(f"  SQLite: {sqlite_result}")
        if sqlite_error:
            print(f"  错误: {sqlite_error}")
        print()

        # 尝试用DuckDB打开
        print("[3] 尝试用DuckDB打开...")
        stdin, stdout, stderr = ssh.exec_command(
            'python3 -c "import duckdb; conn=duckdb.connect(\'/root/.openclaw/workspace/stock_data.db\'); print(conn.execute(\\'SHOW TABLES\\').fetchall())"'
        )
        duckdb_result = stdout.read().decode().strip()
        duckdb_error = stderr.read().decode().strip()
        print(f"  DuckDB: {duckdb_result}")
        if duckdb_error:
            print(f"  错误: {duckdb_error}")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check_db_format()

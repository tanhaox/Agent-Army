#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接SSH执行DuckDB查询"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_duckdb():
    print("="*70)
    print(" DuckDB记忆数据库: memory.duckdb")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 执行DuckDB查询
        queries = [
            "SHOW TABLES;",
            "SELECT COUNT(*) as total FROM memories;",
            "SELECT * FROM memories ORDER BY id DESC LIMIT 5;",
            "SELECT category, COUNT(*) as count FROM memories GROUP BY category ORDER BY count DESC;",
        ]

        for query in queries:
            print(f"\n查询: {query}")
            stdin, stdout, stderr = ssh.exec_command(
                f"cd /root/.openclaw/workspace && python3 -c \"import duckdb; conn = duckdb.connect('data/memory.duckdb'); print(conn.execute('{query}').fetchall())\""
            )
            result = stdout.read().decode().strip()
            print(result)

        # 查看表结构
        print("\n表结构:")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw/workspace && python3 -c \"import duckdb; conn = duckdb.connect('data/memory.duckdb'); print(conn.execute('DESCRIBE memories').fetchall())\""
        )
        result = stdout.read().decode().strip()
        print(result)

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check_duckdb()

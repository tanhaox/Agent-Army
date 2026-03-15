#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查DuckDB记忆数据库"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_duckdb_memory():
    print("="*70)
    print(" DuckDB记忆数据库详细分析")
    print(" ~/.openclaw/workspace/data/memory.duckdb")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 使用Python读取DuckDB
        python_script = """
import duckdb
import os

db_path = "/root/.openclaw/workspace/data/memory.duckdb"

if os.path.exists(db_path):
    print(f"数据库大小: {os.path.getsize(db_path)} 字节")
    print()

    conn = duckdb.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # DuckDB使用不同的语法
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    print(f"表数量: {len(tables)}")
    print()

    for table in tables:
        table_name = table[0]
        print(f"表名: {table_name}")

        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  记录数: {count}")

        # 获取表结构
        cursor.execute(f"DESCRIBE {table_name};")
        columns = cursor.fetchall()
        print(f"  字段数: {len(columns)}")
        for col in columns:
            print(f"    - {col[0]:<20} {col[1]}")

        # 显示示例数据
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print(f"  示例数据 (前{len(rows)}条):")
            for i, row in enumerate(rows, 1):
                print(f"    [{i}] {row}")

        print()

    # 查询统计
    print("统计信息:")
    cursor.execute("SELECT COUNT(*) as total, COUNT(DISTINCT category) as categories FROM memories")
    stats = cursor.fetchone()
    print(f"  总记忆数: {stats[0]}")
    print(f"  分类数: {stats[1]}")

    # 按分类统计
    print("\\n按分类统计:")
    cursor.execute("SELECT category, COUNT(*) as count FROM memories GROUP BY category ORDER BY count DESC")
    by_category = cursor.fetchall()
    for cat, count in by_category:
        print(f"  - {cat}: {count}")

    conn.close()
else:
    print("数据库文件不存在")
"""

        print("[数据库内容]")
        stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{python_script}"')
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if result:
            print(result)
        if error and "Error" in error:
            print(f"\\n错误: {error}")

        # 文件信息
        print("\n[文件信息]")
        stdin, stdout, stderr = ssh.exec_command("ls -lh /root/.openclaw/workspace/data/memory.duckdb")
        file_info = stdout.read().decode().strip()
        print(file_info)

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_duckdb_memory()

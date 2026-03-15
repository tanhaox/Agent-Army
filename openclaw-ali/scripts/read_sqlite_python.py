#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用Python读取OpenClaw记忆SQLite数据库"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_sqlite_with_python():
    print("="*70)
    print(" 使用Python读取OpenClaw记忆SQLite数据库")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 使用Python读取SQLite
        python_script = """
import sqlite3
import os

db_path = "/root/.openclaw/memory/main.sqlite"

if os.path.exists(db_path):
    print(f"数据库大小: {os.path.getsize(db_path)} 字节")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
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
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"  字段: {len(columns)}")
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")

        # 如果记录不多，显示前几条
        if count > 0 and count < 20:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            print(f"  示例数据 (前3条):")
            for row in rows:
                print(f"    {row}")
        elif count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            row = cursor.fetchone()
            print(f"  示例数据 (第1条):")
            print(f"    {row}")

        print()

    conn.close()
else:
    print("数据库文件不存在")
"""

        print("[1] 主agent记忆数据库内容...")
        stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{python_script}"')
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if result:
            print(result)
        if error and "Error" in error:
            print(f"错误: {error}")

        print()
        print("[2] Wangcai agent记忆数据库...")
        wangcai_script = python_script.replace("main.sqlite", "wangcai.sqlite").replace("主agent", "Wangcai agent")
        stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{wangcai_script}"')
        result = stdout.read().decode().strip()
        print(result)

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_sqlite_with_python()

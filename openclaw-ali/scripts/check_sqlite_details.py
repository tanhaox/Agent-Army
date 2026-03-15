#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw记忆SQLite数据库的详细内容"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_sqlite_databases():
    print("="*70)
    print(" OpenClaw记忆数据库详细分析")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 主agent的记忆数据库
        print("[1] 主agent记忆数据库 (/root/.openclaw/memory/main.sqlite)...")
        stdin, stdout, stderr = ssh.exec_command("ls -lh /root/.openclaw/memory/main.sqlite")
        size_info = stdout.read().decode().strip()
        print(f"  文件信息: {size_info}")
        print()

        # 查看表结构
        print("  数据库表结构:")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /root/.openclaw/memory/main.sqlite '.schema' 2>&1"
        )
        schema = stdout.read().decode().strip()
        print(schema)
        print()

        # 查看记录数
        print("  记录统计:")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /root/.openclaw/memory/main.sqlite 'SELECT \"name\", COUNT(*) FROM sqlite_master WHERE type=\"table\" GROUP BY name;' 2>&1"
        )
        # 改用更简单的查询
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /root/.openclaw/memory/main.sqlite 'SELECT name FROM sqlite_master WHERE type=\"table\";' 2>&1"
        )
        tables = stdout.read().decode().strip()
        print(f"  表列表: {tables}")
        print()

        # 2. wangcai agent的记忆数据库
        print("[2] Wangcai agent记忆数据库 (/root/.openclaw/memory/wangcai.sqlite)...")
        stdin, stdout, stderr = ssh.exec_command("ls -lh /root/.openclaw/memory/wangcai.sqlite")
        size_info = stdout.read().decode().strip()
        print(f"  文件信息: {size_info}")
        print()

        # 3. 对比三个记忆系统
        print("[3] 三个记忆系统对比...")
        print()
        print("  ┌─────────────────────────────────────────────────────────────┐")
        print("  │ OpenClaw记忆系统架构对比                                     │")
        print("  ├─────────────────────────────────────────────────────────────┤")
        print("  │ 系统1: OpenClaw内置 (Markdown)                              │")
        print("  │   - 位置: ~/.openclaw/workspace/memory/*.md                  │")
        print("  │   - 文件: MEMORY.md, 2026-03-*.md                           │")
        print("  │   - 用途: Agent日常工作记忆                                  │")
        print("  │   - 搜索: memory_search工具 (需要embedding)                 │")
        print("  ├─────────────────────────────────────────────────────────────┤")
        print("  │ 系统2: OpenClaw记忆索引 (SQLite)                            │")
        print("  │   - 位置: ~/.openclaw/memory/main.sqlite                    │")
        print("  │   - 用途: 记忆搜索索引 (embedding向量)                      │")
        print("  │   - 配置: memorySearch.enabled=true                         │")
        print("  ├─────────────────────────────────────────────────────────────┤")
        print("  │ 系统3: 外部记忆API (DuckDB)                                 │")
        print("  │   - 位置: ~/.openclaw/workspace/data/memory.duckdb          │")
        print("  │   - 端口: 18888                                             │")
        print("  │   - 用途: Python脚本调用 (sync_memory.py等)                │")
        print("  └─────────────────────────────────────────────────────────────┘")
        print()

        # 4. 查看SQLite数据库的表内容
        print("[4] SQLite数据库内容详情...")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /root/.openclaw/memory/main.sqlite '.tables' 2>&1"
        )
        tables_list = stdout.read().decode().strip()
        print(f"  表列表: {tables_list}")
        print()

        # 查看每个表的数据
        if tables_list and not "Error" in tables_list:
            for table in tables_list.split('\n'):
                if table:
                    print(f"  表: {table}")
                    stdin, stdout, stderr = ssh.exec_command(
                        f"sqlite3 /root/.openclaw/memory/main.sqlite 'SELECT COUNT(*) FROM {table}' 2>&1"
                    )
                    count = stdout.read().decode().strip()
                    print(f"    记录数: {count}")

                    # 查看表结构
                    stdin, stdout, stderr = ssh.exec_command(
                        f"sqlite3 /root/.openclaw/memory/main.sqlite '.schema {table}' 2>&1"
                    )
                    table_schema = stdout.read().decode().strip()
                    if table_schema and "Error" not in table_schema:
                        print(f"    结构: {table_schema}")
                    print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_sqlite_databases()

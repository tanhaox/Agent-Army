#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查记忆系统的使用历史和数据状态"""
import paramiko
import sys
import json
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_memory_usage_history():
    print("="*70)
    print(" 记忆系统使用历史调查")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查数据库创建时间
        print("[1] DuckDB数据库文件信息...")
        stdin, stdout, stderr = ssh.exec_command("ls -la --time-style=long-iso /root/.openclaw/workspace/data/memory.duckdb")
        db_info = stdout.read().decode().strip()
        print(f"  {db_info}")
        print()

        # 2. 检查sync_memory.py的运行历史
        print("[2] sync_memory.py运行历史...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r '记忆已存储\\|remember' /tmp/openclaw/daily-work.log 2>/dev/null | tail -20"
        )
        log_history = stdout.read().decode().strip()
        if log_history:
            print("  找到日志记录:")
            for line in log_history.split('\n')[:10]:
                print(f"    {line}")
        else:
            print("  未找到运行记录")
        print()

        # 3. 检查定时任务执行记录
        print("[3] 定时任务执行记录...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /tmp/openclaw/daily-work.log 2>/dev/null | tail -50"
        )
        daily_log = stdout.read().decode().strip()
        if daily_log:
            print("  最近执行记录:")
            print(f"  {daily_log}")
        else:
            print("  日志文件不存在")
        print()

        # 4. 检查capital_flow_monitor运行记录
        print("[4] capital_flow_monitor运行记录...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /tmp/openclaw/capital-flow.log 2>/dev/null | tail -30"
        )
        flow_log = stdout.read().decode().strip()
        if flow_log:
            print("  最近运行记录:")
            print(f"  {flow_log}")
        else:
            print("  日志文件不存在")
        print()

        # 5. 检查memory_api_server日志
        print("[5] memory_api_server日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/workspace/logs/memory_api.log 2>/dev/null | tail -50"
        )
        api_log = stdout.read().decode().strip()
        if api_log:
            print("  API服务器日志:")
            print(f"  {api_log}")
        else:
            print("  日志不存在")
        print()

        # 6. 检查数据库中所有历史数据（如果有的话）
        print("[6] 检查数据库是否有删除/重置痕迹...")
        check_query = """
import duckdb
conn = duckdb.connect('/root/.openclaw/workspace/data/memory.duckdb')

# 检查是否有被删除的数据（通过ID序列）
print("检查ID序列:")
result = conn.execute("SELECT id FROM memories ORDER BY id").fetchall()
print(f"  所有ID: {[r[0] for r in result]}")

# 检查最早和最晚的记录时间
if len(result) > 0:
    earliest = conn.execute("SELECT MIN(created_at) FROM memories").fetchone()
    latest = conn.execute("SELECT MAX(created_at) FROM memories").fetchone()
    print(f"  最早记录: {earliest[0]}")
    print(f"  最晚记录: {latest[0]}")

conn.close()
"""
        stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{check_query}"')
        check_result = stdout.read().decode().strip()
        print(f"  {check_result}")
        print()

        # 7. 检查sync_memory.py的API地址历史
        print("[7] sync_memory.py中的API地址...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n 'MEMORY_API\\|157.245' /root/.openclaw/workspace/sync_memory.py"
        )
        api_config = stdout.read().decode().strip()
        print(f"  {api_config}")
        print()

        # 8. 查看sync_memory.py的完整内容
        print("[8] sync_memory.py完整代码...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/workspace/sync_memory.py"
        )
        sync_code = stdout.read().decode().strip()
        print(f"  {sync_code}")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_memory_usage_history()

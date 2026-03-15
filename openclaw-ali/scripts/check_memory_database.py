#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw记忆系统的数据库"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_memory_database():
    print("="*70)
    print(" 检查OpenClaw记忆系统的专属数据库")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查找所有数据库文件
        print("[1] 查找OpenClaw目录下的数据库文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw -type f \\( -name '*.db' -o -name '*.sqlite' -o -name '*.duckdb' -o -name '*.lance' \\) 2>/dev/null"
        )
        db_files = stdout.read().decode().strip()
        if db_files:
            print("  找到以下数据库文件:")
            for f in db_files.split('\n'):
                if f:
                    print(f"    - {f}")
        else:
            print("  未找到数据库文件")
        print()

        # 2. 检查workspace目录下的数据目录
        print("[2] 检查workspace数据目录...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/workspace/ | grep -E 'data|db|database|index|vector'"
        )
        data_dirs = stdout.read().decode().strip()
        if data_dirs:
            print("  找到:")
            print(f"  {data_dirs}")
        else:
            print("  未找到数据相关目录")
        print()

        # 3. 检查记忆索引目录
        print("[3] 检查记忆索引目录...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw -type d -name '*index*' -o -name '*vector*' -o -name '*embed*' 2>/dev/null | head -20"
        )
        index_dirs = stdout.read().decode().strip()
        if index_dirs:
            print("  找到索引目录:")
            for d in index_dirs.split('\n'):
                if d:
                    print(f"    - {d}")
        else:
            print("  未找到索引目录")
        print()

        # 4. 检查.qmd文件 (QMD数据库)
        print("[4] 检查QMD数据库文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw -name '*.qmd' 2>/dev/null"
        )
        qmd_files = stdout.read().decode().strip()
        if qmd_files:
            print("  找到QMD文件:")
            for f in qmd_files.split('\n'):
                if f:
                    print(f"    - {f}")
                    # 显示文件大小
                    stdin2, stdout2, stderr2 = ssh.exec_command(f"ls -lh {f}")
                    size = stdout2.read().decode().strip()
                    print(f"      {size}")
        else:
            print("  未找到QMD文件")
        print()

        # 5. 检查agents目录
        print("[5] 检查agents目录结构...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/agents/ 2>/dev/null"
        )
        agents_dir = stdout.read().decode().strip()
        if agents_dir:
            print("  Agents目录:")
            print(f"  {agents_dir}")
        print()

        # 6. 查看主agent的数据目录
        print("[6] 检查主agent的数据存储...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents/main -type f \\( -name '*.db' -o -name '*.qmd' -o -name '*.json' \\) 2>/dev/null | head -20"
        )
        main_data = stdout.read().decode().strip()
        if main_data:
            print("  主agent数据文件:")
            for f in main_data.split('\n'):
                if f:
                    print(f"    - {f}")
        else:
            print("  未找到数据文件")
        print()

        # 7. 检查完整的agents目录树
        print("[7] agents目录完整结构...")
        stdin, stdout, stderr = ssh.exec_command(
            "tree /root/.openclaw/agents/ -L 3 2>/dev/null || find /root/.openclaw/agents/ -type d | head -30"
        )
        tree = stdout.read().decode().strip()
        print(tree)
        print()

        # 8. 检查session存储
        print("[8] 检查session存储...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw -name '*session*' -o -name '*transcript*' 2>/dev/null | grep -v '.git' | head -10"
        )
        sessions = stdout.read().decode().strip()
        if sessions:
            print("  Session文件:")
            for s in sessions.split('\n'):
                if s:
                    print(f"    - {s}")
        else:
            print("  未找到session文件")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_memory_database()

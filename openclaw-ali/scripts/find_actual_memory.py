#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查找之前实际在用的记忆系统"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def find_actual_memory_system():
    print("="*70)
    print(" 查找之前实际在用的记忆系统")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查workspace/data目录下所有数据库
        print("[1] workspace/data目录所有数据库...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lh /root/.openclaw/workspace/data/ 2>/dev/null"
        )
        data_dir = stdout.read().decode().strip()
        print(f"  {data_dir}")
        print()

        # 2. 检查每个数据库的大小和内容
        print("[2] 检查各数据库的表和记录数...")
        databases = [
            "/root/.openclaw/workspace/data/a_market.duckdb",
            "/root/.openclaw/workspace/data/stock_detail.duckdb",
            "/root/.openclaw/workspace/data/memory.duckdb",
            "/root/.openclaw/workspace/stock_data.db",
        ]

        for db in databases:
            db_name = db.split('/')[-1]
            print(f"\n  {db_name}:")

            # 检查文件大小
            stdin, stdout, stderr = ssh.exec_command(f"ls -lh {db}")
            size_info = stdout.read().decode().strip()
            print(f"    {size_info}")

            # 检查表和记录数
            check_script = f"""
import duckdb
try:
    conn = duckdb.connect('{db}')
    tables = conn.execute('SHOW TABLES').fetchall()
    print(f'    表: {{len(tables)}}')
    for t in tables:
        count = conn.execute(f'SELECT COUNT(*) FROM {{t[0]}}').fetchone()[0]
        print(f'      - {{t[0]}}: {{count}}条')
except Exception as e:
    print(f'    Error: {{e}}')
"""
            stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{check_script}"')
            result = stdout.read().decode().strip()
            if result and not "Error" in result:
                print(f"    {result}")

        print()

        # 3. 检查sync_memory.py的git历史（看之前版本调用什么）
        print("[3] sync_memory.py的修改历史...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw/workspace && git log --oneline --all -10 sync_memory.py 2>/dev/null"
        )
        git_history = stdout.read().decode().strip()
        if git_history:
            print(f"  {git_history}")
        else:
            print("  无git记录")

        print()

        # 4. 查看MEMORY.md和memory目录的内容
        print("[4] Markdown记忆文件内容...")
        stdin, stdout, stderr = ssh.exec_command(
            "wc -l /root/.openclaw/workspace/MEMORY.md 2>/dev/null && head -20 /root/.openclaw/workspace/MEMORY.md"
        )
        memory_md = stdout.read().decode().strip()
        print(f"  MEMORY.md:\n{memory_md}")

        print("\n  memory目录:")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lh /root/.openclaw/workspace/memory/*.md 2>/dev/null | head -5"
        )
        memory_files = stdout.read().decode().strip()
        print(f"  {memory_files}")

        print()

        # 5. 检查是否有其他记忆相关的脚本
        print("[5] 记忆相关的Python脚本...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/workspace -name '*memory*.py' -o -name '*remember*.py' 2>/dev/null"
        )
        memory_scripts = stdout.read().decode().strip()
        if memory_scripts:
            print("  找到以下脚本:")
            for script in memory_scripts.split('\n'):
                if script:
                    print(f"    - {script}")
        print()

        # 6. 检查memory_backups目录
        print("[6] memory_backups目录...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lh /root/.openclaw/workspace/memory_backups/ 2>/dev/null | head -10"
        )
        backups = stdout.read().decode().strip()
        if backups:
            print(f"  {backups}")
        else:
            print("  目录不存在")
        print()

        # 7. 检查是否有直接写入MEMORY.md的脚本
        print("[7] 查找写入MEMORY.md的代码...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r 'MEMORY.md\\|memory.*write\\|append.*memory' /root/.openclaw/workspace/*.py 2>/dev/null | head -10"
        )
        write_code = stdout.read().decode().strip()
        if write_code:
            print("  找到相关代码:")
            print(f"  {write_code}")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    find_actual_memory_system()

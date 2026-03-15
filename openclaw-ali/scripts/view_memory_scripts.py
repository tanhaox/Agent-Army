#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看服务器上的记忆系统脚本"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def view_memory_scripts():
    print("="*70)
    print(" 查看记忆系统脚本")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. memory_backup.py
        print("[1] memory_backup.py...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/workspace/scripts/memory_backup.py"
        )
        content = stdout.read().decode().strip()
        print(content[:500])
        print()

        # 2. convert_memory.py
        print("[2] convert_memory.py...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/workspace/scripts/convert_memory.py"
        )
        content = stdout.read().decode().strip()
        print(content[:500])
        print()

        # 3. smart_heartbeat.py (写入MEMORY.md的脚本)
        print("[3] smart_heartbeat.py (写入MEMORY.md)...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -A 20 'MEMORY.md' /root/.openclaw/workspace/smart_heartbeat.py | head -30"
        )
        content = stdout.read().decode().strip()
        print(content)
        print()

        # 4. memory_backups目录的备份文件
        print("[4] memory_backups备份文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/workspace/memory_backups/memory_backup_20260312_234032.csv"
        )
        backup = stdout.read().decode().strip()
        print(backup[:500])
        print()

        # 5. MEMORY.md的内容
        print("[5] MEMORY.md内容 (前100行)...")
        stdin, stdout, stderr = ssh.exec_command(
            "head -100 /root/.openclaw/workspace/MEMORY.md"
        )
        memory_md = stdout.read().decode().strip()
        print(memory_md)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    view_memory_scripts()

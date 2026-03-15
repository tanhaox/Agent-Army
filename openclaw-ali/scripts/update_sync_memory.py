#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新sync_memory.py的API地址"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"
NEW_API = f"http://{SG_HOST}:18888"

def update_sync_memory():
    print("="*60)
    print(" 更新sync_memory.py的API地址")
    print("="*60)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 检查当前配置
        print("[1] 检查当前API地址...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n 'MEMORY_API' /root/.openclaw/workspace/sync_memory.py"
        )
        current = stdout.read().decode().strip()
        print(f"  当前配置:\n{current}")
        print()

        # 更新API地址
        print(f"[2] 更新为新的API地址: {NEW_API}")
        stdin, stdout, stderr = ssh.exec_command(
            f"sed -i 's|MEMORY_API.*|MEMORY_API = \"{NEW_API}\"|' "
            "/root/.openclaw/workspace/sync_memory.py"
        )
        stdout.read()

        # 验证更新
        print("[3] 验证更新...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n 'MEMORY_API' /root/.openclaw/workspace/sync_memory.py"
        )
        updated = stdout.read().decode().strip()
        print(f"  新配置:\n{updated}")
        print()

        # 检查capital_flow_monitor.py
        print("[4] 检查capital_flow_monitor.py...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n '18888\\|MEMORY_API' /root/.openclaw/workspace/capital_flow_monitor.py || echo '无相关配置'"
        )
        monitor = stdout.read().decode().strip()
        print(f"  {monitor}")
        print()

        print("="*60)
        print(" 更新完成!")
        print("="*60)
        print()
        print("  sync_memory.py现在可以使用新的记忆API了")
        print(f"  API地址: {NEW_API}")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    update_sync_memory()

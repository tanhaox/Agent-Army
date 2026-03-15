#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw完整配置"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_full_config():
    print("="*70)
    print(" 检查OpenClaw完整配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查openclaw.json中的channel配置
        print("[1] Channel配置（openclaw.json）...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 30 'channels'"
        )
        channels = stdout.read().decode().strip()
        print(channels)
        print()

        # 2. 检查Telegram配置
        print("[2] Telegram配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 20 'telegram'"
        )
        telegram = stdout.read().decode().strip()
        print(telegram)
        print()

        # 3. 检查所有Agent
        print("[3] 所有Agent列表...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/agents/"
        )
        agents = stdout.read().decode().strip()
        print(agents)
        print()

        # 4. 检查Gateway端口
        print("[4] Gateway配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 10 'gateway'"
        )
        gateway = stdout.read().decode().strip()
        print(gateway)
        print()

        # 5. 查看完整的openclaw.json
        print("[5] 完整配置（前100行）...")
        stdin, stdout, stderr = ssh.exec_command(
            "head -100 /root/.openclaw/openclaw.json"
        )
        full_config = stdout.read().decode().strip()
        print(full_config)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_full_config()

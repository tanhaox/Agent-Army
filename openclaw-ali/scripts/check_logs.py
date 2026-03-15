#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Gateway实时日志"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_realtime_logs():
    print("="*70)
    print(" 检查Gateway实时日志")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查看最近的所有日志（包括错误）
        print("[1] Gateway最近日志（包含错误）...")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -100 /root/.openclaw/logs/gateway.log 2>/dev/null | tail -50"
        )
        logs = stdout.read().decode().strip()
        if logs:
            print(logs)
        else:
            print("  无日志")
        print()

        # 2. 检查系统日志
        print("[2] 系统日志（journalctl）...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u openclaw-gateway -n 50 --no-pager 2>/dev/null | tail -30"
        )
        syslog = stdout.read().decode().strip()
        if syslog:
            print(syslog)
        else:
            print("  无系统日志")
        print()

        # 3. 检查实际使用的配置
        print("[3] 实际配置检查...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -m json.tool | grep -A 5 'model'"
        )
        config = stdout.read().decode().strip()
        print(config)
        print()

        # 4. 检查API Key
        print("[4] API Key配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/auth-profiles.json | python3 -m json.tool | grep -A 3 'zai'"
        )
        auth = stdout.read().decode().strip()
        print(auth)
        print()

        # 5. 检查是否有多个Gateway进程
        print("[5] 检查Gateway进程...")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep -E 'openclaw|gateway' | grep -v grep"
        )
        processes = stdout.read().decode().strip()
        print(processes)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_realtime_logs()

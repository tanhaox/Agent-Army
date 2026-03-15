#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Telegram配置和错误"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_telegram():
    print("="*70)
    print(" 检查Telegram配置和错误")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查Telegram bot token
        print("[1] Telegram Bot Token...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r 'TELEGRAM_BOT_TOKEN\\|telegram.*token' /root/.openclaw/ 2>/dev/null | head -10"
        )
        tokens = stdout.read().decode().strip()
        if tokens:
            print(tokens[:500])
        else:
            print("  未找到token配置")
        print()

        # 2. 检查.env文件
        print("[2] 检查.env文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw -name '.env' -o -name '*.env' | xargs cat 2>/dev/null | grep -i telegram"
        )
        env = stdout.read().decode().strip()
        if env:
            print(env)
        else:
            print("  无Telegram环境变量")
        print()

        # 3. 查看完整的Gateway日志（所有内容）
        print("[3] 完整Gateway日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/logs/gateway.log 2>/dev/null | tail -200"
        )
        logs = stdout.read().decode().strip()
        if logs:
            # 只显示包含error或rate的行
            error_lines = [line for line in logs.split('\n')
                          if 'error' in line.lower() or 'rate' in line.lower() or 'limit' in line.lower()]
            if error_lines:
                print("  错误日志：")
                for line in error_lines[-20:]:
                    print(f"  {line}")
            else:
                print("  无错误日志")
                print("\n  最后10行：")
                for line in logs.split('\n')[-10:]:
                    print(f"  {line}")
        else:
            print("  无日志")
        print()

        # 4. 检查Agent日志
        print("[4] Agent日志...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/logs/agent.log 2>/dev/null | tail -50"
        )
        agent_logs = stdout.read().decode().strip()
        if agent_logs:
            print(agent_logs)
        else:
            print("  无Agent日志")
        print()

        # 5. 检查内存使用
        print("[5] 内存和CPU使用...")
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep openclaw-gateway | grep -v grep | awk '{print \"CPU: \"$3\"%  MEM: \"$4\"%  RSS: \"$6\" KB\"}'"
        )
        usage = stdout.read().decode().strip()
        print(usage)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_telegram()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Telegram配置和实际错误"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_telegram_config():
    print("="*70)
    print(" 检查Telegram配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查Telegram bot token
        print("[1] Telegram Bot配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r 'TELEGRAM_BOT_TOKEN\\|bot.*token' /root/.openclaw/ 2>/dev/null | head -5 || echo '  未找到'"
        )
        print(stdout.read().decode().strip())
        print()

        # 2. 查看最近的Telegram会话
        print("[2] 最近的Telegram会话错误:")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents -name '*.jsonl' -type f -exec grep -l 'telegram' {} \\; | "
            "xargs grep -h 'rate limit\\|error' | tail -5"
        )
        errors = stdout.read().decode().strip()
        if errors:
            for line in errors.split('\n'):
                if line.strip():
                    print(f"  {line[:200]}")
        else:
            print("  无错误")
        print()

        # 3. 检查实际使用的模型
        print("[3] 最近调用的模型:")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/agents -name '*.jsonl' -type f -mmin -10 | "
            "xargs grep -h '\"model\":' | tail -5"
        )
        models = stdout.read().decode().strip()
        if models:
            for line in models.split('\n'):
                if 'model' in line.lower():
                    print(f"  {line[:150]}")
        else:
            print("  无记录")
        print()

        # 4. 检查Gateway日志中的API调用
        print("[4] Gateway日志（API调用）:")
        stdin, stdout, stderr = ssh.exec_command(
            "tail -100 /root/.openclaw/logs/gateway.log 2>/dev/null | "
            "grep -i 'glm\\|model\\|api' | tail -10"
        )
        api_calls = stdout.read().decode().strip()
        if api_calls:
            for line in api_calls.split('\n'):
                print(f"  {line[:150]}")
        else:
            print("  无API调用记录")
        print()

        # 5. 检查完整的agent配置
        print("[5] 完整agent配置（model部分）:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -c "
            "'import sys, json; c=json.load(sys.stdin); "
            "print(json.dumps({\"model\": c.get(\"model\", {}), \"models\": c.get(\"models\", {})}, indent=2))'"
        )
        print(stdout.read().decode().strip())
        print()

        # 6. 检查环境变量中的模型设置
        print("[6] 环境变量:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -i 'model\\|glm' /root/.openclaw/agents/main/agent/.env 2>/dev/null || echo '  无.env文件'"
        )
        print(stdout.read().decode().strip())
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_telegram_config()

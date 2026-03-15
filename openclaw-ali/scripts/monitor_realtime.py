#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""监控Gateway实时日志"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def monitor_realtime():
    print("="*70)
    print(" 监控Gateway实时日志")
    print("="*70)
    print()
    print("请在Telegram发送一条消息，我会捕获实时日志...")
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 清空日志
        stdin, stdout, stderr = ssh.exec_command("truncate -s 0 /root/.openclaw/logs/gateway.log")
        stdout.read()

        print("[监控中] 等待30秒，捕获新日志...")
        print()

        # 等待30秒，持续监控日志
        time.sleep(30)

        # 读取日志
        stdin, stdout, stderr = ssh.exec_command("cat /root/.openclaw/logs/gateway.log 2>/dev/null | tail -100")
        logs = stdout.read().decode().strip()

        if logs:
            print("="*70)
            print(" 捕获到的日志")
            print("="*70)
            print()

            # 只显示错误相关的行
            error_keywords = ['error', 'rate', 'limit', 'failed', '429', 'glm']
            lines = logs.split('\n')

            for line in lines:
                # 解析JSON日志
                if line.strip():
                    try:
                        import json
                        log_entry = json.loads(line)

                        # 提取关键信息
                        log_level = log_entry.get('_meta', {}).get('logLevelName', 'INFO')
                        message = log_entry.get('0', '')

                        # 只显示错误或包含关键词的日志
                        if (log_level == 'ERROR' or
                            any(keyword in message.lower() for keyword in error_keywords) or
                            'model' in message.lower() or
                            'api' in message.lower()):

                            print(f"[{log_level}] {message[:200]}")

                    except:
                        # 如果不是JSON，直接显示
                        if any(keyword in line.lower() for keyword in error_keywords):
                            print(line[:200])
        else:
            print("  无日志输出")

        print()
        print("="*70)
        print(" 检查当前模型配置")
        print("="*70)
        print()

        # 检查实际使用的模型
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -c 'import sys, json; c=json.load(sys.stdin); print(\"Primary Model:\", c.get(\"model\", {}).get(\"primary\", \"未设置\"))'"
        )
        model = stdout.read().decode().strip()
        print(model)
        print()

        # 检查API Key
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/auth-profiles.json | python3 -c 'import sys, json; c=json.load(sys.stdin); print(\"API Key:\", c.get(\"profiles\", {}).get(\"zai\", {}).get(\"key\", \"未设置\")[:20] + \"...\")'"
        )
        api_key = stdout.read().decode().strip()
        print(api_key)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    monitor_realtime()

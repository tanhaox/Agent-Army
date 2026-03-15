#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw限流配置"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_rate_limits():
    print("="*70)
    print(" 检查OpenClaw限流配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查openclaw.json中的限流配置
        print("[1] 检查限流配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 10 -B 2 'rate\\|limit\\|throttle' || echo '  无限流配置'"
        )
        rate_config = stdout.read().decode().strip()
        print(rate_config)
        print()

        # 2. 检查agent.json中的限流
        print("[2] Agent限流配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json | python3 -m json.tool | grep -A 5 -B 2 'rate\\|limit\\|throttle' || echo '  无限流配置'"
        )
        agent_rate = stdout.read().decode().strip()
        print(agent_rate)
        print()

        # 3. 检查完整agent配置
        print("[3] 完整Agent配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/agents/main/agent/agent.json"
        )
        agent_config = stdout.read().decode().strip()
        # 只显示关键部分
        for line in agent_config.split('\n'):
            if any(word in line.lower() for word in ['model', 'rate', 'limit', 'throttle', 'api']):
                print(f"  {line}")
        print()

        # 4. 搜索"API rate limit reached"字符串
        print("[4] 搜索错误消息来源:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r 'API rate limit reached' /root/.openclaw/ 2>/dev/null | head -5 || echo '  未找到'"
        )
        search = stdout.read().decode().strip()
        print(search)
        print()

        # 5. 检查Telegram bot配置
        print("[5] Telegram Bot配置:")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | python3 -m json.tool | grep -A 15 'telegram'"
        )
        telegram = stdout.read().decode().strip()
        print(telegram)
        print()

        # 6. 检查最近的会话日志
        print("[6] 最近的会话（查看实际错误）:")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt /root/.openclaw/agents/main/sessions/*.jsonl 2>/dev/null | head -1 | awk '{print $NF}' | xargs tail -5 2>/dev/null || echo '  无会话日志'"
        )
        sessions = stdout.read().decode().strip()
        if sessions and sessions != '  无会话日志':
            print(sessions[:500])
        else:
            print(sessions)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check_rate_limits()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接查看最新的Telegram会话错误"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_latest_error():
    print("="*70)
    print(" 查看最新的Telegram错误")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 找到最新的会话文件
        print("[1] 查找最新会话...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt /root/.openclaw/agents/main/sessions/*.jsonl 2>/dev/null | head -1 | awk '{print $NF}'"
        )
        session_file = stdout.read().decode().strip()
        print(f"  会话文件: {session_file}")
        print()

        # 读取最后10条消息
        print("[2] 最后10条消息:")
        stdin, stdout, stderr = ssh.exec_command(f"tail -10 '{session_file}'")
        messages = stdout.read().decode().strip()

        for i, line in enumerate(messages.split('\n'), 1):
            if line.strip():
                import json
                try:
                    msg = json.loads(line)
                    msg_type = msg.get('type', '')
                    role = msg.get('message', {}).get('role', '')

                    # 显示关键信息
                    if msg_type == 'message':
                        content = msg.get('message', {}).get('content', [])
                        error = msg.get('message', {}).get('errorMessage', '')
                        model = msg.get('message', {}).get('model', '')

                        if error:
                            print(f"\n  [{i}] ERROR:")
                            print(f"    {error[:200]}")

                        if model:
                            print(f"\n  [{i}] Model: {model}")

                        if role == 'user':
                            text = ''
                            if isinstance(content, list) and content:
                                text = content[0].get('text', '')[:50] if isinstance(content[0], dict) else str(content[0])[:50]
                            print(f"\n  [{i}] User: {text}...")

                except:
                    pass
        print()

        # 查找包含"rate limit"或"429"的消息
        print("[3] 查找错误详情:")
        stdin, stdout, stderr = ssh.exec_command(
            f"grep -i 'rate limit\\|429\\|余额不足\\|error' '{session_file}' | tail -3"
        )
        errors = stdout.read().decode().strip()

        if errors:
            for line in errors.split('\n'):
                if line.strip():
                    try:
                        import json
                        msg = json.loads(line)
                        error_msg = msg.get('message', {}).get('errorMessage', '')
                        if error_msg:
                            print(f"\n  ❌ {error_msg}")
                    except:
                        print(f"  {line[:200]}")
        else:
            print("  无错误")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check_latest_error()

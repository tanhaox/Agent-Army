#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速检查记忆API状态"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_status():
    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 检查端口
        print("检查端口18888...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
        port = stdout.read().decode().strip()

        if port:
            print(f"[OK] {port}")

            # 测试API
            print("\n测试健康检查...")
            stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:18888/health")
            health = stdout.read().decode().strip()
            print(f"{health}")
        else:
            print("[未监听] 查看日志...")
            stdin, stdout, stderr = ssh.exec_command("tail -20 /root/.openclaw/workspace/logs/memory_api.log")
            log = stdout.read().decode().strip()
            print(log)

        ssh.close()

    except Exception as e:
        print(f"[错误] {e}")

if __name__ == '__main__':
    check_status()

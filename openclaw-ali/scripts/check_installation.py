#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw安装和启动方式"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_installation():
    print("="*70)
    print(" 检查OpenClaw安装")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查找openclaw命令
        print("[1] 查找openclaw命令...")
        stdin, stdout, stderr = ssh.exec_command("which openclaw || command -v openclaw || echo '未找到'")
        which = stdout.read().decode().strip()
        print(f"  {which}")
        print()

        # 2. 检查npm全局安装
        print("[2] npm全局安装...")
        stdin, stdout, stderr = ssh.exec_command("npm list -g openclaw 2>&1 | head -5")
        npm = stdout.read().decode().strip()
        print(npm)
        print()

        # 3. 检查node进程
        print("[3] Node进程...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep node | grep -v grep")
        nodes = stdout.read().decode().strip()
        print(nodes if nodes else "  无node进程")
        print()

        # 4. 检查OpenClaw目录
        print("[4] OpenClaw目录...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/.openclaw/ | head -20")
        dir_list = stdout.read().decode().strip()
        print(dir_list)
        print()

        # 5. 尝试用openclaw命令启动
        print("[5] 使用openclaw命令启动...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > logs/gateway.log 2>&1 &"
        )
        stdout.read()

        import time
        time.sleep(5)

        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'openclaw|gateway' | grep -v grep")
        process = stdout.read().decode().strip()
        if process:
            print("  ✅ 启动成功")
            print(f"  {process[:100]}")
        else:
            print("  ❌ 启动失败")

            # 查看错误日志
            stdin, stdout, stderr = ssh.exec_command("cat /root/.openclaw/logs/gateway.log 2>/dev/null | tail -20")
            error_log = stdout.read().decode().strip()
            if error_log:
                print(f"\n  错误日志:\n{error_log}")
        print()

        # 6. 检查端口
        print("[6] 检查端口18789...")
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep 18789 || netstat -tlnp 2>/dev/null | grep 18789 || echo '  未监听'"
        )
        port = stdout.read().decode().strip()
        print(port)
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_installation()

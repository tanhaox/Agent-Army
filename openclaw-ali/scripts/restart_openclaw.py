#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重启新加坡OpenClaw"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def restart_openclaw():
    print("="*70)
    print(" 重启新加坡OpenClaw")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查看当前状态
        print("[1] 当前Gateway进程...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw | grep -v grep")
        current = stdout.read().decode().strip()
        if current:
            for line in current.split('\n'):
                print(f"  {line}")
        else:
            print("  无运行中的进程")
        print()

        # 2. 停止Gateway
        print("[2] 停止OpenClaw Gateway...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f openclaw-gateway; pkill -f openclaw\\ gateway")
        stdout.read()
        time.sleep(2)
        print("  已停止")
        print()

        # 3. 启动Gateway
        print("[3] 启动OpenClaw Gateway...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw && nohup openclaw gateway start > /tmp/gateway.log 2>&1 &"
        )
        stdout.read()
        time.sleep(5)
        print("  已启动")
        print()

        # 4. 验证
        print("[4] 验证进程...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw | grep -v grep")
        running = stdout.read().decode().strip()
        if running:
            for line in running.split('\n'):
                print(f"  {line}")
        else:
            print("  ❌ 未找到运行进程")
        print()

        # 5. 检查端口
        print("[5] 检查监听端口...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep -E '18789|18730'")
        ports = stdout.read().decode().strip()
        if ports:
            print(ports)
        else:
            print("  未找到监听端口")
        print()

        # 6. 查看日志
        print("[6] 最新日志 (最后20行)...")
        stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/gateway.log 2>/dev/null || echo '日志文件不存在'")
        log = stdout.read().decode().strip()
        print(log)
        print()

        ssh.close()

        print("="*70)
        print(" 重启完成")
        print("="*70)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    restart_openclaw()

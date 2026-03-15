#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过systemd重启OpenClaw"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def restart_via_systemd():
    print("="*70)
    print(" 通过systemd重启OpenClaw")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 查找OpenClaw服务
        print("[1] 查找systemd服务...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl list-units --type=service | grep -i openclaw"
        )
        services = stdout.read().decode().strip()
        print(services if services else "  未找到服务")
        print()

        # 2. 检查服务状态
        print("[2] 检查服务状态...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl status openclaw-gateway.service 2>&1 | head -20"
        )
        status = stdout.read().decode().strip()
        print(status)
        print()

        # 3. 重启服务
        print("[3] 重启服务...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart openclaw-gateway.service")
        stdout.read()
        time.sleep(3)
        print("  已重启")
        print()

        # 4. 查看服务日志
        print("[4] 服务日志（最近50行）...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u openclaw-gateway.service -n 50 --no-pager"
        )
        logs = stdout.read().decode().strip()
        print(logs if logs else "  无日志")
        print()

        # 5. 验证服务
        print("[5] 验证服务...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl is-active openclaw-gateway.service && "
            "ps aux | grep openclaw | grep -v grep | head -2"
        )
        result = stdout.read().decode().strip()
        print(result)
        print()

        # 6. 检查端口
        print("[6] 检查端口...")
        stdin, stdout, stderr = ssh.exec_command(
            "ss -tlnp 2>/dev/null | grep 18789 || echo '  未监听'"
        )
        port = stdout.read().decode().strip()
        print(port)
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
    restart_via_systemd()

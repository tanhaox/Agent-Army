#!/usr/bin/env python3
"""OpenClaw 安装脚本"""
import paramiko
import time
import os

# 服务器配置
HOST = "157.245.195.58"
PORT = 22
USER = "root"
PASSWORD = "omnbmh@2026OpenClaw"

def install_openclaw():
    """连接服务器并安装 OpenClaw"""
    print(f"[INFO] Connecting to server {HOST}...")

    # 创建SSH客户端
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 尝试使用SSH密钥连接
        key_paths = [
            os.path.expanduser("~/.ssh/id_ed25519"),
            os.path.expanduser("~/.ssh/id_rsa"),
        ]

        key_connected = False
        for key_path in key_paths:
            if os.path.exists(key_path):
                print(f"[INFO] Using SSH key: {key_path}")
                try:
                    if "ed25519" in key_path:
                        key = paramiko.Ed25519Key.from_private_key_file(key_path)
                    else:
                        key = paramiko.RSAKey.from_private_key_file(key_path)
                    client.connect(HOST, PORT, USER, pkey=key, timeout=30)
                    key_connected = True
                    break
                except Exception as e:
                    print(f"[WARN] Failed to use {key_path}: {e}")
                    continue

        if not key_connected:
            # 回退到密码连接
            print(f"[INFO] Using password authentication")
            client.connect(HOST, PORT, USER, PASSWORD, timeout=30)

        print("[OK] Connected successfully!")

        # 执行安装命令（跳过 apt update，直接安装）
        commands = [
            # OpenClaw 官方安装脚本（包含依赖安装）
            "curl -fsSL https://openclaw.ai/install.sh | bash"
        ]

        for cmd in commands:
            print(f"\n[CMD] {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

            # 实时输出
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    line = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                    print(line, end='')
                time.sleep(0.1)

            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print(f"[ERROR] Command failed with exit code: {exit_status}")
                return False

        print("\n[OK] OpenClaw installation completed!")
        print("\nNext step: Run configuration wizard")
        print("  ssh root@157.245.195.58")
        print("  openclaw onboard --install-daemon")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    install_openclaw()

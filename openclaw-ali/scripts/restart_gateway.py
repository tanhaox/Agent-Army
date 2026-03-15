#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新启动OpenClaw Gateway"""
import paramiko
import sys
import time
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  启动OpenClaw Gateway")
print("=" * 70)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 使用SSH密钥连接
key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        break
    except:
        continue

ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)

print("[1/3] 启动Gateway...")
# 启动Gateway（后台运行）
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway > /tmp/openclaw-gateway.log 2>&1 &')
stdout.read()

# 等待启动
print("   等待Gateway启动...")
time.sleep(5)

print()
print("[2/3] 检查Gateway状态...")
# 检查进程
stdin, stdout, stderr = ssh.exec_command('pgrep -f openclaw-gateway')
pid = stdout.read().decode('utf-8', errors='ignore').strip()

if pid:
    print(f"   ✅ Gateway运行中 (PID: {pid})")
else:
    print(f"   ❌ Gateway未运行，查看错误...")

    # 查看最新日志
    stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw-gateway.log')
    log = stdout.read().decode('utf-8', errors='ignore')
    print()
    print("   === 最新日志 ===")
    print(log)

print()

# 检查端口
print("[3/3] 检查端口监听...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port_output = stdout.read().decode('utf-8', errors='ignore')
if port_output.strip():
    print(f"   ✅ 端口18789正在监听")
    print(f"   {port_output.strip()}")
else:
    print(f"   ⚠️  端口18789未监听")

print()
print("=" * 70)
print("  访问地址:")
print("    https://157.245.195.58/chat?session=main")
print("    https://157.245.195.58/#token=openclaw123")
print("=" * 70)

ssh.close()

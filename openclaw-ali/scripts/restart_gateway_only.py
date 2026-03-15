#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重启OpenClaw Gateway"""
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
print("  重启OpenClaw Gateway")
print("=" * 70)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        break
    except:
        continue

ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)

# 停止Gateway
print("[1/3] 停止Gateway...")
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw-gateway')
stdout.read()
print("   ✅ Gateway已停止")

# 等待
time.sleep(2)

# 启动Gateway
print()
print("[2/3] 启动Gateway...")
stdin, stdout, stderr = ssh.exec_command('cd /root && nohup openclaw gateway > /tmp/openclaw-gateway.log 2>&1 &')
stdout.read()
print("   ✅ 启动命令已执行")

# 等待启动
print()
print("   等待Gateway启动...")
time.sleep(5)

# 检查状态
print()
print("[3/3] 检查Gateway状态...")
stdin, stdout, stderr = ssh.exec_command('pgrep -f openclaw-gateway')
pid = stdout.read().decode('utf-8', errors='ignore').strip()

if pid:
    print(f"   ✅ Gateway运行中 (PID: {pid})")

    # 检查端口
    stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
    port = stdout.read().decode('utf-8', errors='ignore')
    if port.strip():
        print(f"   ✅ 端口18789正在监听")
    else:
        print(f"   ⚠️  端口18789未监听")
else:
    print(f"   ❌ Gateway未启动")

    # 查看日志
    print()
    print("   查看错误日志...")
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw-gateway.log')
    log = stdout.read().decode('utf-8', errors='ignore')
    print(log)

print()
print("=" * 70)
print("  访问地址:")
print("    https://157.245.195.58/chat?session=main")
print("=" * 70)

ssh.close()

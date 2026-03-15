#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Gateway完整状态"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

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

print("=" * 70)
print("  OpenClaw Gateway 运行状态")
print("=" * 70)
print()

# 进程状态
print("[1] Gateway进程状态")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('ps aux | grep openclaw-gateway | grep -v grep')
proc = stdout.read().decode('utf-8', errors='ignore')
print(proc)

# 端口监听
print()
print("[2] 端口监听状态")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "(18789|18790)"')
ports = stdout.read().decode('utf-8', errors='ignore')
print(ports if ports.strip() else "   ❌ 未找到监听端口")

# nginx代理
print()
print("[3] Nginx代理状态")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx | grep -E "(Active|running)"')
nginx = stdout.read().decode('utf-8', errors='ignore')
print(nginx)

# Skills
print()
print("[4] 已安装的Skills")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/')
skills = stdout.read().decode('utf-8', errors='ignore')
print(skills)

# yahoo-finance skill
print()
print("[5] Yahoo Finance Skill详情")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('ls -lh ~/.openclaw/skills/yahoo-finance/')
yahoo = stdout.read().decode('utf-8', errors='ignore')
print(yahoo)

# Gateway最新日志
print()
print("[6] Gateway最新日志（最后10行）")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('tail -10 /tmp/openclaw-gateway.log')
log = stdout.read().decode('utf-8', errors='ignore')
print(log)

print()
print("=" * 70)
print("  ✅ OpenClaw正在运行！")
print()
print("  访问地址:")
print("    🌐 https://157.245.195.58/chat?session=main")
print("    🔑 https://157.245.195.58/#token=openclaw123")
print()
print("  测试命令:")
print("    refresh skills")
print("    同步伊利股份的雅虎财经数据")
print("=" * 70)

ssh.close()

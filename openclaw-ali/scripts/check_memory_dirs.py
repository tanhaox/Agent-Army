#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw记忆目录"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
print("  检查 OpenClaw 记忆目录")
print("=" * 70)
print()

# 检查各种可能的记忆目录
memory_dirs = [
    '~/.openclaw/memory/',
    '~/.openclaw/workspace/memory/',
    '~/.openclaw/agents/main/agent/memory/',
    '~/.openclaw/workspace-wangcai/memory/',
    '~/.openclaw/.memory/',
]

for i, dir_path in enumerate(memory_dirs, 1):
    print(f"[{i}] 检查 {dir_path}...")
    stdin, stdout, stderr = ssh.exec_command(f'ls -la {dir_path} 2>/dev/null || echo "目录不存在"')
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)
    print()

# 检查agents目录
print("[检查] agents 目录结构...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/agents/ 2>/dev/null || echo "无agents目录"')
agents = stdout.read().decode('utf-8', errors='ignore')
print(agents)
print()

print("=" * 70)
ssh.close()

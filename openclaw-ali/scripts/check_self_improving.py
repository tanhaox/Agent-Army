#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查self-improving-agent内容"""
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
print("  检查 self-improving-agent 内容")
print("=" * 70)
print()

# 列出文件
print("[1] self-improving-agent 文件列表...")
stdin, stdout, stderr = ssh.exec_command('ls -lah ~/.openclaw/workspace/skills/self-improving-agent/')
files = stdout.read().decode('utf-8', errors='ignore')
print(files)
print()

# 检查SKILL.md
print("[2] SKILL.md 文件...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/workspace/skills/self-improving-agent/SKILL.md 2>/dev/null | head -30')
skill_md = stdout.read().decode('utf-8', errors='ignore')
print(skill_md)
print()

# 检查memory目录
print("[3] memory 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -lah ~/.openclaw/workspace/skills/self-improving-agent/memory/ 2>/dev/null || echo "无memory目录"')
memory_dir = stdout.read().decode('utf-8', errors='ignore')
print(memory_dir)
print()

print("=" * 70)
ssh.close()

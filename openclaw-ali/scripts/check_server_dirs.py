#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查服务器目录状态"""
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
print("  服务器目录状态检查")
print("=" * 70)
print()

# 1. 检查workspace/skills
print("[1] ~/.openclaw/workspace/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/ 2>/dev/null')
result1 = stdout.read().decode('utf-8', errors='ignore')
print(result1)
print()

# 2. 检查yahoo-finance-claude
print("[2] ~/.openclaw/workspace/skills/yahoo-finance-claude/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/yahoo-finance-claude/ 2>/dev/null')
result2 = stdout.read().decode('utf-8', errors='ignore')
print(result2)
print()

# 3. 检查skills目录
print("[3] ~/.openclaw/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/ 2>/dev/null')
result3 = stdout.read().decode('utf-8', errors='ignore')
print(result3)
print()

# 4. 检查最近修改
print("[4] 最近5分钟修改的文件...")
stdin, stdout, stderr = ssh.exec_command('find ~/.openclaw/workspace/skills/ ~/.openclaw/skills/ -name "*.py" -o -name "*.md" 2>/dev/null | xargs ls -lt 2>/dev/null | head -10')
result4 = stdout.read().decode('utf-8', errors='ignore')
print(result4 if result4.strip() else "  无文件")
print()

print("=" * 70)
ssh.close()

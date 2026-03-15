#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查workspace/skills目录状态"""
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
print("  检查 workspace/skills 目录")
print("=" * 70)
print()

# 当前状态
print("[当前状态] workspace/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/')
current = stdout.read().decode('utf-8', errors='ignore')
print(current)
print()

# 检查是否有备份
print("[检查] 是否有备份...")
stdin, stdout, stderr = ssh.exec_command('find ~/.openclaw/ -name "*self-improving*" -type d 2>/dev/null')
backup = stdout.read().decode('utf-8', errors='ignore')
if backup.strip():
    print(backup)
else:
    print("  未找到备份")
print()

# 检查回收站或删除历史
print("[检查] 最近的删除操作...")
stdin, stdout, stderr = ssh.exec_command('grep -i "rm\|delete" ~/.bash_history 2>/dev/null | tail -10')
history = stdout.read().decode('utf-8', errors='ignore')
if history.strip():
    print(history)
else:
    print("  无历史记录")
print()

print("=" * 70)
ssh.close()

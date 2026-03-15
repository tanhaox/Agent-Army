#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用SFTP上传yahoo-finance-claude skill"""
import paramiko
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'
LOCAL_SKILL = Path('C:/AI-Agent-Local/openclaw-ali/skills/yahoo-finance-claude')
REMOTE_DIR = '/root/.openclaw/workspace/skills/yahoo-finance-claude'

print("=" * 70)
print("  上传 yahoo-finance-claude 到服务器")
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

# 创建SFTP
sftp = ssh.open_sftp()

# 创建目录
try:
    sftp.mkdir(REMOTE_DIR)
except:
    pass

# 上传SKILL.md
print("[1/3] 上传 SKILL.md...")
with open(LOCAL_SKILL / 'SKILL.md', 'rb') as f:
    sftp.putfo(f, f'{REMOTE_DIR}/SKILL.md')
print("   ✅ SKILL.md")

# 上传tool.py
print("[2/3] 上传 tool.py...")
with open(LOCAL_SKILL / 'tool.py', 'rb') as f:
    sftp.putfo(f, f'{REMOTE_DIR}/tool.py')
print("   ✅ tool.py")

sftp.close()

# 设置权限
print("[3/3] 设置权限...")
stdin, stdout, stderr = ssh.exec_command(f'chmod +x {REMOTE_DIR}/tool.py')
stdout.read()
print("   ✅ 权限已设置")

# 验证
print()
print("验证上传...")
stdin, stdout, stderr = ssh.exec_command(f'ls -lh {REMOTE_DIR}/')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

print()
print("=" * 70)
print("  ✅ 上传完成")
print("=" * 70)

ssh.close()

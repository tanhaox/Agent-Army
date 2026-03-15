#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复制skill到workspace/skills目录"""
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
print("  复制 yahoo-finance-claude 到 workspace/skills")
print("=" * 70)
print()

# 复制到workspace/skills
print("[1/2] 复制 skill 文件...")
stdin, stdout, stderr = ssh.exec_command('cp -r ~/.openclaw/skills/yahoo-finance-claude ~/.openclaw/workspace/skills/')
stdout.read()
print("   ✅ 文件已复制")
print()

# 验证
print("[2/2] 验证复制...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/yahoo-finance-claude/')
verify = stdout.read().decode('utf-8', errors='ignore')
print(verify)
print()

print("=" * 70)
print("  ✅ yahoo-finance-claude 已复制到正确位置")
print("=" * 70)
print()
print("位置: ~/.openclaw/workspace/skills/yahoo-finance-claude/")
print()
print("现在在OpenClaw中试试:")
print("  refresh skills")
print("  列出所有skill")
print()

ssh.close()

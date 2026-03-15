#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证复制结果"""
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

print("验证复制结果...")
stdin, stdout, stderr = ssh.exec_command('ls -lah ~/.openclaw/workspace/skills/yahoo-finance-claude/')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)
print()

print("检查 SKILL.md 前20行...")
stdin, stdout, stderr = ssh.exec_command('head -20 ~/.openclaw/workspace/skills/yahoo-finance-claude/SKILL.md')
skill_md = stdout.read().decode('utf-8', errors='ignore')
print(skill_md)

ssh.close()

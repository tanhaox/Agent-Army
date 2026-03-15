#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比skill格式，找出问题"""
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
print("  对比Skill格式")
print("=" * 70)
print()

# 1. 检查yahoo-finance-claude的SKILL.md
print("[1] yahoo-finance-claude/SKILL.md (完整内容)")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/skills/yahoo-finance-claude/SKILL.md')
yahoo_skill = stdout.read().decode('utf-8', errors='ignore')
print(yahoo_skill)
print()

# 2. 检查smart-time-handler的SKILL.md
print("[2] smart-time-handler/SKILL.md (完整内容)")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/skills/smart-time-handler/SKILL.md')
smart_skill = stdout.read().decode('utf-8', errors='ignore')
print(smart_skill)
print()

# 3. 检查.deploy-to-vercel的SKILL.md
print("[3] deploy-to-vercel/SKILL.md (完整内容)")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/skills/deploy-to-vercel/SKILL.md')
deploy_skill = stdout.read().decode('utf-8', errors='ignore')
print(deploy_skill)
print()

# 4. 检查文件大小
print("[4] 文件大小对比")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command('ls -lh ~/.openclaw/skills/*/SKILL.md 2>/dev/null')
sizes = stdout.read().decode('utf-8', errors='ignore')
print(sizes)

print()
print("=" * 70)
ssh.close()

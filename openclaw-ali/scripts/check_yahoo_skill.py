#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Yahoo Finance Skill部署情况"""
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
print("  检查Yahoo Finance Skill部署")
print("=" * 70)
print()

# 1. 检查skills目录
print("[1] 检查 ~/.openclaw/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/')
skills = stdout.read().decode('utf-8', errors='ignore')
print(skills)

# 2. 检查yahoo-finance目录
print()
print("[2] 检查 yahoo-finance/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/yahoo-finance/')
yahoo = stdout.read().decode('utf-8', errors='ignore')
print(yahoo)

# 3. 检查SKILL.md内容（前20行）
print()
print("[3] 检查 SKILL.md 前20行...")
stdin, stdout, stderr = ssh.exec_command('head -20 ~/.openclaw/skills/yahoo-finance/SKILL.md')
skill_md = stdout.read().decode('utf-8', errors='ignore')
print(skill_md)

# 4. 检查SKILL.md格式
print()
print("[4] 检查 SKILL.md YAML frontmatter...")
stdin, stdout, stderr = ssh.exec_command('head -10 ~/.openclaw/skills/yahoo-finance/SKILL.md | grep -E "^name:|^description:"')
yaml_check = stdout.read().decode('utf-8', errors='ignore')
if yaml_check.strip():
    print("✅ 找到YAML字段:")
    print(yaml_check)
else:
    print("❌ 未找到YAML字段")

# 5. 对比其他skill的格式
print()
print("[5] 对比其他skill的SKILL.md格式（smart-time-handler）...")
stdin, stdout, stderr = ssh.exec_command('head -10 ~/.openclaw/skills/smart-time-handler/SKILL.md 2>/dev/null || echo "文件不存在"')
other_skill = stdout.read().decode('utf-8', errors='ignore')
print(other_skill)

print()
print("=" * 70)
ssh.close()

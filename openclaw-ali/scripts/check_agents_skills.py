#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查.agents/skills目录"""
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
print("  检查 .agents/skills 目录")
print("=" * 70)
print()

# 检查.agents/skills
print("[1] 检查 ~/.openclaw/.agents/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/.agents/skills/ 2>/dev/null || echo "目录不存在"')
agents_skills = stdout.read().decode('utf-8', errors='ignore')
print(agents_skills)
print()

# 如果存在，检查deploy-to-vercel
if "总用量" in agents_skills or "total" in agents_skills:
    print("[2] 检查 deploy-to-vercel skill...")
    stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/.agents/skills/deploy-to-vercel/ 2>/dev/null | head -10')
    deploy_vercel = stdout.read().decode('utf-8', errors='ignore')
    print(deploy_vercel)
    print()

# 检查是否有配置指定skills根目录
print("[3] 搜索配置中的 skills 根目录...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | grep -i "root"')
roots = stdout.read().decode('utf-8', errors='ignore')
if roots.strip():
    print("找到 'root' 配置:")
    print(roots)
else:
    print("未找到 'root' 配置")
print()

# 检查workspace目录
print("[4] 检查 workspace/skills 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/ 2>/dev/null || echo "目录不存在"')
workspace_skills = stdout.read().decode('utf-8', errors='ignore')
print(workspace_skills)
print()

print("=" * 70)
ssh.close()

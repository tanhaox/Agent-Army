#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细对比不同路径的目录内容"""
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
print("  路径对比检查")
print("=" * 70)
print()

# 检查主workspace目录
print("[A] ~/.openclaw/workspace/ 的内容...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/')
main_workspace = stdout.read().decode('utf-8', errors='ignore')
print(main_workspace)
print()

# 检查skills子目录
print("[B] ~/.openclaw/workspace/skills/ 的内容...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/')
skills_dir = stdout.read().decode('utf-8', errors='ignore')
print(skills_dir)
print()

# 检查yahoo-finance-claude
print("[C] ~/.openclaw/workspace/skills/yahoo-finance-claude/ 的内容...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/workspace/skills/yahoo-finance-claude/')
yahoo_dir = stdout.read().decode('utf-8', errors='ignore')
print(yahoo_dir)
print()

# 检查工作目录配置
print("[D] openclaw.json 中的 workspace 配置...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | grep -A 5 "workspace"')
workspace_config = stdout.read().decode('utf-8', errors='ignore')
print(workspace_config)
print()

print("=" * 70)
print("  分析:")
print("  如果您在 OpenClaw 中运行检查，它看的是 [A] 主workspace目录")
print("  但 skills 实际在 [B] skills/ 子目录中")
print("=" * 70)

ssh.close()

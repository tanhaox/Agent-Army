#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw的skill配置"""
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
print("  检查OpenClaw Skill配置")
print("=" * 70)
print()

# 1. 检查openclaw.json配置
print("[1] openclaw.json 中的 skills 配置...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | grep -A 20 "skills"')
config = stdout.read().decode('utf-8', errors='ignore')
print(config)
print()

# 2. 检查.agents/skills目录
print("[2] .agents/skills/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/.agents/skills/ 2>/dev/null || echo "目录不存在"')
agents_skills = stdout.read().decode('utf-8', errors='ignore')
print(agents_skills)
print()

# 3. 检查Gateway日志中关于skills的信息
print("[3] Gateway启动时的skill加载日志...")
stdin, stdout, stderr = ssh.exec_command('grep -i "skill" /tmp/openclaw-gateway.log | tail -30')
skill_logs = stdout.read().decode('utf-8', errors='ignore')
print(skill_logs)
print()

# 4. 对比能工作的skill路径
print("[4] 检查smart-time-handler的实际路径...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/smart-time-handler/ 2>/dev/null && readlink -f ~/.openclaw/skills/smart-time-handler 2>/dev/null || echo "非符号链接"')
smart_handler = stdout.read().decode('utf-8', errors='ignore')
print(smart_handler)
print()

# 5. 检查yahoo-finance-claude的权限
print("[5] yahoo-finance-claude 权限...")
stdin, stdout, stderr = ssh.exec_command('ls -la ~/.openclaw/skills/yahoo-finance-claude/')
yahoo_perms = stdout.read().decode('utf-8', errors='ignore')
print(yahoo_perms)
print()

print("=" * 70)
ssh.close()

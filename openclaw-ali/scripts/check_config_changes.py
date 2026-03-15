#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查配置文件和状态"""
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
print("  检查配置变更")
print("=" * 70)
print()

# 1. 检查配置备份
print("[1] 查看配置备份...")
stdin, stdout, stderr = ssh.exec_command('ls -lt ~/.openclaw/openclaw.json.backup* | head -5')
backups = stdout.read().decode('utf-8', errors='ignore')
print(backups)
print()

# 2. 对比配置变更
print("[2] 查看最新的备份和当前配置的差异...")
stdin, stdout, stderr = ssh.exec_command('diff -u ~/.openclaw/openclaw.json.backup-$(ls -t ~/.openclaw/openclaw.json.backup* | head -1 | sed "s/.*openclaw.json.backup-//") ~/.openclaw/openclaw.json 2>/dev/null | head -50 || echo "无法对比"')
diff = stdout.read().decode('utf-8', errors='ignore')
print(diff)
print()

# 3. 检查当前skills配置
print("[3] 当前 skills.entries 配置...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | grep -A 50 \'"skills"\' | grep -A 50 \'"entries"\'')
skills_config = stdout.read().decode('utf-8', errors='ignore')
print(skills_config)
print()

print("=" * 70)
ssh.close()

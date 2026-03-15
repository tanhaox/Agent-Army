#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复配置"""
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
print("  恢复 openclaw.json 配置")
print("=" * 70)
print()

# 恢复备份
print("[1/2] 恢复到修改前的配置...")
stdin, stdout, stderr = ssh.exec_command('cp ~/.openclaw/openclaw.json.backup-20260313-023940 ~/.openclaw/openclaw.json')
stdout.read()
print("   ✅ 配置已恢复")
print()

# 验证
print("[2/2] 验证恢复...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | tail -10')
tail = stdout.read().decode('utf-8', errors='ignore')
print(tail)
print()

print("=" * 70)
print("  ✅ 配置已恢复到修改前状态")
print("=" * 70)
print()
print("注意: yahoo-finance-claude skill 文件仍在 ~/.openclaw/workspace/skills/ 目录中")
print("只是配置文件没有修改")
print()

ssh.close()

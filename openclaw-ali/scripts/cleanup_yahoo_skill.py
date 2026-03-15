#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除skill文件，完全恢复"""
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
print("  删除 yahoo-finance 相关文件")
print("=" * 70)
print()

# 删除workspace中的skill
print("[1/3] 删除 workspace/skills/yahoo-finance-claude/...")
stdin, stdout, stderr = ssh.exec_command('rm -rf ~/.openclaw/workspace/skills/yahoo-finance-claude')
stdout.read()
print("   ✅ 已删除")
print()

# 删除skills目录中的两个skill
print("[2/3] 删除 skills/yahoo-finance-claude/...")
stdin, stdout, stderr = ssh.exec_command('rm -rf ~/.openclaw/skills/yahoo-finance-claude')
stdout.read()
print("   ✅ 已删除")
print()

# 删除skills目录中的旧yahoo-finance
print("[3/3] 删除 skills/yahoo-finance/...")
stdin, stdout, stderr = ssh.exec_command('rm -rf ~/.openclaw/skills/yahoo-finance')
stdout.read()
print("   ✅ 已删除")
print()

# 验证
print("验证清理结果...")
stdin, stdout, stderr = ssh.exec_command('ls ~/.openclaw/skills/ && echo "---" && ls ~/.openclaw/workspace/skills/ 2>/dev/null | grep -i yahoo || echo "  无yahoo相关skill"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)
print()

print("=" * 70)
print("  ✅ 已完全清理 yahoo-finance 相关文件")
print("=" * 70)

ssh.close()

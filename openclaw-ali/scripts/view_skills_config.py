#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看skills完整配置"""
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
print("  skills 配置部分")
print("=" * 70)
print()

stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json | grep -A 200 \'"skills"\'')
config = stdout.read().decode('utf-8', errors='ignore')
print(config)
print()

print("=" * 70)
ssh.close()

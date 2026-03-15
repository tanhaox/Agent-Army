#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看_meta.json格式"""
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
print("  _meta.json 和 .clawhub/origin.json 格式")
print("=" * 70)
print()

print("[1] self-improving-agent/_meta.json:")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/workspace/skills/self-improving-agent/_meta.json')
meta1 = stdout.read().decode('utf-8', errors='ignore')
print(meta1)
print()

print("[2] .clawhub/origin.json:")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/workspace/skills/self-improving-agent/.clawhub/origin.json')
origin1 = stdout.read().decode('utf-8', errors='ignore')
print(origin1)
print()

print("[3] a-share-real-time-data/_meta.json:")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/workspace/skills/a-share-real-time-data/_meta.json')
meta2 = stdout.read().decode('utf-8', errors='ignore')
print(meta2)
print()

print("=" * 70)
ssh.close()

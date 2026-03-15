#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload skill files to server"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

LOCAL_SKILL = Path(__file__).parent.parent / "skills" / "eastmoney-sector-crawler"
REMOTE_SKILL = "/root/openclaw-ali/skills/eastmoney-sector-crawler"

print("=" * 70)
print("  Upload Skill Files")
print("=" * 70)
print()

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
sftp = ssh.open_sftp()

try:
    # Files to upload
    files = [
        "_meta.json",
        "SKILL.md",
        "main.py",
        "tool.py",
        ".clawhub/origin.json"
    ]

    print(f"Local: {LOCAL_SKILL}")
    print(f"Remote: {REMOTE_SKILL}")
    print()

    for file in files:
        local_path = str(LOCAL_SKILL / file)
        remote_path = f"{REMOTE_SKILL}/{file}"

        # Read local file
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Write to remote
        try:
            with sftp.file(remote_path, 'w') as f:
                f.write(content)
            print(f"✓ {file}")
        except Exception as e:
            print(f"✗ {file}: {e}")

    print()
    print("Verification:")
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {REMOTE_SKILL}/")
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)

finally:
    sftp.close()
    ssh.close()

print()
print("=" * 70)
print("✓ Upload Complete!")
print("=" * 70)

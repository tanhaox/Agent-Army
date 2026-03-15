#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check and fix server directory structure"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  Check Server Directory Structure")
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

# Check openclaw-ali directory
print("[Step 1] Checking /root/openclaw-ali directory...")
stdin, stdout, stderr = ssh.exec_command("ls -la /root/openclaw-ali/")
result = stdout.read().decode('utf-8', errors='ignore')
print(result)
print()

# Check skills directory
print("[Step 2] Checking /root/openclaw-ali/skills directory...")
stdin, stdout, stderr = ssh.exec_command("ls -la /root/openclaw-ali/skills/")
result = stdout.read().decode('utf-8', errors='ignore')
print(result)
print()

# Check if sector crawler directory exists
print("[Step 3] Checking eastmoney-sector-crawler directory...")
stdin, stdout, stderr = ssh.exec_command("ls -la /root/openclaw-ali/skills/eastmoney-sector-crawler/")
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
if result:
    print(result)
if error:
    print(f"Error: {error}")
print()

# Create directory if needed
print("[Step 4] Creating directory structure...")
stdin, stdout, stderr = ssh.exec_command("mkdir -p /root/openclaw-ali/skills/eastmoney-sector-crawler/.clawhub")
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
if error and 'cannot create' in error.lower():
    print(f"✗ Failed to create directory: {error}")
else:
    print("✓ Directory structure ready")
print()

# Verify
print("[Step 5] Final verification...")
stdin, stdout, stderr = ssh.exec_command("ls -la /root/openclaw-ali/skills/eastmoney-sector-crawler/")
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

ssh.close()
print()
print("=" * 70)

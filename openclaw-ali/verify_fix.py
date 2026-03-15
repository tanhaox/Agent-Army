#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("Verifying gateway status...")

# Check port
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port_status = stdout.read().decode('utf-8', errors='ignore')
print(f"\nPort 18789: {'OK - Listening' if '18789' in port_status else 'FAIL'}")

# Check config
print("\nTrusted proxies config:")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 trustedProxies')
print(stdout.read().decode('utf-8', errors='ignore'))

# Get token
import json
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" READY! Try accessing now:")
print("=" * 60)
print(f"\nHTTPS URL:")
print(f"  https://112.126.61.223/#token={token}")
print(f"\nHTTP URL (backup):")
print(f"  http://112.126.61.223:18789/#token={token}")

ssh.close()

#!/usr/bin/env python3
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("Regenerating token...")

# Get new dashboard URL with token
stdin, stdout, stderr = ssh.exec_command('openclaw dashboard --no-open', get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# Extract token from new URL or config
import json
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" NEW TOKEN GENERATED")
print("=" * 60)
print(f"\nNew Token: {token}")
print(f"\nHTTPS URL:")
print(f"  https://112.126.61.223/#token={token}")
print(f"\nHTTP URL:")
print(f"  http://112.126.61.223:18789/#token={token}")

ssh.close()

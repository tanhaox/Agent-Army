#!/usr/bin/env python3
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("Checking device pairing...")

# List devices
stdin, stdout, stderr = ssh.exec_command('openclaw devices list', get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# Get current token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print(f"\nCurrent token: {token}")
print(f"\nURL: https://112.126.61.223/#token={token}")

# Check paired devices
print("\nChecking paired devices...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/devices/paired.json 2>/dev/null | head -50')
paired = stdout.read().decode('utf-8', errors='ignore')
if paired.strip():
    print(paired)
else:
    print("No paired devices found")

ssh.close()

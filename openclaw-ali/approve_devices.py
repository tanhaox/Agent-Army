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

print("Approving all pending devices...")

# Approve the recent requests
requests = [
    'af38702a-5da9-4954-9016-c6e6eb376267',
    '591ad08c-5c11-488f-ad48-306a5ce46762'
]

for req_id in requests:
    print(f"\nApproving: {req_id}")
    stdin, stdout, stderr = ssh.exec_command(f'openclaw devices approve {req_id}', get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output)

# Verify
print("\n\nVerifying...")
stdin, stdout, stderr = ssh.exec_command('openclaw devices list', get_pty=True)
print(stdout.read().decode('utf-8', errors='ignore'))

# Get token
import json
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print(f"\n✓ Done!")
print(f"\nToken: {token}")
print(f"\nURL:")
print(f"  https://112.126.61.223/#token={token}")

ssh.close()

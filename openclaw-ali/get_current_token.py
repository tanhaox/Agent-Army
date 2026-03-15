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

print("Getting current token...")

# Get token from config
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# Try different paths for token
token = config.get('gateway', {}).get('auth', {}).get('token', '')

if not token:
    # Try getting dashboard URL
    stdin, stdout, stderr = ssh.exec_command('openclaw dashboard --no-open', get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output)

    # Extract token from URL if available
    if 'token=' in output:
        import re
        match = re.search(r'token=([a-f0-9]+)', output)
        if match:
            token = match.group(1)

if token:
    print("\n" + "=" * 60)
    print(" Current Token Info")
    print("=" * 60)
    print(f"\nToken: {token}")
    print(f"\nMobile HTTPS URL:")
    print(f"  https://112.126.61.223/#token={token}")
    print(f"\nHTTP URL:")
    print(f"  http://112.126.61.223:18789/#token={token}")

    # Save to file
    with open('C:/AI-Agent-Local/openclaw-ali/current_url.txt', 'w') as f:
        f.write(f"Token: {token}\n")
        f.write(f"HTTPS: https://112.126.61.223/#token={token}\n")
        f.write(f"HTTP: http://112.126.61.223:18789/#token={token}\n")

    print("\n✓ Saved to: C:\\AI-Agent-Local\\openclaw-ali\\current_url.txt")
else:
    print("\n✗ No token found. Generating new one...")
    stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.auth.token $(openssl rand -hex 32)', get_pty=True)
    stdout.read()

    # Get new token
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
    config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
    token = config.get('gateway', {}).get('auth', {}).get('token', '')

    if token:
        print(f"\nNew token: {token}")
        print(f"\nURL:")
        print(f"  https://112.126.61.223/#token={token}")

ssh.close()

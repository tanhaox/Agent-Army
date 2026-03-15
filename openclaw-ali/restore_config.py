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

print("Restoring config and restarting...")

# Restore from backup
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json.bak.4 /root/.openclaw/openclaw.json', get_pty=True)
stdout.read()

# Fix allowedOrigins for HTTPS
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.controlUi.allowedOrigins "[\\"*\\"]"', get_pty=True)
stdout.read()

# Start gateway
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(5)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("✓ Gateway is running on 0.0.0.0:18789")
    print("\nAccess URLs:")
    print("  HTTPS: https://112.126.61.223/#token=b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
    print("  HTTP:  http://112.126.61.223:18789/#token=b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
else:
    print("✗ Failed. Checking log...")
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/gateway.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

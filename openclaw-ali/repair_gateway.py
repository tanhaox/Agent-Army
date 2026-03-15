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

print("Reparing Gateway...")

# 1. Fix config using openclaw doctor
print("\n[1] Running openclaw doctor --fix...")
stdin, stdout, stderr = ssh.exec_command('openclaw doctor --fix', get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output[:500] if len(output) > 500 else output)

# 2. Set allowedOrigins
print("\n[2] Setting allowedOrigins...")
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.controlUi.allowedOrigins "[\\"*\\"]"', get_pty=True)
stdout.read()

# 3. Start gateway
print("\n[3] Starting gateway...")
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(5)

# 4. Check status
print("\n[4] Checking status...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port_status = stdout.read().decode('utf-8', errors='ignore')
print(f"Port 18789: {'OK' if '18789' in port_status else 'NOT listening'}")

if '18789' in port_status:
    print("\n✓ Gateway is running!")
    print("\nAccess URLs:")
    print("  HTTPS: https://112.126.61.223/#token=b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
    print("  HTTP:  http://112.126.61.223:18789/#token=b65090c779a6fb8d11b4f39db2028fb8ec893d5b04f65359")
else:
    print("\n✗ Gateway failed to start")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway.log')
    print("Log:", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

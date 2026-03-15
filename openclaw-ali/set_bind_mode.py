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

print("Setting gateway bind mode...")

# Set bind in config
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.bind lan', get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# Kill and restart
print("\nRestarting gateway...")
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw', get_pty=True)
stdout.read()

import time
time.sleep(2)

# Start with lan mode
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

time.sleep(8)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

print("\nPort status:")
print(result)

if '0.0.0.0:18789' in result:
    print("\n✓ SUCCESS! Public access enabled")
    print("\nHTTPS URL:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
elif '127.0.0.1:18789' in result:
    print("\n⚠️  Still localhost. Checking config...")
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 gateway')
    print(stdout.read().decode('utf-8', errors='ignore'))
else:
    print("\n✗ Not running. Checking log...")
    stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/gateway.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

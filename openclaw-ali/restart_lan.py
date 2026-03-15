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

print("Restarting gateway with --bind lan...")

# Kill all
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw', get_pty=True)
stdout.read()

import time
time.sleep(2)

# Start with LAN bind
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

time.sleep(8)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

print("\nPort status:")
print(result)

if '0.0.0.0:18789' in result:
    print("\n✓ SUCCESS! Gateway on 0.0.0.0:18789 (public access)")
    print("\nAccess now:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
elif '127.0.0.1:18789' in result:
    print("\n⚠️  Still on localhost. Checking config...")
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 2 gateway | grep bind')
    print(stdout.read().decode('utf-8', errors='ignore'))
else:
    print("\n✗ Not listening")

ssh.close()

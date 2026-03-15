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

# Kill all and check config
print("Checking config file...")
stdin, stdout, stderr = ssh.exec_command('openclaw doctor 2>&1 | head -50')
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

print("\n" + "="*60)
print("Killing old processes and restarting...")
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw; sleep 2', get_pty=True)
stdout.read()

# Start with explicit bind
print("\nStarting gateway...")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway --bind lan 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(8)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("\n✓ SUCCESS - Gateway is running!")
    print(result)
    print("\nAccess:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
else:
    print("\n✗ Still not running")
    stdin, stdout, stderr = ssh.exec_command('tail -50 /tmp/openclaw/openclaw-*.log')
    print("\nLatest log:")
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

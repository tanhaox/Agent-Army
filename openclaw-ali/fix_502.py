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

print("Diagnosing 502 error...")

# Check process
print("\n[1] Checking gateway process...")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[o]penclaw.*gateway"')
proc = stdout.read().decode('utf-8', errors='ignore')
if proc.strip():
    print("Running:", proc)
else:
    print("NOT running")

# Check port
print("\n[2] Checking port 18789...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
port = stdout.read().decode('utf-8', errors='ignore')
if port.strip():
    print("Listening:", port)
else:
    print("NOT listening")

# Check log
print("\n[3] Checking gateway log...")
stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -20')
log = stdout.read().decode('utf-8', errors='ignore')
print(log[-500:] if len(log) > 500 else log)

# Start gateway
print("\n[4] Starting gateway...")
stdin, stdout, stderr = ssh.exec_command('cd /root && openclaw gateway --bind lan > /tmp/gateway-start.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(8)

# Verify
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("\n✓ Gateway started successfully!")
    print("\nAccess now:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
else:
    print("\n✗ Failed to start")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway-start.log')
    print("Error log:")
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

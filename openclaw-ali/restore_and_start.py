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

print("Restoring from backup...")

# Find a good backup
stdin, stdout, stderr = ssh.exec_command('ls -lt /root/.openclaw/openclaw.json.bak* | head -5')
backups = stdout.read().decode('utf-8', errors='ignore')
print("Available backups:")
print(backups)

# Use the oldest backup (before our edits)
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json.bak.4 /root/.openclaw/openclaw.json', get_pty=True)
stdout.read()

print("\n✓ Config restored")

# Set allowedOrigins properly
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.controlUi.allowedOrigins "[\\"*\\"]"', get_pty=True)
stdout.read()

print("✓ allowedOrigins set")

# Start gateway
print("\nStarting gateway...")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway --bind lan &', get_pty=True)
stdout.read()

import time
time.sleep(8)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("\n✓ SUCCESS!")
    print(result)
    print("\nAccess now:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
else:
    print("\n✗ Check log:")
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw/openclaw-*.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

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

print("=" * 60)
print(" Complete OpenClaw Setup")
print("=" * 60)

# Step 1: Kill everything
print("\n[1/5] Cleaning up...")
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw', get_pty=True)
stdout.read()
print("✓ Killed all OpenClaw processes")

# Step 2: Get oldest backup (before our edits)
print("\n[2/5] Restoring clean config...")
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json.bak.4 /root/.openclaw/openclaw.json', get_pty=True)
stdout.read()
print("✓ Restored from bak.4")

# Step 3: Configure using OpenClaw CLI
print("\n[3/5] Configuring gateway...")
stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.bind lan', get_pty=True)
stdout.read()

stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.controlUi.allowedOrigins "[\\"*\\"]"', get_pty=True)
stdout.read()

stdin, stdout, stderr = ssh.exec_command('openclaw config set gateway.trustedProxies "[\\"127.0.0.1\\",\\"::1\\"]"', get_pty=True)
stdout.read()
print("✓ Config updated")

# Step 4: Verify config
print("\n[4/5] Verifying config...")
stdin, stdout, stderr = ssh.exec_command('openclaw doctor 2>&1 | head -20')
output = stdout.read().decode('utf-8', errors='ignore')
print(output[:500] if len(output) > 500 else output)

# Step 5: Start gateway
print("\n[5/5] Starting gateway...")
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway > /tmp/gateway-start.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(10)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "18789|443"')
result = stdout.read().decode('utf-8', errors='ignore')

print("\n" + "=" * 60)
print(" Status Check")
print("=" * 60)
print(result)

if '0.0.0.0:18789' in result:
    print("\n✓ SUCCESS!")
    print("\n📱 Mobile HTTPS Access:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
elif '127.0.0.1:18789' in result:
    print("\n⚠️  Gateway on localhost only")
    print("  nginx will fail with 502")
    print("\nTrying manual start with --bind lan...")
    stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw; sleep 2; openclaw gateway --bind lan &', get_pty=True)
    stdout.read()
    time.sleep(10)

    stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
    result = stdout.read().decode('utf-8', errors='ignore')

    if '0.0.0.0:18789' in result:
        print("\n✓ NOW on 0.0.0.0:18789!")
        print("\nAccess:")
        print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
    else:
        print("\n✗ Still failing. Checking startup log...")
        stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway-start.log')
        print(stdout.read().decode('utf-8', errors='ignore')[:500])
else:
    print("\n✗ Gateway not running")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway-start.log')
    print("\nError log:")
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

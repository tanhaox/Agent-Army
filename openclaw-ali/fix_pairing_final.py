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

print("Configuring trusted proxies for HTTPS...")

# Read config
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# Add trustedProxies
if 'gateway' not in config:
    config['gateway'] = {}
config['gateway']['trustedProxies'] = ['127.0.0.1', '::1']

# Add allowedOrigins for HTTPS
if 'controlUi' not in config['gateway']:
    config['gateway']['controlUi'] = {}
config['gateway']['controlUi']['allowedOrigins'] = ['*']

# Write back
config_json = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(config_json.encode('utf-8'))
stdin.close()

print("Config updated. Restarting gateway...")

# Restart gateway
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw-gateway; sleep 2; nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(5)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("✓ Gateway restarted")
    print("\nNow try accessing:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
else:
    print("✗ Failed")
    stdin, stdout, stderr = ssh.exec_command('tail -20 /tmp/openclaw/openclaw-*.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

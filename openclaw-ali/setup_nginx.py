#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" Complete HTTPS Setup")
print("=" * 60)

# Create SSL cert
print("\n[1] Create SSL certificate")
stdin, stdout, stderr = ssh.exec_command('mkdir -p /etc/nginx/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/openclaw.key -out /etc/nginx/ssl/openclaw.crt 2>&1 | tail -5')
print(stdout.read().decode('utf-8', errors='ignore') or "OK")

# Create nginx config
print("\n[2] Create nginx config")
nginx_config = '''server {
    listen 443 ssl;
    server_name 112.126.61.223;

    ssl_certificate /etc/nginx/ssl/openclaw.crt;
    ssl_certificate_key /etc/nginx/ssl/openclaw.key;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
'''

stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/openclaw', get_pty=True)
stdin.write(nginx_config + '\n')
stdin.close()
print("OK")

# Enable site
print("\n[3] Enable nginx site")
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/')
stdout.read()

# Test and reload
print("\n[4] Test and reload nginx")
stdin, stdout, stderr = ssh.exec_command('nginx -t')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

if 'syntax is ok' in result or 'successful' in result:
    stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
    stdout.read()
    print("nginx reloaded")
else:
    print("nginx config test failed!")

# Configure trustedProxies
print("\n[5] Configure OpenClaw trustedProxies")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

config.setdefault('gateway', {})['trustedProxies'] = ['127.0.0.1', '::1']

new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("OK")

# Restart Gateway
print("\n[6] Restart Gateway")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
print(stdout.read().decode('utf-8', errors='ignore'))

# Wait
time.sleep(3)

# Check ports
print("\n[7] Check ports")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "(443|18789)"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# Get token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" Configuration Complete!")
print("=" * 60)

print("\nNext steps:")
print("1. Open port 443 in Aliyun security group")
print(f"2. Visit: https://112.126.61.223/#token={token}")
print(f"3. Token: {token}")

ssh.close()

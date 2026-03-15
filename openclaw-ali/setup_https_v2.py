#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" Configure HTTPS for Mobile Access")
print("=" * 60)

# Step 1: Install nginx
print("\n[Step 1/5] Install nginx")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('apt update && apt install -y nginx')
stdout.read()
print("OK")

# Step 2: Create SSL certificate
print("\n[Step 2/5] Create self-signed SSL certificate")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('mkdir -p /etc/nginx/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/openclaw.key -out /etc/nginx/ssl/openclaw.crt')
stdout.read()
print("OK")

# Step 3: Configure nginx
print("\n[Step 3/5] Configure nginx reverse proxy")
print("-" * 60)
nginx_config = '''server {
    listen 443 ssl;
    server_name 112.126.61.223;

    ssl_certificate /etc/nginx/ssl/openclaw.crt;
    ssl_certificate_key /etc/nginx/ssl/openclaw.key;

    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
'''

stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/openclaw', get_pty=True)
stdin.write(nginx_config + '\n')
stdin.close()
print("OK")

# Step 4: Enable nginx config
print("\n[Step 4/5] Enable nginx config")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx')
stdout.read()
print("OK")

# Step 5: Configure OpenClaw trustedProxies
print("\n[Step 5/5] Configure OpenClaw trustedProxies")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

config.setdefault('gateway', {})['trustedProxies'] = ['127.0.0.1', '::1']

new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("OK")

# Restart Gateway
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
stdout.read()

# Wait
import time
time.sleep(3)

# Get token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

# Check nginx
stdin, stdout, stderr = ssh.exec_command('systemctl is-active nginx')
nginx_active = stdout.read().decode('utf-8', errors='ignore').strip()

print("\n" + "=" * 60)
print(" HTTPS Configuration Complete!")
print("=" * 60)

if nginx_active == 'active':
    print("\nnginx status: active")
else:
    print("\nnginx status: unknown")

print("\nHTTPS URL (for mobile):")
print(f"   https://112.126.61.223/#token={token}")

print("\nToken:")
print(f"   {token}")

print("\nImportant:")
print("   1. Open port 443 in Aliyun security group")
print("   2. First visit will show certificate warning")
print("   3. Click Advanced -> Continue to proceed")

print("\nMobile access steps:")
print("   1. Open port 443 in security group")
print("   2. Visit: https://112.126.61.223/")
print("   3. Accept certificate warning")
print("   4. Enter token")

ssh.close()

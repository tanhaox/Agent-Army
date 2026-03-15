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

print("=" * 60)
print(" HTTPS Setup - Final")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# Step by step
print("\n[1] SSL cert")
stdin, stdout, stderr = ssh.exec_command('mkdir -p /etc/nginx/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/openclaw.key -out /etc/nginx/ssl/openclaw.crt', get_pty=True)
stdout.read()
print("OK")

print("\n[2] nginx config")
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
    }
}
'''
stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/openclaw')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/')
stdout.read()
print("OK")

print("\n[3] Test nginx")
stdin, stdout, stderr = ssh.exec_command('nginx -t')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[4] Reload nginx")
stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[5] trustedProxies")
stdin, stdout, stderr = ssh.exec_command("cat /root/.openclaw/openclaw.json | python3 -c \"import sys,json; c=json.load(sys.stdin); c.setdefault('gateway', {})['trustedProxies']=['127.0.0.1','::1']; print(json.dumps(c,indent=2))\" | tee /root/.openclaw/openclaw.json")
stdout.read()
print("OK")

print("\n[6] Restart Gateway")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
print(stdout.read().decode('utf-8', errors='ignore'))

time.sleep(3)

print("\n[7] Check ports")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E \"(443|18789)\"')
print(stdout.read().decode('utf-8', errors='ignore'))

# Get token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" HTTPS Ready!")
print("=" * 60)
print(f"\nHTTPS URL:")
print(f"  https://112.126.61.223/#token={token}")
print(f"\nToken: {token}")
print(f"\nNext: Open port 443 in Aliyun security group!")

ssh.close()

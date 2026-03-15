#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("Creating nginx configuration...")

# Create config via heredoc
cmd = '''cat > /etc/nginx/sites-available/openclaw << 'NGINXCONFIG'
server {
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
NGINXCONFIG'''

stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
stdout.read()
print("Config created")

# Enable site
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/')
stdout.read()
print("Site enabled")

# Test
stdin, stdout, stderr = ssh.exec_command('nginx -t')
result = stdout.read().decode('utf-8', errors='ignore')
print("Test:", result)

# Reload
stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
stdout.read()
print("nginx reloaded")

# Check ports
print("\nPort status:")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "(443|80|18789)"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

if ':443' in result:
    print("\n✅ HTTPS is ready!")
else:
    print("\n❌ Port 443 not listening yet")
    print("Check: nginx error log")
    stdin, stdout, stderr = ssh.exec_command('tail -20 /var/log/nginx/error.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

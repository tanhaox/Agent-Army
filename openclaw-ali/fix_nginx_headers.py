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

# Create proper nginx config with proxy headers
nginx_config = """server {
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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
"""

# Write config
stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/openclaw', get_pty=True)
stdin.write(nginx_config.encode('utf-8'))
stdin.close()

# Ensure site is enabled
stdin, stdout, stderr = ssh.exec_command('ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/', get_pty=True)
stdout.read()

# Test and reload nginx
stdin, stdout, stderr = ssh.exec_command('nginx -t && systemctl reload nginx', get_pty=True)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

print("\n✓ nginx config updated with proxy headers")

# Restart gateway
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw-gateway; sleep 2; nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &', get_pty=True)
stdout.read()

import time
time.sleep(5)

# Check
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "443|18789"')
result = stdout.read().decode('utf-8', errors='ignore')
print("\nPort status:")
print(result)

print("\n✓ Done! Now try accessing:")
print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")

ssh.close()

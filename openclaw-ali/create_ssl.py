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

print("Creating SSL certificate...")

# Create directory and cert
stdin, stdout, stderr = ssh.exec_command('mkdir -p /etc/nginx/ssl', get_pty=True)
stdout.read()

# Create certificate
stdin, stdout, stderr = ssh.exec_command('openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/openclaw.key -out /etc/nginx/ssl/openclaw.crt', get_pty=True)
output = stdout.read()
error = stderr.read()
if output:
    print(output)
if error and 'error' not in error.lower():
    print("Error:", error)

# Verify files exist
print("\nVerifying certificate files...")
stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/ssl/')
print(stdout.read().decode('utf-8', errors='ignore'))

# Test nginx
print("\nTesting nginx config...")
stdin, stdout, stderr = ssh.exec_command('nginx -t')
print(stdout.read().decode('utf-8', errors='ignore'))

# Restart nginx
print("\nRestarting nginx...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart nginx')
print(stdout.read().decode('utf-8', errors='ignore'))

# Check ports
print("\nPort status:")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "443"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result if result else "443 not listening")

if ':443' in result:
    print("\n✅ SUCCESS! HTTPS is ready!")
else:
    print("\n❌ Checking error log...")
    stdin, stdout, stderr = ssh.exec_command('tail -10 /var/log/nginx/error.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

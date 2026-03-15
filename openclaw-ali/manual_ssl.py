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

print("Generating SSL certificate manually...")

# Use yes stdin for openssl
stdin, stdout, stderr = ssh.exec_command('cd /etc/nginx/ssl && openssl req -x509 -newkey rsa:2048 -nodes -keyout openclaw.key -out openclaw.crt -subj "/CN=112.126.61.223" -days 365', get_pty=True)
output = stdout.read()
error = stderr.read()

print(output)
if error.strip() and 'error' not in error.lower():
    print("Errors:", error)

# Verify
print("\nVerifying files...")
stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/ssl/openclaw.*')
print(stdout.read().decode('utf-8', errors='ignore'))

# Restart nginx
print("\nRestarting nginx...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart nginx')
print(stdout.read().decode('utf-8', errors='ignore'))

# Check port
print("\nChecking port 443...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep ":443"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result if result else "Not listening")

if ':443' in result:
    print("\n✅ HTTPS READY!")
    print("\nNext steps:")
    print("1. Open port 443 in Aliyun security group")
    print("2. Visit: https://112.126.61.223/")
else:
    print("\n❌ Port 443 not ready, checking logs...")
    stdin, stdout, stderr = ssh.exec_command('tail -5 /var/log/nginx/error.log')
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

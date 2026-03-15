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

# Check if apt is running
stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[a]pt"')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("apt is still running, installing nginx...")
    print(result)
else:
    print("apt install completed")

# Check nginx
print("\nChecking nginx...")
stdin, stdout, stderr = ssh.exec_command('which nginx && nginx -v')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("nginx installed:")
    print(result)
else:
    print("nginx not found, still installing...")

# Check nginx status
print("\nChecking nginx status...")
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx | head -3')
print(stdout.read().decode('utf-8', errors='ignore'))

# Check ports
print("\nChecking ports...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep -E "(443|18789)"')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

key = paramiko.Ed25519Key.from_private_key_file(
    r"C:\Users\tanha\.ssh\digitalocean_openclaw",
    password="a19571004"
)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('157.245.195.58', 22, 'root', pkey=key, timeout=15)

print('=== 1. OpenClaw进程 ===')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep openclaw | grep -v grep')
print(stdout.read().decode().strip())

print()
print('=== 2. 监听端口 ===')
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep -E "18789|18730"')
ports = stdout.read().decode().strip()
if ports:
    print(ports)
else:
    print('无监听端口')

print()
print('=== 3. 测试API ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:18789/health 2>&1')
print(stdout.read().decode().strip())

print()
print('=== 4. 记忆API (18888) ===')
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep 18888')
api_port = stdout.read().decode().strip()
if api_port:
    print(api_port)
else:
    print('18888未监听')

ssh.close()

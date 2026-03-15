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

print("服务器当前监听的端口:")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep LISTEN')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n既然 22 端口能连接，说明安全组已经开放了 22。")
print("你需要用同样的方式添加 18789 端口。")

ssh.close()

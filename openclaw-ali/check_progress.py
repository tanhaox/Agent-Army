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

# 检查npm进程
print("[检查] npm install 进程...")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "[n]pm|[n]ode"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查openclaw是否已安装
print("\n[检查] openclaw 命令...")
stdin, stdout, stderr = ssh.exec_command('which openclaw || echo "尚未安装"')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

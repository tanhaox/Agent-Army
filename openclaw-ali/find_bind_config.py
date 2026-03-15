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

print("=" * 60)
print(" 查找 Gateway 绑定配置方式")
print("=" * 60)

# 查看帮助
print("\n[1] Gateway 帮助")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw gateway --help')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看环境变量相关
print("\n[2] 查看所有配置选项")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw config --help')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看当前完整配置
print("\n[3] 当前完整配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

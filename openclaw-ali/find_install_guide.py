#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw安装说明"""
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
print(" OpenClaw-CN 安装指南")
print("=" * 60)

# 查看install目录
print("\n[install 目录内容]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/openclaw-cn/install/')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看是否有install.sh
print("\n[检查安装脚本]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('find /root/openclaw-cn -name "*.sh" -type f | grep -i install | head -20')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看中文文档
print("\n[中文文档目录]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/openclaw-cn/zh-CN/')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看主要README（中文）
print("\n[中文 README]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/openclaw-cn/zh-CN/README.md | head -200')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看安装文档"""
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
print(" OpenClaw-CN 快速安装指南")
print("=" * 60)

# 查看快速安装文档
print("\n[docker-quick.md - Docker快速安装]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/openclaw-cn/install/docker-quick.md')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n\n[installer.md - 安装程序]")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/openclaw-cn/install/installer.md')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

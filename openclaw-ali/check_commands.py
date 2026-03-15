#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw可用命令"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

print("=" * 60)
print(" 服务器 OpenClaw 配置指南")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("\n[1] 查看项目结构")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/openclaw-cn/')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[2] 查看package.json中的scripts")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/openclaw-cn/package.json | grep -A 50 "scripts"')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n[3] 查看README文件")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/openclaw-cn/README.md | head -100')
print(stdout.read().decode('utf-8', errors='ignore'))

print("\n" + "=" * 60)
print(" 配置准备完成")
print("=" * 60)

print("\n下一步操作:")
print("1. 登录服务器: ssh root@112.126.61.223")
print("2. 进入目录: cd /root/openclaw-cn")
print("3. 运行初始化: 根据README中的说明操作")

ssh.close()

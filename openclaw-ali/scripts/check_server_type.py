#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查服务器类型"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

print("=" * 70)
print("  检查服务器类型")
print("=" * 70)
print()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=15)

print(f"当前连接: 112.126.61.223")
print()

# 检查是否有 dandanyi 文件夹
print("检查 /var/www/ 目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/ 2>/dev/null')
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# 检查根目录
print("检查根目录...")
stdin, stdout, stderr = ssh.exec_command('ls -la /root/ | grep -i dandanyi')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip():
    print(f"✅ 找到 dandanyi 相关:\n{output}")
    print()
    print(">>> 这是阿里云服务器（有dandanyi文件夹）<<<")
else:
    print("❌ 未找到 dandanyi 文件夹")
    print()
    print(">>> 这是新加坡服务器（没有dandanyi文件夹）<<<")

ssh.close()
print()
print("=" * 70)

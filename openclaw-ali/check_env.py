#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查服务器环境"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

print("=" * 60)
print(" 服务器环境检查")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# 检查 Node.js
print("\n[1] Node.js 版本:")
stdin, stdout, stderr = ssh.exec_command('node --version')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查 npm
print("\n[2] npm 版本:")
stdin, stdout, stderr = ssh.exec_command('npm --version')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查 pnpm
print("\n[3] pnpm 版本:")
stdin, stdout, stderr = ssh.exec_command('pnpm --version 2>/dev/null || echo "未安装"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查 Docker
print("\n[4] Docker 版本:")
stdin, stdout, stderr = ssh.exec_command('docker --version')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查 Git
print("\n[5] Git 版本:")
stdin, stdout, stderr = ssh.exec_command('git --version')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查磁盘空间
print("\n[6] 磁盘空间:")
stdin, stdout, stderr = ssh.exec_command('df -h / | tail -1')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查内存
print("\n[7] 内存使用:")
stdin, stdout, stderr = ssh.exec_command('free -h | grep Mem')
print(stdout.read().decode('utf-8', errors='ignore').strip())

# 检查 CPU
print("\n[8] CPU 信息:")
stdin, stdout, stderr = ssh.exec_command('nproc')
print(f"CPU核心数: {stdout.read().decode('utf-8', errors='ignore').strip()}")

# 检查已安装的OpenClaw
print("\n[9] OpenClaw 安装状态:")
stdin, stdout, stderr = ssh.exec_command('ls -la /root/ 2>/dev/null | grep -i claw || echo "未找到OpenClaw目录"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

print("\n" + "=" * 60)
print(" 环境检查完成")
print("=" * 60)

ssh.close()

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
print(" 检查 Gateway 日志")
print("=" * 60)

# 检查日志文件
print("\n[1] 临时日志")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway.log 2>/dev/null || echo "无日志"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查 openclaw 日志目录
print("\n[2] OpenClaw 日志")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/.openclaw/logs/')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看最新的日志文件
print("\n[3] 最新日志内容")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('find /root/.openclaw/logs/ -name "*.log" -type f -exec tail -30 {} \\; 2>/dev/null | tail -50')
print(stdout.read().decode('utf-8', errors='ignore'))

# 直接运行 gateway 看输出
print("\n[4] 直接运行查看错误")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('timeout 5 openclaw gateway 2>&1 || true')
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print("STDOUT:", output)
print("STDERR:", error)

ssh.close()

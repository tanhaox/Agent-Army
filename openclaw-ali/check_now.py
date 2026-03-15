#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("等待 Gateway 启动...")
time.sleep(5)

# 检查端口
print("\n端口状态:")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
print(result if result.strip() else "仍未监听")

# 查看日志
print("\nGateway 日志:")
stdin, stdout, stderr = ssh.exec_command('cat /tmp/openclaw/openclaw-*.log 2>/dev/null | tail -30')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

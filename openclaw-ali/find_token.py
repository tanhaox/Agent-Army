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
print(" 查找 OpenClaw 令牌")
print("=" * 60)

# 检查配置目录
print("\n[1] 配置目录结构")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ls -la /root/.openclaw/')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查找 gateway 配置
print("\n[2] Gateway 配置文件")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/gateway.json 2>/dev/null || echo "未找到 gateway.json"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查找设备配置（通常包含令牌）
print("\n[3] 设备配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/devices.json 2>/dev/null || echo "未找到 devices.json"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查找令牌
print("\n[4] 搜索包含 token 的配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('grep -r "token" /root/.openclaw/ 2>/dev/null | head -20')
print(stdout.read().decode('utf-8', errors='ignore'))

# 查看所有配置文件
print("\n[5] 所有配置文件")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('find /root/.openclaw/ -type f -name "*.json"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 使用 openclaw 命令查看配置
print("\n[6] 使用 openclaw 命令查看")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw config get 2>&1 | head -50')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查 gateway 是否运行
print("\n[7] Gateway 运行状态")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "[o]penclaw|[g]ateway" | head -5')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print(result)
else:
    print("Gateway 未运行")

ssh.close()

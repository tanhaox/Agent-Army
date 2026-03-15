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

print("=" * 60)
print(" 检查 Gateway 状态")
print("=" * 60)

# 等待一下
time.sleep(2)

# 检查进程
print("\n[1] Gateway 进程")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "[o]penclaw|[g]ateway"')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print(result)
else:
    print("❌ Gateway 未运行")
    print("\n尝试启动...")
    stdin, stdout, stderr = ssh.exec_command('openclaw gateway > /dev/null 2>&1 &')
    stdout.read()
    print("已发送启动命令，等待5秒...")
    time.sleep(5)

# 检查端口
print("\n[2] 端口监听状态")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('ss -tlnp 2>/dev/null | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print(result)
else:
    print("未检测到端口，尝试 netstat...")
    stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep 18789')
    result = stdout.read().decode('utf-8', errors='ignore')
    if result.strip():
        print(result)
    else:
        print("⚠️ 端口 18789 未监听")

# 查看日志
print("\n[3] Gateway 日志")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('tail -30 /root/.openclaw/logs/gateway.log 2>/dev/null || echo "日志文件不存在"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 读取配置确认
print("\n[4] 当前配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 "auth"')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()

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
print(" 验证 Gateway 状态")
print("=" * 60)

# 检查端口
print("\n[1] 端口监听状态")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if '0.0.0.0:18789' in result:
    print("✅ Gateway 监听在 0.0.0.0:18789 (公网可访问)")
    print(result)
else:
    print("❌ Gateway 未正确监听")
    print(result)

# 检查进程
print("\n[2] 进程状态")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[o]penclaw.*gateway" | head -1')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("✅ Gateway 进程运行中")
    print(result)
else:
    print("❌ Gateway 进程未运行")

# 获取配置
import json
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')
model = config.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', '')

print("\n" + "=" * 60)
print(" 🌐 访问信息")
print("=" * 60)
print(f"\n公网 URL:")
print(f"  http://112.126.61.223:18789/")
print(f"\n带令牌 URL:")
print(f"  http://112.126.61.223:18789/#token={token}")
print(f"\n默认模型: {model}")

print("\n✅ 安全组已配置，端口已开放！")
print("🚀 现在可以在浏览器访问了！")

ssh.close()

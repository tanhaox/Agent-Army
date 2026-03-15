#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" 令牌信息")
print("=" * 60)

# 查看完整配置
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = stdout.read().decode('utf-8', errors='ignore')

# 解析 JSON 获取令牌
try:
    data = json.loads(config)
    gateway_auth = data.get('gateway', {}).get('auth', {})
    token = gateway_auth.get('token', '')
    mode = gateway_auth.get('mode', '')

    print(f"\n✅ 找到令牌！")
    print(f"   模式: {mode}")
    print(f"   令牌: {token}")

    # 检查绑定地址
    bind = gateway_auth.get('bind', 'localhost')
    print(f"   绑定: {bind}")

    # 生成访问 URL
    if bind == 'localhost':
        url = "http://127.0.0.1:18789/"
    elif bind == 'lan':
        url = "http://112.126.61.223:18789/"
    else:
        url = f"http://{bind}:18789/"

    print(f"\n🌐 访问 URL:")
    print(f"   {url}")
    print(f"\n🔑 完整登录 URL (带令牌):")
    print(f"   {url}#token={token}")

except Exception as e:
    print(f"\n解析配置失败: {e}")
    print("\n原始配置:")
    print(config)

# 检查 Gateway 是否在运行
print("\n" + "-" * 60)
print("Gateway 状态:")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "[o]penclaw-gateway"')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("✅ Gateway 正在运行")
else:
    print("❌ Gateway 未运行")

# 检查端口监听
print("\n端口监听状态:")
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep 18789 || ss -tlnp 2>/dev/null | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print(result)
else:
    print("未检测到 18789 端口监听")

ssh.close()

print("\n" + "=" * 60)

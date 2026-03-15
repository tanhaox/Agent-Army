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
print(" 🎉 OpenClaw Gateway 公网访问模式配置成功！")
print("=" * 60)

# 检查端口
print("\n[端口监听状态]")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

# 获取模型
model = config.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', 'unknown')

print("\n" + "=" * 60)
print(" 📋 访问信息")
print("=" * 60)

print(f"\n🌐 公网访问 URL:")
print(f"   http://112.126.61.223:18789/")

print(f"\n🔑 带令牌 URL（可直接访问）:")
print(f"   http://112.126.61.223:18789/#token={token}")

print(f"\n🤖 当前模型: {model}")

print(f"\n⚠️  重要提示:")
print(f"   1. 确保阿里云安全组已开放 TCP 端口 18789")
print(f"   2. 令牌认证已启用，访问时需要令牌")
print(f"   3. Gateway 进程 PID: 593126")

print(f"\n📝 管理命令:")
print(f"   查看状态: openclaw gateway status")
print(f"   重启: openclaw gateway restart")
print(f"   停止: openclaw gateway stop")

ssh.close()

# 创建快捷访问文件
with open(r'C:\AI-Agent-Local\openclaw-ali\访问URL.txt', 'w', encoding='utf-8') as f:
    f.write(f"OpenClaw Gateway 访问信息\n")
    f.write(f"=" * 50 + "\n\n")
    f.write(f"公网URL: http://112.126.61.223:18789/\n")
    f.write(f"令牌URL: http://112.126.61.223:18789/#token={token}\n\n")
    f.write(f"令牌: {token}\n")
    f.write(f"模型: {model}\n\n")
    f.write(f"配置时间: 2026-03-10\n")

print(f"\n📄 访问信息已保存到: C:\\AI-Agent-Local\\openclaw-ali\\访问URL.txt")

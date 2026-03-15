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
print(" 允许公网访问 Control UI")
print("=" * 60)

# 读取配置
print("\n[1] 读取当前配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 添加 allowedOrigins
print("\n[2] 添加 gateway.controlUi.allowedOrigins")
if 'controlUi' not in config.get('gateway', {}):
    config['gateway']['controlUi'] = {}
config['gateway']['controlUi']['allowedOrigins'] = ['*']  # 允许所有来源

# 写回配置
new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("✅ 配置已更新")

# 验证
print("\n[3] 验证配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 "controlUi"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 重启 Gateway
print("\n[4] 重启 Gateway")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 等待
import time
time.sleep(3)

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" ✅ Control UI 已允许公网访问")
print("=" * 60)
print(f"\n🌐 现在可以访问了:")
print(f"   http://112.126.61.223:18789/#token={token}")
print(f"\n🔑 令牌: {token}")

ssh.close()

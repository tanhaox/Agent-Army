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
print(" 修改默认模型为 zai/glm-4.7")
print("=" * 60)

# 读取配置
print("\n[1] 读取当前配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 显示当前模型
current_model = config.get('agents', {}).get('defaults', {}).get('model', {}).get('primary', '')
print(f"当前模型: {current_model}")

# 修改模型
print("\n[2] 修改为 zai/glm-4.7")
config['agents']['defaults']['model']['primary'] = 'zai/glm-4.7'

# 写回配置
new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("✅ 配置已更新")

# 验证
print("\n[3] 验证配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 "model" | head -15')
print(stdout.read().decode('utf-8', errors='ignore'))

# 重启 Gateway 使配置生效
print("\n[4] 重启 Gateway")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
print(stdout.read().decode('utf-8', errors='ignore'))

# 等待重启
import time
time.sleep(3)

# 检查状态
print("\n[5] 检查 Gateway 状态")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("✅ Gateway 运行中")
    print(result)
else:
    print("⚠️  Gateway 未运行，手动启动...")
    stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &')
    stdout.read()

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" ✅ 模型已修改为 zai/glm-4.7")
print("=" * 60)
print(f"\n🌐 访问 URL: http://112.126.61.223:18789/")
print(f"🔑 令牌 URL: http://112.126.61.223:18789/#token={token}")
print(f"🤖 默认模型: zai/glm-4.7")

ssh.close()

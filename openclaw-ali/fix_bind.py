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
print(" 修改 Gateway 绑定为 LAN 模式")
print("=" * 60)

# 备份原配置
print("\n[1] 备份配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.backup')
stdout.read()
print("✅ 已备份到 openclaw.json.backup")

# 读取配置
print("\n[2] 读取配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config_str = stdout.read().decode('utf-8', errors='ignore')
config = json.loads(config_str)

# 显示当前配置
current_bind = config.get('gateway', {}).get('auth', {}).get('bind', 'unknown')
print(f"当前绑定: {current_bind}")

# 修改绑定
print("\n[3] 修改绑定为 lan")
print("-" * 60)
config['gateway']['auth']['bind'] = 'lan'

# 写入新配置
new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()

print("✅ 配置已更新")

# 重启 Gateway
print("\n[4] 重启 Gateway")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command("pkill -f openclaw-gateway && sleep 1 && openclaw gateway &")
stdout.read()
print("✅ Gateway 已重启")

# 等待启动
import time
time.sleep(3)

# 检查新状态
print("\n[5] 验证新配置")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp 2>/dev/null | grep 18789 || ss -tlnp 2>/dev/null | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

# 读取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" ✅ 配置完成！")
print("=" * 60)
print(f"\n🔑 令牌: {token}")
print(f"🌐 访问 URL: http://112.126.61.223:18789/")
print(f"🔐 完整 URL: http://112.126.61.223:18789/#token={token}")

ssh.close()

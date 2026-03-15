#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print(" 设置 Gateway 为 LAN 模式（公网可访问）")
print("=" * 60)

# 读取配置
print("\n[1] 读取当前配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 设置 gateway.bind
print("\n[2] 设置 gateway.bind = 'lan'")
config['gateway']['bind'] = 'lan'

# 写回配置
new_config = json.dumps(config, indent=2, ensure_ascii=False)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
print("✅ 配置已更新")

# 验证配置
print("\n[3] 验证配置")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 3 "gateway"')
print(stdout.read().decode('utf-8', errors='ignore'))

# 重启 Gateway
print("\n[4] 重启 Gateway")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('pkill -f "openclaw.*gateway"; sleep 2')
stdout.read()
print("✅ 旧进程已停止")

# 启动新 Gateway
stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway > /tmp/gateway.log 2>&1 &')
stdout.read()
print("✅ 新 Gateway 已启动")

# 等待启动
time.sleep(5)

# 检查端口
print("\n[5] 检查端口监听")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')
if result.strip():
    print("✅ 端口监听:")
    print(result)

    # 检查是否监听在 0.0.0.0
    if '0.0.0.0:18789' in result or ':::18789' in result:
        print("\n✅✅✅ 成功！Gateway 已绑定到所有网络接口（公网可访问）")
    else:
        print("\n⚠️ 仍然监听在 127.0.0.1，尝试用命令行参数启动...")
        # 用命令行参数强制 lan 模式
        stdin, stdout, stderr = ssh.exec_command('pkill -f "openclaw.*gateway"; sleep 1; nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &')
        stdout.read()
        time.sleep(5)
        stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
        result = stdout.read().decode('utf-8', errors='ignore')
        print(result)
else:
    print("❌ 端口未监听，查看日志:")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/gateway.log | tail -20')
    print(stdout.read().decode('utf-8', errors='ignore'))

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" 📋 访问信息")
print("=" * 60)
print(f"\n🔑 令牌: {token}")
print(f"🌐 公网访问 URL: http://112.126.61.223:18789/")
print(f"🔐 完整 URL: http://112.126.61.223:18789/#token={token}")

print(f"\n⚠️  重要提示:")
print(f"   1. 确保阿里云安全组已开放端口 18789")
print(f"   2. 令牌认证已启用，相对安全")

ssh.close()

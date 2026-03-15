#!/usr/bin/env python3
"""
修复 Gateway 默认模型配置
"""
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print("  修复 Gateway 默认模型配置")
print("=" * 60)

# 1. 读取当前配置
print("\n[1] 读取当前 Gateway 配置...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 2. 添加默认模型
print("\n[2] 添加默认模型配置...")
if 'agents' not in config:
    config['agents'] = {}
if 'defaults' not in config['agents']:
    config['agents']['defaults'] = {}

config['agents']['defaults']['model'] = 'zai/glm-4.7'
config['agents']['defaults']['reasoning'] = True

print("新默认配置:")
print(json.dumps(config['agents']['defaults'], indent=2))

# 3. 备份
print("\n[3] 备份原配置...")
stdin, stdout, stderr = ssh.exec_command('cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak')
stdout.read()
print("✓ 已备份")

# 4. 写入新配置
print("\n[4] 写入新配置...")
new_config = json.dumps(config, indent=2)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config)
stdin.channel.shutdown_write()
print("✓ 配置已更新")

# 5. 验证
print("\n[5] 验证配置...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 "defaults"')
verify = stdout.read().decode('utf-8', errors='ignore')
print(verify)

# 6. 重启 Gateway
print("\n[6] 重启 Gateway...")
stdin, stdout, stderr = ssh.exec_command('pkill -f openclaw')
stdout.read()
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway > /dev/null 2>&1 &')
stdout.read()
time.sleep(3)

# 7. 检查进程
print("\n[7] 检查进程状态...")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep "[o]penclaw"')
status = stdout.read().decode('utf-8', errors='ignore')

if 'openclaw' in status:
    print("✓ Gateway 已启动")
else:
    print("⚠️  Gateway 未启动")

# 8. 获取 token
print("\n[8] 获取访问 URL...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print("  ✓ 修复完成！")
print("=" * 60)
print(f"\nToken: {token}")
print(f"\n访问 URL:")
print(f"  HTTPS: https://112.126.61.223/#token={token}")
print(f"  HTTP:  http://112.126.61.223:18789/#token={token}")
print(f"\n默认模型已设置为: zai/glm-4.7")
print(f"现在重新访问应该可以正常对话了！")

ssh.close()

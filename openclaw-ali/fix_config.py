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
print(" 修复配置文件")
print("=" * 60)

# 方法1: 使用 doctor 命令
print("\n[方法 1] 运行 openclaw doctor --fix")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('openclaw doctor --fix', get_pty=True)
import time
time.sleep(3)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# 检查配置是否修复
print("\n[检查] 配置文件")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json | grep -A 5 "gateway" | head -20')
print(stdout.read().decode('utf-8', errors='ignore'))

# 如果 doctor 没修复，手动删除 bind 键
print("\n[方法 2] 手动删除 bind 键")
print("-" * 60)
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 删除 bind 键
if 'gateway' in config and 'auth' in config['gateway'] and 'bind' in config['gateway']['auth']:
    del config['gateway']['auth']['bind']
    print("✅ 已删除 bind 键")

    # 写回配置
    new_config = json.dumps(config, indent=2, ensure_ascii=False)
    stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/openclaw.json', get_pty=True)
    stdin.write(new_config + '\n')
    stdin.close()
    print("✅ 配置已更新")
else:
    print("bind 键不存在或已被删除")

# 获取令牌
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(" ✅ 配置已修复！")
print("=" * 60)
print(f"\n🔑 令牌: {token}")
print(f"\n🌐 访问 URL:")
print(f"   http://112.126.61.223:18789/")
print(f"   http://112.126.61.223:18789/#token={token}")
print(f"\n📝 下一步:")
print(f"   1. 在服务器上运行: openclaw gateway")
print(f"   2. 用上面的 URL 访问 Web UI")

ssh.close()

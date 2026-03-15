#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在openclaw.json中添加yahoo-finance-claude skill"""
import paramiko
import sys
import json
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        break
    except:
        continue

ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)

print("=" * 70)
print("  添加 yahoo-finance-claude 到 OpenClaw 配置")
print("=" * 70)
print()

# 1. 备份配置文件
print("[1/4] 备份配置文件...")
stdin, stdout, stderr = ssh.exec_command('cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)')
stdout.read()
print("   ✅ 配置已备份")
print()

# 2. 读取配置
print("[2/4] 读取配置...")
stdin, stdout, stderr = ssh.exec_command('cat ~/.openclaw/openclaw.json')
config_json = stdout.read().decode('utf-8', errors='ignore')
config = json.loads(config_json)
print("   ✅ 配置已读取")
print()

# 3. 添加yahoo-finance-claude
print("[3/4] 添加 yahoo-finance-claude...")
if 'yahoo-finance-claude' not in config['skills']['entries']:
    config['skills']['entries']['yahoo-finance-claude'] = {
        'enabled': True
    }
    print("   ✅ yahoo-finance-claude 已添加")
else:
    print("   ⚠️  yahoo-finance-claude 已存在")
print()

# 4. 写回配置
print("[4/4] 保存配置...")
new_config = json.dumps(config, indent=2, ensure_ascii=False)
# 使用heredoc写入配置
stdin, stdout, stderr = ssh.exec_command('cat > ~/.openclaw/openclaw.json', get_pty=True)
stdin.write(new_config + '\n')
stdin.close()
# 等待写入完成
import time
time.sleep(1)
print("   ✅ 配置已保存")
print()

print("=" * 70)
print("  ✅ yahoo-finance-claude 已添加到配置")
print("=" * 70)
print()
print("下一步：")
print("  1. 重启OpenClaw Gateway")
print("  2. 在OpenClaw中: refresh skills")
print("  3. 列出所有skill验证")
print()

ssh.close()

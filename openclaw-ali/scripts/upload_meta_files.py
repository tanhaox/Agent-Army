#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传_meta.json和.clawhub目录"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'
LOCAL_SKILL = Path('C:/AI-Agent-Local/openclaw-ali/skills/yahoo-finance-claude')
REMOTE_DIR = '/root/.openclaw/workspace/skills/yahoo-finance-claude'

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

sftp = ssh.open_sftp()

# 创建.clawhub目录
try:
    sftp.mkdir(f'{REMOTE_DIR}/.clawhub')
except:
    pass

# 上传_meta.json
print("上传 _meta.json...")
with open(LOCAL_SKILL / '_meta.json', 'rb') as f:
    sftp.putfo(f, f'{REMOTE_DIR}/_meta.json')
print("✅ _meta.json")

# 上传 origin.json
print("上传 .clawhub/origin.json...")
with open(LOCAL_SKILL / '.clawhub/origin.json', 'rb') as f:
    sftp.putfo(f, f'{REMOTE_DIR}/.clawhub/origin.json')
print("✅ .clawhub/origin.json")

sftp.close()

# 验证
print()
print("验证上传...")
stdin, stdout, stderr = ssh.exec_command(f'ls -lah {REMOTE_DIR}/')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

stdin, stdout, stderr = ssh.exec_command(f'ls -lah {REMOTE_DIR}/.clawhub/')
result2 = stdout.read().decode('utf-8', errors='ignore')
print(result2)

print()
print("✅ 上传完成！")
ssh.close()

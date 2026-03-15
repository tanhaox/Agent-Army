#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传main.py到服务器"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'
LOCAL_FILE = Path('C:/AI-Agent-Local/openclaw-ali/skills/yahoo-finance-claude/main.py')
REMOTE_FILE = '/root/.openclaw/workspace/skills/yahoo-finance-claude/main.py'

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

with open(LOCAL_FILE, 'rb') as f:
    sftp.putfo(f, REMOTE_FILE)

sftp.close()

# 验证
stdin, stdout, stderr = ssh.exec_command('ls -lh /root/.openclaw/workspace/skills/yahoo-finance-claude/')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

ssh.close()
print("✅ main.py 已上传")

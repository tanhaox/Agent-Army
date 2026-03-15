#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比成功skill的目录结构"""
import paramiko
import sys
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

print("=" * 80)
print("  对比成功 Skills 的结构")
print("=" * 80)
print()

skills_to_check = [
    ("self-improving-agent", "✅ 被识别的"),
    ("a-share-real-time-data", "✅ 被识别的"),
    ("yahoo-finance-claude", "❌ 我们创建的")
]

for skill_name, status in skills_to_check:
    print(f"\n{'='*80}")
    print(f"  {skill_name} - {status}")
    print('='*80)
    print()

    # 完整目录树
    print("目录结构:")
    stdin, stdout, stderr = ssh.exec_command(f'cd ~/.openclaw/workspace/skills/{skill_name} && find . -type f -name "*.py" -o -name "*.md" -o -name "*.json" | sort')
    files = stdout.read().decode('utf-8', errors='ignore')
    if files.strip():
        for line in files.strip().split('\n')[:20]:
            print(f"  {line}")
    else:
        print("  (无文件)")
    print()

    # 列出所有文件
    print("所有文件:")
    stdin, stdout, stderr = ssh.exec_command(f'ls -lah ~/.openclaw/workspace/skills/{skill_name}/')
    all_files = stdout.read().decode('utf-8', errors='ignore')
    print(all_files)
    print()

print("=" * 80)
ssh.close()

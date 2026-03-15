#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查workspace/skills目录下的所有skills"""
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
print("  Workspace Skills 详细分析")
print("=" * 80)
print()

skills = [
    "openclaw-skill-vetter",
    "self-improving-agent",
    "a-share-real-time-data",
    "yahoo-finance-claude",
    "browser",
    "new-akshare-stock"
]

for i, skill in enumerate(skills, 1):
    print(f"[{i}] {skill}")
    print("-" * 80)

    # 读取_meta.json
    stdin, stdout, stderr = ssh.exec_command(f'cat ~/.openclaw/workspace/skills/{skill}/_meta.json 2>/dev/null || echo "无_meta.json"')
    meta = stdout.read().decode('utf-8', errors='ignore')
    if "无_meta.json" not in meta and meta.strip():
        print("📄 _meta.json:")
        print("   " + meta.strip().replace('\n', '\n   '))
        print()

    # 读取SKILL.md的前20行
    stdin, stdout, stderr = ssh.exec_command(f'head -20 ~/.openclaw/workspace/skills/{skill}/SKILL.md 2>/dev/null || echo "无SKILL.md"')
    skill_md = stdout.read().decode('utf-8', errors='ignore')
    if "无SKILL.md" not in skill_md:
        # 提取name和description
        name = ""
        desc = ""
        for line in skill_md.split('\n')[:10]:
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                desc = line.split(':', 1)[1].strip()

        print(f"📝 Name: {name}")
        print(f"📝 Description: {desc}")
        print()
    else:
        print("   (无SKILL.md)")
        print()

    # 列出主要文件
    stdin, stdout, stderr = ssh.exec_command(f'ls -lh ~/.openclaw/workspace/skills/{skill}/ | grep -v "^total" | grep -v "^d" | head -5')
    files = stdout.read().decode('utf-8', errors='ignore')
    if files.strip():
        print("📦 主要文件:")
        for line in files.strip().split('\n')[:5]:
            if line.strip():
                print(f"   {line}")
        print()

    print()

print("=" * 80)
ssh.close()

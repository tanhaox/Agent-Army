#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部署eastmoney-stock-claude Skill到DigitalOcean服务器"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'
LOCAL_SKILL = Path('C:/AI-Agent-Local/openclaw-ali/skills/eastmoney-stock-claude')
REMOTE_DIR = '/root/.openclaw/workspace/skills/eastmoney-stock-claude'

print("=" * 70)
print("  部署 个股数据补充 Skill 到 DigitalOcean")
print("=" * 70)
print()

# 连接服务器
print(f"📡 连接服务器 {SERVER}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 加载SSH密钥
key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        print(f"✅ 密钥加载成功: {key_class.__name__}")
        break
    except:
        continue

if not key:
    print("❌ 无法加载SSH密钥")
    sys.exit(1)

ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)
print("✅ 服务器连接成功")
print()

# 创建SFTP
sftp = ssh.open_sftp()

# 创建目录结构
print("📁 创建目录结构...")
dirs = [
    REMOTE_DIR,
    f'{REMOTE_DIR}/.clawhub'
]

for dir_path in dirs:
    try:
        sftp.mkdir(dir_path)
        print(f"  ✅ {dir_path}")
    except IOError:
        print(f"  ⚠️  已存在: {dir_path}")

print()

# 上传文件
print("📤 上传文件...")
files = [
    ('_meta.json', f'{REMOTE_DIR}/_meta.json'),
    ('SKILL.md', f'{REMOTE_DIR}/SKILL.md'),
    ('main.py', f'{REMOTE_DIR}/main.py'),
    ('tool.py', f'{REMOTE_DIR}/tool.py'),
    ('.clawhub/origin.json', f'{REMOTE_DIR}/.clawhub/origin.json')
]

for local_file, remote_file in files:
    local_path = LOCAL_SKILL / local_file
    print(f"  上传 {local_file}...")
    with open(local_path, 'rb') as f:
        sftp.putfo(f, remote_file)
    print(f"  ✅ {local_file}")

sftp.close()
print()

# 验证上传
print("🔍 验证上传...")
stdin, stdout, stderr = ssh.exec_command(f'ls -lah {REMOTE_DIR}/')
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

stdin, stdout, stderr = ssh.exec_command(f'ls -lah {REMOTE_DIR}/.clawhub/')
result2 = stdout.read().decode('utf-8', errors='ignore')
print(result2)

# 检查Python文件语法
print()
print("🐍 检查Python文件语法...")
stdin, stdout, stderr = ssh.exec_command(f'cd {REMOTE_DIR} && python3 -m py_compile main.py tool.py')
syntax_error = stderr.read().decode('utf-8', errors='ignore')
if syntax_error:
    print(f"❌ 语法错误:\n{syntax_error}")
else:
    print("✅ Python文件语法正确")

# 初始化数据库
print()
print("🗄️  初始化数据库...")
stdin, stdout, stderr = ssh.exec_command(f'cd {REMOTE_DIR} && python3 -c "from tool import init_db; init_db()"')
init_result = stdout.read().decode('utf-8', errors='ignore')
init_error = stderr.read().decode('utf-8', errors='ignore')
if init_error:
    print(f"⚠️  初始化警告: {init_error}")
else:
    print(f"✅ {init_result.strip()}")

print()
print("=" * 70)
print("  ✅ 部署完成！")
print("=" * 70)
print()
print("📋 Skill信息:")
print(f"  名称: eastmoney-stock-claude")
print(f"  路径: {REMOTE_DIR}")
print(f"  入口: main.py")
print(f"  数据库: /root/.openclaw/workspace/data/stock_detail.duckdb")
print()
print("📌 下一步:")
print("  1. 在OpenClaw中刷新skill列表")
print("  2. 记录skill信息到Identity表")
print("  3. 测试功能：同步伊利股份的所有补充数据")
print()

ssh.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在服务器上下载板块成分股数据
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

# 本地脚本路径
LOCAL_SCRIPT = Path(__file__).parent / "download_sector_constituents.py"
# 服务器路径
REMOTE_SCRIPT = "/root/openclaw-ali/scripts/download_sector_constituents.py"
# 输出目录
OUTPUT_DIR = "/root/openclaw-ali/data/sector_constituents"

print("=" * 70)
print("  下载板块成分股数据（服务器版）")
print("=" * 70)
print()

# 连接服务器
print("[步骤 1] 连接服务器...")
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
print(f"✓ 已连接: {SERVER}")
print()

# 上传脚本
print("[步骤 2] 创建目录并上传脚本...")
sftp = ssh.open_sftp()

try:
    # 创建目录
    try:
        sftp.mkdir('/root/openclaw-ali/scripts')
        print(f"✓ 创建目录: /root/openclaw-ali/scripts")
    except IOError:
        pass  # 目录已存在

    # 读取本地脚本
    with open(LOCAL_SCRIPT, 'r', encoding='utf-8') as f:
        script_content = f.read()

    # 写入服务器
    with sftp.file(REMOTE_SCRIPT, 'w') as f:
        f.write(script_content)

    print(f"✓ 脚本已上传: {REMOTE_SCRIPT}")
finally:
    sftp.close()

# 创建输出目录
print("\n[步骤 3] 创建输出目录...")
stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {OUTPUT_DIR}")
stdout.read()
print(f"✓ 目录已创建: {OUTPUT_DIR}")

# 执行脚本
print("\n[步骤 4] 执行下载脚本...")
print("-" * 70)
stdin, stdout, stderr = ssh.exec_command(f'cd /root/openclaw-ali && python3 {REMOTE_SCRIPT}')

# 实时输出
while True:
    line = stdout.readline()
    if not line:
        break
    print(line.rstrip())

exit_status = stdout.channel.recv_exit_status()
print("-" * 70)

if exit_status == 0:
    print("\n✓ 下载成功!")
else:
    print(f"\n✗ 下载失败，退出码: {exit_status}")
    error = stderr.read().decode('utf-8', errors='ignore')
    if error:
        print(f"错误信息: {error}")

# 查看生成的文件
print("\n[步骤 5] 查看生成的文件...")
stdin, stdout, stderr = ssh.exec_command(f"ls -lh {OUTPUT_DIR}/")
files = stdout.read().decode('utf-8', errors='ignore')
print(files)

ssh.close()

print()
print("=" * 70)
print("  完成!")
print("=" * 70)

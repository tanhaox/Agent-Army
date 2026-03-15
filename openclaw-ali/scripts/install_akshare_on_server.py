#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在新加坡服务器上安装AKShare依赖"""
import paramiko
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

print("=" * 70)
print("  在新加坡服务器上安装 AKShare")
print("=" * 70)
print()

# 连接服务器
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

# 1. 检查Python版本
print("🐍 检查Python版本...")
stdin, stdout, stderr = ssh.exec_command('python3 --version')
version = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"  {version}")

# 2. 检查pip
print()
print("📦 检查pip...")
stdin, stdout, stderr = ssh.exec_command('pip3 --version')
pip_version = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"  {pip_version}")

# 3. 安装AKShare
print()
print("📥 安装AKShare...")
stdin, stdout, stderr = ssh.exec_command('pip3 install akshare -q')
stdout.channel.recv_exit_status()  # 等待命令完成
print("  ✅ AKShare 安装完成")

# 4. 验证安装
print()
print("🔍 验证安装...")
stdin, stdout, stderr = ssh.exec_command('python3 -c "import akshare as ak; print(ak.__version__)"')
akshare_version = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"  AKShare 版本: {akshare_version}")

# 5. 测试功能
print()
print("🧪 测试AKShare功能...")
stdin, stdout, stderr = ssh.exec_command('python3 -c "import akshare as ak; df=ak.stock_individual_fund_flow(stock=\'601669\',market=\'sh\'); print(f\'获取{len(df)}条记录\')"')
test_result = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"  {test_result}")

print()
print("=" * 70)
print("  ✅ AKShare 安装和验证完成！")
print("=" * 70)
print()

ssh.close()

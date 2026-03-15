#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查新加坡服务器上的记忆API系统"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新加坡服务器
HOSTNAME = '157.245.195.58'
PORT = 22
USERNAME = 'root'

# 尝试多种连接方式
def try_connect_with_password(password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=HOSTNAME, port=PORT, username=USERNAME, password=password, timeout=10)
        return ssh
    except:
        return None

def try_connect_with_key():
    key_files = [
        'C:/Users/tanha/.ssh/id_rsa',
        'C:/Users/tanha/.ssh/id_ed25519',
        'C:/AI-Agent-Local/.ssh/id_rsa',
    ]
    for key_file in key_files:
        try:
            if os.path.exists(key_file):
                key = paramiko.RSAKey.from_private_key_file(key_file, password='a19571004')
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=HOSTNAME, port=PORT, username=USERNAME, pkey=key, timeout=10)
                return ssh
        except:
            continue
    return None

import os

print("="*60)
print(" 连接新加坡服务器: 157.245.195.58")
print("="*60)
print()

# 尝试密码连接
passwords = ['', 'Dandanyi2024!&Root', 'a19571004', 'Root19571004!']
ssh = None

for pwd in passwords:
    print(f"[*] 尝试密码连接...")
    ssh = try_connect_with_password(pwd)
    if ssh:
        print(f"[OK] 密码连接成功")
        break

# 如果密码失败，尝试密钥
if not ssh:
    print("[*] 尝试SSH密钥连接...")
    ssh = try_connect_with_key()
    if ssh:
        print("[OK] SSH密钥连接成功")

if not ssh:
    print("[ERROR] 所有连接方式都失败了")
    sys.exit(1)

print()
print("-"*60)
print(" 连接成功! 开始检查记忆API系统...")
print("-"*60)
print()

# 1. 查找记忆API服务器脚本
print("[1] 搜索记忆API服务器脚本...")
stdin, stdout, stderr = ssh.exec_command(
    "find /root/.openclaw/workspace -name '*.py' -type f 2>/dev/null | xargs grep -l '18888\\|FastAPI\\|uvicorn\\|app = FastAPI' 2>/dev/null"
)
files = stdout.read().decode().strip()
if files:
    print("找到以下文件:")
    for f in files.split('\n'):
        if f:
            print(f"  - {f}")
else:
    print("  未找到包含FastAPI的文件")

print()

# 2. 列出所有Python文件
print("[2] 列出workspace目录所有Python文件...")
stdin, stdout, stderr = ssh.exec_command("ls -la /root/.openclaw/workspace/*.py 2>/dev/null")
output = stdout.read().decode().strip()
print(output)

print()

# 3. 查看sync_memory.py的完整内容
print("[3] 查看sync_memory.py内容...")
stdin, stdout, stderr = ssh.exec_command("cat /root/.openclaw/workspace/sync_memory.py 2>/dev/null | head -100")
content = stdout.read().decode().strip()
print(content)

print()

# 4. 检查端口
print("[4] 检查端口18888状态...")
stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep -E '18888|188\\|1880' || echo '未找到相关端口'")
port_status = stdout.read().decode().strip()
print(port_status)

print()

# 5. 检查进程
print("[5] 检查运行中的Python进程...")
stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'python.*memory|uvicorn|gunicorn' | grep -v grep")
processes = stdout.read().decode().strip()
if processes:
    print("找到以下进程:")
    print(processes)
else:
    print("  未找到相关进程")

ssh.close()

print()
print("="*60)
print(" 检查完成")
print("="*60)

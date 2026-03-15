#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经Skill部署到DigitalOcean服务器
使用SSH密钥认证
"""
import sys
import os
from pathlib import Path

# UTF-8设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko

# DigitalOcean服务器配置
SERVER = "157.245.195.58"
PORT = 22
USERNAME = "root"
# SSH密钥路径（需要转换OpenSSH私钥格式）
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

# 本地skill目录
SKILL_DIR = Path(__file__).parent.parent / 'skills' / 'yahoo-finance-claude'
TARGET_DIR = "/root/.openclaw/skills/yahoo-finance-claude"

def upload_skill_to_do():
    """部署到DigitalOcean"""
    print("=" * 70)
    print("  雅虎财经Skill部署到DigitalOcean服务器")
    print("=" * 70)
    print()

    # 检查本地文件
    print("[1/5] 检查本地文件...")
    if not SKILL_DIR.exists():
        print(f"   ❌ 错误：本地skill目录不存在: {SKILL_DIR}")
        return False

    required_files = ['SKILL.md', 'tool.py']
    for file in required_files:
        file_path = SKILL_DIR / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ 缺少文件: {file}")
            return False

    print()

    # 检查SSH密钥
    print("[2/5] 检查SSH密钥...")
    if not KEY_PATH.exists():
        print(f"   ❌ SSH密钥不存在: {KEY_PATH}")
        print(f"   请确保密钥文件存在")
        return False
    print(f"   ✅ 找到SSH密钥")
    print()

    # 连接SSH
    print(f"[3/5] 连接服务器 {SERVER}...")
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 加载私钥 - 支持OpenSSH格式
        key = None
        for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
            try:
                key = key_class.from_private_key_file(str(KEY_PATH))
                break
            except:
                continue

        if key is None:
            # 尝试使用兼容性方法
            with open(KEY_PATH, 'r') as f:
                key = paramiko.RSAKey.from_private_key(f)

        # 使用密钥连接
        ssh.connect(hostname=SERVER, port=PORT, username=USERNAME, pkey=key, timeout=15)
        print(f"   ✅ 成功连接到 {SERVER}")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        print(f"   尝试使用密码认证...")
        # 备用方案：使用密码
        try:
            ssh.connect(hostname=SERVER, port=PORT, username='root', password='Dandanyi2024!&Root', timeout=15)
            print(f"   ✅ 使用密码连接成功")
        except Exception as e2:
            print(f"   ❌ 密码连接也失败: {e2}")
            return False

    print()

    # 创建SFTP
    print("[4/5] 上传skill文件...")
    try:
        sftp = ssh.open_sftp()

        # 创建目录（包括父目录）
        try:
            sftp.mkdir(TARGET_DIR)
        except IOError:
            # 父目录不存在，递归创建
            dirs = TARGET_DIR.split('/')
            for i in range(1, len(dirs)):
                path = '/'.join(dirs[:i+1])
                try:
                    sftp.mkdir(path)
                except:
                    pass  # 目录可能已存在

        # 上传SKILL.md
        print(f"   上传 SKILL.md...")
        with open(SKILL_DIR / 'SKILL.md', 'rb') as f:
            sftp.putfo(f, f"{TARGET_DIR}/SKILL.md")
        print("   ✅ SKILL.md")

        # 上传tool.py
        print(f"   上传 tool.py...")
        with open(SKILL_DIR / 'tool.py', 'rb') as f:
            sftp.putfo(f, f"{TARGET_DIR}/tool.py")
        print("   ✅ tool.py")

        sftp.close()
        print("   ✅ 上传完成")

    except Exception as e:
        print(f"   ❌ 上传失败: {e}")
        ssh.close()
        return False

    print()

    # 设置权限
    print("[5/5] 设置权限和重启...")
    try:
        # 设置可执行权限
        stdin, stdout, stderr = ssh.exec_command(f'chmod +x {TARGET_DIR}/tool.py')
        stdout.read()
        print("   ✅ tool.py 可执行权限")

        stdin, stdout, stderr = ssh.exec_command(f'chmod 644 {TARGET_DIR}/SKILL.md')
        stdout.read()
        print("   ✅ SKILL.md 读写权限")

        # 重启OpenClaw Gateway
        print()
        print("   重启OpenClaw Gateway...")
        stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw-gateway && sleep 2 && cd /root && nohup openclaw gateway > /tmp/openclaw-gateway.log 2>&1 &')
        stdout.read()
        print("   ✅ Gateway已重启")

    except Exception as e:
        print(f"   ⚠️  警告: {e}")

    print()

    # 验证
    print("验证部署...")
    try:
        stdin, stdout, stderr = ssh.exec_command(f'ls -lh {TARGET_DIR}/')
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)
    except Exception as e:
        print(f"   ⚠️  验证失败: {e}")

    # 检查Gateway状态
    print()
    print("检查Gateway状态...")
    try:
        stdin, stdout, stderr = ssh.exec_command('pgrep -f openclaw-gateway && echo "✅ Gateway运行中" || echo "❌ Gateway未运行"')
        output = stdout.read().decode('utf-8', errors='ignore')
        print(f"   {output}")
    except Exception as e:
        print(f"   ⚠️  检查失败: {e}")

    ssh.close()

    print()
    print("=" * 70)
    print("  ✅ 雅虎财经Skill部署完成！")
    print("=" * 70)
    print()
    print("下一步：")
    print("  1. 访问: https://157.245.195.58/chat?session=main")
    print("  2. 输入: refresh skills")
    print("  3. 测试: 同步伊利股份的雅虎财经数据")
    print()

    return True

if __name__ == '__main__':
    try:
        success = upload_skill_to_do()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

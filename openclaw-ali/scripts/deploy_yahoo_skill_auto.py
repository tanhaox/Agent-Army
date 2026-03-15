#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经Skill自动化部署脚本
使用paramiko自动连接服务器并部署
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

# 服务器配置
SERVER = "112.126.61.223"
PORT = 22
USERNAME = "root"
PASSWORD = "Dandanyi2024!&Root"

# 本地skill目录
SKILL_DIR = Path(__file__).parent.parent / 'skills' / 'yahoo-finance'
TARGET_DIR = "/root/.openclaw/skills/yahoo-finance"

def upload_skill_via_ssh():
    """通过SSH上传skill"""
    print("=" * 70)
    print("  雅虎财经Skill自动化部署")
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

    # 连接SSH
    print("[2/5] 连接服务器...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SERVER, port=PORT, username=USERNAME, password=PASSWORD, timeout=15)
        print(f"   ✅ 成功连接到 {SERVER}")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False

    print()

    # 创建SFTP
    print("[3/5] 上传skill文件...")
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
    print("[4/5] 设置权限...")
    try:
        stdin, stdout, stderr = ssh.exec_command(f'chmod +x {TARGET_DIR}/tool.py')
        stdout.read()
        print("   ✅ tool.py 可执行权限")

        stdin, stdout, stderr = ssh.exec_command(f'chmod 644 {TARGET_DIR}/SKILL.md')
        stdout.read()
        print("   ✅ SKILL.md 读写权限")

    except Exception as e:
        print(f"   ⚠️  权限设置警告: {e}")

    print()

    # 重启Gateway
    print("[5/5] 重启OpenClaw Gateway...")
    try:
        stdin, stdout, stderr = ssh.exec_command('openclaw gateway restart')
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        print(f"   ✅ Gateway已重启")
    except Exception as e:
        print(f"   ⚠️  重启警告: {e}")
        print("   请手动重启: openclaw gateway restart")

    print()

    # 验证
    print("验证部署...")
    try:
        stdin, stdout, stderr = ssh.exec_command(f'ls -lh {TARGET_DIR}/')
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)
    except Exception as e:
        print(f"   ⚠️  验证失败: {e}")

    ssh.close()

    print()
    print("=" * 70)
    print("  ✅ 雅虎财经Skill部署完成！")
    print("=" * 70)
    print()
    print("下一步：在OpenClaw中测试")
    print("  输入: refresh skills")
    print("  输入: 同步伊利股份的雅虎财经数据")
    print()

    return True

if __name__ == '__main__':
    try:
        success = upload_skill_via_ssh()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

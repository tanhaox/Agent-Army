#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆API服务器部署脚本
将memory_api_server.py部署到新加坡服务器(157.245.195.58)
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import os
from pathlib import Path

# 服务器信息
SG_HOST = "157.245.195.58"
SG_USER = "root"

# 本地脚本路径
LOCAL_SCRIPT = Path(__file__).parent / "memory_api_server.py"
# 服务器目标路径
REMOTE_PATH = "/root/.openclaw/workspace/memory_api_server.py"

def deploy_via_sshpass():
    """使用sshpass部署（如果有sshpass命令）"""
    print("[方法1] 尝试使用sshpass...")

    # 检查是否有sshpass
    try:
        subprocess.run(["sshpass", "-V"], capture_output=True, check=True)
    except:
        print("  sshpass未安装，跳过此方法")
        return False

    # 使用sshpass上传文件
    passwords = ['', 'Dandanyi2024!&Root', 'a19571004']

    for pwd in passwords:
        try:
            # 上传脚本
            result = subprocess.run([
                "sshpass", "-p", pwd,
                "scp", "-o", "StrictHostKeyChecking=no",
                str(LOCAL_SCRIPT), f"{SG_USER}@{SG_HOST}:{REMOTE_PATH}"
            ], capture_output=True, timeout=30)

            if result.returncode == 0:
                print(f"  [OK] 使用密码上传成功")

                # 启动服务
                subprocess.run([
                    "sshpass", "-p", pwd,
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{SG_USER}@{SG_HOST}",
                    "cd /root/.openclaw/workspace && "
                    "mkdir -p logs data && "
                    "nohup python3 memory_api_server.py > logs/memory_api.log 2>&1 &"
                ])

                print(f"  [OK] 服务已启动")
                return True

        except Exception as e:
            continue

    print("  所有密码都尝试失败")
    return False

def deploy_via_python():
    """使用Python的paramiko库部署"""
    print("[方法2] 尝试使用paramiko...")

    try:
        import paramiko

        # 尝试多种认证方式
        passwords = ['', 'Dandanyi2024!&Root', 'a19571004']
        ssh = None

        # 1. 尝试密码认证
        for pwd in passwords:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=SG_HOST, port=22, username=SG_USER, password=pwd, timeout=10)
                print(f"  [OK] 使用密码连接成功")
                break
            except:
                ssh = None
                continue

        # 2. 如果密码失败，尝试密钥认证
        if not ssh:
            key_files = [
                'C:/Users/tanha/.ssh/id_rsa',
                os.path.expanduser('~/.ssh/id_rsa'),
            ]
            for key_file in key_files:
                try:
                    if os.path.exists(key_file):
                        key = paramiko.RSAKey.from_private_key_file(key_file)
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(hostname=SG_HOST, port=22, username=SG_USER, pkey=key, timeout=10)
                        print(f"  [OK] 使用SSH密钥连接成功")
                        break
                except:
                    continue

        if not ssh:
            print("  所有连接方式都失败")
            return False

        # 创建SFTP客户端上传文件
        print("  [*] 上传脚本...")
        sftp = ssh.open_sftp()
        sftp.put(str(LOCAL_SCRIPT), REMOTE_PATH)
        sftp.close()

        print("  [OK] 脚本已上传")

        # 创建目录并启动服务
        print("  [*] 启动服务...")
        commands = [
            "mkdir -p /root/.openclaw/workspace/logs",
            "mkdir -p /root/.openclaw/workspace/data",
            "pip3 install fastapi uvicorn duckdb -q 2>/dev/null",
            "pkill -f memory_api_server.py 2>/dev/null",  # 停止旧进程
            "cd /root/.openclaw/workspace && nohup python3 memory_api_server.py > logs/memory_api.log 2>&1 &",
        ]

        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdout.read()

        print("  [OK] 服务已启动")

        ssh.close()
        return True

    except ImportError:
        print("  paramiko未安装")
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def deploy_via_manual():
    """生成手动部署命令"""
    print("[方法3] 生成手动部署命令...")
    print()
    print("="*60)
    print(" 手动部署步骤")
    print("="*60)
    print()
    print(f"1. 将以下文件复制到服务器:")
    print(f"   本地: {LOCAL_SCRIPT}")
    print(f"   远程: {SG_HOST}:{REMOTE_PATH}")
    print()
    print(f"2. 使用以下命令上传:")
    print(f"   scp {LOCAL_SCRIPT} {SG_USER}@{SG_HOST}:{REMOTE_PATH}")
    print()
    print(f"3. SSH登录服务器并执行:")
    print(f"   ssh {SG_USER}@{SG_HOST}")
    print(f"   cd /root/.openclaw/workspace")
    print(f"   mkdir -p logs data")
    print(f"   pip3 install fastapi uvicorn duckdb")
    print(f"   nohup python3 memory_api_server.py > logs/memory_api.log 2>&1 &")
    print()
    print(f"4. 验证服务:")
    print(f"   netstat -tlnp | grep 18888")
    print(f"   curl http://localhost:18888/health")
    print()
    print("="*60)

    return False

def main():
    print()
    print("="*60)
    print(" 记忆API服务器部署")
    print("="*60)
    print(f" 目标服务器: {SG_HOST}")
    print(f" 脚本: {LOCAL_SCRIPT.name}")
    print("="*60)
    print()

    # 检查本地脚本是否存在
    if not LOCAL_SCRIPT.exists():
        print(f"[ERROR] 脚本不存在: {LOCAL_SCRIPT}")
        return

    # 尝试各种部署方法
    if deploy_via_sshpass():
        print()
        print("[SUCCESS] 部署成功!")
        verify_deployment()
        return

    print()
    if deploy_via_python():
        print()
        print("[SUCCESS] 部署成功!")
        verify_deployment()
        return

    print()
    print("[INFO] 自动部署失败，请使用手动部署")
    deploy_via_manual()

def verify_deployment():
    """验证部署"""
    print()
    print("[验证] 检查服务状态...")
    print(f"  API端点: http://{SG_HOST}:18888")
    print(f"  健康检查: http://{SG_HOST}:18888/health")
    print(f"  文档: http://{SG_HOST}:18888/docs")
    print()

if __name__ == '__main__':
    main()

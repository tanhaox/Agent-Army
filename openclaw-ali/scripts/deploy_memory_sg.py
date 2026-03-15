#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用正确的SSH密钥部署记忆API到新加坡服务器"""
import paramiko
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新加坡服务器
SG_HOST = "157.245.195.58"
SG_USER = "root"

# SSH密钥文件（DigitalOcean）
KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"  # 密钥密码

# 本地脚本路径
LOCAL_SCRIPT = r"C:\AI-Agent-Local\openclaw-ali\scripts\memory_api_server.py"
REMOTE_PATH = "/root/.openclaw/workspace/memory_api_server.py"

def deploy_to_singapore():
    """部署记忆API到新加坡服务器"""
    print("="*60)
    print(" 使用SSH密钥部署记忆API到新加坡服务器")
    print("="*60)
    print()

    try:
        # 加载SSH密钥
        print("[1] 加载SSH密钥...")
        print(f"     密钥文件: {KEY_FILE}")

        if not os.path.exists(KEY_FILE):
            print(f"  [ERROR] 密钥文件不存在!")
            return False

        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        print("  [OK] 密钥已加载")
        print()

        # 连接服务器
        print(f"[2] 连接新加坡服务器: {SG_HOST}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username=SG_USER, pkey=key, timeout=15)
        print("  [OK] 连接成功!")
        print()

        # 检查服务器上的文件
        print("[3] 检查workspace目录...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/.openclaw/workspace/")
        output = stdout.read().decode().strip()
        print(output)
        print()

        # 上传脚本
        print("[4] 上传记忆API服务器脚本...")
        sftp = ssh.open_sftp()

        # 检查本地脚本
        if not os.path.exists(LOCAL_SCRIPT):
            print(f"  [ERROR] 本地脚本不存在: {LOCAL_SCRIPT}")
            ssh.close()
            return False

        # 上传文件
        sftp.put(LOCAL_SCRIPT, REMOTE_PATH)
        sftp.close()
        print(f"  [OK] 脚本已上传: {REMOTE_PATH}")
        print()

        # 安装依赖
        print("[5] 安装Python依赖...")
        stdin, stdout, stderr = ssh.exec_command(
            "pip3 install fastapi uvicorn duckdb 2>&1"
        )
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(output)
        if error and "Successfully installed" not in error:
            print(f"  注意: {error}")
        print()

        # 创建目录
        print("[6] 创建日志和数据目录...")
        stdin, stdout, stderr = ssh.exec_command(
            "mkdir -p /root/.openclaw/workspace/logs /root/.openclaw/workspace/data"
        )
        stdout.read()
        print("  [OK] 目录已创建")
        print()

        # 停止旧进程
        print("[7] 停止旧的记忆API进程...")
        stdin, stdout, stderr = ssh.exec_command(
            "pkill -f memory_api_server.py 2>/dev/null; echo 'done'"
        )
        print("  [OK] 旧进程已停止")
        print()

        # 启动服务
        print("[8] 启动记忆API服务...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw/workspace && "
            "nohup python3 memory_api_server.py > logs/memory_api.log 2>&1 & "
            "echo 'Service started with PID:' $!"
        )
        output = stdout.read().decode().strip()
        print(f"  {output}")
        print()

        # 等待服务启动
        import time
        print("[9] 等待服务启动...")
        time.sleep(3)
        print()

        # 验证服务
        print("[10] 验证服务状态...")

        # 检查端口
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
        port_status = stdout.read().decode().strip()

        if port_status:
            print("  [OK] 端口18888正在监听:")
            for line in port_status.split('\n'):
                print(f"       {line}")
        else:
            print("  [WARN] 端口18888未监听，检查日志...")

            # 查看日志
            stdin, stdout, stderr = ssh.exec_command(
                "tail -50 /root/.openclaw/workspace/logs/memory_api.log"
            )
            logs = stdout.read().decode().strip()
            print("  === 日志 ===")
            print(logs)
            print("  === 日志结束 ===")

        print()
        print("="*60)
        print(" 部署完成!")
        print("="*60)
        print()
        print("  API端点信息:")
        print(f"    - 基础URL: http://{SG_HOST}:18888")
        print(f"    - 健康检查: http://{SG_HOST}:18888/health")
        print(f"    - API文档: http://{SG_HOST}:18888/docs")
        print(f"    - 统计信息: http://{SG_HOST}:18888/api/memory/stats")
        print()
        print("  使用sync_memory.py调用:")
        print(f"    MEMORY_API = \"http://{SG_HOST}:18888\"")
        print()
        print("="*60)

        ssh.close()
        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    deploy_to_singapore()

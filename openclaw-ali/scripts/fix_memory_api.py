#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安装记忆API依赖并启动服务"""
import paramiko
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新加坡服务器
SG_HOST = "157.245.195.58"
SG_USER = "root"

# SSH密钥
KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"

def install_and_start():
    """安装依赖并启动服务"""
    print("="*60)
    print(" 安装记忆API依赖并启动服务")
    print("="*60)
    print()

    try:
        # 加载密钥并连接
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username=SG_USER, pkey=key, timeout=15)

        print("[1] 安装Python依赖 (使用--break-system-packages)...")
        stdin, stdout, stderr = ssh.exec_command(
            "pip3 install fastapi uvicorn duckdb --break-system-packages 2>&1"
        )

        output = stdout.read().decode().strip()
        print(output)

        # 检查是否安装成功
        stdin, stdout, stderr = ssh.exec_command(
            "python3 -c 'import fastapi, uvicorn, duckdb; print(\"依赖已安装\")' 2>&1"
        )
        check = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if "依赖已安装" in check:
            print("  [OK] 依赖安装成功!")
        else:
            print(f"  [ERROR] 依赖检查失败: {error}")
            ssh.close()
            return False

        print()

        # 停止旧进程
        print("[2] 停止旧的记忆API进程...")
        stdin, stdout, stderr = ssh.exec_command(
            "pkill -f memory_api_server.py 2>/dev/null; echo 'done'"
        )
        print("  [OK] 旧进程已停止")
        print()

        # 启动服务
        print("[3] 启动记忆API服务...")
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
        print("[4] 等待服务启动...")
        time.sleep(5)
        print()

        # 验证服务
        print("[5] 验证服务状态...")

        # 检查端口
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
        port_status = stdout.read().decode().strip()

        if port_status:
            print("  [OK] 端口18888正在监听:")
            for line in port_status.split('\n'):
                print(f"       {line}")
            print()

            # 测试API
            print("[6] 测试API端点...")
            stdin, stdout, stderr = ssh.exec_command(
                "curl -s http://localhost:18888/health 2>&1"
            )
            health = stdout.read().decode().strip()
            print(f"  健康检查响应:")
            print(f"  {health}")

            print()
            print("="*60)
            print(" 记忆API部署成功!")
            print("="*60)
            print()
            print("  API端点信息:")
            print(f"    - 基础URL: http://{SG_HOST}:18888")
            print(f"    - 健康检查: http://{SG_HOST}:18888/health")
            print(f"    - API文档: http://{SG_HOST}:18888/docs")
            print(f"    - 存储记忆: POST http://{SG_HOST}:18888/api/memory/remember")
            print(f"    - 检索记忆: POST http://{SG_HOST}:18888/api/memory/recall")
            print(f"    - 搜索记忆: POST http://{SG_HOST}:18888/api/memory/search")
            print(f"    - 统计信息: http://{SG_HOST}:18888/api/memory/stats")
            print()
            print("  sync_memory.py配置:")
            print(f'    MEMORY_API = "http://{SG_HOST}:18888"')
            print()

            ssh.close()
            return True

        else:
            print("  [WARN] 端口18888未监听，检查日志...")

            # 查看日志
            stdin, stdout, stderr = ssh.exec_command(
                "cat /root/.openclaw/workspace/logs/memory_api.log"
            )
            logs = stdout.read().decode().strip()
            print("  === 错误日志 ===")
            print(logs)
            print("  === 日志结束 ===")

            ssh.close()
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    install_and_start()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新上传并启动记忆API服务"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新加坡服务器
SG_HOST = "157.245.195.58"
SG_USER = "root"

# SSH密钥
KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"

# 本地脚本路径
LOCAL_SCRIPT = r"C:\AI-Agent-Local\openclaw-ali\scripts\memory_api_server.py"
REMOTE_PATH = "/root/.openclaw/workspace/memory_api_server.py"

def redeploy():
    """重新部署并启动"""
    print("="*60)
    print(" 重新部署记忆API服务")
    print("="*60)
    print()

    try:
        # 连接
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username=SG_USER, pkey=key, timeout=15)

        # 停止旧服务
        print("[1] 停止旧服务...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f memory_api_server.py 2>/dev/null")
        stdout.read()
        print("  [OK] 旧服务已停止")
        print()

        # 上传新脚本
        print("[2] 上传修复后的脚本...")
        sftp = ssh.open_sftp()
        sftp.put(LOCAL_SCRIPT, REMOTE_PATH)
        sftp.close()
        print("  [OK] 脚本已上传")
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

        # 等待启动
        import time
        print("[4] 等待服务启动...")
        time.sleep(5)
        print()

        # 验证
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
            stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:18888/ 2>&1")
            response = stdout.read().decode().strip()
            print("  [API测试] 根路径响应:")
            print(f"  {response}")
            print()

            # 测试健康检查
            stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:18888/health 2>&1")
            health = stdout.read().decode().strip()
            print("  [API测试] 健康检查响应:")
            print(f"  {health}")
            print()

            print("="*60)
            print(" 记忆API部署成功!")
            print("="*60)
            print()
            print("  API端点:")
            print(f"    - 基础URL: http://{SG_HOST}:18888")
            print(f"    - 健康检查: http://{SG_HOST}:18888/health")
            print(f"    - API文档: http://{SG_HOST}:18888/docs")
            print()
            print("  使用示例 (Python):")
            print(f'    import requests')
            print(f'    response = requests.post("http://{SG_HOST}:18888/api/memory/remember",')
            print(f'        json={{"content": "测试记忆", "category": "test", "importance": 80}})')
            print()

            # 更新todo
            print("  [TODO] 更新sync_memory.py中的API地址:")
            print(f'    MEMORY_API = "http://{SG_HOST}:18888"')
            print()

        else:
            print("  [ERROR] 端口未监听，检查日志:")
            stdin, stdout, stderr = ssh.exec_command("tail -30 /root/.openclaw/workspace/logs/memory_api.log")
            logs = stdout.read().decode().strip()
            print(logs)

        ssh.close()

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    redeploy()

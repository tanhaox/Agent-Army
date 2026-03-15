#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过跳转服务器部署记忆API到新加坡服务器"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 跳转服务器
JUMP_HOST = "112.126.61.223"
JUMP_USER = "root"
JUMP_PASSWORD = r'Dandanyi2024!&Root'

# 目标服务器（新加坡）
TARGET_HOST = "157.245.195.58"
TARGET_USER = "root"

# 本地脚本路径
LOCAL_SCRIPT = r"C:\AI-Agent-Local\openclaw-ali\scripts\memory_api_server.py"
REMOTE_PATH = "/root/.openclaw/workspace/memory_api_server.py"

def deploy_via_jump_host():
    """通过跳转服务器部署"""
    print("="*60)
    print(" 通过跳转服务器部署记忆API")
    print("="*60)
    print()

    try:
        # 连接到跳转服务器
        print(f"[1] 连接跳转服务器: {JUMP_HOST}...")
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_ssh.connect(hostname=JUMP_HOST, port=22, username=JUMP_USER, password=JUMP_PASSWORD, timeout=10)
        print("  [OK] 跳转服务器连接成功")
        print()

        # 从跳转服务器连接到目标服务器
        print(f"[2] 从跳转服务器连接到新加坡服务器...")
        print(f"     检查跳转服务器是否可以SSH到{TARGET_HOST}...")

        # 测试连接
        stdin, stdout, stderr = jump_ssh.exec_command(
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {TARGET_USER}@{TARGET_HOST} 'echo OK'",
            timeout=15
        )
        result = stdout.read().decode().strip()

        if "OK" in result:
            print(f"  [OK] 可以从跳转服务器连接到新加坡服务器")
            print()

            # 读取本地脚本内容
            print("[3] 读取本地脚本...")
            with open(LOCAL_SCRIPT, 'r', encoding='utf-8') as f:
                script_content = f.read()
            print(f"  [OK] 脚本已读取 ({len(script_content)} 字节)")
            print()

            # 通过跳转服务器传输脚本
            print("[4] 通过跳转服务器传输脚本...")
            transport = jump_ssh.get_transport()
            dest_addr = (TARGET_HOST, 22)
            local_addr = (JUMP_HOST, 22)
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

            target_ssh = paramiko.SSHClient()
            target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target_ssh.connect(hostname=TARGET_HOST, port=22, username=TARGET_USER, sock=channel, timeout=15)

            # 使用SFTP上传
            sftp = target_ssh.open_sftp()
            with open(LOCAL_SCRIPT, 'rb') as f:
                sftp.putfo(f, REMOTE_PATH)
            sftp.close()
            print(f"  [OK] 脚本已上传到: {REMOTE_PATH}")
            print()

            # 安装依赖并启动服务
            print("[5] 安装依赖并启动服务...")
            commands = [
                "mkdir -p /root/.openclaw/workspace/logs",
                "mkdir -p /root/.openclaw/workspace/data",
                "pip3 install fastapi uvicorn duckdb -q 2>/dev/null || pip3 install fastapi uvicorn duckdb",
                "pkill -f memory_api_server.py 2>/dev/null",  # 停止旧进程
            ]

            for cmd in commands:
                stdin, stdout, stderr = target_ssh.exec_command(cmd)
                stdout.read()
                stderr.read()

            print("  [OK] 依赖已安装")
            print()

            # 启动服务
            print("[6] 启动记忆API服务...")
            stdin, stdout, stderr = target_ssh.exec_command(
                "cd /root/.openclaw/workspace && nohup python3 memory_api_server.py > logs/memory_api.log 2>&1 &"
            )
            print("  [OK] 服务已启动")
            print()

            # 验证服务
            print("[7] 验证服务状态...")
            import time
            time.sleep(3)

            stdin, stdout, stderr = target_ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
            port_status = stdout.read().decode().strip()
            if port_status:
                print(f"  [OK] 端口18888正在监听:")
                print(f"       {port_status}")
            else:
                print(f"  [WARN] 端口18888未监听，请检查日志")

            print()
            print("="*60)
            print(" 部署完成!")
            print("="*60)
            print(f"  API端点: http://{TARGET_HOST}:18888")
            print(f"  健康检查: http://{TARGET_HOST}:18888/health")
            print(f"  文档: http://{TARGET_HOST}:18888/docs")
            print("="*60)

            target_ssh.close()
            jump_ssh.close()
            return True

        else:
            print(f"  [ERROR] 无法从跳转服务器连接到新加坡服务器")
            print(f"         错误: {stderr.read().decode().strip()}")
            jump_ssh.close()
            return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not deploy_via_jump_host():
        print()
        print("[INFO] 请尝试其他方式部署:")
        print("  1. 检查新加坡服务器的SSH配置")
        print("  2. 检查防火墙规则")
        print("  3. 使用VPN连接后直接SSH")
        print("  4. 通过服务商控制台上传文件")

if __name__ == '__main__':
    main()

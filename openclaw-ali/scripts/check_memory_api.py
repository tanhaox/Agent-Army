#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查服务器上的记忆API相关文件"""
import paramiko
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_server(hostname, password):
    print(f"\n{'='*60}")
    print(f" 检查服务器: {hostname}")
    print(f"{'='*60}\n")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, port=22, username='root', password=password, timeout=10)

        print("[OK] SSH连接成功\n")

        # 1. 查找记忆API服务器脚本
        print("[1] 搜索记忆API服务器脚本...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/workspace -name '*.py' -type f -exec grep -l '18888\\|FastAPI\\|uvicorn' {} \\; 2>/dev/null"
        )
        files = stdout.read().decode().strip()
        if files:
            print("找到以下文件:")
            for f in files.split('\n'):
                if f:
                    print(f"  - {f}")
        else:
            print("  未找到包含18888或FastAPI的文件")

        print()

        # 2. 查找所有记忆相关的文件
        print("[2] 搜索所有记忆相关文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/workspace/*memory*.py 2>/dev/null || echo '未找到记忆相关文件'"
        )
        files = stdout.read().decode().strip()
        print(files)

        print()

        # 3. 检查端口18888是否在监听
        print("[3] 检查端口18888状态...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888 || echo '端口未监听'")
        port_status = stdout.read().decode().strip()
        print(f"  {port_status}")

        print()

        # 4. 查看sync_memory.py的内容以了解API端点
        print("[4] 查看sync_memory.py中的API配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "head -50 /root/.openclaw/workspace/sync_memory.py 2>/dev/null | grep -E 'MEMORY_API|18888|import|class|def' || echo '文件不存在'"
        )
        api_config = stdout.read().decode().strip()
        print(api_config)

        print()

        # 5. 查看是否有启动脚本
        print("[5] 查找启动脚本或服务...")
        stdin, stdout, stderr = ssh.exec_command(
            "find /root/.openclaw/workspace -name '*start*' -o -name '*serve*' 2>/dev/null | head -10"
        )
        scripts = stdout.read().decode().strip()
        if scripts:
            print("找到:")
            for s in scripts.split('\n'):
                if s:
                    print(f"  - {s}")
        else:
            print("  未找到启动脚本")

        ssh.close()

    except Exception as e:
        print(f"[ERROR] 连接失败: {e}\n")

# 检查两个服务器
# 服务器1: 112.126.61.223 (原始服务器)
check_server('112.126.61.223', r'Dandanyi2024!&Root')

# 服务器2: 157.245.195.58 (新加坡服务器)
print("\n注意: 新加坡服务器(157.245.195.58)可能需要SSH密钥，暂时跳过\n")

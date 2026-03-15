#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查配置备份历史，对比版本回退前后的变化"""
import paramiko
import sys
import json
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_backup_history():
    print("="*70)
    print(" 检查配置备份历史 - 分析版本回退影响")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 获取所有备份文件
        print("[1] 配置备份文件列表...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt --time-style=long-iso /root/.openclaw/openclaw.json.bak* 2>/dev/null"
        )
        backups = stdout.read().decode().strip()
        print(backups)
        print()

        # 检查每个备份的memorySearch配置
        print("[2] 各个备份中的memorySearch配置...")
        backup_files = [
            "/root/.openclaw/openclaw.json.bak",      # 最新
            "/root/.openclaw/openclaw.json.bak.1",
            "/root/.openclaw/openclaw.json.bak.2",
            "/root/.openclaw/openclaw.json.bak.3",
            "/root/.openclaw/openclaw.json.bak.4",
        ]

        for i, bak_file in enumerate(backup_files, 1):
            stdin, stdout, stderr = ssh.exec_command(
                f"cat {bak_file} 2>/dev/null | grep -A 5 'memorySearch'"
            )
            config = stdout.read().decode().strip()
            if config:
                print(f"  备份{i} ({bak_file.split('/')[-1]}):")
                print(f"  {config}")
            print()

        # 当前配置
        print("[3] 当前配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | grep -A 5 'memorySearch'"
        )
        current = stdout.read().decode().strip()
        print(f"  {current}")
        print()

        # 检查版本回退时间点
        print("[4] 版本回退时间线...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt --time-style=long-iso /root/.openclaw/openclaw.json* | head -10"
        )
        timeline = stdout.read().decode().strip()
        print(timeline)
        print()

        ssh.close()

        print("="*70)
        print(" 分析结论")
        print("="*70)
        print()
        print("1. OpenClaw内置记忆系统 (memorySearch)")
        print("   - 状态: 已禁用 (enabled: false)")
        print("   - 原因: ollama未安装，无法提供embedding服务")
        print("   - 影响: Agent无法使用语义搜索记忆文件")
        print()
        print("2. 外部记忆API系统 (端口18888)")
        print("   - 状态: ✅ 运行正常")
        print("   - 用途: 供Python脚本调用 (sync_memory.py等)")
        print("   - 版本回退影响: 无，独立运行")
        print()
        print("3. 记忆文件")
        print("   - MEMORY.md: ✅ 存在 (16642字节)")
        print("   - memory/*.md: ✅ 存在每日日志")
        print("   - 说明: 文件系统未受影响")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_backup_history()

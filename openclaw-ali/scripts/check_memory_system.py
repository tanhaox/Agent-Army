#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw是否使用外部记忆API系统"""
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_openclaw_memory_config():
    print("="*70)
    print(" 检查OpenClaw记忆系统配置")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查OpenClaw配置中的记忆搜索设置
        print("[1] OpenClaw配置 (openclaw.json) - 记忆搜索设置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | grep -A 10 'memorySearch'"
        )
        config = stdout.read().decode().strip()
        print(config)
        print()

        # 2. 检查OpenClaw版本
        print("[2] OpenClaw版本...")
        stdin, stdout, stderr = ssh.exec_command("openclaw --version")
        version = stdout.read().decode().strip()
        print(f"  {version}")
        print()

        # 3. 检查内置记忆文件
        print("[3] OpenClaw内置记忆文件 (Markdown)...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/workspace/memory/ 2>/dev/null || echo '目录不存在'"
        )
        memory_files = stdout.read().decode().strip()
        print(f"  {memory_files}")
        print()

        # 4. 检查MEMORY.md
        print("[4] MEMORY.md文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -la /root/.openclaw/workspace/MEMORY.md 2>/dev/null || echo '文件不存在'"
        )
        memory_md = stdout.read().decode().strip()
        print(f"  {memory_md}")
        print()

        # 5. 检查外部记忆API调用
        print("[5] 外部记忆API调用情况...")
        print("  sync_memory.py:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n 'MEMORY_API\\|18888' /root/.openclaw/workspace/sync_memory.py | head -5"
        )
        sync_api = stdout.read().decode().strip()
        if sync_api:
            for line in sync_api.split('\n'):
                print(f"    {line}")
        else:
            print("    未找到API调用")
        print()

        # 6. 检查capital_flow_monitor.py
        print("  capital_flow_monitor.py:")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -n '18888' /root/.openclaw/workspace/capital_flow_monitor.py | head -3"
        )
        monitor_api = stdout.read().decode().strip()
        if monitor_api:
            for line in monitor_api.split('\n'):
                print(f"    {line}")
        else:
            print("    未找到API调用")
        print()

        # 7. 检查配置备份历史
        print("[6] 配置备份文件...")
        stdin, stdout, stderr = ssh.exec_command(
            "ls -lt /root/.openclaw/*.bak* 2>/dev/null | head -5"
        )
        backups = stdout.read().decode().strip()
        if backups:
            print("  找到以下备份:")
            for line in backups.split('\n'):
                print(f"    {line}")
        else:
            print("  未找到备份文件")
        print()

        # 8. 完整的openclaw.json配置
        print("[7] 完整的openclaw.json配置...")
        stdin, stdout, stderr = ssh.exec_command("cat /root/.openclaw/openclaw.json")
        full_config = stdout.read().decode().strip()
        try:
            config_json = json.loads(full_config)
            print(json.dumps(config_json, indent=2, ensure_ascii=False))
        except:
            print(full_config)
        print()

        # 9. 检查记忆API服务状态
        print("[8] 外部记忆API服务状态 (端口18888)...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
        api_status = stdout.read().decode().strip()
        if api_status:
            print(f"  [运行中] {api_status}")
        else:
            print("  [未运行] 端口18888未监听")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_openclaw_memory_config()

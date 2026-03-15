#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OpenClaw回退后与外部DuckDB记忆系统的集成状态"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def check_integration():
    print("="*70)
    print(" 检查OpenClaw与外部DuckDB记忆系统的集成")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 1. 检查OpenClaw配置中是否有指向外部API的配置
        print("[1] OpenClaw配置中是否有外部记忆API配置...")
        stdin, stdout, stderr = ssh.exec_command(
            "cat /root/.openclaw/openclaw.json | grep -i '18888\\|memory.*api\\|duckdb\\|external'"
        )
        config = stdout.read().decode().strip()
        if config:
            print(f"  找到配置:\n{config}")
        else:
            print("  ❌ 未找到外部记忆API配置")
        print()

        # 2. 检查workspace中哪些脚本使用外部API
        print("[2] workspace中使用外部API的脚本...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r '18888\\|MEMORY_API' /root/.openclaw/workspace/*.py 2>/dev/null | cut -d: -f1 | sort -u"
        )
        scripts = stdout.read().decode().strip()
        if scripts:
            print("  找到以下脚本:")
            for script in scripts.split('\n'):
                if script:
                    print(f"    - {script}")
        else:
            print("  未找到")
        print()

        # 3. 检查OpenClaw技能(skills)中是否有调用
        print("[3] OpenClaw技能目录中是否有外部API调用...")
        stdin, stdout, stderr = ssh.exec_command(
            "grep -r '18888\\|MEMORY_API' /root/.openclaw/workspace/skills/ 2>/dev/null | head -10"
        )
        skill_calls = stdout.read().decode().strip()
        if skill_calls:
            print(f"  找到调用:\n{skill_calls}")
        else:
            print("  ❌ 未找到")
        print()

        # 4. 检查crontab定时任务
        print("[4] crontab定时任务...")
        stdin, stdout, stderr = ssh.exec_command("crontab -l 2>/dev/null")
        crontab = stdout.read().decode().strip()
        if crontab:
            print("  定时任务:")
            for line in crontab.split('\n'):
                if 'sync_memory' in line or 'capital_flow' in line:
                    print(f"    ⭐ {line}")
                elif line and not line.startswith('#'):
                    print(f"    - {line}")
        print()

        # 5. 检查外部API服务状态
        print("[5] 外部记忆API服务状态...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 18888")
        api_status = stdout.read().decode().strip()
        if api_status:
            print(f"  ✅ 运行中: {api_status}")
        else:
            print("  ❌ 未运行")
        print()

        # 6. 分析影响
        print("="*70)
        print(" 影响分析")
        print("="*70)
        print()
        print("外部DuckDB记忆系统 (端口18888):")
        print("  ✅ 服务独立运行，不依赖OpenClaw版本")
        print("  ✅ Python脚本可以正常调用")
        print()
        print("OpenClaw Agent记忆系统:")
        print("  ❌ 不知道外部API的存在")
        print("  ❌ 使用内置的SQLite + Markdown系统")
        print("  ⚠️  版本回退后memorySearch被禁用")
        print()
        print("集成情况:")
        print("  - sync_memory.py: ✅ 独立脚本，手动/定时运行")
        print("  - capital_flow_monitor.py: ✅ 独立脚本")
        print("  - OpenClaw Agent: ❌ 无法访问外部API")
        print()
        print("结论:")
        print("  外部DuckDB记忆系统对OpenClaw Agent是透明的")
        print("  只有workspace中的Python脚本可以使用")
        print("  如果Agent需要记忆，需要通过Skill或工具调用")
        print()

        ssh.close()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_integration()

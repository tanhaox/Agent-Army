#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动启动脚本 - 每次 Claude Code 对话时自动执行

功能：
- 自动启动 Backup Agent 后台服务
- 检查服务状态
- 显示下次备份时间

作者：Backup Agent
创建日期：2026-02-27
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def is_backup_agent_running():
    """检查 Backup Agent 是否在运行"""
    try:
        result = subprocess.run(
            ['tasklist'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        return 'pythonw.exe' in result.stdout or 'python.exe' in result.stdout
    except:
        return False


def start_backup_agent():
    """启动 Backup Agent 后台服务"""
    try:
        # 获取 Backup Agent 路径
        agent_dir = r'C:\AI-Agent-Local\projects\tools\backup-agent'
        agent_script = os.path.join(agent_dir, 'backup_agent.py')

        if not os.path.exists(agent_script):
            print(f"⚠️  Backup Agent 未找到: {agent_script}")
            return False

        # 启动后台服务
        subprocess.Popen(
            ['pythonw', agent_script, '--daemon'],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=agent_dir
        )

        # 等待启动
        time.sleep(2)
        return True

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False


def get_next_backup_time():
    """获取下次备份时间"""
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0)
    next_hour = next_hour.replace(hour=now.hour + 1)
    return next_hour.strftime('%H:%M')


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" 🤖 Backup Agent 自动启动")
    print("=" * 60)

    # 检查是否已在运行
    if is_backup_agent_running():
        print("\n✅ Backup Agent 已在运行")
    else:
        print("\n📋 正在启动 Backup Agent...")
        if start_backup_agent():
            print("✅ Backup Agent 启动成功")
        else:
            print("❌ Backup Agent 启动失败")
            return 1

    # 显示状态信息
    print(f"\n📁 监控路径: C:\\AI-Agent-Local")
    print(f"📝 监控目录: docs/improvements/")
    print(f"🕐 下次备份: {get_next_backup_time()}")
    print(f"🔄 自动备份: 每小时整点 + 改进意见触发")
    print("\n" + "=" * 60 + "\n")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速备份脚本 - 由 AI 主动调用触发备份

使用场景：
- AI 检测到对话中包含关键词（bug、修复、优化等）
- AI 在执行任务前先调用此脚本备份
- 确保代码安全

作者：Backup Agent
创建日期：2026-02-27
"""

import os
import sys
import subprocess
from datetime import datetime

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加当前目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from git_manager import GitManager
from config import Config
from logger import Logger


def quick_backup(reason="关键词触发"):
    """
    执行快速备份

    Args:
        reason: 备份原因

    Returns:
        str: Git commit hash
    """
    # 初始化
    config_obj = Config()

    # 初始化日志
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    logger = Logger(log_dir)

    # 获取配置
    config = config_obj.get_config()

    # 检查是否有修改
    repo_path = config_obj.get('monitor_path')
    git_manager = GitManager(repo_path, config)

    # 检查状态
    status = git_manager.get_status()
    has_changes = status.get('is_dirty', False) or status.get('untracked_files', 0) > 0

    if not has_changes:
        print("📝 当前没有修改，无需备份")
        return None

    # 显示备份信息
    print(f"\n{'='*60}")
    print(f" 🤖 AI 触发的快速备份")
    print(f"{'='*60}")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 原因: {reason}")
    print(f"📁 路径: {config_obj.get('monitor_path')}")
    print(f"{'='*60}\n")

    # 执行备份
    try:
        print("⏳ 正在备份...")
        commit_hash = git_manager.backup("ai_trigger", reason)
        print(f"✅ 备份成功！")
        print(f"📦 Commit: {commit_hash}")
        print(f"{'='*60}\n")

        logger.info(f"AI 触发备份: {reason} -> {commit_hash}")
        return commit_hash

    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        logger.error(f"AI 触发备份失败: {str(e)}")
        return None


if __name__ == "__main__":
    # 从命令行参数获取备份原因
    if len(sys.argv) > 1:
        reason = " ".join(sys.argv[1:])
    else:
        reason = "AI 检测到关键词"

    # 执行备份
    quick_backup(reason)

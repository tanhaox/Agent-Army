#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 测试 Backup Agent 核心功能
"""

import sys
import os

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import Config
from git_manager import GitManager
from logger import Logger

def test_basic():
    """测试基本功能"""
    print("=" * 60)
    print(" Backup Agent 基本功能测试")
    print("=" * 60)

    # 测试配置加载
    print("\n[1/4] 测试配置加载...")
    config_manager = Config()
    config = config_manager.get_config()
    print(f"  ✓ 配置加载成功")
    print(f"  监控路径: {config.get('monitor_path')}")

    # 测试日志系统
    print("\n[2/4] 测试日志系统...")
    logger = Logger(os.path.join(current_dir, 'logs'))
    logger.info("测试日志记录")
    print(f"  ✓ 日志系统正常")
    print(f"  日志文件: {logger.get_log_path()}")

    # 测试 Git 管理器
    print("\n[3/4] 测试 Git 管理器...")
    git_manager = GitManager(config.get('monitor_path'), config)
    status = git_manager.get_status()
    print(f"  ✓ Git 管理器正常")
    print(f"  仓库路径: {status['repo_path']}")
    print(f"  当前分支: {status['branch']}")
    print(f"  是否有修改: {'是' if status['is_dirty'] else '否'}")

    # 测试提交历史
    print("\n[4/4] 测试提交历史...")
    commits = git_manager.get_commit_history(hours=24)
    print(f"  ✓ 查询到最近 24 小时内 {len(commits)} 个提交")
    if commits:
        print(f"  最新提交: {commits[0]['message'][:50]}...")

    print("\n" + "=" * 60)
    print(" ✓ 所有测试通过！")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_basic()
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

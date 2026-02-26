#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强功能测试脚本
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
from backup_compressor import BackupCompressor
from logger import Logger

def test_compressor():
    """测试备份压缩功能"""
    print("=" * 60)
    print(" 备份压缩功能测试")
    print("=" * 60)

    # 加载配置
    print("\n[1/4] 加载配置...")
    config_manager = Config()
    config = config_manager.get_config()
    print(f"  ✓ 配置加载成功")

    # 初始化日志
    print("\n[2/4] 初始化日志...")
    logger = Logger(os.path.join(current_dir, 'logs'))
    print(f"  ✓ 日志系统正常")

    # 初始化 Git 管理器
    print("\n[3/4] 初始化 Git 管理器...")
    monitor_path = config.get('monitor_path')
    git_manager = GitManager(monitor_path, config)
    print(f"  ✓ Git 管理器正常")

    # 初始化压缩器
    print("\n[4/4] 初始化压缩器...")
    compressor = BackupCompressor(monitor_path, config, logger)
    print(f"  ✓ 压缩器初始化成功")
    print(f"  压缩目录: {compressor.backup_dir_path}")
    print(f"  保留数量: {compressor.keep_count}")
    print(f"  排除模式: {compressor.exclude_patterns}")

    # 测试压缩包列表
    print("\n[5/5] 查看压缩包列表...")
    backups = compressor.get_backups_list()
    if backups:
        print(f"  找到 {len(backups)} 个压缩包:")
        for backup in backups[:5]:  # 只显示前5个
            print(f"    - {backup['name']} ({backup['time_str']})")
        if len(backups) > 5:
            print(f"    ... 还有 {len(backups) - 5} 个")
    else:
        print(f"  当前没有压缩包")

    print("\n" + "=" * 60)
    print(" ✓ 所有测试通过！")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_compressor()
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

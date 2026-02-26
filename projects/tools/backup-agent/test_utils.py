#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 测试工具函数和边界情况

运行方式:
    python -m pytest test_utils.py -v
    或者
    python test_utils.py
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

from utils import load_notification_messages, format_timestamp, should_exclude_path


def test_load_notification_messages():
    """测试通知消息加载"""
    print("\n[1/5] 测试通知消息加载...")

    # 测试完整配置
    config = {
        'notification': {
            'backup_start': '开始备份',
            'backup_complete': '备份完成'
        }
    }
    start, complete = load_notification_messages(config)
    assert start == '开始备份', f"期望 '开始备份', 得到 '{start}'"
    assert complete == '备份完成', f"期望 '备份完成', 得到 '{complete}'"
    print("  ✓ 完整配置加载正常")

    # 测试默认配置
    config = {}
    start, complete = load_notification_messages(config)
    assert start == '老板，我在备份...', f"期望默认值, 得到 '{start}'"
    assert complete == '老板，我备份好了', f"期望默认值, 得到 '{complete}'"
    print("  ✓ 默认配置加载正常")

    # 测试部分配置
    config = {'notification': {'backup_start': '自定义开始'}}
    start, complete = load_notification_messages(config)
    assert start == '自定义开始'
    assert complete == '老板，我备份好了'  # 默认值
    print("  ✓ 部分配置混合正常")


def test_format_timestamp():
    """测试时间格式化"""
    print("\n[2/5] 测试时间格式化...")

    # 测试默认格式（只有时间）
    ts = format_timestamp()
    assert ':' in ts, f"时间戳应包含冒号: {ts}"
    assert len(ts) == 8, f"默认格式应为 HH:MM:SS (8字符), 得到: {ts}"
    print(f"  ✓ 默认格式: {ts}")

    # 测试包含日期
    ts = format_timestamp(include_date=True)
    assert '-' in ts, f"完整时间戳应包含连字符: {ts}"
    assert ':' in ts, f"完整时间戳应包含冒号: {ts}"
    print(f"  ✓ 完整格式: {ts}")


def test_should_exclude_path():
    """测试路径排除逻辑 - 边界情况"""
    print("\n[3/5] 测试路径排除逻辑...")

    patterns = ['.git', 'node_modules', '__pycache__', '.next', 'github_downloads']

    # 测试直接匹配
    assert should_exclude_path('.git', patterns) == True
    assert should_exclude_path('node_modules', patterns) == True
    print("  ✓ 直接目录匹配正常")

    # 测试路径前缀匹配
    assert should_exclude_path('.git/config', patterns) == True
    assert should_exclude_path('node_modules/package.json', patterns) == True
    assert should_exclude_path('src/node_modules/file.txt', patterns) == True  # 包含 /node_modules/ 应该排除
    assert should_exclude_path('lib/file.js', patterns) == False  # 不包含任何排除模式
    print("  ✓ 路径前缀匹配正常")

    # 测试路径中间匹配（嵌套目录）
    assert should_exclude_path('project/node_modules/file.txt', patterns) == True
    assert should_exclude_path('a/b/c/__pycache__/test.py', patterns) == True
    print("  ✓ 嵌套目录匹配正常")

    # 测试不排除的情况
    assert should_exclude_path('src/main.py', patterns) == False
    assert should_exclude_path('README.md', patterns) == False
    assert should_exclude_path('docs/api.md', patterns) == False
    print("  ✓ 正常路径不排除")

    # 测试 Windows 反斜杠路径
    assert should_exclude_path('.git\\config', patterns) == True
    assert should_exclude_path('node_modules\\package.json', patterns) == True
    assert should_exclude_path('project\\node_modules\\file.txt', patterns) == True
    print("  ✓ Windows 路径兼容正常")

    # 测试边界情况
    assert should_exclude_path('', patterns) == False  # 空路径
    assert should_exclude_path('.', patterns) == False  # 当前目录
    assert should_exclude_path('git', patterns) == False  # 部分匹配（.git vs git）
    assert should_exclude_path('node_module', patterns) == False  # 部分匹配（node_modules vs node_module）
    print("  ✓ 边界情况处理正常")


def test_edge_cases():
    """测试边界情况和特殊情况"""
    print("\n[4/5] 测试边界情况...")

    patterns = ['.git', 'node_modules']

    # 测试特殊字符
    assert should_exclude_path('.git/locks/file.lock', patterns) == True
    assert should_exclude_path('node_modules/@scope/package', patterns) == True
    print("  ✓ 特殊字符路径正常")

    # 测试大小写敏感（Git 在 Windows 上通常大小写不敏感，但路径比较应该保持一致）
    assert should_exclude_path('.GIT/config', patterns) == False  # 大写不应匹配
    assert should_exclude_path('Node_Modules/file', patterns) == False  # 大写不应匹配
    print("  ✓ 大小写敏感正常")

    # 测试点开头的文件 vs 目录
    assert should_exclude_path('.gitignore', ['.git']) == False  # 文件不应匹配目录
    print("  ✓ 文件与目录区分正常")


def test_complex_patterns():
    """测试复杂排除模式"""
    print("\n[5/5] 测试复杂排除模式...")

    # 测试包含通配符的模式（should_exclude_path 不支持通配符，只支持前缀匹配）
    patterns = ['.claude/cache', '.claude/sessions']

    # 测试多级路径排除
    assert should_exclude_path('.claude/cache/session1.json', patterns) == True
    assert should_exclude_path('.claude/sessions/active.json', patterns) == True
    assert should_exclude_path('.claude/config.json', patterns) == False
    print("  ✓ 多级路径排除正常")

    # 测试重叠模式
    patterns = ['test', 'test/temp']
    assert should_exclude_path('test/file.txt', patterns) == True
    assert should_exclude_path('test/temp/file.txt', patterns) == True
    print("  ✓ 重叠模式处理正常")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print(" Backup Agent 单元测试")
    print("=" * 60)

    tests = [
        test_load_notification_messages,
        test_format_timestamp,
        test_should_exclude_path,
        test_edge_cases,
        test_complex_patterns
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ 测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f" 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

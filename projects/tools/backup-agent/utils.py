#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块 - 通用工具函数

功能：
- 通知消息加载
- 时间格式化
- 路径处理

作者：Backup Agent
创建日期：2026-02-27
"""

from datetime import datetime
from typing import Tuple
from functools import lru_cache


def load_notification_messages(config: dict) -> Tuple[str, str]:
    """
    加载通知消息配置

    Args:
        config: 配置字典

    Returns:
        Tuple[str, str]: (backup_start_msg, backup_complete_msg)
    """
    notification = config.get('notification', {})
    backup_start_msg = notification.get('backup_start', '老板，我在备份...')
    backup_complete_msg = notification.get('backup_complete', '老板，我备份好了')
    return backup_start_msg, backup_complete_msg


def format_timestamp(include_date: bool = False) -> str:
    """
    格式化当前时间戳

    Args:
        include_date: 是否包含日期

    Returns:
        str: 格式化的时间字符串
    """
    if include_date:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return datetime.now().strftime('%H:%M:%S')


def should_exclude_path(filepath: str, exclude_patterns: list) -> bool:
    """
    判断文件路径是否应该被排除

    使用 LRU 缓存优化性能，缓存最近 1024 次调用的结果

    Args:
        filepath: 文件路径（支持 / 和 \\ 分隔符）
        exclude_patterns: 排除模式列表

    Returns:
        bool: True 表示排除，False 表示不排除
    """
    # 将 list 转为 tuple 以便缓存（list 不可哈希）
    return _should_exclude_path_cached(filepath, tuple(exclude_patterns))


@lru_cache(maxsize=1024)
def _should_exclude_path_cached(filepath: str, exclude_patterns: tuple) -> bool:
    """
    判断文件路径是否应该被排除（内部缓存函数）

    Args:
        filepath: 文件路径（支持 / 和 \\ 分隔符）
        exclude_patterns: 排除模式元组（可哈希）

    Returns:
        bool: True 表示排除，False 表示不排除
    """
    # 统一路径分隔符
    normalized_path = filepath.replace('\\', '/')

    for pattern in exclude_patterns:
        # 确保模式也是 / 分隔符
        normalized_pattern = pattern.replace('\\', '/')

        # 检查路径是否以模式开头（作为目录）
        # 或者模式完整匹配路径的某个部分
        if normalized_path.startswith(normalized_pattern + '/') or normalized_path == normalized_pattern:
            return True

        # 检查路径中是否包含模式（处理 /node_modules/ 情况）
        if '/' + normalized_pattern + '/' in normalized_path:
            return True

    return False

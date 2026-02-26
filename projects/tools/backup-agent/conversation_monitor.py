#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话监控模块 - 负责监控改进意见文档创建

功能：
- 监控 docs/improvements/ 目录
- 检测新文件创建（待改进-*.md）
- 触发备份

作者：Backup Agent
创建日期：2026-02-26
"""

import os
import re
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from git_manager import GitManager
from utils import load_notification_messages, format_timestamp


class ImprovementFileHandler(FileSystemEventHandler):
    """改进意见文件处理器"""

    def __init__(self, git_manager: GitManager, config: dict, logger=None):
        """
        初始化文件处理器

        Args:
            git_manager: Git 管理器实例
            config: 配置字典
            logger: 日志记录器（可选）
        """
        self.git_manager = git_manager
        self.config = config
        self.logger = logger
        self.last_backup_time = 0

        # 获取通知消息
        self.backup_start_msg, self.backup_complete_msg = load_notification_messages(config)

        # 冷却期（秒），防止频繁触发
        self.cooldown = config.get('backup_cooldown', 60)  # 默认 60 秒

        # 文件名匹配模式：从配置读取
        patterns = config.get('file_monitor', {}).get('improvement_filename_patterns',
                                                       [r'^(待改进|进行中)-.*\.md$'])
        # 编译所有正则模式
        self.filename_patterns = [re.compile(pattern) for pattern in patterns]

    def on_created(self, event):
        """
        文件创建事件处理

        Args:
            event: 文件事件
        """
        # 只处理文件，不处理目录
        if event.is_directory:
            return

        # 检查是否是改进意见文档
        filename = os.path.basename(event.src_path)

        # 使用配置的多个正则模式匹配文件名
        for pattern in self.filename_patterns:
            if pattern.match(filename):
                self._trigger_backup("改进意见", filename)
                break

    def _trigger_backup(self, trigger_type: str, filename: str):
        """
        触发备份

        Args:
            trigger_type: 触发类型
            filename: 文件名
        """
        current_time = time.time()

        # 检查冷却期
        if current_time - self.last_backup_time < self.cooldown:
            ts = format_timestamp()
            print(f"\n[{ts}] ⏸️ 冷却期内，跳过备份")
            return

        try:
            # 执行备份
            ts = format_timestamp()
            print(f"\n[{ts}] 📝 检测到改进意见文档: {filename}")
            print(f"[{ts}] {self.backup_start_msg}")

            commit_msg = self.git_manager.backup("improvement")

            print(f"[{ts}] {self.backup_complete_msg}")
            print(f"[{ts}] 💾 备份成功: {commit_msg}")

            # 记录日志
            if self.logger:
                self.logger.info(f"改进意见触发备份: {commit_msg}")

            # 更新最后备份时间
            self.last_backup_time = current_time

        except Exception as e:
            ts = format_timestamp()
            print(f"[{ts}] ❌ 备份失败: {str(e)}")
            if self.logger:
                self.logger.error(f"改进意见触发备份失败: {str(e)}")


class ConversationMonitor:
    """对话监控器"""

    def __init__(self, git_manager: GitManager, config: dict, logger=None):
        """
        初始化对话监控器

        Args:
            git_manager: Git 管理器实例
            config: 配置字典
            logger: 日志记录器（可选）
        """
        self.git_manager = git_manager
        self.config = config
        self.logger = logger
        self.running = False

        # 监控路径
        self.monitor_path = os.path.join(
            config.get('monitor_path', '.'),
            'docs',
            'improvements'
        )

        # 确保监控目录存在
        if not os.path.exists(self.monitor_path):
            os.makedirs(self.monitor_path, exist_ok=True)

        # 创建事件处理器和观察者
        self.event_handler = ImprovementFileHandler(git_manager, config, logger)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.monitor_path, recursive=False)

    def start(self):
        """启动监控"""
        if self.running:
            print("⚠️ 监控器已在运行")
            return

        self.observer.start()
        self.running = True
        print(f"📝 对话监控已启动: {self.monitor_path}")

    def stop(self):
        """停止监控"""
        if not self.running:
            return

        self.observer.stop()
        self.observer.join()
        self.running = False
        print("🛑 对话监控已停止")

    def run(self):
        """运行监控循环"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

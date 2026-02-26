#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块 - 负责整点定时备份

功能：
- 每小时整点执行备份
- 检查文件修改
- 自动执行备份

作者：Backup Agent
创建日期：2026-02-26
"""

import schedule
import time
from datetime import datetime
from git_manager import GitManager
from utils import load_notification_messages, format_timestamp


class Scheduler:
    """定时任务调度器"""

    def __init__(self, git_manager: GitManager, config: dict, logger=None, compressor=None):
        """
        初始化调度器

        Args:
            git_manager: Git 管理器实例
            config: 配置字典
            logger: 日志记录器（可选）
            compressor: 压缩器实例（可选）
        """
        self.git_manager = git_manager
        self.config = config
        self.logger = logger
        self.compressor = compressor
        self.running = False

        # 获取通知消息
        self.backup_start_msg, self.backup_complete_msg = load_notification_messages(config)

    def hourly_backup(self):
        """整点备份任务"""
        try:
            # 检查是否有修改
            if self.git_manager.has_changes():
                # 执行备份
                ts = format_timestamp()
                print(f"\n[{ts}] 🕐 整点备份检查...")
                print(f"[{ts}] {self.backup_start_msg}")

                commit_msg = self.git_manager.backup("hourly")

                print(f"[{ts}] {self.backup_complete_msg}")
                print(f"[{ts}] 💾 备份成功: {commit_msg}")

                # 记录日志
                if self.logger:
                    self.logger.info(f"整点备份: {commit_msg}")

                # 触发压缩备份
                if self.compressor:
                    try:
                        # 获取修改的文件列表（从 Git diff）
                        changed_files = self._get_changed_files()
                        if changed_files:
                            print(f"[{ts}] 📦 正在创建压缩包...")
                            zip_path = self.compressor.compress_backup(changed_files)
                            if zip_path:
                                print(f"[{ts}] ✅ 压缩包创建成功")
                                if self.logger:
                                    self.logger.info(f"压缩备份: {zip_path}")
                            else:
                                print(f"[{ts}] ⚠️ 无修改文件，跳过压缩")
                    except Exception as e:
                        print(f"[{ts}] ❌ 压缩失败: {str(e)}")
                        if self.logger:
                            self.logger.error(f"压缩备份失败: {str(e)}")
            else:
                # 无修改，跳过
                ts = format_timestamp()
                print(f"\n[{ts}] 🕐 整点备份检查: 无修改，跳过")

        except Exception as e:
            ts = format_timestamp()
            print(f"❌ 整点备份失败: {str(e)}")
            if self.logger:
                self.logger.error(f"整点备份失败: {str(e)}")

    def _get_changed_files(self) -> list:
        """
        获取自上次提交以来修改的文件

        Returns:
            list: 修改的文件列表
        """
        try:
            # 获取当前 HEAD
            current_head = self.git_manager.repo.head.commit

            # 获取所有修改的文件（相对于工作目录）
            changed_files = []

            # 获取未暂存的修改
            for item in current_head.diff(None):
                if item.a_path:
                    changed_files.append(item.a_path)
                if item.b_path:
                    changed_files.append(item.b_path)

            # 获取未跟踪的文件
            changed_files.extend(self.git_manager.repo.untracked_files)

            # 去重
            changed_files = list(set(changed_files))

            return changed_files

        except Exception as e:
            if self.logger:
                self.logger.error(f"获取修改文件列表失败: {str(e)}")
            return []

    def start(self):
        """启动调度器"""
        if self.running:
            print("⚠️ 调度器已在运行")
            return

        # 设置每小时整点执行
        schedule.every().hour.at(":00").do(self.hourly_backup)

        # 立即执行一次检查（如果到了整点）
        now = datetime.now()
        if now.minute == 0:
            self.hourly_backup()

        self.running = True
        print(f"🕐 定时任务已启动: 每小时整点备份")

    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        print("🛑 定时任务已停止")

    def run(self):
        """运行调度循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 负责日志记录

功能：
- 记录到文件
- 支持日志级别
- UTF-8 编码支持中文

作者：Backup Agent
创建日期：2026-02-26
"""

import os
import logging
from datetime import datetime


class Logger:
    """日志记录器"""

    def __init__(self, log_dir: str, log_file: str = "backup-agent.log"):
        """
        初始化日志记录器

        Args:
            log_dir: 日志目录
            log_file: 日志文件名
        """
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 日志文件路径
        self.log_path = os.path.join(log_dir, log_file)

        # 创建日志记录器
        self.logger = logging.getLogger('BackupAgent')
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 创建文件处理器（UTF-8 编码）
        file_handler = logging.FileHandler(
            self.log_path,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 记录启动信息
        self.info("=" * 60)
        self.info("Backup Agent 日志系统启动")
        self.info(f"日志文件: {self.log_path}")
        self.info("=" * 60)

    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """记录 INFO 级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self.logger.error(message)

    def critical(self, message: str):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(message)

    def get_log_path(self) -> str:
        """获取日志文件路径"""
        return self.log_path

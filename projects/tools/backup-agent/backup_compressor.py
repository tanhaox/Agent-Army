#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份压缩模块 - 负责创建和管理备份压缩包

功能：
- 获取 Git 修改的文件列表
- 创建 ZIP 压缩包
- 自动清理旧压缩包

作者：Backup Agent
创建日期：2026-02-26
"""

import os
import zipfile
from datetime import datetime
from typing import List, Optional


class BackupCompressor:
    """备份压缩器"""

    def __init__(self, repo_path: str, config: dict, logger=None):
        """
        初始化备份压缩器

        Args:
            repo_path: 仓库路径
            config: 配置字典
            logger: 日志记录器（可选）
        """
        self.repo_path = repo_path
        self.config = config
        self.logger = logger

        # 压缩配置
        compression_config = config.get('backup_compression', {})
        self.enabled = compression_config.get('enabled', True)
        self.backup_dir = compression_config.get('backup_dir', 'backups')
        self.keep_count = compression_config.get('keep_count', 10)
        self.exclude_patterns = compression_config.get('exclude_patterns', [])

        # 确保备份目录存在
        self.backup_dir_path = os.path.join(
            os.path.dirname(__file__),
            self.backup_dir
        )
        if not os.path.exists(self.backup_dir_path):
            os.makedirs(self.backup_dir_path, exist_ok=True)

    def compress_backup(self, changed_files: List[str]) -> Optional[str]:
        """
        压缩备份

        Args:
            changed_files: 修改的文件列表（相对于仓库根目录）

        Returns:
            str: 压缩包路径，如果失败则返回 None
        """
        if not self.enabled or not changed_files:
            return None

        try:
            # 生成压缩包名称
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            zip_name = f"backup-agent-{timestamp}.zip"
            zip_path = os.path.join(self.backup_dir_path, zip_name)

            # 创建压缩包
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in changed_files:
                    # 过滤排除的文件
                    if self._should_exclude(file_path):
                        continue

                    full_path = os.path.join(self.repo_path, file_path)

                    # 只压缩存在的文件
                    if os.path.exists(full_path) and os.path.isfile(full_path):
                        arcname = file_path  # 保持相对路径
                        zipf.write(full_path, arcname)

            # 记录日志
            if self.logger:
                self.logger.info(f"创建压缩包: {zip_name} ({len(changed_files)} 个文件)")

            # 自动清理旧压缩包
            self._cleanup_old_backups()

            return zip_path

        except Exception as e:
            if self.logger:
                self.logger.error(f"创建压缩包失败: {str(e)}")
            return None

    def _should_exclude(self, file_path: str) -> bool:
        """
        检查文件是否应该被排除

        Args:
            file_path: 文件路径

        Returns:
            bool: True 表示排除，False 表示不排除
        """
        for pattern in self.exclude_patterns:
            if pattern in file_path:
                return True
        return False

    def _cleanup_old_backups(self):
        """清理旧压缩包，保留最近的 N 个"""
        try:
            # 获取所有压缩包
            zip_files = []
            for file in os.listdir(self.backup_dir_path):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir_path, file)
                    mtime = os.path.getmtime(file_path)
                    zip_files.append((file_path, mtime, file))

            # 如果压缩包数量超过保留数量，删除旧的
            if len(zip_files) > self.keep_count:
                # 按修改时间排序（旧的在前）
                zip_files.sort(key=lambda x: x[1])

                # 计算需要删除的数量
                delete_count = len(zip_files) - self.keep_count

                # 删除旧压缩包
                for i in range(delete_count):
                    file_path, _, file_name = zip_files[i]
                    os.remove(file_path)
                    if self.logger:
                        self.logger.info(f"删除旧压缩包: {file_name}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"清理旧压缩包失败: {str(e)}")

    def get_backup_count(self) -> int:
        """
        获取当前压缩包数量

        Returns:
            int: 压缩包数量
        """
        try:
            count = 0
            for file in os.listdir(self.backup_dir_path):
                if file.endswith('.zip'):
                    count += 1
            return count
        except:
            return 0

    def get_backups_list(self) -> List[dict]:
        """
        获取压缩包列表

        Returns:
            List[dict]: 压缩包信息列表
        """
        try:
            backups = []
            for file in os.listdir(self.backup_dir_path):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir_path, file)
                    mtime = os.path.getmtime(file_path)
                    size = os.path.getsize(file_path)

                    backups.append({
                        'name': file,
                        'path': file_path,
                        'size': size,
                        'mtime': mtime,
                        'time_str': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })

            # 按修改时间排序（新的在前）
            backups.sort(key=lambda x: x['mtime'], reverse=True)

            return backups
        except:
            return []

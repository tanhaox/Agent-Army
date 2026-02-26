#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载模块 - 负责加载和管理配置

功能：
- 加载配置文件
- 提供配置访问接口
- 验证配置有效性

作者：Backup Agent
创建日期：2026-02-26
"""

import json
import os


class Config:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        "monitor_path": "C:\\AI-Agent-Local",
        "backup_intervals": {
            "hourly": True
        },
        "keywords": [
            "方案", "bug", "漏洞", "升级", "修复",
            "添加功能", "改进", "开发", "实现",
            "重构", "优化", "部署", "更新"
        ],
        "commit_message_template": "💾 [{type}] 在检测到'{keyword}'讨论前 - {date}",
        "notification": {
            "backup_start": "老板，我在备份...",
            "backup_complete": "老板，我备份好了"
        },
        "rollback": {
            "list_hours": 12
        },
        "git": {
            "auto_init": True,
            "user_name": "Backup Agent",
            "user_email": "backup-agent@local"
        },
        "backup_cooldown": 60
    }

    def __init__(self, config_file: str = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径（可选）
        """
        self.config_file = config_file or self._find_config_file()
        self.config = self._load_config()

    def _find_config_file(self) -> str:
        """
        查找配置文件

        Returns:
            str: 配置文件路径
        """
        # 当前目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'config.json')

        if os.path.exists(config_path):
            return config_path

        # 如果不存在，返回默认路径
        return config_path

    def _load_config(self) -> dict:
        """
        加载配置

        Returns:
            dict: 配置字典
        """
        # 如果配置文件不存在，使用默认配置
        if not os.path.exists(self.config_file):
            print(f"⚠️ 配置文件不存在: {self.config_file}")
            print(f"📝 将使用默认配置")
            return self.DEFAULT_CONFIG.copy()

        # 加载配置文件
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 合并默认配置（确保所有必需的键都存在）
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value

            return config

        except Exception as e:
            print(f"❌ 加载配置文件失败: {str(e)}")
            print(f"📝 将使用默认配置")
            return self.DEFAULT_CONFIG.copy()

    def get(self, key: str, default=None):
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')

        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value):
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')

        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {str(e)}")

    def get_config(self) -> dict:
        """
        获取完整配置

        Returns:
            dict: 配置字典
        """
        return self.config

"""
Agent Army - 配置管理
加载和管理YAML配置文件
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv


class ConfigManager:
    """
    配置管理器
    负责加载和管理所有配置文件
    """

    def __init__(self, config_dir: str = "./config"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self._configs: Dict[str, Any] = {}

        # 加载环境变量
        load_dotenv()

        # 自动加载所有配置文件
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """加载所有配置文件"""
        config_files = {
            "database": "database.yaml",
            "api_keys": "api_keys.yaml",
            "logging": "logging.yaml",
            "agents": "agents.yaml",
        }

        for key, filename in config_files.items():
            config_path = self.config_dir / filename
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    self._configs[key] = yaml.safe_load(f)

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        递归替换配置中的环境变量

        Args:
            config: 配置值

        Returns:
            替换后的配置值
        """
        if isinstance(config, str):
            # 匹配 ${VAR_NAME} 格式
            if config.startswith("${") and config.endswith("}"):
                env_var = config[2:-1]
                return os.getenv(env_var, config)
            return config
        elif isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键,支持点号分隔的路径 (如 "database.postgresql.host")
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._configs

        try:
            for k in keys:
                value = value[k]

            # 替换环境变量
            value = self._substitute_env_vars(value)
            return value
        except (KeyError, TypeError):
            return default

    def get_database_config(self, env: str = "local") -> Dict[str, Any]:
        """
        获取数据库配置

        Args:
            env: 环境名称 (local, production)

        Returns:
            数据库配置
        """
        return self.get(f"database.{env}", {})

    def get_api_config(self, provider: str) -> Dict[str, Any]:
        """
        获取API配置

        Args:
            provider: 提供商名称 (zhipu, deepseek, openai)

        Returns:
            API配置
        """
        return self.get(f"api_keys.{provider}", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置

        Returns:
            日志配置
        """
        return self.get("logging", {})

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        获取Agent配置

        Args:
            agent_name: Agent名称

        Returns:
            Agent配置
        """
        return self.get(f"agents.{agent_name}", {})

    def reload(self) -> None:
        """重新加载所有配置"""
        self._configs.clear()
        self._load_all_configs()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str = "./config") -> ConfigManager:
    """
    获取全局配置管理器实例

    Args:
        config_dir: 配置文件目录

    Returns:
        配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager

"""
Agent Army - Config Module
配置管理模块

同时支持:
- v2.0: model_config_v2.py (包月版，质量优先)
- v1.0: model_config.py (按量版，成本优化)
- ConfigManager: config.py (YAML配置管理)
"""

import sys
from pathlib import Path
import importlib.util

# 导入 ConfigManager (从父目录的config.py)
# 注意：由于包名冲突（config/目录 vs config.py），需要使用动态导入
config_base_path = Path(__file__).parent.parent / 'config.py'
spec = importlib.util.spec_from_file_location("src.core.config_base", str(config_base_path))
if spec and spec.loader:
    config_base_module = importlib.util.module_from_spec(spec)
    sys.modules['src.core.config_base'] = config_base_module
    try:
        spec.loader.exec_module(config_base_module)
        ConfigManager = config_base_module.ConfigManager
    except Exception as e:
        print(f"警告: ConfigManager加载失败: {e}")
        ConfigManager = None
else:
    ConfigManager = None

# ========== v2.0 导入（默认） ==========
from .model_config_v2 import (
    ModelType,
    DEFAULT_MODEL,
    SPECIAL_AGENTS,
    MODEL_MAPPING,
    MODEL_CONFIGS,
    CONCURRENCY_LIMITS,
    get_model_type,
    get_model_name,
    get_model_config as get_model_config_v2,
    get_concurrency_limit,
    get_all_agents_by_model,
    get_statistics,
    get_model_for_agents,
    group_agents_by_model
)

# ========== v1.0 导入（向后兼容） ==========
from .model_config import (
    ModelTier,
    ModelConfig,
    AGENT_MODEL_CONFIG,
    get_model_stats as get_model_stats_v1,
    get_agent_config as get_agent_config_v1,
    recommend_model
)

# ========== 统一接口 ==========
def get_model_config(agent_id: str):
    """获取Agent配置（统一接口，优先使用v2）"""
    try:
        return get_model_config_v2(agent_id)
    except:
        return get_agent_config_v1(agent_id)

__all__ = [
    # 重要！向后兼容
    'ConfigManager',

    # v2.0 (默认 - 包月版)
    'ModelType',
    'DEFAULT_MODEL',
    'SPECIAL_AGENTS',
    'MODEL_MAPPING',
    'MODEL_CONFIGS',
    'CONCURRENCY_LIMITS',
    'get_model_type',
    'get_model_name',
    'get_model_config',
    'get_concurrency_limit',
    'get_all_agents_by_model',
    'get_statistics',
    'get_model_for_agents',
    'group_agents_by_model',

    # v1.0 (向后兼容)
    'ModelTier',
    'ModelConfig',
    'AGENT_MODEL_CONFIG',
    'recommend_model',

    # 别名
    'get_model_stats',
    'get_agent_config',
]

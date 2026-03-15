"""
自我进化系统

包含三个核心模式：
1. 经验积累模式 - 记录完整投资路径
2. 参数优化模式 - 根据验证结果调整参数
3. 模式发现模式 - 发现新的投资模式

职责：
- 建立投资经验数据库
- 自动优化系统参数
- 发现和验证新的投资模式
"""

from .experience_accumulation_ai import ExperienceAccumulationAI
from .parameter_optimization_ai import ParameterOptimizationAI
from .pattern_discovery_ai import PatternDiscoveryAI

__all__ = [
    "ExperienceAccumulationAI",
    "ParameterOptimizationAI",
    "PatternDiscoveryAI",
]

"""
优化部Agent模块
Optimization Corps Agents

包含3个Agent：
1. SelfEvolutionAI - 自我进化AI（经验积累 + 参数优化 + 模式识别）
2. ConfigurationOptimizationAI - 配置优化AI（资产配置优化 + 机会筛选）
3. ChipAnalysisAI - 筹码分析AI（筹码分布分析）
"""

from .self_evolution_ai import SelfEvolutionAI
from .configuration_optimization_ai import ConfigurationOptimizationAI
from .chip_analysis_ai import ChipAnalysisAI

__all__ = [
    "SelfEvolutionAI",
    "ConfigurationOptimizationAI",
    "ChipAnalysisAI",
]

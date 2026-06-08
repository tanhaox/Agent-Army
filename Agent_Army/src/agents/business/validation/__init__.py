"""
验证部 - Validation Department

验证部包含2个AI Agent:
1. 验证回测AI (ValidationBacktestAI) - 预测验证 + 回测分析
2. 归因期权AI (AttributionOptionAI) - 归因分析 + 期权分析

精简说明：
- 原有4个Agent精简为2个Agent（-50%）
- 验证回测AI = 预测验证AI + 回测分析AI（2合1）
- 归因期权AI = 归因分析AI + 期权分析AI（2合1）
"""

from src.agents.business.validation.validation_backtest_ai import (
    ValidationBacktestAI,
    analyze_validation_backtest
)
from src.agents.business.validation.attribution_option_ai import (
    AttributionOptionAI,
    analyze_attribution_option
)

__all__ = [
    # Agent类
    "ValidationBacktestAI",
    "AttributionOptionAI",

    # 便捷函数
    "analyze_validation_backtest",
    "analyze_attribution_option"
]

"""
策略部成员 - Strategy Corps

策略部负责投资策略制定和执行，包含4个核心Agent：
1. 时机判断AI (TimingJudgmentAI) - 买卖时机判断
2. 仓位管理AI (PositionManagementAI) - 仓位大小和分配
3. 风控AI (RiskControlAI) - 风险控制和止损策略
4. 策略评估AI (StrategyEvaluationAI) - 情景分析和风险时机
"""

from .timing_judgment_ai import TimingJudgmentAI, analyze_timing_judgment
from .position_management_ai import PositionManagementAI, analyze_position_management
from .risk_control_ai import RiskControlAI, analyze_risk_control
from .strategy_evaluation_ai import StrategyEvaluationAI, analyze_strategy_evaluation

__all__ = [
    # Agent类
    "TimingJudgmentAI",
    "PositionManagementAI",
    "RiskControlAI",
    "StrategyEvaluationAI",

    # 便捷函数
    "analyze_timing_judgment",
    "analyze_position_management",
    "analyze_risk_control",
    "analyze_strategy_evaluation",
]

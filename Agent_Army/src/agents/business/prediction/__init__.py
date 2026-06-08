"""
预测部 - Prediction Department

预测部包含3个AI Agent:
1. 估值定价AI (ValuationPricingAI) - 目标定价 + 估值建议
2. 综合评估AI (ComprehensiveEvaluationAI) - 综合评分 + 质量评分
3. 预测AI (PriceForecastAI) - 价格预测 + 利润预测

精简说明：
- 原有6个Agent精简为3个Agent（-50%）
- 估值定价AI = 目标定价AI + 估值建议AI（2合1）
- 综合评估AI = 综合评分AI + 质量评分AI（2合1）
- 预测AI = 价格预测AI + 利润预测AI（2合1）
"""

from src.agents.business.prediction.valuation_pricing_ai import (
    ValuationPricingAI,
    analyze_valuation_pricing
)
from src.agents.business.prediction.comprehensive_evaluation_ai import (
    ComprehensiveEvaluationAI,
    analyze_comprehensive_evaluation
)
from src.agents.business.prediction.price_forecast_ai import (
    PriceForecastAI,
    analyze_price_forecast
)

__all__ = [
    # Agent类
    "ValuationPricingAI",
    "ComprehensiveEvaluationAI",
    "PriceForecastAI",

    # 便捷函数
    "analyze_valuation_pricing",
    "analyze_comprehensive_evaluation",
    "analyze_price_forecast"
]

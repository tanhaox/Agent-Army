"""
买入时机AI - 策略执行军团 (1/4)

⚠️ DEPRECATED: 此Agent已废弃,请使用RiskAndTimingAI代替
迁移指南: docs/MIGRATION_GUIDE_RISK_TIMING.md
废弃日期: 2026-03-14
计划移除日期: 2026-04-14

职责：
- 评估当前买入时机
- 分析价格合理性
- 给出买入建议
- 提供风险提示
"""

from typing import Dict, Any, Optional
from datetime import datetime
import warnings

# 显示废弃警告
warnings.warn(
    "BuyTimingAI已废弃,请使用RiskAndTimingAI代替。"
    "迁移指南: docs/MIGRATION_GUIDE_RISK_TIMING.md"
    "废弃日期: 2026-03-14, 计划移除日期: 2026-04-14",
    DeprecationWarning,
    stacklevel=2
)

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source import FinancialTool


class BuyTimingAI(BusinessAgent):
    """买入时机AI - 策略执行军团 (1/4)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="买入时机AI",
            role="评估买入时机",
            corps="strategy_execution",
            analysis_type="buy_timing",
            capabilities=[
                AgentCapability(
                    name="timing_analysis",
                    description="买入时机分析",
                    input_type="stock_data",
                    output_type="timing_score"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
                    tool_type="library",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("买入时机AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """分析买入时机"""
        self.logger.info(f"开始买入时机分析", extra={"stock_code": stock_code})

        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取财务数据
        financial_data = await self.financial_tool.fetch_financial_data(stock_code, years=1)

        # 业务逻辑：评估买入时机
        timing_score = self._evaluate_timing(financial_data)
        recommendation = self._generate_recommendation(timing_score)

        result = {
            "stock_code": stock_code,
            "stock_name": financial_data["stock_name"],
            "analysis_type": "buy_timing",
            "timestamp": datetime.now().isoformat(),

            # 买入时机评分（0-100）
            "timing_score": timing_score["total"],
            "timing_level": timing_score["level"],

            # 分项评分
            "scores": {
                "valuation": timing_score["valuation"],
                "momentum": timing_score["momentum"],
                "safety": timing_score["safety"]
            },

            # 买入建议
            "recommendation": recommendation["action"],
            "confidence": recommendation["confidence"],
            "reasoning": recommendation["reasoning"],

            # 风险提示
            "warnings": timing_score["warnings"],

            # 总结
            "summary": self._generate_summary(timing_score, recommendation)
        }

        self.logger.info(
            f"买入时机分析完成",
            extra={
                "stock_code": stock_code,
                "timing_score": result["timing_score"],
                "recommendation": result["recommendation"]
            }
        )

        return result

    def _evaluate_timing(self, financial_data: Dict) -> Dict[str, Any]:
        """评估买入时机（业务逻辑）"""
        latest = financial_data["latest"]

        # 估值评分（基于PE，简化版）
        valuation = 70  # 示例：假设估值合理

        # 动量评分（基于增长趋势）
        revenue_growth = latest.get("revenue_growth", 0)
        momentum = min(100, max(0, 50 + revenue_growth * 2))

        # 安全评分（基于负债率）
        debt_ratio = latest.get("debt_ratio", 0)
        safety = max(0, 100 - debt_ratio)

        # 总分
        total = (valuation * 0.4 + momentum * 0.3 + safety * 0.3)

        # 确定等级
        if total >= 75:
            level = "EXCELLENT"
        elif total >= 60:
            level = "GOOD"
        elif total >= 45:
            level = "FAIR"
        else:
            level = "POOR"

        # 风险提示
        warnings = []
        if debt_ratio > 60:
            warnings.append("⚠️ 负债率较高，需谨慎")
        if revenue_growth < 0:
            warnings.append("⚠️ 营收下滑，时机不佳")

        return {
            "total": round(total, 1),
            "level": level,
            "valuation": valuation,
            "momentum": momentum,
            "safety": safety,
            "warnings": warnings if warnings else ["✅ 时机评估正常"]
        }

    def _generate_recommendation(self, timing_score: Dict) -> Dict[str, Any]:
        """生成买入建议（业务逻辑）"""
        total = timing_score["total"]

        if total >= 75:
            return {
                "action": "STRONG_BUY",
                "confidence": 0.8,
                "reasoning": "买入时机优秀，建议积极买入"
            }
        elif total >= 60:
            return {
                "action": "BUY",
                "confidence": 0.7,
                "reasoning": "买入时机良好，可以考虑买入"
            }
        elif total >= 45:
            return {
                "action": "HOLD",
                "confidence": 0.6,
                "reasoning": "买入时机一般，建议观望"
            }
        else:
            return {
                "action": "WAIT",
                "confidence": 0.7,
                "reasoning": "买入时机不佳，建议等待"
            }

    def _generate_summary(self, timing_score: Dict, recommendation: Dict) -> str:
        """生成总结（业务逻辑）"""
        action_map = {
            "STRONG_BUY": "强烈建议买入",
            "BUY": "建议买入",
            "HOLD": "建议观望",
            "WAIT": "建议等待"
        }

        return (
            f"买入时机评分{timing_score['total']}分（{timing_score['level']}），"
            f"{action_map.get(recommendation['action'], '未知')}"
        )


# 便捷函数
async def analyze_buy_timing(stock_code: str) -> Dict[str, Any]:
    """分析买入时机（便捷函数）"""
    ai = BuyTimingAI()
    return await ai.analyze(stock_code)

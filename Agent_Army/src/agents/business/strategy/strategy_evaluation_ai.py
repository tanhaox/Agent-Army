"""
策略评估AI - Strategy Evaluation AI

策略部成员 (4/4)

职责：
1. 情景分析 - 分析不同市场情景下的策略表现
2. 风险时机 - 识别风险时机和机会时机

合并来源：
- 情景分析AI
- 风险时机AI

使用工具：
- MarketTool（市场数据）
- ScenarioModel（情景模型）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class MarketScenario(str, Enum):
    """市场情景"""
    BULL = "牛市"
    BEAR = "熊市"
    RANGE_BOUND = "震荡"
    VOLATILE = "剧烈波动"
    RECOVERY = "复苏"
    CORRECTION = "调整"


class StrategyEvaluationAI(BusinessAgent):
    """
    策略评估AI - 策略部成员 (4/4)

    核心能力:
    1. 情景分析 - 多情景策略表现评估
    2. 时机识别 - 风险时机vs机会时机

    使用工具:
    - MarketTool (市场数据)
    - ScenarioModel (情景模型)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="策略评估AI",
            role="情景分析与风险时机评估",
            corps="strategy",
            analysis_type="strategy_evaluation",
            capabilities=[
                AgentCapability(
                    name="scenario_analysis",
                    description="情景分析",
                    input_type="stock_code",
                    output_type="scenario_performance"
                ),
                AgentCapability(
                    name="timing_evaluation",
                    description="时机评估",
                    input_type="stock_code",
                    output_type="timing_assessment"
                )
            ],
            tools=[
                AgentTool(
                    name="market_tool",
                    description="市场数据工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="scenario_model",
                    description="情景模型工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("策略评估AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行策略评估分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前股价（必需）
                - investment_horizon: 投资期限（可选，短期/中期/长期）
                - strategy_type: 策略类型（可选，价值/成长/动量等）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        current_price = kwargs.get("current_price")
        if not current_price:
            raise ValueError("缺少current_price参数")

        investment_horizon = kwargs.get("investment_horizon", "中期")
        strategy_type = kwargs.get("strategy_type", "价值")

        self.logger.info(
            f"开始策略评估分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "investment_horizon": investment_horizon,
                "strategy_type": strategy_type
            }
        )

        # ========== 1. 当前市场情景识别 ==========
        current_scenario = await self._identify_current_scenario()

        # ========== 2. 情景分析 ==========
        scenario_analysis = await self._analyze_scenarios(
            stock_code,
            current_price,
            strategy_type
        )

        # 将current_scenario添加到scenario_analysis中
        scenario_analysis["current_scenario"] = current_scenario

        # ========== 3. 时机评估 ==========
        timing_evaluation = self._evaluate_timing(
            current_scenario,
            scenario_analysis
        )

        # ========== 4. 策略表现预测 ==========
        performance_forecast = self._forecast_performance(
            scenario_analysis,
            investment_horizon
        )

        # ========== 5. 策略调整建议 ==========
        adjustment_suggestions = self._generate_adjustment_suggestions(
            current_scenario,
            timing_evaluation,
            performance_forecast
        )

        # ========== 6. 风险提示 ==========
        risks = self._identify_risks(
            current_scenario,
            timing_evaluation,
            scenario_analysis
        )

        # ========== 7. 建议 ==========
        recommendations = self._generate_recommendations(
            current_scenario,
            timing_evaluation,
            performance_forecast
        )

        # ========== 8. 构建分析结果 ==========
        details = {
            "current_price": current_price,
            "investment_horizon": investment_horizon,
            "strategy_type": strategy_type,

            # 当前情景
            "current_scenario": current_scenario,

            # 情景分析
            "scenario_analysis": scenario_analysis,

            # 时机评估
            "timing_assessment": timing_evaluation,

            # 表现预测
            "performance_prediction": performance_forecast,

            # 调整建议
            "adjustment_suggestions": adjustment_suggestions,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                current_scenario,
                timing_evaluation,
                performance_forecast
            ),
            confidence=timing_evaluation["confidence"],
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"策略评估分析完成",
            extra={
                "stock_code": stock_code,
                "scenario": current_scenario["scenario"],
                "timing": timing_evaluation["timing_type"]
            }
        )

        return result

    # ========== 当前情景识别 ==========

    async def _identify_current_scenario(self) -> Dict[str, Any]:
        """
        识别当前市场情景

        Returns:
            当前情景
        """
        # TODO: 接入真实市场数据
        # 当前使用模拟数据

        # 市场特征
        market_trend = "震荡上涨"
        volatility = "中等"
        liquidity = "充裕"
        sentiment = "谨慎乐观"

        # 情景判断
        if market_trend == "震荡上涨" and volatility == "中等":
            scenario = MarketScenario.RANGE_BOUND
            scenario_prob = 0.65
        else:
            scenario = MarketScenario.RANGE_BOUND
            scenario_prob = 0.60

        # 情景特征
        characteristics = {
            "trend": market_trend,
            "volatility": volatility,
            "liquidity": liquidity,
            "sentiment": sentiment
        }

        # 持续时间预测
        duration_expectation = "3-6个月"

        return {
            "scenario": scenario.value,
            "probability": round(scenario_prob, 2),
            "characteristics": characteristics,
            "duration": duration_expectation,
            "description": f"当前处于{scenario.value}情景，概率{scenario_prob*100:.0f}%"
        }

    # ========== 情景分析 ==========

    async def _analyze_scenarios(
        self,
        stock_code: str,
        current_price: float,
        strategy_type: str
    ) -> Dict[str, Any]:
        """
        分析不同情景下的策略表现

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            strategy_type: 策略类型

        Returns:
            情景分析结果
        """
        # TODO: 接入真实数据和模型
        # 当前使用模拟数据

        # 定义主要情景
        scenarios = [
            MarketScenario.BULL,
            MarketScenario.RANGE_BOUND,
            MarketScenario.BEAR,
            MarketScenario.VOLATILE
        ]

        scenario_performance = {}

        for scenario in scenarios:
            # 模拟各情景下的表现
            if scenario == MarketScenario.BULL:
                performance = {
                    "expected_return": 0.35,
                    "probability": 0.25,
                    "risk_level": "中",
                    "win_rate": 0.70
                }
            elif scenario == MarketScenario.RANGE_BOUND:
                performance = {
                    "expected_return": 0.10,
                    "probability": 0.40,
                    "risk_level": "低",
                    "win_rate": 0.60
                }
            elif scenario == MarketScenario.BEAR:
                performance = {
                    "expected_return": -0.20,
                    "probability": 0.20,
                    "risk_level": "高",
                    "win_rate": 0.35
                }
            else:  # VOLATILE
                performance = {
                    "expected_return": 0.05,
                    "probability": 0.15,
                    "risk_level": "高",
                    "win_rate": 0.45
                }

            scenario_performance[scenario.value] = performance

        # 加权期望收益
        weighted_return = sum(
            perf["expected_return"] * perf["probability"]
            for perf in scenario_performance.values()
        )

        # 综合风险评估
        avg_risk_score = (
            scenario_performance[MarketScenario.BULL.value]["probability"] * 30 +
            scenario_performance[MarketScenario.BEAR.value]["probability"] * 80 +
            scenario_performance[MarketScenario.VOLATILE.value]["probability"] * 70
        )

        return {
            "scenarios": list(scenario_performance.keys()),
            "scenario_performance": scenario_performance,
            "weighted_return": round(weighted_return, 2),
            "avg_risk_score": round(avg_risk_score, 1),
            "best_scenario": MarketScenario.BULL.value,
            "worst_scenario": MarketScenario.BEAR.value,
            "description": f"加权期望收益{weighted_return*100:.1f}%，最佳情景{MarketScenario.BULL.value}"
        }

    # ========== 时机评估 ==========

    def _evaluate_timing(
        self,
        current_scenario: Dict[str, Any],
        scenario_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估时机

        Args:
            current_scenario: 当前情景
            scenario_analysis: 情景分析

        Returns:
            时机评估
        """
        scenario = current_scenario["scenario"]
        weighted_return = scenario_analysis["weighted_return"]

        # 时机类型判断
        if weighted_return >= 0.20 and scenario in [MarketScenario.BULL.value, MarketScenario.RANGE_BOUND.value]:
            timing_type = "机会时机"
            timing_score = 85
            timing_desc = "当前为较好的入场时机"
        elif weighted_return >= 0.10 and scenario == MarketScenario.RANGE_BOUND.value:
            timing_type = "中性时机"
            timing_score = 65
            timing_desc = "可适度参与，注意节奏"
        elif weighted_return >= 0:
            timing_type = "观察时机"
            timing_score = 45
            timing_desc = "观望为主，等待更好时机"
        else:
            timing_type = "风险时机"
            timing_score = 25
            timing_desc = "风险较高，建议谨慎或回避"

        # 机会窗口
        if timing_type == "机会时机":
            window = "1-3个月"
        elif timing_type == "中性时机":
            window = "2-4周"
        else:
            window = "不确定"

        # 置信度
        confidence = max(0.5, min(0.9, timing_score / 100))

        return {
            "timing_type": timing_type,
            "timing_score": timing_score,
            "timing_description": timing_desc,
            "opportunity_window": window,
            "confidence": round(confidence, 2)
        }

    # ========== 表现预测 ==========

    def _forecast_performance(
        self,
        scenario_analysis: Dict[str, Any],
        investment_horizon: str
    ) -> Dict[str, Any]:
        """
        预测策略表现

        Args:
            scenario_analysis: 情景分析
            investment_horizon: 投资期限

        Returns:
            表现预测
        """
        weighted_return = scenario_analysis["weighted_return"]

        # 根据投资期限调整预测
        if investment_horizon == "短期":
            horizon_factor = 0.6
            time_range = "1-3个月"
        elif investment_horizon == "中期":
            horizon_factor = 1.0
            time_range = "3-12个月"
        else:  # 长期
            horizon_factor = 1.5
            time_range = "1-3年"

        # 预期收益
        expected_return = weighted_return * horizon_factor

        # 收益区间
        if expected_return > 0:
            return_range = [
                round(expected_return * 0.5, 2),
                round(expected_return * 1.5, 2)
            ]
        else:
            return_range = [
                round(expected_return * 1.5, 2),
                round(expected_return * 0.5, 2)
            ]

        # 胜率
        win_rate = 0.60 if expected_return > 0 else 0.40

        return {
            "time_range": time_range,
            "expected_return": round(expected_return, 2),
            "return_range": return_range,
            "win_rate": round(win_rate, 2),
            "description": f"预期{time_range}收益{expected_return*100:.1f}%，胜率{win_rate*100:.0f}%"
        }

    # ========== 策略调整建议 ==========

    def _generate_adjustment_suggestions(
        self,
        current_scenario: Dict[str, Any],
        timing_evaluation: Dict[str, Any],
        performance_forecast: Dict[str, Any]
    ) -> List[str]:
        """
        生成策略调整建议

        Args:
            current_scenario: 当前情景
            timing_evaluation: 时机评估
            performance_forecast: 表现预测

        Returns:
            调整建议列表
        """
        suggestions = []

        timing_type = timing_evaluation["timing_type"]
        expected_return = performance_forecast["expected_return"]

        # 根据时机类型给出建议
        if timing_type == "机会时机":
            suggestions.append("当前为机会时机，可积极布局")
            suggestions.append("建议分批建仓，控制成本")
            if expected_return > 0.25:
                suggestions.append("预期收益较高，可适当提高仓位")
        elif timing_type == "中性时机":
            suggestions.append("时机中性，适度参与")
            suggestions.append("建议轻仓试探，灵活应对")
        elif timing_type == "观察时机":
            suggestions.append("建议观望，等待更好时机")
            suggestions.append("可关注市场变化，择机入场")
        else:  # 风险时机
            suggestions.append("当前为风险时机，建议谨慎")
            suggestions.append("可考虑减仓或空仓观望")
            suggestions.append("等待市场企稳信号")

        return suggestions

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        current_scenario: Dict[str, Any],
        timing_evaluation: Dict[str, Any],
        scenario_analysis: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 情景风险
        scenario = current_scenario["scenario"]
        if scenario == MarketScenario.VOLATILE.value:
            risks.append("市场波动剧烈，注意短期风险")
        elif scenario == MarketScenario.BEAR.value:
            risks.append("熊市情景，下行风险较大")

        # 时机风险
        if timing_evaluation["timing_type"] == "风险时机":
            risks.append("当前为风险时机，不宜重仓")

        # 预测风险
        worst_scenario = scenario_analysis["worst_scenario"]
        worst_return = scenario_analysis["scenario_performance"][worst_scenario]["expected_return"]
        if worst_return < -0.15:
            risks.append(f"最差情景可能亏损{abs(worst_return)*100:.0f}%，注意止损")

        # 模型风险
        risks.append("情景分析基于历史数据，实际可能偏离预测")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        current_scenario: Dict[str, Any],
        timing_evaluation: Dict[str, Any],
        performance_forecast: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 情景建议
        recommendations.append(f"当前市场情景：{current_scenario['description']}")

        # 时机建议
        recommendations.append(f"时机评估：{timing_evaluation['timing_description']}")

        # 策略建议
        timing_type = timing_evaluation["timing_type"]
        if timing_type in ["机会时机", "中性时机"]:
            recommendations.append(f"预期收益：{performance_forecast['description']}")
            recommendations.append("建议设置止损，控制下行风险")
        else:
            recommendations.append("建议保持耐心，等待更好的入场时机")

        return recommendations

    # ========== 辅助方法 ==========

    def _generate_conclusion(
        self,
        current_scenario: Dict[str, Any],
        timing_evaluation: Dict[str, Any],
        performance_forecast: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        return (
            f"当前情景【{current_scenario['scenario']}】，"
            f"时机类型【{timing_evaluation['timing_type']}】，"
            f"预期收益{performance_forecast['expected_return']*100:.1f}%，"
            f"置信度{timing_evaluation['confidence']*100:.0f}%"
        )


# 便捷函数
async def analyze_strategy_evaluation(
    stock_code: str,
    current_price: float,
    investment_horizon: str = "中期",
    strategy_type: str = "价值"
) -> AnalysisResult:
    """
    策略评估分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        investment_horizon: 投资期限
        strategy_type: 策略类型

    Returns:
        分析结果
    """
    ai = StrategyEvaluationAI()
    return await ai.analyze(
        stock_code,
        current_price=current_price,
        investment_horizon=investment_horizon,
        strategy_type=strategy_type
    )

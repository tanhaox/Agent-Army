"""
预测AI - Price Forecast AI

预测部成员 (3/3)

职责：
1. 价格预测 - 未来股价走势预测
2. 利润预测 - 公司利润增长预测

合并来源：
- 价格预测AI
- 利润预测AI

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class PriceForecastAI(BusinessAgent):
    """
    预测AI - 预测部成员 (3/3)

    核心能力:
    1. 价格预测 - 3/6/12个月股价预测
    2. 利润预测 - 公司利润增长预测

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="预测AI",
            role="预测未来股价和利润增长",
            corps="prediction",
            analysis_type="price_forecast",
            capabilities=[
                AgentCapability(
                    name="price_forecast",
                    description="股价预测",
                    input_type="stock_code",
                    output_type="price_forecast"
                ),
                AgentCapability(
                    name="profit_forecast",
                    description="利润预测",
                    input_type="stock_code",
                    output_type="profit_forecast"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
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

        self.logger.info("预测AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行预测分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前股价（必需）
                - forecast_period: 预测周期（默认12m）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        current_price = kwargs.get("current_price")
        if not current_price:
            raise ValueError("缺少current_price参数")

        forecast_period = kwargs.get("forecast_period", "12m")

        self.logger.info(
            f"开始预测分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "forecast_period": forecast_period
            }
        )

        # ========== 1. 价格预测 ==========
        price_forecast = await self._forecast_price(
            stock_code,
            current_price,
            forecast_period
        )

        # ========== 2. 利润预测 ==========
        profit_forecast = await self._forecast_profit(
            stock_code,
            forecast_period
        )

        # ========== 3. 趋势预测 ==========
        trend_forecast = self._forecast_trend(
            price_forecast,
            profit_forecast,
            current_price
        )

        # ========== 4. 情景分析 ==========
        scenario_analysis = self._analyze_scenarios(
            price_forecast,
            profit_forecast,
            current_price
        )

        # ========== 5. 风险提示 ==========
        risks = self._identify_risks(price_forecast, profit_forecast)

        # ========== 6. 建议 ==========
        recommendations = self._generate_recommendations(
            price_forecast,
            profit_forecast,
            trend_forecast
        )

        # ========== 7. 构建分析结果 ==========
        details = {
            "current_price": current_price,
            "forecast_period": forecast_period,

            # 价格预测
            "price_forecast": price_forecast,

            # 利润预测
            "profit_forecast": profit_forecast,

            # 趋势预测
            "trend_forecast": trend_forecast,

            # 情景分析
            "scenario_analysis": scenario_analysis,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(price_forecast, profit_forecast),
            confidence=price_forecast["confidence"],
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"预测分析完成",
            extra={
                "stock_code": stock_code,
                "forecast_price": price_forecast["forecast_price"],
                "upside": price_forecast["upside"]
            }
        )

        return result

    # ========== 价格预测 ==========

    async def _forecast_price(
        self,
        stock_code: str,
        current_price: float,
        forecast_period: str
    ) -> Dict[str, Any]:
        """
        价格预测

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            forecast_period: 预测周期（3m/6m/12m）

        Returns:
            价格预测结果
        """
        # TODO: 接入真实预测模型
        # 当前使用简化的趋势预测

        # 根据预测周期确定时间因子
        period_months = int(forecast_period.replace("m", ""))
        time_factor = period_months / 12  # 年化因子

        # 基于历史趋势的简化预测
        # 假设年化增长率 10-20%
        annual_growth_rate = 0.15  # 15%年化增长

        # 预测价格
        forecast_price = current_price * (1 + annual_growth_rate * time_factor)

        # 计算上行空间
        upside = ((forecast_price - current_price) / current_price) * 100

        # 生成价格区间
        range_width = 0.10 * time_factor  # 时间越长，不确定性越大
        lower_bound = forecast_price * (1 - range_width)
        upper_bound = forecast_price * (1 + range_width)

        # 置信度（时间越长，置信度越低）
        confidence = max(0.5, 0.8 - 0.1 * time_factor)

        # 趋势判断
        if upside > 15:
            trend = "强势上涨"
        elif upside > 5:
            trend = "温和上涨"
        elif upside > -5:
            trend = "横盘震荡"
        elif upside > -15:
            trend = "温和下跌"
        else:
            trend = "弱势下跌"

        return {
            "forecast_price": round(forecast_price, 2),
            "upside": round(upside, 2),
            "price_range": {
                "lower": round(lower_bound, 2),
                "upper": round(upper_bound, 2),
                "width": f"±{round(range_width * 100, 1)}%"
            },
            "trend": trend,
            "confidence": round(confidence, 2),
            "forecast_period": forecast_period,
            "annual_growth_rate": f"{annual_growth_rate * 100:.1f}%",
            "description": f"预计{forecast_period}内股价{trend}，目标价{forecast_price:.2f}元"
        }

    # ========== 利润预测 ==========

    async def _forecast_profit(
        self,
        stock_code: str,
        forecast_period: str
    ) -> Dict[str, Any]:
        """
        利润预测

        Args:
            stock_code: 股票代码
            forecast_period: 预测周期

        Returns:
            利润预测结果
        """
        # TODO: 接入真实财务数据
        # 当前使用模拟数据

        # 历史利润数据（亿元）
        historical_profits = {
            "2023": 50.0,
            "2024": 55.0,
            "2025": 60.0
        }

        # 计算历史增长率
        growth_rates = []
        years = sorted(historical_profits.keys())
        for i in range(1, len(years)):
            prev_profit = historical_profits[years[i-1]]
            curr_profit = historical_profits[years[i]]
            growth_rate = ((curr_profit - prev_profit) / prev_profit) * 100
            growth_rates.append(growth_rate)

        # 平均增长率
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 10.0

        # 预测未来利润
        period_months = int(forecast_period.replace("m", ""))
        forecast_years = period_months / 12

        last_profit = historical_profits[max(historical_profits.keys())]
        forecast_profit = last_profit * (1 + avg_growth_rate / 100 * forecast_years)

        # 利润增长
        profit_growth = ((forecast_profit - last_profit) / last_profit) * 100

        # EPS预测（假设总股本10亿股）
        total_shares = 10.0
        forecast_eps = forecast_profit / total_shares

        return {
            "historical_profits": historical_profits,
            "forecast_profit": round(forecast_profit, 2),
            "profit_growth": round(profit_growth, 2),
            "avg_growth_rate": round(avg_growth_rate, 2),
            "forecast_eps": round(forecast_eps, 2),
            "forecast_period": forecast_period,
            "confidence": 0.75,
            "description": f"预计利润增长{profit_growth:.1f}%，EPS达到{forecast_eps:.2f}元"
        }

    # ========== 趋势预测 ==========

    def _forecast_trend(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        趋势预测

        Args:
            price_forecast: 价格预测
            profit_forecast: 利润预测
            current_price: 当前股价

        Returns:
            趋势预测
        """
        price_upside = price_forecast["upside"]
        profit_growth = profit_forecast["profit_growth"]

        # 价格与利润的匹配度
        # 理论上，股价涨幅应该与利润增长匹配
        price_profit_match = abs(price_upside - profit_growth) < 5

        # 趋势强度
        if price_upside > 20 and profit_growth > 15:
            trend_strength = "强劲"
            trend_quality = "量价齐升"
        elif price_upside > 10 and profit_growth > 10:
            trend_strength = "较强"
            trend_quality = "稳步上升"
        elif price_upside > 0 and profit_growth > 0:
            trend_strength = "温和"
            trend_quality = "缓慢增长"
        else:
            trend_strength = "疲弱"
            trend_quality = "增长乏力"

        # 趋势可持续性
        if price_profit_match and profit_growth > 10:
            sustainability = "高"
        elif price_profit_match:
            sustainability = "中"
        else:
            sustainability = "低"

        return {
            "trend_strength": trend_strength,
            "trend_quality": trend_quality,
            "price_profit_match": price_profit_match,
            "sustainability": sustainability,
            "key_drivers": self._identify_trend_drivers(price_forecast, profit_forecast)
        }

    def _identify_trend_drivers(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any]
    ) -> List[str]:
        """识别趋势驱动因素"""
        drivers = []

        if profit_forecast["avg_growth_rate"] > 15:
            drivers.append("利润高速增长")

        if price_forecast["confidence"] > 0.7:
            drivers.append("预测置信度高")

        if profit_forecast["profit_growth"] > 10:
            drivers.append("基本面支撑强")

        if not drivers:
            drivers.append("无明显驱动因素")

        return drivers

    # ========== 情景分析 ==========

    def _analyze_scenarios(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        情景分析

        Returns:
            乐观/中性/悲观三种情景
        """
        base_price = price_forecast["forecast_price"]
        base_profit = profit_forecast["forecast_profit"]

        # 乐观情景（+20%）
        optimistic_price = base_price * 1.20
        optimistic_upside = ((optimistic_price - current_price) / current_price) * 100

        # 中性情景（基准）
        neutral_upside = ((base_price - current_price) / current_price) * 100

        # 悲观情景（-20%）
        pessimistic_price = base_price * 0.80
        pessimistic_upside = ((pessimistic_price - current_price) / current_price) * 100

        # 情景概率（简化假设）
        probabilities = {
            "optimistic": 0.30,
            "neutral": 0.50,
            "pessimistic": 0.20
        }

        return {
            "optimistic": {
                "price": round(optimistic_price, 2),
                "upside": round(optimistic_upside, 2),
                "probability": probabilities["optimistic"],
                "description": "市场环境向好，业绩超预期"
            },
            "neutral": {
                "price": round(base_price, 2),
                "upside": round(neutral_upside, 2),
                "probability": probabilities["neutral"],
                "description": "市场环境稳定，业绩符合预期"
            },
            "pessimistic": {
                "price": round(pessimistic_price, 2),
                "upside": round(pessimistic_upside, 2),
                "probability": probabilities["pessimistic"],
                "description": "市场环境恶化，业绩低于预期"
            },
            "expected_value": round(
                optimistic_price * probabilities["optimistic"] +
                base_price * probabilities["neutral"] +
                pessimistic_price * probabilities["pessimistic"],
                2
            )
        }

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 价格预测风险
        if price_forecast["confidence"] < 0.7:
            risks.append("价格预测置信度较低，存在较大不确定性")

        # 利润增长风险
        if profit_forecast["avg_growth_rate"] < 10:
            risks.append("利润增长率偏低，增长动力不足")

        # 价格与利润不匹配风险
        if abs(price_forecast["upside"] - profit_forecast["profit_growth"]) > 10:
            risks.append("股价涨幅与利润增长不匹配，存在估值风险")

        # 时间风险
        period_months = int(price_forecast["forecast_period"].replace("m", ""))
        if period_months > 6:
            risks.append(f"预测周期较长（{period_months}个月），不确定性增加")

        if not risks:
            risks.append("未发现明显预测风险")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any],
        trend_forecast: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 基于价格预测的建议
        upside = price_forecast["upside"]
        if upside > 20:
            recommendations.append(f"股价上涨空间{upside:.1f}%，建议积极关注")
        elif upside > 10:
            recommendations.append(f"股价具有{upside:.1f}%上涨空间，可以持有")

        # 基于利润预测的建议
        profit_growth = profit_forecast["profit_growth"]
        if profit_growth > 15:
            recommendations.append(f"利润预计增长{profit_growth:.1f}%，基本面支撑强")

        # 基于趋势的建议
        if trend_forecast["sustainability"] == "高":
            recommendations.append("趋势可持续性高，适合中长期持有")

        if not recommendations:
            recommendations.append("建议谨慎观望，等待更好时机")

        return recommendations

    # ========== 辅助方法 ==========

    def _generate_conclusion(
        self,
        price_forecast: Dict[str, Any],
        profit_forecast: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        return (
            f"预计{price_forecast['forecast_period']}目标价{price_forecast['forecast_price']}元"
            f"（上涨{price_forecast['upside']:.1f}%），"
            f"利润增长{profit_forecast['profit_growth']:.1f}%，"
            f"趋势{price_forecast['trend']}"
        )


# 便捷函数
async def analyze_price_forecast(
    stock_code: str,
    current_price: float,
    forecast_period: str = "12m"
) -> AnalysisResult:
    """
    价格预测分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        forecast_period: 预测周期

    Returns:
        分析结果
    """
    ai = PriceForecastAI()
    return await ai.analyze(
        stock_code,
        current_price=current_price,
        forecast_period=forecast_period
    )

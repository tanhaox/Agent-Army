"""
Agent Army - 风险控制AI Agent
负责投资风险评估、风险限额管理和风险控制建议

基于BaseBusinessAgent架构，实现全面的风险控制功能
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult, StockInfo
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class RiskAssessment(BaseModel):
    """风险评估结果"""
    overall_risk: str = Field(description="整体风险等级: 低/中/高")
    risk_score: float = Field(ge=0.0, le=100.0, description="风险评分 0-100")
    risk_level: int = Field(ge=1, le=5, description="风险等级 1-5")


class RiskIndicators(BaseModel):
    """风险指标"""
    var_95: Optional[float] = Field(default=None, description="95%置信度VaR(风险价值)")
    max_drawdown: Optional[float] = Field(default=None, description="最大回撤")
    volatility: Optional[float] = Field(default=None, description="波动率")
    beta: Optional[float] = Field(default=None, description="Beta系数")
    sharpe_ratio: Optional[float] = Field(default=None, description="夏普比率")


class RiskLimits(BaseModel):
    """风险限额"""
    single_stock_max: float = Field(description="单股最大仓位比例")
    single_industry_max: float = Field(description="单行业最大仓位比例")
    total_max_position: float = Field(description="总最大仓位比例")
    cash_min_ratio: float = Field(description="最小现金比例")


class RiskControlResult(BaseModel):
    """风险控制分析结果"""
    stock_code: str
    timestamp: str
    risk_assessment: RiskAssessment
    risk_indicators: RiskIndicators
    risk_limits: RiskLimits
    stop_loss_strategy: Dict[str, Any] = Field(default_factory=dict, description="止损策略")
    risk_control_plan: List[str] = Field(default_factory=list, description="风险控制计划")
    suggestions: List[str] = Field(default_factory=list, description="风险控制建议")


class RiskControlAI(BusinessAgent):
    """
    风险控制AI Agent

    职责:
    1. 评估投资风险(市场风险、个股风险、流动性风险、集中度风险)
    2. 计算风险指标(VaR、最大回撤、波动率、Beta、夏普比率)
    3. 设置风险限额和风控策略
    4. 生成风险控制建议

    所属军团: 战略军团
    分析类型: 风险控制
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        tools: Optional[List[AgentTool]] = None
    ):
        """
        初始化风险控制AI Agent

        Args:
            config: 配置信息
            capabilities: 能力列表
            tools: 工具列表
        """
        # 定义能力
        default_capabilities = [
            AgentCapability(
                name="risk_assessment",
                description="风险评估: 评估市场、个股、流动性和集中度风险",
                enabled=True
            ),
            AgentCapability(
                name="risk_indicators",
                description="风险指标计算: VaR、最大回撤、波动率、Beta、夏普比率",
                enabled=True
            ),
            AgentCapability(
                name="risk_limits",
                description="风险限额管理: 设置单股、行业、总仓位限额",
                enabled=True
            ),
            AgentCapability(
                name="risk_control_advice",
                description="风险控制建议: 生成风控建议和策略",
                enabled=True
            )
        ]

        # 合并能力
        if capabilities:
            default_capabilities.extend(capabilities)

        # 初始化基类
        super().__init__(
            name="风控AI",
            role="风险控制专家",
            corps="战略军团",
            analysis_type="risk_control",
            capabilities=default_capabilities,
            tools=tools,
            config=config
        )

        # 风险参数配置
        self.risk_free_rate = config.get("risk_free_rate", 0.03) if config else 0.03  # 无风险利率3%
        self.confidence_level = config.get("confidence_level", 0.95) if config else 0.95  # 置信度95%

        self.logger.info(
            "风险控制AI初始化完成",
            risk_free_rate=self.risk_free_rate,
            confidence_level=self.confidence_level
        )

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行风险控制分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - price_data: 价格数据(用于计算指标)
                - market_data: 市场数据(用于计算Beta)
                - portfolio_data: 组合数据(用于计算集中度风险)
                - current_position: 当前仓位

        Returns:
            风险控制分析结果
        """
        self.logger.info(
            "开始风险控制分析",
            stock_code=stock_code,
            kwargs=list(kwargs.keys())
        )

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            error_msg = f"无效的股票代码: {stock_code}"
            self.logger.error(error_msg)
            return AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=error_msg,
                confidence=0.0,
                risks=["股票代码格式错误"],
                recommendations=["请检查股票代码是否为6位数字"]
            )

        # 获取数据
        price_data = kwargs.get("price_data", [])
        market_data = kwargs.get("market_data", [])
        portfolio_data = kwargs.get("portfolio_data", {})
        current_position = kwargs.get("current_position", 0.0)

        try:
            # 计算风险控制结果
            risk_result = await self._calculate_risk_control(
                stock_code=stock_code,
                price_data=price_data,
                market_data=market_data,
                portfolio_data=portfolio_data,
                current_position=current_position
            )

            # 构建分析结论
            conclusion = self._build_conclusion(risk_result)

            # 构建风险提示
            risks = self._build_risk_warnings(risk_result)

            # 构建建议
            recommendations = risk_result.suggestions

            # 构建详细数据
            details = risk_result.model_dump()

            self.logger.info(
                "风险控制分析完成",
                stock_code=stock_code,
                overall_risk=risk_result.risk_assessment.overall_risk,
                risk_score=risk_result.risk_assessment.risk_score
            )

            return AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=conclusion,
                confidence=self._calculate_confidence(risk_result),
                details=details,
                risks=risks,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(
                "风险控制分析失败",
                stock_code=stock_code,
                error=str(e),
                exc_info=True
            )
            return AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=f"风险控制分析失败: {str(e)}",
                confidence=0.0,
                risks=["分析过程出现异常"],
                recommendations=["请检查输入数据是否完整", "请联系技术支持"]
            )

    async def _calculate_risk_control(
        self,
        stock_code: str,
        price_data: List[float],
        market_data: List[float],
        portfolio_data: Dict[str, Any],
        current_position: float
    ) -> RiskControlResult:
        """
        计算风险控制指标

        Args:
            stock_code: 股票代码
            price_data: 价格数据
            market_data: 市场数据
            portfolio_data: 组合数据
            current_position: 当前仓位

        Returns:
            风险控制结果
        """
        self.logger.info(
            "计算风险控制指标",
            stock_code=stock_code,
            has_price_data=len(price_data) > 0,
            has_market_data=len(market_data) > 0
        )

        # 1. 风险评估
        risk_assessment = await self._assess_risk(
            price_data=price_data,
            portfolio_data=portfolio_data
        )

        # 2. 风险指标计算
        risk_indicators = await self._calculate_indicators(
            price_data=price_data,
            market_data=market_data
        )

        # 3. 风险限额设置
        risk_limits = await self._set_risk_limits(
            risk_assessment=risk_assessment,
            current_position=current_position
        )

        # 4. 生成风险控制建议
        suggestions = await self._generate_suggestions(
            risk_assessment=risk_assessment,
            risk_indicators=risk_indicators,
            risk_limits=risk_limits
        )

        # 5. 止损策略（简化版本）
        # 从price_data获取当前价格（如果有）
        current_price = price_data[-1] if price_data else 50.0

        stop_loss_strategy = {
            "stop_loss_price": round(current_price * 0.92, 2),  # 止损价：当前价*0.92
            "take_profit_price": round(current_price * 1.15, 2),  # 止盈价：当前价*1.15
            "stop_loss_ratio": 0.08,  # 止损比例8%
            "take_profit_ratio": 0.15  # 止盈比例15%
        }

        # 6. 风险控制计划
        risk_control_plan = [
            "严格执行止损策略",
            "控制仓位在限额内",
            "关注市场风险变化"
        ]

        return RiskControlResult(
            stock_code=stock_code,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_assessment=risk_assessment,
            risk_indicators=risk_indicators,
            risk_limits=risk_limits,
            stop_loss_strategy=stop_loss_strategy,
            risk_control_plan=risk_control_plan,
            suggestions=suggestions
        )

    async def _assess_risk(
        self,
        price_data: List[float],
        portfolio_data: Dict[str, Any]
    ) -> RiskAssessment:
        """
        综合风险评估

        Args:
            price_data: 价格数据
            portfolio_data: 组合数据

        Returns:
            风险评估结果
        """
        self.logger.info("开始风险评估")

        risk_factors = []

        # 1. 市场风险评估(基于价格波动)
        if price_data and len(price_data) > 1:
            returns = self._calculate_returns(price_data)
            volatility = np.std(returns) if returns else 0.0

            if volatility > 0.05:  # 日波动率>5%
                risk_factors.append(("市场风险", 30))
            elif volatility > 0.03:  # 日波动率>3%
                risk_factors.append(("市场风险", 20))
            else:
                risk_factors.append(("市场风险", 10))
        else:
            risk_factors.append(("市场风险", 15))  # 无数据时中等风险

        # 2. 个股风险评估(基于集中度)
        if portfolio_data:
            concentration = portfolio_data.get("concentration", 0.5)
            if concentration > 0.3:  # 单股占比>30%
                risk_factors.append(("个股风险", 30))
            elif concentration > 0.2:
                risk_factors.append(("个股风险", 20))
            else:
                risk_factors.append(("个股风险", 10))
        else:
            risk_factors.append(("个股风险", 15))

        # 3. 流动性风险评估(基于成交量)
        if portfolio_data:
            liquidity_ratio = portfolio_data.get("liquidity_ratio", 0.8)
            if liquidity_ratio < 0.3:  # 流动性差
                risk_factors.append(("流动性风险", 25))
            elif liquidity_ratio < 0.5:
                risk_factors.append(("流动性风险", 15))
            else:
                risk_factors.append(("流动性风险", 5))
        else:
            risk_factors.append(("流动性风险", 10))

        # 4. 集中度风险评估(基于行业分布)
        if portfolio_data:
            industry_concentration = portfolio_data.get("industry_concentration", 0.6)
            if industry_concentration > 0.7:  # 单行业占比>70%
                risk_factors.append(("集中度风险", 25))
            elif industry_concentration > 0.5:
                risk_factors.append(("集中度风险", 15))
            else:
                risk_factors.append(("集中度风险", 5))
        else:
            risk_factors.append(("集中度风险", 10))

        # 计算总风险评分
        total_score = sum(score for _, score in risk_factors)

        # 归一化到0-100
        normalized_score = min(total_score * 1.5, 100.0)

        # 确定风险等级
        if normalized_score >= 70:
            overall_risk = "高"
            risk_level = 5
        elif normalized_score >= 50:
            overall_risk = "中高"
            risk_level = 4
        elif normalized_score >= 30:
            overall_risk = "中"
            risk_level = 3
        elif normalized_score >= 15:
            overall_risk = "中低"
            risk_level = 2
        else:
            overall_risk = "低"
            risk_level = 1

        self.logger.info(
            "风险评估完成",
            total_score=total_score,
            normalized_score=normalized_score,
            overall_risk=overall_risk
        )

        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=normalized_score,
            risk_level=risk_level
        )

    async def _calculate_indicators(
        self,
        price_data: List[float],
        market_data: List[float]
    ) -> RiskIndicators:
        """
        计算风险指标

        Args:
            price_data: 价格数据
            market_data: 市场数据

        Returns:
            风险指标
        """
        self.logger.info("计算风险指标")

        indicators = RiskIndicators()

        if not price_data or len(price_data) < 2:
            self.logger.warning("价格数据不足，无法计算风险指标")
            return indicators

        # 转换为numpy数组
        prices = np.array(price_data)

        # 1. 计算收益率
        returns = self._calculate_returns(price_data)

        if returns:
            returns_array = np.array(returns)

            # 2. 波动率(年化)
            daily_volatility = np.std(returns_array)
            annual_volatility = daily_volatility * np.sqrt(252)  # 年化
            indicators.volatility = round(annual_volatility, 4)

            # 3. VaR(风险价值) - 95%置信度
            var_95_daily = np.percentile(returns_array, 5)  # 5%分位数
            var_95_annual = var_95_daily * np.sqrt(252)  # 年化
            indicators.var_95 = round(var_95_annual, 4)

            # 4. 夏普比率
            if daily_volatility > 0:
                excess_return = np.mean(returns_array) * 252 - self.risk_free_rate
                sharpe = excess_return / annual_volatility
                indicators.sharpe_ratio = round(sharpe, 4)

            # 5. Beta系数(需要市场数据)
            if market_data and len(market_data) >= len(price_data):
                market_returns = self._calculate_returns(market_data[:len(price_data)])
                if market_returns and len(market_returns) == len(returns):
                    covariance = np.cov(returns_array, np.array(market_returns))[0][1]
                    market_variance = np.var(np.array(market_returns))
                    if market_variance > 0:
                        beta = covariance / market_variance
                        indicators.beta = round(beta, 4)

        # 6. 最大回撤
        if len(prices) > 1:
            max_drawdown = self._calculate_max_drawdown(prices)
            indicators.max_drawdown = round(max_drawdown, 4)

        self.logger.info(
            "风险指标计算完成",
            volatility=indicators.volatility,
            var_95=indicators.var_95,
            max_drawdown=indicators.max_drawdown
        )

        return indicators

    async def _set_risk_limits(
        self,
        risk_assessment: RiskAssessment,
        current_position: float
    ) -> RiskLimits:
        """
        设置风险限额

        Args:
            risk_assessment: 风险评估结果
            current_position: 当前仓位

        Returns:
            风险限额
        """
        self.logger.info(
            "设置风险限额",
            risk_level=risk_assessment.risk_level
        )

        # 根据风险等级调整限额
        risk_level = risk_assessment.risk_level

        if risk_level == 5:  # 高风险
            single_stock_max = 0.05  # 5%
            single_industry_max = 0.15  # 15%
            total_max_position = 0.40  # 40%
            cash_min_ratio = 0.30  # 30%
        elif risk_level == 4:  # 中高风险
            single_stock_max = 0.08  # 8%
            single_industry_max = 0.20  # 20%
            total_max_position = 0.50  # 50%
            cash_min_ratio = 0.25  # 25%
        elif risk_level == 3:  # 中风险
            single_stock_max = 0.10  # 10%
            single_industry_max = 0.25  # 25%
            total_max_position = 0.60  # 60%
            cash_min_ratio = 0.20  # 20%
        elif risk_level == 2:  # 中低风险
            single_stock_max = 0.12  # 12%
            single_industry_max = 0.30  # 30%
            total_max_position = 0.70  # 70%
            cash_min_ratio = 0.15  # 15%
        else:  # 低风险
            single_stock_max = 0.15  # 15%
            single_industry_max = 0.35  # 35%
            total_max_position = 0.80  # 80%
            cash_min_ratio = 0.10  # 10%

        self.logger.info(
            "风险限额设置完成",
            single_stock_max=single_stock_max,
            single_industry_max=single_industry_max,
            total_max_position=total_max_position,
            cash_min_ratio=cash_min_ratio
        )

        return RiskLimits(
            single_stock_max=single_stock_max,
            single_industry_max=single_industry_max,
            total_max_position=total_max_position,
            cash_min_ratio=cash_min_ratio
        )

    async def _generate_suggestions(
        self,
        risk_assessment: RiskAssessment,
        risk_indicators: RiskIndicators,
        risk_limits: RiskLimits
    ) -> List[str]:
        """
        生成风险控制建议

        Args:
            risk_assessment: 风险评估
            risk_indicators: 风险指标
            risk_limits: 风险限额

        Returns:
            建议列表
        """
        self.logger.info("生成风险控制建议")

        suggestions = []

        # 基于风险等级的建议
        if risk_assessment.risk_level >= 4:
            suggestions.append("当前风险等级较高，建议降低仓位，增加现金比例")
            suggestions.append("严格执行止损策略，控制单只股票仓位")

        # 基于波动率的建议
        if risk_indicators.volatility and risk_indicators.volatility > 0.4:
            suggestions.append("股票波动率较高，建议分批建仓，降低买入成本")
            suggestions.append("设置较宽的止损幅度，避免被正常波动震出")

        # 基于最大回撤的建议
        if risk_indicators.max_drawdown and risk_indicators.max_drawdown > 0.2:
            suggestions.append("历史最大回撤较大，建议控制仓位并设置严格止损")

        # 基于VaR的建议
        if risk_indicators.var_95 and risk_indicators.var_95 < -0.3:
            suggestions.append("潜在下行风险较大，建议做好风险对冲或降低仓位")

        # 基于Beta的建议
        if risk_indicators.beta and risk_indicators.beta > 1.5:
            suggestions.append(f"Beta系数为{risk_indicators.beta}，对市场波动敏感，注意系统性风险")
        elif risk_indicators.beta and risk_indicators.beta < 0.5:
            suggestions.append(f"Beta系数为{risk_indicators.beta}，具有防御特性，适合稳健配置")

        # 基于夏普比率的建议
        if risk_indicators.sharpe_ratio and risk_indicators.sharpe_ratio < 0.5:
            suggestions.append("夏普比率较低，风险调整后收益不理想，建议谨慎投资")
        elif risk_indicators.sharpe_ratio and risk_indicators.sharpe_ratio > 1.5:
            suggestions.append("夏普比率较高，风险调整后收益良好，可适当关注")

        # 基于风险限额的建议
        suggestions.append(f"单股最大仓位建议: {risk_limits.single_stock_max*100:.1f}%")
        suggestions.append(f"单行业最大仓位建议: {risk_limits.single_industry_max*100:.1f}%")
        suggestions.append(f"总仓位上限建议: {risk_limits.total_max_position*100:.1f}%")
        suggestions.append(f"最小现金比例: {risk_limits.cash_min_ratio*100:.1f}%")

        # 通用风控建议
        suggestions.append("严格执行仓位管理，避免过度集中")
        suggestions.append("设置止损位，控制单笔损失")
        suggestions.append("定期检查风险指标，及时调整策略")

        self.logger.info(
            "风险控制建议生成完成",
            suggestion_count=len(suggestions)
        )

        return suggestions

    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """
        计算收益率

        Args:
            prices: 价格列表

        Returns:
            收益率列表
        """
        if len(prices) < 2:
            return []

        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)

        return returns

    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """
        计算最大回撤

        Args:
            prices: 价格数组

        Returns:
            最大回撤
        """
        if len(prices) < 2:
            return 0.0

        # 计算累计最高价
        cummax = np.maximum.accumulate(prices)

        # 计算回撤
        drawdown = (prices - cummax) / cummax

        # 最大回撤
        max_drawdown = np.min(drawdown)

        return abs(max_drawdown)

    def _build_conclusion(self, risk_result: RiskControlResult) -> str:
        """构建分析结论"""
        return (f"风险等级: {risk_result.risk_assessment.overall_risk} "
                f"(评分: {risk_result.risk_assessment.risk_score:.1f}/100), "
                f"建议单股最大仓位: {risk_result.risk_limits.single_stock_max*100:.1f}%")

    def _build_risk_warnings(self, risk_result: RiskControlResult) -> List[str]:
        """构建风险提示"""
        warnings = []

        if risk_result.risk_assessment.risk_level >= 4:
            warnings.append("当前风险等级较高，需要特别谨慎")

        if risk_result.risk_indicators.max_drawdown and risk_result.risk_indicators.max_drawdown > 0.2:
            warnings.append(f"历史最大回撤达到{risk_result.risk_indicators.max_drawdown*100:.1f}%")

        if risk_result.risk_indicators.volatility and risk_result.risk_indicators.volatility > 0.4:
            warnings.append(f"年化波动率高达{risk_result.risk_indicators.volatility*100:.1f}%")

        return warnings

    def _calculate_confidence(self, risk_result: RiskControlResult) -> float:
        """计算置信度"""
        confidence = 0.8  # 基础置信度

        # 如果有关键指标缺失，降低置信度
        if risk_result.risk_indicators.volatility is None:
            confidence -= 0.2
        if risk_result.risk_indicators.var_95 is None:
            confidence -= 0.1
        if risk_result.risk_indicators.max_drawdown is None:
            confidence -= 0.1

        return max(confidence, 0.3)  # 最低0.3


# 便捷函数
async def analyze_risk_control(
    stock_code: str,
    current_price: float,
    position_cost: Optional[float] = None,
    intended_buy_price: Optional[float] = None
) -> AnalysisResult:
    """
    风控分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        position_cost: 持仓成本
        intended_buy_price: 计划买入价

    Returns:
        分析结果
    """
    ai = RiskControlAI()
    return await ai.analyze(
        stock_code,
        current_price=current_price,
        position_cost=position_cost,
        intended_buy_price=intended_buy_price
    )

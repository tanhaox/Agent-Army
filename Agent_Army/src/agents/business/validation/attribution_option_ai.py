"""
归因期权AI - Attribution and Option AI

验证部成员 (2/2)

职责：
1. 归因分析 - 分析收益来源和风险因子
2. 期权分析 - 期权定价和策略分析

合并来源：
- 归因分析AI
- 期权分析AI

使用工具：
- FinancialTool（市场数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import math

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class AttributionOptionAI(BusinessAgent):
    """
    归因期权AI - 验证部成员 (2/2)

    核心能力:
    1. 归因分析 - 收益归因和风险因子分析
    2. 期权分析 - 期权定价和策略分析

    使用工具:
    - FinancialTool (市场数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="归因期权AI",
            role="分析收益归因，提供期权定价",
            corps="validation",
            analysis_type="attribution_option",
            capabilities=[
                AgentCapability(
                    name="return_attribution",
                    description="收益归因分析",
                    input_type="stock_code",
                    output_type="attribution_factors"
                ),
                AgentCapability(
                    name="option_analysis",
                    description="期权分析",
                    input_type="stock_code",
                    output_type="option_pricing"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="市场数据工具",
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

        self.logger.info("归因期权AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行归因期权分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前股价（必需）
                - benchmark_return: 基准收益（可选）
                - option_params: 期权参数（可选）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        current_price = kwargs.get("current_price")
        if not current_price:
            raise ValueError("缺少current_price参数")

        benchmark_return = kwargs.get("benchmark_return", 0.0)
        option_params = kwargs.get("option_params", {})

        self.logger.info(
            f"开始归因期权分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "has_option_params": bool(option_params)
            }
        )

        # ========== 1. 收益归因分析 ==========
        attribution_factors = await self._analyze_return_attribution(
            stock_code,
            current_price,
            benchmark_return
        )

        # ========== 2. 风险因子分析 ==========
        risk_factors = await self._analyze_risk_factors(
            stock_code,
            current_price
        )

        # ========== 3. 期权定价分析 ==========
        option_analysis = await self._analyze_options(
            stock_code,
            current_price,
            option_params
        )

        # ========== 4. 生成投资建议 ==========
        recommendations = self._generate_recommendations(
            attribution_factors,
            risk_factors,
            option_analysis
        )

        # ========== 5. 风险识别 ==========
        risks = self._identify_risks(
            attribution_factors,
            risk_factors,
            option_analysis
        )

        # ========== 6. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,
            "current_price": current_price,

            # 归因分析
            "return_attribution": attribution_factors,

            # 风险因子
            "risk_factors": risk_factors,

            # 期权分析
            "option_analysis": option_analysis,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(attribution_factors, option_analysis),
            confidence=attribution_factors.get("confidence", 0.75),
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"归因期权分析完成",
            extra={
                "stock_code": stock_code,
                "attribution_type": attribution_factors.get("primary_factor", "unknown"),
                "option_iv": option_analysis.get("implied_volatility", 0)
            }
        )

        return result

    # ========== 核心归因方法 ==========

    async def _analyze_return_attribution(
        self,
        stock_code: str,
        current_price: float,
        benchmark_return: float
    ) -> Dict[str, Any]:
        """
        分析收益归因

        Returns:
            收益归因因子
        """
        # TODO: 接入真实市场数据
        # 当前使用模拟数据

        # 1. 行业因子
        industry_factor = await self._calculate_industry_factor(stock_code)

        # 2. 风格因子
        style_factor = await self._calculate_style_factor(stock_code)

        # 3. 特质因子
        specific_factor = await self._calculate_specific_factor(stock_code)

        # 4. 宏观因子
        macro_factor = await self._calculate_macro_factor(stock_code)

        # 5. 识别主要归因
        primary_factor = self._identify_primary_factor(
            industry_factor,
            style_factor,
            specific_factor,
            macro_factor
        )

        return {
            "primary_factor": primary_factor,
            "industry_factor": industry_factor,
            "style_factor": style_factor,
            "specific_factor": specific_factor,
            "macro_factor": macro_factor,
            "benchmark_return": benchmark_return,
            "confidence": 0.75
        }

    async def _analyze_risk_factors(
        self,
        stock_code: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        分析风险因子

        Returns:
            风险因子分析
        """
        # TODO: 接入真实数据

        # 1. Beta风险
        beta = self._calculate_beta(stock_code)

        # 2. 波动率风险
        volatility = self._calculate_volatility(stock_code)

        # 3. 流动性风险
        liquidity = self._calculate_liquidity(stock_code)

        # 4. 价值风险
        value_risk = self._calculate_value_risk(stock_code)

        # 5. 动量风险
        momentum_risk = self._calculate_momentum_risk(stock_code)

        # 综合风险评分
        risk_score = self._calculate_risk_score(
            beta, volatility, liquidity, value_risk, momentum_risk
        )

        return {
            "beta": beta,
            "volatility": volatility,
            "liquidity": liquidity,
            "value_risk": value_risk,
            "momentum_risk": momentum_risk,
            "risk_score": risk_score,
            "risk_level": self._assess_risk_level(risk_score)
        }

    async def _analyze_options(
        self,
        stock_code: str,
        current_price: float,
        option_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        期权分析

        Returns:
            期权定价分析
        """
        # TODO: 接入真实期权数据

        # 默认期权参数
        strike_price = option_params.get("strike_price", current_price * 1.1)
        time_to_expiry = option_params.get("time_to_expiry", 0.25)  # 3个月
        risk_free_rate = option_params.get("risk_free_rate", 0.03)
        volatility = option_params.get("volatility", 0.30)

        # 1. Black-Scholes定价
        call_price = self._black_scholes_call(
            current_price, strike_price, time_to_expiry, risk_free_rate, volatility
        )

        put_price = self._black_scholes_put(
            current_price, strike_price, time_to_expiry, risk_free_rate, volatility
        )

        # 2. 希腊字母计算
        greeks = self._calculate_greeks(
            current_price, strike_price, time_to_expiry, risk_free_rate, volatility
        )

        # 3. 隐含波动率
        implied_volatility = self._calculate_implied_volatility(
            current_price, strike_price, time_to_expiry, call_price
        )

        # 4. 期权策略建议
        strategy_suggestions = self._generate_option_strategies(
            current_price, strike_price, greeks, implied_volatility
        )

        return {
            "option_price": {
                "call": call_price,
                "put": put_price
            },
            "call_price": call_price,
            "put_price": put_price,
            "strike_price": strike_price,
            "time_to_expiry": time_to_expiry,
            "implied_volatility": implied_volatility,
            "greeks": greeks,
            "strategy_suggestions": strategy_suggestions
        }

    # ========== 归因因子计算 ==========

    async def _calculate_industry_factor(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """计算行业因子"""
        # TODO: 接入真实行业数据
        industry_return = 0.08  # 行业收益率
        industry_contribution = 0.60  # 行业贡献度

        return {
            "return": industry_return,
            "contribution": industry_contribution,
            "description": "行业整体表现"
        }

    async def _calculate_style_factor(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """计算风格因子"""
        # TODO: 接入真实风格数据
        size_factor = 0.02  # 规模因子
        value_factor = 0.03  # 价值因子
        growth_factor = 0.04  # 成长因子
        quality_factor = 0.01  # 质量因子

        total_style_return = size_factor + value_factor + growth_factor + quality_factor

        return {
            "size_factor": size_factor,
            "value_factor": value_factor,
            "growth_factor": growth_factor,
            "quality_factor": quality_factor,
            "total_return": total_style_return,
            "description": "风格因子贡献"
        }

    async def _calculate_specific_factor(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """计算特质因子"""
        # TODO: 接入真实公司数据
        company_return = 0.05  # 公司特质收益
        specific_contribution = 0.25  # 特质贡献度

        return {
            "return": company_return,
            "contribution": specific_contribution,
            "description": "公司特有因素"
        }

    async def _calculate_macro_factor(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """计算宏观因子"""
        # TODO: 接入真实宏观数据
        gdp_factor = 0.01  # GDP因子
        inflation_factor = -0.005  # 通胀因子
        interest_rate_factor = -0.01  # 利率因子

        total_macro_return = gdp_factor + inflation_factor + interest_rate_factor

        return {
            "gdp_factor": gdp_factor,
            "inflation_factor": inflation_factor,
            "interest_rate_factor": interest_rate_factor,
            "total_return": total_macro_return,
            "description": "宏观经济因素"
        }

    def _identify_primary_factor(
        self,
        industry_factor: Dict[str, Any],
        style_factor: Dict[str, Any],
        specific_factor: Dict[str, Any],
        macro_factor: Dict[str, Any]
    ) -> str:
        """识别主要归因因子"""
        # 比较各因子贡献度
        factors = {
            "行业因子": abs(industry_factor["return"]),
            "风格因子": abs(style_factor["total_return"]),
            "特质因子": abs(specific_factor["return"]),
            "宏观因子": abs(macro_factor["total_return"])
        }

        primary = max(factors, key=factors.get)

        return primary

    # ========== 风险因子计算 ==========

    def _calculate_beta(self, stock_code: str) -> float:
        """计算Beta"""
        # TODO: 接入真实数据
        return 1.2

    def _calculate_volatility(self, stock_code: str) -> float:
        """计算波动率"""
        # TODO: 接入真实数据
        return 0.30

    def _calculate_liquidity(self, stock_code: str) -> float:
        """计算流动性"""
        # TODO: 接入真实数据
        return 0.80

    def _calculate_value_risk(self, stock_code: str) -> float:
        """计算价值风险"""
        # TODO: 接入真实数据
        return 0.15

    def _calculate_momentum_risk(self, stock_code: str) -> float:
        """计算动量风险"""
        # TODO: 接入真实数据
        return 0.20

    def _calculate_risk_score(
        self,
        beta: float,
        volatility: float,
        liquidity: float,
        value_risk: float,
        momentum_risk: float
    ) -> float:
        """计算综合风险评分"""
        # 标准化各因子
        beta_score = min(beta / 2.0, 1.0)
        volatility_score = min(volatility / 0.5, 1.0)
        liquidity_score = 1 - liquidity  # 流动性越高，风险越低
        value_score = min(value_risk / 0.3, 1.0)
        momentum_score = min(momentum_risk / 0.4, 1.0)

        # 加权平均
        risk_score = (
            beta_score * 0.3 +
            volatility_score * 0.3 +
            liquidity_score * 0.15 +
            value_score * 0.125 +
            momentum_score * 0.125
        )

        return round(risk_score, 3)

    def _assess_risk_level(self, risk_score: float) -> str:
        """评估风险等级"""
        if risk_score >= 0.7:
            return "高风险"
        elif risk_score >= 0.5:
            return "中等风险"
        else:
            return "低风险"

    # ========== 期权定价方法 ==========

    def _black_scholes_call(
        self,
        S: float,  # 标的资产价格
        K: float,  # 行权价
        T: float,  # 到期时间（年）
        r: float,  # 无风险利率
        sigma: float  # 波动率
    ) -> float:
        """Black-Scholes看涨期权定价"""
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        call_price = S * self._cdf(d1) - K * math.exp(-r * T) * self._cdf(d2)

        return round(call_price, 2)

    def _black_scholes_put(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """Black-Scholes看跌期权定价"""
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        put_price = K * math.exp(-r * T) * self._cdf(-d2) - S * self._cdf(-d1)

        return round(put_price, 2)

    def _cdf(self, x: float) -> float:
        """标准正态分布累积分布函数"""
        # 近似计算
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)

        return 0.5 * (1.0 + sign * y)

    def _calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> Dict[str, float]:
        """计算希腊字母"""
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Delta
        delta = self._cdf(d1)

        # Gamma
        phi_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
        gamma = phi_d1 / (S * sigma * math.sqrt(T))

        # Vega
        vega = S * phi_d1 * math.sqrt(T) / 100

        # Theta
        theta = (
            -S * phi_d1 * sigma / (2 * math.sqrt(T)) -
            r * K * math.exp(-r * T) * self._cdf(d2)
        ) / 365

        # Rho
        rho = K * T * math.exp(-r * T) * self._cdf(d2) / 100

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "vega": round(vega, 4),
            "theta": round(theta, 4),
            "rho": round(rho, 4)
        }

    def _calculate_implied_volatility(
        self,
        S: float,
        K: float,
        T: float,
        market_price: float,
        initial_guess: float = 0.3,
        tolerance: float = 1e-6,
        max_iterations: int = 100
    ) -> float:
        """计算隐含波动率（牛顿迭代法）"""
        sigma = initial_guess

        for _ in range(max_iterations):
            price = self._black_scholes_call(S, K, T, 0.03, sigma)

            if abs(price - market_price) < tolerance:
                break

            # 计算vega（导数）
            d1 = (math.log(S / K) + (0.03 + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            phi_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
            vega = S * phi_d1 * math.sqrt(T)

            # 牛顿迭代
            sigma = sigma - (price - market_price) / vega

        return round(sigma, 4)

    def _generate_option_strategies(
        self,
        current_price: float,
        strike_price: float,
        greeks: Dict[str, float],
        implied_volatility: float
    ) -> List[str]:
        """生成期权策略建议"""
        strategies = []

        # 基于Delta的策略
        delta = greeks["delta"]
        if delta > 0.7:
            strategies.append("Delta较高，期权对标的资产变动敏感，适合趋势交易")
        elif delta < 0.3:
            strategies.append("Delta较低，期权对标的资产变动不敏感，适合震荡市场")

        # 基于Gamma的策略
        gamma = greeks["gamma"]
        if gamma > 0.05:
            strategies.append("Gamma较高，Delta变化快，适合对冲策略")

        # 基于Vega的策略
        vega = greeks["vega"]
        if vega > 0.2:
            strategies.append("Vega较高，期权对波动率变化敏感，注意波动率风险")

        # 基于隐含波动率的策略
        if implied_volatility > 0.4:
            strategies.append(f"隐含波动率偏高（{implied_volatility:.1%}），可考虑卖出期权策略")
        elif implied_volatility < 0.2:
            strategies.append(f"隐含波动率偏低（{implied_volatility:.1%}），可考虑买入期权策略")

        return strategies

    # ========== 辅助方法 ==========

    def _generate_recommendations(
        self,
        attribution_factors: Dict[str, Any],
        risk_factors: Dict[str, Any],
        option_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 归因建议
        primary = attribution_factors["primary_factor"]
        recommendations.append(f"主要收益归因于【{primary}】，建议关注该因子变化")

        # 风险建议
        risk_level = risk_factors["risk_level"]
        if risk_level == "高风险":
            recommendations.append(f"综合风险评分较高，建议控制仓位或使用期权对冲")
        elif risk_level == "低风险":
            recommendations.append(f"综合风险评分较低，可适当增加仓位")

        # Beta建议
        beta = risk_factors["beta"]
        if beta > 1.2:
            recommendations.append(f"Beta较高（{beta:.2f}），波动大于市场，注意系统性风险")

        # 流动性建议
        liquidity = risk_factors["liquidity"]
        if liquidity < 0.5:
            recommendations.append(f"流动性较低（{liquidity:.2f}），注意交易成本和冲击成本")

        # 期权建议
        if option_analysis.get("strategy_suggestions"):
            recommendations.extend(option_analysis["strategy_suggestions"])

        return recommendations

    def _identify_risks(
        self,
        attribution_factors: Dict[str, Any],
        risk_factors: Dict[str, Any],
        option_analysis: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 风险评分风险
        if risk_factors["risk_score"] > 0.7:
            risks.append(f"综合风险评分较高（{risk_factors['risk_score']:.2f}），存在较大风险")

        # 波动率风险
        if risk_factors["volatility"] > 0.4:
            risks.append(f"波动率较高（{risk_factors['volatility']:.1%}），价格波动大")

        # Beta风险
        if risk_factors["beta"] > 1.5:
            risks.append(f"Beta过高（{risk_factors['beta']:.2f}），系统性风险较大")

        # 期权风险
        theta = option_analysis.get("greeks", {}).get("theta", 0)
        if theta < -0.1:
            risks.append(f"Theta损耗较高（{theta:.4f}），时间价值衰减快")

        # 隐含波动率风险
        iv = option_analysis.get("implied_volatility", 0)
        if iv > 0.5:
            risks.append(f"隐含波动率过高（{iv:.1%}），期权价格可能被高估")

        if not risks:
            risks.append("未发现明显归因期权风险")

        return risks

    def _generate_conclusion(
        self,
        attribution_factors: Dict[str, Any],
        option_analysis: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        primary = attribution_factors["primary_factor"]
        call_price = option_analysis.get("call_price", 0)
        iv = option_analysis.get("implied_volatility", 0)

        return (
            f"主要归因【{primary}】，"
            f"看涨期权价格{call_price:.2f}元，"
            f"隐含波动率{iv:.1%}"
        )


# 便捷函数
async def analyze_attribution_option(
    stock_code: str,
    current_price: float,
    benchmark_return: float = 0.0,
    option_params: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    归因期权分析（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        benchmark_return: 基准收益
        option_params: 期权参数

    Returns:
        分析结果
    """
    ai = AttributionOptionAI()
    return await ai.analyze(
        stock_code,
        current_price=current_price,
        benchmark_return=benchmark_return,
        option_params=option_params or {}
    )

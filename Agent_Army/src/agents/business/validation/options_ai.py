"""
期权衍生品AI - Options & Derivatives AI

结果验证军团成员

职责：
1. 期权定价分析（Black-Scholes模型、二叉树模型）
2. 期权策略建议（备兑、保护性看跌、价差等）
3. Greeks风险分析（Delta、Gamma、Vega、Theta、Rho）
4. 隐含波动率分析（IV、IV Rank、IV Percentile）
5. 期权组合风险监控
6. 套利机会识别

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
- FormulaTool（数学公式计算）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, LLMTool


class OptionsAI(BaseAgent, LoggerMixin):
    """
    期权衍生品AI - 结果验证军团成员

    核心能力:
    1. 期权定价分析（Black-Scholes模型、二叉树模型）
    2. 期权策略建议（备兑、保护性看跌、价差等）
    3. Greeks风险分析（Delta、Gamma、Vega、Theta、Rho）
    4. 隐含波动率分析（IV、IV Rank、IV Percentile）
    5. 期权组合风险监控
    6. 套利机会识别

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    - FormulaTool (数学公式计算)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="期权衍生品AI",
            role="分析期权策略，管理衍生品风险",
            capabilities=[
                AgentCapability(
                    name="option_pricing",
                    description="期权定价",
                    input_type="option_params",
                    output_type="option_price"
                ),
                AgentCapability(
                    name="greeks_analysis",
                    description="Greeks风险分析",
                    input_type="option_params",
                    output_type="greeks"
                ),
                AgentCapability(
                    name="iv_analysis",
                    description="隐含波动率分析",
                    input_type="option_chain",
                    output_type="iv_analysis"
                ),
                AgentCapability(
                    name="strategy_recommendation",
                    description="期权策略建议",
                    input_type="market_view",
                    output_type="option_strategy"
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

        self.logger.info("期权衍生品AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "option_pricing":
            return await self._calculate_option_price(**kwargs)
        elif task == "greeks_analysis":
            return await self._calculate_greeks(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        current_price: float,
        option_type: str = "call",
        strike_price: Optional[float] = None,
        days_to_expiry: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        期权综合分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价
            option_type: 期权类型（call/put）
            strike_price: 行权价（默认为平值）
            days_to_expiry: 到期天数

        Returns:
            期权综合分析报告
        """
        self.logger.info(
            f"开始期权综合分析",
            extra={
                "stock_code": stock_code,
                "current_price": current_price,
                "option_type": option_type
            }
        )

        # 设置默认行权价（平值）
        if strike_price is None:
            strike_price = current_price

        # ========== 1. 期权定价 ==========
        option_price = await self._calculate_option_price(
            current_price,
            strike_price,
            days_to_expiry,
            option_type
        )

        # ========== 2. Greeks风险分析 ==========
        greeks = await self._calculate_greeks(
            current_price,
            strike_price,
            days_to_expiry,
            option_type
        )

        # ========== 3. 隐含波动率分析 ==========
        iv_analysis = await self._analyze_implied_volatility(
            stock_code,
            current_price
        )

        # ========== 4. 期权策略建议 ==========
        strategy_recommendation = await self._recommend_option_strategy(
            current_price,
            strike_price,
            days_to_expiry,
            option_type,
            greeks,
            iv_analysis
        )

        # ========== 5. 盈亏分析 ==========
        payoff_analysis = self._analyze_payoff(
            current_price,
            strike_price,
            option_price["price"],
            option_type
        )

        # ========== 6. 风险提示 ==========
        risk_warnings = self._generate_risk_warnings(
            greeks,
            iv_analysis,
            days_to_expiry
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "options_analysis",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "current_price": current_price,
            "option_type": option_type,
            "strike_price": strike_price,
            "days_to_expiry": days_to_expiry,

            # 期权定价
            "option_price": option_price,

            # Greeks
            "greeks": greeks,

            # 隐含波动率
            "iv_analysis": iv_analysis,

            # 策略建议
            "strategy_recommendation": strategy_recommendation,

            # 盈亏分析
            "payoff_analysis": payoff_analysis,

            # 风险提示
            "risk_warnings": risk_warnings
        }

        self.logger.info(
            f"期权综合分析完成",
            extra={
                "stock_code": stock_code,
                "option_price": option_price["price"],
                "delta": greeks["delta"]
            }
        )

        return result

    # ========== 期权定价（Black-Scholes模型）==========

    async def _calculate_option_price(
        self,
        S: float,  # 当前股价
        K: float,  # 行权价
        T: int,    # 到期天数
        option_type: str,
        r: float = 0.03,  # 无风险利率
        sigma: float = 0.25  # 波动率
    ) -> Dict[str, Any]:
        """
        Black-Scholes期权定价

        Args:
            S: 当前股价
            K: 行权价
            T: 到期天数
            option_type: 期权类型
            r: 无风险利率
            sigma: 波动率

        Returns:
            期权价格
        """
        # 转换为年化时间
        t = T / 365.0

        # 计算d1和d2
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        # 计算期权价格
        if option_type == "call":
            price = S * self._norm_cdf(d1) - K * math.exp(-r * t) * self._norm_cdf(d2)
        else:  # put
            price = K * math.exp(-r * t) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)

        # 计算内在价值和时间价值
        if option_type == "call":
            intrinsic_value = max(S - K, 0)
        else:
            intrinsic_value = max(K - S, 0)

        time_value = price - intrinsic_value

        return {
            "price": round(price, 2),
            "intrinsic_value": round(intrinsic_value, 2),
            "time_value": round(time_value, 2),
            "model": "Black-Scholes",
            "parameters": {
                "spot_price": S,
                "strike_price": K,
                "days_to_expiry": T,
                "risk_free_rate": r,
                "volatility": sigma
            },
            "update_time": datetime.now().isoformat()
        }

    # ========== Greeks计算 ==========

    async def _calculate_greeks(
        self,
        S: float,
        K: float,
        T: int,
        option_type: str,
        r: float = 0.03,
        sigma: float = 0.25
    ) -> Dict[str, Any]:
        """
        计算Greeks

        Args:
            S: 当前股价
            K: 行权价
            T: 到期天数
            option_type: 期权类型
            r: 无风险利率
            sigma: 波动率

        Returns:
            Greeks
        """
        t = T / 365.0

        # 计算d1和d2
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        # Delta
        if option_type == "call":
            delta = self._norm_cdf(d1)
        else:
            delta = self._norm_cdf(d1) - 1

        # Gamma
        gamma = self._norm_pdf(d1) / (S * sigma * math.sqrt(t))

        # Vega
        vega = S * self._norm_pdf(d1) * math.sqrt(t) / 100  # 每1%波动率变化

        # Theta
        if option_type == "call":
            theta = (
                -S * self._norm_pdf(d1) * sigma / (2 * math.sqrt(t))
                - r * K * math.exp(-r * t) * self._norm_cdf(d2)
            ) / 365  # 每天
        else:
            theta = (
                -S * self._norm_pdf(d1) * sigma / (2 * math.sqrt(t))
                + r * K * math.exp(-r * t) * self._norm_cdf(-d2)
            ) / 365

        # Rho
        if option_type == "call":
            rho = K * t * math.exp(-r * t) * self._norm_cdf(d2) / 100  # 每1%利率变化
        else:
            rho = -K * t * math.exp(-r * t) * self._norm_cdf(-d2) / 100

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "vega": round(vega, 4),
            "theta": round(theta, 4),
            "rho": round(rho, 4),
            "interpretations": {
                "delta": f"股价每变动1元，期权价格变动{abs(delta):.2f}元",
                "gamma": f"股价每变动1元，Delta变动{gamma:.4f}",
                "vega": f"波动率每变动1%，期权价格变动{vega:.2f}元",
                "theta": f"每经过1天，期权价格变动{theta:.2f}元",
                "rho": f"利率每变动1%，期权价格变动{rho:.2f}元"
            },
            "update_time": datetime.now().isoformat()
        }

    # ========== 隐含波动率分析 ==========

    async def _analyze_implied_volatility(
        self,
        stock_code: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        隐含波动率分析

        Args:
            stock_code: 股票代码
            current_price: 当前股价

        Returns:
            隐含波动率分析结果
        """
        # TODO: 接入真实期权链数据
        # 当前返回模拟数据

        implied_volatility = 25.0  # 当前IV
        historical_volatility = 20.0  # 历史波动率
        iv_rank = 45.0  # IV Rank（过去一年IV排名）
        iv_percentile = 52.0  # IV Percentile

        # IV评估
        if iv_rank >= 70:
            iv_level = "高"
            iv_comment = "隐含波动率较高，期权价格昂贵，适合卖方策略"
        elif iv_rank >= 30:
            iv_level = "中"
            iv_comment = "隐含波动率适中，期权价格合理"
        else:
            iv_level = "低"
            iv_comment = "隐含波动率较低，期权价格便宜，适合买方策略"

        # IV vs HV
        iv_premium = implied_volatility - historical_volatility

        return {
            "implied_volatility": implied_volatility,
            "historical_volatility": historical_volatility,
            "iv_premium": round(iv_premium, 2),
            "iv_rank": iv_rank,
            "iv_percentile": iv_percentile,
            "iv_level": iv_level,
            "iv_comment": iv_comment,
            "update_time": datetime.now().isoformat()
        }

    # ========== 期权策略建议 ==========

    async def _recommend_option_strategy(
        self,
        current_price: float,
        strike_price: float,
        days_to_expiry: int,
        option_type: str,
        greeks: Dict[str, Any],
        iv_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        期权策略建议

        Args:
            current_price: 当前股价
            strike_price: 行权价
            days_to_expiry: 到期天数
            option_type: 期权类型
            greeks: Greeks
            iv_analysis: 隐含波动率分析

        Returns:
            期权策略建议
        """
        strategies = []

        # 基于IV水平的策略
        iv_level = iv_analysis["iv_level"]

        if iv_level == "高":
            strategies.append({
                "strategy": "备兑看涨期权（Covered Call）",
                "suitability": "高",
                "description": "持有正股+卖出看涨期权，在IV高时获取权利金",
                "risk": "有限（股价下跌风险）",
                "reward": "有限（权利金收入）",
                "breakeven": round(current_price - 2.0, 2)
            })

            strategies.append({
                "strategy": "卖出宽跨式（Short Strangle）",
                "suitability": "中",
                "description": "卖出虚值看涨+看跌期权，在IV高时获利",
                "risk": "无限",
                "reward": "有限（权利金收入）",
                "breakeven": f"{round(current_price * 0.90, 2)} - {round(current_price * 1.10, 2)}"
            })

        elif iv_level == "低":
            strategies.append({
                "strategy": "买入跨式（Long Straddle）",
                "suitability": "中",
                "description": "买入平值看涨+看跌期权，在IV低时成本较低",
                "risk": "有限（权利金）",
                "reward": "无限",
                "breakeven": f"{round(current_price - 5.0, 2)} 或 {round(current_price + 5.0, 2)}"
            })

            strategies.append({
                "strategy": "保护性看跌期权（Protective Put）",
                "suitability": "高",
                "description": "持有正股+买入看跌期权，在IV低时成本较低",
                "risk": "有限（下跌保护）",
                "reward": "无限（股价上涨空间）",
                "breakeven": round(current_price + 2.0, 2)
            })

        else:  # IV中等
            strategies.append({
                "strategy": "牛市价差（Bull Call Spread）",
                "suitability": "中",
                "description": "买入低行权价看涨+卖出高行权价看涨",
                "risk": "有限",
                "reward": "有限",
                "breakeven": round(current_price + 1.0, 2)
            })

        # 推荐最佳策略
        best_strategy = strategies[0] if strategies else None

        return {
            "strategies": strategies,
            "best_strategy": best_strategy,
            "market_outlook": "震荡偏多",
            "update_time": datetime.now().isoformat()
        }

    # ========== 盈亏分析 ==========

    def _analyze_payoff(
        self,
        current_price: float,
        strike_price: float,
        premium: float,
        option_type: str
    ) -> Dict[str, Any]:
        """
        盈亏分析

        Args:
            current_price: 当前股价
            strike_price: 行权价
            premium: 权利金
            option_type: 期权类型

        Returns:
            盈亏分析
        """
        # 计算不同股价下的盈亏
        scenarios = []
        for price_change_pct in [-20, -10, 0, 10, 20]:
            scenario_price = current_price * (1 + price_change_pct / 100)

            if option_type == "call":
                payoff = max(scenario_price - strike_price, 0) - premium
            else:
                payoff = max(strike_price - scenario_price, 0) - premium

            profit_pct = (payoff / premium) * 100 if premium > 0 else 0

            scenarios.append({
                "stock_price": round(scenario_price, 2),
                "price_change_pct": price_change_pct,
                "payoff": round(payoff, 2),
                "profit_pct": round(profit_pct, 2)
            })

        # 计算盈亏平衡点
        if option_type == "call":
            breakeven = strike_price + premium
        else:
            breakeven = strike_price - premium

        return {
            "scenarios": scenarios,
            "breakeven": round(breakeven, 2),
            "max_profit": "无限" if option_type == "call" else round(strike_price - premium, 2),
            "max_loss": round(premium, 2),
            "update_time": datetime.now().isoformat()
        }

    # ========== 风险提示 ==========

    def _generate_risk_warnings(
        self,
        greeks: Dict[str, Any],
        iv_analysis: Dict[str, Any],
        days_to_expiry: int
    ) -> List[Dict[str, Any]]:
        """
        生成风险提示

        Args:
            greeks: Greeks
            iv_analysis: 隐含波动率分析
            days_to_expiry: 到期天数

        Returns:
            风险提示列表
        """
        warnings = []

        # Gamma风险
        if abs(greeks["gamma"]) > 0.1:
            warnings.append({
                "type": "Gamma风险",
                "level": "高",
                "description": "Gamma较高，Delta变化快，需要频繁对冲"
            })

        # Theta风险
        if greeks["theta"] < -0.5:
            warnings.append({
                "type": "时间衰减风险",
                "level": "高",
                "description": f"Theta为{greeks['theta']:.2f}，时间价值快速衰减"
            })

        # IV风险
        if iv_analysis["iv_level"] == "高":
            warnings.append({
                "type": "波动率风险",
                "level": "中",
                "description": "IV较高，波动率下降会导致期权价格下跌"
            })

        # 到期风险
        if days_to_expiry <= 7:
            warnings.append({
                "type": "到期风险",
                "level": "高",
                "description": f"距离到期仅{days_to_expiry}天，时间价值即将归零"
            })

        # 流动性风险
        warnings.append({
            "type": "流动性风险",
            "level": "中",
            "description": "部分期权合约流动性较差，买卖价差可能较大"
        })

        return warnings

    # ========== 辅助数学函数 ==========

    def _norm_cdf(self, x: float) -> float:
        """标准正态分布累积分布函数"""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def _norm_pdf(self, x: float) -> float:
        """标准正态分布概率密度函数"""
        return math.exp(-0.5 * x ** 2) / math.sqrt(2.0 * math.pi)

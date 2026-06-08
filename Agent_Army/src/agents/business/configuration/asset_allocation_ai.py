"""
资产配置AI - Asset Allocation AI

配置部成员 (1/2)

职责：
1. 资产配置策略 - 股债平衡、行业配置
2. 风险平价配置 - 基于风险贡献的资产配置
3. 动态再平衡 - 根据市场变化调整配置

使用工具：
- FinancialTool（财务数据）
- MarketTool（市场数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class AssetAllocationAI(BusinessAgent):
    """
    资产配置AI - 配置部成员 (1/2)

    核心能力:
    1. 资产配置策略 - 股债平衡、行业配置
    2. 风险平价配置 - 基于风险贡献优化配置
    3. 动态再平衡 - 市场变化时自动调整

    使用工具:
    - FinancialTool (财务数据)
    - MarketTool (市场数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="资产配置AI",
            role="制定资产配置策略，优化投资组合",
            corps="configuration",
            analysis_type="asset_allocation",
            capabilities=[
                AgentCapability(
                    name="strategic_allocation",
                    description="战略性资产配置",
                    input_type="portfolio_requirements",
                    output_type="allocation_plan"
                ),
                AgentCapability(
                    name="risk_parity",
                    description="风险平价配置",
                    input_type="risk_targets",
                    output_type="risk_parity_weights"
                ),
                AgentCapability(
                    name="dynamic_rebalance",
                    description="动态再平衡",
                    input_type="current_allocation",
                    output_type="rebalance_suggestions"
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
                    name="market_tool",
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

        # 配置参数
        self.risk_free_rate = 0.03  # 无风险利率 3%
        self.default_volatility_threshold = 0.20  # 默认波动率阈值 20%

        self.logger.info("资产配置AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行资产配置分析

        Args:
            stock_code: 股票代码（用于获取基准信息）
            **kwargs: 其他参数
                - portfolio_size: 投资组合规模（必需）
                - risk_tolerance: 风险承受能力（保守/稳健/激进）
                - investment_horizon: 投资期限（短期/中期/长期）
                - current_allocation: 当前配置（可选）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        portfolio_size = kwargs.get("portfolio_size")
        if not portfolio_size:
            raise ValueError("缺少portfolio_size参数")

        risk_tolerance = kwargs.get("risk_tolerance", "稳健")
        investment_horizon = kwargs.get("investment_horizon", "中期")
        current_allocation = kwargs.get("current_allocation")

        self.logger.info(
            f"开始资产配置分析",
            extra={
                "stock_code": stock_code,
                "portfolio_size": portfolio_size,
                "risk_tolerance": risk_tolerance,
                "investment_horizon": investment_horizon
            }
        )

        # ========== 1. 战略性资产配置 ==========
        strategic_allocation = await self._strategic_asset_allocation(
            portfolio_size,
            risk_tolerance,
            investment_horizon
        )

        # ========== 2. 风险平价配置 ==========
        risk_parity_weights = self._calculate_risk_parity_weights(
            strategic_allocation,
            risk_tolerance
        )

        # ========== 3. 行业配置建议 ==========
        sector_allocation = await self._generate_sector_allocation(
            stock_code,
            risk_tolerance
        )

        # ========== 4. 动态再平衡建议 ==========
        rebalance_suggestions = self._generate_rebalance_suggestions(
            current_allocation,
            risk_parity_weights
        )

        # ========== 5. 风险分析 ==========
        risk_analysis = self._analyze_portfolio_risk(
            risk_parity_weights,
            strategic_allocation
        )

        # ========== 6. 构建分析结果 ==========
        details = {
            "portfolio_size": portfolio_size,
            "risk_tolerance": risk_tolerance,
            "investment_horizon": investment_horizon,

            # 战略性配置
            "strategic_allocation": strategic_allocation,

            # 风险平价权重
            "risk_parity_weights": risk_parity_weights,

            # 行业配置
            "sector_allocation": sector_allocation,

            # 再平衡建议
            "rebalance_suggestions": rebalance_suggestions,

            # 风险分析
            "risk_analysis": risk_analysis,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        # 生成核心结论
        conclusion = self._generate_conclusion(
            strategic_allocation,
            risk_analysis,
            rebalance_suggestions
        )

        # 生成建议
        recommendations = self._generate_recommendations(
            strategic_allocation,
            risk_parity_weights,
            rebalance_suggestions
        )

        # 识别风险
        risks = self._identify_risks(
            risk_analysis,
            strategic_allocation
        )

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=conclusion,
            confidence=0.85,
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"资产配置分析完成",
            extra={
                "stock_code": stock_code,
                "equity_ratio": strategic_allocation["equity"]["ratio"],
                "bond_ratio": strategic_allocation["bond"]["ratio"],
                "expected_return": risk_analysis["expected_annual_return"]
            }
        )

        return result

    # ========== 核心配置方法 ==========

    async def _strategic_asset_allocation(
        self,
        portfolio_size: float,
        risk_tolerance: str,
        investment_horizon: str
    ) -> Dict[str, Any]:
        """
        战略性资产配置

        Args:
            portfolio_size: 投资组合规模
            risk_tolerance: 风险承受能力
            investment_horizon: 投资期限

        Returns:
            战略性配置方案
        """
        # 根据风险承受能力确定股债比例
        if risk_tolerance == "保守":
            equity_ratio = 0.20  # 股票20%
            bond_ratio = 0.70  # 债券70%
            cash_ratio = 0.10  # 现金10%
        elif risk_tolerance == "稳健":
            equity_ratio = 0.50  # 股票50%
            bond_ratio = 0.40  # 债券40%
            cash_ratio = 0.10  # 现金10%
        elif risk_tolerance == "激进":
            equity_ratio = 0.70  # 股票70%
            bond_ratio = 0.20  # 债券20%
            cash_ratio = 0.10  # 现金10%
        else:
            # 默认稳健型
            equity_ratio = 0.50
            bond_ratio = 0.40
            cash_ratio = 0.10

        # 根据投资期限调整
        if investment_horizon == "长期":
            # 长期投资可以提高股票比例
            equity_ratio = min(equity_ratio + 0.10, 0.80)
            bond_ratio = max(bond_ratio - 0.10, 0.10)
        elif investment_horizon == "短期":
            # 短期投资降低股票比例
            equity_ratio = max(equity_ratio - 0.10, 0.10)
            bond_ratio = min(bond_ratio + 0.10, 0.70)

        # 计算各资产配置金额
        equity_amount = portfolio_size * equity_ratio
        bond_amount = portfolio_size * bond_ratio
        cash_amount = portfolio_size * cash_ratio

        # 预期收益和风险
        expected_return = self._calculate_expected_return(
            equity_ratio, bond_ratio, cash_ratio
        )
        expected_volatility = self._calculate_expected_volatility(
            equity_ratio, bond_ratio
        )

        return {
            "equity": {
                "ratio": round(equity_ratio, 3),
                "amount": round(equity_amount, 2),
                "description": "股票资产"
            },
            "bond": {
                "ratio": round(bond_ratio, 3),
                "amount": round(bond_amount, 2),
                "description": "债券资产"
            },
            "cash": {
                "ratio": round(cash_ratio, 3),
                "amount": round(cash_amount, 2),
                "description": "现金及等价物"
            },
            "expected_return": round(expected_return, 3),
            "expected_volatility": round(expected_volatility, 3),
            "sharpe_ratio": round(
                (expected_return - self.risk_free_rate) / expected_volatility, 3
            ),
            "allocation_type": f"{risk_tolerance}型{investment_horizon}配置"
        }

    def _calculate_risk_parity_weights(
        self,
        strategic_allocation: Dict[str, Any],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        计算风险平价权重

        基于风险贡献而非资金贡献来配置资产
        """
        # 获取战略性配置比例
        equity_ratio = strategic_allocation["equity"]["ratio"]
        bond_ratio = strategic_allocation["bond"]["ratio"]
        cash_ratio = strategic_allocation["cash"]["ratio"]

        # 假设各资产类别波动率
        equity_volatility = 0.25  # 股票年化波动率 25%
        bond_volatility = 0.08  # 债券年化波动率 8%
        cash_volatility = 0.01  # 现金年化波动率 1%

        # 计算风险贡献
        equity_risk_contribution = equity_ratio * equity_volatility
        bond_risk_contribution = bond_ratio * bond_volatility
        cash_risk_contribution = cash_ratio * cash_volatility

        total_risk = (
            equity_risk_contribution +
            bond_risk_contribution +
            cash_risk_contribution
        )

        # 计算风险平价权重（使各资产风险贡献相等）
        # 简化版本：风险平价权重 = 1/波动率
        inv_equity_vol = 1 / equity_volatility
        inv_bond_vol = 1 / bond_volatility
        inv_cash_vol = 1 / cash_volatility

        total_inv_vol = inv_equity_vol + inv_bond_vol + inv_cash_vol

        rp_equity = inv_equity_vol / total_inv_vol
        rp_bond = inv_bond_vol / total_inv_vol
        rp_cash = inv_cash_vol / total_inv_vol

        # 根据风险承受能力调整
        if risk_tolerance == "保守":
            # 降低股票风险贡献
            rp_equity *= 0.7
            rp_bond *= 1.2
        elif risk_tolerance == "激进":
            # 提高股票风险贡献
            rp_equity *= 1.2
            rp_bond *= 0.8

        # 重新归一化
        total_weight = rp_equity + rp_bond + rp_cash
        rp_equity /= total_weight
        rp_bond /= total_weight
        rp_cash /= total_weight

        return {
            "risk_parity_equity": round(rp_equity, 3),
            "risk_parity_bond": round(rp_bond, 3),
            "risk_parity_cash": round(rp_cash, 3),
            "risk_contributions": {
                "equity": round(rp_equity * equity_volatility, 3),
                "bond": round(rp_bond * bond_volatility, 3),
                "cash": round(rp_cash * cash_volatility, 3)
            },
            "volatility_assumptions": {
                "equity": equity_volatility,
                "bond": bond_volatility,
                "cash": cash_volatility
            },
            "description": "基于风险平价的资产配置权重"
        }

    async def _generate_sector_allocation(
        self,
        stock_code: str,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        生成行业配置建议

        Args:
            stock_code: 基准股票代码
            risk_tolerance: 风险承受能力

        Returns:
            行业配置方案
        """
        # TODO: 接入真实行业数据
        # 当前使用模拟数据

        # 核心行业配置（根据风险偏好调整）
        if risk_tolerance == "保守":
            sector_weights = {
                "金融": 0.25,  # 银行、保险
                "公用事业": 0.20,  # 电力、水务
                "消费": 0.20,  # 必需消费
                "医疗": 0.15,  # 医药、医疗设备
                "能源": 0.10,  # 石油、煤炭
                "科技": 0.10  # 软件、硬件
            }
        elif risk_tolerance == "稳健":
            sector_weights = {
                "金融": 0.20,
                "消费": 0.20,
                "科技": 0.18,
                "医疗": 0.15,
                "制造业": 0.12,
                "能源": 0.10,
                "公用事业": 0.05
            }
        else:  # 激进
            sector_weights = {
                "科技": 0.30,  # 高科技成长
                "消费": 0.20,
                "医疗": 0.15,
                "制造业": 0.15,
                "金融": 0.10,
                "新能源": 0.10
            }

        # 计算行业集中度
        weights_list = list(sector_weights.values())
        max_weight = max(weights_list)
        herfindahl_index = sum(w ** 2 for w in weights_list)

        # 生成配置建议
        allocation_suggestions = []

        if max_weight > 0.30:
            allocation_suggestions.append(
                f"单一行业权重过高（{max_weight:.1%}），建议分散风险"
            )

        if herfindahl_index > 0.25:
            allocation_suggestions.append(
                f"行业集中度较高（HHI={herfindahl_index:.3f}），建议增加行业多样性"
            )

        return {
            "sector_weights": {
                sector: round(weight, 3)
                for sector, weight in sector_weights.items()
            },
            "diversification_metrics": {
                "max_weight": round(max_weight, 3),
                "herfindahl_index": round(herfindahl_index, 3),
                "sector_count": len(sector_weights)
            },
            "allocation_suggestions": allocation_suggestions,
            "description": f"{risk_tolerance}型行业配置方案"
        }

    def _generate_rebalance_suggestions(
        self,
        current_allocation: Optional[Dict[str, Any]],
        target_weights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成再平衡建议

        Args:
            current_allocation: 当前配置
            target_weights: 目标权重（风险平价权重）

        Returns:
            再平衡建议
        """
        if not current_allocation:
            return {
                "need_rebalance": False,
                "reason": "无当前配置信息",
                "suggestions": []
            }

        # 提取当前权重
        current_equity = current_allocation.get("equity", 0.5)
        current_bond = current_allocation.get("bond", 0.4)
        current_cash = current_allocation.get("cash", 0.1)

        # 提取目标权重
        target_equity = target_weights["risk_parity_equity"]
        target_bond = target_weights["risk_parity_bond"]
        target_cash = target_weights["risk_parity_cash"]

        # 计算偏差
        equity_deviation = current_equity - target_equity
        bond_deviation = current_bond - target_bond
        cash_deviation = current_cash - target_cash

        # 判断是否需要再平衡（阈值5%）
        rebalance_threshold = 0.05
        need_rebalance = (
            abs(equity_deviation) > rebalance_threshold or
            abs(bond_deviation) > rebalance_threshold or
            abs(cash_deviation) > rebalance_threshold
        )

        # 生成再平衡建议
        suggestions = []

        if need_rebalance:
            if abs(equity_deviation) > rebalance_threshold:
                action = "减持" if equity_deviation > 0 else "增持"
                amount = abs(equity_deviation)
                suggestions.append(
                    f"{action}股票资产 {amount:.1%}，"
                    f"从{current_equity:.1%}调整至{target_equity:.1%}"
                )

            if abs(bond_deviation) > rebalance_threshold:
                action = "减持" if bond_deviation > 0 else "增持"
                amount = abs(bond_deviation)
                suggestions.append(
                    f"{action}债券资产 {amount:.1%}，"
                    f"从{current_bond:.1%}调整至{target_bond:.1%}"
                )

            if abs(cash_deviation) > rebalance_threshold:
                action = "减持" if cash_deviation > 0 else "增持"
                amount = abs(cash_deviation)
                suggestions.append(
                    f"{action}现金资产 {amount:.1%}，"
                    f"从{current_cash:.1%}调整至{target_cash:.1%}"
                )

        return {
            "need_rebalance": need_rebalance,
            "current_allocation": {
                "equity": round(current_equity, 3),
                "bond": round(current_bond, 3),
                "cash": round(current_cash, 3)
            },
            "target_allocation": {
                "equity": round(target_equity, 3),
                "bond": round(target_bond, 3),
                "cash": round(target_cash, 3)
            },
            "deviations": {
                "equity": round(equity_deviation, 3),
                "bond": round(bond_deviation, 3),
                "cash": round(cash_deviation, 3)
            },
            "suggestions": suggestions,
            "rebalance_method": "定期再平衡（建议每季度检查）"
        }

    def _analyze_portfolio_risk(
        self,
        weights: Dict[str, Any],
        strategic_allocation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析投资组合风险

        Args:
            weights: 权重配置
            strategic_allocation: 战略性配置

        Returns:
            风险分析结果
        """
        # 提取权重
        equity_weight = weights["risk_parity_equity"]
        bond_weight = weights["risk_parity_bond"]
        cash_weight = weights["risk_parity_cash"]

        # 波动率假设
        equity_vol = weights["volatility_assumptions"]["equity"]
        bond_vol = weights["volatility_assumptions"]["bond"]
        cash_vol = weights["volatility_assumptions"]["cash"]

        # 相关系数假设
        equity_bond_correlation = -0.2  # 股债负相关
        equity_cash_correlation = 0.0  # 股票与现金无相关
        bond_cash_correlation = 0.0  # 债券与现金无相关

        # 计算组合波动率
        portfolio_variance = (
            (equity_weight * equity_vol) ** 2 +
            (bond_weight * bond_vol) ** 2 +
            (cash_weight * cash_vol) ** 2 +
            2 * equity_weight * bond_weight * equity_bond_correlation * equity_vol * bond_vol
        )

        portfolio_volatility = portfolio_variance ** 0.5

        # 计算预期收益
        expected_return = strategic_allocation["expected_return"]

        # 计算VaR（95%置信度）
        var_95 = expected_return - 1.65 * portfolio_volatility

        # 计算CVaR（95%置信度）
        cvar_95 = expected_return - 2.0 * portfolio_volatility

        # 最大回撤估计
        max_drawdown = -2.0 * portfolio_volatility

        return {
            "portfolio_volatility": round(portfolio_volatility, 3),
            "expected_annual_return": round(expected_return, 3),
            "var_95": round(var_95, 3),
            "cvar_95": round(cvar_95, 3),
            "max_drawdown_estimate": round(max_drawdown, 3),
            "risk_level": self._assess_risk_level(portfolio_volatility),
            "sharpe_ratio": strategic_allocation["sharpe_ratio"],
            "risk_metrics": {
                "volatility": f"{portfolio_volatility:.1%}",
                "var_95": f"{var_95:.1%}",
                "max_drawdown": f"{max_drawdown:.1%}"
            }
        }

    # ========== 辅助方法 ==========

    def _calculate_expected_return(
        self,
        equity_ratio: float,
        bond_ratio: float,
        cash_ratio: float
    ) -> float:
        """计算预期收益"""
        equity_return = 0.10  # 股票预期年化收益 10%
        bond_return = 0.05  # 债券预期年化收益 5%
        cash_return = 0.03  # 现金预期年化收益 3%

        return (
            equity_ratio * equity_return +
            bond_ratio * bond_return +
            cash_ratio * cash_return
        )

    def _calculate_expected_volatility(
        self,
        equity_ratio: float,
        bond_ratio: float
    ) -> float:
        """计算预期波动率"""
        equity_vol = 0.25  # 股票波动率
        bond_vol = 0.08  # 债券波动率
        correlation = -0.2  # 股债相关系数

        variance = (
            (equity_ratio * equity_vol) ** 2 +
            (bond_ratio * bond_vol) ** 2 +
            2 * equity_ratio * bond_ratio * correlation * equity_vol * bond_vol
        )

        return variance ** 0.5

    def _assess_risk_level(self, volatility: float) -> str:
        """评估风险等级"""
        if volatility < 0.10:
            return "低风险"
        elif volatility < 0.15:
            return "中低风险"
        elif volatility < 0.20:
            return "中等风险"
        elif volatility < 0.25:
            return "中高风险"
        else:
            return "高风险"

    def _generate_conclusion(
        self,
        strategic_allocation: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        rebalance_suggestions: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        equity_ratio = strategic_allocation["equity"]["ratio"]
        expected_return = risk_analysis["expected_annual_return"]
        volatility = risk_analysis["portfolio_volatility"]
        risk_level = risk_analysis["risk_level"]

        conclusion = (
            f"推荐配置股票{equity_ratio:.1%}，"
            f"预期年化收益{expected_return:.1%}，"
            f"波动率{volatility:.1%}（{risk_level}）"
        )

        if rebalance_suggestions["need_rebalance"]:
            conclusion += "，建议进行再平衡调整"

        return conclusion

    def _generate_recommendations(
        self,
        strategic_allocation: Dict[str, Any],
        risk_parity_weights: Dict[str, Any],
        rebalance_suggestions: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 配置建议
        equity_ratio = strategic_allocation["equity"]["ratio"]
        recommendations.append(
            f"采用{strategic_allocation['allocation_type']}，"
            f"股票配置{equity_ratio:.1%}"
        )

        # 风险平价建议
        recommendations.append(
            "基于风险平价优化配置权重，"
            "使各资产风险贡献更均衡"
        )

        # 再平衡建议
        if rebalance_suggestions["need_rebalance"]:
            recommendations.extend(rebalance_suggestions["suggestions"])
        else:
            recommendations.append("当前配置合理，暂不需要再平衡")

        # 风险管理建议
        volatility = strategic_allocation["expected_volatility"]
        if volatility > 0.20:
            recommendations.append(
                "组合波动率较高，建议设置止损线（-15%）"
            )

        recommendations.append("建议每季度检查一次配置，必要时进行再平衡")

        return recommendations

    def _identify_risks(
        self,
        risk_analysis: Dict[str, Any],
        strategic_allocation: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        volatility = risk_analysis["portfolio_volatility"]
        max_drawdown = risk_analysis["max_drawdown_estimate"]

        # 波动率风险
        if volatility > 0.25:
            risks.append(
                f"组合波动率较高（{volatility:.1%}），"
                "可能面临较大净值波动"
            )

        # 最大回撤风险
        if max_drawdown < -0.40:
            risks.append(
                f"估计最大回撤{max_drawdown:.1%}，"
                "需注意下行风险控制"
            )

        # 集中度风险
        equity_ratio = strategic_allocation["equity"]["ratio"]
        if equity_ratio > 0.70:
            risks.append(
                f"股票配置过高（{equity_ratio:.1%}），"
                "建议适当分散到债券资产"
            )

        # 市场风险
        risks.append("股市大幅波动可能影响组合收益")
        risks.append("利率上升可能导致债券价格下跌")

        return risks


# 便捷函数
async def analyze_asset_allocation(
    stock_code: str,
    portfolio_size: float,
    risk_tolerance: str = "稳健",
    investment_horizon: str = "中期",
    current_allocation: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    资产配置分析（便捷函数）

    Args:
        stock_code: 股票代码
        portfolio_size: 投资组合规模
        risk_tolerance: 风险承受能力
        investment_horizon: 投资期限
        current_allocation: 当前配置

    Returns:
        分析结果
    """
    ai = AssetAllocationAI()
    return await ai.analyze(
        stock_code,
        portfolio_size=portfolio_size,
        risk_tolerance=risk_tolerance,
        investment_horizon=investment_horizon,
        current_allocation=current_allocation
    )

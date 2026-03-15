"""
风险归因AI - Risk Attribution AI

结果验证军团成员

职责：
1. 市场风险归因（系统性风险贡献）
2. 因子风险归因（因子暴露风险）
3. 行业风险归因（行业集中度风险）
4. 个股风险归因（个股波动贡献）
5. 流动性风险归因（流动性风险贡献）
6. 风险管理建议

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
- FormulaTool（财务指标计算）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool, LLMTool


class RiskAttributionAI(BaseAgent, LoggerMixin):
    """
    风险归因AI - 结果验证军团成员

    核心能力:
    1. 市场风险归因（系统性风险贡献）
    2. 因子风险归因（因子暴露风险）
    3. 行业风险归因（行业集中度风险）
    4. 个股风险归因（个股波动贡献）
    5. 流动性风险归因（流动性风险贡献）
    6. 风险管理建议

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    - FormulaTool (财务指标计算)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="风险归因AI",
            role="分析风险来源，优化风险管理",
            capabilities=[
                AgentCapability(
                    name="market_risk_attribution",
                    description="市场风险归因",
                    input_type="portfolio",
                    output_type="market_risk"
                ),
                AgentCapability(
                    name="factor_risk_attribution",
                    description="因子风险归因",
                    input_type="portfolio",
                    output_type="factor_risk"
                ),
                AgentCapability(
                    name="industry_risk_attribution",
                    description="行业风险归因",
                    input_type="portfolio",
                    output_type="industry_risk"
                ),
                AgentCapability(
                    name="stock_risk_attribution",
                    description="个股风险归因",
                    input_type="portfolio",
                    output_type="stock_risk"
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

        self.logger.info("风险归因AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "market_risk":
            return await self._analyze_market_risk(**kwargs)
        elif task == "factor_risk":
            return await self._analyze_factor_risk(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        portfolio_volatility: float,
        holdings: List[Dict[str, Any]],
        total_value: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        风险归因综合分析

        Args:
            portfolio_volatility: 组合波动率
            holdings: 持仓列表
            total_value: 总市值

        Returns:
            风险归因综合报告
        """
        self.logger.info(
            f"开始风险归因综合分析",
            extra={
                "portfolio_volatility": portfolio_volatility,
                "holdings_count": len(holdings),
                "total_value": total_value
            }
        )

        # ========== 1. 市场风险归因 ==========
        market_risk = await self._analyze_market_risk(portfolio_volatility, holdings)

        # ========== 2. 因子风险归因 ==========
        factor_risk = await self._analyze_factor_risk(holdings)

        # ========== 3. 行业风险归因 ==========
        industry_risk = await self._analyze_industry_risk(holdings)

        # ========== 4. 个股风险归因 ==========
        stock_risk = await self._analyze_stock_risk(holdings)

        # ========== 5. 流动性风险归因 ==========
        liquidity_risk = await self._analyze_liquidity_risk(holdings, total_value)

        # ========== 6. 风险管理建议 ==========
        risk_management = self._generate_risk_management(
            market_risk,
            factor_risk,
            industry_risk,
            stock_risk,
            liquidity_risk
        )

        # ========== 7. 构建返回结果 ==========
        result = {
            "analysis_type": "risk_attribution",
            "timestamp": datetime.now().isoformat(),
            "portfolio_volatility": portfolio_volatility,
            "holdings_count": len(holdings),
            "total_value": total_value,

            # 市场风险
            "market_risk": market_risk,

            # 因子风险
            "factor_risk": factor_risk,

            # 行业风险
            "industry_risk": industry_risk,

            # 个股风险
            "stock_risk": stock_risk,

            # 流动性风险
            "liquidity_risk": liquidity_risk,

            # 风险管理
            "risk_management": risk_management
        }

        self.logger.info(
            f"风险归因综合分析完成",
            extra={
                "total_risk": portfolio_volatility,
                "market_risk_pct": market_risk["risk_percentage"],
                "specific_risk_pct": stock_risk["risk_percentage"]
            }
        )

        return result

    # ========== 核心分析方法 ==========

    async def _analyze_market_risk(
        self,
        portfolio_volatility: float,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        市场风险归因分析

        Args:
            portfolio_volatility: 组合波动率
            holdings: 持仓列表

        Returns:
            市场风险归因结果
        """
        # TODO: 接入真实市场数据
        # 计算Beta
        beta = self._calculate_portfolio_beta(holdings)

        # 市场波动率（假设沪深300波动率15%）
        market_volatility = 15.0

        # 系统性风险 = Beta * 市场波动率
        systematic_risk = beta * market_volatility

        # 特质性风险（残差）
        specific_risk = (portfolio_volatility ** 2 - systematic_risk ** 2) ** 0.5

        # 风险贡献百分比
        systematic_pct = (systematic_risk / portfolio_volatility) * 100
        specific_pct = (specific_risk / portfolio_volatility) * 100

        return {
            "portfolio_beta": round(beta, 2),
            "market_volatility": market_volatility,
            "systematic_risk": round(systematic_risk, 2),
            "specific_risk": round(specific_risk, 2),
            "risk_percentage": round(systematic_pct, 2),
            "specific_percentage": round(specific_pct, 2),
            "description": f"系统性风险占比{systematic_pct:.1f}%，特质性风险占比{specific_pct:.1f}%",
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_factor_risk(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        因子风险归因分析

        Args:
            holdings: 持仓列表

        Returns:
            因子风险归因结果
        """
        # TODO: 接入真实因子数据
        factor_risks = {
            "市场因子": {
                "exposure": 1.0,
                "volatility": 15.0,
                "risk_contribution": 15.0,
                "percentage": 50.0
            },
            "规模因子": {
                "exposure": -0.2,
                "volatility": 8.0,
                "risk_contribution": 1.6,
                "percentage": 5.3
            },
            "价值因子": {
                "exposure": 0.3,
                "volatility": 10.0,
                "risk_contribution": 3.0,
                "percentage": 10.0
            },
            "动量因子": {
                "exposure": 0.15,
                "volatility": 12.0,
                "risk_contribution": 1.8,
                "percentage": 6.0
            },
            "质量因子": {
                "exposure": 0.25,
                "volatility": 8.0,
                "risk_contribution": 2.0,
                "percentage": 6.7
            }
        }

        # 计算总因子风险
        total_factor_risk = sum(
            factor["risk_contribution"] for factor in factor_risks.values()
        )

        # 识别主要风险因子
        dominant_factor = max(factor_risks.keys(),
                            key=lambda k: factor_risks[k]["risk_contribution"])

        return {
            "factor_risks": factor_risks,
            "total_factor_risk": round(total_factor_risk, 2),
            "dominant_factor": dominant_factor,
            "diversification_score": 75.0,  # 分散化评分
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_industry_risk(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        行业风险归因分析

        Args:
            holdings: 持仓列表

        Returns:
            行业风险归因结果
        """
        # TODO: 接入真实行业数据
        industry_concentrations = {
            "科技": {"weight": 0.30, "volatility": 25.0, "risk": 7.5},
            "消费": {"weight": 0.25, "volatility": 18.0, "risk": 4.5},
            "金融": {"weight": 0.20, "volatility": 15.0, "risk": 3.0},
            "医药": {"weight": 0.15, "volatility": 22.0, "risk": 3.3},
            "其他": {"weight": 0.10, "volatility": 12.0, "risk": 1.2}
        }

        # 计算集中度风险
        hhi = sum(
            (data["weight"] ** 2) for data in industry_concentrations.values()
        )

        # 评估集中度
        if hhi > 0.25:
            concentration_level = "高"
        elif hhi > 0.15:
            concentration_level = "中"
        else:
            concentration_level = "低"

        # 计算总行业风险
        total_industry_risk = sum(
            data["risk"] for data in industry_concentrations.values()
        )

        return {
            "industry_concentrations": industry_concentrations,
            "hhi_index": round(hhi, 3),
            "concentration_level": concentration_level,
            "total_industry_risk": round(total_industry_risk, 2),
            "risk_percentage": 40.0,
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_stock_risk(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        个股风险归因分析

        Args:
            holdings: 持仓列表

        Returns:
            个股风险归因结果
        """
        # TODO: 接入真实个股数据
        # 识别高风险股票
        high_risk_stocks = [
            {"code": "000001", "name": "平安银行", "weight": 0.15, "volatility": 28.0, "risk": 4.2},
            {"code": "000002", "name": "万科A", "weight": 0.12, "volatility": 32.0, "risk": 3.8},
            {"code": "000063", "name": "中兴通讯", "weight": 0.10, "volatility": 35.0, "risk": 3.5}
        ]

        # 计算最大持仓风险
        max_position_risk = max(stock["risk"] for stock in high_risk_stocks)

        # 计算个股风险贡献
        total_stock_risk = sum(stock["risk"] for stock in high_risk_stocks)

        return {
            "high_risk_stocks": high_risk_stocks,
            "max_position_risk": round(max_position_risk, 2),
            "total_stock_risk": round(total_stock_risk, 2),
            "risk_percentage": 35.0,
            "description": f"个股特质风险占比35%，需关注{len(high_risk_stocks)}只高风险股票",
            "update_time": datetime.now().isoformat()
        }

    async def _analyze_liquidity_risk(
        self,
        holdings: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[str, Any]:
        """
        流动性风险归因分析

        Args:
            holdings: 持仓列表
            total_value: 总市值

        Returns:
            流动性风险归因结果
        """
        # TODO: 接入真实流动性数据
        # 评估流动性风险
        liquidity_risks = {
            "高流动性": {"weight": 0.60, "days_to_liquidate": 1},
            "中流动性": {"weight": 0.30, "days_to_liquidate": 3},
            "低流动性": {"weight": 0.10, "days_to_liquidate": 10}
        }

        # 计算平均变现天数
        avg_days = sum(
            data["weight"] * data["days_to_liquidate"]
            for data in liquidity_risks.values()
        )

        # 评估流动性风险等级
        if avg_days <= 2:
            liquidity_level = "低"
        elif avg_days <= 5:
            liquidity_level = "中"
        else:
            liquidity_level = "高"

        return {
            "liquidity_risks": liquidity_risks,
            "avg_days_to_liquidate": round(avg_days, 1),
            "liquidity_level": liquidity_level,
            "risk_percentage": 10.0,
            "update_time": datetime.now().isoformat()
        }

    # ========== 风险管理建议 ==========

    def _generate_risk_management(
        self,
        market_risk: Dict[str, Any],
        factor_risk: Dict[str, Any],
        industry_risk: Dict[str, Any],
        stock_risk: Dict[str, Any],
        liquidity_risk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成风险管理建议

        Args:
            market_risk: 市场风险
            factor_risk: 因子风险
            industry_risk: 行业风险
            stock_risk: 个股风险
            liquidity_risk: 流动性风险

        Returns:
            风险管理建议
        """
        recommendations = []

        # 市场风险管理
        if market_risk["portfolio_beta"] > 1.2:
            recommendations.append({
                "type": "市场风险",
                "priority": "高",
                "action": "降低Beta",
                "description": f"组合Beta {market_risk['portfolio_beta']:.2f}偏高，建议降低高Beta股票配置"
            })

        # 行业风险管理
        if industry_risk["hhi_index"] > 0.25:
            recommendations.append({
                "type": "行业风险",
                "priority": "高",
                "action": "分散行业配置",
                "description": f"行业集中度HHI {industry_risk['hhi_index']:.3f}过高，建议增加行业分散度"
            })

        # 个股风险管理
        if stock_risk["max_position_risk"] > 4.0:
            recommendations.append({
                "type": "个股风险",
                "priority": "中",
                "action": "降低单股仓位",
                "description": "部分个股风险贡献过大，建议降低单股仓位至10%以下"
            })

        # 流动性风险管理
        if liquidity_risk["avg_days_to_liquidate"] > 5:
            recommendations.append({
                "type": "流动性风险",
                "priority": "中",
                "action": "提高流动性",
                "description": "平均变现天数较长，建议增加高流动性资产配置"
            })

        # 因子风险管理
        dominant_factor = factor_risk["dominant_factor"]
        if factor_risk["factor_risks"][dominant_factor]["percentage"] > 50:
            recommendations.append({
                "type": "因子风险",
                "priority": "低",
                "action": "平衡因子暴露",
                "description": f"{dominant_factor}风险占比较高，建议平衡因子暴露"
            })

        return {
            "recommendations": recommendations,
            "total_risk_score": 65.0,
            "risk_level": "中等",
            "update_time": datetime.now().isoformat()
        }

    # ========== 辅助方法 ==========

    def _calculate_portfolio_beta(self, holdings: List[Dict[str, Any]]) -> float:
        """计算组合Beta"""
        # TODO: 实现真实计算
        return 1.1

"""
配置优化AI - Configuration Optimization AI

优化部成员 (2/3)

职责：
1. 资产配置优化 - 组合优化
2. 机会筛选 - 投资机会识别

合并来源：
- 资产配置AI
- 机会筛选AI

使用工具：
- FinancialTool（财务数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class ConfigurationOptimizationAI(BusinessAgent):
    """
    配置优化AI - 优化部成员 (2/3)

    核心能力:
    1. 资产配置优化 - 投资组合优化配置
    2. 机会筛选 - 识别优质投资机会

    使用工具:
    - FinancialTool (财务数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="配置优化AI",
            role="资产配置与机会筛选",
            corps="optimization",
            analysis_type="configuration_optimization",
            capabilities=[
                AgentCapability(
                    name="portfolio_optimization",
                    description="投资组合优化",
                    input_type="portfolio",
                    output_type="optimized_allocation"
                ),
                AgentCapability(
                    name="opportunity_screening",
                    description="投资机会筛选",
                    input_type="market_universe",
                    output_type="opportunity_list"
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

        # 默认配置参数
        self.optimization_params = {
            "risk_tolerance": 0.5,  # 风险容忍度 0-1
            "return_target": 0.15,  # 目标收益率 15%
            "max_position": 0.3,  # 单个资产最大仓位 30%
            "min_position": 0.05,  # 单个资产最小仓位 5%
            "diversification_threshold": 0.6  # 分散化阈值
        }

        self.logger.info("配置优化AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行配置优化分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - portfolio: 当前投资组合（用于配置优化）
                - market_universe: 市场股票池（用于机会筛选）
                - optimization_params: 优化参数（可选）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取优化参数
        opt_params = kwargs.get("optimization_params", {})
        if opt_params:
            self.optimization_params.update(opt_params)

        self.logger.info(
            f"开始配置优化分析",
            extra={
                "stock_code": stock_code,
                "risk_tolerance": self.optimization_params["risk_tolerance"],
                "return_target": self.optimization_params["return_target"]
            }
        )

        # ========== 1. 资产配置优化 ==========
        portfolio_optimization = await self._optimize_portfolio(stock_code, **kwargs)

        # ========== 2. 机会筛选 ==========
        opportunity_screening = await self._screen_opportunities(stock_code, **kwargs)

        # ========== 3. 风险评估 ==========
        risk_assessment = self._assess_risk(
            portfolio_optimization,
            opportunity_screening
        )

        # ========== 4. 生成配置建议 ==========
        allocation_recommendations = self._generate_allocation_recommendations(
            portfolio_optimization,
            opportunity_screening,
            risk_assessment
        )

        # ========== 5. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,

            # 配置优化
            "portfolio_optimization": portfolio_optimization,

            # 机会筛选
            "opportunity_screening": opportunity_screening,

            # 风险评估
            "risk_assessment": risk_assessment,

            # 配置建议
            "allocation_recommendations": allocation_recommendations,

            # 优化参数
            "optimization_params": self.optimization_params,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                portfolio_optimization,
                opportunity_screening
            ),
            confidence=self._calculate_confidence(
                portfolio_optimization,
                opportunity_screening
            ),
            details=details,
            risks=risk_assessment.get("risks", []),
            recommendations=allocation_recommendations.get("recommendations", [])
        )

        self.logger.info(
            f"配置优化分析完成",
            extra={
                "stock_code": stock_code,
                "opportunities_found": len(opportunity_screening["top_opportunities"]),
                "expected_return": portfolio_optimization.get("expected_return", 0)
            }
        )

        return result

    # ========== 资产配置优化 ==========

    async def _optimize_portfolio(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        资产配置优化（投资组合优化）

        Args:
            stock_code: 股票代码
            **kwargs: 当前投资组合

        Returns:
            优化后的配置方案
        """
        # TODO: 接入真实投资组合数据
        current_portfolio = kwargs.get("portfolio", {})

        # 获取当前配置
        current_allocation = current_portfolio.get("allocation", {})

        # 计算最优配置
        optimal_allocation = self._calculate_optimal_allocation(
            stock_code,
            current_allocation
        )

        # 计算预期收益和风险
        expected_return = self._calculate_expected_return(optimal_allocation)
        expected_risk = self._calculate_expected_risk(optimal_allocation)

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_risk)

        # 对比优化效果
        comparison = self._compare_with_current(
            current_allocation,
            optimal_allocation
        )

        return {
            "current_allocation": current_allocation,
            "optimal_allocation": optimal_allocation,
            "expected_return": expected_return,
            "expected_risk": expected_risk,
            "sharpe_ratio": sharpe_ratio,
            "optimization_comparison": comparison,
            "allocation_adjustments": self._generate_allocation_adjustments(
                current_allocation,
                optimal_allocation
            )
        }

    def _calculate_optimal_allocation(
        self,
        stock_code: str,
        current_allocation: Dict[str, float]
    ) -> Dict[str, float]:
        """计算最优配置"""
        # TODO: 实现真实的均值-方差优化
        # 简化版本：基于风险平价

        # 模拟最优配置
        optimal_allocation = {
            "stock_code": 0.25,  # 目标股票 25%
            "cash": 0.15,  # 现金 15%
            "bonds": 0.20,  # 债券 20%
            "equity_funds": 0.30,  # 股票基金 30%
            "other": 0.10  # 其他 10%
        }

        # 验证总和为1
        total = sum(optimal_allocation.values())
        if abs(total - 1.0) > 0.01:
            # 归一化
            optimal_allocation = {
                k: round(v / total, 3)
                for k, v in optimal_allocation.items()
            }

        return optimal_allocation

    def _calculate_expected_return(
        self,
        allocation: Dict[str, float]
    ) -> float:
        """计算预期收益率"""
        # TODO: 基于历史数据计算真实预期收益
        # 简化版本：各资产预期收益加权平均

        asset_returns = {
            "stock_code": 0.20,  # 20%
            "cash": 0.03,  # 3%
            "bonds": 0.05,  # 5%
            "equity_funds": 0.12,  # 12%
            "other": 0.08  # 8%
        }

        expected_return = sum(
            allocation.get(asset, 0) * asset_returns.get(asset, 0.10)
            for asset in allocation
        )

        return round(expected_return, 3)

    def _calculate_expected_risk(
        self,
        allocation: Dict[str, float]
    ) -> float:
        """计算预期风险（标准差）"""
        # TODO: 基于历史数据计算真实风险
        # 简化版本：各资产风险加权平均

        asset_risks = {
            "stock_code": 0.25,  # 25%
            "cash": 0.01,  # 1%
            "bonds": 0.08,  # 8%
            "equity_funds": 0.18,  # 18%
            "other": 0.12  # 12%
        }

        expected_risk = sum(
            allocation.get(asset, 0) * asset_risks.get(asset, 0.15)
            for asset in allocation
        )

        return round(expected_risk, 3)

    def _calculate_sharpe_ratio(
        self,
        expected_return: float,
        expected_risk: float
    ) -> float:
        """计算夏普比率"""
        # 假设无风险利率为3%
        risk_free_rate = 0.03

        if expected_risk == 0:
            return 0.0

        sharpe = (expected_return - risk_free_rate) / expected_risk
        return round(sharpe, 2)

    def _compare_with_current(
        self,
        current: Dict[str, float],
        optimal: Dict[str, float]
    ) -> Dict[str, Any]:
        """对比优化效果"""
        # 当前配置的预期收益和风险
        current_return = self._calculate_expected_return(current)
        current_risk = self._calculate_expected_risk(current)
        current_sharpe = self._calculate_sharpe_ratio(current_return, current_risk)

        # 最优配置的预期收益和风险
        optimal_return = self._calculate_expected_return(optimal)
        optimal_risk = self._calculate_expected_risk(optimal)
        optimal_sharpe = self._calculate_sharpe_ratio(optimal_return, optimal_risk)

        return {
            "return_improvement": round((optimal_return - current_return) * 100, 2),
            "risk_reduction": round((current_risk - optimal_risk) * 100, 2),
            "sharpe_improvement": round(optimal_sharpe - current_sharpe, 2),
            "current_return": current_return,
            "optimal_return": optimal_return,
            "current_risk": current_risk,
            "optimal_risk": optimal_risk
        }

    def _generate_allocation_adjustments(
        self,
        current: Dict[str, float],
        optimal: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """生成配置调整建议"""
        adjustments = []

        for asset in set(list(current.keys()) + list(optimal.keys())):
            current_weight = current.get(asset, 0)
            optimal_weight = optimal.get(asset, 0)

            diff = optimal_weight - current_weight

            if abs(diff) > 0.05:  # 差异超过5%才调整
                action = "增持" if diff > 0 else "减持"
                adjustments.append({
                    "asset": asset,
                    "action": action,
                    "current_weight": round(current_weight * 100, 1),
                    "optimal_weight": round(optimal_weight * 100, 1),
                    "adjustment": round(diff * 100, 1)
                })

        # 按调整幅度排序
        adjustments.sort(key=lambda x: abs(x["adjustment"]), reverse=True)

        return adjustments

    # ========== 机会筛选 ==========

    async def _screen_opportunities(
        self,
        stock_code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        机会筛选（投资机会识别）

        Args:
            stock_code: 股票代码
            **kwargs: 市场股票池

        Returns:
            筛选后的投资机会
        """
        # TODO: 接入真实市场数据
        market_universe = kwargs.get("market_universe", [])

        # 多维度筛选
        valuation_screen = await self._screen_by_valuation(market_universe)
        growth_screen = await self._screen_by_growth(market_universe)
        quality_screen = await self._screen_by_quality(market_universe)
        momentum_screen = await self._screen_by_momentum(market_universe)

        # 综合评分
        top_opportunities = self._rank_opportunities(
            valuation_screen,
            growth_screen,
            quality_screen,
            momentum_screen
        )

        # 目标股票评分
        target_stock_score = self._score_target_stock(
            stock_code,
            valuation_screen,
            growth_screen,
            quality_screen
        )

        return {
            "valuation_screen": valuation_screen,
            "growth_screen": growth_screen,
            "quality_screen": quality_screen,
            "momentum_screen": momentum_screen,
            "top_opportunities": top_opportunities[:5],  # 前5个机会
            "target_stock_score": target_stock_score,
            "screening_criteria": self._get_screening_criteria()
        }

    async def _screen_by_valuation(
        self,
        market_universe: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """估值筛选"""
        # TODO: 接入真实估值数据
        # 模拟低估值股票
        return [
            {"stock": "600519", "name": "贵州茅台", "pe": 25.5, "score": 85},
            {"stock": "000858", "name": "五粮液", "pe": 22.3, "score": 82},
            {"stock": "600036", "name": "招商银行", "pb": 0.9, "score": 88}
        ]

    async def _screen_by_growth(
        self,
        market_universe: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """成长性筛选"""
        # TODO: 接入真实增长数据
        # 模拟高增长股票
        return [
            {"stock": "300750", "name": "宁德时代", "growth_rate": 45.2, "score": 90},
            {"stock": "688981", "name": "中芯国际", "growth_rate": 38.5, "score": 85},
            {"stock": "002594", "name": "比亚迪", "growth_rate": 32.1, "score": 82}
        ]

    async def _screen_by_quality(
        self,
        market_universe: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """质量筛选"""
        # TODO: 接入真实质量数据
        # 模拟高质量股票
        return [
            {"stock": "600519", "name": "贵州茅台", "roe": 25.3, "score": 95},
            {"stock": "000333", "name": "美的集团", "roe": 22.1, "score": 90},
            {"stock": "600036", "name": "招商银行", "roe": 16.8, "score": 85}
        ]

    async def _screen_by_momentum(
        self,
        market_universe: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """动量筛选"""
        # TODO: 接入真实动量数据
        # 模拟强势股票
        return [
            {"stock": "600519", "name": "贵州茅台", "momentum_3m": 15.2, "score": 88},
            {"stock": "300750", "name": "宁德时代", "momentum_3m": 22.5, "score": 92},
            {"stock": "002594", "name": "比亚迪", "momentum_3m": 18.3, "score": 85}
        ]

    def _rank_opportunities(
        self,
        valuation: List[Dict[str, Any]],
        growth: List[Dict[str, Any]],
        quality: List[Dict[str, Any]],
        momentum: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """综合评分排名"""
        # TODO: 实现真实的综合评分算法
        # 简化版本：模拟排名

        opportunities = [
            {
                "stock": "600519",
                "name": "贵州茅台",
                "overall_score": 92,
                "valuation_score": 85,
                "growth_score": 78,
                "quality_score": 95,
                "momentum_score": 88,
                "rating": "强烈推荐"
            },
            {
                "stock": "300750",
                "name": "宁德时代",
                "overall_score": 89,
                "valuation_score": 75,
                "growth_score": 90,
                "quality_score": 88,
                "momentum_score": 92,
                "rating": "强烈推荐"
            },
            {
                "stock": "600036",
                "name": "招商银行",
                "overall_score": 86,
                "valuation_score": 88,
                "growth_score": 75,
                "quality_score": 85,
                "momentum_score": 78,
                "rating": "推荐"
            }
        ]

        return opportunities

    def _score_target_stock(
        self,
        stock_code: str,
        valuation: List[Dict[str, Any]],
        growth: List[Dict[str, Any]],
        quality: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """为目标股票评分"""
        # TODO: 接入真实数据
        # 模拟目标股票评分
        return {
            "stock": stock_code,
            "overall_score": 84,
            "valuation_score": 80,
            "growth_score": 82,
            "quality_score": 85,
            "momentum_score": 79,
            "rating": "推荐",
            "ranking": 5  # 在市场中的排名
        }

    def _get_screening_criteria(self) -> Dict[str, Any]:
        """获取筛选标准"""
        return {
            "valuation": {
                "pe_range": [10, 30],
                "pb_range": [0.8, 3.0],
                "description": "估值合理"
            },
            "growth": {
                "min_growth_rate": 15.0,
                "description": "增长率>15%"
            },
            "quality": {
                "min_roe": 12.0,
                "description": "ROE>12%"
            },
            "momentum": {
                "min_3m_return": 10.0,
                "description": "3月涨幅>10%"
            }
        }

    # ========== 辅助方法 ==========

    def _assess_risk(
        self,
        portfolio_opt: Dict[str, Any],
        opportunity_screen: Dict[str, Any]
    ) -> Dict[str, Any]:
        """风险评估"""
        risks = []

        # 配置风险
        expected_risk = portfolio_opt.get("expected_risk", 0)
        if expected_risk > 0.20:
            risks.append(f"组合风险较高（{expected_risk*100:.1f}%），建议降低仓位")

        # 集中度风险
        optimal_alloc = portfolio_opt.get("optimal_allocation", {})
        max_weight = max(optimal_alloc.values()) if optimal_alloc else 0
        if max_weight > 0.35:
            risks.append(f"单一资产权重过高（{max_weight*100:.1f}%），建议分散投资")

        # 市场风险
        top_opportunities = opportunity_screen.get("top_opportunities", [])
        if len(top_opportunities) < 3:
            risks.append("市场投资机会较少，建议谨慎配置")

        return {
            "risks": risks,
            "expected_risk": expected_risk,
            "risk_level": self._assess_risk_level(expected_risk)
        }

    def _assess_risk_level(self, risk: float) -> str:
        """评估风险等级"""
        if risk < 0.10:
            return "低风险"
        elif risk < 0.15:
            return "中等风险"
        elif risk < 0.20:
            return "中高风险"
        else:
            return "高风险"

    def _generate_allocation_recommendations(
        self,
        portfolio_opt: Dict[str, Any],
        opportunity_screen: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成配置建议"""
        recommendations = []

        # 基于优化效果的建议
        comparison = portfolio_opt.get("optimization_comparison", {})
        if comparison.get("return_improvement", 0) > 2:
            recommendations.append(
                f"优化后预期收益提升{comparison['return_improvement']:.1f}%，建议采用新配置"
            )

        # 基于机会的建议
        target_score = opportunity_screen.get("target_stock_score", {})
        if target_score.get("overall_score", 0) >= 85:
            recommendations.append(f"目标股票评分{target_score['overall_score']}分，建议增加配置")

        # 基于风险的建议
        risk_level = risk_assessment.get("risk_level", "")
        if "高" in risk_level:
            recommendations.append(f"当前组合{risk_level}，建议适当降低风险资产配置")

        return {
            "recommendations": recommendations,
            "target_allocation": portfolio_opt.get("optimal_allocation", {}),
            "adjustments_needed": portfolio_opt.get("allocation_adjustments", [])
        }

    def _calculate_confidence(
        self,
        portfolio_opt: Dict[str, Any],
        opportunity_screen: Dict[str, Any]
    ) -> float:
        """计算综合置信度"""
        # 夏普比率权重
        sharpe = portfolio_opt.get("sharpe_ratio", 0)
        sharpe_score = min(1.0, sharpe / 2.0)  # 归一化到0-1

        # 机会数量权重
        opp_count = len(opportunity_screen.get("top_opportunities", []))
        opp_score = min(1.0, opp_count / 10.0)

        # 综合置信度
        confidence = sharpe_score * 0.6 + opp_score * 0.4

        return round(confidence, 2)

    def _generate_conclusion(
        self,
        portfolio_opt: Dict[str, Any],
        opportunity_screen: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        expected_return = portfolio_opt.get("expected_return", 0)
        expected_risk = portfolio_opt.get("expected_risk", 0)
        sharpe = portfolio_opt.get("sharpe_ratio", 0)
        opp_count = len(opportunity_screen.get("top_opportunities", []))

        return (
            f"预期收益{expected_return*100:.1f}%，"
            f"预期风险{expected_risk*100:.1f}%，"
            f"夏普比率{sharpe:.2f}，"
            f"发现{opp_count}个优质机会"
        )


# 便捷函数
async def analyze_configuration_optimization(
    stock_code: str,
    portfolio: Optional[Dict[str, Any]] = None,
    market_universe: Optional[List[Dict[str, Any]]] = None,
    optimization_params: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    配置优化分析（便捷函数）

    Args:
        stock_code: 股票代码
        portfolio: 当前投资组合
        market_universe: 市场股票池
        optimization_params: 优化参数

    Returns:
        分析结果
    """
    ai = ConfigurationOptimizationAI()
    return await ai.analyze(
        stock_code,
        portfolio=portfolio,
        market_universe=market_universe,
        optimization_params=optimization_params
    )

"""
风险控制AI - Risk Control AI

⚠️ DEPRECATED: 此Agent已废弃,请使用RiskAndTimingAI代替
迁移指南: docs/MIGRATION_GUIDE_RISK_TIMING.md
废弃日期: 2026-03-14
计划移除日期: 2026-04-14

职责：
- 评估投资风险
- 设置风险控制策略
- 监控风险指标

输入：
- 股票代码
- 投资金额
- 风险偏好

输出：
- 风险评估报告
- 风险控制策略
- 风险监控指标
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import warnings

# 显示废弃警告
warnings.warn(
    "RiskControlAI已废弃,请使用RiskAndTimingAI代替。"
    "迁移指南: docs/MIGRATION_GUIDE_RISK_TIMING.md"
    "废弃日期: 2026-03-14, 计划移除日期: 2026-04-14",
    DeprecationWarning,
    stacklevel=2
)

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class RiskControlAI(BaseAgent, LoggerMixin):
    """风险控制AI - 评估和控制投资风险"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="风险控制AI",
            role="评估投资风险，设置风险控制策略，监控风险指标",
            capabilities=[
                AgentCapability(
                    name="risk_assessment",
                    description="评估投资风险",
                    input_type="stock_code",
                    output_type="risk_report"
                ),
                AgentCapability(
                    name="strategy_setting",
                    description="设置风险策略",
                    input_type="risk_preference",
                    output_type="risk_strategy"
                ),
                AgentCapability(
                    name="risk_monitoring",
                    description="监控风险指标",
                    input_type="position_data",
                    output_type="monitoring_report"
                )
            ],
            tools=[
                AgentTool(
                    name="risk_calculator",
                    description="风险计算工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("风险控制AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "assess_risk":
            return await self.assess_risk(
                kwargs.get("stock_code"),
                kwargs.get("investment_amount", 100000)
            )
        elif task == "set_strategy":
            return await self.set_strategy(
                kwargs.get("risk_preference", "moderate"),
                kwargs.get("investment_amount", 100000)
            )
        elif task == "monitor_risk":
            return await self.monitor_risk(
                kwargs.get("positions", [])
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def assess_risk(
        self,
        stock_code: str,
        investment_amount: float = 100000
    ) -> Dict[str, Any]:
        """评估投资风险"""
        self.logger.info(
            f"开始评估投资风险",
            extra={"stock_code": stock_code, "amount": investment_amount}
        )

        # 1. 获取风险指标
        risk_indicators = await self._fetch_risk_indicators(stock_code)

        # 2. 计算风险评分
        risk_score = self._calculate_risk_score(risk_indicators)

        # 3. 评估风险等级
        risk_level = self._assess_risk_level(risk_score)

        # 4. 生成风险报告
        report = {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "investment_amount": investment_amount,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_indicators": risk_indicators,
            "max_loss_estimate": self._estimate_max_loss(investment_amount, risk_score),
            "summary": self._generate_risk_summary(risk_level, risk_score),
            "suggestion": self._generate_risk_suggestion(risk_level)
        }

        self.logger.info(
            f"投资风险评估完成",
            extra={"stock_code": stock_code, "risk_level": risk_level}
        )

        return report

    async def set_strategy(
        self,
        risk_preference: str = "moderate",
        investment_amount: float = 100000
    ) -> Dict[str, Any]:
        """设置风险控制策略"""
        self.logger.info(
            f"设置风险控制策略",
            extra={"preference": risk_preference, "amount": investment_amount}
        )

        # 根据风险偏好设置策略
        strategy = self._get_risk_strategy(risk_preference, investment_amount)

        return {
            "timestamp": datetime.now().isoformat(),
            "risk_preference": risk_preference,
            "investment_amount": investment_amount,
            "strategy": strategy,
            "risk_limits": self._set_risk_limits(risk_preference, investment_amount),
            "summary": f"风险偏好：{risk_preference}，已设置相应风险控制策略"
        }

    async def monitor_risk(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """监控风险指标"""
        self.logger.info(f"监控风险指标", extra={"position_count": len(positions)})

        # 如果没有持仓数据，生成模拟数据
        if not positions:
            positions = await self._generate_sample_positions()

        # 计算组合风险
        portfolio_risk = self._calculate_portfolio_risk(positions)

        # 检查风险预警
        warnings = self._check_risk_warnings(positions, portfolio_risk)

        return {
            "timestamp": datetime.now().isoformat(),
            "position_count": len(positions),
            "portfolio_risk": portfolio_risk,
            "positions": positions,
            "warnings": warnings,
            "summary": self._generate_monitoring_summary(portfolio_risk, warnings)
        }

    # ========== 辅助方法 ==========

    async def _fetch_risk_indicators(self, stock_code: str) -> Dict[str, Any]:
        """获取风险指标（模拟）"""
        import random

        return {
            "波动率": round(random.uniform(15, 45), 2),
            "Beta系数": round(random.uniform(0.5, 1.8), 2),
            "最大回撤": round(random.uniform(10, 40), 2),
            "夏普比率": round(random.uniform(0.5, 2.5), 2),
            "流动性风险": round(random.uniform(1, 10), 2),
            "集中度风险": round(random.uniform(1, 10), 2)
        }

    def _calculate_risk_score(self, indicators: Dict[str, Any]) -> float:
        """计算风险评分（0-100）"""
        # 波动率评分（权重30%）
        volatility = indicators["波动率"]
        if volatility > 35:
            volatility_score = 90
        elif volatility > 25:
            volatility_score = 70
        elif volatility > 18:
            volatility_score = 50
        else:
            volatility_score = 30

        # Beta评分（权重25%）
        beta = indicators["Beta系数"]
        if beta > 1.5:
            beta_score = 90
        elif beta > 1.2:
            beta_score = 70
        elif beta > 0.8:
            beta_score = 50
        else:
            beta_score = 30

        # 最大回撤评分（权重25%）
        max_drawdown = indicators["最大回撤"]
        if max_drawdown > 30:
            drawdown_score = 90
        elif max_drawdown > 20:
            drawdown_score = 70
        elif max_drawdown > 15:
            drawdown_score = 50
        else:
            drawdown_score = 30

        # 流动性和集中度（权重20%）
        liquidity_risk = indicators["流动性风险"]
        concentration_risk = indicators["集中度风险"]
        other_score = (liquidity_risk + concentration_risk) * 5

        # 综合评分
        risk_score = (
            volatility_score * 0.30 +
            beta_score * 0.25 +
            drawdown_score * 0.25 +
            other_score * 0.20
        )

        return round(risk_score, 2)

    def _assess_risk_level(self, risk_score: float) -> str:
        """评估风险等级"""
        if risk_score >= 80:
            return "极高风险"
        elif risk_score >= 65:
            return "高风险"
        elif risk_score >= 50:
            return "中风险"
        elif risk_score >= 35:
            return "低风险"
        else:
            return "极低风险"

    def _estimate_max_loss(self, amount: float, risk_score: float) -> Dict[str, float]:
        """估算最大损失"""
        # 根据风险评分估算最大可能损失
        loss_rate = risk_score / 100 * 0.5  # 最高50%损失

        return {
            "estimated_max_loss_rate": round(loss_rate * 100, 2),
            "estimated_max_loss_amount": round(amount * loss_rate, 2)
        }

    def _get_risk_strategy(
        self,
        preference: str,
        amount: float
    ) -> Dict[str, Any]:
        """获取风险策略"""
        strategies = {
            "conservative": {
                "name": "保守型策略",
                "单只股票最大仓位": "20%",
                "止损线": "-5%",
                "止盈线": "+10%",
                "总仓位上限": "60%",
                "description": "严格控制风险，追求稳定收益"
            },
            "moderate": {
                "name": "稳健型策略",
                "单只股票最大仓位": "30%",
                "止损线": "-8%",
                "止盈线": "+15%",
                "总仓位上限": "75%",
                "description": "平衡风险与收益，适度进取"
            },
            "aggressive": {
                "name": "激进型策略",
                "单只股票最大仓位": "40%",
                "止损线": "-12%",
                "止盈线": "+25%",
                "总仓位上限": "90%",
                "description": "追求高收益，承受较高风险"
            }
        }

        return strategies.get(preference, strategies["moderate"])

    def _set_risk_limits(
        self,
        preference: str,
        amount: float
    ) -> Dict[str, float]:
        """设置风险限制"""
        limits = {
            "conservative": {
                "单只最大金额": amount * 0.20,
                "止损金额": amount * 0.05,
                "日亏损上限": amount * 0.02
            },
            "moderate": {
                "单只最大金额": amount * 0.30,
                "止损金额": amount * 0.08,
                "日亏损上限": amount * 0.03
            },
            "aggressive": {
                "单只最大金额": amount * 0.40,
                "止损金额": amount * 0.12,
                "日亏损上限": amount * 0.05
            }
        }

        return limits.get(preference, limits["moderate"])

    async def _generate_sample_positions(self) -> List[Dict[str, Any]]:
        """生成示例持仓数据"""
        import random

        return [
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "position": 200,
                "cost_price": 1800.0,
                "current_price": 1850.0,
                "market_value": 370000.0,
                "profit_loss": 10000.0,
                "profit_loss_rate": 2.78
            },
            {
                "stock_code": "000858",
                "stock_name": "五粮液",
                "position": 300,
                "cost_price": 160.0,
                "current_price": 155.0,
                "market_value": 46500.0,
                "profit_loss": -1500.0,
                "profit_loss_rate": -3.13
            }
        ]

    def _calculate_portfolio_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算组合风险"""
        if not positions:
            return {"risk_level": "无持仓", "total_value": 0}

        total_value = sum(p["market_value"] for p in positions)
        total_profit = sum(p["profit_loss"] for p in positions)

        # 计算集中度风险
        max_position_value = max(p["market_value"] for p in positions)
        concentration = (max_position_value / total_value) * 100 if total_value > 0 else 0

        # 评估风险等级
        if concentration > 60:
            risk_level = "高集中度风险"
        elif concentration > 40:
            risk_level = "中集中度风险"
        else:
            risk_level = "低集中度风险"

        return {
            "risk_level": risk_level,
            "total_value": round(total_value, 2),
            "total_profit": round(total_profit, 2),
            "concentration": round(concentration, 2),
            "position_count": len(positions)
        }

    def _check_risk_warnings(
        self,
        positions: List[Dict[str, Any]],
        portfolio_risk: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检查风险预警"""
        warnings = []

        # 检查集中度
        if portfolio_risk["concentration"] > 60:
            warnings.append({
                "type": "集中度预警",
                "severity": "高",
                "message": f"单一持仓占比{portfolio_risk['concentration']:.1f}%，建议分散投资"
            })

        # 检查亏损
        for pos in positions:
            if pos["profit_loss_rate"] < -8:
                warnings.append({
                    "type": "亏损预警",
                    "severity": "高",
                    "message": f"{pos['stock_code']}亏损{abs(pos['profit_loss_rate']):.1f}%，建议止损"
                })

        return warnings

    def _generate_risk_summary(self, risk_level: str, risk_score: float) -> str:
        """生成风险摘要"""
        return f"投资风险等级：{risk_level}（风险评分{risk_score:.1f}分）"

    def _generate_risk_suggestion(self, risk_level: str) -> str:
        """生成风险建议"""
        suggestions = {
            "极高风险": "风险极高，建议谨慎投资或规避",
            "高风险": "风险较高，建议轻仓参与，严格止损",
            "中风险": "风险适中，可适度参与，注意风险控制",
            "低风险": "风险较低，可以正常投资",
            "极低风险": "风险极低，适合稳健投资"
        }
        return suggestions.get(risk_level, "未知风险等级")

    def _generate_monitoring_summary(
        self,
        portfolio_risk: Dict[str, Any],
        warnings: List[Dict[str, Any]]
    ) -> str:
        """生成监控摘要"""
        summary = f"组合风险：{portfolio_risk['risk_level']}，"
        summary += f"总市值{portfolio_risk['total_value']:.0f}元，"

        if warnings:
            summary += f"发现{len(warnings)}个风险预警"
        else:
            summary += "暂无风险预警"

        return summary

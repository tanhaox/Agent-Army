"""
风险与时机AI - Risk and Timing AI

整合功能:
1. 风险评估 (原RiskControlAI)
2. 买入时机评估 (原BuyTimingAI)
3. 综合投资建议 (结合风险和时机)

使用工具:
- FinancialTool (财务数据)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class RiskAndTimingAI(BaseAgent, LoggerMixin):
    """
    风险与时机AI - 策略执行军团核心成员

    整合功能:
    1. 风险评估 (风险评分、风险等级、最大损失估算)
    2. 买入时机评估 (时机评分、时机等级)
    3. 综合投资建议 (结合风险和时机)

    使用工具:
    - FinancialTool (财务数据)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.financial_tool = FinancialTool()

        super().__init__(
            name="风险与时机AI",
            role="评估投资风险和买入时机，提供综合投资建议",
            capabilities=[
                AgentCapability(
                    name="risk_assessment",
                    description="风险评估",
                    input_type="stock_code",
                    output_type="risk_report"
                ),
                AgentCapability(
                    name="timing_evaluation",
                    description="时机评估",
                    input_type="stock_code",
                    output_type="timing_report"
                ),
                AgentCapability(
                    name="comprehensive_recommendation",
                    description="综合建议",
                    input_type="stock_code",
                    output_type="recommendation"
                )
            ],
            tools=[
                AgentTool(
                    name="risk_calculator",
                    description="风险计算工具",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="timing_analyzer",
                    description="时机分析工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("风险与时机AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(
                kwargs.get("stock_code"),
                **kwargs
            )
        elif task == "assess_risk":
            return await self._assess_risk(
                kwargs.get("stock_code"),
                kwargs.get("investment_amount", 100000)
            )
        elif task == "evaluate_timing":
            return await self._evaluate_timing(
                kwargs.get("stock_code")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: str,
        investment_amount: float = 100000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        综合分析 (风险 + 时机)

        Args:
            stock_code: 股票代码
            investment_amount: 投资金额

        Returns:
            综合分析报告
        """
        self.logger.info(
            f"开始综合分析",
            extra={"stock_code": stock_code, "amount": investment_amount}
        )

        # ========== 1. 并行获取数据 ==========
        financial_data, risk_indicators = await asyncio.gather(
            self.financial_tool.fetch_financial_data(stock_code, years=1),
            self._fetch_risk_indicators(stock_code)
        )

        # ========== 2. 风险评估 (原RiskControlAI) ==========
        risk = await self._assess_risk_internal(
            stock_code,
            investment_amount,
            risk_indicators
        )

        # ========== 3. 时机评估 (原BuyTimingAI) ==========
        timing = self._evaluate_timing_internal(
            stock_code,
            financial_data
        )

        # ========== 4. 综合建议 (结合风险和时机) ==========
        recommendation = self._generate_comprehensive_recommendation(
            risk,
            timing
        )

        # ========== 5. 构建返回结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": financial_data.get("stock_name", stock_code),
            "analysis_type": "risk_and_timing",
            "timestamp": datetime.now().isoformat(),
            "investment_amount": investment_amount,

            # 风险评估 (原RiskControlAI)
            "risk": risk,

            # 时机评估 (原BuyTimingAI)
            "timing": timing,

            # 综合建议
            "recommendation": recommendation,

            # 总结
            "summary": self._generate_summary(risk, timing, recommendation)
        }

        self.logger.info(
            f"综合分析完成",
            extra={
                "stock_code": stock_code,
                "risk_level": risk["risk_level"],
                "timing_level": timing["timing_level"],
                "action": recommendation["action"]
            }
        )

        return result

    # ========== 风险评估 (原RiskControlAI) ==========

    async def _assess_risk(
        self,
        stock_code: str,
        investment_amount: float = 100000
    ) -> Dict[str, Any]:
        """
        风险评估 (兼容旧API)

        Args:
            stock_code: 股票代码
            investment_amount: 投资金额

        Returns:
            风险评估报告
        """
        risk_indicators = await self._fetch_risk_indicators(stock_code)
        return await self._assess_risk_internal(
            stock_code,
            investment_amount,
            risk_indicators
        )

    async def _assess_risk_internal(
        self,
        stock_code: str,
        investment_amount: float,
        risk_indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """风险评估 (内部方法)"""
        # 1. 计算风险评分
        risk_score = self._calculate_risk_score(risk_indicators)

        # 2. 评估风险等级
        risk_level = self._assess_risk_level(risk_score)

        # 3. 估算最大损失
        max_loss = self._estimate_max_loss(investment_amount, risk_score)

        # 4. 风险建议
        risk_suggestion = self._generate_risk_suggestion(risk_level)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_indicators": risk_indicators,

            "max_loss_estimate": max_loss,

            "risk_suggestion": risk_suggestion,
            "risk_recommendation": self._generate_risk_recommendation(risk_level)
        }

    # ========== 时机评估 (原BuyTimingAI) ==========

    def _evaluate_timing(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        时机评估 (兼容旧API)

        Args:
            stock_code: 股票代码

        Returns:
            时机评估报告
        """
        # 获取财务数据 (同步调用)
        # TODO: 优化为异步
        financial_data = asyncio.run(
            self.financial_tool.fetch_financial_data(stock_code, years=1)
        )
        return self._evaluate_timing_internal(stock_code, financial_data)

    def _evaluate_timing_internal(
        self,
        stock_code: str,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """时机评估 (内部方法)"""
        latest = financial_data.get("latest", {})

        # 1. 估值评分
        valuation = self._calculate_valuation_score(latest)

        # 2. 动量评分
        momentum = self._calculate_momentum_score(latest)

        # 3. 安全评分
        safety = self._calculate_safety_score(latest)

        # 4. 总分
        total = (valuation * 0.4 + momentum * 0.3 + safety * 0.3)

        # 5. 确定等级
        timing_level = self._assess_timing_level(total)

        # 6. 风险提示
        warnings = self._generate_timing_warnings(latest)

        return {
            "timing_score": round(total, 1),
            "timing_level": timing_level,

            "scores": {
                "valuation": valuation,
                "momentum": momentum,
                "safety": safety
            },

            "warnings": warnings,

            "timing_recommendation": self._generate_timing_recommendation(total)
        }

    # ========== 综合建议生成 ==========

    def _generate_comprehensive_recommendation(
        self,
        risk: Dict[str, Any],
        timing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成综合投资建议

        使用投票机制:
        - 风险建议: 买入/持有/等待
        - 时机建议: 买入/持有/等待
        - 综合建议: 投票决定
        """
        # 风险建议
        risk_rec = risk.get("risk_recommendation", "观望")

        # 时机建议
        timing_rec = timing.get("timing_recommendation", "观望")

        # 转换为统一格式
        def normalize_recommendation(rec: str) -> str:
            if rec in ["强烈建议买入", "建议买入", "可以买入"]:
                return "BUY"
            elif rec in ["建议观望", "观望", "谨慎"]:
                return "HOLD"
            elif rec in ["建议等待", "等待", "规避风险"]:
                return "WAIT"
            else:
                return "HOLD"

        risk_action = normalize_recommendation(risk_rec)
        timing_action = normalize_recommendation(timing_rec)

        # 投票机制
        votes = {"BUY": 0, "HOLD": 0, "WAIT": 0}
        votes[risk_action] += 1
        votes[timing_action] += 1

        # 确定最终建议
        if votes["BUY"] >= 2:
            action = "BUY"
            confidence = 0.80 if votes["BUY"] == 2 else 0.90
        elif votes["WAIT"] >= 2:
            action = "WAIT"
            confidence = 0.80 if votes["WAIT"] == 2 else 0.90
        else:
            action = "HOLD"
            confidence = 0.65

        # 生成推理说明
        reasoning = self._generate_reasoning(risk, timing, action)

        # 生成策略建议
        strategy = self._generate_strategy(risk, timing, action)

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "strategy": strategy,

            "details": {
                "risk_recommendation": risk_rec,
                "risk_action": risk_action,
                "timing_recommendation": timing_rec,
                "timing_action": timing_action
            }
        }

    def _generate_reasoning(
        self,
        risk: Dict[str, Any],
        timing: Dict[str, Any],
        action: str
    ) -> str:
        """生成推理说明"""
        risk_level = risk.get("risk_level", "")
        timing_level = timing.get("timing_level", "")
        risk_score = risk.get("risk_score", 0)
        timing_score = timing.get("timing_score", 0)

        reasoning = f"风险面：{risk_level}（风险评分{risk_score:.1f}分）。"
        reasoning += f"时机面：时机评估{timing_level}（时机评分{timing_score:.1f}分）。"

        if action == "BUY":
            reasoning += "风险可控，时机良好，建议买入。"
        elif action == "WAIT":
            reasoning += "风险较高或时机不佳，建议等待。"
        else:
            reasoning += "风险和时机表现分化，建议观望。"

        return reasoning

    def _generate_strategy(
        self,
        risk: Dict[str, Any],
        timing: Dict[str, Any],
        action: str
    ) -> Dict[str, Any]:
        """生成投资策略"""
        risk_score = risk.get("risk_score", 50)
        timing_score = timing.get("timing_score", 50)

        # 根据风险和时机调整策略
        if action == "BUY":
            if timing_score >= 75:
                position_ratio = 0.30  # 积极买入
                stop_loss = -0.08
                take_profit = 0.15
            else:
                position_ratio = 0.20  # 适度买入
                stop_loss = -0.06
                take_profit = 0.12
        elif action == "WAIT":
            position_ratio = 0.05  # 观望
            stop_loss = -0.05
            take_profit = 0.08
        else:  # HOLD
            position_ratio = 0.10  # 轻仓
            stop_loss = -0.07
            take_profit = 0.10

        return {
            "position_ratio": f"{int(position_ratio * 100)}%",
            "stop_loss": f"{int(stop_loss * 100)}%",
            "take_profit": f"+{int(take_profit * 100)}%",
            "risk_control": "严格止损" if risk_score > 65 else "适度止损"
        }

    # ========== 辅助方法 ==========

    async def _fetch_risk_indicators(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """获取风险指标 (模拟)"""
        import random

        return {
            "波动率": round(random.uniform(15, 45), 2),
            "Beta系数": round(random.uniform(0.5, 1.8), 2),
            "最大回撤": round(random.uniform(10, 40), 2),
            "夏普比率": round(random.uniform(0.5, 2.5), 2),
            "流动性风险": round(random.uniform(1, 10), 2),
            "集中度风险": round(random.uniform(1, 10), 2)
        }

    def _calculate_risk_score(
        self,
        indicators: Dict[str, Any]
    ) -> float:
        """计算风险评分 (0-100)"""
        # 波动率评分 (权重30%)
        volatility = indicators["波动率"]
        if volatility > 35:
            volatility_score = 90
        elif volatility > 25:
            volatility_score = 70
        elif volatility > 18:
            volatility_score = 50
        else:
            volatility_score = 30

        # Beta评分 (权重25%)
        beta = indicators["Beta系数"]
        if beta > 1.5:
            beta_score = 90
        elif beta > 1.2:
            beta_score = 70
        elif beta > 0.8:
            beta_score = 50
        else:
            beta_score = 30

        # 最大回撤评分 (权重25%)
        max_drawdown = indicators["最大回撤"]
        if max_drawdown > 30:
            drawdown_score = 90
        elif max_drawdown > 20:
            drawdown_score = 70
        elif max_drawdown > 15:
            drawdown_score = 50
        else:
            drawdown_score = 30

        # 流动性和集中度 (权重20%)
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

    def _estimate_max_loss(
        self,
        amount: float,
        risk_score: float
    ) -> Dict[str, float]:
        """估算最大损失"""
        loss_rate = risk_score / 100 * 0.5  # 最高50%损失

        return {
            "estimated_max_loss_rate": f"{round(loss_rate * 100, 2)}%",
            "estimated_max_loss_amount": round(amount * loss_rate, 2)
        }

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

    def _generate_risk_recommendation(self, risk_level: str) -> str:
        """生成风险面建议"""
        if risk_level in ["极高风险", "高风险"]:
            return "规避风险"
        elif risk_level == "中风险":
            return "谨慎"
        else:
            return "可以买入"

    def _calculate_valuation_score(self, latest: Dict[str, Any]) -> float:
        """计算估值评分"""
        # 简化版：基于PE
        pe_ratio = latest.get("pe_ratio", 20)

        if pe_ratio < 15:
            return 90
        elif pe_ratio < 25:
            return 70
        elif pe_ratio < 35:
            return 50
        else:
            return 30

    def _calculate_momentum_score(self, latest: Dict[str, Any]) -> float:
        """计算动量评分"""
        revenue_growth = latest.get("revenue_growth", 0)
        return min(100, max(0, 50 + revenue_growth * 2))

    def _calculate_safety_score(self, latest: Dict[str, Any]) -> float:
        """计算安全评分"""
        debt_ratio = latest.get("debt_ratio", 0)
        return max(0, 100 - debt_ratio)

    def _assess_timing_level(self, timing_score: float) -> str:
        """评估时机等级"""
        if timing_score >= 75:
            return "EXCELLENT (优秀)"
        elif timing_score >= 60:
            return "GOOD (良好)"
        elif timing_score >= 45:
            return "FAIR (一般)"
        else:
            return "POOR (较差)"

    def _generate_timing_warnings(self, latest: Dict[str, Any]) -> List[str]:
        """生成时机风险提示"""
        warnings = []

        debt_ratio = latest.get("debt_ratio", 0)
        if debt_ratio > 60:
            warnings.append("⚠️ 负债率较高，需谨慎")

        revenue_growth = latest.get("revenue_growth", 0)
        if revenue_growth < 0:
            warnings.append("⚠️ 营收下滑，时机不佳")

        return warnings if warnings else ["✅ 时机评估正常"]

    def _generate_timing_recommendation(self, timing_score: float) -> str:
        """生成时机面建议"""
        if timing_score >= 75:
            return "强烈建议买入"
        elif timing_score >= 60:
            return "建议买入"
        elif timing_score >= 45:
            return "建议观望"
        else:
            return "建议等待"

    def _generate_summary(
        self,
        risk: Dict[str, Any],
        timing: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """生成总结"""
        summary = f"风险面：{risk['risk_level']}（风险评分{risk['risk_score']:.1f}分）。"
        summary += f"时机面：时机评估{timing['timing_level']}（时机评分{timing['timing_score']:.1f}分）。"
        summary += f"投资建议：{recommendation['action']}（置信度{recommendation['confidence']*100:.0f}%）。"

        return summary

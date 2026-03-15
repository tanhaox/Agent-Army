"""
目标定价AI - 目标预测军团 (1/4)

⚠️ DEPRECATED: 此Agent已废弃,请使用ValuationAndRecommendationAI代替
迁移指南: docs/MIGRATION_GUIDE_VALUATION.md
废弃日期: 2026-03-14
计划移除日期: 2026-04-14

职责：
- 计算合理估值区间
- 预测目标价格
- 评估上涨空间
- 生成投资建议

使用工具库：
- FinancialTool（财务数据）
- FormulaTool（估值公式）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import warnings

# 显示废弃警告
warnings.warn(
    "TargetPricingAI已废弃,请使用ValuationAndRecommendationAI代替。"
    "迁移指南: docs/MIGRATION_GUIDE_VALUATION.md"
    "废弃日期: 2026-03-14, 计划移除日期: 2026-04-14",
    DeprecationWarning,
    stacklevel=2
)

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source import FinancialTool
from src.core.tools.calculation import FormulaTool


class TargetPricingAI(BusinessAgent):
    """
    目标定价AI

    目标预测军团 (1/4)
    负责预测目标价格和上涨空间
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具库
        self.financial_tool = FinancialTool()
        self.formula_tool = FormulaTool()

        super().__init__(
            name="目标定价AI",
            role="预测目标价格和上涨空间",
            corps="target_forecast",
            analysis_type="target_pricing",
            capabilities=[
                AgentCapability(
                    name="valuation_calculation",
                    description="估值计算",
                    input_type="financial_data",
                    output_type="valuation_range"
                ),
                AgentCapability(
                    name="price_prediction",
                    description="价格预测",
                    input_type="valuation_data",
                    output_type="target_price"
                ),
                AgentCapability(
                    name="upside_analysis",
                    description="上涨空间分析",
                    input_type="current_price,target_price",
                    output_type="upside_percentage"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具",
                    tool_type="library",
                    config={}
                ),
                AgentTool(
                    name="formula_tool",
                    description="公式计算工具",
                    tool_type="library",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("目标定价AI初始化完成（使用工具库）")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        分析目标价格

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - current_price: 当前价格（可选，默认使用模拟价格）

        Returns:
            目标定价分析结果
        """
        self.logger.info(f"开始目标定价分析", extra={"stock_code": stock_code})

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # ========== 1. 获取财务数据（工具库）==========
        financial_data = await self.financial_tool.fetch_financial_data(stock_code, years=1)
        latest = financial_data["latest"]

        # ========== 2. 计算估值指标（工具库）==========
        valuation = self._calculate_valuation(latest)

        # ========== 3. 业务逻辑：确定合理价格区间 ==========
        price_range = self._determine_price_range(valuation, latest)

        # ========== 4. 业务逻辑：预测目标价格 ==========
        target_price = self._predict_target_price(price_range)

        # ========== 5. 业务逻辑：计算上涨空间 ==========
        current_price = kwargs.get("current_price", 1800.0)  # 默认模拟价格
        upside = self._calculate_upside(current_price, target_price)

        # ========== 6. 业务逻辑：风险评估 ==========
        risk_level = self._assess_risk_level(valuation, upside)

        # ========== 7. 生成投资建议 ==========
        recommendation = self._generate_recommendation(target_price, current_price, upside)

        # ========== 8. 生成分析结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": financial_data["stock_name"],
            "analysis_type": "target_pricing",
            "timestamp": datetime.now().isoformat(),

            # 价格信息
            "current_price": current_price,
            "target_price": target_price,
            "upside_percentage": upside["percentage"],
            "upside_description": upside["description"],

            # 估值区间
            "price_range": price_range,

            # 估值指标
            "valuation_metrics": {
                "pe_ratio": valuation["pe_ratio"],
                "pb_ratio": valuation["pb_ratio"],
                "fair_value_estimate": valuation["fair_value"]
            },

            # 风险评估
            "risk_level": risk_level["level"],
            "risk_score": risk_level["score"],
            "risk_factors": risk_level["factors"],

            # 投资建议
            "recommendation": recommendation["action"],
            "confidence": recommendation["confidence"],
            "reasoning": recommendation["reasoning"],

            # 详细分析
            "details": {
                "valuation_method": "综合PE、PB和DCF估值法",
                "key_assumptions": [
                    "未来3年净利润增长率10-15%",
                    "合理PE倍数25-30倍",
                    "安全边际要求20%以上"
                ],
                "analysis_notes": self._generate_analysis_notes(valuation, upside)
            },

            # 总结
            "summary": self._generate_summary(
                target_price,
                current_price,
                upside["percentage"],
                recommendation["action"]
            )
        }

        self.logger.info(
            f"目标定价分析完成",
            extra={
                "stock_code": stock_code,
                "target_price": target_price,
                "upside": upside["percentage"]
            }
        )

        return result

    def _calculate_valuation(self, financial_data: Dict) -> Dict[str, float]:
        """
        计算估值指标（使用工具库）

        Args:
            financial_data: 财务数据

        Returns:
            估值指标
        """
        # 使用公式工具计算PE
        pe_data = {
            "stock_price": 1800.0,  # 模拟价格
            "earnings_per_share": financial_data.get("net_profit", 0) / 12.56  # 假设总股本
        }
        pe_ratio = self.formula_tool.calculate("pe", pe_data)

        # 使用公式工具计算PB
        pb_data = {
            "stock_price": 1800.0,
            "net_assets_per_share": financial_data.get("net_assets", 0) / 12.56
        }
        pb_ratio = self.formula_tool.calculate("pb", pb_data)

        # 计算合理价值（简化版DCF）
        fair_value = financial_data.get("net_profit", 0) * 25 / 12.56  # PE 25倍

        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "fair_value": fair_value
        }

    def _determine_price_range(self, valuation: Dict, financial_data: Dict) -> Dict[str, float]:
        """
        确定合理价格区间（业务逻辑）

        Args:
            valuation: 估值指标
            financial_data: 财务数据

        Returns:
            价格区间 {low, mid, high}
        """
        # 基于PE估值
        pe_based_price = financial_data.get("net_profit", 0) * 25 / 12.56

        # 安全边际调整
        low = pe_based_price * 0.8   # 保守价格（20%安全边际）
        mid = pe_based_price          # 合理价格
        high = pe_based_price * 1.2  # 乐观价格

        return {
            "low": round(low, 2),
            "mid": round(mid, 2),
            "high": round(high, 2)
        }

    def _predict_target_price(self, price_range: Dict) -> float:
        """
        预测目标价格（业务逻辑）

        Args:
            price_range: 价格区间

        Returns:
            目标价格
        """
        # 目标价格取合理价格和乐观价格的中位数
        target = (price_range["mid"] + price_range["high"]) / 2
        return round(target, 2)

    def _calculate_upside(self, current_price: float, target_price: float) -> Dict[str, Any]:
        """
        计算上涨空间（业务逻辑）

        Args:
            current_price: 当前价格
            target_price: 目标价格

        Returns:
            上涨空间信息
        """
        if current_price == 0:
            return {"percentage": 0, "description": "无法计算"}

        percentage = ((target_price - current_price) / current_price) * 100

        if percentage >= 50:
            description = "大幅上涨空间"
        elif percentage >= 30:
            description = "显著上涨空间"
        elif percentage >= 15:
            description = "温和上涨空间"
        elif percentage >= 0:
            description = "有限上涨空间"
        else:
            description = "下跌风险"

        return {
            "percentage": round(percentage, 1),
            "description": description
        }

    def _assess_risk_level(self, valuation: Dict, upside: Dict) -> Dict[str, Any]:
        """
        评估风险等级（业务逻辑）

        Args:
            valuation: 估值指标
            upside: 上涨空间

        Returns:
            风险评估
        """
        factors = []
        risk_score = 0

        # PE过高风险
        if valuation["pe_ratio"] > 40:
            factors.append("PE估值偏高")
            risk_score += 20
        elif valuation["pe_ratio"] > 30:
            factors.append("PE估值合理偏高")
            risk_score += 10

        # PB过高风险
        if valuation["pb_ratio"] > 8:
            factors.append("PB估值偏高")
            risk_score += 15

        # 上涨空间过大（可能不切实际）
        if upside["percentage"] > 80:
            factors.append("目标价格过于乐观")
            risk_score += 15

        # 确定风险等级
        if risk_score >= 40:
            level = "HIGH"
        elif risk_score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"
            factors.append("风险可控")

        return {
            "level": level,
            "score": risk_score,
            "factors": factors
        }

    def _generate_recommendation(
        self,
        target_price: float,
        current_price: float,
        upside: Dict
    ) -> Dict[str, Any]:
        """
        生成投资建议（业务逻辑）

        Args:
            target_price: 目标价格
            current_price: 当前价格
            upside: 上涨空间

        Returns:
            投资建议
        """
        percentage = upside["percentage"]

        if percentage >= 40:
            action = "STRONG_BUY"
            confidence = 0.8
            reasoning = "目标价格显著高于当前价格，具备较好投资价值"
        elif percentage >= 20:
            action = "BUY"
            confidence = 0.7
            reasoning = "目标价格高于当前价格，具备投资价值"
        elif percentage >= 0:
            action = "HOLD"
            confidence = 0.6
            reasoning = "目标价格接近当前价格，建议持有观望"
        else:
            action = "SELL"
            confidence = 0.7
            reasoning = "目标价格低于当前价格，存在下跌风险"

        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning
        }

    def _generate_analysis_notes(self, valuation: Dict, upside: Dict) -> list:
        """
        生成分析说明（业务逻辑）

        Args:
            valuation: 估值指标
            upside: 上涨空间

        Returns:
            分析说明列表
        """
        notes = []

        notes.append(f"当前PE倍数{valuation['pe_ratio']:.1f}倍")
        notes.append(f"当前PB倍数{valuation['pb_ratio']:.1f}倍")

        if upside["percentage"] > 0:
            notes.append(f"预期上涨空间{upside['percentage']:.1f}%")
        else:
            notes.append(f"预期下跌风险{abs(upside['percentage']):.1f}%")

        return notes

    def _generate_summary(
        self,
        target_price: float,
        current_price: float,
        upside_percentage: float,
        recommendation: str
    ) -> str:
        """
        生成总结（业务逻辑）

        Args:
            target_price: 目标价格
            current_price: 当前价格
            upside_percentage: 上涨空间
            recommendation: 投资建议

        Returns:
            总结文本
        """
        action_map = {
            "STRONG_BUY": "强烈推荐买入",
            "BUY": "建议买入",
            "HOLD": "持有观望",
            "SELL": "建议卖出"
        }

        summary_parts = [
            f"当前价格{current_price:.2f}元",
            f"目标价格{target_price:.2f}元",
            f"预期上涨空间{upside_percentage:.1f}%",
            f"投资建议：{action_map.get(recommendation, '未知')}"
        ]

        return "，".join(summary_parts)


# ========== 便捷函数 ==========

async def analyze_target_price(stock_code: str, current_price: float = None) -> Dict[str, Any]:
    """
    分析目标价格（便捷函数）

    Args:
        stock_code: 股票代码
        current_price: 当前价格（可选）

    Returns:
        目标定价分析结果
    """
    ai = TargetPricingAI()
    kwargs = {"current_price": current_price} if current_price else {}
    return await ai.analyze(stock_code, **kwargs)

"""
基本面分析AI - 个股挖掘军团 (1/4)

职责：
- 分析财务数据质量
- 评估盈利能力
- 评估成长能力
- 评估偿债能力
- 生成投资建议

重构说明：
- 使用工具库（FinancialTool、FormulaTool）处理数据获取和计算
- AI只关心业务逻辑（评分、评级、风险判断）
- ⭐ Phase 3: 添加缓存支持
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source import FinancialTool
from src.core.tools.calculation import FormulaTool
from src.core.utils.cache import get_global_cache_manager


class FundamentalAnalyzer(BusinessAgent):
    """
    基本面分析AI

    个股挖掘军团 (1/4)
    负责分析股票基本面情况，评估投资价值
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具库
        self.financial_tool = FinancialTool()
        self.formula_tool = FormulaTool()

        # ⭐ Phase 3: 初始化缓存
        self.cache = get_global_cache_manager().get("fundamental_analysis")

        super().__init__(
            name="基本面分析AI",
            role="分析股票基本面情况",
            corps="stock_mining",
            analysis_type="fundamental",
            capabilities=[
                AgentCapability(
                    name="financial_analysis",
                    description="财务数据分析",
                    input_type="stock_code",
                    output_type="financial_metrics"
                ),
                AgentCapability(
                    name="profitability_analysis",
                    description="盈利能力分析",
                    input_type="financial_data",
                    output_type="profitability_score"
                ),
                AgentCapability(
                    name="growth_analysis",
                    description="成长能力分析",
                    input_type="financial_data",
                    output_type="growth_score"
                ),
                AgentCapability(
                    name="solvency_analysis",
                    description="偿债能力分析",
                    input_type="financial_data",
                    output_type="solvency_score"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具（工具库）",
                    tool_type="library",
                    config={}
                ),
                AgentTool(
                    name="formula_tool",
                    description="公式计算工具（工具库）",
                    tool_type="library",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("基本面分析AI初始化完成（使用工具库+缓存）")

    async def _do_analysis(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        实际的基本面分析逻辑（内部方法）

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - years: 分析年数（默认3年）

        Returns:
            基本面分析结果
        """
        self.logger.info(f"开始基本面分析", extra={"stock_code": stock_code})

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取分析年数
        years = kwargs.get("years", 3)

        # ========== 1. 获取财务数据（使用工具库）==========
        financial_data = await self.financial_tool.fetch_financial_data(stock_code, years)

        # ========== 2. 计算财务指标（使用工具库）==========
        metrics = self._calculate_metrics(financial_data)

        # ========== 3. 业务逻辑：评分和评级 ==========
        scores = self._calculate_scores(metrics)
        rating = self._determine_rating(scores["composite_score"])
        investment_value = self._generate_investment_value(scores, metrics)

        # ========== 4. 业务逻辑：风险分析 ==========
        warnings = self._analyze_risks(metrics)

        # ========== 5. 生成分析结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": financial_data["stock_name"],
            "analysis_type": "fundamental",
            "timestamp": datetime.now().isoformat(),
            "analysis_period": f"最近{years}年",

            # 综合评分
            "composite_score": scores["composite_score"],
            "confidence": scores["confidence"],

            # 分项评分
            "scores": {
                "financial_quality": scores["financial_quality"],
                "profitability": scores["profitability"],
                "growth_ability": scores["growth_ability"],
                "solvency": scores["solvency"]
            },

            # 投资评级
            "rating": rating,
            "investment_value": investment_value,

            # 核心指标
            "key_metrics": {
                "roe": metrics["latest_roe"],
                "revenue_growth": metrics["revenue_growth"],
                "profit_growth": metrics["profit_growth"],
                "debt_ratio": metrics["debt_ratio"]
            },

            # 详细数据
            "details": {
                "financial_data": financial_data["latest"],
                "analysis_highlights": self._generate_highlights(scores, metrics)
            },

            # 风险提示
            "warnings": warnings,

            # 总结
            "summary": self._generate_summary(scores, rating)
        }

        self.logger.info(
            f"基本面分析完成",
            extra={
                "stock_code": stock_code,
                "composite_score": result["composite_score"],
                "rating": result["rating"]
            }
        )

        return result

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        分析股票基本面（带缓存）

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - years: 分析年数（默认3年）

        Returns:
            基本面分析结果
        """
        # ⭐ Phase 3: 使用缓存
        return await self.cache.get_or_compute_async(
            self._do_analysis,
            stock_code,
            **kwargs
        )

    def _calculate_metrics(self, financial_data: Dict) -> Dict[str, Any]:
        """
        计算财务指标（使用工具库）

        Args:
            financial_data: 财务数据

        Returns:
            计算的指标
        """
        latest = financial_data["latest"]

        # 使用公式工具计算指标
        roe_data = {
            "net_profit": latest.get("net_profit", 0),
            "net_assets": latest.get("net_assets", 0)
        }
        roe = self.formula_tool.calculate("roe", roe_data)

        # 计算增长率（简化版本）
        revenue_growth = self._calculate_growth(
            financial_data["history"],
            "revenue"
        )
        profit_growth = self._calculate_growth(
            financial_data["history"],
            "net_profit"
        )

        return {
            "latest_roe": roe,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "debt_ratio": latest.get("debt_ratio", 0),
            "gross_margin": latest.get("gross_margin", 0),
            "net_margin": latest.get("net_margin", 0),
            "current_ratio": latest.get("current_ratio", 0)
        }

    def _calculate_growth(self, history: list, field: str) -> float:
        """
        计算增长率（业务逻辑）

        Args:
            history: 历史数据列表
            field: 字段名

        Returns:
            平均增长率（%）
        """
        if len(history) < 2:
            return 0.0

        # 简单计算最近两年的增长率
        try:
            latest = history[-1].get(field, 0)
            previous = history[-2].get(field, 0)

            if previous == 0:
                return 0.0

            growth = ((latest - previous) / previous) * 100
            return round(growth, 1)
        except:
            return 0.0

    def _calculate_scores(self, metrics: Dict) -> Dict[str, float]:
        """
        计算各项评分（业务逻辑）

        Args:
            metrics: 财务指标

        Returns:
            评分字典
        """
        # 盈利能力评分（ROE 15%以上得高分）
        roe = metrics["latest_roe"]
        profitability = min(100, roe * 5) if roe > 0 else 0

        # 成长能力评分（增长15%以上得高分）
        avg_growth = (metrics["revenue_growth"] + metrics["profit_growth"]) / 2
        growth_ability = min(100, avg_growth * 4) if avg_growth > 0 else 0

        # 偿债能力评分（负债率40%以下得高分）
        debt_ratio = metrics["debt_ratio"]
        solvency = max(0, 100 - debt_ratio * 1.5)

        # 财务质量评分（综合指标）
        financial_quality = (
            profitability * 0.3 +
            growth_ability * 0.3 +
            solvency * 0.2 +
            (metrics["gross_margin"] * 2) * 0.2
        )

        # 综合评分
        composite_score = (
            financial_quality * 0.25 +
            profitability * 0.3 +
            growth_ability * 0.25 +
            solvency * 0.2
        )

        # 置信度（基于数据完整性）
        confidence = 0.85 if all([
            roe > 0,
            metrics["revenue_growth"] != 0,
            metrics["profit_growth"] != 0
        ]) else 0.7

        return {
            "composite_score": round(composite_score, 1),
            "financial_quality": round(financial_quality, 1),
            "profitability": round(profitability, 1),
            "growth_ability": round(growth_ability, 1),
            "solvency": round(solvency, 1),
            "confidence": confidence
        }

    def _determine_rating(self, composite_score: float) -> str:
        """
        确定投资评级（业务逻辑）

        Args:
            composite_score: 综合评分

        Returns:
            评级（STRONG_BUY/BUY/HOLD/SELL）
        """
        if composite_score >= 80:
            return "STRONG_BUY"
        elif composite_score >= 65:
            return "BUY"
        elif composite_score >= 50:
            return "HOLD"
        else:
            return "SELL"

    def _generate_investment_value(self, scores: Dict, metrics: Dict) -> str:
        """
        生成投资价值说明（业务逻辑）

        Args:
            scores: 评分
            metrics: 指标

        Returns:
            投资价值说明
        """
        parts = []

        if scores["composite_score"] >= 75:
            parts.append("具备长期投资价值")
        elif scores["composite_score"] >= 60:
            parts.append("具备一定投资价值")
        else:
            parts.append("投资价值有限")

        if metrics["latest_roe"] >= 15:
            parts.append("ROE表现优秀")
        if scores["growth_ability"] >= 70:
            parts.append("成长性良好")
        if scores["solvency"] >= 70:
            parts.append("财务稳健")

        return "，".join(parts)

    def _analyze_risks(self, metrics: Dict) -> list:
        """
        分析风险（业务逻辑）

        Args:
            metrics: 指标

        Returns:
            风险提示列表
        """
        warnings = []

        if metrics["debt_ratio"] > 60:
            warnings.append(f"⚠️ 资产负债率较高({metrics['debt_ratio']}%)，需关注偿债压力")

        if metrics["revenue_growth"] < 0:
            warnings.append("⚠️ 营收增长为负，需关注业务发展")

        if metrics["profit_growth"] < 0 and metrics["revenue_growth"] > 0:
            warnings.append("⚠️ 营收增长但利润下滑，需关注成本控制")

        if metrics["latest_roe"] < 10:
            warnings.append("⚠️ ROE偏低，盈利能力需提升")

        return warnings

    def _generate_highlights(self, scores: Dict, metrics: Dict) -> list:
        """
        生成分析亮点（业务逻辑）

        Args:
            scores: 评分
            metrics: 指标

        Returns:
            亮点列表
        """
        highlights = []

        if metrics["latest_roe"] >= 15:
            highlights.append(f"ROE达到{metrics['latest_roe']}%，盈利能力优秀")

        if metrics["revenue_growth"] >= 10 and metrics["profit_growth"] >= 10:
            highlights.append("营收和利润保持双位数增长")

        if metrics["debt_ratio"] <= 40:
            highlights.append("资产负债率控制在合理范围")

        if scores["solvency"] >= 80:
            highlights.append("现金流充沛，财务稳健")

        return highlights if highlights else ["财务状况基本正常"]

    def _generate_summary(self, scores: Dict, rating: str) -> str:
        """
        生成总结（业务逻辑）

        Args:
            scores: 评分
            rating: 评级

        Returns:
            总结文本
        """
        rating_map = {
            "STRONG_BUY": "强烈推荐",
            "BUY": "建议买入",
            "HOLD": "持有观望",
            "SELL": "建议卖出"
        }

        summary_parts = [
            f"综合评分{scores['composite_score']}分",
            f"评级：{rating_map.get(rating, '未知')}",
            f"盈利能力{scores['profitability']}分",
            f"成长能力{scores['growth_ability']}分",
            f"偿债能力{scores['solvency']}分"
        ]

        return "，".join(summary_parts)


# ========== 便捷函数 ==========

async def analyze_fundamental(stock_code: str, years: int = 3) -> Dict[str, Any]:
    """
    分析股票基本面（便捷函数）

    Args:
        stock_code: 股票代码
        years: 分析年数

    Returns:
        基本面分析结果
    """
    analyzer = FundamentalAnalyzer()
    return await analyzer.analyze(stock_code, years=years)

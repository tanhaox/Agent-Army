"""
综合评分AI - Comprehensive Score AI

⚠️ DEPRECATED: 此Agent已废弃,请使用ValuationAndRecommendationAI代替
迁移指南: docs/MIGRATION_GUIDE_VALUATION.md
废弃日期: 2026-03-14
计划移除日期: 2026-04-14

职责：
- 综合多维度数据打分
- 生成投资价值评分
- 提供投资建议

输入：
- 股票代码
- 分析维度

输出：
- 综合评分（0-100）
- 各维度评分
- 投资建议
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import warnings

# 显示废弃警告
warnings.warn(
    "ComprehensiveScoreAI已废弃,请使用ValuationAndRecommendationAI代替。"
    "迁移指南: docs/MIGRATION_GUIDE_VALUATION.md"
    "废弃日期: 2026-03-14, 计划移除日期: 2026-04-14",
    DeprecationWarning,
    stacklevel=2
)

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class ComprehensiveScoreAI(BaseAgent, LoggerMixin):
    """综合评分AI - 综合多维度数据打分"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="综合评分AI",
            role="综合多维度数据打分，生成投资价值评分，提供投资建议",
            capabilities=[
                AgentCapability(
                    name="comprehensive_scoring",
                    description="综合评分",
                    input_type="stock_code",
                    output_type="comprehensive_score"
                ),
                AgentCapability(
                    name="dimension_analysis",
                    description="维度分析",
                    input_type="stock_code",
                    output_type="dimension_report"
                ),
                AgentCapability(
                    name="investment_recommendation",
                    description="投资建议",
                    input_type="stock_code",
                    output_type="recommendation"
                )
            ],
            tools=[
                AgentTool(
                    name="score_calculator",
                    description="评分计算工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("综合评分AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "calculate_score":
            return await self.calculate_score(
                kwargs.get("stock_code")
            )
        elif task == "analyze_dimensions":
            return await self.analyze_dimensions(
                kwargs.get("stock_code")
            )
        elif task == "get_recommendation":
            return await self.get_recommendation(
                kwargs.get("stock_code")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def calculate_score(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """计算综合评分"""
        self.logger.info(f"开始计算综合评分", extra={"stock_code": stock_code})

        # 1. 获取各维度数据
        dimensions = await self._fetch_all_dimensions(stock_code)

        # 2. 计算各维度评分
        dimension_scores = self._calculate_dimension_scores(dimensions)

        # 3. 计算综合评分
        comprehensive_score = self._calculate_comprehensive_score(dimension_scores)

        # 4. 生成评级
        rating = self._get_rating(comprehensive_score)

        # 5. 生成报告
        report = {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "comprehensive_score": comprehensive_score,
            "rating": rating,
            "dimension_scores": dimension_scores,
            "summary": self._generate_summary(comprehensive_score, rating),
            "recommendation": self._generate_recommendation(comprehensive_score, rating)
        }

        self.logger.info(
            f"综合评分计算完成",
            extra={"stock_code": stock_code, "score": comprehensive_score}
        )

        return report

    async def analyze_dimensions(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """分析各维度"""
        self.logger.info(f"分析各维度", extra={"stock_code": stock_code})

        # 获取各维度数据
        dimensions = await self._fetch_all_dimensions(stock_code)

        # 分析各维度
        analysis = {}
        for dim_name, dim_data in dimensions.items():
            analysis[dim_name] = {
                "data": dim_data,
                "analysis": self._analyze_single_dimension(dim_name, dim_data)
            }

        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "dimensions": analysis,
            "dimension_count": len(analysis)
        }

    async def get_recommendation(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """获取投资建议"""
        self.logger.info(f"获取投资建议", extra={"stock_code": stock_code})

        # 计算综合评分
        score_result = await self.calculate_score(stock_code)

        # 生成建议
        recommendation = {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "score": score_result["comprehensive_score"],
            "rating": score_result["rating"],
            "action": self._get_action(score_result["comprehensive_score"]),
            "confidence": self._calculate_confidence(score_result["dimension_scores"]),
            "reasons": self._get_recommendation_reasons(score_result),
            "risks": self._identify_risks(score_result),
            "suggestion": self._generate_detailed_suggestion(score_result)
        }

        return recommendation

    # ========== 辅助方法 ==========

    async def _fetch_all_dimensions(self, stock_code: str) -> Dict[str, Any]:
        """获取所有维度数据（模拟）"""
        import random

        # 模拟各维度数据
        return {
            "基本面": {
                "财务健康": random.uniform(60, 90),
                "盈利能力": random.uniform(50, 85),
                "成长性": random.uniform(40, 80),
                "估值水平": random.uniform(30, 70)
            },
            "技术面": {
                "趋势强度": random.uniform(40, 80),
                "成交量": random.uniform(50, 90),
                "技术指标": random.uniform(45, 75)
            },
            "资金面": {
                "主力资金": random.uniform(30, 80),
                "北向资金": random.uniform(40, 85),
                "融资余额": random.uniform(50, 75)
            },
            "情绪面": {
                "市场热度": random.uniform(30, 90),
                "机构评级": random.uniform(50, 85),
                "舆情情感": random.uniform(40, 80)
            }
        }

    def _calculate_dimension_scores(
        self,
        dimensions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算各维度评分"""
        scores = {}

        # 基本面评分（权重40%）
        fundamental = dimensions["基本面"]
        fundamental_score = (
            fundamental["财务健康"] * 0.3 +
            fundamental["盈利能力"] * 0.3 +
            fundamental["成长性"] * 0.25 +
            fundamental["估值水平"] * 0.15
        )
        scores["基本面"] = {
            "score": round(fundamental_score, 2),
            "weight": 0.40,
            "details": fundamental
        }

        # 技术面评分（权重25%）
        technical = dimensions["技术面"]
        technical_score = (
            technical["趋势强度"] * 0.4 +
            technical["成交量"] * 0.3 +
            technical["技术指标"] * 0.3
        )
        scores["技术面"] = {
            "score": round(technical_score, 2),
            "weight": 0.25,
            "details": technical
        }

        # 资金面评分（权重20%）
        capital = dimensions["资金面"]
        capital_score = (
            capital["主力资金"] * 0.4 +
            capital["北向资金"] * 0.35 +
            capital["融资余额"] * 0.25
        )
        scores["资金面"] = {
            "score": round(capital_score, 2),
            "weight": 0.20,
            "details": capital
        }

        # 情绪面评分（权重15%）
        sentiment = dimensions["情绪面"]
        sentiment_score = (
            sentiment["市场热度"] * 0.3 +
            sentiment["机构评级"] * 0.4 +
            sentiment["舆情情感"] * 0.3
        )
        scores["情绪面"] = {
            "score": round(sentiment_score, 2),
            "weight": 0.15,
            "details": sentiment
        }

        return scores

    def _calculate_comprehensive_score(
        self,
        dimension_scores: Dict[str, Any]
    ) -> float:
        """计算综合评分"""
        total_score = 0

        for dim_name, dim_data in dimension_scores.items():
            total_score += dim_data["score"] * dim_data["weight"]

        return round(total_score, 2)

    def _get_rating(self, score: float) -> str:
        """获取评级"""
        if score >= 85:
            return "强烈推荐"
        elif score >= 75:
            return "推荐"
        elif score >= 65:
            return "中性"
        elif score >= 55:
            return "谨慎"
        else:
            return "不推荐"

    def _analyze_single_dimension(
        self,
        dim_name: str,
        dim_data: Dict[str, float]
    ) -> str:
        """分析单个维度"""
        avg_score = sum(dim_data.values()) / len(dim_data)

        if avg_score >= 75:
            status = "优秀"
        elif avg_score >= 60:
            status = "良好"
        elif avg_score >= 45:
            status = "一般"
        else:
            status = "较差"

        return f"{dim_name}整体{status}，平均得分{avg_score:.1f}分"

    def _get_action(self, score: float) -> str:
        """获取操作建议"""
        if score >= 85:
            return "强烈买入"
        elif score >= 75:
            return "买入"
        elif score >= 65:
            return "持有"
        elif score >= 55:
            return "观望"
        else:
            return "卖出"

    def _calculate_confidence(
        self,
        dimension_scores: Dict[str, Any]
    ) -> float:
        """计算置信度"""
        # 基于各维度的一致性计算置信度
        scores = [dim["score"] for dim in dimension_scores.values()]
        avg_score = sum(scores) / len(scores)

        # 计算标准差（越小越一致）
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # 标准差越小，置信度越高
        confidence = max(50, 100 - std_dev * 2)

        return round(confidence, 2)

    def _get_recommendation_reasons(
        self,
        score_result: Dict[str, Any]
    ) -> List[str]:
        """获取推荐理由"""
        reasons = []
        dimension_scores = score_result["dimension_scores"]

        # 找出优势维度
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["score"] >= 75:
                reasons.append(f"{dim_name}优秀（{dim_data['score']:.1f}分）")

        # 如果没有优势维度
        if not reasons:
            best_dim = max(
                dimension_scores.items(),
                key=lambda x: x[1]["score"]
            )
            reasons.append(f"{best_dim[0]}相对较好（{best_dim[1]['score']:.1f}分）")

        return reasons

    def _identify_risks(
        self,
        score_result: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []
        dimension_scores = score_result["dimension_scores"]

        # 找出劣势维度
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["score"] < 55:
                risks.append(f"{dim_name}较弱（{dim_data['score']:.1f}分）")

        # 如果没有明显风险
        if not risks:
            worst_dim = min(
                dimension_scores.items(),
                key=lambda x: x[1]["score"]
            )
            if worst_dim[1]["score"] < 65:
                risks.append(f"{worst_dim[0]}需关注（{worst_dim[1]['score']:.1f}分）")

        return risks if risks else ["暂无明显风险"]

    def _generate_summary(self, score: float, rating: str) -> str:
        """生成摘要"""
        return f"综合评分{score:.1f}分，评级：{rating}"

    def _generate_recommendation(self, score: float, rating: str) -> str:
        """生成建议"""
        if score >= 75:
            return "投资价值较高，建议关注"
        elif score >= 65:
            return "投资价值一般，可适度关注"
        elif score >= 55:
            return "投资价值较低，建议谨慎"
        else:
            return "投资价值较差，建议规避"

    def _generate_detailed_suggestion(
        self,
        score_result: Dict[str, Any]
    ) -> str:
        """生成详细建议"""
        score = score_result["comprehensive_score"]
        rating = score_result["rating"]
        dimension_scores = score_result["dimension_scores"]

        suggestion = f"综合评分{score:.1f}分（{rating}）。\n\n"

        # 各维度分析
        suggestion += "维度分析：\n"
        for dim_name, dim_data in dimension_scores.items():
            status = "优秀" if dim_data["score"] >= 75 else "良好" if dim_data["score"] >= 60 else "一般"
            suggestion += f"- {dim_name}：{dim_data['score']:.1f}分（{status}）\n"

        # 建议
        if score >= 75:
            suggestion += "\n建议：可以重点关注，考虑逢低布局。"
        elif score >= 65:
            suggestion += "\n建议：可以适度关注，等待更好时机。"
        elif score >= 55:
            suggestion += "\n建议：谨慎对待，不宜重仓。"
        else:
            suggestion += "\n建议：建议规避，风险较大。"

        return suggestion

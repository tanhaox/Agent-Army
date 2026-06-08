"""
综合评估AI - Comprehensive Evaluation AI

预测部成员 (2/3)

职责：
1. 综合评分 - 整合各部门分析结果的综合评分
2. 质量评分 - 投资质量和风险评估

合并来源：
- 综合评分AI
- 质量评分AI

使用工具：
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class ComprehensiveEvaluationAI(BusinessAgent):
    """
    综合评估AI - 预测部成员 (2/3)

    核心能力:
    1. 综合评分 - 多维度综合评分系统
    2. 质量评分 - 投资质量评估

    使用工具:
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="综合评估AI",
            role="综合评估投资质量，生成综合评分",
            corps="prediction",
            analysis_type="comprehensive_evaluation",
            capabilities=[
                AgentCapability(
                    name="comprehensive_scoring",
                    description="综合评分计算",
                    input_type="multi_source_data",
                    output_type="overall_score"
                ),
                AgentCapability(
                    name="quality_assessment",
                    description="质量评估分析",
                    input_type="stock_data",
                    output_type="quality_rating"
                )
            ],
            tools=[
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("综合评估AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行综合评估分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - research_data: 研究部数据（可选）
                - analysis_data: 分析部数据（可选）
                - prediction_data: 预测部数据（可选）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        self.logger.info(
            f"开始综合评估分析",
            extra={"stock_code": stock_code}
        )

        # ========== 1. 获取多源数据 ==========
        research_data = kwargs.get("research_data", {})
        analysis_data = kwargs.get("analysis_data", {})
        prediction_data = kwargs.get("prediction_data", {})

        # ========== 2. 多维度评分 ==========
        dimension_scores = self._calculate_dimension_scores(
            research_data,
            analysis_data,
            prediction_data
        )

        # ========== 3. 综合评分计算 ==========
        comprehensive_score = self._calculate_comprehensive_score(dimension_scores)

        # ========== 4. 质量评估 ==========
        quality_assessment = self._assess_quality(
            comprehensive_score,
            dimension_scores
        )

        # ========== 5. 投资评级 ==========
        investment_rating = self._determine_investment_rating(comprehensive_score)

        # ========== 6. 风险提示 ==========
        risks = self._identify_risks(dimension_scores, comprehensive_score)

        # ========== 7. 建议 ==========
        recommendations = self._generate_recommendations(
            comprehensive_score,
            investment_rating,
            dimension_scores
        )

        # ========== 8. 构建分析结果 ==========
        details = {
            # 维度评分
            "dimension_scores": dimension_scores,

            # 综合评分
            "comprehensive_score": comprehensive_score,

            # 质量评估
            "quality_assessment": quality_assessment,

            # 投资评级
            "investment_rating": investment_rating,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(comprehensive_score, investment_rating),
            confidence=self._calculate_confidence(dimension_scores),
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"综合评估分析完成",
            extra={
                "stock_code": stock_code,
                "comprehensive_score": comprehensive_score,
                "investment_rating": investment_rating
            }
        )

        return result

    # ========== 多维度评分 ==========

    def _calculate_dimension_scores(
        self,
        research_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        prediction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算多维度评分

        评分维度：
        1. 基本面维度（30分）
        2. 成长性维度（25分）
        3. 估值维度（20分）
        4. 技术面维度（15分）
        5. 市场情绪维度（10分）

        Returns:
            各维度评分
        """
        # TODO: 从实际数据中提取指标
        # 当前使用模拟数据

        # 1. 基本面维度（30分）
        fundamental_score = self._score_fundamental(analysis_data)

        # 2. 成长性维度（25分）
        growth_score = self._score_growth(analysis_data)

        # 3. 估值维度（20分）
        valuation_score = self._score_valuation(prediction_data)

        # 4. 技术面维度（15分）
        technical_score = self._score_technical(research_data)

        # 5. 市场情绪维度（10分）
        sentiment_score = self._score_sentiment(research_data)

        return {
            "fundamental": {
                "score": fundamental_score,
                "weight": 0.30,
                "weighted_score": fundamental_score * 0.30,
                "description": "基本面评分（ROE、财务健康度等）"
            },
            "growth": {
                "score": growth_score,
                "weight": 0.25,
                "weighted_score": growth_score * 0.25,
                "description": "成长性评分（营收增长、利润增长等）"
            },
            "valuation": {
                "score": valuation_score,
                "weight": 0.20,
                "weighted_score": valuation_score * 0.20,
                "description": "估值评分（PE、PB合理性等）"
            },
            "technical": {
                "score": technical_score,
                "weight": 0.15,
                "weighted_score": technical_score * 0.15,
                "description": "技术面评分（趋势、形态等）"
            },
            "sentiment": {
                "score": sentiment_score,
                "weight": 0.10,
                "weighted_score": sentiment_score * 0.10,
                "description": "市场情绪评分（资金流向、热度等）"
            }
        }

    def _score_fundamental(self, analysis_data: Dict[str, Any]) -> float:
        """基本面评分（满分100）"""
        # TODO: 从真实数据计算
        # 模拟评分
        return 75.0

    def _score_growth(self, analysis_data: Dict[str, Any]) -> float:
        """成长性评分（满分100）"""
        # TODO: 从真实数据计算
        # 模拟评分
        return 80.0

    def _score_valuation(self, prediction_data: Dict[str, Any]) -> float:
        """估值评分（满分100）"""
        # TODO: 从真实数据计算
        # 模拟评分
        return 70.0

    def _score_technical(self, research_data: Dict[str, Any]) -> float:
        """技术面评分（满分100）"""
        # TODO: 从真实数据计算
        # 模拟评分
        return 65.0

    def _score_sentiment(self, research_data: Dict[str, Any]) -> float:
        """市场情绪评分（满分100）"""
        # TODO: 从真实数据计算
        # 模拟评分
        return 60.0

    # ========== 综合评分计算 ==========

    def _calculate_comprehensive_score(
        self,
        dimension_scores: Dict[str, Any]
    ) -> float:
        """
        计算综合评分

        Args:
            dimension_scores: 各维度评分

        Returns:
            综合评分（0-100）
        """
        # 加权求和
        total_score = sum(
            dim["weighted_score"] for dim in dimension_scores.values()
        )

        return round(total_score, 1)

    # ========== 质量评估 ==========

    def _assess_quality(
        self,
        comprehensive_score: float,
        dimension_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        质量评估

        Args:
            comprehensive_score: 综合评分
            dimension_scores: 各维度评分

        Returns:
            质量评估结果
        """
        # 质量等级
        if comprehensive_score >= 85:
            quality_grade = "A+"
            quality_description = "优秀"
        elif comprehensive_score >= 80:
            quality_grade = "A"
            quality_description = "良好"
        elif comprehensive_score >= 70:
            quality_grade = "B+"
            quality_description = "较好"
        elif comprehensive_score >= 60:
            quality_grade = "B"
            quality_description = "一般"
        elif comprehensive_score >= 50:
            quality_grade = "C"
            quality_description = "较差"
        else:
            quality_grade = "D"
            quality_description = "差"

        # 识别优势和劣势
        strengths = []
        weaknesses = []

        for dim_name, dim_data in dimension_scores.items():
            score = dim_data["score"]
            if score >= 80:
                strengths.append(f"{dim_data['description']}优秀（{score}分）")
            elif score < 60:
                weaknesses.append(f"{dim_data['description']}不足（{score}分）")

        if not strengths:
            strengths.append("各维度评分均衡")
        if not weaknesses:
            weaknesses.append("无明显短板")

        # 平衡性评估
        scores = [dim["score"] for dim in dimension_scores.values()]
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        if std_dev < 10:
            balance = "高度平衡"
        elif std_dev < 15:
            balance = "较为平衡"
        else:
            balance = "存在失衡"

        return {
            "quality_grade": quality_grade,
            "quality_description": quality_description,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "balance_assessment": balance,
            "standard_deviation": round(std_dev, 2)
        }

    # ========== 投资评级 ==========

    def _determine_investment_rating(self, comprehensive_score: float) -> Dict[str, Any]:
        """
        确定投资评级

        Args:
            comprehensive_score: 综合评分

        Returns:
            投资评级
        """
        if comprehensive_score >= 85:
            rating = "强烈推荐"
            action = "积极买入"
            risk_level = "低"
        elif comprehensive_score >= 75:
            rating = "推荐"
            action = "买入"
            risk_level = "中低"
        elif comprehensive_score >= 65:
            rating = "中性"
            action = "持有观望"
            risk_level = "中"
        elif comprehensive_score >= 55:
            rating = "谨慎"
            action = "谨慎观望"
            risk_level = "中高"
        else:
            rating = "不推荐"
            action = "回避"
            risk_level = "高"

        return {
            "rating": rating,
            "action": action,
            "risk_level": risk_level,
            "score_range": self._get_score_range(comprehensive_score)
        }

    def _get_score_range(self, score: float) -> str:
        """获取评分区间描述"""
        if score >= 80:
            return "优秀区间（80-100）"
        elif score >= 60:
            return "良好区间（60-80）"
        elif score >= 40:
            return "一般区间（40-60）"
        else:
            return "较差区间（0-40）"

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        dimension_scores: Dict[str, Any],
        comprehensive_score: float
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 检查各维度风险
        for dim_name, dim_data in dimension_scores.items():
            score = dim_data["score"]
            if score < 60:
                risks.append(f"{dim_data['description']}风险（仅{score}分）")
            elif score < 70:
                risks.append(f"{dim_data['description']}存在隐忧（{score}分）")

        # 综合风险
        if comprehensive_score < 60:
            risks.append(f"综合评分偏低（{comprehensive_score}分），投资风险较大")

        # 平衡性风险
        scores = [dim["score"] for dim in dimension_scores.values()]
        if max(scores) - min(scores) > 30:
            risks.append("各维度评分差异较大，存在结构性风险")

        if not risks:
            risks.append("未发现明显投资风险")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        comprehensive_score: float,
        investment_rating: Dict[str, Any],
        dimension_scores: Dict[str, Any]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        # 基于评级的建议
        recommendations.append(
            f"综合评分{comprehensive_score}分，评级【{investment_rating['rating']}】，"
            f"建议{investment_rating['action']}"
        )

        # 基于优势的建议
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["score"] >= 80:
                recommendations.append(
                    f"利用{dim_name}优势，可作为核心投资标的"
                )
                break

        # 基于风险的建议
        if comprehensive_score < 70:
            recommendations.append("建议控制仓位，分批建仓降低风险")

        return recommendations

    # ========== 辅助方法 ==========

    def _calculate_confidence(self, dimension_scores: Dict[str, Any]) -> float:
        """计算评估置信度"""
        # 基于数据完整性和评分一致性
        # TODO: 实现更复杂的置信度计算

        # 简化：基于评分方差
        scores = [dim["score"] for dim in dimension_scores.values()]
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # 标准差越小，置信度越高
        # 标准差范围约 0-30，映射到 0.6-0.9
        confidence = max(0.6, min(0.9, 0.9 - std_dev / 100))

        return round(confidence, 2)

    def _generate_conclusion(
        self,
        comprehensive_score: float,
        investment_rating: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        return (
            f"综合评分{comprehensive_score}分，"
            f"质量等级{investment_rating['rating']}，"
            f"风险水平{investment_rating['risk_level']}"
        )


# 便捷函数
async def analyze_comprehensive_evaluation(
    stock_code: str,
    research_data: Optional[Dict] = None,
    analysis_data: Optional[Dict] = None,
    prediction_data: Optional[Dict] = None
) -> AnalysisResult:
    """
    综合评估分析（便捷函数）

    Args:
        stock_code: 股票代码
        research_data: 研究部数据
        analysis_data: 分析部数据
        prediction_data: 预测部数据

    Returns:
        分析结果
    """
    ai = ComprehensiveEvaluationAI()
    return await ai.analyze(
        stock_code,
        research_data=research_data or {},
        analysis_data=analysis_data or {},
        prediction_data=prediction_data or {}
    )

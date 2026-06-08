"""
机会筛选AI - Opportunity Screening AI

配置部成员 (2/2)

职责：
1. 多因子筛选 - 价值、成长、质量、动量因子
2. 行业轮动 - 识别行业轮动机会
3. 市场热点识别 - 发现市场热点和投资机会

使用工具：
- FinancialTool（财务数据）
- MarketTool（市场数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import asyncio

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class OpportunityScreeningAI(BusinessAgent):
    """
    机会筛选AI - 配置部成员 (2/2)

    核心能力:
    1. 多因子筛选 - 价值、成长、质量、动量四维筛选
    2. 行业轮动 - 识别行业轮动机会
    3. 市场热点识别 - 发现市场热点和投资机会

    使用工具:
    - FinancialTool (财务数据)
    - MarketTool (市场数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="机会筛选AI",
            role="筛选投资机会，发现优质标的",
            corps="configuration",
            analysis_type="opportunity_screening",
            capabilities=[
                AgentCapability(
                    name="multi_factor_screening",
                    description="多因子筛选",
                    input_type="stock_universe",
                    output_type="screened_stocks"
                ),
                AgentCapability(
                    name="sector_rotation",
                    description="行业轮动分析",
                    input_type="sector_data",
                    output_type="rotation_opportunities"
                ),
                AgentCapability(
                    name="hot_spot_detection",
                    description="市场热点识别",
                    input_type="market_data",
                    output_type="hot_spots"
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

        # 因子权重配置
        self.factor_weights = {
            "value": 0.30,  # 价值因子权重
            "growth": 0.30,  # 成长因子权重
            "quality": 0.25,  # 质量因子权重
            "momentum": 0.15  # 动量因子权重
        }

        self.logger.info("机会筛选AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行机会筛选分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - stock_universe: 股票池列表（可选）
                - screening_criteria: 筛选标准（可选）
                - top_n: 返回前N个机会（默认10）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        stock_universe = kwargs.get("stock_universe", [])
        screening_criteria = kwargs.get("screening_criteria", {})
        top_n = kwargs.get("top_n", 10)

        self.logger.info(
            f"开始机会筛选分析",
            extra={
                "stock_code": stock_code,
                "universe_size": len(stock_universe),
                "top_n": top_n
            }
        )

        # ========== 1. 多因子筛选 ==========
        multi_factor_scores = await self._multi_factor_screening(
            stock_code,
            stock_universe
        )

        # ========== 2. 行业轮动分析 ==========
        sector_rotation = await self._analyze_sector_rotation(
            stock_code
        )

        # ========== 3. 市场热点识别 ==========
        hot_spots = await self._identify_market_hot_spots(
            stock_code
        )

        # ========== 4. 综合评分排名 ==========
        ranked_opportunities = self._rank_opportunities(
            multi_factor_scores,
            sector_rotation,
            hot_spots,
            top_n
        )

        # ========== 5. 生成推荐理由 ==========
        recommendations = self._generate_recommendations(
            ranked_opportunities
        )

        # ========== 6. 风险提示 ==========
        risks = self._identify_risks(
            ranked_opportunities,
            sector_rotation
        )

        # ========== 7. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,
            "screening_criteria": screening_criteria,
            "top_n": top_n,

            # 多因子评分
            "multi_factor_scores": multi_factor_scores,

            # 行业轮动
            "sector_rotation": sector_rotation,

            # 市场热点
            "hot_spots": hot_spots,

            # 排名机会
            "ranked_opportunities": ranked_opportunities,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        # 生成核心结论
        conclusion = self._generate_conclusion(
            ranked_opportunities,
            hot_spots
        )

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=conclusion,
            confidence=0.82,
            details=details,
            risks=risks,
            recommendations=recommendations
        )

        self.logger.info(
            f"机会筛选分析完成",
            extra={
                "stock_code": stock_code,
                "opportunities_found": len(ranked_opportunities),
                "top_opportunity": ranked_opportunities[0]["stock_code"] if ranked_opportunities else None
            }
        )

        return result

    # ========== 核心筛选方法 ==========

    async def _multi_factor_screening(
        self,
        stock_code: str,
        stock_universe: List[str]
    ) -> Dict[str, Any]:
        """
        多因子筛选

        基于价值、成长、质量、动量四个因子进行综合评分
        """
        # TODO: 接入真实数据
        # 当前使用模拟数据

        # 如果没有提供股票池，使用示例股票
        if not stock_universe:
            stock_universe = [
                "600519",  # 贵州茅台
                "000858",  # 五粮液
                "600036",  # 招商银行
                "000001",  # 平安银行
                "601318",  # 中国平安
                "000333",  # 美的集团
                "600276",  # 恒瑞医药
                "300750",  # 宁德时代
                "688981",  # 中芯国际
                "601012"   # 隆基绿能
            ]

        # 并行计算各股票的因子得分
        scoring_tasks = [
            self._calculate_stock_score(stock)
            for stock in stock_universe
        ]

        stock_scores = await asyncio.gather(*scoring_tasks)

        # 按综合得分排序
        stock_scores.sort(key=lambda x: x["total_score"], reverse=True)

        # 统计信息
        scores_list = [s["total_score"] for s in stock_scores]
        avg_score = sum(scores_list) / len(scores_list)
        median_score = scores_list[len(scores_list) // 2]

        return {
            "stock_scores": stock_scores[:20],  # 返回前20名
            "statistics": {
                "total_stocks": len(stock_universe),
                "avg_score": round(avg_score, 2),
                "median_score": round(median_score, 2),
                "highest_score": round(scores_list[0], 2),
                "lowest_score": round(scores_list[-1], 2)
            },
            "factor_weights": self.factor_weights,
            "description": "基于价值、成长、质量、动量四因子综合评分"
        }

    async def _calculate_stock_score(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        计算单只股票的综合得分

        Returns:
            股票评分信息
        """
        # TODO: 接入真实财务和市场数据
        # 当前使用模拟数据

        # 计算各因子得分（0-100分）
        value_score = self._calculate_value_factor(stock_code)
        growth_score = self._calculate_growth_factor(stock_code)
        quality_score = self._calculate_quality_factor(stock_code)
        momentum_score = self._calculate_momentum_factor(stock_code)

        # 加权计算综合得分
        total_score = (
            value_score * self.factor_weights["value"] +
            growth_score * self.factor_weights["growth"] +
            quality_score * self.factor_weights["quality"] +
            momentum_score * self.factor_weights["momentum"]
        )

        return {
            "stock_code": stock_code,
            "stock_name": f"股票{stock_code}",  # TODO: 获取真实名称
            "total_score": round(total_score, 2),
            "factor_scores": {
                "value": round(value_score, 2),
                "growth": round(growth_score, 2),
                "quality": round(quality_score, 2),
                "momentum": round(momentum_score, 2)
            },
            "rating": self._get_rating(total_score)
        }

    def _calculate_value_factor(self, stock_code: str) -> float:
        """
        计算价值因子得分

        基于PE、PB、PS、股息率等指标
        """
        # TODO: 接入真实数据
        # 模拟数据
        pe_ratio = 15.0  # 市盈率
        pb_ratio = 2.5  # 市净率
        ps_ratio = 3.0  # 市销率
        dividend_yield = 0.03  # 股息率

        # 价值得分计算（越低越好的指标取倒数）
        pe_score = min(100, max(0, 100 - pe_ratio))  # PE越低越好
        pb_score = min(100, max(0, 100 - pb_ratio * 20))  # PB越低越好
        ps_score = min(100, max(0, 100 - ps_ratio * 15))  # PS越低越好
        dividend_score = min(100, dividend_yield * 2000)  # 股息率越高越好

        # 加权平均
        value_score = (
            pe_score * 0.30 +
            pb_score * 0.25 +
            ps_score * 0.25 +
            dividend_score * 0.20
        )

        return value_score

    def _calculate_growth_factor(self, stock_code: str) -> float:
        """
        计算成长因子得分

        基于营收增长、利润增长、ROE等指标
        """
        # TODO: 接入真实数据
        revenue_growth = 0.20  # 营收增长率 20%
        profit_growth = 0.25  # 利润增长率 25%
        roe = 0.18  # ROE 18%

        # 成长得分计算
        revenue_score = min(100, revenue_growth * 300)  # 营收增长
        profit_score = min(100, profit_growth * 300)  # 利润增长
        roe_score = min(100, roe * 400)  # ROE

        # 加权平均
        growth_score = (
            revenue_score * 0.35 +
            profit_score * 0.40 +
            roe_score * 0.25
        )

        return growth_score

    def _calculate_quality_factor(self, stock_code: str) -> float:
        """
        计算质量因子得分

        基于ROE、ROA、资产负债率、现金流等指标
        """
        # TODO: 接入真实数据
        roe = 0.18  # ROE
        roa = 0.08  # ROA
        debt_ratio = 0.40  # 资产负债率
        cash_ratio = 0.15  # 现金比率

        # 质量得分计算
        roe_score = min(100, roe * 400)
        roa_score = min(100, roa * 800)
        debt_score = min(100, (1 - debt_ratio) * 100)  # 负债越低越好
        cash_score = min(100, cash_ratio * 500)

        # 加权平均
        quality_score = (
            roe_score * 0.30 +
            roa_score * 0.25 +
            debt_score * 0.25 +
            cash_score * 0.20
        )

        return quality_score

    def _calculate_momentum_factor(self, stock_code: str) -> float:
        """
        计算动量因子得分

        基于近期股价表现、相对强弱等指标
        """
        # TODO: 接入真实数据
        return_1m = 0.05  # 1个月收益
        return_3m = 0.12  # 3个月收益
        return_6m = 0.20  # 6个月收益
        relative_strength = 1.2  # 相对强弱

        # 动量得分计算
        momentum_1m_score = min(100, max(0, return_1m * 500))
        momentum_3m_score = min(100, max(0, return_3m * 300))
        momentum_6m_score = min(100, max(0, return_6m * 200))
        rs_score = min(100, max(0, (relative_strength - 1) * 200))

        # 加权平均
        momentum_score = (
            momentum_1m_score * 0.20 +
            momentum_3m_score * 0.30 +
            momentum_6m_score * 0.30 +
            rs_score * 0.20
        )

        return momentum_score

    async def _analyze_sector_rotation(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        行业轮动分析

        识别行业轮动机会和趋势
        """
        # TODO: 接入真实行业数据
        # 当前使用模拟数据

        # 行业轮动信号
        sector_signals = [
            {
                "sector": "科技",
                "signal": "增持",
                "strength": 0.85,
                "reason": "政策支持+业绩增长+资金流入"
            },
            {
                "sector": "新能源",
                "signal": "增持",
                "strength": 0.78,
                "reason": "产业景气度提升+需求旺盛"
            },
            {
                "sector": "消费",
                "signal": "中性",
                "strength": 0.60,
                "reason": "复苏缓慢+业绩平稳"
            },
            {
                "sector": "金融",
                "signal": "减持",
                "strength": 0.45,
                "reason": "利率下行+资产质量压力"
            },
            {
                "sector": "地产",
                "signal": "减持",
                "strength": 0.35,
                "reason": "政策调控+需求疲软"
            }
        ]

        # 识别轮动机会
        rotation_opportunities = [
            s["sector"] for s in sector_signals
            if s["signal"] == "增持" and s["strength"] > 0.70
        ]

        # 轮动趋势
        if len(rotation_opportunities) >= 2:
            rotation_trend = "成长风格占优"
        elif len(rotation_opportunities) == 1:
            rotation_trend = "结构性机会"
        else:
            rotation_trend = "防御为主"

        return {
            "sector_signals": sector_signals,
            "rotation_opportunities": rotation_opportunities,
            "rotation_trend": rotation_trend,
            "key_message": f"重点关注{', '.join(rotation_opportunities)}板块",
            "description": "基于行业景气度、政策面、资金流的轮动分析"
        }

    async def _identify_market_hot_spots(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        识别市场热点

        发现当前市场热点和投资机会
        """
        # TODO: 接入真实市场数据
        # 当前使用模拟数据

        # 市场热点主题
        hot_themes = [
            {
                "theme": "人工智能",
                "heat_level": 95,
                "related_stocks": ["300750", "688981"],
                "description": "AI技术应用加速，算力需求爆发",
                "risk": "估值偏高，需注意回调风险"
            },
            {
                "theme": "新能源汽车",
                "heat_level": 85,
                "related_stocks": ["002594", "601012"],
                "description": "渗透率持续提升，产业链景气度高",
                "risk": "竞争加剧，政策退坡风险"
            },
            {
                "theme": "半导体",
                "heat_level": 80,
                "related_stocks": ["688981", "600584"],
                "description": "国产替代加速，政策大力支持",
                "风险": "技术突破不及预期"
            },
            {
                "theme": "储能",
                "heat_level": 75,
                "related_stocks": ["300750", "688111"],
                "description": "新能源发展配套，需求快速增长",
                "risk": "产能过剩风险"
            }
        ]

        # 按热度排序
        hot_themes.sort(key=lambda x: x["heat_level"], reverse=True)

        # 生成热点总结
        top_themes = hot_themes[:3]
        hot_spots_summary = (
            f"当前市场热点集中在{top_themes[0]['theme']}、"
            f"{top_themes[1]['theme']}、{top_themes[2]['theme']}等主题"
        )

        return {
            "hot_themes": hot_themes,
            "hot_spots_summary": hot_spots_summary,
            "suggested_focus": top_themes[0]["theme"],
            "description": "基于市场情绪、资金流向、政策导向的热点识别"
        }

    def _rank_opportunities(
        self,
        multi_factor_scores: Dict[str, Any],
        sector_rotation: Dict[str, Any],
        hot_spots: Dict[str, Any],
        top_n: int
    ) -> List[Dict[str, Any]]:
        """
        综合排名投资机会

        结合多因子评分、行业轮动、市场热点进行综合排名
        """
        stock_scores = multi_factor_scores["stock_scores"]

        # 为每个股票添加综合评分
        for stock in stock_scores:
            # 基础得分：多因子得分
            base_score = stock["total_score"]

            # 行业轮动加成
            # TODO: 获取股票所属行业，这里简化处理
            sector_bonus = 5.0  # 如果股票属于增持行业，加5分

            # 热点主题加成
            # TODO: 判断股票是否属于热点主题，这里简化处理
            hot_spot_bonus = 3.0  # 如果股票属于热点主题，加3分

            # 计算最终得分
            final_score = base_score + sector_bonus + hot_spot_bonus

            stock["final_score"] = round(final_score, 2)
            stock["investment_suggestion"] = self._get_investment_suggestion(final_score)

        # 按最终得分排序
        stock_scores.sort(key=lambda x: x["final_score"], reverse=True)

        # 返回前N个机会
        top_opportunities = stock_scores[:top_n]

        # 为每个机会添加推荐理由
        for opp in top_opportunities:
            opp["reasons"] = self._generate_opportunity_reasons(opp)

        return top_opportunities

    def _generate_opportunity_reasons(
        self,
        opportunity: Dict[str, Any]
    ) -> List[str]:
        """生成机会推荐理由"""
        reasons = []

        # 综合评分
        final_score = opportunity["final_score"]
        reasons.append(f"综合评分{final_score:.1f}分，表现优异")

        # 因子亮点
        factor_scores = opportunity["factor_scores"]

        if factor_scores["value"] > 70:
            reasons.append(f"价值得分{factor_scores['value']:.1f}，估值合理")

        if factor_scores["growth"] > 70:
            reasons.append(f"成长得分{factor_scores['growth']:.1f}，成长性强")

        if factor_scores["quality"] > 70:
            reasons.append(f"质量得分{factor_scores['quality']:.1f}，基本面优秀")

        if factor_scores["momentum"] > 70:
            reasons.append(f"动量得分{factor_scores['momentum']:.1f}，近期表现强势")

        # 评级
        rating = opportunity["rating"]
        if rating in ["强烈推荐", "推荐"]:
            reasons.append(f"投资评级【{rating}】，值得重点关注")

        return reasons

    def _generate_recommendations(
        self,
        ranked_opportunities: List[Dict[str, Any]]
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []

        if not ranked_opportunities:
            recommendations.append("当前未发现明显投资机会，建议继续观望")
            return recommendations

        # 总体建议
        top_opportunity = ranked_opportunities[0]
        recommendations.append(
            f"发现{len(ranked_opportunities)}个投资机会，"
            f"首选{top_opportunity['stock_name']}（{top_opportunity['stock_code']}）"
        )

        # 配置建议
        if len(ranked_opportunities) >= 3:
            recommendations.append(
                "建议从前3名中分散配置，降低单一股票风险"
            )

        # 风险提示
        recommendations.append("建议分批买入，控制单一标的仓位不超过10%")

        # 后续跟踪
        recommendations.append("买入后建议持续跟踪基本面变化和行业动态")

        return recommendations

    def _identify_risks(
        self,
        ranked_opportunities: List[Dict[str, Any]],
        sector_rotation: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        if not ranked_opportunities:
            risks.append("当前市场缺乏明显投资机会")
            return risks

        # 估值风险
        top_opportunity = ranked_opportunities[0]
        value_score = top_opportunity["factor_scores"]["value"]

        if value_score < 50:
            risks.append("首选标的估值偏高，需注意回调风险")

        # 集中度风险
        if len(ranked_opportunities) < 5:
            risks.append("筛选结果较少，建议扩大筛选范围")

        # 行业风险
        rotation_trend = sector_rotation["rotation_trend"]
        if "防御" in rotation_trend:
            risks.append("当前市场偏向防御，需注意成长股波动风险")

        # 热点风险
        risks.append("热点主题轮动较快，需注意及时止盈止损")

        # 市场风险
        risks.append("股市系统性风险可能影响个股表现")

        return risks

    # ========== 辅助方法 ==========

    def _get_rating(self, score: float) -> str:
        """根据得分获取评级"""
        if score >= 85:
            return "强烈推荐"
        elif score >= 75:
            return "推荐"
        elif score >= 65:
            return "中性"
        elif score >= 55:
            return "观望"
        else:
            return "不推荐"

    def _get_investment_suggestion(self, score: float) -> str:
        """根据得分获取投资建议"""
        if score >= 85:
            return "积极配置"
        elif score >= 75:
            return "重点配置"
        elif score >= 65:
            return "适当配置"
        elif score >= 55:
            return "少量配置"
        else:
            return "暂不配置"

    def _generate_conclusion(
        self,
        ranked_opportunities: List[Dict[str, Any]],
        hot_spots: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        if not ranked_opportunities:
            return "当前市场投资机会较少，建议耐心等待"

        top_opportunity = ranked_opportunities[0]
        hot_spot = hot_spots["suggested_focus"]

        return (
            f"筛选出{len(ranked_opportunities)}个优质机会，"
            f"首选{top_opportunity['stock_name']}（评分{top_opportunity['final_score']:.1f}），"
            f"建议重点关注{hot_spot}板块"
        )


# 便捷函数
async def analyze_opportunity_screening(
    stock_code: str,
    stock_universe: Optional[List[str]] = None,
    screening_criteria: Optional[Dict[str, Any]] = None,
    top_n: int = 10
) -> AnalysisResult:
    """
    机会筛选分析（便捷函数）

    Args:
        stock_code: 股票代码
        stock_universe: 股票池
        screening_criteria: 筛选标准
        top_n: 返回前N个机会

    Returns:
        分析结果
    """
    ai = OpportunityScreeningAI()
    return await ai.analyze(
        stock_code,
        stock_universe=stock_universe,
        screening_criteria=screening_criteria,
        top_n=top_n
    )

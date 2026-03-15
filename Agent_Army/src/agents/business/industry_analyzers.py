"""
Agent Army - 产业分析军团
4个AI: 产业链分析、竞争格局、政策解读、价值评估
"""

from typing import Any, Dict, Optional, List
from ...core.base_agent import AgentCapability, AgentTool
from ...models.analysis_models import IndustryAnalysisResult
from .base_business_agent import BusinessAgent
from ...core.utils.cache import get_global_cache_manager


class IndustryChainAnalyzer(BusinessAgent):
    """产业链分析AI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="产业链分析AI",
            role="分析产业链上下游关系",
            corps="industry_analysis",
            analysis_type="chain",
            capabilities=[
                AgentCapability(name="upstream_analysis", description="上游分析", enabled=True),
                AgentCapability(name="downstream_analysis", description="下游分析", enabled=True),
                AgentCapability(name="value_chain", description="价值链分析", enabled=True),
            ],
            tools=[
                AgentTool(name="chain_mapper", description="产业链图谱", enabled=True),
            ],
            config=config
        )

        # ⭐ Phase 3: 初始化缓存
        self.cache = get_global_cache_manager().get("industry_analysis")

    def _calculate_industry_score(self, industry_data: Dict[str, Any]) -> float:
        """
        计算行业评分

        评分维度：
        - 行业规模（20%）
        - 行业增长率（30%）
        - 市场份额（20%）
        - 行业排名（30%）
        """
        # 1. 行业规模评分（越大越好）
        size = industry_data.get("industry_size", 0.0)
        size_score = min(size / 10000.0 * 20, 20)  # 最大20分

        # 2. 行业增长率评分（越高越好）
        growth = industry_data.get("industry_growth", 0.0)
        growth_score = min(abs(growth) / 20.0 * 30, 30)  # 最大30分

        # 3. 市场份额评分（越大越好）
        market_share = industry_data.get("market_share", 0.0)
        share_score = min(market_share / 10.0 * 20, 20)  # 最大20分

        # 4. 行业排名评分（越小越好，前10名得满分）
        rank = industry_data.get("industry_rank", 999)
        if rank <= 10:
            rank_score = 30
        elif rank <= 50:
            rank_score = 20
        elif rank <= 100:
            rank_score = 10
        else:
            rank_score = 5

        total_score = size_score + growth_score + share_score + rank_score
        return round(total_score, 2)

    def _calculate_confidence(self, industry_data: Dict[str, Any]) -> float:
        """
        计算置信度

        置信度基于：
        - 数据完整性
        - 数据来源可靠性
        """
        confidence = 0.7  # 基础置信度

        # 如果有行业名称，增加置信度
        if industry_data.get("industry_name") and industry_data["industry_name"] != "未知":
            confidence += 0.1

        # 如果有行业规模，增加置信度
        if industry_data.get("industry_size", 0) > 0:
            confidence += 0.1

        # 如果有行业排名，增加置信度
        if industry_data.get("industry_rank", 0) > 0:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_summary(self, industry_data: Dict[str, Any]) -> str:
        """
        生成分析摘要

        Args:
            industry_data: 行业数据

        Returns:
            摘要文本
        """
        industry_name = industry_data.get("industry_name", "未知行业")
        cycle = industry_data.get("industry_cycle", "未知")
        growth = industry_data.get("industry_growth", 0.0)
        rank = industry_data.get("industry_rank", 0)

        summary_parts = []

        # 行业和周期
        summary_parts.append(f"所属{industry_name}行业，处于{cycle}阶段")

        # 增长情况
        if growth > 10:
            summary_parts.append(f"行业增长率达{growth:.1f}%，处于快速增长期")
        elif growth > 0:
            summary_parts.append(f"行业增长率{growth:.1f}%，平稳增长")
        else:
            summary_parts.append(f"行业增长率为{growth:.1f}%，增长放缓")

        # 行业地位
        if rank > 0 and rank <= 10:
            summary_parts.append(f"在行业内排名第{rank}，处于领先地位")
        elif rank > 0 and rank <= 50:
            summary_parts.append(f"在行业内排名第{rank}，具有一定地位")
        elif rank > 0:
            summary_parts.append(f"在行业内排名第{rank}")

        return "；".join(summary_parts) + "。"

    def _identify_growth_driver(self, industry_data: Dict[str, Any]) -> List[str]:
        """
        识别成长驱动因素

        Args:
            industry_data: 行业数据

        Returns:
            驱动因素列表
        """
        drivers = []

        # 基于行业周期判断
        cycle = industry_data.get("industry_cycle", "")
        if cycle == "成长期":
            drivers.append("行业处于快速成长期")

        # 基于增长率判断
        growth = industry_data.get("industry_growth", 0.0)
        if growth > 15:
            drivers.append("市场需求强劲")
            drivers.append("行业增长率高")

        # 基于行业名称判断
        industry_name = industry_data.get("industry_name", "")
        if any(keyword in industry_name for keyword in ["新能源", "半导体", "生物医药", "人工智能"]):
            drivers.append("国家政策支持")
            drivers.append("技术创新驱动")

        # 基于市场份额判断
        market_share = industry_data.get("market_share", 0.0)
        if market_share > 10:
            drivers.append("市场地位领先")

        return drivers if drivers else ["常规增长因素"]

    def _identify_risks(self, industry_data: Dict[str, Any]) -> List[str]:
        """
        识别风险因素

        Args:
            industry_data: 行业数据

        Returns:
            风险因素列表
        """
        risks = []

        # 基于行业周期判断
        cycle = industry_data.get("industry_cycle", "")
        if cycle == "衰退期":
            risks.append("行业处于衰退期")
        elif cycle == "成熟期":
            risks.append("行业增长放缓")

        # 基于增长率判断
        growth = industry_data.get("industry_growth", 0.0)
        if growth < 0:
            risks.append("行业负增长")
        elif growth < 5:
            risks.append("行业增长乏力")

        # 基于市场份额判断
        market_share = industry_data.get("market_share", 0.0)
        if market_share < 1:
            risks.append("市场份额较低")
            risks.append("竞争压力大")

        # 基于行业排名判断
        rank = industry_data.get("industry_rank", 0)
        if rank > 100:
            risks.append("行业地位不突出")

        return risks if risks else ["常规市场风险"]

    async def _do_analysis(self, stock_code: str, **kwargs) -> IndustryAnalysisResult:
        """实际的分析逻辑（内部方法）"""
        self.logger.info(f"执行产业链分析: {stock_code}")

        try:
            # ⭐ Phase 3: 使用东方财富API获取真实数据
            from ...core.tools.data_source.east_money_scraper import EastMoneyScraper

            scraper = EastMoneyScraper()
            industry_data = await scraper.get_industry_info(stock_code)

            # 分析产业链数据
            score = self._calculate_industry_score(industry_data)
            confidence = self._calculate_confidence(industry_data)
            summary = self._generate_summary(industry_data)

            # 提取产业链信息
            chain = industry_data.get("industry_chain", {})
            growth_driver = self._identify_growth_driver(industry_data)
            risk_factors = self._identify_risks(industry_data)

            self.logger.info(f"产业链分析完成: {industry_data['industry_name']}, 评分: {score}")

            return IndustryAnalysisResult(
                stock_code=stock_code,
                stock_name=industry_data.get("stock_name", ""),
                score=score,
                confidence=confidence,
                summary=summary,
                industry_name=industry_data.get("industry_name", ""),
                industry_size=industry_data.get("industry_size", 0.0),
                industry_growth=industry_data.get("industry_growth", 0.0),
                market_share=industry_data.get("market_share", 0.0),
                industry_rank=industry_data.get("industry_rank", 0),
                industry_cycle=industry_data.get("industry_cycle", ""),
                growth_driver=growth_driver,
                risk_factors=risk_factors
            )

        except Exception as e:
            self.logger.error(f"产业链分析失败: {str(e)}")
            # 降级方案：返回默认值
            return IndustryAnalysisResult(
                stock_code=stock_code,
                stock_name="未知",
                score=50.0,
                confidence=0.0,
                summary=f"数据获取失败: {str(e)}",
                industry_name="未知",
                industry_size=0.0,
                industry_growth=0.0,
                market_share=0.0,
                industry_rank=0,
                industry_cycle="未知",
                growth_driver=[],
                risk_factors=["数据获取失败"]
            )

    async def analyze(self, stock_code: str, **kwargs) -> IndustryAnalysisResult:
        """产业链分析（带缓存）"""
        self.logger.info(f"产业链分析: {stock_code}")

        # ⭐ Phase 3: 使用缓存
        return await self.cache.get_or_compute_async(
            self._do_analysis,
            stock_code,
            **kwargs
        )


class CompetitionAnalyzer(BusinessAgent):
    """竞争格局AI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="竞争格局AI",
            role="分析行业竞争格局",
            corps="industry_analysis",
            analysis_type="competition",
            capabilities=[
                AgentCapability(name="competitor_analysis", description="竞争对手分析", enabled=True),
                AgentCapability(name="market_share_analysis", description="市场份额分析", enabled=True),
            ],
            tools=[AgentTool(name="competitor_tracker", description="竞争者追踪", enabled=True)],
            config=config
        )

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """竞争格局分析"""
        self.logger.info(f"竞争格局分析: {stock_code}")
        # TODO: Phase 1实现
        return {
            "stock_code": stock_code,
            "score": 70.0,
            "competitive_position": "行业前三",
            "market_share": 5.0,
            "key_competitors": ["竞品A", "竞品B"],
            "competitive_advantages": ["技术领先", "成本优势"]
        }


class PolicyAnalyzer(BusinessAgent):
    """政策解读AI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="政策解读AI",
            role="解读行业政策影响",
            corps="industry_analysis",
            analysis_type="policy",
            capabilities=[
                AgentCapability(name="policy_tracking", description="政策追踪", enabled=True),
                AgentCapability(name="impact_analysis", description="影响分析", enabled=True),
            ],
            tools=[AgentTool(name="policy_monitor", description="政策监控", enabled=True)],
            config=config
        )

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """政策影响分析"""
        self.logger.info(f"政策分析: {stock_code}")
        # TODO: Phase 1实现
        return {
            "stock_code": stock_code,
            "score": 80.0,
            "policy_environment": "利好",
            "key_policies": ["政策A", "政策B"],
            "impact_assessment": "正面影响"
        }


class IndustryValueEvaluator(BusinessAgent):
    """行业价值评估AI"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="行业价值评估AI",
            role="评估行业投资价值",
            corps="industry_analysis",
            analysis_type="value",
            capabilities=[
                AgentCapability(name="industry_valuation", description="行业估值", enabled=True),
                AgentCapability(name="growth_potential", description="成长潜力", enabled=True),
            ],
            tools=[AgentTool(name="valuation_tool", description="估值工具", enabled=True)],
            config=config
        )

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """行业价值评估"""
        self.logger.info(f"行业价值评估: {stock_code}")
        # TODO: Phase 1实现
        return {
            "stock_code": stock_code,
            "score": 85.0,
            "industry_rating": "优秀",
            "investment_value": "高",
            "growth_outlook": "看好"
        }

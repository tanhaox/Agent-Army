"""
政策影响AI - Policy Impact AI

产业分析军团成员

职责：
- 分析政策对行业的影响
- 使用NewsTool获取政策新闻
- 使用LLMTool进行政策分析
- 评估政策利好/利空程度
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source.news_tool import NewsTool
from src.core.tools.ai_service.llm_tool import LLMTool


class PolicyEvent(BaseModel):
    """政策事件"""
    title: str  # 政策标题
    date: str  # 发布日期
    impact_type: str  # positive/negative/neutral
    impact_score: float = Field(ge=0.0, le=1.0)  # 影响程度 0-1
    description: str  # 政策描述


class PolicyImpactResult(BaseModel):
    """政策影响分析结果"""
    industry: str  # 行业名称
    stock_code: str  # 股票代码
    policy_events: List[PolicyEvent]  # 政策事件列表
    overall_impact: str  # positive/negative/neutral
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度
    timestamp: str  # 分析时间


class PolicyImpactAI(BusinessAgent):
    """
    政策影响AI - 产业分析军团成员

    职责：
    - 分析政策对行业的影响
    - 使用NewsTool获取政策新闻
    - 使用LLMTool进行政策分析
    - 评估政策利好/利空程度

    使用工具：
    - NewsTool (政策新闻)
    - LLMTool (政策分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.news_tool = NewsTool(config)
        self.llm_tool = LLMTool(config)

        super().__init__(
            name="政策影响AI",
            role="分析政策对行业的影响",
            corps="industry_analysis",
            analysis_type="policy_impact",
            capabilities=[
                AgentCapability(
                    name="policy_identification",
                    description="政策识别",
                    enabled=True
                ),
                AgentCapability(
                    name="impact_assessment",
                    description="影响评估",
                    enabled=True
                ),
                AgentCapability(
                    name="sentiment_analysis",
                    description="情感分析",
                    enabled=True
                )
            ],
            tools=[
                AgentTool(
                    name="news_tool",
                    description="政策新闻工具",
                    enabled=True
                ),
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    enabled=True
                )
            ],
            config=config
        )

        self.logger.info("政策影响AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        政策影响分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - industry: 行业名称（可选）
                - days: 查询天数（默认7天）

        Returns:
            政策影响分析结果
        """
        self.logger.info(f"开始政策影响分析: {stock_code}")

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取参数
        industry = kwargs.get("industry", self._get_industry(stock_code))
        days = kwargs.get("days", 7)

        # ========== 1. 获取政策新闻 ==========
        self.logger.info(f"获取最近{days}天的政策新闻...")
        news_list = await self.news_tool.fetch_news(
            stock_code=stock_code,
            days=days
        )

        # ========== 2. 分析政策影响 ==========
        self.logger.info(f"分析{len(news_list)}条新闻的政策影响...")
        policy_events = []

        for news in news_list:
            # 分析单条新闻的政策影响
            event = await self._analyze_policy_event(news, industry)
            if event:
                policy_events.append(event)

        # ========== 3. 计算整体影响 ==========
        overall_impact, confidence = self._calculate_overall_impact(policy_events)

        # ========== 4. 构建返回结果 ==========
        result = PolicyImpactResult(
            industry=industry,
            stock_code=stock_code,
            policy_events=policy_events,
            overall_impact=overall_impact,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )

        self.logger.info(
            f"政策影响分析完成: {stock_code}, "
            f"整体影响: {overall_impact}, "
            f"置信度: {confidence:.2f}, "
            f"政策事件: {len(policy_events)}个"
        )

        # 返回字典格式
        return result.dict()

    async def _analyze_policy_event(self, news: Dict[str, Any], industry: str) -> Optional[PolicyEvent]:
        """
        分析单条新闻的政策影响

        Args:
            news: 新闻数据
            industry: 行业名称

        Returns:
            政策事件
        """
        try:
            title = news.get("title", "")
            content = news.get("content", "")
            published_at = news.get("published_at", "")

            # 构建分析提示词
            prompt = f"""
分析以下新闻的政策影响：

行业：{industry}
标题：{title}
内容：{content}

请判断：
1. 这是利好政策还是利空政策？
2. 影响程度有多大？（0-1之间的分数）

返回JSON格式：
{{
    "impact_type": "positive/negative/neutral",
    "impact_score": 0.8,
    "description": "政策影响的简要描述"
}}
"""

            # 调用LLM分析
            response = await self.llm_tool.chat(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )

            # 解析LLM响应
            import json
            try:
                analysis = json.loads(response)

                # 创建政策事件
                event = PolicyEvent(
                    title=title,
                    date=published_at,
                    impact_type=analysis.get("impact_type", "neutral"),
                    impact_score=analysis.get("impact_score", 0.5),
                    description=analysis.get("description", content[:100])
                )

                self.logger.info(
                    f"政策事件分析完成: {title[:20]}..., "
                    f"影响: {event.impact_type}, "
                    f"评分: {event.impact_score:.2f}"
                )

                return event

            except json.JSONDecodeError:
                # 如果LLM返回的不是JSON，使用简单的关键词匹配
                self.logger.warning(f"LLM响应解析失败，使用关键词匹配")
                return await self._fallback_analysis(title, content, published_at)

        except Exception as e:
            self.logger.error(f"政策事件分析失败: {str(e)}，使用备用分析方法")
            # 即使出错也尝试使用备用分析方法
            return await self._fallback_analysis(title, content, published_at)

    async def _fallback_analysis(
        self,
        title: str,
        content: str,
        published_at: str
    ) -> Optional[PolicyEvent]:
        """
        备用分析方法（关键词匹配）

        Args:
            title: 新闻标题
            content: 新闻内容
            published_at: 发布时间

        Returns:
            政策事件
        """
        # 正面关键词
        positive_keywords = ["支持", "鼓励", "补贴", "利好", "优惠", "减税", "促进"]
        # 负面关键词
        negative_keywords = ["限制", "禁止", "收紧", "处罚", "监管", "规范"]

        # 统计关键词
        text = title + content
        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        # 判断影响类型
        if positive_count > negative_count:
            impact_type = "positive"
            impact_score = min(1.0, 0.6 + positive_count * 0.1)
        elif negative_count > positive_count:
            impact_type = "negative"
            impact_score = min(1.0, 0.6 + negative_count * 0.1)
        else:
            impact_type = "neutral"
            impact_score = 0.5

        return PolicyEvent(
            title=title,
            date=published_at,
            impact_type=impact_type,
            impact_score=impact_score,
            description=content[:100]
        )

    def _calculate_overall_impact(self, policy_events: List[PolicyEvent]) -> tuple:
        """
        计算整体政策影响

        Args:
            policy_events: 政策事件列表

        Returns:
            (整体影响类型, 置信度)
        """
        if not policy_events:
            return "neutral", 0.0

        # 统计各类政策数量
        positive_count = sum(1 for e in policy_events if e.impact_type == "positive")
        negative_count = sum(1 for e in policy_events if e.impact_type == "negative")
        neutral_count = sum(1 for e in policy_events if e.impact_type == "neutral")

        total = len(policy_events)

        # 计算加权影响分数
        positive_score = sum(e.impact_score for e in policy_events if e.impact_type == "positive")
        negative_score = sum(e.impact_score for e in policy_events if e.impact_type == "negative")

        # 判断整体影响
        if positive_count / total >= 0.6:
            overall_impact = "positive"
            confidence = positive_score / (positive_count + 1) if positive_count > 0 else 0.5
        elif negative_count / total >= 0.6:
            overall_impact = "negative"
            confidence = negative_score / (negative_count + 1) if negative_count > 0 else 0.5
        else:
            overall_impact = "neutral"
            confidence = 1.0 - abs(positive_count - negative_count) / total

        # 置信度范围限制
        confidence = max(0.3, min(1.0, confidence))

        return overall_impact, confidence

    def _get_industry(self, stock_code: str) -> str:
        """
        获取股票所属行业

        Args:
            stock_code: 股票代码

        Returns:
            行业名称
        """
        # 简单的行业映射（实际应该从数据库获取）
        industry_map = {
            "600519": "白酒",
            "000858": "白酒",
            "000333": "家电",
            "600036": "银行",
            "600276": "医药",
            "300750": "新能源"
        }

        return industry_map.get(stock_code, "未知行业")


# ========== 便捷函数 ==========

async def analyze_policy_impact(stock_code: str, **kwargs) -> Dict[str, Any]:
    """
    分析政策影响（便捷函数）

    Args:
        stock_code: 股票代码
        **kwargs: 其他参数

    Returns:
        政策影响分析结果
    """
    agent = PolicyImpactAI()
    return await agent.analyze(stock_code, **kwargs)

"""
新闻监控AI - 热点捕捉军团 (1/4)

职责：
- 监控财经新闻
- 识别关键事件
- 提取关键信息
- 生成事件报告
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import random

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool


class NewsMonitor(BusinessAgent):
    """
    新闻监控AI

    热点捕捉军团 (1/4)
    负责实时监控财经新闻，识别关键事件
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="新闻监控AI",
            role="监控财经新闻，识别关键事件",
            corps="hot_spot",
            analysis_type="news_monitoring",
            capabilities=[
                AgentCapability(
                    name="news_fetching",
                    description="获取新闻数据",
                    input_type="stock_code",
                    output_type="news_list"
                ),
                AgentCapability(
                    name="event_extraction",
                    description="提取关键事件",
                    input_type="news_content",
                    output_type="event_list"
                ),
                AgentCapability(
                    name="sentiment_analysis",
                    description="情感分析",
                    input_type="event_text",
                    output_type="sentiment_score"
                ),
                AgentCapability(
                    name="impact_assessment",
                    description="影响评估",
                    input_type="event_data",
                    output_type="impact_score"
                )
            ],
            tools=[
                AgentTool(
                    name="news_api",
                    description="新闻API接口",
                    tool_type="api",
                    config={}
                ),
                AgentTool(
                    name="nlp_processor",
                    description="自然语言处理",
                    tool_type="processor",
                    config={}
                ),
                AgentTool(
                    name="event_classifier",
                    description="事件分类器",
                    tool_type="classifier",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("新闻监控AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        分析股票相关新闻

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - days: 监控天数（默认7天）
                - event_types: 事件类型过滤（可选）

        Returns:
            新闻分析结果
        """
        self.logger.info(f"开始新闻监控分析", extra={"stock_code": stock_code})

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取监控天数
        days = kwargs.get("days", 7)
        event_types = kwargs.get("event_types", None)

        # 1. 获取新闻数据
        news_list = await self._fetch_news(stock_code, days)

        # 2. 提取关键事件
        events = await self._extract_events(news_list)

        # 3. 情感分析
        events = await self._analyze_sentiment(events)

        # 4. 影响评估
        events = await self._assess_impact(events)

        # 5. 过滤事件类型（如果指定）
        if event_types:
            events = [e for e in events if e["type"] in event_types]

        # 6. 生成分析结果
        result = {
            "stock_code": stock_code,
            "stock_name": self._get_stock_name(stock_code),
            "analysis_type": "news_monitoring",
            "timestamp": datetime.now().isoformat(),
            "monitoring_period": f"最近{days}天",
            "total_news": len(news_list),
            "total_events": len(events),
            "events": events,
            "summary": self._generate_summary(events),
            "warnings": self._generate_warnings(events)
        }

        self.logger.info(
            f"新闻监控分析完成",
            extra={
                "stock_code": stock_code,
                "total_news": len(news_list),
                "total_events": len(events)
            }
        )

        return result

    async def _fetch_news(self, stock_code: str, days: int) -> List[Dict]:
        """
        获取新闻数据

        Args:
            stock_code: 股票代码
            days: 监控天数

        Returns:
            新闻列表
        """
        # TODO: 接入真实新闻API
        # 当前返回示例数据

        self.logger.info(f"获取新闻数据: {stock_code}, 最近{days}天")

        # 示例新闻数据
        sample_news = [
            {
                "title": f"{self._get_stock_name(stock_code)}发布2025年年报",
                "content": "公司2025年实现营收100亿元，同比增长15%；净利润10亿元，同比增长20%。",
                "source": "东方财富",
                "published_at": "2026-03-13 10:30:00",
                "url": "https://example.com/news/1"
            },
            {
                "title": f"{self._get_stock_name(stock_code)}获机构调研",
                "content": "多家机构调研公司，关注未来发展战略和新产品布局。",
                "source": "同花顺",
                "published_at": "2026-03-12 15:20:00",
                "url": "https://example.com/news/2"
            },
            {
                "title": f"行业政策利好：{self._get_stock_name(stock_code)}受益",
                "content": "国家出台行业支持政策，鼓励技术创新和产业升级。",
                "source": "新浪财经",
                "published_at": "2026-03-11 09:15:00",
                "url": "https://example.com/news/3"
            },
            {
                "title": f"{self._get_stock_name(stock_code)}控股股东增持",
                "content": "控股股东增持公司股份100万股，显示对公司未来信心。",
                "source": "东方财富",
                "published_at": "2026-03-10 18:00:00",
                "url": "https://example.com/news/4"
            },
            {
                "title": f"券商看好{self._get_stock_name(stock_code)}前景",
                "content": "多家券商发布研报，给予买入评级，目标价上调至200元。",
                "source": "同花顺",
                "published_at": "2026-03-09 11:45:00",
                "url": "https://example.com/news/5"
            }
        ]

        return sample_news

    async def _extract_events(self, news_list: List[Dict]) -> List[Dict]:
        """
        提取关键事件

        Args:
            news_list: 新闻列表

        Returns:
            事件列表
        """
        events = []

        # 事件类型映射（关键词 → 事件类型）
        event_keywords = {
            "年报": "业绩公告",
            "季报": "业绩公告",
            "财报": "业绩公告",
            "机构调研": "机构调研",
            "调研": "机构调研",
            "政策": "政策变化",
            "支持": "政策变化",
            "增持": "股东增持",
            "减持": "股东减持",
            "券商": "券商研报",
            "研报": "券商研报",
            "目标价": "券商研报"
        }

        for news in news_list:
            # 识别事件类型
            event_type = "其他"
            for keyword, etype in event_keywords.items():
                if keyword in news["title"] or keyword in news["content"]:
                    event_type = etype
                    break

            # 提取事件
            event = {
                "type": event_type,
                "title": news["title"],
                "content": news["content"],
                "source": news["source"],
                "published_at": news["published_at"],
                "url": news["url"],
                "related_stocks": [self._get_stock_code_from_news(news)]
            }

            events.append(event)

        return events

    async def _analyze_sentiment(self, events: List[Dict]) -> List[Dict]:
        """
        情感分析

        Args:
            events: 事件列表

        Returns:
            添加情感信息的事件列表
        """
        # 情感关键词
        positive_keywords = ["利好", "增长", "增持", "看好", "买入", "支持", "获"]
        negative_keywords = ["利空", "下降", "减持", "看空", "卖出", "限制", "罚"]

        for event in events:
            # 简单的情感分析（基于关键词）
            text = event["title"] + " " + event["content"]

            positive_count = sum(1 for kw in positive_keywords if kw in text)
            negative_count = sum(1 for kw in negative_keywords if kw in text)

            if positive_count > negative_count:
                sentiment = "positive"
                sentiment_score = 0.7 + random.uniform(0, 0.3)
            elif negative_count > positive_count:
                sentiment = "negative"
                sentiment_score = 0.3 - random.uniform(0, 0.3)
            else:
                sentiment = "neutral"
                sentiment_score = 0.5

            event["sentiment"] = sentiment
            event["sentiment_score"] = round(sentiment_score, 2)

        return events

    async def _assess_impact(self, events: List[Dict]) -> List[Dict]:
        """
        影响评估

        Args:
            events: 事件列表

        Returns:
            添加影响评分的事件列表
        """
        # 事件类型权重
        event_weights = {
            "业绩公告": 9.0,
            "政策变化": 8.0,
            "股东增持": 7.0,
            "券商研报": 6.0,
            "机构调研": 5.0,
            "其他": 3.0
        }

        for event in events:
            # 基础影响分
            base_score = event_weights.get(event["type"], 3.0)

            # 情感调整
            sentiment_adjustment = 0
            if event["sentiment"] == "positive":
                sentiment_adjustment = random.uniform(0.5, 1.5)
            elif event["sentiment"] == "negative":
                sentiment_adjustment = -random.uniform(0.5, 1.5)

            # 最终影响分（0-10）
            impact_score = max(0, min(10, base_score + sentiment_adjustment))

            event["impact_score"] = round(impact_score, 1)

        # 按影响分排序
        events.sort(key=lambda e: e["impact_score"], reverse=True)

        return events

    def _generate_summary(self, events: List[Dict]) -> str:
        """生成摘要"""
        if not events:
            return "暂无重要事件"

        # 统计事件类型
        event_types = {}
        for event in events:
            etype = event["type"]
            event_types[etype] = event_types.get(etype, 0) + 1

        # 生成摘要
        summary_parts = [f"共监控到{len(events)}个关键事件"]

        for etype, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"{etype}{count}个")

        # 最高影响事件
        if events:
            top_event = events[0]
            summary_parts.append(
                f"最高影响事件: {top_event['title']} (影响分{top_event['impact_score']})"
            )

        return "，".join(summary_parts)

    def _generate_warnings(self, events: List[Dict]) -> List[str]:
        """生成警告"""
        warnings = []

        # 检查高影响负面事件
        negative_high_impact = [
            e for e in events
            if e["sentiment"] == "negative" and e["impact_score"] >= 7.0
        ]

        if negative_high_impact:
            warnings.append(f"⚠️ 发现{len(negative_high_impact)}个高影响负面事件，需重点关注")

        # 检查事件集中度
        if len(events) >= 5:
            warnings.append(f"⚠️ 事件数量较多（{len(events)}个），信息密度高，建议筛选关键事件")

        return warnings

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（示例）"""
        # TODO: 接入真实股票数据API
        stock_names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000333": "美的集团",
            "600036": "招商银行"
        }
        return stock_names.get(stock_code, "示例公司")

    def _get_stock_code_from_news(self, news: Dict) -> str:
        """从新闻中提取股票代码"""
        # 简化实现，返回固定代码
        return "600519"


# ========== 便捷函数 ==========

async def monitor_news(stock_code: str, days: int = 7) -> Dict[str, Any]:
    """
    监控股票新闻（便捷函数）

    Args:
        stock_code: 股票代码
        days: 监控天数

    Returns:
        新闻分析结果
    """
    monitor = NewsMonitor()
    return await monitor.analyze(stock_code, days=days)

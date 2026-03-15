"""
新闻监控AI - News Monitor AI

热点捕捉军团成员

职责：
1. 获取财经新闻、公告、研报
2. 提取关键事件
3. 评估影响（正面/负面/中性）
4. 关联受影响股票
5. 生成投资建议

使用工具：
- NewsTool（新闻获取）
- NLPTool（文本处理）
- LLMTool（智能分析）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import NewsTool, NLPTool, LLMTool


class NewsMonitorAI(BaseAgent, LoggerMixin):
    """
    新闻监控AI - 热点捕捉军团成员

    核心能力:
    1. 新闻获取（财经新闻、公告、研报）
    2. 事件提取（关键事件识别）
    3. 影响评估（正面/负面/中性）
    4. 股票关联（识别受影响股票）
    5. 投资建议生成

    使用工具:
    - NewsTool (新闻获取)
    - NLPTool (文本处理)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.news_tool = NewsTool()
        self.nlp_tool = NLPTool()
        self.llm_tool = LLMTool()

        super().__init__(
            name="新闻监控AI",
            role="监控财经新闻，识别关键事件和投资机会",
            capabilities=[
                AgentCapability(
                    name="news_monitoring",
                    description="新闻监控",
                    input_type="time_range",
                    output_type="news_report"
                ),
                AgentCapability(
                    name="event_extraction",
                    description="事件提取",
                    input_type="news_content",
                    output_type="events"
                ),
                AgentCapability(
                    name="impact_assessment",
                    description="影响评估",
                    input_type="events",
                    output_type="impact_report"
                ),
                AgentCapability(
                    name="stock_correlation",
                    description="股票关联",
                    input_type="events",
                    output_type="correlated_stocks"
                )
            ],
            tools=[
                AgentTool(
                    name="news_tool",
                    description="新闻获取工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="nlp_tool",
                    description="文本处理工具",
                    tool_type="ai_service",
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

        self.logger.info("新闻监控AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze":
            return await self.analyze(**kwargs)
        elif task == "monitor_news":
            return await self._monitor_news(**kwargs)
        elif task == "extract_events":
            return await self._extract_events(**kwargs)
        elif task == "assess_impact":
            return await self._assess_impact(**kwargs)
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 主入口方法 ==========

    async def analyze(
        self,
        stock_code: Optional[str] = None,
        time_range: str = "1d",
        news_types: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        新闻监控分析

        Args:
            stock_code: 股票代码（可选，用于特定股票新闻）
            time_range: 时间范围（1d, 3d, 7d）
            news_types: 新闻类型（财经、公告、研报）

        Returns:
            新闻监控报告
        """
        self.logger.info(
            f"开始新闻监控分析",
            extra={"stock_code": stock_code, "time_range": time_range}
        )

        if news_types is None:
            news_types = ["财经新闻", "公告", "研报"]

        # ========== 1. 获取新闻 ==========
        news_data = await self._monitor_news(stock_code, time_range, news_types)

        # ========== 2. 提取关键事件 ==========
        events = await self._extract_events(news_data)

        # ========== 3. 评估事件影响 ==========
        impact_assessment = await self._assess_impact(events, stock_code)

        # ========== 4. 关联受影响股票 ==========
        correlated_stocks = await self._correlate_stocks(events, stock_code)

        # ========== 5. 生成投资建议 ==========
        investment_suggestion = self._generate_investment_suggestion(
            events,
            impact_assessment,
            correlated_stocks
        )

        # ========== 6. 构建返回结果 ==========
        result = {
            "analysis_type": "news_monitoring",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "time_range": time_range,

            # 新闻数据
            "news_data": news_data,

            # 关键事件
            "events": events,

            # 影响评估
            "impact_assessment": impact_assessment,

            # 关联股票
            "correlated_stocks": correlated_stocks,

            # 投资建议
            "investment_suggestion": investment_suggestion
        }

        self.logger.info(
            f"新闻监控分析完成",
            extra={
                "news_count": len(news_data.get("news_list", [])),
                "event_count": len(events.get("events", [])),
                "impact_level": impact_assessment.get("overall_impact", "中性")
            }
        )

        return result

    # ========== 核心分析方法 ==========

    async def _monitor_news(
        self,
        stock_code: Optional[str],
        time_range: str,
        news_types: List[str]
    ) -> Dict[str, Any]:
        """
        监控新闻

        Args:
            stock_code: 股票代码
            time_range: 时间范围
            news_types: 新闻类型

        Returns:
            新闻数据
        """
        # 获取新闻列表
        news_list = await self.news_tool.fetch_news(
            stock_code=stock_code,
            time_range=time_range,
            news_types=news_types
        )

        # 统计信息
        total_count = len(news_list)
        type_distribution = {}
        for news in news_list:
            news_type = news.get("type", "未知")
            type_distribution[news_type] = type_distribution.get(news_type, 0) + 1

        return {
            "news_list": news_list,
            "total_count": total_count,
            "type_distribution": type_distribution,
            "time_range": time_range,
            "update_time": datetime.now().isoformat()
        }

    async def _extract_events(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取关键事件

        Args:
            news_data: 新闻数据

        Returns:
            关键事件列表
        """
        events = []
        news_list = news_data.get("news_list", [])

        for news in news_list[:10]:  # 只处理前10条重要新闻
            # 使用NLP工具提取关键事件
            event = await self.nlp_tool.extract_key_events(
                news.get("title", ""),
                news.get("content", "")
            )

            if event:
                event["news_id"] = news.get("id")
                event["news_title"] = news.get("title")
                event["publish_time"] = news.get("publish_time")
                events.append(event)

        # 按重要性排序
        events.sort(key=lambda x: x.get("importance", 0), reverse=True)

        return {
            "events": events,
            "total_count": len(events),
            "update_time": datetime.now().isoformat()
        }

    async def _assess_impact(
        self,
        events: Dict[str, Any],
        stock_code: Optional[str]
    ) -> Dict[str, Any]:
        """
        评估事件影响

        Args:
            events: 事件列表
            stock_code: 股票代码

        Returns:
            影响评估结果
        """
        event_list = events.get("events", [])

        # 分类统计
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        high_importance_events = []

        for event in event_list:
            impact = event.get("impact", "中性")

            if impact == "正面":
                positive_count += 1
            elif impact == "负面":
                negative_count += 1
            else:
                neutral_count += 1

            # 记录高重要性事件
            if event.get("importance", 0) >= 8:
                high_importance_events.append({
                    "title": event.get("title"),
                    "impact": impact,
                    "importance": event.get("importance"),
                    "description": event.get("description")
                })

        # 计算整体影响
        total = len(event_list)
        if total > 0:
            positive_ratio = positive_count / total
            negative_ratio = negative_count / total

            if positive_ratio >= 0.6:
                overall_impact = "正面"
                impact_score = 75 + positive_ratio * 20
            elif negative_ratio >= 0.6:
                overall_impact = "负面"
                impact_score = 25 + (1 - negative_ratio) * 20
            else:
                overall_impact = "中性"
                impact_score = 50 + (positive_ratio - negative_ratio) * 25
        else:
            overall_impact = "中性"
            impact_score = 50

        return {
            "overall_impact": overall_impact,
            "impact_score": round(impact_score, 2),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "high_importance_events": high_importance_events,
            "update_time": datetime.now().isoformat()
        }

    async def _correlate_stocks(
        self,
        events: Dict[str, Any],
        stock_code: Optional[str]
    ) -> Dict[str, Any]:
        """
        关联受影响股票

        Args:
            events: 事件列表
            stock_code: 股票代码

        Returns:
            关联股票列表
        """
        event_list = events.get("events", [])
        stock_impacts = {}

        for event in event_list:
            # 提取事件关联的股票
            related_stocks = event.get("related_stocks", [])

            for stock in related_stocks:
                stock_code_related = stock.get("code")
                impact = event.get("impact", "中性")

                if stock_code_related not in stock_impacts:
                    stock_impacts[stock_code_related] = {
                        "code": stock_code_related,
                        "name": stock.get("name", ""),
                        "positive_count": 0,
                        "negative_count": 0,
                        "neutral_count": 0,
                        "events": []
                    }

                # 统计影响
                if impact == "正面":
                    stock_impacts[stock_code_related]["positive_count"] += 1
                elif impact == "负面":
                    stock_impacts[stock_code_related]["negative_count"] += 1
                else:
                    stock_impacts[stock_code_related]["neutral_count"] += 1

                # 记录事件
                stock_impacts[stock_code_related]["events"].append({
                    "title": event.get("title"),
                    "impact": impact,
                    "importance": event.get("importance")
                })

        # 计算综合影响
        correlated_list = []
        for stock_code_key, stock_data in stock_impacts.items():
            total = (
                stock_data["positive_count"] +
                stock_data["negative_count"] +
                stock_data["neutral_count"]
            )

            if total > 0:
                positive_ratio = stock_data["positive_count"] / total
                negative_ratio = stock_data["negative_count"] / total

                if positive_ratio >= 0.6:
                    stock_data["overall_impact"] = "利好"
                    stock_data["impact_score"] = 75 + positive_ratio * 20
                elif negative_ratio >= 0.6:
                    stock_data["overall_impact"] = "利空"
                    stock_data["impact_score"] = 25 + (1 - negative_ratio) * 20
                else:
                    stock_data["overall_impact"] = "中性"
                    stock_data["impact_score"] = 50 + (positive_ratio - negative_ratio) * 25

                correlated_list.append(stock_data)

        # 按影响评分排序
        correlated_list.sort(key=lambda x: x.get("impact_score", 50), reverse=True)

        return {
            "correlated_stocks": correlated_list[:10],  # 只返回前10个
            "total_count": len(correlated_list),
            "update_time": datetime.now().isoformat()
        }

    # ========== 投资建议生成 ==========

    def _generate_investment_suggestion(
        self,
        events: Dict[str, Any],
        impact_assessment: Dict[str, Any],
        correlated_stocks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成投资建议

        Args:
            events: 事件列表
            impact_assessment: 影响评估
            correlated_stocks: 关联股票

        Returns:
            投资建议
        """
        overall_impact = impact_assessment.get("overall_impact", "中性")
        impact_score = impact_assessment.get("impact_score", 50)

        # 生成建议
        if impact_score >= 75:
            action = "积极关注"
            suggestion = "重大利好事件较多，建议积极关注相关股票投资机会"
            risk_level = "低"
        elif impact_score >= 60:
            action = "适度关注"
            suggestion = "利好事件较多，可以适度关注投资机会"
            risk_level = "中低"
        elif impact_score >= 40:
            action = "观望"
            suggestion = "事件影响中性，建议观望为主"
            risk_level = "中"
        elif impact_score >= 25:
            action = "谨慎"
            suggestion = "利空事件较多，建议谨慎对待，控制风险"
            risk_level = "中高"
        else:
            action = "回避"
            suggestion = "重大利空事件较多，建议回避相关股票"
            risk_level = "高"

        # 推荐股票
        recommended_stocks = []
        for stock in correlated_stocks.get("correlated_stocks", [])[:3]:
            if stock.get("impact_score", 50) >= 60:
                recommended_stocks.append({
                    "code": stock["code"],
                    "name": stock["name"],
                    "impact": stock["overall_impact"],
                    "score": stock["impact_score"]
                })

        # 风险提示
        risk_tips = []
        high_importance_events = impact_assessment.get("high_importance_events", [])
        for event in high_importance_events[:3]:
            if event["impact"] == "负面":
                risk_tips.append(event["title"])

        return {
            "action": action,
            "suggestion": suggestion,
            "risk_level": risk_level,
            "impact_score": impact_score,
            "recommended_stocks": recommended_stocks,
            "risk_tips": risk_tips,
            "confidence": "中" if len(events.get("events", [])) >= 5 else "低"
        }

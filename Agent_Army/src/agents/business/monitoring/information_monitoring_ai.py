"""
信息监控AI - Information Monitoring AI

监控部成员 (1/2)

职责：
1. 新闻监控 - 实时监控相关新闻和公告
2. 市场情绪 - 分析市场情绪和舆论走向

合并来源：
- 新闻监控AI
- 市场情绪AI

使用工具：
- DataTool（新闻数据）
- LLMTool（情绪分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from collections import Counter

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class InformationMonitoringAI(BusinessAgent):
    """
    信息监控AI - 监控部成员 (1/2)

    核心能力:
    1. 新闻监控 - 实时监控公司新闻、行业动态、政策变化
    2. 市场情绪 - 分析市场情绪、投资者情绪、舆论走向

    使用工具:
    - DataTool (新闻数据)
    - LLMTool (情绪分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="信息监控AI",
            role="监控新闻事件，分析市场情绪",
            corps="monitoring",
            analysis_type="information_monitoring",
            capabilities=[
                AgentCapability(
                    name="news_monitoring",
                    description="新闻监控",
                    input_type="stock_code",
                    output_type="news_events"
                ),
                AgentCapability(
                    name="sentiment_analysis",
                    description="市场情绪分析",
                    input_type="stock_code",
                    output_type="sentiment_index"
                )
            ],
            tools=[
                AgentTool(
                    name="data_tool",
                    description="数据工具",
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

        self.logger.info("信息监控AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行信息监控分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - days: 监控天数（默认7天）
                - include_industry: 是否包含行业新闻（默认True）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        days = kwargs.get("days", 7)
        include_industry = kwargs.get("include_industry", True)

        self.logger.info(
            f"开始信息监控分析",
            extra={
                "stock_code": stock_code,
                "days": days,
                "include_industry": include_industry
            }
        )

        # ========== 1. 新闻监控 ==========
        news_events = await self._monitor_news(
            stock_code,
            days,
            include_industry
        )

        # ========== 2. 市场情绪分析 ==========
        sentiment_analysis = await self._analyze_sentiment(
            stock_code,
            news_events
        )

        # ========== 3. 重要信息提取 ==========
        important_info = self._extract_important_info(
            news_events,
            sentiment_analysis
        )

        # ========== 4. 风险识别 ==========
        risks = self._identify_risks(news_events, sentiment_analysis)

        # ========== 5. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,
            "monitoring_period": f"{days}天",

            # 新闻事件
            "news_events": news_events,

            # 情绪分析
            "sentiment_analysis": sentiment_analysis,

            # 重要信息
            "important_info": important_info,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                news_events,
                sentiment_analysis,
                important_info
            ),
            confidence=sentiment_analysis["confidence"],
            details=details,
            risks=risks,
            recommendations=self._generate_recommendations(
                news_events,
                sentiment_analysis,
                important_info
            )
        )

        self.logger.info(
            f"信息监控分析完成",
            extra={
                "stock_code": stock_code,
                "news_count": len(news_events["company_news"]),
                "sentiment_score": sentiment_analysis["overall_sentiment"]["score"],
                "confidence": sentiment_analysis["confidence"]
            }
        )

        return result

    # ========== 新闻监控 ==========

    async def _monitor_news(
        self,
        stock_code: str,
        days: int,
        include_industry: bool
    ) -> Dict[str, Any]:
        """
        监控新闻事件

        Returns:
            包含公司新闻、行业新闻、政策新闻的字典
        """
        # 并行获取三类新闻
        company_news_task = self._get_company_news(stock_code, days)
        industry_news_task = self._get_industry_news(stock_code, days) if include_industry else asyncio.sleep(0)
        policy_news_task = self._get_policy_news(stock_code, days)

        results = await asyncio.gather(
            company_news_task,
            industry_news_task,
            policy_news_task,
            return_exceptions=True
        )

        company_news = results[0] if not isinstance(results[0], Exception) else []
        industry_news = results[1] if include_industry and not isinstance(results[1], Exception) else []
        policy_news = results[2] if not isinstance(results[2], Exception) else []

        # 新闻分类统计
        news_summary = self._summarize_news(company_news, industry_news, policy_news)

        return {
            "company_news": company_news,
            "industry_news": industry_news,
            "policy_news": policy_news,
            "summary": news_summary
        }

    async def _get_company_news(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取公司新闻"""
        # TODO: 接入真实新闻API
        # 模拟数据
        mock_news = [
            {
                "title": "公司发布2025年业绩预告，净利润同比增长50%",
                "source": "公司公告",
                "time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "业绩",
                "importance": "高",
                "sentiment": "positive"
            },
            {
                "title": "公司拟斥资5亿元回购股份",
                "source": "上海证券交易所",
                "time": (datetime.now() - timedelta(days=1)).isoformat(),
                "type": "重大事项",
                "importance": "高",
                "sentiment": "positive"
            },
            {
                "title": "公司获得国家发明专利授权",
                "source": "公司公告",
                "time": (datetime.now() - timedelta(days=2)).isoformat(),
                "type": "技术",
                "importance": "中",
                "sentiment": "positive"
            },
            {
                "title": "公司高管减持100万股",
                "source": "深圳证券交易所",
                "time": (datetime.now() - timedelta(days=3)).isoformat(),
                "type": "交易",
                "importance": "中",
                "sentiment": "negative"
            },
            {
                "title": "公司召开投资者交流会，展望未来发展战略",
                "source": "公司公告",
                "time": (datetime.now() - timedelta(days=5)).isoformat(),
                "type": "投资者关系",
                "importance": "低",
                "sentiment": "neutral"
            }
        ]

        return mock_news

    async def _get_industry_news(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取行业新闻"""
        # TODO: 接入真实行业新闻API
        mock_news = [
            {
                "title": "行业景气度持续回升，需求增长超预期",
                "source": "行业研究报告",
                "time": (datetime.now() - timedelta(hours=6)).isoformat(),
                "type": "行业动态",
                "importance": "高",
                "sentiment": "positive"
            },
            {
                "title": "行业协会发布新标准，促进行业健康发展",
                "source": "行业协会",
                "time": (datetime.now() - timedelta(days=2)).isoformat(),
                "type": "政策",
                "importance": "中",
                "sentiment": "positive"
            },
            {
                "title": "原材料价格大幅上涨，企业成本承压",
                "source": "市场资讯",
                "time": (datetime.now() - timedelta(days=4)).isoformat(),
                "type": "市场",
                "importance": "中",
                "sentiment": "negative"
            }
        ]

        return mock_news

    async def _get_policy_news(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取政策新闻"""
        # TODO: 接入真实政策新闻API
        mock_news = [
            {
                "title": "国家出台产业扶持政策，加大税收优惠力度",
                "source": "国务院",
                "time": (datetime.now() - timedelta(days=1)).isoformat(),
                "type": "产业政策",
                "importance": "高",
                "sentiment": "positive"
            },
            {
                "title": "监管部门加强行业规范管理",
                "source": "证监会",
                "time": (datetime.now() - timedelta(days=6)).isoformat(),
                "type": "监管政策",
                "importance": "中",
                "sentiment": "neutral"
            }
        ]

        return mock_news

    def _summarize_news(
        self,
        company_news: List[Dict],
        industry_news: List[Dict],
        policy_news: List[Dict]
    ) -> Dict[str, Any]:
        """新闻分类统计"""
        all_news = company_news + industry_news + policy_news

        # 按类型统计
        type_counter = Counter([news["type"] for news in all_news])

        # 按重要性统计
        importance_counter = Counter([news["importance"] for news in all_news])

        # 按情绪统计
        sentiment_counter = Counter([news.get("sentiment", "neutral") for news in all_news])

        return {
            "total_count": len(all_news),
            "company_news_count": len(company_news),
            "industry_news_count": len(industry_news),
            "policy_news_count": len(policy_news),
            "by_type": dict(type_counter),
            "by_importance": dict(importance_counter),
            "by_sentiment": dict(sentiment_counter)
        }

    # ========== 市场情绪分析 ==========

    async def _analyze_sentiment(
        self,
        stock_code: str,
        news_events: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析市场情绪

        Returns:
            情绪分析结果
        """
        all_news = (
            news_events["company_news"] +
            news_events["industry_news"] +
            news_events["policy_news"]
        )

        if not all_news:
            return {
                "overall_sentiment": {
                    "score": 0.0,
                    "label": "中性",
                    "description": "无新闻数据"
                },
                "sentiment_trend": "stable",
                "confidence": 0.0,
                "breakdown": {}
            }

        # 计算情绪得分
        sentiment_scores = []
        for news in all_news:
            sentiment = news.get("sentiment", "neutral")
            if sentiment == "positive":
                score = 1.0
            elif sentiment == "negative":
                score = -1.0
            else:
                score = 0.0

            # 根据重要性加权
            importance_weight = {
                "高": 1.5,
                "中": 1.0,
                "低": 0.5
            }.get(news.get("importance", "中"), 1.0)

            sentiment_scores.append(score * importance_weight)

        # 计算加权平均
        overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        # 情绪标签
        if overall_score >= 0.5:
            sentiment_label = "积极"
            sentiment_description = "市场情绪乐观，利好消息占主导"
        elif overall_score >= 0.2:
            sentiment_label = "偏积极"
            sentiment_description = "市场情绪偏向乐观"
        elif overall_score >= -0.2:
            sentiment_label = "中性"
            sentiment_description = "市场情绪平稳，多空消息交织"
        elif overall_score >= -0.5:
            sentiment_label = "偏消极"
            sentiment_description = "市场情绪偏向悲观"
        else:
            sentiment_label = "消极"
            sentiment_description = "市场情绪悲观，利空消息占主导"

        # 情绪趋势
        sentiment_trend = self._calculate_sentiment_trend(all_news)

        # 置信度
        confidence = min(len(all_news) / 10, 1.0)  # 新闻越多，置信度越高

        # 分类情绪
        breakdown = {
            "company_sentiment": self._calculate_category_sentiment(news_events["company_news"]),
            "industry_sentiment": self._calculate_category_sentiment(news_events["industry_news"]),
            "policy_sentiment": self._calculate_category_sentiment(news_events["policy_news"])
        }

        return {
            "overall_sentiment": {
                "score": round(overall_score, 2),
                "label": sentiment_label,
                "description": sentiment_description
            },
            "sentiment_trend": sentiment_trend,
            "confidence": round(confidence, 2),
            "breakdown": breakdown,
            "news_count": len(all_news)
        }

    def _calculate_sentiment_trend(self, news_list: List[Dict]) -> str:
        """计算情绪趋势"""
        if len(news_list) < 2:
            return "stable"

        # 按时间排序
        sorted_news = sorted(
            news_list,
            key=lambda x: x["time"],
            reverse=True
        )

        # 最近3天 vs 前3天
        recent_news = sorted_news[:3]
        earlier_news = sorted_news[3:6] if len(sorted_news) >= 6 else []

        if not earlier_news:
            return "stable"

        # 计算平均情绪
        recent_avg = self._avg_sentiment(recent_news)
        earlier_avg = self._avg_sentiment(earlier_news)

        diff = recent_avg - earlier_avg

        if diff > 0.3:
            return "improving"  # 情绪改善
        elif diff > -0.3:
            return "stable"  # 稳定
        else:
            return "declining"  # 情绪恶化

    def _avg_sentiment(self, news_list: List[Dict]) -> float:
        """计算平均情绪"""
        sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        scores = [sentiment_map.get(news.get("sentiment", "neutral"), 0.0) for news in news_list]
        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_category_sentiment(self, news_list: List[Dict]) -> Dict[str, Any]:
        """计算分类情绪"""
        if not news_list:
            return {
                "score": 0.0,
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        sentiment_counter = Counter([news.get("sentiment", "neutral") for news in news_list])

        total = len(news_list)
        positive_ratio = sentiment_counter["positive"] / total
        negative_ratio = sentiment_counter["negative"] / total

        # 计算得分
        score = positive_ratio - negative_ratio

        return {
            "score": round(score, 2),
            "positive": sentiment_counter["positive"],
            "negative": sentiment_counter["negative"],
            "neutral": sentiment_counter["neutral"]
        }

    # ========== 重要信息提取 ==========

    def _extract_important_info(
        self,
        news_events: Dict[str, Any],
        sentiment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取重要信息"""
        all_news = (
            news_events["company_news"] +
            news_events["industry_news"] +
            news_events["policy_news"]
        )

        # 高重要性新闻
        high_importance_news = [
            news for news in all_news
            if news.get("importance") == "高"
        ]

        # 利好消息
        positive_news = [
            news for news in all_news
            if news.get("sentiment") == "positive" and news.get("importance") in ["高", "中"]
        ]

        # 利空消息
        negative_news = [
            news for news in all_news
            if news.get("sentiment") == "negative" and news.get("importance") in ["高", "中"]
        ]

        # 最新消息（最近24小时）
        recent_news = [
            news for news in all_news
            if datetime.fromisoformat(news["time"]) > datetime.now() - timedelta(days=1)
        ]

        return {
            "high_importance": high_importance_news,
            "positive_news": positive_news[:5],  # 最多5条
            "negative_news": negative_news[:5],  # 最多5条
            "recent_news": recent_news,
            "summary": {
                "high_importance_count": len(high_importance_news),
                "positive_count": len(positive_news),
                "negative_count": len(negative_news),
                "recent_count": len(recent_news)
            }
        }

    # ========== 风险识别 ==========

    def _identify_risks(
        self,
        news_events: Dict[str, Any],
        sentiment_analysis: Dict[str, Any]
    ) -> List[str]:
        """识别风险"""
        risks = []

        # 情绪风险
        overall_sentiment = sentiment_analysis["overall_sentiment"]
        if overall_sentiment["score"] < -0.3:
            risks.append(f"市场情绪{overall_sentiment['label']}，可能出现恐慌性抛售")

        # 情绪趋势风险
        if sentiment_analysis["sentiment_trend"] == "declining":
            risks.append("市场情绪持续恶化，需警惕进一步下跌风险")

        # 利空消息集中
        negative_count = news_events["summary"]["by_sentiment"].get("negative", 0)
        positive_count = news_events["summary"]["by_sentiment"].get("positive", 0)
        if negative_count > positive_count * 1.5:
            risks.append(f"利空消息集中（{negative_count}条 vs {positive_count}条），短期承压")

        # 高重要性利空
        all_news = (
            news_events["company_news"] +
            news_events["industry_news"] +
            news_events["policy_news"]
        )
        high_importance_negative = [
            news for news in all_news
            if news.get("importance") == "高" and news.get("sentiment") == "negative"
        ]
        if high_importance_negative:
            risks.append(f"发现{len(high_importance_negative)}条高重要性利空消息，需重点关注")

        # 政策风险
        policy_negative = [
            news for news in news_events["policy_news"]
            if news.get("sentiment") == "negative"
        ]
        if policy_negative:
            risks.append("政策面出现不利变化，可能对行业产生长期影响")

        if not risks:
            risks.append("未发现明显风险")

        return risks

    # ========== 建议生成 ==========

    def _generate_recommendations(
        self,
        news_events: Dict[str, Any],
        sentiment_analysis: Dict[str, Any],
        important_info: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于情绪的建议
        sentiment_score = sentiment_analysis["overall_sentiment"]["score"]
        if sentiment_score >= 0.5:
            recommendations.append("市场情绪积极，利好消息占主导，适宜积极布局")
        elif sentiment_score >= 0.2:
            recommendations.append("市场情绪偏积极，可考虑逢低吸纳")
        elif sentiment_score >= -0.2:
            recommendations.append("市场情绪中性，建议观望等待更明确信号")
        else:
            recommendations.append("市场情绪悲观，建议谨慎操作或暂时回避")

        # 基于情绪趋势的建议
        trend = sentiment_analysis["sentiment_trend"]
        if trend == "improving":
            recommendations.append("市场情绪持续改善，可逐步建仓")
        elif trend == "declining":
            recommendations.append("市场情绪持续恶化，建议减仓或规避")

        # 基于重要消息的建议
        high_importance_count = important_info["summary"]["high_importance_count"]
        if high_importance_count >= 3:
            recommendations.append(f"近期有{high_importance_count}条高重要性消息，建议密切关注")

        # 利好消息
        positive_count = important_info["summary"]["positive_count"]
        if positive_count >= 3:
            recommendations.append(f"利好消息集中（{positive_count}条），短期可能走强")

        # 利空消息
        negative_count = important_info["summary"]["negative_count"]
        if negative_count >= 2:
            recommendations.append(f"利空消息较多（{negative_count}条），注意风险控制")

        return recommendations

    # ========== 结论生成 ==========

    def _generate_conclusion(
        self,
        news_events: Dict[str, Any],
        sentiment_analysis: Dict[str, Any],
        important_info: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        summary = news_events["summary"]
        sentiment = sentiment_analysis["overall_sentiment"]

        return (
            f"近{summary['total_count']}条新闻，"
            f"市场情绪【{sentiment['label']}】（得分{sentiment['score']:.2f}），"
            f"趋势【{sentiment_analysis['sentiment_trend']}】，"
            f"高重要性消息{important_info['summary']['high_importance_count']}条"
        )


# 便捷函数
async def analyze_information_monitoring(
    stock_code: str,
    days: int = 7,
    include_industry: bool = True
) -> AnalysisResult:
    """
    信息监控分析（便捷函数）

    Args:
        stock_code: 股票代码
        days: 监控天数
        include_industry: 是否包含行业新闻

    Returns:
        分析结果
    """
    ai = InformationMonitoringAI()
    return await ai.analyze(
        stock_code,
        days=days,
        include_industry=include_industry
    )

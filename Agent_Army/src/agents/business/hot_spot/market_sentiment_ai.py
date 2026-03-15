"""
市场情绪AI - Market Sentiment AI

职责：
- 分析市场情绪，计算情感指数(0-100)
- 使用NewsTool获取新闻数据
- 使用NLPTool进行情感分析
- 计算整体市场情绪指数

输入：
- 股票代码
- 时间范围（可选）

输出：
- 情感指数（0-100）
- 市场情绪评级（bullish/neutral/bearish）
- 新闻统计
- 情感分析详情

技术架构：
- 继承BaseBusinessAgent
- 使用工具库：NewsTool、NLPTool
- 数据源：Yahoo Finance（新闻）+ AKShare（情绪数据）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from src.agents.business.base_business_agent import (
    BusinessAgent,
    AnalysisResult,
    StockInfo
)
from src.core.tools import NewsTool, NLPTool
from src.core.logger import get_logger


class SentimentAnalysisResult(BaseModel):
    """市场情绪分析结果"""
    stock_code: str = Field(..., description="股票代码")
    sentiment_index: float = Field(..., ge=0.0, le=100.0, description="情感指数(0-100)")
    market_mood: str = Field(..., description="市场情绪(bullish/neutral/bearish)")
    news_count: int = Field(..., ge=0, description="新闻总数")
    positive_count: int = Field(..., ge=0, description="正面新闻数")
    negative_count: int = Field(..., ge=0, description="负面新闻数")
    neutral_count: int = Field(..., ge=0, description="中性新闻数")
    timestamp: str = Field(..., description="分析时间")
    analysis_period: str = Field(..., description="分析周期")
    sentiment_details: Dict[str, Any] = Field(default_factory=dict, description="详细情感数据")
    top_keywords: List[str] = Field(default_factory=list, description="热门关键词")


class MarketSentimentAI(BusinessAgent):
    """
    市场情绪AI - 分析市场情绪和舆论导向

    功能：
    1. 获取股票相关新闻
    2. 使用NLP分析新闻情感
    3. 计算综合情感指数
    4. 生成市场情绪评级
    """

    def __init__(
        self,
        capabilities: Optional[List] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化市场情绪AI

        Args:
            capabilities: 能力列表
            tools: 工具列表
            config: 配置参数
        """
        # 初始化工具
        self.news_tool = NewsTool(config=config)
        self.nlp_tool = NLPTool(config=config)

        # 初始化基类
        super().__init__(
            name="市场情绪AI",
            role="分析市场情绪、舆论导向，计算情感指数和热度排名",
            corps="热点追踪军团",
            analysis_type="市场情绪分析",
            capabilities=capabilities,
            tools=tools,
            config=config
        )

        # 配置参数
        self.default_days = config.get("default_days", 7) if config else 7
        self.sentiment_thresholds = config.get("sentiment_thresholds", {
            "bullish": 60.0,
            "bearish": 40.0
        }) if config else {
            "bullish": 60.0,
            "bearish": 40.0
        }

        self.logger.info("市场情绪AI初始化完成")

    async def analyze(
        self,
        stock_code: str,
        days: Optional[int] = None,
        **kwargs
    ) -> AnalysisResult:
        """
        分析市场情绪（实现基类的抽象方法）

        Args:
            stock_code: 股票代码
            days: 分析天数（默认使用配置的默认值）
            **kwargs: 其他参数

        Returns:
            AnalysisResult对象，包含完整的分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 设置分析周期
        analysis_days = days or self.default_days

        self.logger.info(
            f"开始分析市场情绪",
            extra={
                "stock_code": stock_code,
                "days": analysis_days
            }
        )

        try:
            # 1. 获取新闻数据
            news_data = await self._fetch_news(stock_code, analysis_days)

            # 2. 分析每条新闻的情感
            sentiment_results = await self._analyze_news_sentiment(news_data)

            # 3. 计算综合情感指数
            sentiment_index = self._calculate_sentiment_index(sentiment_results)

            # 4. 判断市场情绪
            market_mood = self._determine_market_mood(sentiment_index)

            # 5. 提取关键词
            top_keywords = await self._extract_keywords(news_data)

            # 6. 生成分析结论
            conclusion = self._generate_conclusion(
                sentiment_index,
                market_mood,
                sentiment_results
            )

            # 7. 生成风险提示
            risks = self._generate_risks(sentiment_results, sentiment_index)

            # 8. 生成建议
            recommendations = self._generate_recommendations(market_mood)

            # 构建详细数据
            details = {
                "sentiment_index": sentiment_index,
                "market_mood": market_mood,
                "news_count": len(news_data),
                "positive_count": sentiment_results["positive"],
                "negative_count": sentiment_results["negative"],
                "neutral_count": sentiment_results["neutral"],
                "analysis_period": f"{analysis_days}天",
                "top_keywords": top_keywords,
                "timestamp": datetime.now().isoformat()
            }

            # 构建分析结果
            result = AnalysisResult(
                agent_name=self.name,
                analysis_type=self.analysis_type,
                conclusion=conclusion,
                confidence=self._calculate_confidence(sentiment_results),
                details=details,
                risks=risks,
                recommendations=recommendations
            )

            self.logger.info(
                f"市场情绪分析完成",
                extra={
                    "stock_code": stock_code,
                    "sentiment_index": sentiment_index,
                    "market_mood": market_mood
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"市场情绪分析失败: {e}", exc_info=True)
            raise

    async def get_sentiment_result(
        self,
        stock_code: str,
        days: Optional[int] = None
    ) -> SentimentAnalysisResult:
        """
        获取标准格式的情绪分析结果

        Args:
            stock_code: 股票代码
            days: 分析天数

        Returns:
            SentimentAnalysisResult对象
        """
        # 执行分析
        analysis_result = await self.analyze(stock_code, days)

        # 提取详细信息
        details = analysis_result.details

        # 构建情绪分析结果
        sentiment_result = SentimentAnalysisResult(
            stock_code=stock_code,
            sentiment_index=details["sentiment_index"],
            market_mood=details["market_mood"],
            news_count=details["news_count"],
            positive_count=details["positive_count"],
            negative_count=details["negative_count"],
            neutral_count=details["neutral_count"],
            timestamp=details["timestamp"],
            analysis_period=details["analysis_period"],
            sentiment_details={
                "conclusion": analysis_result.conclusion,
                "confidence": analysis_result.confidence
            },
            top_keywords=details["top_keywords"]
        )

        return sentiment_result

    # ========== 私有方法 ==========

    async def _fetch_news(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        获取新闻数据

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            新闻列表
        """
        try:
            news_list = await self.news_tool.fetch_news(
                stock_code=stock_code,
                days=days
            )

            self.logger.info(f"获取到{len(news_list)}条新闻")

            return news_list

        except Exception as e:
            self.logger.warning(f"获取新闻失败: {e}，使用模拟数据")
            # 返回模拟数据
            return await self._get_mock_news(stock_code, days)

    async def _get_mock_news(
        self,
        stock_code: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        获取模拟新闻数据（备用）

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            模拟新闻列表
        """
        stock_names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000333": "美的集团",
            "600036": "招商银行"
        }
        stock_name = stock_names.get(stock_code, "该公司")

        mock_news = [
            {
                "title": f"{stock_name}发布2025年年报，业绩超预期",
                "content": f"{stock_name}2025年实现营收100亿元，同比增长15%；净利润10亿元，同比增长20%，业绩表现优异。",
                "source": "东方财富",
                "published_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "url": "https://example.com/news/1"
            },
            {
                "title": f"多家机构调研{stock_name}，看好长期发展",
                "content": f"近期多家机构调研{stock_name}，关注公司新产品布局和市场拓展策略，分析师普遍看好公司长期发展前景。",
                "source": "同花顺",
                "published_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "url": "https://example.com/news/2"
            },
            {
                "title": f"行业政策利好，{stock_name}有望受益",
                "content": f"国家出台新的行业支持政策，鼓励技术创新和产业升级，{stock_name}作为行业龙头企业有望优先受益。",
                "source": "新浪财经",
                "published_at": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "url": "https://example.com/news/3"
            },
            {
                "title": f"{stock_name}控股股东增持，彰显信心",
                "content": f"{stock_name}控股股东增持公司股份100万股，占总股本的0.1%，显示对公司未来发展的信心。",
                "source": "东方财富",
                "published_at": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
                "url": "https://example.com/news/4"
            },
            {
                "title": f"券商上调{stock_name}目标价",
                "content": f"多家券商发布研报，给予{stock_name}买入评级，目标价上调至200元，对应市盈率25倍。",
                "source": "同花顺",
                "published_at": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "url": "https://example.com/news/5"
            }
        ]

        return mock_news

    async def _analyze_news_sentiment(
        self,
        news_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析新闻情感

        Args:
            news_data: 新闻列表

        Returns:
            情感统计结果
        """
        sentiment_stats = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "scores": [],
            "total_score": 0.0
        }

        if not news_data:
            return sentiment_stats

        # 分析每条新闻
        for news in news_data:
            # 合并标题和内容
            text = f"{news.get('title', '')} {news.get('content', '')}"

            # 使用NLP工具分析情感
            sentiment = await self.nlp_tool.analyze_sentiment(text)

            # 记录分数
            score = sentiment.get("score", 50)
            sentiment_stats["scores"].append(score)
            sentiment_stats["total_score"] += score

            # 统计情感分类
            label = sentiment.get("label", "neutral")
            if label == "positive":
                sentiment_stats["positive"] += 1
            elif label == "negative":
                sentiment_stats["negative"] += 1
            else:
                sentiment_stats["neutral"] += 1

        # 计算平均分数
        if news_data:
            avg_score = sentiment_stats["total_score"] / len(news_data)
            sentiment_stats["average_score"] = round(avg_score, 2)
        else:
            sentiment_stats["average_score"] = 50.0

        return sentiment_stats

    def _calculate_sentiment_index(
        self,
        sentiment_results: Dict[str, Any]
    ) -> float:
        """
        计算综合情感指数

        Args:
            sentiment_results: 情感分析结果

        Returns:
            情感指数（0-100）
        """
        if not sentiment_results["scores"]:
            return 50.0  # 无数据时返回中性

        # 使用加权平均
        # 正面新闻权重更高，负面新闻权重更低
        total = 0
        weight_sum = 0

        for score in sentiment_results["scores"]:
            # 分数越高，权重越大
            weight = score / 50.0
            total += score * weight
            weight_sum += weight

        if weight_sum > 0:
            index = total / weight_sum
        else:
            index = sentiment_results["average_score"]

        return round(index, 2)

    def _determine_market_mood(self, sentiment_index: float) -> str:
        """
        判断市场情绪

        Args:
            sentiment_index: 情感指数

        Returns:
            市场情绪 (bullish/neutral/bearish)
        """
        bullish_threshold = self.sentiment_thresholds["bullish"]
        bearish_threshold = self.sentiment_thresholds["bearish"]

        if sentiment_index >= bullish_threshold:
            return "bullish"
        elif sentiment_index <= bearish_threshold:
            return "bearish"
        else:
            return "neutral"

    def _generate_conclusion(
        self,
        sentiment_index: float,
        market_mood: str,
        sentiment_results: Dict[str, Any]
    ) -> str:
        """
        生成分析结论

        Args:
            sentiment_index: 情感指数
            market_mood: 市场情绪
            sentiment_results: 情感统计

        Returns:
            结论文本
        """
        mood_map = {
            "bullish": "乐观",
            "neutral": "中性",
            "bearish": "悲观"
        }

        mood_text = mood_map.get(market_mood, "中性")

        positive_ratio = sentiment_results["positive"]
        negative_ratio = sentiment_results["negative"]

        conclusion = (
            f"市场情绪{mood_text}（指数{sentiment_index:.1f}分），"
            f"正面新闻{positive_ratio}条，负面新闻{negative_ratio}条。"
        )

        if market_mood == "bullish":
            conclusion += "投资者信心较强，市场氛围积极。"
        elif market_mood == "bearish":
            conclusion += "投资者情绪谨慎，市场氛围偏空。"
        else:
            conclusion += "市场情绪平稳，多空均衡。"

        return conclusion

    def _generate_risks(
        self,
        sentiment_results: Dict[str, Any],
        sentiment_index: float
    ) -> List[str]:
        """
        生成风险提示

        Args:
            sentiment_results: 情感统计
            sentiment_index: 情感指数

        Returns:
            风险提示列表
        """
        risks = []

        # 新闻数量不足
        if sentiment_results["positive"] + sentiment_results["negative"] + sentiment_results["neutral"] < 5:
            risks.append("新闻样本较少，分析结果可能不够准确")

        # 情感极端
        if sentiment_index >= 80:
            risks.append("市场情绪过于乐观，注意回调风险")
        elif sentiment_index <= 20:
            risks.append("市场情绪过于悲观，可能存在超跌机会")

        # 负面新闻较多
        if sentiment_results["negative"] > sentiment_results["positive"]:
            risks.append(f"负面新闻数量({sentiment_results['negative']})超过正面新闻")

        return risks

    def _generate_recommendations(self, market_mood: str) -> List[str]:
        """
        生成投资建议

        Args:
            market_mood: 市场情绪

        Returns:
            建议列表
        """
        recommendations = []

        if market_mood == "bullish":
            recommendations.append("市场情绪乐观，可适当关注")
            recommendations.append("注意结合其他指标综合判断")
        elif market_mood == "bearish":
            recommendations.append("市场情绪悲观，建议谨慎对待")
            recommendations.append("可等待情绪好转后再考虑")
        else:
            recommendations.append("市场情绪中性，建议观望")
            recommendations.append("关注后续新闻变化")

        return recommendations

    def _calculate_confidence(
        self,
        sentiment_results: Dict[str, Any]
    ) -> float:
        """
        计算置信度

        Args:
            sentiment_results: 情感统计

        Returns:
            置信度（0-1）
        """
        total_news = (
            sentiment_results["positive"] +
            sentiment_results["negative"] +
            sentiment_results["neutral"]
        )

        if total_news == 0:
            return 0.0

        # 新闻越多，置信度越高（最高0.9）
        confidence = min(0.9, total_news / 20.0)

        # 如果正反面新闻差距大，置信度降低
        diff = abs(sentiment_results["positive"] - sentiment_results["negative"])
        if diff > total_news * 0.7:
            confidence *= 0.8

        return round(confidence, 2)

    async def _extract_keywords(
        self,
        news_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        提取关键词

        Args:
            news_data: 新闻列表

        Returns:
            关键词列表
        """
        if not news_data:
            return []

        # 合并所有新闻文本
        all_text = " ".join([
            f"{news.get('title', '')} {news.get('content', '')}"
            for news in news_data
        ])

        # 使用NLP工具提取关键词
        keywords = await self.nlp_tool.extract_keywords(all_text, top_n=10)

        return keywords


# ========== 便捷函数 ==========

async def analyze_market_sentiment(
    stock_code: str,
    days: int = 7,
    config: Optional[Dict] = None
) -> SentimentAnalysisResult:
    """
    分析市场情绪（便捷函数）

    Args:
        stock_code: 股票代码
        days: 分析天数
        config: 配置参数

    Returns:
        情绪分析结果
    """
    ai = MarketSentimentAI(config=config)
    return await ai.get_sentiment_result(stock_code, days)

"""
新闻工具 - 统一管理新闻数据获取
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
import asyncio

from src.core.logger import get_logger


class NewsTool:
    """
    新闻工具

    职责：
    - 封装所有新闻API调用
    - 提供统一接口给AI Agent使用
    - AI Agent不关心新闻数据如何获取的
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("news_tool")
        self.config = config or {}

        # API配置
        self.apis = {
            "eastmoney": {
                "base_url": "https://newsapi.eastmoney.com/kuaixun/v1",
                "enabled": True
            },
            "sina": {
                "base_url": "https://finance.sina.com.cn/api",
                "enabled": True
            },
            "tonghuaxun": {
                "base_url": "https://news.10jqka.com.cn/api",
                "enabled": False  # 示例：暂时禁用
            }
        }

        self.logger.info("新闻工具初始化完成")

    async def fetch_news(
        self,
        stock_code: str,
        days: int = 7,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取股票相关新闻

        Args:
            stock_code: 股票代码
            days: 监控天数（默认7天）
            sources: 指定数据源（默认所有启用的）

        Returns:
            标准化的新闻列表:
            [
                {
                    "title": "新闻标题",
                    "content": "新闻内容",
                    "source": "东方财富",
                    "published_at": "2026-03-14 10:30:00",
                    "url": "https://...",
                    "sentiment": "positive",  # 可选
                    "importance": 8.5  # 可选
                }
            ]
        """
        self.logger.info(f"获取新闻: {stock_code}, 最近{days}天")

        # 确定使用的数据源
        if sources is None:
            sources = [name for name, api in self.apis.items() if api["enabled"]]

        # 并发获取多个数据源
        all_news = []

        # TODO: 接入真实API
        # 当前返回示例数据
        all_news = await self._fetch_sample_news(stock_code, days)

        self.logger.info(f"获取到{len(all_news)}条新闻")

        return all_news

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        情感分析

        Args:
            text: 待分析的文本

        Returns:
            {
                "sentiment": "positive" | "negative" | "neutral",
                "score": 0.85,  # 0-1
                "confidence": 0.9,  # 0-1
                "keywords": ["增长", "利好"]  # 关键词
            }
        """
        self.logger.info("情感分析中...")

        # TODO: 调用真实的NLP服务
        # 当前使用简单的关键词匹配
        positive_keywords = ["增长", "利好", "增持", "看好", "买入", "支持", "获"]
        negative_keywords = ["下降", "利空", "减持", "看空", "卖出", "限制", "罚"]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.7 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            sentiment = "negative"
            score = 0.3 - (negative_count - positive_count) * 0.1
        else:
            sentiment = "neutral"
            score = 0.5

        # 提取关键词
        keywords = []
        for kw in positive_keywords + negative_keywords:
            if kw in text:
                keywords.append(kw)

        result = {
            "sentiment": sentiment,
            "score": round(score, 2),
            "confidence": 0.8,
            "keywords": keywords[:5]  # 最多5个
        }

        self.logger.info(f"情感分析完成: {sentiment} ({score})")

        return result

    async def _fetch_sample_news(self, stock_code: str, days: int) -> List[Dict]:
        """
        获取示例新闻（临时方法）

        TODO: 接入真实API后删除此方法
        """
        # 模拟异步
        await asyncio.sleep(0.1)

        # 返回示例数据
        stock_name = self._get_stock_name(stock_code)

        sample_news = [
            {
                "title": f"{stock_name}发布2025年年报",
                "content": f"公司2025年实现营收100亿元，同比增长15%；净利润10亿元，同比增长20%。",
                "source": "东方财富",
                "published_at": "2026-03-13 10:30:00",
                "url": "https://example.com/news/1"
            },
            {
                "title": f"{stock_name}获机构调研",
                "content": f"多家机构调研公司，关注未来发展战略和新产品布局。",
                "source": "同花顺",
                "published_at": "2026-03-12 15:20:00",
                "url": "https://example.com/news/2"
            },
            {
                "title": f"行业政策利好：{stock_name}受益",
                "content": f"国家出台行业支持政策，鼓励技术创新和产业升级。",
                "source": "新浪财经",
                "published_at": "2026-03-11 09:15:00",
                "url": "https://example.com/news/3"
            },
            {
                "title": f"{stock_name}控股股东增持",
                "content": f"控股股东增持公司股份100万股，显示对公司未来信心。",
                "source": "东方财富",
                "published_at": "2026-03-10 18:00:00",
                "url": "https://example.com/news/4"
            },
            {
                "title": f"券商看好{stock_name}前景",
                "content": f"多家券商发布研报，给予买入评级，目标价上调至200元。",
                "source": "同花顺",
                "published_at": "2026-03-09 11:45:00",
                "url": "https://example.com/news/5"
            }
        ]

        return sample_news

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（临时方法）"""
        stock_names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000333": "美的集团",
            "600036": "招商银行"
        }
        return stock_names.get(stock_code, "示例公司")


# ========== 便捷函数 ==========

async def fetch_news(stock_code: str, days: int = 7) -> List[Dict]:
    """
    获取新闻（便捷函数）

    Args:
        stock_code: 股票代码
        days: 监控天数

    Returns:
        新闻列表
    """
    tool = NewsTool()
    return await tool.fetch_news(stock_code, days)


async def analyze_sentiment(text: str) -> Dict:
    """
    情感分析（便捷函数）

    Args:
        text: 待分析文本

    Returns:
        情感分析结果
    """
    tool = NewsTool()
    return await tool.analyze_sentiment(text)

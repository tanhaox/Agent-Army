"""
NLP工具 - 统一管理NLP处理
"""

from typing import Dict, List, Any, Optional
import asyncio

from src.core.logger import get_logger


class NLPTool:
    """
    NLP工具

    职责：
    - 封装所有NLP处理（情感分析、关键词提取、文本摘要等）
    - 提供统一接口给AI Agent使用
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("nlp_tool")
        self.config = config or {}

        self.logger.info("NLP工具初始化完成")

    async def analyze_sentiment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        情感分析

        Args:
            text: 待分析文本

        Returns:
            情感分析结果 {"score": 0-100, "label": "positive/negative/neutral"}
        """
        self.logger.info("开始情感分析")

        # TODO: 接入真实NLP服务
        # 当前使用简单的方法
        result = self._simple_sentiment_analysis(text)

        self.logger.info(f"情感分析完成: {result['label']}")

        return result

    async def extract_keywords(
        self,
        text: str,
        top_n: int = 10
    ) -> List[str]:
        """
        提取关键词

        Args:
            text: 待提取文本
            top_n: 返回前N个关键词

        Returns:
            关键词列表
        """
        self.logger.info(f"提取关键词: top {top_n}")

        # TODO: 接入真实NLP服务
        # 当前使用简单的方法
        keywords = self._simple_keyword_extraction(text, top_n)

        self.logger.info(f"提取到{len(keywords)}个关键词")

        return keywords

    async def summarize(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """
        生成摘要

        Args:
            text: 待摘要文本
            max_length: 最大长度

        Returns:
            摘要文本
        """
        self.logger.info(f"生成摘要: max {max_length}字")

        # TODO: 接入真实NLP服务
        # 当前使用简单的方法
        summary = self._simple_summarize(text, max_length)

        self.logger.info("摘要生成完成")

        return summary

    async def classify_text(
        self,
        text: str,
        categories: List[str]
    ) -> Dict[str, float]:
        """
        文本分类

        Args:
            text: 待分类文本
            categories: 分类类别列表

        Returns:
            各类别概率 {"类别A": 0.85, "类别B": 0.15}
        """
        self.logger.info(f"文本分类: {len(categories)}个类别")

        # TODO: 接入真实NLP服务
        # 当前使用简单的方法
        result = self._simple_classify(text, categories)

        self.logger.info(f"分类完成: {max(result, key=result.get)}")

        return result

    def _simple_keyword_extraction(self, text: str, top_n: int) -> List[str]:
        """
        简单关键词提取（临时方法）

        TODO: 接入真实NLP后删除
        """
        # 金融领域关键词
        financial_keywords = [
            "增长", "下降", "利好", "利空", "业绩", "盈利", "亏损",
            "营收", "净利润", "ROE", "PE", "PB", "估值",
            "增持", "减持", "调研", "研报", "目标价",
            "政策", "行业", "竞争", "市场份额", "护城河",
            "增长", "下滑", "改善", "恶化", "稳定", "波动"
        ]

        # 提取存在的关键词
        found_keywords = []
        for keyword in financial_keywords:
            if keyword in text:
                found_keywords.append(keyword)
                if len(found_keywords) >= top_n:
                    break

        return found_keywords

    def _simple_summarize(self, text: str, max_length: int) -> str:
        """
        简单摘要（临时方法）

        TODO: 接入真实NLP后删除
        """
        # 简单截取前max_length个字符
        if len(text) <= max_length:
            return text

        # 截取到最近的句号
        summary = text[:max_length]
        last_period = summary.rfind("。")
        if last_period > max_length * 0.7:
            summary = summary[:last_period + 1]

        return summary + "..."

    def _simple_classify(self, text: str, categories: List[str]) -> Dict[str, float]:
        """
        简单分类（临时方法）

        TODO: 接入真实NLP后删除
        """
        # 简单统计各类别关键词出现次数
        category_keywords = {
            "业绩公告": ["业绩", "年报", "季报", "营收", "利润"],
            "政策变化": ["政策", "规定", "支持", "限制", "鼓励"],
            "股东增减持": ["增持", "减持", "股东", "回购"],
            "券商研报": ["研报", "券商", "评级", "目标价"],
            "机构调研": ["调研", "机构", "投资者", "交流"]
        }

        scores = {}
        for category in categories:
            keywords = category_keywords.get(category, [])
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score

        # 归一化
        total = sum(scores.values()) if sum(scores.values()) > 0 else 1
        scores = {k: v / total for k, v in scores.items()}

        return scores

    def _simple_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        简单情感分析（临时方法）

        TODO: 接入真实NLP后删除
        """
        # 情感词汇表
        positive_words = [
            "利好", "增长", "盈利", "优秀", "强劲", "领先", "突破",
            "创新", "扩张", "增持", "回购", "目标价", "买入", "推荐",
            "稳健", "优质", "增长", "改善", "超预期", "乐观"
        ]

        negative_words = [
            "利空", "下降", "亏损", "疲软", "下滑", "恶化", "减持",
            "风险", "损失", "下跌", "悲观", "担忧", "压力", "困难",
            "不足", "衰退", "低于预期", "缩水", "拖累"
        ]

        # 统计情感词
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        # 计算情感分数（0-100）
        total = positive_count + negative_count
        if total == 0:
            score = 50  # 中性
        else:
            score = 50 + (positive_count - negative_count) * 10
            score = max(0, min(100, score))

        # 判断情感标签
        if score >= 70:
            label = "positive"
        elif score >= 30:
            label = "neutral"
        else:
            label = "negative"

        return {
            "score": score,
            "label": label,
            "positive_count": positive_count,
            "negative_count": negative_count
        }


# ========== 便捷函数 ==========

async def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    提取关键词（便捷函数）

    Args:
        text: 待提取文本
        top_n: 返回前N个关键词

    Returns:
        关键词列表
    """
    tool = NLPTool()
    return await tool.extract_keywords(text, top_n)


async def summarize(text: str, max_length: int = 200) -> str:
    """
    生成摘要（便捷函数）

    Args:
        text: 待摘要文本
        max_length: 最大长度

    Returns:
        摘要文本
    """
    tool = NLPTool()
    return await tool.summarize(text, max_length)

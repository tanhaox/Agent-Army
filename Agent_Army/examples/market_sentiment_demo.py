"""
市场情绪AI使用示例

演示如何使用MarketSentimentAI进行市场情绪分析
"""

import asyncio
import sys
import os
from pathlib import Path

# Windows控制台UTF-8编码支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.hot_spot.market_sentiment_ai import (
    MarketSentimentAI,
    SentimentAnalysisResult,
    analyze_market_sentiment
)


async def example_1_basic_usage():
    """示例1：基本使用"""
    print("\n" + "="*60)
    print("示例1：基本使用")
    print("="*60)

    # 创建AI实例
    ai = MarketSentimentAI()

    # 分析市场情绪
    result = await ai.analyze("600519", days=7)

    # 打印结果
    print(f"\n📊 市场情绪分析结果:")
    print(f"   Agent名称: {result.agent_name}")
    print(f"   分析类型: {result.analysis_type}")
    print(f"   情感指数: {result.details['sentiment_index']:.1f}分")
    print(f"   市场情绪: {result.details['market_mood']}")
    print(f"   新闻数量: {result.details['news_count']}")
    print(f"   正面新闻: {result.details['positive_count']}")
    print(f"   负面新闻: {result.details['negative_count']}")
    print(f"   中性新闻: {result.details['neutral_count']}")
    print(f"\n   分析结论: {result.conclusion}")
    print(f"   置信度: {result.confidence:.2%}")


async def example_2_standard_result():
    """示例2：获取标准格式结果"""
    print("\n" + "="*60)
    print("示例2：获取标准格式结果（Pydantic模型）")
    print("="*60)

    # 创建AI实例
    ai = MarketSentimentAI()

    # 获取标准格式结果
    result: SentimentAnalysisResult = await ai.get_sentiment_result("000858", days=7)

    # 打印完整结果
    print(f"\n📋 标准格式结果:")
    print(f"   stock_code: {result.stock_code}")
    print(f"   sentiment_index: {result.sentiment_index}")
    print(f"   market_mood: {result.market_mood}")
    print(f"   news_count: {result.news_count}")
    print(f"   positive_count: {result.positive_count}")
    print(f"   negative_count: {result.negative_count}")
    print(f"   neutral_count: {result.neutral_count}")
    print(f"   timestamp: {result.timestamp}")
    print(f"   analysis_period: {result.analysis_period}")

    # 打印关键词
    print(f"\n🔑 热门关键词:")
    for i, keyword in enumerate(result.top_keywords, 1):
        print(f"      {i}. {keyword}")


async def example_3_convenience_function():
    """示例3：使用便捷函数"""
    print("\n" + "="*60)
    print("示例3：使用便捷函数")
    print("="*60)

    # 直接调用便捷函数（无需创建实例）
    result = await analyze_market_sentiment("000333", days=7)

    print(f"\n🚀 便捷函数结果:")
    print(f"   情感指数: {result.sentiment_index:.1f}分")
    print(f"   市场情绪: {result.market_mood}")
    print(f"   新闻统计: 正面{result.positive_count} / 负面{result.negative_count} / 中性{result.neutral_count}")


async def example_4_batch_analysis():
    """示例4：批量分析多只股票"""
    print("\n" + "="*60)
    print("示例4：批量分析多只股票")
    print("="*60)

    # 待分析的股票列表
    stocks = [
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000333", "美的集团"),
        ("600036", "招商银行")
    ]

    # 创建AI实例
    ai = MarketSentimentAI()

    # 批量分析
    results = []
    for stock_code, stock_name in stocks:
        result = await ai.get_sentiment_result(stock_code, days=7)
        results.append((stock_name, result))

    # 打印排名
    print(f"\n📊 市场情绪排名:")
    results.sort(key=lambda x: x[1].sentiment_index, reverse=True)

    for i, (stock_name, result) in enumerate(results, 1):
        mood_icon = {
            "bullish": "📈",
            "neutral": "➡️",
            "bearish": "📉"
        }[result.market_mood]

        print(f"   {i}. {stock_name}: {result.sentiment_index:.1f}分 {mood_icon} ({result.market_mood})")


async def example_5_custom_config():
    """示例5：使用自定义配置"""
    print("\n" + "="*60)
    print("示例5：使用自定义配置")
    print("="*60)

    # 自定义配置
    custom_config = {
        "default_days": 14,
        "sentiment_thresholds": {
            "bullish": 70.0,  # 更严格的乐观阈值
            "bearish": 30.0   # 更严格的悲观阈值
        }
    }

    # 创建带配置的AI实例
    ai = MarketSentimentAI(config=custom_config)

    # 分析
    result = await ai.get_sentiment_result("600519", days=14)

    print(f"\n⚙️  使用自定义配置分析:")
    print(f"   分析周期: {result.analysis_period}")
    print(f"   情感指数: {result.sentiment_index:.1f}分")
    print(f"   市场情绪: {result.market_mood}")
    print(f"   阈值设置: bullish≥70, bearish≤30")


async def example_6_risk_analysis():
    """示例6：风险分析"""
    print("\n" + "="*60)
    print("示例6：风险分析")
    print("="*60)

    ai = MarketSentimentAI()

    # 获取完整分析结果
    result = await ai.analyze("600519", days=7)

    # 打印风险提示
    print(f"\n⚠️  风险提示:")
    if result.risks:
        for i, risk in enumerate(result.risks, 1):
            print(f"   {i}. {risk}")
    else:
        print("   无明显风险")

    # 打印投资建议
    print(f"\n💡 投资建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"   {i}. {rec}")


async def main():
    """运行所有示例"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "市场情绪AI使用示例" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await example_1_basic_usage()
        await example_2_standard_result()
        await example_3_convenience_function()
        await example_4_batch_analysis()
        await example_5_custom_config()
        await example_6_risk_analysis()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "✅ 所有示例完成！" + " "*20 + "║")
        print("╚"+"═"*58+"╝")

    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

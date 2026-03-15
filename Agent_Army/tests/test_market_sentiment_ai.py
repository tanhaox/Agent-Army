"""
测试市场情绪AI - MarketSentimentAI (新版本)

测试内容：
1. 基本功能测试
2. 工具库集成测试
3. 返回值结构测试
4. 异常处理测试
5. BaseBusinessAgent继承测试
"""
import pytest

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

import asyncio
from datetime import datetime

from src.agents.business.hot_spot.market_sentiment_ai import (
    MarketSentimentAI,
    SentimentAnalysisResult,
    analyze_market_sentiment
)


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：市场情绪AI初始化")
    print("="*60)

    ai = MarketSentimentAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 所属军团: {ai.corps}")
    print(f"✅ 分析类型: {ai.analysis_type}")

    # 检查工具
    assert ai.news_tool is not None, "NewsTool未初始化"
    assert ai.nlp_tool is not None, "NLPTool未初始化"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_analyze_basic():
    """测试2：基本分析功能"""
    print("\n" + "="*60)
    print("测试2：基本分析功能")
    print("="*60)

    ai = MarketSentimentAI()

    # 执行分析
    result = await ai.analyze("600519", days=7)

    # 验证返回结构
    assert result is not None, "分析结果不应为空"
    assert result.agent_name == "市场情绪AI", "Agent名称不匹配"
    assert result.analysis_type == "市场情绪分析", "分析类型不匹配"
    assert result.conclusion is not None, "结论不应为空"
    assert 0.0 <= result.confidence <= 1.0, "置信度应在0-1之间"

    # 验证详细信息
    details = result.details
    assert "sentiment_index" in details, "缺少sentiment_index"
    assert "market_mood" in details, "缺少market_mood"
    assert "news_count" in details, "缺少news_count"
    assert "positive_count" in details, "缺少positive_count"
    assert "negative_count" in details, "缺少negative_count"
    assert "neutral_count" in details, "缺少neutral_count"

    # 验证情感指数范围
    assert 0.0 <= details["sentiment_index"] <= 100.0, "情感指数应在0-100之间"

    # 验证市场情绪类型
    assert details["market_mood"] in ["bullish", "neutral", "bearish"], "市场情绪类型无效"

    print(f"\n📊 分析结果:")
    print(f"   股票代码: 600519")
    print(f"   情感指数: {details['sentiment_index']}")
    print(f"   市场情绪: {details['market_mood']}")
    print(f"   新闻数量: {details['news_count']}")
    print(f"   正面新闻: {details['positive_count']}")
    print(f"   负面新闻: {details['negative_count']}")
    print(f"   中性新闻: {details['neutral_count']}")
    print(f"\n   结论: {result.conclusion}")
    print(f"   置信度: {result.confidence}")

    print("\n✅ 基本分析测试通过")


@pytest.mark.asyncio
async def test_sentiment_result_structure():
    """测试3：标准格式结果"""
    print("\n" + "="*60)
    print("测试3：标准格式结果")
    print("="*60)

    ai = MarketSentimentAI()

    # 获取标准格式结果
    result = await ai.get_sentiment_result("600519", days=7)

    # 验证Pydantic模型
    assert isinstance(result, SentimentAnalysisResult), "应该是SentimentAnalysisResult类型"

    # 验证必需字段
    assert result.stock_code == "600519", "股票代码不匹配"
    assert 0.0 <= result.sentiment_index <= 100.0, "情感指数应在0-100之间"
    assert result.market_mood in ["bullish", "neutral", "bearish"], "市场情绪类型无效"
    assert result.news_count >= 0, "新闻数量不能为负"
    assert result.positive_count >= 0, "正面新闻数不能为负"
    assert result.negative_count >= 0, "负面新闻数不能为负"
    assert result.neutral_count >= 0, "中性新闻数不能为负"

    # 验证数据一致性
    total = result.positive_count + result.negative_count + result.neutral_count
    assert total == result.news_count, "正+负+中性应等于总数"

    # 验证时间戳格式
    try:
        datetime.fromisoformat(result.timestamp)
    except ValueError:
        assert False, "时间戳格式无效"

    print(f"\n✅ Pydantic模型验证通过:")
    print(f"   stock_code: {result.stock_code}")
    print(f"   sentiment_index: {result.sentiment_index}")
    print(f"   market_mood: {result.market_mood}")
    print(f"   news_count: {result.news_count}")
    print(f"   timestamp: {result.timestamp}")

    print("\n✅ 标准格式测试通过")


@pytest.mark.asyncio
async def test_market_mood_determination():
    """测试4：市场情绪判定"""
    print("\n" + "="*60)
    print("测试4：市场情绪判定")
    print("="*60)

    ai = MarketSentimentAI()

    # 测试多只股票
    test_stocks = [
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000333", "美的集团")
    ]

    for stock_code, stock_name in test_stocks:
        result = await ai.get_sentiment_result(stock_code, days=7)

        # 验证情绪判定逻辑
        if result.market_mood == "bullish":
            assert result.sentiment_index >= 60.0, "bullish时指数应>=60"
        elif result.market_mood == "bearish":
            assert result.sentiment_index <= 40.0, "bearish时指数应<=40"
        else:
            assert 40.0 < result.sentiment_index < 60.0, "neutral时指数应在40-60之间"

        print(f"   {stock_name}: {result.sentiment_index:.1f}分 ({result.market_mood})")

    print("\n✅ 市场情绪判定测试通过")


@pytest.mark.asyncio
async def test_keyword_extraction():
    """测试5：关键词提取"""
    print("\n" + "="*60)
    print("测试5：关键词提取")
    print("="*60)

    ai = MarketSentimentAI()
    result = await ai.get_sentiment_result("600519", days=7)

    # 验证关键词
    assert isinstance(result.top_keywords, list), "关键词应该是列表"
    assert len(result.top_keywords) <= 10, "关键词不应超过10个"

    # 验证关键词类型
    for keyword in result.top_keywords:
        assert isinstance(keyword, str), "关键词应该是字符串"
        assert len(keyword) > 0, "关键词不应为空"

    print(f"\n🔑 热门关键词 ({len(result.top_keywords)}个):")
    for i, keyword in enumerate(result.top_keywords, 1):
        print(f"   {i}. {keyword}")

    print("\n✅ 关键词提取测试通过")


@pytest.mark.asyncio
async def test_risks_and_recommendations():
    """测试6：风险提示和建议"""
    print("\n" + "="*60)
    print("测试6：风险提示和建议")
    print("="*60)

    ai = MarketSentimentAI()
    result = await ai.analyze("600519", days=7)

    # 验证风险提示
    assert isinstance(result.risks, list), "风险提示应该是列表"

    print(f"\n⚠️  风险提示 ({len(result.risks)}条):")
    for i, risk in enumerate(result.risks, 1):
        print(f"   {i}. {risk}")

    # 验证建议
    assert isinstance(result.recommendations, list), "建议应该是列表"
    assert len(result.recommendations) > 0, "建议不应为空"

    print(f"\n💡 投资建议 ({len(result.recommendations)}条):")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"   {i}. {rec}")

    print("\n✅ 风险提示和建议测试通过")


@pytest.mark.asyncio
async def test_confidence_calculation():
    """测试7：置信度计算"""
    print("\n" + "="*60)
    print("测试7：置信度计算")
    print("="*60)

    ai = MarketSentimentAI()

    # 测试不同时间范围
    for days in [3, 7, 14]:
        result = await ai.analyze("600519", days=days)
        print(f"   {days}天分析: 置信度={result.confidence:.2f}")

        # 验证置信度范围
        assert 0.0 <= result.confidence <= 1.0, "置信度应在0-1之间"

    print("\n✅ 置信度计算测试通过")


@pytest.mark.asyncio
async def test_invalid_stock_code():
    """测试8：无效股票代码"""
    print("\n" + "="*60)
    print("测试8：无效股票代码")
    print("="*60)

    ai = MarketSentimentAI()

    # 测试无效代码
    invalid_codes = ["invalid", "12345", "abcdef", ""]
    for code in invalid_codes:
        try:
            await ai.analyze(code)
            assert False, f"应该抛出ValueError: {code}"
        except ValueError as e:
            print(f"   ✅ 正确拒绝无效代码: {code}")

    print("\n✅ 无效股票代码测试通过")


@pytest.mark.asyncio
async def test_convenience_function():
    """测试9：便捷函数"""
    print("\n" + "="*60)
    print("测试9：便捷函数")
    print("="*60)

    # 使用便捷函数
    result = await analyze_market_sentiment("600519", days=7)

    # 验证结果
    assert isinstance(result, SentimentAnalysisResult), "应该返回SentimentAnalysisResult"
    assert result.stock_code == "600519", "股票代码不匹配"

    print(f"\n🚀 便捷函数结果:")
    print(f"   情感指数: {result.sentiment_index}")
    print(f"   市场情绪: {result.market_mood}")
    print(f"   新闻数量: {result.news_count}")

    print("\n✅ 便捷函数测试通过")


@pytest.mark.asyncio
async def test_tool_integration():
    """测试10：工具集成"""
    print("\n" + "="*60)
    print("测试10：工具库集成")
    print("="*60)

    ai = MarketSentimentAI()

    # 验证工具已初始化
    assert ai.news_tool is not None, "NewsTool未初始化"
    assert ai.nlp_tool is not None, "NLPTool未初始化"

    print(f"   ✅ NewsTool: {type(ai.news_tool).__name__}")
    print(f"   ✅ NLPTool: {type(ai.nlp_tool).__name__}")

    # 执行分析（会自动调用工具）
    result = await ai.analyze("600519", days=7)

    # 验证工具调用成功
    assert result.details["news_count"] > 0, "NewsTool应该返回新闻"
    assert result.details["positive_count"] + result.details["negative_count"] + result.details["neutral_count"] > 0, "NLPTool应该分析情感"

    print(f"\n   📊 工具调用结果:")
    print(f"      NewsTool: 获取{result.details['news_count']}条新闻")
    print(f"      NLPTool: 分析{result.details['news_count']}条新闻情感")

    print("\n✅ 工具集成测试通过")


@pytest.mark.asyncio
async def test_base_business_agent_inheritance():
    """测试11：BaseBusinessAgent继承"""
    print("\n" + "="*60)
    print("测试11：BaseBusinessAgent继承")
    print("="*60)

    ai = MarketSentimentAI()

    # 验证继承
    from src.agents.business.base_business_agent import BusinessAgent
    assert isinstance(ai, BusinessAgent), "应该继承BusinessAgent"

    # 验证必需属性
    assert hasattr(ai, 'corps'), "应该有corps属性"
    assert hasattr(ai, 'analysis_type'), "应该有analysis_type属性"
    assert hasattr(ai, 'analyze'), "应该有analyze方法"
    assert hasattr(ai, 'validate_stock_code'), "应该有validate_stock_code方法"

    # 测试validate_stock_code方法
    assert ai.validate_stock_code("600519") == True, "600519应该是有效代码"
    assert ai.validate_stock_code("invalid") == False, "invalid应该是无效代码"

    print(f"   ✅ 继承自: BusinessAgent")
    print(f"   ✅ 所属军团: {ai.corps}")
    print(f"   ✅ 分析类型: {ai.analysis_type}")
    print(f"   ✅ validate_stock_code: 正常工作")

    print("\n✅ 继承测试通过")


@pytest.mark.asyncio
async def test_custom_config():
    """测试12：自定义配置"""
    print("\n" + "="*60)
    print("测试12：自定义配置")
    print("="*60)

    # 自定义配置
    custom_config = {
        "default_days": 14,
        "sentiment_thresholds": {
            "bullish": 70.0,
            "bearish": 30.0
        }
    }

    ai = MarketSentimentAI(config=custom_config)

    # 验证配置生效
    assert ai.default_days == 14, "default_days应该是14"
    assert ai.sentiment_thresholds["bullish"] == 70.0, "bullish阈值应该是70"
    assert ai.sentiment_thresholds["bearish"] == 30.0, "bearish阈值应该是30"

    print(f"   ✅ default_days: {ai.default_days}")
    print(f"   ✅ bullish阈值: {ai.sentiment_thresholds['bullish']}")
    print(f"   ✅ bearish阈值: {ai.sentiment_thresholds['bearish']}")

    # 测试配置生效
    result = await ai.get_sentiment_result("600519", days=14)
    assert result.analysis_period == "14天", "应该使用配置的天数"

    print(f"\n   使用配置分析: {result.analysis_period}")
    print(f"   情感指数: {result.sentiment_index} (阈值: bullish≥70, bearish≤30)")

    print("\n✅ 自定义配置测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "市场情绪AI测试套件" + " "*18 + "║")
    print("║" + " "*15 + "BaseBusinessAgent版本" + " "*15 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_analyze_basic()
        await test_sentiment_result_structure()
        await test_market_mood_determination()
        await test_keyword_extraction()
        await test_risks_and_recommendations()
        await test_confidence_calculation()
        await test_invalid_stock_code()
        await test_convenience_function()
        await test_tool_integration()
        await test_base_business_agent_inheritance()
        await test_custom_config()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 基本分析测试通过")
        print("   - ✅ 标准格式测试通过")
        print("   - ✅ 市场情绪判定测试通过")
        print("   - ✅ 关键词提取测试通过")
        print("   - ✅ 风险提示和建议测试通过")
        print("   - ✅ 置信度计算测试通过")
        print("   - ✅ 无效股票代码测试通过")
        print("   - ✅ 便捷函数测试通过")
        print("   - ✅ 工具集成测试通过")
        print("   - ✅ 继承测试通过")
        print("   - ✅ 自定义配置测试通过")

        print("\n📋 功能验证:")
        print("   - ✅ 继承BaseBusinessAgent")
        print("   - ✅ 使用NewsTool获取新闻")
        print("   - ✅ 使用NLPTool分析情感")
        print("   - ✅ 返回标准Pydantic模型")
        print("   - ✅ 计算情感指数(0-100)")
        print("   - ✅ 判断市场情绪(bullish/neutral/bearish)")
        print("   - ✅ 提取关键词")
        print("   - ✅ 生成风险提示和建议")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

"""
测试工具库基础功能
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.asyncio
async def test_tools():
    """测试工具库"""

    print("\n" + "=" * 60)
    print("  测试工具库")
    print("=" * 60)

    # ========== 1. NewsTool ==========
    print("\n[1] NewsTool（新闻工具）")
    print("-" * 60)

    from src.core.tools.data_source import NewsTool

    news_tool = NewsTool()
    print(f"✅ 初始化成功")

    # 获取新闻
    news = await news_tool.fetch_news("600519", 7)
    print(f"✅ 获取到{len(news)}条新闻")

    if news:
        print(f"   示例: {news[0]['title']}")

    # 情感分析
    sentiment = await news_tool.analyze_sentiment("公司业绩增长，利润大幅提升")
    print(f"✅ 情感分析: {sentiment['sentiment']} ({sentiment['score']})")

    # ========== 2. FinancialTool ==========
    print("\n[2] FinancialTool（财务数据工具）")
    print("-" * 60)

    from src.core.tools.data_source import FinancialTool

    financial_tool = FinancialTool()
    print(f"✅ 初始化成功")

    # 获取财务数据
    data = await financial_tool.fetch_financial_data("600519", 3)
    print(f"✅ 获取到财务数据")
    print(f"   股票: {data['stock_name']}")
    print(f"   ROE: {data['latest']['roe']}%")

    # ========== 3. LLMTool ==========
    print("\n[3] LLMTool（大模型工具）")
    print("-" * 60)

    from src.core.tools.ai_service import LLMTool

    llm_tool = LLMTool()
    print(f"✅ 初始化成功")

    # 调用大模型
    response = await llm_tool.chat("请用一句话总结贵州茅台的投资价值", model="glm-4")
    print(f"✅ LLM响应: {response[:50]}...")

    # ========== 4. NLPTool ==========
    print("\n[4] NLPTool（NLP工具）")
    print("-" * 60)

    from src.core.tools.ai_service import NLPTool

    nlp_tool = NLPTool()
    print(f"✅ 初始化成功")

    # 提取关键词
    text = "贵州茅台发布2025年年报，营收增长15%，净利润增长20%，ROE达到15%"
    keywords = await nlp_tool.extract_keywords(text, top_n=5)
    print(f"✅ 提取关键词: {keywords}")

    # 生成摘要
    summary = await nlp_tool.summarize(text, max_length=50)
    print(f"✅ 生成摘要: {summary}")

    # ========== 5. FormulaTool ==========
    print("\n[5] FormulaTool（公式工具）")
    print("-" * 60)

    from src.core.tools.calculation import FormulaTool

    formula_tool = FormulaTool()
    print(f"✅ 初始化成功")

    # 计算ROE
    roe_data = {
        "net_profit": 1500000000,
        "net_assets": 10000000000
    }
    roe = formula_tool.calculate("roe", roe_data)
    print(f"✅ ROE计算: {roe}%")

    # 计算综合评分
    score_data = {
        "roe": 15.5,
        "revenue_growth": 12.0,
        "profit_growth": 18.0,
        "pe": 20,
        "debt_ratio": 40.0
    }
    score = formula_tool.calculate("composite_score", score_data)
    print(f"✅ 综合评分: {score}/100")

    # 列出所有公式
    all_formulas = formula_tool.list_formulas()
    print(f"✅ 标准公式: {len(all_formulas['standard'])}个")
    print(f"✅ 私有公式: {len(all_formulas['private'])}组")

    print("\n" + "=" * 60)
    print("  ✅ 工具库测试全部通过!")
    print("=" * 60)

    print("\n工具库功能:")
    print("1. ✅ NewsTool: 新闻获取、情感分析")
    print("2. ✅ FinancialTool: 财务数据获取")
    print("3. ✅ LLMTool: 大模型调用（智谱/DeepSeek/OpenAI）")
    print("4. ✅ NLPTool: 关键词提取、摘要生成")
    print("5. ✅ FormulaTool: 公式计算（标准+私有）")


if __name__ == "__main__":
    asyncio.run(test_tools())

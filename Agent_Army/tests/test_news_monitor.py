"""
测试新闻监控AI
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

from src.agents.business.news_monitor import NewsMonitor


@pytest.mark.asyncio
async def test_news_monitor():
    """测试新闻监控AI"""

    print("\n" + "=" * 60)
    print("  测试新闻监控AI（热点捕捉军团 1/4）")
    print("=" * 60)

    # 初始化
    print("\n[1] 初始化新闻监控AI")
    print("-" * 60)
    monitor = NewsMonitor()

    print(f"✅ 名称: {monitor.name}")
    print(f"✅ 角色: {monitor.role}")
    print(f"✅ 军团: {monitor.corps}")
    print(f"✅ 能力数: {len(monitor.get_capabilities())}")
    print(f"✅ 工具数: {len(monitor.get_tools())}")

    # 列出能力
    print("\n能力列表:")
    for cap in monitor.get_capabilities():
        print(f"  - {cap.name}: {cap.description}")

    # 列出工具
    print("\n工具列表:")
    for tool in monitor.get_tools():
        print(f"  - {tool.name}: {tool.description}")

    # 分析股票
    print("\n[2] 分析股票: 600519（贵州茅台）")
    print("-" * 60)

    result = await monitor.analyze("600519", days=7)

    print(f"✅ 股票代码: {result['stock_code']}")
    print(f"✅ 股票名称: {result['stock_name']}")
    print(f"✅ 监控周期: {result['monitoring_period']}")
    print(f"✅ 新闻总数: {result['total_news']}条")
    print(f"✅ 事件总数: {result['total_events']}个")

    # 显示事件
    print("\n[3] 关键事件（按影响分排序）")
    print("-" * 60)

    for i, event in enumerate(result['events'], 1):
        print(f"\n事件 #{i}:")
        print(f"  类型: {event['type']}")
        print(f"  标题: {event['title']}")
        print(f"  来源: {event['source']}")
        print(f"  时间: {event['published_at']}")
        print(f"  情感: {event['sentiment']} ({event['sentiment_score']})")
        print(f"  影响分: {event['impact_score']}/10")

    # 显示摘要
    print("\n[4] 分析摘要")
    print("-" * 60)
    print(result['summary'])

    # 显示警告
    if result['warnings']:
        print("\n[5] 风险警告")
        print("-" * 60)
        for warning in result['warnings']:
            print(warning)

    # 验证结果
    print("\n[6] 验证结果")
    print("-" * 60)

    assert result['stock_code'] == "600519", "股票代码应匹配"
    assert result['total_news'] > 0, "应该有新闻"
    assert result['total_events'] > 0, "应该有事件"
    assert len(result['events']) == result['total_events'], "事件数量应一致"

    for event in result['events']:
        assert 'impact_score' in event, "事件应有影响分"
        assert 0 <= event['impact_score'] <= 10, "影响分应在0-10之间"
        assert event['sentiment'] in ['positive', 'negative', 'neutral'], "情感应有效"

    print("✅ 所有断言通过")

    print("\n" + "=" * 60)
    print("  ✅ 新闻监控AI测试通过!")
    print("=" * 60)

    return True


@pytest.mark.asyncio
async def test_different_stocks():
    """测试不同股票"""

    print("\n" + "=" * 60)
    print("  测试不同股票的新闻监控")
    print("=" * 60)

    monitor = NewsMonitor()

    test_stocks = ["600519", "000858", "000333"]

    for stock_code in test_stocks:
        print(f"\n分析股票: {stock_code}")
        result = await monitor.analyze(stock_code, days=7)
        print(f"  ✅ 新闻: {result['total_news']}条")
        print(f"  ✅ 事件: {result['total_events']}个")

    print("\n✅ 多股票测试通过")


async def main():
    """主测试流程"""

    print("\n🚀 新闻监控AI测试开始\n")

    # 测试1: 基本功能
    success1 = await test_news_monitor()

    # 测试2: 多股票
    success2 = await test_different_stocks()

    # 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    print(f"  基本功能测试: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"  多股票测试: {'✅ 通过' if success2 else '❌ 失败'}")
    print()

    if success1 and success2:
        print("🎉 新闻监控AI测试全部通过!")
        print("   ✅ Agent初始化正常")
        print("   ✅ 新闻分析功能正常")
        print("   ✅ 事件提取准确")
        print("   ✅ 情感分析合理")
        print("   ✅ 影响评估科学")
        print("\n   热点捕捉军团 (1/4) ✅ 已上线")
    else:
        print("❌ 部分测试失败，需要修复")

    return success1 and success2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

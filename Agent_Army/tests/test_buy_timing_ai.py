"""
测试买入时机AI
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.strategy.buy_timing_ai import BuyTimingAI


@pytest.mark.asyncio
async def test_buy_timing_ai():
    """测试买入时机AI"""

    print("\n" + "=" * 60)
    print("  测试买入时机AI")
    print("=" * 60)

    # 初始化
    print("\n[1] 初始化")
    print("-" * 60)
    ai = BuyTimingAI()
    print(f"✅ 初始化成功: {ai.name}")

    # 分析
    print("\n[2] 分析买入时机（600519）")
    print("-" * 60)
    result = await ai.analyze("600519")

    print(f"✅ 分析完成")
    print(f"   股票: {result['stock_name']}")
    print(f"   时机评分: {result['timing_score']}分")
    print(f"   时机等级: {result['timing_level']}")
    print(f"   买入建议: {result['recommendation']}")

    # 分项评分
    print("\n[3] 分项评分")
    print("-" * 60)
    for key, value in result['scores'].items():
        print(f"   {key}: {value}分")

    # 风险提示
    print("\n[4] 风险提示")
    print("-" * 60)
    for warning in result['warnings']:
        print(f"   {warning}")

    # 总结
    print("\n[5] 总结")
    print("-" * 60)
    print(f"   {result['summary']}")

    print("\n" + "=" * 60)
    print("  ✅ 买入时机AI测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_buy_timing_ai())

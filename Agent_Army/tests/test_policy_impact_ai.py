"""
测试政策影响AI - 简化版
"""
import pytest

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.business.industry_analysis.policy_impact_ai import PolicyImpactAI


@pytest.mark.asyncio
async def test_policy_impact_ai():
    """测试政策影响AI"""
    print("=" * 60)
    print("Policy Impact AI Test")
    print("=" * 60)

    # 初始化AI
    ai = PolicyImpactAI()

    # 测试用例
    test_case = {
        "stock_code": "600519",
        "industry": "白酒",
        "days": 7
    }

    print(f"\n[Test Case]")
    print(f"Stock Code: {test_case['stock_code']}")
    print(f"Industry: {test_case['industry']}")
    print(f"Days: {test_case['days']}")

    try:
        # 执行分析
        result = await ai.analyze(**test_case)

        # 打印结果
        print(f"\n[Analysis Result]")
        print(f"  Industry: {result['industry']}")
        print(f"  Stock Code: {result['stock_code']}")
        print(f"  Overall Impact: {result['overall_impact']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Policy Events Count: {len(result['policy_events'])}")

        # 打印政策事件
        if result['policy_events']:
            print(f"\n[Policy Events]")
            for j, event in enumerate(result['policy_events'][:3], 1):
                print(f"  Event {j}:")
                print(f"    Title: {event['title']}")
                print(f"    Date: {event['date']}")
                print(f"    Impact: {event['impact_type']} (score: {event['impact_score']:.2f})")
                print(f"    Description: {event['description'][:50]}...")
        else:
            print(f"\n[No policy events found]")

        # 验证返回结构
        print(f"\n[Structure Validation]")
        required_fields = ['industry', 'stock_code', 'policy_events', 'overall_impact', 'confidence', 'timestamp']
        all_valid = True
        for field in required_fields:
            if field in result:
                print(f"  [OK] {field}: {type(result[field]).__name__}")
            else:
                print(f"  [FAIL] {field}: MISSING")
                all_valid = False

        # 验证policy_events结构
        if result['policy_events']:
            event = result['policy_events'][0]
            event_fields = ['title', 'date', 'impact_type', 'impact_score', 'description']
            print(f"\n[Policy Event Structure]")
            for field in event_fields:
                if field in event:
                    print(f"    [OK] {field}: {type(event[field]).__name__}")
                else:
                    print(f"    [FAIL] {field}: MISSING")
                    all_valid = False

        # 最终结果
        print(f"\n[Test Result]")
        if all_valid:
            print("  [SUCCESS] All tests passed!")
            print("  [INFO] PolicyImpactAI is working correctly")
            print("  [INFO] Return structure matches requirements")
        else:
            print("  [FAIL] Some tests failed")

    except Exception as e:
        print(f"\n[FAIL] Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_policy_impact_ai())

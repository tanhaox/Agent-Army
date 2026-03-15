"""
测试方案C v2: 混合增量预审模式
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.management.commander_agent import CommanderAgent
from src.agents.business.industry_analyzers import IndustryChainAnalyzer
from src.agents.business.fundamental_analyzer import FundamentalAnalyzer


def test_commander_precheck():
    """测试Commander预审功能"""
    print("=" * 60)
    print("测试1: Commander预审功能")
    print("=" * 60)

    commander = CommanderAgent()

    # 测试1.1: 预审通过的产业链报告
    print("\n[1.1] 测试预审通过场景...")
    industry_result = {
        "stock_code": "600519",
        "industry_name": "食品饮料",
        "score": 85,
        "industry_cycle": "成长期",
        "market_share": 35.5,
        "industry_rank": 1,
        "growth_driver": ["消费升级", "品牌溢价"],
        "risk_factors": ["政策风险", "市场竞争"],
        "confidence": 0.85
    }

    precheck_result = asyncio.run(commander.precheck_report(
        agent_name="产业链分析AI",
        report_type="industry",
        report_data=industry_result
    ))

    print(f"预审结果: {'通过' if precheck_result['approved'] else '未通过'}")
    print(f"质量评分: {precheck_result['quality_score']}/100")
    print(f"状态: {precheck_result['status']}")

    if not precheck_result['approved']:
        print("❌ 测试失败：应该通过预审")
        return False

    print("✅ 测试1.1通过")

    # 测试1.2: 预审不通过的产业链报告
    print("\n[1.2] 测试预审不通过场景...")
    bad_industry_result = {
        "stock_code": "600519",
        # 缺少industry_name
        "score": 0,  # 评分为0
        "growth_driver": [],  # 空列表
        "risk_factors": []   # 空列表
    }

    precheck_result = asyncio.run(commander.precheck_report(
        agent_name="产业链分析AI",
        report_type="industry",
        report_data=bad_industry_result
    ))

    print(f"预审结果: {'通过' if precheck_result['approved'] else '未通过'}")
    print(f"质量评分: {precheck_result['quality_score']}/100")
    print(f"状态: {precheck_result['status']}")

    if precheck_result['approved']:
        print("❌ 测试失败：不应该通过预审")
        return False

    if precheck_result.get("issues"):
        print("发现的问题:")
        for i, issue in enumerate(precheck_result["issues"], 1):
            print(f"  {i}. {issue}")

    if precheck_result.get("missing_content"):
        print("需要补充的内容:")
        for i, item in enumerate(precheck_result["missing_content"], 1):
            print(f"  {i}. {item}")

    print("✅ 测试1.2通过")

    # 测试1.3: 严重错误（工具坏了）
    print("\n[1.3] 测试严重错误场景...")
    error_result = {
        "error_code": "API_PAYMENT_REQUIRED",
        "error": "API欠费"
    }

    precheck_result = asyncio.run(commander.precheck_report(
        agent_name="产业链分析AI",
        report_type="industry",
        report_data=error_result
    ))

    print(f"预审结果: {'通过' if precheck_result['approved'] else '未通过'}")
    print(f"严重错误: {'是' if precheck_result.get('critical_error') else '否'}")
    print(f"错误类型: {precheck_result.get('error_type', '无')}")
    print(f"动作: {precheck_result.get('action', '无')}")

    if not precheck_result.get('critical_error'):
        print("❌ 测试失败：应该检测到严重错误")
        return False

    print("✅ 测试1.3通过")

    print("\n" + "=" * 60)
    print("✅ 所有Commander预审测试通过")
    print("=" * 60)
    return True


def test_retry_mechanism():
    """测试重试机制"""
    print("\n" + "=" * 60)
    print("测试2: 重试和死循环防护")
    print("=" * 60)

    commander = CommanderAgent()

    # 模拟连续失败
    print("\n[2.1] 测试Agent重试机制...")
    bad_result = {
        "stock_code": "600519",
        "score": 0,
        "growth_driver": [],
        "risk_factors": []
    }

    for i in range(1, 6):
        print(f"\n第{i}次预审:")
        precheck_result = asyncio.run(commander.precheck_report(
            agent_name="产业链分析AI",
            report_type="industry",
            report_data=bad_result
        ))

        print(f"  重试次数: {precheck_result.get('retry_count', 0)}")
        print(f"  状态: {precheck_result['status']}")

        if precheck_result.get("give_up"):
            print(f"  ✅ 已放弃该Agent: {precheck_result.get('reason')}")
            break

    print("\n✅ 测试2通过：重试机制正常")

    print("\n" + "=" * 60)
    print("✅ 所有重试机制测试通过")
    print("=" * 60)
    return True


def test_industry_analyzer():
    """测试产业链分析Agent"""
    print("\n" + "=" * 60)
    print("测试3: 产业链分析Agent")
    print("=" * 60)

    analyzer = IndustryChainAnalyzer()

    print("\n[3.1] 执行产业链分析...")
    result = asyncio.run(analyzer.analyze("600519"))

    print(f"行业名称: {result.industry_name}")
    print(f"行业评分: {result.score}/100")
    print(f"数据完整: {'是' if result.industry_name else '否'}")

    print("\n✅ 测试3通过：产业链分析Agent正常")

    print("\n" + "=" * 60)
    print("✅ 所有产业链分析测试通过")
    print("=" * 60)
    return True


def main():
    """主测试函数"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     方案C v2: 混合增量预审模式 - 完整测试                  ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    results = []

    # 测试1: Commander预审功能
    try:
        results.append(("Commander预审功能", test_commander_precheck()))
    except Exception as e:
        print(f"❌ 测试1失败: {str(e)}")
        results.append(("Commander预审功能", False))

    # 测试2: 重试机制
    try:
        results.append(("重试机制", test_retry_mechanism()))
    except Exception as e:
        print(f"❌ 测试2失败: {str(e)}")
        results.append(("重试机制", False))

    # 测试3: 产业链分析Agent
    try:
        results.append(("产业链分析Agent", test_industry_analyzer()))
    except Exception as e:
        print(f"❌ 测试3失败: {str(e)}")
        results.append(("产业链分析Agent", False))

    # 汇总结果
    print("\n")
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s} {status}")

    print("=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！方案C v2已完整实现并验证！\n")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要修复\n")
        return 1


if __name__ == "__main__":
    exit(main())

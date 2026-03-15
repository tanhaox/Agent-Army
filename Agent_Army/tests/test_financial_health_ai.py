"""
财务健康AI测试

测试核心功能：
1. 财务健康度分析
2. 财务风险评估
3. 财务异常识别
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
from src.agents.business.stock.financial_health_ai import FinancialHealthAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：财务健康AI初始化")
    print("="*60)

    ai = FinancialHealthAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "financial_health_analysis" in capability_names, "缺少财务健康分析能力"
    assert "risk_assessment" in capability_names, "缺少风险评估能力"
    assert "anomaly_detection" in capability_names, "缺少异常检测能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_health_analysis():
    """测试2：财务健康度分析"""
    print("\n" + "="*60)
    print("测试2：财务健康度分析")
    print("="*60)

    ai = FinancialHealthAI()

    # 分析贵州茅台的财务健康
    result = await ai.execute(
        "analyze_health",
        stock_code="600519",
        years=3
    )

    print(f"\n💰 财务健康度分析结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   分析周期: {result['analysis_period']}")
    print(f"   健康度评分: {result['health_score']}")
    print(f"   健康度等级: {result['health_grade']}")
    print(f"\n   偿债能力: {result['health_metrics']['偿债能力']['status']} ({result['health_metrics']['偿债能力']['score']}分)")
    print(f"   盈利能力: {result['health_metrics']['盈利能力']['status']} ({result['health_metrics']['盈利能力']['score']}分)")
    print(f"   成长能力: {result['health_metrics']['成长能力']['status']} ({result['health_metrics']['成长能力']['score']}分)")
    print(f"   现金流: {result['health_metrics']['现金流']['status']} ({result['health_metrics']['现金流']['score']}分)")
    print(f"\n   摘要: {result['summary']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 0 <= result['health_score'] <= 100, "健康度评分应该在0-100之间"
    assert result['health_grade'] in ['A+', 'A', 'B', 'C', 'D'], "健康度等级不对"

    print("\n✅ 财务健康度分析测试通过")


@pytest.mark.asyncio
async def test_risk_assessment():
    """测试3：财务风险评估"""
    print("\n" + "="*60)
    print("测试3：财务风险评估")
    print("="*60)

    ai = FinancialHealthAI()

    # 评估财务风险
    result = await ai.execute(
        "assess_risk",
        stock_code="600519"
    )

    print(f"\n⚠️ 财务风险评估结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   风险等级: {result['risk_level']}")
    print(f"   风险因素数量: {len(result['risk_factors'])}")

    if result['risk_factors']:
        print(f"\n   风险因素:")
        for i, risk in enumerate(result['risk_factors'], 1):
            print(f"      {i}. [{risk['severity']}] {risk['type']}: {risk['description']}")

    if result['warning_signals']:
        print(f"\n   警告信号:")
        for signal in result['warning_signals']:
            print(f"      - {signal}")

    print(f"\n   摘要: {result['summary']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert result['risk_level'] in ["极高风险", "高风险", "中风险", "低风险", "安全"], "风险等级不对"

    print("\n✅ 财务风险评估测试通过")


@pytest.mark.asyncio
async def test_anomaly_detection():
    """测试4：财务异常识别"""
    print("\n" + "="*60)
    print("测试4：财务异常识别")
    print("="*60)

    ai = FinancialHealthAI()

    # 识别财务异常
    result = await ai.execute(
        "detect_anomaly",
        stock_code="600519"
    )

    print(f"\n🔍 财务异常识别结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   异常数量: {result['anomaly_count']}")
    print(f"   严重程度: {result['severity']}")

    if result['anomalies']:
        print(f"\n   异常详情:")
        for i, anomaly in enumerate(result['anomalies'], 1):
            print(f"      {i}. {anomaly['type']}: {anomaly['description']}")

    print(f"\n   摘要: {result['summary']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert result['anomaly_count'] >= 0, "异常数量应该>=0"

    print("\n✅ 财务异常识别测试通过")


@pytest.mark.asyncio
async def test_health_scenarios():
    """测试5：不同健康度场景"""
    print("\n" + "="*60)
    print("测试5：不同健康度场景")
    print("="*60)

    ai = FinancialHealthAI()

    # 场景1：优秀企业
    print("\n场景1：模拟优秀企业")
    excellent_data = {
        "资产负债率": 35.0,
        "流动比率": 2.0,
        "速动比率": 1.5,
        "毛利率": 45.0,
        "净利率": 18.0,
        "ROE": 20.0,
        "营收增长率": 25.0,
        "净利润增长率": 30.0,
        "经营现金流": 3500.0,
        "应收账款周转率": 12.0
    }
    metrics = ai._calculate_health_metrics(excellent_data)
    score = ai._calculate_health_score(metrics)
    grade = ai._get_health_grade(score)
    print(f"   健康度评分: {score}分")
    print(f"   健康度等级: {grade}")
    assert score >= 75, "优秀企业评分应该>=75"
    assert grade in ['A+', 'A'], "优秀企业应该是A或A+级"

    # 场景2：一般企业
    print("\n场景2：模拟一般企业")
    average_data = {
        "资产负债率": 55.0,
        "流动比率": 1.3,
        "速动比率": 0.9,
        "毛利率": 30.0,
        "净利率": 8.0,
        "ROE": 10.0,
        "营收增长率": 8.0,
        "净利润增长率": 6.0,
        "经营现金流": 800.0,
        "应收账款周转率": 8.0
    }
    metrics = ai._calculate_health_metrics(average_data)
    score = ai._calculate_health_score(metrics)
    grade = ai._get_health_grade(score)
    print(f"   健康度评分: {score}分")
    print(f"   健康度等级: {grade}")
    assert 55 <= score <= 75, "一般企业评分应该在55-75之间"

    # 场景3：风险企业
    print("\n场景3：模拟风险企业")
    risk_data = {
        "资产负债率": 75.0,
        "流动比率": 0.8,
        "速动比率": 0.4,
        "毛利率": 15.0,
        "净利率": 2.0,
        "ROE": 3.0,
        "营收增长率": -5.0,
        "净利润增长率": -15.0,
        "经营现金流": -500.0,
        "应收账款周转率": 4.0
    }
    metrics = ai._calculate_health_metrics(risk_data)
    score = ai._calculate_health_score(metrics)
    grade = ai._get_health_grade(score)
    print(f"   健康度评分: {score}分")
    print(f"   健康度等级: {grade}")
    assert score < 55, "风险企业评分应该<55"

    print("\n✅ 健康度场景测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "财务健康AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_health_analysis()
        await test_risk_assessment()
        await test_anomaly_detection()
        await test_health_scenarios()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 财务健康度分析测试通过")
        print("   - ✅ 财务风险评估测试通过")
        print("   - ✅ 财务异常识别测试通过")
        print("   - ✅ 健康度场景测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

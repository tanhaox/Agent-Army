"""
风险控制AI测试

测试核心功能：
1. 投资风险评估
2. 风险策略设置
3. 风险指标监控
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
from src.agents.business.strategy.risk_control_ai import RiskControlAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：风险控制AI初始化")
    print("="*60)

    ai = RiskControlAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "risk_assessment" in capability_names, "缺少风险评估能力"
    assert "strategy_setting" in capability_names, "缺少策略设置能力"
    assert "risk_monitoring" in capability_names, "缺少风险监控能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_risk_assessment():
    """测试2：投资风险评估"""
    print("\n" + "="*60)
    print("测试2：投资风险评估")
    print("="*60)

    ai = RiskControlAI()

    # 评估贵州茅台的投资风险
    result = await ai.execute(
        "assess_risk",
        stock_code="600519",
        investment_amount=100000
    )

    print(f"\n⚠️ 风险评估结果:")
    print(f"   股票代码: {result['stock_code']}")
    print(f"   投资金额: {result['investment_amount']}元")
    print(f"   风险评分: {result['risk_score']}")
    print(f"   风险等级: {result['risk_level']}")
    print(f"\n   风险指标:")
    for indicator, value in result['risk_indicators'].items():
        print(f"      - {indicator}: {value}")
    print(f"\n   最大损失估算:")
    print(f"      - 最大损失率: {result['max_loss_estimate']['estimated_max_loss_rate']}%")
    print(f"      - 最大损失金额: {result['max_loss_estimate']['estimated_max_loss_amount']}元")
    print(f"\n   摘要: {result['summary']}")
    print(f"   建议: {result['suggestion']}")

    # 验证结果
    assert result['stock_code'] == "600519", "股票代码不对"
    assert 0 <= result['risk_score'] <= 100, "风险评分应该在0-100之间"
    assert result['risk_level'] in ["极高风险", "高风险", "中风险", "低风险", "极低风险"], "风险等级不对"

    print("\n✅ 风险评估测试通过")


@pytest.mark.asyncio
async def test_strategy_setting():
    """测试3：风险策略设置"""
    print("\n" + "="*60)
    print("测试3：风险策略设置")
    print("="*60)

    ai = RiskControlAI()

    # 测试不同风险偏好
    preferences = ["conservative", "moderate", "aggressive"]

    for preference in preferences:
        print(f"\n【{preference}型策略】")
        result = await ai.execute(
            "set_strategy",
            risk_preference=preference,
            investment_amount=100000
        )

        print(f"   策略名称: {result['strategy']['name']}")
        print(f"   描述: {result['strategy']['description']}")
        print(f"   单只最大仓位: {result['strategy']['单只股票最大仓位']}")
        print(f"   止损线: {result['strategy']['止损线']}")
        print(f"   止盈线: {result['strategy']['止盈线']}")
        print(f"   总仓位上限: {result['strategy']['总仓位上限']}")
        print(f"\n   风险限制:")
        for limit_name, limit_value in result['risk_limits'].items():
            print(f"      - {limit_name}: {limit_value:.0f}元")

        # 验证结果
        assert result['risk_preference'] == preference, "风险偏好不对"
        assert 'strategy' in result, "应该有策略信息"
        assert 'risk_limits' in result, "应该有风险限制"

    print("\n✅ 策略设置测试通过")


@pytest.mark.asyncio
async def test_risk_monitoring():
    """测试4：风险指标监控"""
    print("\n" + "="*60)
    print("测试4：风险指标监控")
    print("="*60)

    ai = RiskControlAI()

    # 监控风险指标（使用模拟持仓）
    result = await ai.execute("monitor_risk", positions=[])

    print(f"\n📊 风险监控结果:")
    print(f"   持仓数量: {result['position_count']}")
    print(f"   组合风险: {result['portfolio_risk']['risk_level']}")
    print(f"   总市值: {result['portfolio_risk']['total_value']}元")
    print(f"   总盈亏: {result['portfolio_risk']['total_profit']}元")
    print(f"   集中度: {result['portfolio_risk']['concentration']}%")

    print(f"\n   持仓详情:")
    for pos in result['positions']:
        print(f"      {pos['stock_code']} {pos['stock_name']}: "
              f"{pos['position']}股，市值{pos['market_value']:.0f}元，"
              f"盈亏{pos['profit_loss_rate']:.2f}%")

    if result['warnings']:
        print(f"\n   ⚠️ 风险预警:")
        for warning in result['warnings']:
            print(f"      [{warning['severity']}] {warning['type']}: {warning['message']}")
    else:
        print(f"\n   ✅ 暂无风险预警")

    print(f"\n   摘要: {result['summary']}")

    # 验证结果
    assert result['position_count'] > 0, "应该有持仓"
    assert 'portfolio_risk' in result, "应该有组合风险"

    print("\n✅ 风险监控测试通过")


@pytest.mark.asyncio
async def test_risk_scenarios():
    """测试5：不同风险场景"""
    print("\n" + "="*60)
    print("测试5：不同风险场景")
    print("="*60)

    ai = RiskControlAI()

    # 场景1：低风险股票
    print("\n场景1：模拟低风险股票")
    low_risk_indicators = {
        "波动率": 15.0,
        "Beta系数": 0.6,
        "最大回撤": 12.0,
        "夏普比率": 2.0,
        "流动性风险": 2.0,
        "集中度风险": 2.0
    }
    score = ai._calculate_risk_score(low_risk_indicators)
    level = ai._assess_risk_level(score)
    print(f"   风险评分: {score}分")
    print(f"   风险等级: {level}")
    assert score < 50, "低风险股票评分应该<50"

    # 场景2：中风险股票
    print("\n场景2：模拟中风险股票")
    medium_risk_indicators = {
        "波动率": 25.0,
        "Beta系数": 1.0,
        "最大回撤": 20.0,
        "夏普比率": 1.2,
        "流动性风险": 5.0,
        "集中度风险": 5.0
    }
    score = ai._calculate_risk_score(medium_risk_indicators)
    level = ai._assess_risk_level(score)
    print(f"   风险评分: {score}分")
    print(f"   风险等级: {level}")
    assert 50 <= score <= 65, "中风险股票评分应该在50-65之间"

    # 场景3：高风险股票
    print("\n场景3：模拟高风险股票")
    high_risk_indicators = {
        "波动率": 40.0,
        "Beta系数": 1.6,
        "最大回撤": 35.0,
        "夏普比率": 0.8,
        "流动性风险": 8.0,
        "集中度风险": 8.0
    }
    score = ai._calculate_risk_score(high_risk_indicators)
    level = ai._assess_risk_level(score)
    print(f"   风险评分: {score}分")
    print(f"   风险等级: {level}")
    assert score >= 65, "高风险股票评分应该>=65"

    print("\n✅ 风险场景测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "风险控制AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_risk_assessment()
        await test_strategy_setting()
        await test_risk_monitoring()
        await test_risk_scenarios()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 风险评估测试通过")
        print("   - ✅ 策略设置测试通过")
        print("   - ✅ 风险监控测试通过")
        print("   - ✅ 风险场景测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

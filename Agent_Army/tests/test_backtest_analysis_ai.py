"""
回测分析AI测试

测试核心功能：
1. 策略回测
2. 表现分析
3. 策略评估
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
from src.agents.business.validation.backtest_analysis_ai import BacktestAnalysisAI


@pytest.mark.asyncio
async def test_initialization():
    """测试1：初始化"""
    print("\n" + "="*60)
    print("测试1：回测分析AI初始化")
    print("="*60)

    ai = BacktestAnalysisAI()

    print(f"✅ AI名称: {ai.name}")
    print(f"✅ AI角色: {ai.role}")
    print(f"✅ 能力数量: {len(ai.capabilities)}")
    print(f"✅ 工具数量: {len(ai.tools)}")

    # 检查核心能力
    capability_names = [cap.name for cap in ai.capabilities]
    assert "strategy_backtest" in capability_names, "缺少策略回测能力"
    assert "performance_analysis" in capability_names, "缺少表现分析能力"
    assert "strategy_evaluation" in capability_names, "缺少策略评估能力"

    print("✅ 初始化测试通过")


@pytest.mark.asyncio
async def test_strategy_backtest():
    """测试2：策略回测"""
    print("\n" + "="*60)
    print("测试2：策略回测")
    print("="*60)

    ai = BacktestAnalysisAI()

    # 运行策略回测
    result = await ai.execute(
        "run_backtest",
        strategy_name="均线策略",
        start_date="2023-01-01",
        end_date="2023-03-31",
        initial_capital=1000000
    )

    print(f"\n📈 策略回测结果:")
    print(f"   策略名称: {result['strategy_name']}")
    print(f"   回测周期: {result['backtest_period']}")
    print(f"   初始资金: {result['initial_capital']:.0f}元")
    print(f"   最终资金: {result['final_capital']:.0f}元")
    print(f"\n   收益指标:")
    print(f"      总收益: {result['performance']['total_return']:.2f}%")
    print(f"      年化收益: {result['performance']['annualized_return']:.2f}%")
    print(f"      平均日收益: {result['performance']['avg_daily_return']:.2f}%")
    print(f"      盈利金额: {result['performance']['profit']:.0f}元")
    print(f"\n   风险指标:")
    print(f"      波动率: {result['risk_metrics']['volatility']:.2f}%")
    print(f"      最大回撤: {result['risk_metrics']['max_drawdown']:.2f}%")
    print(f"      夏普比率: {result['risk_metrics']['sharpe_ratio']:.2f}")
    print(f"\n   交易次数: {result['trade_count']}")
    print(f"   摘要: {result['summary']}")
    print(f"   评估: {result['evaluation']}")

    # 验证结果
    assert result['strategy_name'] == "均线策略", "策略名称不对"
    assert 'performance' in result, "应该有收益指标"
    assert 'risk_metrics' in result, "应该有风险指标"

    print("\n✅ 策略回测测试通过")


@pytest.mark.asyncio
async def test_performance_analysis():
    """测试3：表现分析"""
    print("\n" + "="*60)
    print("测试3：表现分析")
    print("="*60)

    ai = BacktestAnalysisAI()

    # 分析回测表现
    result = await ai.execute("analyze_performance", backtest_data=None)

    print(f"\n📊 表现分析结果:")
    print(f"\n   月度表现:")
    for month in result['monthly_performance'][:3]:  # 显示前3个月
        print(f"      {month['month']}: {month['return']:.2f}%, 交易{month['trade_count']}次")

    print(f"\n   胜率分析:")
    print(f"      盈利天数: {result['win_rate_analysis']['win_days']}")
    print(f"      亏损天数: {result['win_rate_analysis']['loss_days']}")
    print(f"      胜率: {result['win_rate_analysis']['win_rate']:.2f}%")
    print(f"      平均盈利: {result['win_rate_analysis']['avg_win']:.2f}%")
    print(f"      平均亏损: {result['win_rate_analysis']['avg_loss']:.2f}%")

    print(f"\n   回撤分析:")
    print(f"      最大回撤: {result['drawdown_analysis']['max_drawdown']:.2f}%")
    print(f"      回撤次数: {result['drawdown_analysis']['drawdown_count']}")
    print(f"      平均回撤: {result['drawdown_analysis']['avg_drawdown']:.2f}%")

    print(f"\n   摘要: {result['summary']}")

    # 验证结果
    assert 'monthly_performance' in result, "应该有月度表现"
    assert 'win_rate_analysis' in result, "应该有胜率分析"
    assert 'drawdown_analysis' in result, "应该有回撤分析"

    print("\n✅ 表现分析测试通过")


@pytest.mark.asyncio
async def test_strategy_evaluation():
    """测试4：策略评估"""
    print("\n" + "="*60)
    print("测试4：策略评估")
    print("="*60)

    ai = BacktestAnalysisAI()

    # 评估策略
    result = await ai.execute(
        "evaluate_strategy",
        strategy_name="动量策略",
        backtest_period="1y"
    )

    print(f"\n🎯 策略评估结果:")
    print(f"   策略名称: {result['strategy_name']}")
    print(f"   综合评级: {result['overall_rating']}")
    print(f"\n   策略优势:")
    for strength in result['strengths']:
        print(f"      ✅ {strength}")
    print(f"\n   策略劣势:")
    for weakness in result['weaknesses']:
        print(f"      ⚠️ {weakness}")
    print(f"\n   适用性: {result['suitability']}")
    print(f"   建议: {result['recommendation']}")

    # 验证结果
    assert result['strategy_name'] == "动量策略", "策略名称不对"
    assert result['overall_rating'] in ['A+', 'A', 'B', 'C', 'D'], "评级不对"
    assert 'strengths' in result, "应该有优势分析"
    assert 'weaknesses' in result, "应该有劣势分析"

    print("\n✅ 策略评估测试通过")


@pytest.mark.asyncio
async def test_backtest_scenarios():
    """测试5：不同回测场景"""
    print("\n" + "="*60)
    print("测试5：不同回测场景")
    print("="*60)

    ai = BacktestAnalysisAI()

    # 场景1：优秀策略
    print("\n场景1：模拟优秀策略")
    excellent_backtest = {
        "performance": {
            "total_return": 25.0,
            "annualized_return": 28.0
        },
        "risk_metrics": {
            "sharpe_ratio": 1.8,
            "max_drawdown": 12.0,
            "volatility": 15.0
        }
    }
    rating = ai._rate_strategy(excellent_backtest)
    strengths = ai._identify_strengths(excellent_backtest)
    print(f"   评级: {rating}")
    print(f"   优势: {strengths}")
    assert rating in ['A+', 'A'], "优秀策略应该是A或A+"

    # 场景2：中等策略
    print("\n场景2：模拟中等策略")
    moderate_backtest = {
        "performance": {
            "total_return": 10.0,
            "annualized_return": 12.0
        },
        "risk_metrics": {
            "sharpe_ratio": 0.8,
            "max_drawdown": 20.0,
            "volatility": 22.0
        }
    }
    rating = ai._rate_strategy(moderate_backtest)
    strengths = ai._identify_strengths(moderate_backtest)
    weaknesses = ai._identify_weaknesses(moderate_backtest)
    print(f"   评级: {rating}")
    print(f"   优势: {strengths}")
    print(f"   劣势: {weaknesses}")
    assert rating in ['B', 'C'], "中等策略应该是B或C"

    # 场景3：较差策略
    print("\n场景3：模拟较差策略")
    poor_backtest = {
        "performance": {
            "total_return": 2.0,
            "annualized_return": 2.5
        },
        "risk_metrics": {
            "sharpe_ratio": 0.3,
            "max_drawdown": 35.0,
            "volatility": 30.0
        }
    }
    rating = ai._rate_strategy(poor_backtest)
    weaknesses = ai._identify_weaknesses(poor_backtest)
    print(f"   评级: {rating}")
    print(f"   劣势: {weaknesses}")
    assert rating in ['C', 'D'], "较差策略应该是C或D"

    print("\n✅ 回测场景测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "╔"+"═"*58+"╗")
    print("║" + " "*18 + "回测分析AI测试套件" + " "*18 + "║")
    print("╚"+"═"*58+"╝")

    try:
        await test_initialization()
        await test_strategy_backtest()
        await test_performance_analysis()
        await test_strategy_evaluation()
        await test_backtest_scenarios()

        print("\n" + "╔"+"═"*58+"╗")
        print("║" + " "*21 + "🎉 所有测试通过！" + " "*21 + "║")
        print("╚"+"═"*58+"╝")

        print("\n✅ 测试总结:")
        print("   - ✅ 初始化测试通过")
        print("   - ✅ 策略回测测试通过")
        print("   - ✅ 表现分析测试通过")
        print("   - ✅ 策略评估测试通过")
        print("   - ✅ 回测场景测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

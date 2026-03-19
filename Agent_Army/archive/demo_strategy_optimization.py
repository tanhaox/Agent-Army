"""
策略优化AI演示 - Strategy Optimization AI Demo
展示策略优化AI的各项功能
"""

import asyncio
import json
from datetime import datetime
from src.agents.business.validation.strategy_optimization_ai import StrategyOptimizationAI


async def demo_strategy_optimization():
    """演示策略优化功能"""
    print("=" * 80)
    print("策略优化AI演示")
    print("=" * 80)
    print()

    # 创建优化AI实例
    optimizer = StrategyOptimizationAI()

    # 示例策略参数
    strategy_name = "双均线策略"
    original_params = {
        "ma_short": 5,
        "ma_long": 20,
        "stop_loss": 0.05,
        "take_profit": 0.15,
        "position_size": 0.3
    }

    print(f"策略名称: {strategy_name}")
    print(f"原始参数:")
    for key, value in original_params.items():
        print(f"  {key}: {value}")
    print()

    # 1. 网格搜索优化
    print("-" * 80)
    print("1. 网格搜索优化")
    print("-" * 80)

    result_grid = await optimizer.optimize_strategy(
        strategy_name=strategy_name,
        original_params=original_params,
        optimization_method="grid_search",
        objective="sharpe_ratio"
    )

    print(f"优化方法: {result_grid['optimization_method']}")
    print(f"优化目标: {result_grid['objective']}")
    print(f"最优参数:")
    for key, value in result_grid['optimized_params'].items():
        print(f"  {key}: {value}")

    print(f"\n改进指标:")
    improvements = result_grid['improvements']
    print(f"  收益提升: {improvements['return_improvement']:.2f}%")
    print(f"  风险降低: {improvements['risk_reduction']:.2f}%")
    print(f"  夏普比率提升: {improvements['sharpe_improvement']:.2f}")

    print(f"\n优化建议 (共{len(result_grid['recommendations'])}条):")
    for i, rec in enumerate(result_grid['recommendations'][:5], 1):
        print(f"  {i}. {rec['param']}: {rec['current_value']} → {rec['suggested_value']}")
        print(f"     原因: {rec['reason']}")
        print(f"     预期影响: {rec['expected_impact']}")

    print(f"\n优化置信度: {result_grid['confidence']*100:.1f}%")
    print(f"摘要: {result_grid['summary']}")
    print()

    # 2. 遗传算法优化
    print("-" * 80)
    print("2. 遗传算法优化")
    print("-" * 80)

    result_genetic = await optimizer.optimize_strategy(
        strategy_name=strategy_name,
        original_params=original_params,
        optimization_method="genetic",
        objective="sharpe_ratio"
    )

    print(f"优化方法: {result_genetic['optimization_method']}")
    print(f"最优参数:")
    for key, value in result_genetic['optimized_params'].items():
        print(f"  {key}: {value}")

    print(f"\n优化详情:")
    details = result_genetic['optimization_details']
    print(f"  总迭代次数: {details['total_iterations']}")
    print(f"  目标函数值: {details['objective_value']:.2f}")
    if details['convergence']:
        print(f"  收敛轨迹: {details['convergence'][:5]}...")

    print()

    # 3. 贝叶斯优化
    print("-" * 80)
    print("3. 贝叶斯优化")
    print("-" * 80)

    result_bayesian = await optimizer.optimize_strategy(
        strategy_name=strategy_name,
        original_params=original_params,
        optimization_method="bayesian",
        objective="total_return"
    )

    print(f"优化方法: {result_bayesian['optimization_method']}")
    print(f"优化目标: {result_bayesian['objective']}")
    print(f"最优参数:")
    for key, value in result_bayesian['optimized_params'].items():
        print(f"  {key}: {value}")

    print()

    # 4. 策略组合优化
    print("-" * 80)
    print("4. 策略组合优化")
    print("-" * 80)

    strategies = [
        {"name": "趋势跟踪", "params": {"ma_short": 5, "ma_long": 20}, "weight": 0.4},
        {"name": "均值回归", "params": {"threshold": 2.0}, "weight": 0.3},
        {"name": "动量策略", "params": {"lookback": 10}, "weight": 0.3}
    ]

    portfolio_result = await optimizer.optimize_portfolio(strategies)

    print("策略组合:")
    for strategy in strategies:
        print(f"  - {strategy['name']}: {strategy['weight']:.1%}")

    print(f"\n最优权重分配:")
    for strategy_name, weight in portfolio_result['optimal_weights'].items():
        print(f"  {strategy_name}: {weight:.2%}")

    print(f"\n组合指标:")
    metrics = portfolio_result['portfolio_metrics']
    print(f"  总收益: {metrics['total_return']:.2f}%")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {metrics['max_drawdown']:.2f}%")
    print(f"  波动率: {metrics['volatility']:.2f}%")
    print(f"  分散度比率: {metrics['diversification_ratio']:.2f}")

    print(f"\n组合建议:")
    for rec in portfolio_result['recommendations']:
        print(f"  - {rec}")

    print(f"\n摘要: {portfolio_result['summary']}")
    print()

    # 5. 对比不同优化方法
    print("-" * 80)
    print("5. 优化方法对比")
    print("-" * 80)

    print(f"{'优化方法':<15} {'收益提升':<12} {'夏普提升':<12} {'置信度':<12}")
    print("-" * 60)

    methods = [
        ("网格搜索", result_grid),
        ("遗传算法", result_genetic),
        ("贝叶斯优化", result_bayesian)
    ]

    for method_name, result in methods:
        improvements = result['improvements']
        print(f"{method_name:<15} {improvements['return_improvement']:>10.2f}% "
              f"{improvements['sharpe_improvement']:>10.2f} "
              f"{result['confidence']*100:>10.1f}%")

    print()
    print("=" * 80)
    print("演示完成")
    print("=" * 80)


async def demo_parameter_space():
    """演示参数空间定义"""
    print("=" * 80)
    print("参数空间定义演示")
    print("=" * 80)
    print()

    optimizer = StrategyOptimizationAI()

    # 示例参数
    params = {
        "ma_short": 5,
        "ma_long": 20,
        "stop_loss": 0.05,
        "take_profit": 0.15
    }

    print("原始参数:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()

    # 定义参数空间
    param_space = optimizer._define_param_space("test_strategy", params)

    print("参数空间定义:")
    for param_name, space in param_space.items():
        print(f"  {param_name}:")
        print(f"    类型: {space['type']}")
        print(f"    范围: {space['range']}")
        if 'step' in space:
            print(f"    步长: {space['step']}")
    print()

    # 参数采样
    print("随机采样5组参数:")
    for i in range(5):
        sampled_params = optimizer._sample_params(param_space)
        print(f"  样本{i+1}: {sampled_params}")
    print()


async def main():
    """主函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "策略优化AI 功能演示" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    await demo_strategy_optimization()
    print()
    await demo_parameter_space()

    print()
    print("演示时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()


if __name__ == "__main__":
    asyncio.run(main())

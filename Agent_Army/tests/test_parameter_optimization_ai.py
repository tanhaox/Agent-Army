"""
测试参数优化AI
"""
import pytest

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.evolution.parameter_optimization_ai import ParameterOptimizationAI


@pytest.mark.asyncio
async def test_parameter_optimization():
    """测试参数优化功能"""
    print("=" * 60)
    print("测试参数优化AI")
    print("=" * 60)

    # 初始化Agent
    agent = ParameterOptimizationAI()

    # 测试1: 查看当前配置
    print("\n测试1: 查看当前配置")
    print("-" * 40)

    current_config = await agent.get_current_config()
    print(f"PB阈值: {current_config['pb_min']} - {current_config['pb_max']}")
    print(f"PE阈值: {current_config['pe_min']} - {current_config['pe_max']}")
    print(f"ROE最小值: {current_config['roe_min']}")
    print(f"负债率上限: {current_config['debt_max']}")
    print("权重配置:")
    for dim, weight in current_config['weights'].items():
        print(f"  - {dim}: {weight}")

    # 测试2: 分析性能（低准确率场景）
    print("\n测试2: 分析性能（低准确率场景）")
    print("-" * 40)

    validation_results = [
        {
            "case_type": "failure",
            "accuracy": 0.45,
            "prediction": {"target_price": 7.5},
            "actual_result": {"actual_target_price": 5.0}
        },
        {
            "case_type": "failure",
            "accuracy": 0.50,
            "prediction": {"target_price": 8.0},
            "actual_result": {"actual_target_price": 5.5}
        },
        {
            "case_type": "success",
            "accuracy": 0.85,
            "prediction": {"target_price": 6.5},
            "actual_result": {"actual_target_price": 6.8}
        }
    ]

    performance_report = await agent.analyze_performance(validation_results)
    print(f"总案例数: {performance_report['total_cases']}")
    print(f"平均准确率: {performance_report['average_accuracy']:.1%}")
    print(f"成功率: {performance_report['success_rate']:.1%}")
    print(f"弱点:")
    for wp in performance_report['weak_points']:
        print(f"  - {wp}")
    print(f"建议:")
    for rec in performance_report['recommendations']:
        print(f"  - {rec}")

    # 测试3: 生成优化提案
    print("\n测试3: 生成优化提案")
    print("-" * 40)

    proposal = await agent.optimize_parameters(performance_report)
    print(f"优化ID: {proposal['optimization_id']}")
    print(f"参数调整: {len(proposal['parameter_adjustments'])} 项")
    for adj in proposal['parameter_adjustments']:
        print(f"  - {adj['parameter']}: {adj['old_value']} -> {adj['new_value']}")
        print(f"    原因: {adj['reason']}")
    print(f"权重调整: {len(proposal['weight_adjustments'])} 项")
    for adj in proposal['weight_adjustments']:
        print(f"  - {adj['dimension']}: {adj['old_weight']} -> {adj['new_weight']}")
        print(f"    原因: {adj['reason']}")
    print(f"预期改进: {proposal['expected_improvement']}")
    print(f"风险评估: {proposal['risk_assessment']}")

    # 测试4: 应用优化（自动模式）
    print("\n测试4: 应用优化（自动模式）")
    print("-" * 40)

    result = await agent.apply_optimization(proposal, auto_apply=True)
    print(f"应用状态: {result['status']}")
    print(f"应用时间: {result['applied_at']}")
    print(f"变更数量: {len(result['changes'])}")
    for change in result['changes']:
        print(f"  - {change}")

    # 测试5: 查看更新后的配置
    print("\n测试5: 查看更新后的配置")
    print("-" * 40)

    new_config = await agent.get_current_config()
    print(f"PB阈值: {new_config['pb_min']} - {new_config['pb_max']}")
    print(f"PE阈值: {new_config['pe_min']} - {new_config['pe_max']}")
    print("权重配置:")
    for dim, weight in new_config['weights'].items():
        print(f"  - {dim}: {weight}")

    # 测试6: 查看优化历史
    print("\n测试6: 查看优化历史")
    print("-" * 40)

    history = await agent.get_optimization_history()
    print(f"优化历史记录: {len(history)} 条")
    for record in history:
        print(f"  - {record['optimization_id']}: {record['applied_at']}")
        print(f"    变更: {len(record['changes'])} 项")

    # 测试7: 高准确率场景（无需优化）
    print("\n测试7: 高准确率场景（无需优化）")
    print("-" * 40)

    good_results = [
        {"case_type": "success", "accuracy": 0.92, "prediction": {"target_price": 7.5}, "actual_result": {"actual_target_price": 7.6}},
        {"case_type": "success", "accuracy": 0.88, "prediction": {"target_price": 8.0}, "actual_result": {"actual_target_price": 8.2}},
        {"case_type": "success", "accuracy": 0.85, "prediction": {"target_price": 6.5}, "actual_result": {"actual_target_price": 6.7}}
    ]

    good_report = await agent.analyze_performance(good_results)
    print(f"平均准确率: {good_report['average_accuracy']:.1%}")
    print(f"弱点: {good_report['weak_points'] if good_report['weak_points'] else '无'}")

    good_proposal = await agent.optimize_parameters(good_report)
    print(f"参数调整: {len(good_proposal['parameter_adjustments'])} 项")
    print(f"权重调整: {len(good_proposal['weight_adjustments'])} 项")
    print(f"预期改进: {good_proposal['expected_improvement']}")


if __name__ == "__main__":
    asyncio.run(test_parameter_optimization())

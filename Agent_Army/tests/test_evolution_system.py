"""
测试自我进化系统

包含三个核心模式的集成测试：
1. 经验积累AI
2. 参数优化AI
3. 模式发现AI
"""
import pytest

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.evolution import (
    ExperienceAccumulationAI,
    ParameterOptimizationAI,
    PatternDiscoveryAI
)


@pytest.mark.asyncio
async def test_experience_accumulation():
    """测试经验积累AI"""
    print("\n" + "="*60)
    print("测试经验积累AI")
    print("="*60)

    ai = ExperienceAccumulationAI()

    # 模拟6维度分析数据
    dimensions = {
        "fundamental": {
            "pb": 0.8,
            "roe": 15.0,
            "revenue_growth": 20.0,
            "debt_ratio": 40.0
        },
        "technical": {
            "trend": "up",
            "support_level": 10.50,
            "ma5": 11.20,
            "ma10": 11.00,
            "ma20": 10.80
        },
        "capital": {
            "flow": "in",
            "inflow": 1000000
        },
        "policy": {
            "support": True
        },
        "historical": {
            "similar_cases": 5
        },
        "industry": {
            "name": "新能源",
            "cycle": "growth"
        }
    }

    # 模拟预测结果
    prediction = {
        "stop_loss": 10.00,
        "buy_price": 10.80,
        "cost_price": 10.85,
        "resistance": [12.00, 13.50],
        "time_window": "3个月",
        "target_price": 13.50,
        "confidence": 0.75
    }

    # 记录投资路径
    record_id = await ai.record_investment_path(
        stock_code="300750",
        dimensions=dimensions,
        prediction=prediction
    )

    print(f"[OK] 记录创建成功: {record_id}")

    # 查询经验
    cases = await ai.query_experience(stock_code="300750")
    print(f"[OK] 查询到 {len(cases)} 个案例")

    # 验证预测
    report = await ai.verify_prediction(
        record_id=record_id,
        actual_target_price=14.00,
        current_price=13.80
    )
    print(f"[OK] 验证完成: 准确率={report['accuracy']:.1%}, 类型={report['case_type']}")

    # 获取统计
    stats = await ai.get_statistics()
    print(f"[OK] 经验库统计: 总案例={stats['total_cases']}, 成功={stats['success_cases']}, 失败={stats['failure_cases']}, 待验证={stats['pending_cases']}")

    return record_id


@pytest.mark.asyncio
async def test_parameter_optimization():
    """测试参数优化AI"""
    print("\n" + "="*60)
    print("测试参数优化AI")
    print("="*60)

    ai = ParameterOptimizationAI()

    # 模拟验证结果
    validation_results = [
        {"accuracy": 0.65, "case_type": "success"},
        {"accuracy": 0.70, "case_type": "success"},
        {"accuracy": 0.50, "case_type": "failure"},
        {"accuracy": 0.75, "case_type": "success"},
    ]

    # 分析性能
    performance_report = await ai.analyze_performance(validation_results)
    print(f"[OK] 性能分析: 准确率={performance_report['average_accuracy']:.1%}, 成功率={performance_report['success_rate']:.1%}")
    print(f"   弱点: {performance_report['weak_points']}")

    # 生成优化提案
    proposal = await ai.optimize_parameters(performance_report)
    print(f"[OK] 优化提案: ID={proposal['optimization_id']}")
    print(f"   参数调整: {len(proposal['parameter_adjustments'])} 项")
    print(f"   权重调整: {len(proposal['weight_adjustments'])} 项")
    print(f"   预期改进: {proposal['expected_improvement']}")

    # 应用优化（演示，不实际应用）
    # result = await ai.apply_optimization(proposal, auto_apply=False)
    # print(f"[OK] 优化状态: {result['status']}")

    # 获取当前配置
    current_config = await ai.get_current_config()
    print(f"[OK] 当前配置: PB阈值=[{current_config['pb_min']}, {current_config['pb_max']}], PE阈值=[{current_config['pe_min']}, {current_config['pe_max']}]")

    return proposal


@pytest.mark.asyncio
async def test_pattern_discovery():
    """测试模式发现AI"""
    print("\n" + "="*60)
    print("测试模式发现AI")
    print("="*60)

    ai = PatternDiscoveryAI()

    # 模拟经验案例
    experience_cases = [
        {
            "record_id": "300750_20250315",
            "stock_code": "300750",
            "case_type": "success",
            "dimensions": {
                "fundamental": {"pb": 0.8, "roe": 15.0},
                "technical": {"trend": "up", "support_level": 10.50},
                "capital": {"flow": "in"},
                "policy": {"support": True},
                "historical": {},
                "industry": {"name": "新能源"}
            },
            "prediction": {
                "stop_loss": 10.00,
                "buy_price": 10.80,
                "target_price": 13.50,
                "time_window": "3个月"
            },
            "actual_result": {
                "accuracy": 0.9,
                "actual_target_price": 14.00
            }
        },
        {
            "record_id": "600519_20250315",
            "stock_code": "600519",
            "case_type": "success",
            "dimensions": {
                "fundamental": {"pb": 0.9, "roe": 18.0},
                "technical": {"trend": "up"},
                "capital": {"flow": "in"},
                "policy": {"support": True},
                "historical": {},
                "industry": {"name": "白酒"}
            },
            "prediction": {
                "stop_loss": 1800.00,
                "buy_price": 1850.00,
                "target_price": 2100.00,
                "time_window": "3个月"
            },
            "actual_result": {
                "accuracy": 0.85,
                "actual_target_price": 2150.00
            }
        },
        {
            "record_id": "000858_20250315",
            "stock_code": "000858",
            "case_type": "failure",
            "dimensions": {
                "fundamental": {"pb": 2.5, "roe": 6.0},
                "technical": {"trend": "down"},
                "capital": {"flow": "out"},
                "policy": {"support": False},
                "historical": {},
                "industry": {"name": "钢铁"}
            },
            "prediction": {
                "stop_loss": 5.00,
                "buy_price": 5.50,
                "target_price": 7.00,
                "time_window": "3个月"
            },
            "actual_result": {
                "accuracy": 0.3,
                "deviation": 0.6
            }
        }
    ]

    # 发现模式
    patterns = await ai.discover_patterns(experience_cases)
    print(f"[OK] 发现 {len(patterns)} 个模式:")

    for pattern in patterns[:3]:
        print(f"   - {pattern['pattern_name']}")
        print(f"     类型: {pattern['pattern_type']}")
        print(f"     支持度: {pattern.get('support', 0)}")
        print(f"     置信度: {pattern.get('confidence', 0):.1%}")

    # 验证模式
    if patterns:
        pattern_to_verify = patterns[0]
        validation_result = await ai.verify_pattern(
            pattern_id=pattern_to_verify['pattern_id'],
            validation_cases=experience_cases
        )
        print(f"\n[OK] 模式验证: {validation_result['pattern_name']}")
        print(f"   状态: {validation_result['status']}")
        print(f"   置信度: {validation_result['confidence']:.1%}")
        print(f"   匹配案例: {validation_result['matched_cases']} 个")

    # 获取统计
    stats = await ai.get_statistics()
    print(f"\n[OK] 模式库统计: 总模式={stats['total_patterns']}, 成功模式={stats.get('success_patterns', 0)}, 失败模式={stats.get('failure_patterns', 0)}")

    return patterns


@pytest.mark.asyncio
async def test_integration():
    """测试集成流程"""
    print("\n" + "="*60)
    print("测试自我进化系统集成流程")
    print("="*60)

    # 1. 经验积累：记录案例
    print("\n[阶段1] 经验积累")
    exp_ai = ExperienceAccumulationAI()

    dimensions = {
        "fundamental": {"pb": 0.8, "roe": 15.0},
        "technical": {"trend": "up"},
        "capital": {"flow": "in"},
        "policy": {"support": True},
        "historical": {},
        "industry": {"name": "新能源"}
    }

    prediction = {
        "stop_loss": 10.00,
        "buy_price": 10.80,
        "target_price": 13.50,
        "time_window": "3个月",
        "confidence": 0.75
    }

    record_id = await exp_ai.record_investment_path(
        stock_code="300750",
        dimensions=dimensions,
        prediction=prediction
    )
    print(f"[OK] 案例已记录: {record_id}")

    # 2. 验证并更新
    await exp_ai.verify_prediction(
        record_id=record_id,
        actual_target_price=14.00,
        current_price=13.80
    )
    print(f"[OK] 案例已验证")

    # 3. 获取所有经验案例
    all_cases = await exp_ai.query_experience(limit=10)
    print(f"[OK] 当前经验库有 {len(all_cases)} 个案例")

    # 4. 参数优化：分析性能
    print("\n[阶段2] 参数优化")
    param_ai = ParameterOptimizationAI()

    # 模拟验证结果
    validation_results = [
        {"accuracy": 0.7, "case_type": "success"},
        {"accuracy": 0.75, "case_type": "success"},
        {"accuracy": 0.6, "case_type": "success"},
    ]

    performance_report = await param_ai.analyze_performance(validation_results)
    proposal = await param_ai.optimize_parameters(performance_report)
    print(f"[OK] 参数优化提案已生成")
    print(f"   调整项目: {len(proposal['parameter_adjustments'])} 个参数")

    # 5. 模式发现：从经验中发现模式
    print("\n[阶段3] 模式发现")
    pattern_ai = PatternDiscoveryAI()

    patterns = await pattern_ai.discover_patterns(all_cases)
    print(f"[OK] 发现 {len(patterns)} 个新模式")

    # 6. 验证模式
    if patterns:
        validation_result = await pattern_ai.validate_pattern(
            pattern_id=patterns[0]['pattern_id'],
            validation_cases=all_cases
        )
        print(f"[OK] 模式验证完成: {validation_result['status']}")

    print("\n" + "="*60)
    print("[OK] 自我进化系统集成测试完成")
    print("="*60)

    print("\n系统流程:")
    print("1. 经验积累 → 记录投资路径 → 验证预测 → 建立案例库")
    print("2. 参数优化 → 分析性能 → 生成提案 → 调整配置")
    print("3. 模式发现 → 发现模式 → 验证模式 → 更新模式库")


async def main():
    """主测试函数"""
    print("\n[TEST] 自我进化系统测试")
    print("="*60)

    try:
        # 测试经验积累
        await test_experience_accumulation()

        # 测试参数优化
        await test_parameter_optimization()

        # 测试模式发现
        await test_pattern_discovery()

        # 测试集成流程
        await test_integration()

        print("\n" + "="*60)
        print("[OK] 所有测试通过!")
        print("="*60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

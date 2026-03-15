"""
测试模式发现AI
"""
import pytest

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.evolution.pattern_discovery_ai import PatternDiscoveryAI


@pytest.mark.asyncio
async def test_pattern_discovery():
    """测试模式发现功能"""
    print("=" * 60)
    print("测试模式发现AI")
    print("=" * 60)

    # 初始化Agent
    agent = PatternDiscoveryAI()

    # 准备测试数据
    test_cases = [
        # 成功案例1: 低PB高ROE
        {
            "record_id": "601669_20260315_success1",
            "case_type": "success",
            "dimensions": {
                "fundamental": {"pb": 0.8, "roe": 12.5},
                "technical": {"trend": "up"},
                "capital": {"flow": "in"},
                "policy": {"support": True}
            },
            "actual_result": {"accuracy": 0.95, "deviation": 0.05}
        },
        # 成功案例2: 低PB高ROE
        {
            "record_id": "600519_20260310_success2",
            "case_type": "success",
            "dimensions": {
                "fundamental": {"pb": 0.9, "roe": 15.0},
                "technical": {"trend": "up"},
                "capital": {"flow": "in"},
                "policy": {"support": False}
            },
            "actual_result": {"accuracy": 0.88, "deviation": 0.08}
        },
        # 成功案例3: 低PB高ROE
        {
            "record_id": "000858_20260312_success3",
            "case_type": "success",
            "dimensions": {
                "fundamental": {"pb": 0.7, "roe": 11.0},
                "technical": {"trend": "up"},
                "capital": {"flow": "in"},
                "policy": {"support": True}
            },
            "actual_result": {"accuracy": 0.92, "deviation": 0.06}
        },
        # 失败案例1: 高PB低ROE
        {
            "record_id": "601318_20260308_failure1",
            "case_type": "failure",
            "dimensions": {
                "fundamental": {"pb": 2.5, "roe": 6.0},
                "technical": {"trend": "down"},
                "capital": {"flow": "out"},
                "policy": {"support": False}
            },
            "actual_result": {"accuracy": 0.35, "deviation": 0.55}
        },
        # 失败案例2: 高PB低ROE
        {
            "record_id": "601398_20260305_failure2",
            "case_type": "failure",
            "dimensions": {
                "fundamental": {"pb": 3.0, "roe": 5.5},
                "technical": {"trend": "down"},
                "capital": {"flow": "out"},
                "policy": {"support": False}
            },
            "actual_result": {"accuracy": 0.30, "deviation": 0.60}
        },
        # 失败案例3: 资金流出
        {
            "record_id": "601888_20260301_failure3",
            "case_type": "failure",
            "dimensions": {
                "fundamental": {"pb": 1.5, "roe": 9.0},
                "technical": {"trend": "up"},
                "capital": {"flow": "out"},
                "policy": {"support": False}
            },
            "actual_result": {"accuracy": 0.45, "deviation": 0.40}
        }
    ]

    # 测试1: 发现模式
    print("\n测试1: 发现模式")
    print("-" * 40)

    patterns = await agent.discover_patterns(test_cases, min_support=2)
    print(f"发现模式数量: {len(patterns)}")

    for i, pattern in enumerate(patterns, 1):
        print(f"\n模式{i}: {pattern['pattern_name']}")
        print(f"  类型: {pattern['pattern_type']}")
        print(f"  描述: {pattern['description']}")
        print(f"  支持度: {pattern['support']}")
        print(f"  置信度: {pattern.get('confidence', pattern.get('risk_level', 0)):.1%}")
        print(f"  案例: {', '.join(pattern['examples'])}")

    # 测试2: 保存模式到数据库
    print("\n\n测试2: 保存模式到数据库")
    print("-" * 40)

    for pattern in patterns:
        saved = await agent.save_pattern(pattern)
        print(f"保存模式 {pattern['pattern_id']}: {'成功' if saved else '失败'}")

    # 测试3: 查询模式统计
    print("\n\n测试3: 查询模式统计")
    print("-" * 40)

    stats = await agent.get_statistics()
    print(f"总模式数: {stats['total_patterns']}")
    print(f"盈利模式: {stats['success_patterns']}")
    print(f"风险模式: {stats['failure_patterns']}")
    print(f"发现次数: {stats['discovery_count']}")

    # 测试4: 验证模式
    print("\n\n测试4: 验证模式")
    print("-" * 40)

    if patterns:
        test_pattern = patterns[0]
        print(f"验证模式: {test_pattern['pattern_name']}")

        # 新案例数据
        new_cases = [
            {
                "record_id": "000001_20260320_new1",
                "case_type": "success",
                "dimensions": {
                    "fundamental": {"pb": 0.85, "roe": 13.0},
                    "technical": {"trend": "up"},
                    "capital": {"flow": "in"},
                    "policy": {"support": True}
                }
            },
            {
                "record_id": "000002_20260320_new2",
                "case_type": "success",
                "dimensions": {
                    "fundamental": {"pb": 0.75, "roe": 14.5},
                    "technical": {"trend": "up"},
                    "capital": {"flow": "in"},
                    "policy": {"support": False}
                }
            },
            {
                "record_id": "000003_20260320_new3",
                "case_type": "failure",
                "dimensions": {
                    "fundamental": {"pb": 0.95, "roe": 9.5},
                    "technical": {"trend": "down"},
                    "capital": {"flow": "out"},
                    "policy": {"support": False}
                }
            }
        ]

        verification = await agent.verify_pattern(test_pattern, new_cases)
        print(f"验证结果: {'通过' if verification['verified'] else '未通过'}")
        print(f"匹配案例: {verification['matched_count']}")
        print(f"验证率: {verification['verification_rate']:.1%}")
        print(f"原始置信度: {verification['original_confidence']:.1%}")

    # 测试5: 搜索模式
    print("\n\n测试5: 搜索模式")
    print("-" * 40)

    # 搜索盈利模式
    success_patterns = await agent.search_patterns(pattern_type="success")
    print(f"盈利模式数量: {len(success_patterns)}")
    for p in success_patterns:
        print(f"  - {p['pattern_name']} (支持度: {p['support']})")

    # 搜索风险模式
    failure_patterns = await agent.search_patterns(pattern_type="failure")
    print(f"\n风险模式数量: {len(failure_patterns)}")
    for p in failure_patterns:
        print(f"  - {p['pattern_name']} (支持度: {p['support']})")

    # 测试6: 查看发现历史
    print("\n\n测试6: 查看发现历史")
    print("-" * 40)

    history = await agent.get_discovery_history()
    print(f"发现历史记录: {len(history)} 条")
    for record in history:
        print(f"  - {record['discovery_time']}: 发现 {record['patterns_found']} 个模式")
        print(f"    盈利模式: {record['success_patterns']}, 风险模式: {record['failure_patterns']}")


if __name__ == "__main__":
    asyncio.run(test_pattern_discovery())

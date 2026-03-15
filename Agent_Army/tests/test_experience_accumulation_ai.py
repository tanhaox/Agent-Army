"""
测试经验积累AI
"""
import pytest

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.evolution.experience_accumulation_ai import ExperienceAccumulationAI


@pytest.mark.asyncio
async def test_experience_accumulation():
    """测试经验积累功能"""
    print("=" * 60)
    print("测试经验积累AI")
    print("=" * 60)

    # 初始化Agent
    agent = ExperienceAccumulationAI()

    # 测试1: 记录投资路径
    print("\n测试1: 记录投资路径")
    print("-" * 40)

    dimensions = {
        "fundamental": {"pb": 0.6, "roe": 12.5},
        "technical": {"trend": "up", "resistance": 8.0},
        "capital": {"flow": "in"},
        "policy": {"support": True},
        "historical": {"cycle": "12个月"},
        "industry": {"growth": True}
    }

    prediction = {
        "stop_loss": 5.2,
        "buy_price": 5.6,
        "cost_price": 5.6,
        "resistance": [6.5, 7.8],
        "time_window": "2026年7-8月",
        "target_price": 7.5,
        "confidence": 0.75
    }

    record_id = await agent.record_investment_path(
        stock_code="601669",
        dimensions=dimensions,
        prediction=prediction,
        analysis_date=date(2026, 3, 15)
    )

    print(f"记录ID: {record_id}")

    # 测试2: 查询经验库
    print("\n测试2: 查询经验库")
    print("-" * 40)

    stats = await agent.get_statistics()
    print(f"总案例数: {stats['total_cases']}")
    print(f"成功案例: {stats['success_cases']}")
    print(f"失败案例: {stats['failure_cases']}")
    print(f"待验证案例: {stats['pending_cases']}")
    print(f"成功率: {stats['success_rate']:.1%}")

    # 测试3: 验证预测（成功案例）
    print("\n测试3: 验证预测（成功案例）")
    print("-" * 40)

    report = await agent.verify_prediction(
        record_id=record_id,
        actual_target_price=7.8,  # 超过目标价
        current_price=7.8
    )

    print(f"案例类型: {report['case_type']}")
    print(f"准确率: {report['accuracy']:.1%}")
    print(f"偏离度: {report['deviation']:.1%}")
    print(f"验证摘要: {report['verification_summary']}")

    # 测试4: 查询成功案例
    print("\n测试4: 查询成功案例")
    print("-" * 40)

    success_cases = await agent.query_experience(case_type="success")
    print(f"成功案例数: {len(success_cases)}")
    for case in success_cases:
        print(f"  - {case['record_id']}: {case['verification_summary']}")

    # 测试5: 记录失败案例
    print("\n测试5: 记录失败案例")
    print("-" * 40)

    prediction2 = {
        "stop_loss": 5.2,
        "buy_price": 5.6,
        "cost_price": 5.6,
        "resistance": [6.5, 7.8],
        "time_window": "2026年7-8月",
        "target_price": 7.5,
        "confidence": 0.75
    }

    record_id2 = await agent.record_investment_path(
        stock_code="600519",
        dimensions=dimensions,
        prediction=prediction2,
        analysis_date=date(2026, 3, 10)
    )

    # 验证为失败案例
    report2 = await agent.verify_prediction(
        record_id=record_id2,
        actual_target_price=5.0,  # 未达到目标价
        current_price=5.0
    )

    print(f"案例类型: {report2['case_type']}")
    print(f"准确率: {report2['accuracy']:.1%}")
    print(f"验证摘要: {report2['verification_summary']}")

    # 最终统计
    print("\n最终统计")
    print("-" * 40)

    stats_final = await agent.get_statistics()
    print(f"总案例数: {stats_final['total_cases']}")
    print(f"成功案例: {stats_final['success_cases']}")
    print(f"失败案例: {stats_final['failure_cases']}")
    print(f"待验证案例: {stats_final['pending_cases']}")
    print(f"成功率: {stats_final['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(test_experience_accumulation())

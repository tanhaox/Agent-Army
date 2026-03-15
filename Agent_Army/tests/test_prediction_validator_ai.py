"""
测试预测验证AI
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.validation.prediction_validator_ai import PredictionValidatorAI


@pytest.mark.asyncio
async def test_prediction_validator():
    """测试预测验证AI"""

    print("\n" + "=" * 60)
    print("  测试预测验证AI")
    print("=" * 60)

    # 初始化
    print("\n[1] 初始化")
    print("-" * 60)
    ai = PredictionValidatorAI()
    print(f"✅ 初始化成功: {ai.name}")

    # 准备测试数据
    print("\n[2] 准备测试数据")
    print("-" * 60)

    predictions = [
        {"direction": "up", "value": 2000},
        {"direction": "up", "value": 2100},
        {"direction": "down", "value": 1900},
    ]

    actual_results = [
        {"direction": "up", "value": 1950},   # 预测正确
        {"direction": "up", "value": 2050},   # 预测正确
        {"direction": "down", "value": 1850}, # 预测正确
    ]

    print(f"   预测数量: {len(predictions)}")
    print(f"   实际结果: {len(actual_results)}")

    # 验证
    print("\n[3] 验证预测")
    print("-" * 60)
    result = await ai.analyze(predictions, actual_results)

    print(f"✅ 验证完成")
    print(f"   准确率: {result['accuracy']['overall']}%")
    print(f"   评级: {result['grade']}")

    # 详细指标
    print("\n[4] 准确性指标")
    print("-" * 60)
    for key, value in result['accuracy'].items():
        print(f"   {key}: {value}%")

    # 错误模式
    print("\n[5] 错误模式")
    print("-" * 60)
    for pattern in result['error_patterns']:
        print(f"   - {pattern}")

    # 改进建议
    print("\n[6] 改进建议")
    print("-" * 60)
    for improvement in result['improvements']:
        print(f"   - {improvement}")

    # 总结
    print("\n[7] 总结")
    print("-" * 60)
    print(f"   {result['summary']}")

    print("\n" + "=" * 60)
    print("  ✅ 预测验证AI测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_prediction_validator())

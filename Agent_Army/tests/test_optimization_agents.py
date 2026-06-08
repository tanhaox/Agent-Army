"""
测试优化部Agent
"""

import asyncio
import sys
import pytest
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.business.optimization import (
    SelfEvolutionAI,
    ConfigurationOptimizationAI,
    ChipAnalysisAI
)


@pytest.mark.asyncio
async def test_self_evolution_ai():
    """测试自我进化AI"""
    print("\n" + "="*60)
    print("测试自我进化AI")
    print("="*60)

    ai = SelfEvolutionAI()
    print(f"[OK] Agent初始化成功: {ai.name}")
    print(f"  - 角色: {ai.role}")
    print(f"  - 军团: {ai.corps}")
    print(f"  - 分析类型: {ai.analysis_type}")
    print(f"  - 能力数量: {len(ai.capabilities)}")
    print(f"  - 工具数量: {len(ai.tools)}")

    # 执行分析
    try:
        result = await ai.analyze(
            "600519",
            current_price=1850.0,
            prediction_period="1y"
        )
        print(f"\n[OK] 分析执行成功")
        print(f"  - 结论: {result.conclusion}")
        print(f"  - 置信度: {result.confidence}")
        print(f"  - 风险数量: {len(result.risks)}")
        print(f"  - 建议数量: {len(result.recommendations)}")
    except Exception as e:
        print(f"\n[ERROR] 分析执行失败: {e}")


@pytest.mark.asyncio
async def test_configuration_optimization_ai():
    """测试配置优化AI"""
    print("\n" + "="*60)
    print("测试配置优化AI")
    print("="*60)

    ai = ConfigurationOptimizationAI()
    print(f"[OK] Agent初始化成功: {ai.name}")
    print(f"  - 角色: {ai.role}")
    print(f"  - 军团: {ai.corps}")
    print(f"  - 分析类型: {ai.analysis_type}")
    print(f"  - 能力数量: {len(ai.capabilities)}")
    print(f"  - 工具数量: {len(ai.tools)}")

    # 执行分析
    try:
        result = await ai.analyze(
            "600519",
            current_price=1850.0
        )
        print(f"\n[OK] 分析执行成功")
        print(f"  - 结论: {result.conclusion}")
        print(f"  - 置信度: {result.confidence}")
        print(f"  - 风险数量: {len(result.risks)}")
        print(f"  - 建议数量: {len(result.recommendations)}")
    except Exception as e:
        print(f"\n[ERROR] 分析执行失败: {e}")


@pytest.mark.asyncio
async def test_chip_analysis_ai():
    """测试筹码分析AI"""
    print("\n" + "="*60)
    print("测试筹码分析AI")
    print("="*60)

    ai = ChipAnalysisAI()
    print(f"[OK] Agent初始化成功: {ai.name}")
    print(f"  - 角色: {ai.role}")
    print(f"  - 军团: {ai.corps}")
    print(f"  - 分析类型: {ai.analysis_type}")
    print(f"  - 能力数量: {len(ai.capabilities)}")
    print(f"  - 工具数量: {len(ai.tools)}")

    # 执行分析
    try:
        result = await ai.analyze(
            "600519",
            current_price=1850.0,
            analysis_period="3m"
        )
        print(f"\n[OK] 分析执行成功")
        print(f"  - 结论: {result.conclusion}")
        print(f"  - 置信度: {result.confidence}")
        print(f"  - 风险数量: {len(result.risks)}")
        print(f"  - 建议数量: {len(result.recommendations)}")
    except Exception as e:
        print(f"\n[ERROR] 分析执行失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "#"*60)
    print("# 优化部Agent测试")
    print("#"*60)

    # 测试3个Agent
    await test_self_evolution_ai()
    await test_configuration_optimization_ai()
    await test_chip_analysis_ai()

    print("\n" + "#"*60)
    print("# 测试完成")
    print("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

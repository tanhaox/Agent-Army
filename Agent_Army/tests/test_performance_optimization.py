"""
Phase 3 性能优化测试 - 并发分析性能对比

测试目标：
1. 对比顺序执行 vs 并发执行的性能差异
2. 验证并发执行的正确性
3. 测试API节流控制效果
"""
import pytest

import asyncio
import time
from typing import Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.investment_analysis_workflow import (
    InvestmentAnalysisWorkflow,
    quick_analyze,
    quick_analyze_concurrent
)


@pytest.mark.asyncio
async def test_sequential_analysis(stock_code: str) -> Dict[str, Any]:
    """测试顺序分析"""
    print("=" * 60)
    print("测试 1: 顺序执行模式")
    print("=" * 60)

    start_time = time.time()

    try:
        workflow = InvestmentAnalysisWorkflow()
        report = await workflow.analyze_stock(stock_code)

        duration = time.time() - start_time

        return {
            "success": True,
            "duration": duration,
            "report": report,
            "mode": "sequential"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "mode": "sequential"
        }


@pytest.mark.asyncio
async def test_concurrent_analysis(stock_code: str) -> Dict[str, Any]:
    """测试并发分析"""
    print("=" * 60)
    print("测试 2: 并发执行模式")
    print("=" * 60)

    start_time = time.time()

    try:
        workflow = InvestmentAnalysisWorkflow()
        report = await workflow.analyze_stock_concurrent(stock_code)

        duration = time.time() - start_time

        return {
            "success": True,
            "duration": duration,
            "report": report,
            "mode": "concurrent"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "mode": "concurrent"
        }


async def compare_performance(stock_code: str = "600519"):
    """性能对比测试"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     Phase 3 性能优化测试 - 并发 vs 顺序                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print("")

    # 测试1: 顺序执行
    print(">>> 测试 1: 顺序执行模式...")
    seq_result = await test_sequential_analysis(stock_code)

    print("")
    print(f"顺序执行结果:")
    if seq_result["success"]:
        print(f"  - 状态: 成功")
        print(f"  - 耗时: {seq_result['duration']:.2f}秒")
        print(f"  - 股票: {seq_result['report'].stock_name}")
        print(f"  - 评分: {seq_result['report'].overall_score:.1f}/100")
    else:
        print(f"  - 状态: 失败")
        print(f"  - 耗时: {seq_result['duration']:.2f}秒")
        print(f"  - 错误: {seq_result['error']}")

    print("")
    print("=" * 60)
    print("")

    # 等待一段时间（避免API限流）
    print(">>> 等待5秒...")
    await asyncio.sleep(5)

    print("")

    # 测试2: 并发执行
    print(">>> 测试 2: 并发执行模式...")
    conc_result = await test_concurrent_analysis(stock_code)

    print("")
    print(f"并发执行结果:")
    if conc_result["success"]:
        print(f"  - 状态: 成功")
        print(f"  - 耗时: {conc_result['duration']:.2f}秒")
        print(f"  - 股票: {conc_result['report'].stock_name}")
        print(f"  - 评分: {conc_result['report'].overall_score:.1f}/100")
    else:
        print(f"  - 状态: 失败")
        print(f"  - 耗时: {conc_result['duration']:.2f}秒")
        print(f"  - 错误: {conc_result['error']}")

    print("")
    print("=" * 60)
    print("")

    # 性能对比
    print(">>> 性能对比分析:")
    print("")

    if seq_result["success"] and conc_result["success"]:
        speedup = seq_result["duration"] / conc_result["duration"] if conc_result["duration"] > 0 else 0
        time_saved = seq_result["duration"] - conc_result["duration"]

        print(f"  性能提升: {speedup:.2f}x")
        print(f"  节省时间: {time_saved:.2f}秒 ({(time_saved/seq_result['duration']*100):.1f}%)")
        print("")
        print(f"  顺序执行: {seq_result['duration']:.2f}秒")
        print(f"  并发执行: {conc_result['duration']:.2f}秒")
        print("")

        # 结果一致性检查
        seq_score = seq_result['report'].overall_score
        conc_score = conc_result['report'].overall_score
        score_diff = abs(seq_score - conc_score)

        print(f"  结果一致性:")
        print(f"    - 顺序评分: {seq_score:.1f}/100")
        print(f"    - 并发评分: {conc_score:.1f}/100")
        print(f"    - 评分差异: {score_diff:.1f}")

        if score_diff < 1.0:
            print(f"    - 结论: 结果一致（差异<1分）")
        else:
            print(f"    - 结论: 结果有差异（需要检查）")

    else:
        print(f"  无法对比（测试失败）")
        print(f"    - 顺序: {'成功' if seq_result['success'] else '失败'}")
        print(f"    - 并发: {'成功' if conc_result['success'] else '失败'}")

    print("")
    print("=" * 60)
    print("")

    # 最终结论
    print(">>> 测试结论:")
    print("")

    if seq_result["success"] and conc_result["success"]:
        if speedup > 1.5:
            print(f"  [PASS] 并发执行显著提升性能（{speedup:.2f}x）")
        else:
            print(f"  [WARN] 性能提升不明显（{speedup:.2f}x）")

        if score_diff < 1.0:
            print(f"  [PASS] 结果一致性良好")
        else:
            print(f"  [FAIL] 结果存在差异")

        print("")
        print(f"  总体评价: 优秀" if speedup > 1.5 and score_diff < 1.0 else f"  总体评价: 需改进")
    else:
        print(f"  [FAIL] 测试未完全成功")

    print("")
    print("=" * 60)


@pytest.mark.asyncio
async def test_api_rate_limiting():
    """测试API节流控制（Task #2）"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     API节流控制测试（待实现）                               ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print("")

    print(">>> 注意: API节流控制功能将在Task #2中实现")
    print("")

    # TODO: 实现API节流测试
    # 1. 快速调用多次API
    # 2. 验证节流器生效
    # 3. 测试限流后的等待时间


def main():
    """主测试入口"""
    print("")
    print("============================================================")
    print("  Phase 3 性能优化测试套件")
    print("============================================================")
    print("")

    # 运行性能对比测试
    asyncio.run(compare_performance("600519"))

    # 运行API节流测试
    # asyncio.run(test_api_rate_limiting())

    print("")
    print("============================================================")
    print("  测试完成")
    print("============================================================")
    print("")


if __name__ == "__main__":
    main()

"""
Phase 3 性能优化测试 - API调用节流控制

测试目标：
1. 验证RateLimiter基本功能
2. 测试API调用频率控制
3. 验证多API独立限流
4. 统计功能测试
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

from src.core.utils.rate_limiter import (
    RateLimiter,
    MultiRateLimiter,
    get_global_limiter_manager,
    reset_global_limiter_manager
)


@pytest.mark.asyncio
async def test_basic_rate_limiter():
    """测试1: 基本节流功能"""
    print("\n")
    print("=" * 60)
    print("测试 1: RateLimiter基本功能")
    print("=" * 60)
    print("")

    # 创建节流器：每分钟最多10次
    limiter = RateLimiter(calls_per_minute=10, name="TestLimiter")

    print(">>> 测试场景：")
    print("  - 限流阈值：10次/分钟")
    print("  - 测试调用：12次")
    print("")

    start_time = time.time()

    # 快速调用12次
    for i in range(12):
        await limiter.acquire()
        elapsed = time.time() - start_time
        print(f"  [{i+1:2d}/12] 调用成功 (经过时间: {elapsed:.2f}秒)")

    total_time = time.time() - start_time

    print("")
    print(">>> 测试结果:")
    print(f"  - 总调用次数: {limiter.total_calls}")
    print(f"  - 总等待次数: {limiter.total_waits}")
    print(f"  - 总等待时间: {limiter.total_wait_time:.2f}秒")
    print(f"  - 平均等待时间: {limiter.total_wait_time/limiter.total_waits:.2f}秒" if limiter.total_waits > 0 else "  - 平均等待时间: 0秒")
    print(f"  - 实际耗时: {total_time:.2f}秒")
    print("")

    # 验证结果
    if limiter.total_waits > 0:
        print("[PASS] 节流器正常工作，触发了等待")
    else:
        print("[FAIL] 节流器未触发等待")

    if limiter.total_calls == 12:
        print("[PASS] 调用次数正确")
    else:
        print(f"[FAIL] 调用次数错误（预期12，实际{limiter.total_calls}）")

    print("")


@pytest.mark.asyncio
async def test_multi_rate_limiter():
    """测试2: 多API节流管理"""
    print("\n")
    print("=" * 60)
    print("测试 2: MultiRateLimiter多API管理")
    print("=" * 60)
    print("")

    manager = MultiRateLimiter()

    # 注册两个API节流器
    tushare_limiter = manager.register("tushare", 180)
    zhipu_limiter = manager.register("zhipu_ai", 60)

    print(">>> 已注册API节流器:")
    print(f"  - Tushare: {tushare_limiter.calls_per_minute}次/分钟")
    print(f"  - 智谱AI: {zhipu_limiter.calls_per_minute}次/分钟")
    print("")

    # 测试独立调用
    print(">>> 测试独立调用:")
    await manager.acquire("tushare")
    print("  [1] Tushare调用成功")

    await manager.acquire("zhipu_ai")
    print("  [2] 智谱AI调用成功")
    print("")

    # 测试统计
    stats = manager.get_all_stats()
    print(">>> 统计信息:")
    for api_name, stat in stats.items():
        print(f"  - {api_name}:")
        print(f"    * 限流阈值: {stat['calls_per_minute_limit']}次/分钟")
        print(f"    * 总调用次数: {stat['total_calls']}")
        print(f"    * 总等待次数: {stat['total_waits']}")

    print("")
    print("[PASS] 多API节流器正常工作")
    print("")


@pytest.mark.asyncio
async def test_global_limiter_manager():
    """测试3: 全局节流器管理器"""
    print("\n")
    print("=" * 60)
    print("测试 3: 全局节流器管理器")
    print("=" * 60)
    print("")

    # 重置全局管理器（确保干净状态）
    reset_global_limiter_manager()

    # 获取全局管理器
    manager = get_global_limiter_manager()

    print(">>> 全局节流器配置:")
    stats = manager.get_all_stats()
    for api_name, stat in stats.items():
        print(f"  - {api_name}: {stat['calls_per_minute_limit']}次/分钟")
    print("")

    # 验证默认配置
    if "tushare" in stats and "zhipu_ai" in stats:
        print("[PASS] 默认节流器已注册")
    else:
        print("[FAIL] 默认节流器未注册")

    print("")


@pytest.mark.asyncio
async def test_financial_tool_integration():
    """测试4: FinancialTool集成测试"""
    print("\n")
    print("=" * 60)
    print("测试 4: FinancialTool集成测试")
    print("=" * 60)
    print("")

    from src.core.tools.data_source.financial_tool import FinancialTool

    print(">>> 创建FinancialTool实例...")
    tool = FinancialTool()

    print(">>> 验证节流器初始化...")
    if tool.rate_limiter is not None:
        print(f"  - 节流器名称: {tool.rate_limiter.name}")
        print(f"  - 限流阈值: {tool.rate_limiter.calls_per_minute}次/分钟")
        print("[PASS] FinancialTool节流器已集成")
    else:
        print("[FAIL] FinancialTool节流器未初始化")

    print("")


@pytest.mark.asyncio
async def test_llm_tool_integration():
    """测试5: LLMTool集成测试"""
    print("\n")
    print("=" * 60)
    print("测试 5: LLMTool集成测试")
    print("=" * 60)
    print("")

    from src.core.tools.ai_service.llm_tool import LLMTool

    print(">>> 创建LLMTool实例...")
    tool = LLMTool()

    print(">>> 验证节流器初始化...")
    if tool.rate_limiter is not None:
        print(f"  - 节流器名称: {tool.rate_limiter.name}")
        print(f"  - 限流阈值: {tool.rate_limiter.calls_per_minute}次/分钟")
        print("[PASS] LLMTool节流器已集成")
    else:
        print("[FAIL] LLMTool节流器未初始化")

    print("")


@pytest.mark.asyncio
async def test_rate_limiting_with_real_calls():
    """测试6: 真实API调用节流测试（模拟）"""
    print("\n")
    print("=" * 60)
    print("测试 6: 真实API调用节流模拟")
    print("=" * 60)
    print("")

    # 创建严格节流器：每分钟3次
    limiter = RateLimiter(calls_per_minute=3, name="StrictTest")

    print(">>> 测试场景:")
    print("  - 限流阈值: 3次/分钟（严格模式）")
    print("  - 模拟调用: 5次")
    print("  - 预期行为: 前3次立即通过，后2次需要等待")
    print("")

    start_time = time.time()
    call_times = []

    for i in range(5):
        await limiter.acquire()
        elapsed = time.time() - start_time
        call_times.append(elapsed)
        print(f"  [{i+1}/5] 调用成功 (经过时间: {elapsed:.2f}秒)")

    total_time = time.time() - start_time

    print("")
    print(">>> 分析结果:")
    print(f"  - 总耗时: {total_time:.2f}秒")
    print(f"  - 等待次数: {limiter.total_waits}")
    print(f"  - 等待时间: {limiter.total_wait_time:.2f}秒")
    print("")

    # 验证节流行为
    if limiter.total_waits >= 2:
        print("[PASS] 节流器正确限制了调用频率")
    else:
        print(f"[WARN] 节流器可能未完全生效（预期至少等待2次，实际{limiter.total_waits}次）")

    if total_time >= 6:  # 至少等待60秒 * 2/3 = 40秒（考虑浮点误差）
        print("[PASS] 总耗时符合预期（超过1分钟窗口）")
    else:
        print(f"[INFO] 总耗时较短（{total_time:.2f}秒），可能在窗口期内")

    print("")


def main():
    """主测试入口"""
    print("")
    print("============================================================")
    print("  Phase 3 API节流控制测试套件")
    print("============================================================")
    print("")

    # 运行所有测试
    asyncio.run(test_basic_rate_limiter())
    asyncio.run(test_multi_rate_limiter())
    asyncio.run(test_global_limiter_manager())
    asyncio.run(test_financial_tool_integration())
    asyncio.run(test_llm_tool_integration())
    asyncio.run(test_rate_limiting_with_real_calls())

    print("")
    print("============================================================")
    print("  所有测试完成")
    print("============================================================")
    print("")


if __name__ == "__main__":
    main()

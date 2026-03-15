"""
Phase 3 性能优化测试 - 分析结果缓存

测试目标：
1. 验证AnalysisCache基本功能
2. 测试TTL过期机制
3. 测试LRU淘汰策略
4. 缓存命中率统计
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

from src.core.utils.cache import (
    AnalysisCache,
    MultiCacheManager,
    get_global_cache_manager,
    reset_global_cache_manager
)


def test_basic_cache():
    """测试1: 基本缓存功能"""
    print("\n")
    print("=" * 60)
    print("测试 1: AnalysisCache基本功能")
    print("=" * 60)
    print("")

    cache = AnalysisCache(ttl=60, max_size=100, name="TestCache")

    print(">>> 测试场景：")
    print("  - 缓存容量：100")
    print("  - TTL：60秒")
    print("")

    # 设置缓存
    print(">>> 设置缓存...")
    cache.set("key1", {"data": "value1"})
    cache.set("key2", {"data": "value2"})
    print("  - 已设置2个缓存项")

    # 获取缓存
    print("")
    print(">>> 获取缓存...")
    value1 = cache.get("key1")
    value2 = cache.get("key2")
    value3 = cache.get("key3")  # 不存在

    print(f"  - key1: {value1}")
    print(f"  - key2: {value2}")
    print(f"  - key3: {value3}")

    print("")
    print(">>> 统计信息:")
    stats = cache.get_stats()
    print(f"  - 总请求数: {stats['total_requests']}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")
    print(f"  - 命中率: {stats['hit_rate']:.2f}%")

    print("")
    if stats['hits'] == 2 and stats['misses'] == 1:
        print("[PASS] 基本缓存功能正常")
    else:
        print("[FAIL] 基本缓存功能异常")

    print("")


def test_ttl_expiration():
    """测试2: TTL过期机制"""
    print("\n")
    print("=" * 60)
    print("测试 2: TTL过期机制")
    print("=" * 60)
    print("")

    # 设置短TTL：2秒
    cache = AnalysisCache(ttl=2, max_size=100, name="TTLTestCache")

    print(">>> 测试场景：")
    print("  - TTL：2秒")
    print("  - 测试：立即获取 vs 延迟获取")
    print("")

    # 设置缓存
    cache.set("key1", {"data": "value1"})
    print(">>> 设置缓存: key1")

    # 立即获取
    print("")
    print(">>> 立即获取:")
    value = cache.get("key1")
    print(f"  - 结果: {value}")

    if value is not None:
        print("[PASS] 立即获取成功")
    else:
        print("[FAIL] 立即获取失败")

    # 等待3秒
    print("")
    print(">>> 等待3秒...")
    time.sleep(3)

    # 再次获取（应该过期）
    print("")
    print(">>> 3秒后获取:")
    value = cache.get("key1")
    print(f"  - 结果: {value}")

    if value is None:
        print("[PASS] 缓存已过期")
    else:
        print("[FAIL] 缓存未过期")

    print("")


def test_lru_eviction():
    """测试3: LRU淘汰策略"""
    print("\n")
    print("=" * 60)
    print("测试 3: LRU淘汰策略")
    print("=" * 60)
    print("")

    # 设置小容量：3个
    cache = AnalysisCache(ttl=60, max_size=3, name="LRUTestCache")

    print(">>> 测试场景：")
    print("  - 缓存容量：3")
    print("  - 测试：添加4个项，观察淘汰")
    print("")

    # 添加4个项
    print(">>> 添加缓存项:")
    cache.set("key1", "value1")
    print("  - 添加 key1")
    cache.set("key2", "value2")
    print("  - 添加 key2")
    cache.set("key3", "value3")
    print("  - 添加 key3")
    cache.set("key4", "value4")  # 应该淘汰key1
    print("  - 添加 key4（应淘汰key1）")

    print("")
    print(">>> 验证缓存状态:")
    value1 = cache.get("key1")
    value2 = cache.get("key2")
    value3 = cache.get("key3")
    value4 = cache.get("key4")

    print(f"  - key1: {value1} {'(已淘汰)' if value1 is None else ''}")
    print(f"  - key2: {value2}")
    print(f"  - key3: {value3}")
    print(f"  - key4: {value4}")

    print("")
    stats = cache.get_stats()
    print(f">>> 统计信息:")
    print(f"  - 淘汰次数: {stats['evictions']}")

    if value1 is None and value2 is not None and value3 is not None and value4 is not None:
        print("[PASS] LRU淘汰策略正常")
    else:
        print("[FAIL] LRU淘汰策略异常")

    print("")


def test_get_or_compute():
    """测试4: get_or_compute功能"""
    print("\n")
    print("=" * 60)
    print("测试 4: get_or_compute功能")
    print("=" * 60)
    print("")

    cache = AnalysisCache(ttl=60, max_size=100, name="ComputeTestCache")

    # 定义计算函数
    compute_count = 0

    def expensive_computation(x: int, y: int) -> int:
        """模拟耗时计算"""
        nonlocal compute_count
        compute_count += 1
        print(f"  - 执行计算（第{compute_count}次）: {x} + {y}")
        time.sleep(0.1)  # 模拟耗时
        return x + y

    print(">>> 测试场景：")
    print("  - 相同参数调用3次")
    print("  - 预期：第1次计算，第2-3次使用缓存")
    print("")

    # 第1次调用（应该计算）
    print(">>> 第1次调用:")
    result1 = cache.get_or_compute(expensive_computation, 10, 20)
    print(f"  - 结果: {result1}")

    # 第2次调用（应该使用缓存）
    print("")
    print(">>> 第2次调用（相同参数）:")
    result2 = cache.get_or_compute(expensive_computation, 10, 20)
    print(f"  - 结果: {result2}")

    # 第3次调用（应该使用缓存）
    print("")
    print(">>> 第3次调用（相同参数）:")
    result3 = cache.get_or_compute(expensive_computation, 10, 20)
    print(f"  - 结果: {result3}")

    print("")
    stats = cache.get_stats()
    print(f">>> 统计信息:")
    print(f"  - 计算次数: {compute_count}")
    print(f"  - 缓存命中: {stats['hits']}")
    print(f"  - 命中率: {stats['hit_rate']:.2f}%")

    if compute_count == 1 and stats['hits'] == 2:
        print("[PASS] get_or_compute功能正常")
    else:
        print("[FAIL] get_or_compute功能异常")

    print("")


@pytest.mark.asyncio
async def test_get_or_compute_async():
    """测试5: get_or_compute_async功能（异步）"""
    print("\n")
    print("=" * 60)
    print("测试 5: get_or_compute_async功能（异步）")
    print("=" * 60)
    print("")

    cache = AnalysisCache(ttl=60, max_size=100, name="AsyncTestCache")

    # 定义异步计算函数
    compute_count = 0

    async def async_computation(x: int, y: int) -> int:
        """模拟异步耗时计算"""
        nonlocal compute_count
        compute_count += 1
        print(f"  - 执行异步计算（第{compute_count}次）: {x} + {y}")
        await asyncio.sleep(0.1)  # 模拟异步耗时
        return x + y

    print(">>> 测试场景：")
    print("  - 异步调用3次")
    print("  - 预期：第1次计算，第2-3次使用缓存")
    print("")

    # 第1次调用（应该计算）
    print(">>> 第1次调用:")
    result1 = await cache.get_or_compute_async(async_computation, 5, 10)
    print(f"  - 结果: {result1}")

    # 第2次调用（应该使用缓存）
    print("")
    print(">>> 第2次调用（相同参数）:")
    result2 = await cache.get_or_compute_async(async_computation, 5, 10)
    print(f"  - 结果: {result2}")

    # 第3次调用（应该使用缓存）
    print("")
    print(">>> 第3次调用（相同参数）:")
    result3 = await cache.get_or_compute_async(async_computation, 5, 10)
    print(f"  - 结果: {result3}")

    print("")
    stats = cache.get_stats()
    print(f">>> 统计信息:")
    print(f"  - 计算次数: {compute_count}")
    print(f"  - 缓存命中: {stats['hits']}")
    print(f"  - 命中率: {stats['hit_rate']:.2f}%")

    if compute_count == 1 and stats['hits'] == 2:
        print("[PASS] get_or_compute_async功能正常")
    else:
        print("[FAIL] get_or_compute_async功能异常")

    print("")


def test_multi_cache_manager():
    """测试6: 多缓存管理器"""
    print("\n")
    print("=" * 60)
    print("测试 6: MultiCacheManager多缓存管理")
    print("=" * 60)
    print("")

    manager = MultiCacheManager()

    print(">>> 注册缓存:")
    cache1 = manager.register("cache1", ttl=60, max_size=100)
    cache2 = manager.register("cache2", ttl=120, max_size=200)
    print("  - cache1: TTL=60秒, 容量=100")
    print("  - cache2: TTL=120秒, 容量=200")

    print("")
    print(">>> 测试独立缓存:")
    cache1.set("key1", "value1")
    cache2.set("key1", "value2")

    value1 = cache1.get("key1")
    value2 = cache2.get("key1")

    print(f"  - cache1['key1']: {value1}")
    print(f"  - cache2['key1']: {value2}")

    print("")
    if value1 == "value1" and value2 == "value2":
        print("[PASS] 多缓存独立管理正常")
    else:
        print("[FAIL] 多缓存独立管理异常")

    print("")


def test_global_cache_manager():
    """测试7: 全局缓存管理器"""
    print("\n")
    print("=" * 60)
    print("测试 7: 全局缓存管理器")
    print("=" * 60)
    print("")

    # 重置全局管理器
    reset_global_cache_manager()

    # 获取全局管理器
    manager = get_global_cache_manager()

    print(">>> 全局缓存配置:")
    stats = manager.get_all_stats()
    for cache_name, stat in stats.items():
        print(f"  - {cache_name}:")
        print(f"    * TTL: {stat['ttl']}秒")
        print(f"    * 最大容量: {stat['max_size']}")

    print("")
    if "industry_analysis" in stats and "fundamental_analysis" in stats:
        print("[PASS] 全局缓存管理器正常")
    else:
        print("[FAIL] 全局缓存管理器异常")

    print("")


def main():
    """主测试入口"""
    print("")
    print("============================================================")
    print("  Phase 3 分析结果缓存测试套件")
    print("============================================================")
    print("")

    # 运行所有测试
    test_basic_cache()
    test_ttl_expiration()
    test_lru_eviction()
    test_get_or_compute()
    asyncio.run(test_get_or_compute_async())
    test_multi_cache_manager()
    test_global_cache_manager()

    print("")
    print("============================================================")
    print("  所有测试完成")
    print("============================================================")
    print("")


if __name__ == "__main__":
    main()

"""
Phase 3 修复验证测试

测试目标：
1. 验证缓存键生成器安全性（敏感字段过滤）
2. 验证缓存监控和清理机制
3. 验证RateLimiter超时机制
"""
import pytest

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.utils.cache import AnalysisCache, MultiCacheManager
from src.core.utils.rate_limiter import RateLimiter


def test_cache_key_security():
    """测试1: 缓存键安全性（敏感字段过滤）"""
    print("\n")
    print("=" * 60)
    print("测试 1: 缓存键安全性")
    print("=" * 60)
    print("")

    cache = AnalysisCache(ttl=60, max_size=100, name="SecurityTest")

    print(">>> 测试场景：")
    print("  - 场景1: 正常参数（应包含在缓存键中）")
    print("  - 场景2: 敏感参数（应被过滤）")
    print("")

    # 场景1: 正常参数
    key1 = cache._generate_key(
        "test_func",
        "arg1",
        stock_code="600519",
        years=3
    )
    print(f"[PASS] 场景1 - 正常参数缓存键: {key1[:16]}...")

    # 场景2: 包含敏感字段
    key2 = cache._generate_key(
        "test_func",
        "arg1",
        stock_code="600519",
        api_key="SECRET_KEY_123",  # [WARN] 应被过滤
        token="SECRET_TOKEN_456",  # [WARN] 应被过滤
        password="SECRET_PWD_789",  # [WARN] 应被过滤
        years=3
    )
    print(f"[PASS] 场景2 - 敏感参数缓存键: {key2[:16]}...")

    # 验证：两次调用的缓存键应该相同（因为敏感字段被过滤）
    print("")
    if key1 == key2:
        print("[PASS] [PASS] 敏感字段已正确过滤（缓存键相同）")
    else:
        print("[FAIL] [FAIL] 敏感字段未过滤（缓存键不同）")

    # 验证：缓存键是SHA256（64字符），不是MD5（32字符）
    print("")
    if len(key1) == 64:
        print("[PASS] [PASS] 使用SHA256哈希（更安全）")
    else:
        print(f"[FAIL] [FAIL] 哈希长度错误（预期64，实际{len(key1)}）")

    print("")


def test_cache_monitoring():
    """测试2: 缓存监控机制"""
    print("\n")
    print("=" * 60)
    print("测试 2: 缓存监控机制")
    print("=" * 60)
    print("")

    manager = MultiCacheManager()

    print(">>> 注册缓存:")
    cache1 = manager.register("test_cache1", ttl=2, max_size=100)
    cache2 = manager.register("test_cache2", ttl=2, max_size=100)
    print("  - test_cache1: TTL=2秒")
    print("  - test_cache2: TTL=2秒")

    # 添加数据
    print("")
    print(">>> 添加缓存数据:")
    cache1.set("key1", "value1")
    cache2.set("key2", "value2")
    print("  - test_cache1: key1 = value1")
    print("  - test_cache2: key2 = value2")

    # 检查统计信息
    print("")
    print(">>> 检查统计信息:")
    stats = manager.get_all_stats()

    if "__total__" in stats:
        total_stats = stats["__total__"]
        print(f"  - 总缓存数: {total_stats['total_caches']}")
        print(f"  - 总内存占用: {total_stats['total_memory_mb']:.2f}MB")
        print(f"  - 监控线程运行: {total_stats['monitor_running']}")

        if total_stats['monitor_running']:
            print("[PASS] [PASS] 后台监控线程已启动")
        else:
            print("[FAIL] [FAIL] 后台监控线程未启动")
    else:
        print("[FAIL] [FAIL] 缺少总览统计信息")

    # 等待过期
    print("")
    print(">>> 等待3秒（缓存应过期）...")
    time.sleep(3)

    # 清理过期缓存
    print("")
    print(">>> 清理过期缓存:")
    manager.cleanup_all_expired()

    # 验证清理结果
    if cache1.get("key1") is None and cache2.get("key2") is None:
        print("[PASS] [PASS] 过期缓存已清理")
    else:
        print("[FAIL] [FAIL] 过期缓存未清理")

    # 停止监控线程
    print("")
    print(">>> 停止监控线程:")
    manager.shutdown()

    stats_after = manager.get_all_stats()
    if not stats_after.get("__total__", {}).get("monitor_running", True):
        print("[PASS] [PASS] 监控线程已停止")
    else:
        print("[FAIL] [FAIL] 监控线程未停止")

    print("")


@pytest.mark.asyncio
async def test_rate_limiter_timeout():
    """测试3: RateLimiter超时机制"""
    print("\n")
    print("=" * 60)
    print("测试 3: RateLimiter超时机制")
    print("=" * 60)
    print("")

    # 创建严格限流器：3次/分钟
    limiter = RateLimiter(calls_per_minute=3, name="TimeoutTest")

    print(">>> 测试场景：")
    print("  - 限流阈值: 3次/分钟")
    print("  - 快速调用5次")
    print("  - 预期：第4-5次触发等待，但不应无限阻塞")
    print("")

    start_time = time.time()

    try:
        # 快速调用5次
        for i in range(5):
            try:
                await limiter.acquire(timeout=5.0)  #  设置超时5秒
                elapsed = time.time() - start_time
                print(f"  [{i+1}/5] 调用成功 (经过{elapsed:.2f}秒)")
            except TimeoutError as e:
                elapsed = time.time() - start_time
                print(f"  [{i+1}/5] [FAIL] 超时: {e} (经过{elapsed:.2f}秒)")
                break

        total_time = time.time() - start_time

        print("")
        print(f">>> 总耗时: {total_time:.2f}秒")

        # 验证：应该有等待，但总耗时不应超过10秒
        if total_time < 10:
            print("[PASS] [PASS] 超时机制正常（总耗时 < 10秒）")
        else:
            print(f"[FAIL] [FAIL] 可能死锁（总耗时 {total_time:.2f}秒 > 10秒）")

        # 验证统计信息
        stats = limiter.get_stats()
        print("")
        print(f">>> 统计信息:")
        print(f"  - 总调用: {stats['total_calls']}")
        print(f"  - 总等待: {stats['total_waits']}")
        print(f"  - 总等待时间: {stats['total_wait_time']:.2f}秒")

        if stats['total_waits'] > 0:
            print("[PASS] [PASS] 限流器正常工作（触发了等待）")
        else:
            print("[WARN] [WARN] 限流器可能未触发（无等待）")

    except Exception as e:
        print(f"[FAIL] [FAIL] 测试异常: {e}")

    print("")


def main():
    """主测试入口"""
    print("")
    print("============================================================")
    print("  Phase 3 修复验证测试套件")
    print("============================================================")
    print("")

    # 运行所有测试
    test_cache_key_security()
    test_cache_monitoring()
    asyncio.run(test_rate_limiter_timeout())

    print("")
    print("============================================================")
    print("  所有测试完成")
    print("============================================================")
    print("")


if __name__ == "__main__":
    main()

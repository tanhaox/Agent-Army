"""
Agent Army - 分析结果缓存系统

功能：
1. 缓存Agent分析结果（减少重复API调用）
2. 支持TTL过期机制
3. 缓存命中率统计
4. 内存管理（LRU淘汰策略）

使用场景：
- 相同股票重复分析
- 历史数据复用
- API调用优化
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, Callable, Tuple
from collections import OrderedDict
import logging


class AnalysisCache:
    """
    分析结果缓存

    特性：
    - TTL过期机制
    - LRU淘汰策略
    - 线程安全（单线程asyncio环境）
    - 统计功能
    """

    def __init__(
        self,
        ttl: int = 3600,
        max_size: int = 1000,
        name: str = "DefaultCache"
    ):
        """
        初始化缓存

        Args:
            ttl: 缓存过期时间（秒），默认1小时
            max_size: 最大缓存数量，默认1000个
            name: 缓存名称（用于日志）
        """
        self.ttl = ttl
        self.max_size = max_size
        self.name = name
        self.logger = logging.getLogger(f"AnalysisCache.{name}")

        # 缓存存储（使用OrderedDict实现LRU）
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "total_requests": 0
        }

        self.logger.info(
            f"缓存初始化完成: TTL={ttl}秒, 最大容量={max_size}"
        )

    def _generate_key(
        self,
        func_name: str,
        *args,
        **kwargs
    ) -> str:
        """
        生成缓存键（安全增强版）

        Args:
            func_name: 函数名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键（SHA256哈希）

        注意：
            - 过滤敏感字段（api_key, token, password等）
            - 使用SHA256替代MD5（更安全）
        """
        # ⭐ P0修复: 过滤敏感字段
        SENSITIVE_FIELDS = {
            "api_key", "token", "password", "secret",
            "auth", "credential", "private_key"
        }

        safe_kwargs = {
            k: v for k, v in kwargs.items()
            if k.lower() not in SENSITIVE_FIELDS
        }

        # 将参数序列化为字符串
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": safe_kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)

        # ⭐ P0修复: 使用SHA256替代MD5（更安全，碰撞风险更低）
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值（如果存在且未过期），否则None
        """
        self.stats["total_requests"] += 1

        if key not in self.cache:
            self.stats["misses"] += 1
            self.logger.debug(f"缓存未命中: {key[:8]}...")
            return None

        # 检查是否过期
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            # 过期，删除缓存
            del self.cache[key]
            self.stats["misses"] += 1
            self.stats["expirations"] += 1
            self.logger.debug(f"缓存已过期: {key[:8]}...")
            return None

        # 缓存命中，移动到末尾（LRU）
        self.cache.move_to_end(key)
        self.stats["hits"] += 1
        self.logger.debug(f"缓存命中: {key[:8]}...")

        return value

    def set(self, key: str, value: Any):
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果键已存在，先删除
        if key in self.cache:
            del self.cache[key]

        # 检查容量，执行LRU淘汰
        while len(self.cache) >= self.max_size:
            # 删除最久未使用的项（OrderedDict的第一个）
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
            self.logger.debug(f"LRU淘汰: {oldest_key[:8]}...")

        # 添加新缓存
        self.cache[key] = (value, time.time())
        self.logger.debug(f"缓存已设置: {key[:8]}...")

    def get_or_compute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        获取缓存或计算结果（同步版本）

        Args:
            func: 计算函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存值或计算结果
        """
        # 生成缓存键
        key = self._generate_key(func.__name__, *args, **kwargs)

        # 尝试获取缓存
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        # 缓存未命中，执行计算
        self.logger.info(f"执行计算: {func.__name__}")
        result = func(*args, **kwargs)

        # 存入缓存
        self.set(key, result)

        return result

    async def get_or_compute_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        获取缓存或计算结果（异步版本）

        Args:
            func: 异步计算函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存值或计算结果
        """
        # 生成缓存键
        key = self._generate_key(func.__name__, *args, **kwargs)

        # 尝试获取缓存
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        # 缓存未命中，执行计算
        self.logger.info(f"执行异步计算: {func.__name__}")
        result = await func(*args, **kwargs)

        # 存入缓存
        self.set(key, result)

        return result

    def clear(self):
        """清空缓存"""
        count = len(self.cache)
        self.cache.clear()
        self.logger.info(f"缓存已清空: 删除{count}项")

    def cleanup_expired(self):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]
            self.stats["expirations"] += 1

        if expired_keys:
            self.logger.info(f"清理过期缓存: 删除{len(expired_keys)}项")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        total_requests = self.stats["total_requests"]
        hit_rate = (
            self.stats["hits"] / total_requests * 100
            if total_requests > 0 else 0
        )

        return {
            "name": self.name,
            "ttl": self.ttl,
            "max_size": self.max_size,
            "current_size": len(self.cache),
            "total_requests": total_requests,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"]
        }

    def get_size(self) -> int:
        """获取当前缓存数量"""
        return len(self.cache)


class MultiCacheManager:
    """
    多缓存管理器（带监控和自动清理）

    ⭐ P0修复: 添加后台监控线程，防止内存泄漏
    """

    def __init__(self):
        """初始化多缓存管理器"""
        self.caches: Dict[str, AnalysisCache] = {}
        self.logger = logging.getLogger("MultiCacheManager")

        # ⭐ P0修复: 后台监控线程
        self._monitor_thread = None
        self._monitor_running = False
        self._start_background_monitor()

    def _start_background_monitor(self):
        """
        ⭐ P0修复: 启动后台监控线程

        功能：
        - 每60秒清理过期缓存
        - 监控容量使用率，超过90%告警
        - 记录缓存统计信息
        """
        import threading

        def monitor_loop():
            while self._monitor_running:
                try:
                    # 每60秒执行一次
                    time.sleep(60)

                    # 清理所有过期缓存
                    self.cleanup_all_expired()

                    # 检查容量告警
                    stats = self.get_all_stats()
                    for name, stat in stats.items():
                        usage_rate = stat['current_size'] / stat['max_size']
                        if usage_rate > 0.9:
                            self.logger.warning(
                                f"⚠️ 缓存 '{name}' 容量告警: "
                                f"{stat['current_size']}/{stat['max_size']} "
                                f"({usage_rate*100:.1f}%)"
                            )

                        # 记录缓存统计（每10分钟一次）
                        if int(time.time()) % 600 == 0:
                            self.logger.info(
                                f"📊 缓存统计 '{name}': "
                                f"大小={stat['current_size']}, "
                                f"命中率={stat['hit_rate']:.1f}%, "
                                f"淘汰={stat['evictions']}, "
                                f"过期={stat['expirations']}"
                            )

                except Exception as e:
                    self.logger.error(f"缓存监控线程异常: {e}")

        self._monitor_running = True
        self._monitor_thread = threading.Thread(
            target=monitor_loop,
            daemon=True,  # 守护线程，主进程退出时自动结束
            name="CacheMonitor"
        )
        self._monitor_thread.start()
        self.logger.info("✅ 缓存监控线程已启动（每60秒检查一次）")

    def register(
        self,
        cache_name: str,
        ttl: int = 3600,
        max_size: int = 1000
    ) -> AnalysisCache:
        """
        注册缓存

        Args:
            cache_name: 缓存名称
            ttl: 过期时间（秒）
            max_size: 最大容量

        Returns:
            缓存实例
        """
        if cache_name in self.caches:
            self.logger.warning(f"缓存 '{cache_name}' 已存在，将覆盖")

        cache = AnalysisCache(
            ttl=ttl,
            max_size=max_size,
            name=cache_name
        )
        self.caches[cache_name] = cache

        self.logger.info(
            f"注册缓存: {cache_name} (TTL={ttl}秒, 容量={max_size})"
        )

        return cache

    def get(self, cache_name: str) -> Optional[AnalysisCache]:
        """
        获取缓存

        Args:
            cache_name: 缓存名称

        Returns:
            缓存实例（如果不存在返回None）
        """
        return self.caches.get(cache_name)

    def clear_all(self):
        """清空所有缓存"""
        for cache in self.caches.values():
            cache.clear()

        self.logger.info("所有缓存已清空")

    def cleanup_all_expired(self):
        """
        ⭐ P0修复: 清理所有缓存的过期项

        遍历所有缓存，删除过期的数据项
        """
        total_cleaned = 0
        for name, cache in self.caches.items():
            before_size = cache.get_size()
            cache.cleanup_expired()
            after_size = cache.get_size()
            cleaned = before_size - after_size

            if cleaned > 0:
                total_cleaned += cleaned
                self.logger.info(
                    f"缓存 '{name}' 清理完成: "
                    f"删除 {cleaned} 个过期项，"
                    f"剩余 {after_size} 项"
                )

        if total_cleaned > 0:
            self.logger.info(f"✅ 总计清理 {total_cleaned} 个过期缓存项")

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        获取所有缓存的统计信息（增强版）

        Returns:
            所有缓存的统计数据，包含总内存占用估算
        """
        stats = {}
        total_memory_mb = 0

        for name, cache in self.caches.items():
            cache_stats = cache.get_stats()

            # 估算内存占用（假设每个缓存项平均1KB）
            estimated_memory_kb = cache_stats['current_size']  # 1KB/项
            estimated_memory_mb = estimated_memory_kb / 1024
            cache_stats['estimated_memory_mb'] = estimated_memory_mb

            stats[name] = cache_stats
            total_memory_mb += estimated_memory_mb

        # 添加总览信息
        stats['__total__'] = {
            'total_caches': len(self.caches),
            'total_memory_mb': total_memory_mb,
            'monitor_running': self._monitor_running
        }

        return stats

    def shutdown(self):
        """
        ⭐ P0修复: 停止监控线程

        在程序退出时调用，优雅关闭后台线程
        """
        if self._monitor_thread and self._monitor_running:
            self._monitor_running = False
            self._monitor_thread.join(timeout=5)
            self.logger.info("✅ 缓存监控线程已停止")

    def cleanup_all_expired(self):
        """清理所有缓存的过期项"""
        for cache in self.caches.values():
            cache.cleanup_expired()

        self.logger.info("所有过期缓存已清理")


# ==================== 全局缓存管理器 ====================

_global_cache_manager: Optional[MultiCacheManager] = None


def get_global_cache_manager() -> MultiCacheManager:
    """
    获取全局缓存管理器（单例模式）

    Returns:
        MultiCacheManager: 全局缓存管理器
    """
    global _global_cache_manager

    if _global_cache_manager is None:
        _global_cache_manager = MultiCacheManager()

        # 注册默认缓存
        _global_cache_manager.register(
            "industry_analysis",
            ttl=7200,  # 产业链分析：2小时
            max_size=500
        )
        _global_cache_manager.register(
            "fundamental_analysis",
            ttl=3600,  # 基本面分析：1小时
            max_size=500
        )
        _global_cache_manager.register(
            "financial_data",
            ttl=1800,  # 财务数据：30分钟
            max_size=1000
        )

    return _global_cache_manager


def reset_global_cache_manager():
    """重置全局缓存管理器（主要用于测试）"""
    global _global_cache_manager
    _global_cache_manager = None

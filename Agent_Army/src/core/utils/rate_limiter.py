"""
Agent Army - API调用节流器

功能：
1. 控制API调用频率（避免触发限流）
2. 支持多API独立限流
3. 异步等待机制
4. 调用统计

使用场景：
- Tushare API：≤200次/分钟
- 智谱AI API：根据套餐限制
- 其他第三方API
"""

import asyncio
import time
from typing import Dict, List, Optional
from collections import defaultdict
import logging


class RateLimiter:
    """API调用节流器"""

    def __init__(
        self,
        calls_per_minute: int = 180,
        name: str = "DefaultLimiter"
    ):
        """
        初始化节流器

        Args:
            calls_per_minute: 每分钟允许的最大调用次数
            name: 节流器名称（用于日志）
        """
        self.calls_per_minute = calls_per_minute
        self.name = name
        self.calls: List[float] = []  # 存储调用时间戳
        self.logger = logging.getLogger(f"RateLimiter.{name}")

        # 统计信息
        self.total_calls = 0
        self.total_waits = 0
        self.total_wait_time = 0.0

    async def acquire(self, timeout: float = 70.0) -> bool:
        """
        ⭐ P1修复: 获取调用许可（带超时机制）

        Args:
            timeout: 最大等待时间（秒），默认70秒（略大于1分钟窗口）

        Returns:
            bool: 是否成功获取许可

        Raises:
            TimeoutError: 超过最大等待时间仍未获取许可

        改进：
            - 添加超时机制，避免无限等待
            - 渐进式等待策略（最多等5秒，然后重试）
            - 防止死锁
        """
        start_time = time.time()

        while True:
            now = time.time()

            # 清理1分钟前的调用记录
            self.calls = [c for c in self.calls if now - c < 60]

            # 如果未达到限流阈值，立即获取许可
            if len(self.calls) < self.calls_per_minute:
                self.calls.append(now)
                self.total_calls += 1
                return True

            # ⭐ 检查超时
            elapsed = now - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"[{self.name}] 获取API调用许可超时 "
                    f"(等待{elapsed:.1f}秒 > {timeout}秒)，"
                    f"当前调用频率: {len(self.calls)}/{self.calls_per_minute}次/分钟"
                )

            # ⭐ 渐进式等待策略：最多等5秒
            wait_time = min(60 - (now - self.calls[0]), 5.0)

            self.logger.info(
                f"[{self.name}] 达到限流阈值 {self.calls_per_minute}次/分钟，"
                f"等待 {wait_time:.2f}秒... "
                f"(已等待{elapsed:.1f}秒/上限{timeout}秒)"
            )

            await asyncio.sleep(wait_time)

            # 统计
            self.total_waits += 1
            self.total_wait_time += wait_time

    def get_stats(self) -> Dict[str, any]:
        """
        获取统计信息

        Returns:
            Dict: 统计数据
        """
        now = time.time()
        recent_calls = len([c for c in self.calls if now - c < 60])

        return {
            "name": self.name,
            "calls_per_minute_limit": self.calls_per_minute,
            "recent_calls_in_window": recent_calls,
            "total_calls": self.total_calls,
            "total_waits": self.total_waits,
            "total_wait_time": self.total_wait_time,
            "average_wait_time": (
                self.total_wait_time / self.total_waits
                if self.total_waits > 0 else 0
            )
        }

    def reset(self):
        """重置节流器和统计信息"""
        self.calls = []
        self.total_calls = 0
        self.total_waits = 0
        self.total_wait_time = 0.0
        self.logger.info(f"[{self.name}] 节流器已重置")


class MultiRateLimiter:
    """多API节流器管理器"""

    def __init__(self):
        """初始化多API节流器"""
        self.limiters: Dict[str, RateLimiter] = {}
        self.logger = logging.getLogger("MultiRateLimiter")

    def register(
        self,
        api_name: str,
        calls_per_minute: int
    ) -> RateLimiter:
        """
        注册API节流器

        Args:
            api_name: API名称
            calls_per_minute: 每分钟允许的最大调用次数

        Returns:
            RateLimiter: 节流器实例
        """
        if api_name in self.limiters:
            self.logger.warning(
                f"节流器 '{api_name}' 已存在，将覆盖"
            )

        limiter = RateLimiter(
            calls_per_minute=calls_per_minute,
            name=api_name
        )
        self.limiters[api_name] = limiter

        self.logger.info(
            f"注册节流器: {api_name} ({calls_per_minute}次/分钟)"
        )

        return limiter

    def get(self, api_name: str) -> Optional[RateLimiter]:
        """
        获取节流器

        Args:
            api_name: API名称

        Returns:
            RateLimiter: 节流器实例（如果不存在返回None）
        """
        return self.limiters.get(api_name)

    async def acquire(self, api_name: str) -> bool:
        """
        获取指定API的调用许可

        Args:
            api_name: API名称

        Returns:
            bool: 是否成功获取许可

        Raises:
            KeyError: API节流器不存在
        """
        if api_name not in self.limiters:
            raise KeyError(f"节流器 '{api_name}' 不存在，请先注册")

        return await self.limiters[api_name].acquire()

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        获取所有节流器的统计信息

        Returns:
            Dict: 所有节流器的统计数据
        """
        return {
            name: limiter.get_stats()
            for name, limiter in self.limiters.items()
        }

    def reset_all(self):
        """重置所有节流器"""
        for limiter in self.limiters.values():
            limiter.reset()

        self.logger.info("所有节流器已重置")


# ==================== 全局节流器管理器 ====================

# 默认全局实例
_global_limiter_manager: Optional[MultiRateLimiter] = None


def get_global_limiter_manager() -> MultiRateLimiter:
    """
    获取全局节流器管理器（单例模式）

    Returns:
        MultiRateLimiter: 全局节流器管理器
    """
    global _global_limiter_manager

    if _global_limiter_manager is None:
        _global_limiter_manager = MultiRateLimiter()

        # 注册默认API节流器
        _global_limiter_manager.register("tushare", 180)  # Tushare: 180次/分钟（保守值）
        _global_limiter_manager.register("zhipu_ai", 60)  # 智谱AI: 60次/分钟（默认）

    return _global_limiter_manager


def reset_global_limiter_manager():
    """重置全局节流器管理器（主要用于测试）"""
    global _global_limiter_manager
    _global_limiter_manager = None

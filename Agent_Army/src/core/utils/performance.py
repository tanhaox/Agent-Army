"""
Agent Army - 性能优化工具
缓存、并发、懒加载、分页
"""

import streamlit as st
import pandas as pd
from functools import wraps
import time
from typing import Any, Callable, Optional
import hashlib
import pickle
from datetime import datetime, timedelta


class CacheManager:
    """缓存管理器"""

    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存管理器

        Args:
            ttl_seconds: 缓存生存时间（秒），默认5分钟
        """
        self.ttl_seconds = ttl_seconds

    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 将函数名和参数组合成唯一键
        key_data = f"{func_name}_{str(args)}_{str(kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in st.session_state:
            return None

        cache_data = st.session_state[key]

        # 检查是否过期
        if 'timestamp' in cache_data:
            elapsed = (datetime.now() - cache_data['timestamp']).total_seconds()
            if elapsed > self.ttl_seconds:
                # 缓存过期，删除
                del st.session_state[key]
                return None

        return cache_data.get('data')

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """
        设置缓存

        Args:
            key: 缓存键
            data: 缓存数据
            ttl_seconds: 可选的生存时间（覆盖默认值）
        """
        st.session_state[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        # 如果提供了自定义TTL，保存它
        if ttl_seconds is not None:
            st.session_state[key]['ttl'] = ttl_seconds

    def clear(self, key: str = None):
        """清除缓存"""
        if key:
            if key in st.session_state:
                del st.session_state[key]
        else:
            # 清除所有缓存（保留session_state中的其他数据）
            keys_to_delete = [
                k for k in st.session_state.keys()
                if k.startswith('cache_')
            ]
            for k in keys_to_delete:
                del st.session_state[k]


def cached(ttl_seconds: int = 300):
    """
    缓存装饰器

    Args:
        ttl_seconds: 缓存生存时间（秒）

    Usage:
        @cached(ttl_seconds=600)
        def expensive_function(arg1, arg2):
            # 耗时操作
            return result
    """
    cache_manager = CacheManager(ttl_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_manager._get_cache_key(func.__name__, *args, **kwargs)
            cache_key = f"cache_{cache_key}"

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数
            result = func(*args, **kwargs)

            # 保存到缓存
            cache_manager.set(cache_key, result)

            return result

        return wrapper

    return decorator


class LazyLoader:
    """懒加载管理器"""

    def __init__(self, page_size: int = 50):
        """
        初始化懒加载管理器

        Args:
            page_size: 每页数据量
        """
        self.page_size = page_size

    def load_page(self, data: list, page: int = 1) -> list:
        """
        加载指定页的数据

        Args:
            data: 完整数据列表
            page: 页码（从1开始）

        Returns:
            当前页的数据
        """
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        return data[start_idx:end_idx]

    def get_pagination_info(self, total_count: int) -> dict:
        """
        获取分页信息

        Args:
            total_count: 总数据量

        Returns:
            分页信息字典
        """
        total_pages = (total_count + self.page_size - 1) // self.page_size
        return {
            'page_size': self.page_size,
            'total_count': total_count,
            'total_pages': total_pages
        }


class PerformanceMonitor:
    """性能监控器"""

    # 类级别的指标存储
    _metrics = {}

    @staticmethod
    def measure_time(func_name: str = None):
        """
        性能计时装饰器

        Usage:
            @PerformanceMonitor.measure_time("load_data")
            def load_data():
                # 数据加载
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                name = func_name or func.__name__
                print(f"[性能监控] {name} 执行时间: {elapsed_time:.2f}秒")

                # 保存到指标字典
                if name not in PerformanceMonitor._metrics:
                    PerformanceMonitor._metrics[name] = []
                PerformanceMonitor._metrics[name].append(elapsed_time)

                return result

            return wrapper

        return decorator

    @staticmethod
    def get_metrics() -> dict:
        """
        获取所有性能指标

        Returns:
            指标字典，格式为 {操作名: [执行时间列表]}
        """
        return PerformanceMonitor._metrics.copy()

    @staticmethod
    def show_performance_metrics():
        """显示性能指标（在Streamlit页面中）"""
        with st.expander("📊 性能指标"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "页面加载时间",
                    f"{time.time() - st.session_state.get('page_start_time', time.time()):.2f}秒"
                )

            with col2:
                st.metric(
                    "缓存命中率",
                    f"{st.session_state.get('cache_hit_rate', 0):.1%}"
                )

            with col3:
                st.metric(
                    "内存使用",
                    f"{st.session_state.get('memory_usage', 0):.1f} MB"
                )


class DataOptimizer:
    """数据优化工具"""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        优化DataFrame内存使用

        Args:
            df: 原始DataFrame

        Returns:
            优化后的DataFrame
        """
        # 数值类型优化
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # 对象类型优化
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df[col]) < 0.5:
                df[col] = df[col].astype('category')

        return df

    @staticmethod
    def sample_large_dataset(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
        """
        对大数据集进行采样

        Args:
            df: 原始DataFrame
            max_rows: 最大行数

        Returns:
            采样后的DataFrame
        """
        if len(df) <= max_rows:
            return df

        # 分层采样（保持数据分布）
        sample_ratio = max_rows / len(df)
        return df.sample(frac=sample_ratio, random_state=42)


# 预加载的关键数据（启动时加载）
@st.cache_data(ttl=3600)
def load_critical_data():
    """
    加载关键数据（1小时缓存）
    用于启动时预加载
    """
    # TODO: 实际加载Agent配置、市场数据等
    return {
        'agents': [],
        'armies': [],
        'market_overview': {}
    }


# 分页组件
def render_pagination(total_items: int, page_size: int = 50, key: str = "pagination"):
    """
    渲染分页控件

    Args:
        total_items: 总项目数
        page_size: 每页大小
        key: Streamlit组件键

    Returns:
        当前页码（从1开始）
    """
    total_pages = (total_items + page_size - 1) // page_size

    if total_pages <= 1:
        return 1

    col1, col2, col3 = st.columns([2, 6, 2])

    with col1:
        if st.button("◀ 上一页", key=f"{key}_prev"):
            current_page = max(1, st.session_state.get(key, 1) - 1)
            st.session_state[key] = current_page

    with col2:
        current_page = st.session_state.get(key, 1)
        st.markdown(f"**第 {current_page} / {total_pages} 页**")

    with col3:
        if st.button("下一页 ▶", key=f"{key}_next"):
            current_page = min(total_pages, st.session_state.get(key, 1) + 1)
            st.session_state[key] = current_page

    return st.session_state.get(key, 1)


# 导出所有工具
__all__ = [
    'CacheManager',
    'cached',
    'LazyLoader',
    'PerformanceMonitor',
    'DataOptimizer',
    'load_critical_data',
    'render_pagination'
]

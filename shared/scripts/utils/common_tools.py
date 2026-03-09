#!/usr/bin/env python3
"""
通用工具函数库
提供跨项目的可复用工具函数
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# ==================== 路径工具 ====================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前文件向上查找，直到找到包含 projects/ 的目录
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "projects").exists():
            return parent
    return current.parent.parent.parent


def get_relative_path(path: Path, base: Path = None) -> Path:
    """获取相对路径"""
    base = base or get_project_root()
    try:
        return path.relative_to(base)
    except ValueError:
        return path


# ==================== 文件工具 ====================

def read_file(
    path: Union[str, Path],
    encoding: str = 'utf-8',
    default: Any = None
) -> Optional[str]:
    """
    安全读取文件

    Args:
        path: 文件路径
        encoding: 文件编码
        default: 文件不存在时的默认值

    Returns:
        文件内容或默认值
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except FileNotFoundError:
        if default is not None:
            return default
        raise
    except Exception as e:
        logger.error(f"读取文件失败 {path}: {e}")
        if default is not None:
            return default
        raise


def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    backup: bool = False
) -> bool:
    """
    安全写入文件

    Args:
        path: 文件路径
        content: 文件内容
        encoding: 文件编码
        backup: 是否备份原文件

    Returns:
        是否成功
    """
    try:
        p = Path(path)
        ensure_dir(p.parent)

        # 备份原文件
        if backup and p.exists():
            backup_path = p.with_suffix(f"{p.suffix}.bak")
            p.rename(backup_path)
            logger.info(f"已备份原文件到: {backup_path}")

        p.write_text(content, encoding=encoding)
        return True

    except Exception as e:
        logger.error(f"写入文件失败 {path}: {e}")
        return False


def load_json(
    path: Union[str, Path],
    default: Any = None
) -> Optional[Dict]:
    """加载 JSON 文件"""
    try:
        content = read_file(path)
        if content:
            return json.loads(content)
        return default
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败 {path}: {e}")
        return default


def save_json(
    path: Union[str, Path],
    data: Dict,
    indent: int = 2,
    ensure_ascii: bool = False
) -> bool:
    """保存 JSON 文件"""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        return write_file(path, content)
    except Exception as e:
        logger.error(f"保存 JSON 失败 {path}: {e}")
        return False


# ==================== 字符串工具 ====================

def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def generate_hash(content: str, algorithm: str = "md5") -> str:
    """生成内容哈希"""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(content.encode('utf-8'))
    return hash_obj.hexdigest()


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ==================== 时间工具 ====================

def get_timestamp(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间戳"""
    return datetime.now().strftime(format)


def get_iso_timestamp() -> str:
    """获取 ISO 格式时间戳"""
    return datetime.now().isoformat()


def parse_timestamp(timestamp: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析时间戳"""
    return datetime.strptime(timestamp, format)


# ==================== 装饰器工具 ====================

def timing(func: Callable) -> Callable:
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"{func.__name__} 执行耗时: {format_duration(duration)}")
        return result
    return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff: 退避系数
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} 失败（尝试 {attempt + 1}/{max_attempts}）: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 失败，已达最大尝试次数")

            raise last_exception

        return wrapper
    return decorator


def memoize(max_size: int = 128) -> Callable:
    """
    缓存装饰器

    Args:
        max_size: 最大缓存条目数
    """
    cache = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache:
                return cache[key]

            result = func(*args, **kwargs)

            # 限制缓存大小
            if len(cache) >= max_size:
                # 删除最早的条目
                oldest_key = next(iter(cache))
                del cache[oldest_key]

            cache[key] = result
            return result

        # 添加清除缓存的方法
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {"size": len(cache), "max_size": max_size}

        return wrapper

    return decorator


# ==================== 验证工具 ====================

def validate_email(email: str) -> bool:
    """简单的邮箱验证"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """简单的 URL 验证"""
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def validate_required(data: Dict, fields: List[str]) -> tuple[bool, List[str]]:
    """
    验证必填字段

    Args:
        data: 数据字典
        fields: 必填字段列表

    Returns:
        (是否有效, 缺失字段列表)
    """
    missing = [field for field in fields if field not in data or data[field] is None]
    return len(missing) == 0, missing


# ==================== 转换工具 ====================

def to_snake_case(text: str) -> str:
    """转换为蛇形命名"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(text: str) -> str:
    """转换为驼峰命名"""
    parts = text.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def to_pascal_case(text: str) -> str:
    """转换为帕斯卡命名"""
    return ''.join(p.capitalize() for p in text.split('_'))


# ==================== 日志工具 ====================

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 记录器名称
        level: 日志级别
        log_file: 日志文件路径
        format_string: 日志格式

    Returns:
        配置好的记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    formatter = logging.Formatter(format_string)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        ensure_dir(log_file.parent)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ==================== 配置工具 ====================

def merge_dict(base: Dict, update: Dict) -> Dict:
    """深度合并字典"""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def get_env_value(
    key: str,
    default: Any = None,
    required: bool = False,
    cast_type: type = str
) -> Any:
    """
    获取环境变量值

    Args:
        key: 环境变量名
        default: 默认值
        required: 是否必需
        cast_type: 类型转换

    Returns:
        环境变量值
    """
    value = os.getenv(key)

    if value is None:
        if required and default is None:
            raise ValueError(f"必需的环境变量未设置: {key}")
        return default

    # 类型转换
    if cast_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif cast_type == int:
        return int(value)
    elif cast_type == float:
        return float(value)
    elif cast_type == list:
        return value.split(',')
    else:
        return cast_type(value)


# ==================== 进度工具 ====================

class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total: int, description: str = "处理中"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()

    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time

        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
        else:
            eta = 0

        logger.info(
            f"{self.description}: {self.current}/{self.total} "
            f"({percent:.1f}%) - "
            f"已用时: {format_duration(elapsed)}, "
            f"预计剩余: {format_duration(eta)}"
        )

    def complete(self):
        """完成"""
        elapsed = time.time() - self.start_time
        logger.info(
            f"{self.description} 完成! "
            f"总计: {self.current}, "
            f"耗时: {format_duration(elapsed)}"
        )


# ==================== 示例使用 ====================

if __name__ == "__main__":
    # 设置日志
    logger = setup_logger("utils", log_file=Path("logs/utils.log"))

    # 文件操作示例
    test_file = Path("tests/test_utils.txt")
    write_file(test_file, "Hello, World!", backup=True)
    content = read_file(test_file)
    logger.info(f"读取内容: {content}")

    # 字符串工具示例
    logger.info(f"截断: {truncate('This is a very long string', 10)}")
    logger.info(f"大小: {format_size(1024*1024*5)}")
    logger.info(f"时长: {format_duration(3665)}")

    # 进度跟踪示例
    tracker = ProgressTracker(100, "处理文件")
    for i in range(100):
        if i % 10 == 0:
            tracker.update(10)
    tracker.complete()

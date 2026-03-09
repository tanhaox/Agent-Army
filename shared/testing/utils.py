"""
测试工具函数

提供常用的测试辅助函数。
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager

# ==================== JSON 验证工具 ====================

def assert_valid_json(data: Any, msg: str = "数据不是有效的 JSON 格式"):
    """
    断言数据是有效的 JSON

    Args:
        data: 要验证的数据（字符串或字典）
        msg: 断言失败时的消息

    Raises:
        AssertionError: 如果数据不是有效的 JSON
    """
    try:
        if isinstance(data, str):
            json.loads(data)
        else:
            json.dumps(data)
    except (json.JSONDecodeError, TypeError) as e:
        raise AssertionError(f"{msg}: {e}")


def assert_json_schema(data: Dict[str, Any], schema: Dict[str, Any]):
    """
    断言 JSON 数据符合指定的 schema

    Args:
        data: 要验证的数据
        schema: Schema 定义

    示例:
        schema = {
            "name": str,
            "age": int,
            "email": (str, None),  # 可选
        }
        assert_json_schema(data, schema)
    """
    for key, expected_type in schema.items():
        assert key in data, f"缺少必需字段: {key}"

        value = data[key]

        # 检查可选类型
        if isinstance(expected_type, tuple):
            if None in expected_type and value is None:
                continue
            # 如果是元组但不是 (type, None) 形式，取第一个类型
            if None in expected_type:
                expected_type = expected_type[0]

        assert isinstance(value, expected_type), \
            f"字段 {key} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}"


# ==================== 日志验证工具 ====================

def assert_log_contains(log_file: Path, pattern: str, encoding: str = 'utf-8'):
    """
    断言日志文件包含匹配的内容

    Args:
        log_file: 日志文件路径
        pattern: 要匹配的模式（支持正则表达式）
        encoding: 文件编码

    Raises:
        AssertionError: 如果日志不包含匹配内容
    """
    assert log_file.exists(), f"日志文件不存在: {log_file}"

    content = log_file.read_text(encoding=encoding)

    if re.search(pattern, content):
        return

    raise AssertionError(f"日志文件中未找到匹配模式: {pattern}")


def assert_log_level_exists(log_file: Path, level: str, encoding: str = 'utf-8'):
    """
    断言日志文件包含指定级别的日志

    Args:
        log_file: 日志文件路径
        level: 日志级别 (INFO, DEBUG, ERROR, WARNING)
        encoding: 文件编码
    """
    pattern = rf"\[{level}\]"
    assert_log_contains(log_file, pattern, encoding)


def count_log_entries(log_file: Path, level: Optional[str] = None, encoding: str = 'utf-8') -> int:
    """
    统计日志条目数量

    Args:
        log_file: 日志文件路径
        level: 日志级别（如果指定，只统计该级别）
        encoding: 文件编码

    Returns:
        日志条目数量
    """
    assert log_file.exists(), f"日志文件不存在: {log_file}"

    content = log_file.read_text(encoding=encoding)
    lines = content.strip().split('\n')

    if level:
        pattern = rf"\[{level}\]"
        return sum(1 for line in lines if re.search(pattern, line))

    return len(lines)


# ==================== 文件系统工具 ====================

def assert_file_exists(file_path: Path, msg: Optional[str] = None):
    """
    断言文件存在

    Args:
        file_path: 文件路径
        msg: 自定义消息
    """
    if msg is None:
        msg = f"文件不存在: {file_path}"

    assert file_path.exists(), msg
    assert file_path.is_file(), f"路径不是文件: {file_path}"


def assert_dir_exists(dir_path: Path, msg: Optional[str] = None):
    """
    断言目录存在

    Args:
        dir_path: 目录路径
        msg: 自定义消息
    """
    if msg is None:
        msg = f"目录不存在: {dir_path}"

    assert dir_path.exists(), msg
    assert dir_path.is_dir(), f"路径不是目录: {dir_path}"


def create_temp_file(content: str = "", suffix: str = ".tmp", prefix: str = "test_"):
    """
    创建临时文件

    Args:
        content: 文件内容
        suffix: 文件后缀
        prefix: 文件前缀

    Returns:
        临时文件路径对象
    """
    import tempfile

    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=True)

    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)

    return Path(path)


def create_temp_dir(suffix: str = "", prefix: str = "test_dir_"):
    """
    创建临时目录

    Args:
        suffix: 目录名后缀
        prefix: 目录名前缀

    Returns:
        临时目录路径对象
    """
    import tempfile

    return Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix))


# ==================== 配置模拟工具 ====================

@contextmanager
def mock_config(config_dict: Dict[str, Any]):
    """
    模拟配置上下文管理器

    Args:
        config_dict: 配置字典

    示例:
        with mock_config({"api_key": "test_key"}):
            # 测试代码
            pass
    """
    import os

    old_env = {}

    # 设置环境变量
    for key, value in config_dict.items():
        env_key = f"TEST_{key.upper()}"
        old_env[env_key] = os.environ.get(env_key)
        os.environ[env_key] = str(value)

    try:
        yield config_dict
    finally:
        # 恢复原始环境变量
        for key in config_dict.keys():
            env_key = f"TEST_{key.upper()}"
            if env_key in old_env:
                if old_env[env_key] is None:
                    os.environ.pop(env_key, None)
                else:
                    os.environ[env_key] = old_env[env_key]


# ==================== 性能测试工具 ====================

def measure_execution_time(func: Callable, *args, **kwargs) -> tuple[Any, float]:
    """
    测量函数执行时间

    Args:
        func: 要测量的函数
        *args: 函数位置参数
        **kwargs: 函数关键字参数

    Returns:
        (函数返回值, 执行时间秒数)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    execution_time = end_time - start_time
    return result, execution_time


def assert_execution_time(func: Callable, max_time: float, *args, **kwargs):
    """
    断言函数执行时间不超过指定值

    Args:
        func: 要测试的函数
        max_time: 最大允许时间（秒）
        *args: 函数位置参数
        **kwargs: 函数关键字参数

    Raises:
        AssertionError: 如果执行时间超过 max_time
    """
    _, execution_time = measure_execution_time(func, *args, **kwargs)

    assert execution_time <= max_time, \
        f"执行时间 {execution_time:.2f}s 超过最大允许时间 {max_time:.2f}s"


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.1,
    error_msg: str = "条件未在超时时间内满足"
):
    """
    等待条件满足

    Args:
        condition: 条件函数（返回 bool）
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
        error_msg: 超时错误消息

    Raises:
        AssertionError: 如果超时后条件仍未满足
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return
        time.sleep(interval)

    raise AssertionError(error_msg)


# ==================== 网络模拟工具 ====================

@contextmanager
def mock_network_delay(delay: float = 1.0):
    """
    模拟网络延迟

    注意：这是用于测试的简单延迟，不是真正的网络模拟

    Args:
        delay: 延迟秒数
    """
    def delayed_request(*args, **kwargs):
        time.sleep(delay)
        return args[0](*args[1:], **kwargs) if args else None

    yield delayed_request


# ==================== 数据验证工具 ====================

def assert_valid_email(email: str):
    """
    断言有效的电子邮件地址

    Args:
        email: 电子邮件地址
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert re.match(pattern, email), f"无效的电子邮件地址: {email}"


def assert_valid_url(url: str):
    """
    断言有效的 URL

    Args:
        url: URL 字符串
    """
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    assert re.match(pattern, url), f"无效的 URL: {url}"


def assert_valid_port(port: int):
    """
    断言有效的端口号

    Args:
        port: 端口号
    """
    assert 0 <= port <= 65535, f"无效的端口号: {port}"

"""
常用测试夹具

提供各种可复用的测试夹具函数。
"""

import json
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch


# ==================== API 模拟夹具 ====================

@contextmanager
def mock_api_response(response_data: Any, status_code: int = 200):
    """
    模拟 API 响应

    Args:
        response_data: 响应数据
        status_code: HTTP 状态码

    示例:
        with mock_api_response({"data": "test"}):
            result = api_client.get("/endpoint")
    """
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = response_data
    mock_response.text = json.dumps(response_data)

    with patch('requests.request', return_value=mock_response):
        yield mock_response


# ==================== 文件系统模拟夹具 ====================

@contextmanager
def mock_file_system(file_structure: Dict[str, Any]):
    """
    模拟文件系统结构

    Args:
        file_structure: 文件结构字典
            {
                "file1.txt": "content",
                "dir1": {
                    "file2.txt": "content2"
                }
            }

    示例:
        with mock_file_system({"test.txt": "hello"}):
            # 测试代码
            pass
    """
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp(prefix="mock_fs_"))

    def create_structure(base_path: Path, structure: Dict[str, Any]):
        """递归创建文件结构"""
        for name, content in structure.items():
            path = base_path / name

            if isinstance(content, dict):
                # 目录
                path.mkdir(parents=True, exist_ok=True)
                create_structure(path, content)
            elif isinstance(content, str):
                # 文件
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
            else:
                raise ValueError(f"不支持的内容类型: {type(content)}")

    try:
        create_structure(temp_dir, file_structure)
        yield temp_dir
    finally:
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# ==================== 日志模拟夹具 ====================

@contextmanager
def mock_logger(name: str = "test", level: int = logging.DEBUG):
    """
    模拟日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        (logger, log_records) 元组
    """
    import logging
    from io import StringIO

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 创建字符串 handler 来捕获日志
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    try:
        yield logger, log_stream
    finally:
        logger.removeHandler(handler)
        handler.close()


# ==================== 配置文件夹具 ====================

@contextmanager
def temp_config_file(config_dict: Dict[str, Any], file_type: str = "json"):
    """
    创建临时配置文件

    Args:
        config_dict: 配置字典
        file_type: 文件类型 (json, yaml, env)

    示例:
        with temp_config_file({"key": "value"}, "json") as config_file:
            # 使用配置文件
            pass
    """
    import tempfile
    import yaml

    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(suffix=f".{file_type}", prefix="config_")
    temp_file = Path(temp_path)

    try:
        # 根据类型写入内容
        if file_type == "json":
            temp_file.write_text(json.dumps(config_dict, indent=2, ensure_ascii=False), encoding='utf-8')
        elif file_type == "yaml":
            with open(temp_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True)
        elif file_type == "env":
            lines = [f"{k}={v}" for k, v in config_dict.items()]
            temp_file.write_text("\n".join(lines), encoding='utf-8')
        else:
            raise ValueError(f"不支持的配置文件类型: {file_type}")

        yield temp_file

    finally:
        # 清理
        import os
        os.close(fd)
        if temp_file.exists():
            temp_file.unlink()


# ==================== 数据库模拟夹具 ====================

@contextmanager
def mock_database_connection(data: Dict[str, Any]):
    """
    模拟数据库连接

    Args:
        data: 模拟的数据

    示例:
        with mock_database_connection({"users": []}) as db:
            users = db.query("SELECT * FROM users")
    """
    mock_db = Mock()

    # 模拟查询方法
    def mock_query(query: str, params: Optional[tuple] = None):
        # 简单的查询模拟
        table = query.split("FROM")[1].split()[0] if "FROM" in query else None
        if table and table in data:
            return data[table]
        return []

    mock_db.query = mock_query
    mock_db.execute = Mock(return_value=True)
    mock_db.commit = Mock(return_value=True)
    mock_db.close = Mock(return_value=True)

    yield mock_db


# ==================== 环境变量模拟夹具 ====================

@contextmanager
def mock_environment_vars(env_vars: Dict[str, str]):
    """
    模拟环境变量

    Args:
        env_vars: 环境变量字典

    示例:
        with mock_environment_vars({"API_KEY": "test_key"}):
            # 测试代码
            pass
    """
    import os

    # 保存原始环境变量
    old_values = {}

    # 设置新的环境变量
    for key, value in env_vars.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        # 恢复原始环境变量
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


# ==================== 时间模拟夹具 ====================

@contextmanager
def mock_time(mock_timestamp: float):
    """
    模拟时间

    Args:
        mock_timestamp: 模拟的时间戳

    示例:
        with mock_time(1000000000.0):
            # time.time() 将返回模拟值
            pass
    """
    with patch('time.time', return_value=mock_timestamp):
        yield


# ==================== 输入模拟夹具 ====================

@contextmanager
def mock_user_input(inputs: list):
    """
    模拟用户输入

    Args:
        inputs: 输入值列表

    示例:
        with mock_user_input(["yes", "John"]):
            # 第一次 input() 返回 "yes"
            # 第二次 input() 返回 "John"
            pass
    """
    with patch('builtins.input', side_effect=inputs):
        yield

"""
AI-Agent-Local 测试框架

提供标准化的测试基类、工具函数和测试夹具。
"""

from .test_base import BaseTestCase, BaseSkillTestCase, BaseAppTestCase, BaseToolTestCase
from .utils import (
    assert_valid_json,
    assert_log_contains,
    assert_file_exists,
    mock_config,
    create_temp_file,
    wait_for_condition
)

__version__ = "1.0.0"
__all__ = [
    "BaseTestCase",
    "BaseSkillTestCase",
    "BaseAppTestCase",
    "BaseToolTestCase",
    "assert_valid_json",
    "assert_log_contains",
    "assert_file_exists",
    "mock_config",
    "create_temp_file",
    "wait_for_condition",
]

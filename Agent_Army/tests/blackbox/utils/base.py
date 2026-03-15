"""
Agent Army - 黑盒测试基类
提供通用的测试工具和断言方法
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import logging
import json
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class BlackBoxTestCase:
    """黑盒测试基类"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化测试用例

        Args:
            name: 测试用例名称
            description: 测试用例描述
        """
        self.name = name
        self.description = description
        self.results = {
            'test_name': name,
            'description': description,
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    def log_step(self, step: str, status: str = "INFO"):
        """
        记录测试步骤

        Args:
            step: 步骤描述
            status: 状态（INFO/PASS/FAIL）
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'time': timestamp,
            'step': step,
            'status': status
        }
        self.results['steps'].append(log_entry)

        # 输出到控制台
        icon = {
            'INFO': '📋',
            'PASS': '✅',
            'FAIL': '❌'
        }.get(status, '📋')

        logger.info(f"{icon} {step}")

    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """
        断言相等

        Args:
            actual: 实际值
            expected: 期望值
            message: 断言消息
        """
        if actual == expected:
            self.results['passed'] += 1
            msg = message or f"断言通过: {actual} == {expected}"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or f"断言失败: 期望 {expected}, 实际 {actual}"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'AssertionError',
                'message': error_msg,
                'expected': expected,
                'actual': actual
            })

    def assert_true(self, condition: bool, message: str = ""):
        """
        断言为真

        Args:
            condition: 条件
            message: 断言消息
        """
        if condition:
            self.results['passed'] += 1
            msg = message or "断言通过: 条件为真"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or "断言失败: 条件为假"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'AssertionError',
                'message': error_msg,
                'condition': condition
            })

    def assert_not_none(self, value: Any, message: str = ""):
        """
        断言非空

        Args:
            value: 值
            message: 断言消息
        """
        if value is not None:
            self.results['passed'] += 1
            msg = message or f"断言通过: 值非空"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or "断言失败: 值为 None"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'AssertionError',
                'message': error_msg,
                'value': value
            })

    def assert_in(self, item: Any, container: Any, message: str = ""):
        """
        断言包含

        Args:
            item: 项目
            container: 容器
            message: 断言消息
        """
        if item in container:
            self.results['passed'] += 1
            msg = message or f"断言通过: {item} 在容器中"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or f"断言失败: {item} 不在容器中"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'AssertionError',
                'message': error_msg,
                'item': item,
                'container': str(container)[:100]
            })

    def assert_greater(self, value: int, threshold: int, message: str = ""):
        """
        断言大于

        Args:
            value: 值
            threshold: 阈值
            message: 断言消息
        """
        if value > threshold:
            self.results['passed'] += 1
            msg = message or f"断言通过: {value} > {threshold}"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or f"断言失败: {value} 不大于 {threshold}"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'AssertionError',
                'message': error_msg,
                'value': value,
                'threshold': threshold
            })

    def finish(self) -> Dict:
        """
        完成测试，返回结果

        Returns:
            测试结果字典
        """
        self.results['end_time'] = datetime.now().isoformat()
        self.results['success'] = self.results['failed'] == 0

        # 输出总结
        total = self.results['passed'] + self.results['failed']
        icon = "✅" if self.results['success'] else "❌"
        logger.info(f"{icon} 测试完成: {self.results['passed']}/{total} 通过")

        return self.results


class APITestCase(BlackBoxTestCase):
    """API 测试用例基类"""

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self.base_url = "http://localhost:5000"  # 默认基础 URL
        self.session = None

    def assert_response_status(self, response: Any, expected_status: int, message: str = ""):
        """
        断言响应状态码

        Args:
            response: 响应对象
            expected_status: 期望状态码
            message: 断言消息
        """
        actual_status = getattr(response, 'status_code', None)
        if actual_status == expected_status:
            self.results['passed'] += 1
            msg = message or f"断言通过: 状态码 {actual_status}"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or f"断言失败: 期望状态码 {expected_status}, 实际 {actual_status}"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'StatusCodeError',
                'message': error_msg,
                'expected': expected_status,
                'actual': actual_status
            })

    def assert_response_contains(self, response: Any, key: str, message: str = ""):
        """
        断言响应包含指定字段

        Args:
            response: 响应对象
            key: 字段名
            message: 断言消息
        """
        try:
            data = response.json() if hasattr(response, 'json') else response
            if key in data:
                self.results['passed'] += 1
                msg = message or f"断言通过: 响应包含字段 {key}"
                self.log_step(msg, "PASS")
            else:
                self.results['failed'] += 1
                error_msg = message or f"断言失败: 响应不包含字段 {key}"
                self.log_step(error_msg, "FAIL")
                self.results['errors'].append({
                    'type': 'FieldMissingError',
                    'message': error_msg,
                    'key': key,
                    'response_keys': list(data.keys())
                })
        except Exception as e:
            self.results['failed'] += 1
            error_msg = f"解析响应失败: {str(e)}"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'ParseError',
                'message': error_msg,
                'exception': str(e)
            })


class WorkflowTestCase(BlackBoxTestCase):
    """工作流测试用例基类"""

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self.context = {}  # 存储测试上下文数据

    def set_context(self, key: str, value: Any):
        """设置上下文数据"""
        self.context[key] = value
        self.log_step(f"设置上下文: {key} = {value}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.context.get(key, default)

    def assert_step_success(self, step_name: str, result: Any, message: str = ""):
        """
        断言工作流步骤成功

        Args:
            step_name: 步骤名称
            result: 步骤结果
            message: 断言消息
        """
        # 检查结果是否表示成功（根据实际项目调整）
        success = True

        # 如果是字典，检查 success/status/error 等字段
        if isinstance(result, dict):
            success = (
                result.get('success', True) and
                not result.get('error', None) and
                result.get('status', 'success') != 'failed'
            )

        if success:
            self.results['passed'] += 1
            msg = message or f"步骤成功: {step_name}"
            self.log_step(msg, "PASS")
        else:
            self.results['failed'] += 1
            error_msg = message or f"步骤失败: {step_name}"
            self.log_step(error_msg, "FAIL")
            self.results['errors'].append({
                'type': 'StepFailedError',
                'message': error_msg,
                'step': step_name,
                'result': str(result)[:200]
            })

"""
权限矩阵模块 - 调用权限管理

版本: 2.0 (8部门制)
方案: Plan B - 自己实现，不依赖OpenClaw
"""

import json
from typing import List, Optional, Dict
from functools import wraps


# 默认权限矩阵（从配置文件加载）
PERMISSION_MATRIX = {
    'investor': {
        'can_call': ['commander'],
        'description': '投资者只能调用总司令'
    },
    'commander': {
        'can_call': [
            'research_department',
            'analysis_department',
            'prediction_department',
            'strategy_department',
            'validation_department',
            'monitoring_department',
            'optimization_department',
            'configuration_department'
        ],
        'description': '总司令可以调用任何部门'
    },
    'research_department': {
        'can_call': ['commander', 'research_department'],
        'description': '研究部可以回调总司令和内部调用'
    },
    'analysis_department': {
        'can_call': ['commander', 'analysis_department'],
        'description': '分析部可以回调总司令和内部调用'
    },
    'prediction_department': {
        'can_call': ['commander', 'prediction_department'],
        'description': '预测部可以回调总司令和内部调用'
    },
    'strategy_department': {
        'can_call': ['commander', 'strategy_department'],
        'description': '策略部可以回调总司令和内部调用'
    },
    'validation_department': {
        'can_call': ['commander', 'validation_department'],
        'description': '验证部可以回调总司令和内部调用'
    },
    'monitoring_department': {
        'can_call': ['commander', 'monitoring_department'],
        'description': '监控部可以回调总司令和内部调用'
    },
    'optimization_department': {
        'can_call': ['commander', 'optimization_department'],
        'description': '优化部可以回调总司令和内部调用'
    },
    'configuration_department': {
        'can_call': ['commander', 'configuration_department'],
        'description': '配置部可以回调总司令和内部调用'
    }
}


class PermissionError(Exception):
    """权限错误异常"""
    pass


class PermissionChecker:
    """
    权限检查器

    检查调用者是否有权限调用被调用者。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化权限检查器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.matrix = PERMISSION_MATRIX

        # 如果提供了配置文件，加载配置
        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, path: str) -> None:
        """
        从配置文件加载权限矩阵

        Args:
            path: 配置文件路径
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.matrix = config.get('permission_matrix', PERMISSION_MATRIX)
        except Exception as e:
            # 加载失败，使用默认配置
            print(f"Warning: Failed to load permission matrix from {path}: {e}")

    def can_call(self, caller: str, callee: str) -> bool:
        """
        检查caller是否可以调用callee

        Args:
            caller: 调用者（如 'commander', 'research_department'）
            callee: 被调用者

        Returns:
            True 如果允许调用，False 如果禁止
        """
        # 获取caller的权限列表
        caller_permissions = self.matrix.get(caller)
        if not caller_permissions:
            # 调用者不存在，拒绝访问
            return False

        # 检查callee是否在允许列表中
        allowed_calls = caller_permissions['can_call']
        return callee in allowed_calls

    def check_call(self, caller: str, callee: str) -> bool:
        """
        检查调用权限，如果不允许则抛出异常

        Args:
            caller: 调用者
            callee: 被调用者

        Returns:
            True 如果允许

        Raises:
            PermissionError: 如果不允许调用
        """
        if not self.can_call(caller, callee):
            raise PermissionError(
                f"权限拒绝: {caller} 不能调用 {callee}"
            )

        return True

    def get_permissions(self, caller: str) -> List[str]:
        """
        获取caller的权限列表

        Args:
            caller: 调用者

        Returns:
            允许调用的对象列表
        """
        caller_permissions = self.matrix.get(caller)
        if not caller_permissions:
            return []

        return caller_permissions['can_call']

    def get_all_callers(self) -> List[str]:
        """
        获取所有调用者列表

        Returns:
            所有调用者列表
        """
        return list(self.matrix.keys())

    def validate_matrix(self) -> bool:
        """
        验证权限矩阵的完整性

        Returns:
            True 如果权限矩阵有效
        """
        # 检查每个调用者的权限列表
        for caller, permissions in self.matrix.items():
            if 'can_call' not in permissions:
                print(f"Warning: {caller} missing 'can_call' field")
                return False

            if not isinstance(permissions['can_call'], list):
                print(f"Warning: {caller} 'can_call' is not a list")
                return False

        return True


def require_permission(callee: str):
    """
    权限检查装饰器

    使用示例：
    @require_permission('research_department')
    async def call_research_department(self):
        # 只有有权限的调用者才能执行
        pass

    Args:
        callee: 被调用者

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 获取调用者（假设self有name属性）
            caller = getattr(self, 'name', None)
            if not caller:
                raise PermissionError("无法确定调用者身份")

            # 检查权限
            checker = PermissionChecker()
            if not checker.can_call(caller, callee):
                raise PermissionError(
                    f"权限拒绝: {caller} 不能调用 {callee}"
                )

            # 执行函数
            return await func(self, *args, **kwargs)

        return wrapper
    return decorator


class PermissionManager:
    """
    权限管理器

    管理权限矩阵的加载、保存和更新。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化权限管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.matrix = PERMISSION_MATRIX
        self.checker = PermissionChecker()

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, path: str) -> None:
        """
        从配置文件加载权限

        Args:
            path: 配置文件路径
        """
        self.checker.load_from_file(path)
        self.matrix = self.checker.matrix

    def save_to_file(self, path: Optional[str] = None) -> None:
        """
        保存权限到配置文件

        Args:
            path: 配置文件路径（可选，默认使用初始化时的路径）
        """
        path = path or self.config_path
        if not path:
            raise ValueError("No config path specified")

        config = {
            'version': '2.0',
            'permission_matrix': self.matrix
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def add_permission(self, caller: str, callee: str) -> None:
        """
        添加权限

        Args:
            caller: 调用者
            callee: 被调用者
        """
        if caller not in self.matrix:
            self.matrix[caller] = {
                'can_call': [],
                'description': ''
            }

        if callee not in self.matrix[caller]['can_call']:
            self.matrix[caller]['can_call'].append(callee)

    def remove_permission(self, caller: str, callee: str) -> None:
        """
        移除权限

        Args:
            caller: 调用者
            callee: 被调用者
        """
        if caller in self.matrix:
            if callee in self.matrix[caller]['can_call']:
                self.matrix[caller]['can_call'].remove(callee)

    def get_permission_matrix(self) -> Dict:
        """
        获取完整权限矩阵

        Returns:
            权限矩阵字典
        """
        return self.matrix

"""
权限矩阵单元测试

测试PermissionChecker类和相关功能。
"""

import pytest
import asyncio
from src.core.permission_matrix import (
    PermissionChecker,
    PermissionError,
    PermissionManager,
    require_permission
)


class TestPermissionChecker:
    """测试PermissionChecker类"""

    def test_init(self):
        """测试初始化"""
        checker = PermissionChecker()
        assert checker.matrix is not None

    def test_commander_can_call_any_department(self):
        """测试总司令可以调用任何部门"""
        checker = PermissionChecker()

        departments = [
            'research_department',
            'analysis_department',
            'prediction_department',
            'strategy_department',
            'validation_department',
            'monitoring_department',
            'optimization_department',
            'configuration_department'
        ]

        for dept in departments:
            assert checker.can_call('commander', dept), \
                f"总司令应该可以调用{dept}"

    def test_department_cannot_call_other_department(self):
        """测试部门不能互相调用"""
        checker = PermissionChecker()

        # 研究部不能调用分析部
        assert not checker.can_call('research_department', 'analysis_department')

        # 分析部不能调用预测部
        assert not checker.can_call('analysis_department', 'prediction_department')

        # 预测部不能调用策略部
        assert not checker.can_call('prediction_department', 'strategy_department')

    def test_department_can_callback_commander(self):
        """测试部门可以回调总司令"""
        checker = PermissionChecker()

        # 所有部门都可以回调总司令
        departments = [
            'research_department',
            'analysis_department',
            'prediction_department',
            'strategy_department',
            'validation_department',
            'monitoring_department',
            'optimization_department',
            'configuration_department'
        ]

        for dept in departments:
            assert checker.can_call(dept, 'commander'), \
                f"{dept}应该可以回调总司令"

    def test_investor_can_only_call_commander(self):
        """测试投资者只能调用总司令"""
        checker = PermissionChecker()

        # 投资者可以调用总司令
        assert checker.can_call('investor', 'commander')

        # 投资者不能调用其他部门
        assert not checker.can_call('investor', 'research_department')
        assert not checker.can_call('investor', 'analysis_department')
        assert not checker.can_call('investor', 'prediction_department')

    def test_department_internal_calls(self):
        """测试部门内部调用"""
        checker = PermissionChecker()

        # 研究部可以内部调用
        assert checker.can_call('research_department', 'research_department')

        # 分析部可以内部调用
        assert checker.can_call('analysis_department', 'analysis_department')

    def test_check_call_success(self):
        """测试权限检查成功"""
        checker = PermissionChecker()

        # 总司令调用研究部（应该成功）
        result = checker.check_call('commander', 'research_department')
        assert result is True

    def test_check_call_failure(self):
        """测试权限检查失败"""
        checker = PermissionChecker()

        # 研究部调用分析部（应该失败）
        with pytest.raises(PermissionError, match="权限拒绝"):
            checker.check_call('research_department', 'analysis_department')

    def test_get_permissions(self):
        """测试获取权限列表"""
        checker = PermissionChecker()

        # 获取总司令的权限
        permissions = checker.get_permissions('commander')
        assert len(permissions) == 8
        assert 'research_department' in permissions

        # 获取投资者的权限
        permissions = checker.get_permissions('investor')
        assert len(permissions) == 1
        assert 'commander' in permissions

    def test_get_all_callers(self):
        """测试获取所有调用者"""
        checker = PermissionChecker()

        callers = checker.get_all_callers()
        assert 'commander' in callers
        assert 'investor' in callers
        assert 'research_department' in callers

    def test_validate_matrix(self):
        """测试权限矩阵验证"""
        checker = PermissionChecker()

        # 默认矩阵应该是有效的
        assert checker.validate_matrix() is True

    def test_unknown_caller(self):
        """测试未知调用者"""
        checker = PermissionChecker()

        # 未知调用者不能调用任何人
        assert not checker.can_call('unknown_agent', 'commander')

    def test_unknown_callee(self):
        """测试未知被调用者"""
        checker = PermissionChecker()

        # 总司令不能调用未知的部门
        assert not checker.can_call('commander', 'unknown_department')


class TestPermissionManager:
    """测试PermissionManager类"""

    def test_init(self):
        """测试初始化"""
        manager = PermissionManager()
        assert manager.matrix is not None
        assert manager.checker is not None

    def test_get_permission_matrix(self):
        """测试获取权限矩阵"""
        manager = PermissionManager()

        matrix = manager.get_permission_matrix()
        assert isinstance(matrix, dict)
        assert 'commander' in matrix

    def test_add_permission(self):
        """测试添加权限"""
        manager = PermissionManager()

        # 添加新权限
        manager.add_permission('test_caller', 'test_callee')

        # 验证权限已添加
        assert manager.checker.can_call('test_caller', 'test_callee')

    def test_remove_permission(self):
        """测试移除权限"""
        manager = PermissionManager()

        # 先添加权限
        manager.add_permission('test_caller', 'test_callee')
        assert manager.checker.can_call('test_caller', 'test_callee')

        # 移除权限
        manager.remove_permission('test_caller', 'test_callee')
        assert not manager.checker.can_call('test_caller', 'test_callee')


class TestRequirePermissionDecorator:
    """测试权限检查装饰器"""

    @pytest.mark.asyncio
    async def test_decorator_with_permission(self):
        """测试有权限时的装饰器"""
        checker = PermissionChecker()

        class TestAgent:
            def __init__(self):
                self.name = 'commander'

            @require_permission('research_department')
            async def call_research(self):
                return "success"

        agent = TestAgent()
        result = await agent.call_research()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_without_permission(self):
        """测试无权限时的装饰器"""
        class TestAgent:
            def __init__(self):
                self.name = 'research_department'

            @require_permission('analysis_department')
            async def call_analysis(self):
                return "success"

        agent = TestAgent()

        with pytest.raises(PermissionError, match="权限拒绝"):
            await agent.call_analysis()

    @pytest.mark.asyncio
    async def test_decorator_unknown_caller(self):
        """测试未知调用者的装饰器"""
        class TestAgent:
            def __init__(self):
                # 没有name属性
                pass

            @require_permission('research_department')
            async def call_research(self):
                return "success"

        agent = TestAgent()

        with pytest.raises(PermissionError, match="无法确定调用者身份"):
            await agent.call_research()


class TestPermissionScenarios:
    """测试真实场景"""

    def test_full_permission_matrix(self):
        """测试完整权限矩阵"""
        checker = PermissionChecker()

        # 定义所有应该存在的调用关系
        expected_permissions = {
            'investor': ['commander'],
            'commander': [
                'research_department',
                'analysis_department',
                'prediction_department',
                'strategy_department',
                'validation_department',
                'monitoring_department',
                'optimization_department',
                'configuration_department'
            ],
            'research_department': ['commander', 'research_department'],
            'analysis_department': ['commander', 'analysis_department'],
            'prediction_department': ['commander', 'prediction_department'],
            'strategy_department': ['commander', 'strategy_department'],
            'validation_department': ['commander', 'validation_department'],
            'monitoring_department': ['commander', 'monitoring_department'],
            'optimization_department': ['commander', 'optimization_department'],
            'configuration_department': ['commander', 'configuration_department']
        }

        # 验证每个调用者的权限
        for caller, expected_callees in expected_permissions.items():
            actual_permissions = checker.get_permissions(caller)
            assert set(actual_permissions) == set(expected_callees), \
                f"{caller}的权限不匹配"

    def test_circular_permission_check(self):
        """测试循环权限检查"""
        checker = PermissionChecker()

        # 总司令可以调用研究部
        assert checker.can_call('commander', 'research_department')

        # 研究部可以回调总司令
        assert checker.can_call('research_department', 'commander')

        # 但研究部不能调用其他部门
        assert not checker.can_call('research_department', 'analysis_department')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

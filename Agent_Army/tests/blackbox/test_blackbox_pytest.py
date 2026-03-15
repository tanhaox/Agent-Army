"""
Agent Army - 黑盒测试 Pytest 包装器
将自定义黑盒测试类转换为 pytest 兼容格式
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 抑制Streamlit警告
import logging
for logger_name in ['streamlit.runtime.caching', 'streamlit.runtime.scriptrunner_utils', 'streamlit.runtime.state']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False


class TestAgentManagement:
    """Agent 管理测试套件"""

    def test_agent_manager(self):
        """测试 Agent 管理器"""
        from tests.blackbox.workflow.test_agents import AgentManagerTest
        test = AgentManagerTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_agent_initialization(self):
        """测试 Agent 初始化"""
        from tests.blackbox.workflow.test_agents import AgentInitializationTest
        test = AgentInitializationTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_agent_count(self):
        """测试 Agent 数量"""
        from tests.blackbox.workflow.test_agents import AgentCountTest
        test = AgentCountTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"


class TestConfigSystem:
    """配置系统测试套件"""

    def test_config_system(self):
        """测试配置系统"""
        from tests.blackbox.workflow.test_config import ConfigSystemTest
        test = ConfigSystemTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_design_tokens(self):
        """测试 Design Tokens"""
        from tests.blackbox.workflow.test_config import DesignTokensTest
        test = DesignTokensTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_environment_config(self):
        """测试环境配置"""
        from tests.blackbox.workflow.test_config import EnvironmentConfigTest
        test = EnvironmentConfigTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"


class TestVisualizationTools:
    """可视化工具测试套件"""

    def test_visualization_tools(self):
        """测试可视化工具"""
        from tests.blackbox.workflow.test_tools import VisualizationToolsTest
        test = VisualizationToolsTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_export_tools(self):
        """测试导出工具"""
        from tests.blackbox.workflow.test_tools import ExportToolsTest
        test = ExportToolsTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

    def test_performance_tools(self):
        """测试性能工具"""
        from tests.blackbox.workflow.test_tools import PerformanceToolsTest
        test = PerformanceToolsTest()
        test.run()
        result = test.finish()
        assert result['success'], f"测试失败: {result.get('errors', [])}"

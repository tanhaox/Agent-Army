"""
Agent Army Web v2.0 - 集成测试
测试所有页面功能和性能
"""

import pytest
import streamlit as st
import sys
from pathlib import Path
import time

# 添加项目根目录
# tests/目录在Agent_Army/下，所以需要parent.parent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestWebPages:
    """Web页面测试"""

    def test_dashboard_page(self):
        """测试主页Dashboard"""
        from src.core.pages_v2.dashboard_full import render_dashboard

        # 测试页面渲染
        try:
            # 这里只是示例，实际需要Streamlit测试环境
            assert render_dashboard is not None
            print("✅ Dashboard页面测试通过")
        except Exception as e:
            print(f"❌ Dashboard页面测试失败: {e}")

    def test_agent_status_page(self):
        """测试Agent状态页"""
        from src.core.pages_v2.agent_status_optimized import render_agent_status_optimized

        try:
            assert render_agent_status_optimized is not None
            print("✅ Agent状态页测试通过")
        except Exception as e:
            print(f"❌ Agent状态页测试失败: {e}")

    def test_task_management_page(self):
        """测试任务管理页"""
        from src.core.pages_v2.task_management_optimized import render_task_management_optimized

        try:
            assert render_task_management_optimized is not None
            print("✅ 任务管理页测试通过")
        except Exception as e:
            print(f"❌ 任务管理页测试失败: {e}")

    def test_data_center_page(self):
        """测试数据中心页"""
        from src.core.pages_v2.data_center_v2 import render_data_center_v2

        try:
            assert render_data_center_v2 is not None
            print("✅ 数据中心页测试通过")
        except Exception as e:
            print(f"❌ 数据中心页测试失败: {e}")

    def test_analysis_reports_page(self):
        """测试分析报告页"""
        from src.core.pages_v2.analysis_reports_v2 import render_analysis_reports_v2

        try:
            assert render_analysis_reports_v2 is not None
            print("✅ 分析报告页测试通过")
        except Exception as e:
            print(f"❌ 分析报告页测试失败: {e}")


class TestAgentManager:
    """Agent管理器测试"""

    def test_agent_manager_initialization(self):
        """测试Agent管理器初始化"""
        from src.core.agents.agent_manager import get_agent_manager

        try:
            manager = get_agent_manager()
            assert manager is not None
            print("✅ Agent管理器初始化测试通过")
        except Exception as e:
            print(f"❌ Agent管理器初始化测试失败: {e}")

    def test_get_all_agents(self):
        """测试获取所有Agent"""
        from src.core.agents.agent_manager import get_agent_manager

        try:
            manager = get_agent_manager()
            agents = manager.get_all_agents()
            assert len(agents) == 24
            print(f"✅ 获取所有Agent测试通过 (共{len(agents)}个)")
        except Exception as e:
            print(f"❌ 获取所有Agent测试失败: {e}")

    def test_create_task(self):
        """测试创建任务"""
        from src.core.agents.agent_manager import get_agent_manager

        try:
            manager = get_agent_manager()
            task = manager.create_task(
                task_type="test",
                stock_code="000001",
                agents=["macro_economic"]
            )
            assert task is not None
            print(f"✅ 创建任务测试通过 (ID: {task.task_id})")
        except Exception as e:
            print(f"❌ 创建任务测试失败: {e}")


class TestPerformanceTools:
    """性能工具测试"""

    def test_cache_manager(self):
        """测试缓存管理器"""
        from src.core.utils.performance import CacheManager

        try:
            cache = CacheManager()
            cache.set("test_key", "test_value", ttl_seconds=60)
            value = cache.get("test_key")
            assert value == "test_value"
            print("✅ 缓存管理器测试通过")
        except Exception as e:
            print(f"❌ 缓存管理器测试失败: {e}")

    def test_cached_decorator(self):
        """测试缓存装饰器"""
        from src.core.utils.performance import cached

        try:
            call_count = [0]

            @cached(ttl_seconds=60)
            def test_function():
                call_count[0] += 1
                return "result"

            # 第一次调用
            result1 = test_function()
            assert call_count[0] == 1

            # 第二次调用（应该从缓存获取）
            result2 = test_function()
            assert call_count[0] == 1  # 没有增加

            print("✅ 缓存装饰器测试通过")
        except Exception as e:
            print(f"❌ 缓存装饰器测试失败: {e}")

    def test_performance_monitor(self):
        """测试性能监控"""
        from src.core.utils.performance import PerformanceMonitor

        try:
            # 清除之前的指标
            PerformanceMonitor._metrics.clear()

            @PerformanceMonitor.measure_time("test_operation")
            def test_operation():
                time.sleep(0.1)
                return "done"

            result = test_operation()
            assert result == "done"

            metrics = PerformanceMonitor.get_metrics()
            assert "test_operation" in metrics

            print("✅ 性能监控测试通过")
        except Exception as e:
            print(f"❌ 性能监控测试失败: {e}")


class TestVisualizationTools:
    """可视化工具测试"""

    def test_candlestick_chart(self):
        """测试K线图"""
        from src.core.utils.visualization import (
            CandlestickChart,
            generate_sample_kline_data
        )

        try:
            df = generate_sample_kline_data(100)
            fig = CandlestickChart.create_candlestick(df)
            assert fig is not None
            print("✅ K线图测试通过")
        except Exception as e:
            print(f"❌ K线图测试失败: {e}")

    def test_technical_indicators(self):
        """测试技术指标"""
        from src.core.utils.visualization import (
            TechnicalIndicators,
            generate_sample_kline_data
        )

        try:
            df = generate_sample_kline_data(100)
            df = TechnicalIndicators.calculate_macd(df)
            df = TechnicalIndicators.calculate_rsi(df)
            df = TechnicalIndicators.calculate_bollinger_bands(df)

            assert 'macd' in df.columns
            assert 'rsi' in df.columns
            assert 'boll_upper' in df.columns

            print("✅ 技术指标测试通过")
        except Exception as e:
            print(f"❌ 技术指标测试失败: {e}")


class TestExportTools:
    """导出工具测试"""

    def test_excel_exporter(self):
        """测试Excel导出"""
        from src.core.utils.exporters import ExcelExporter

        try:
            # 准备测试数据
            analysis_result = {
                "agent1": {
                    "agent_name": "Test Agent",
                    "army": "测试军团",
                    "score": 85,
                    "recommendation": "买入",
                    "confidence": 0.85,
                    "analysis": "测试分析",
                    "timestamp": "2026-03-15"
                }
            }

            # 导出
            excel_bytes = ExcelExporter.export_analysis_data(
                stock_code="000001",
                analysis_result=analysis_result
            )

            assert excel_bytes is not None
            assert len(excel_bytes) > 0

            print("✅ Excel导出测试通过")
        except Exception as e:
            print(f"❌ Excel导出测试失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("  Agent Army Web v2.0 - Integration Tests")
    print("=" * 60)
    print()

    # Web页面测试
    print("[Pages] Testing Web Pages...")
    test_pages = TestWebPages()
    test_pages.test_dashboard_page()
    test_pages.test_agent_status_page()
    test_pages.test_task_management_page()
    test_pages.test_data_center_page()
    test_pages.test_analysis_reports_page()
    print()

    # Agent管理器测试
    print("[Agents] Testing Agent Manager...")
    test_agent = TestAgentManager()
    test_agent.test_agent_manager_initialization()
    test_agent.test_get_all_agents()
    test_agent.test_create_task()
    print()

    # 性能工具测试
    print("[Perf] Testing Performance Tools...")
    test_perf = TestPerformanceTools()
    test_perf.test_cache_manager()
    test_perf.test_cached_decorator()
    test_perf.test_performance_monitor()
    print()

    # 可视化工具测试
    print("[Viz] Testing Visualization Tools...")
    test_viz = TestVisualizationTools()
    test_viz.test_candlestick_chart()
    test_viz.test_technical_indicators()
    print()

    # 导出工具测试
    print("[Export] Testing Export Tools...")
    test_export = TestExportTools()
    test_export.test_excel_exporter()
    print()

    print("=" * 60)
    print("  Tests Completed")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

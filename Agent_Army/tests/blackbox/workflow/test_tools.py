"""
Agent Army - 工具库黑盒测试
测试可视化、导出、缓存等工具功能
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.blackbox.utils.base import BlackBoxTestCase


class VisualizationToolsTest(BlackBoxTestCase):
    """可视化工具测试"""

    def __init__(self):
        super().__init__(
            name="可视化工具测试",
            description="测试 K线图、技术指标、财务图表等可视化功能"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 导入可视化模块
        self.log_step("导入可视化模块")
        try:
            from src.core.utils.visualization import (
                CandlestickChart,
                TechnicalIndicators,
                FinancialCharts,
                generate_sample_kline_data
            )
            self.log_step("可视化模块导入成功", "PASS")
        except Exception as e:
            self.log_step(f"可视化模块导入失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ImportError',
                'message': str(e)
            })
            return

        # 步骤2: 生成测试数据
        self.log_step("生成 K线测试数据")
        try:
            df = generate_sample_kline_data(100)
            self.assert_not_none(df, "数据不为空")
            self.assert_true(len(df) > 0, "数据行数 > 0")
            self.log_step(f"生成 {len(df)} 行测试数据", "PASS")
        except Exception as e:
            self.log_step(f"数据生成失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'DataGenerationError',
                'message': str(e)
            })
            return

        # 步骤3: 创建 K线图
        self.log_step("创建 K线图")
        try:
            fig = CandlestickChart.create_candlestick(df)
            self.assert_not_none(fig, "K线图不为空")
            self.log_step("K线图创建成功", "PASS")
        except Exception as e:
            self.log_step(f"K线图创建失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ChartCreationError',
                'message': str(e)
            })

        # 步骤4: 计算技术指标
        self.log_step("计算技术指标")
        try:
            df_macd = TechnicalIndicators.calculate_macd(df)
            self.assert_in('macd', df_macd.columns, "包含 MACD 指标")

            df_rsi = TechnicalIndicators.calculate_rsi(df)
            self.assert_in('rsi', df_rsi.columns, "包含 RSI 指标")

            df_bb = TechnicalIndicators.calculate_bollinger_bands(df)
            self.assert_in('upper_band', df_bb.columns, "包含布林带指标")

            self.log_step("技术指标计算成功", "PASS")

        except Exception as e:
            self.log_step(f"技术指标计算失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'IndicatorCalculationError',
                'message': str(e)
            })

        # 步骤5: 创建财务图表
        self.log_step("创建财务图表")
        try:
            # 雷达图
            scores = {"基本面": 85, "技术面": 78, "情绪面": 82}
            radar_fig = FinancialCharts.create_radar_chart(scores)
            self.assert_not_none(radar_fig, "雷达图不为空")

            # 趋势图
            trend_df = pd.DataFrame({
                'date': pd.date_range('2026-01-01', periods=10),
                'score': range(10)
            })
            trend_fig = FinancialCharts.create_trend_chart(trend_df)
            self.assert_not_none(trend_fig, "趋势图不为空")

            self.log_step("财务图表创建成功", "PASS")

        except Exception as e:
            self.log_step(f"财务图表创建失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'FinancialChartError',
                'message': str(e)
            })


class ExportToolsTest(BlackBoxTestCase):
    """导出工具测试"""

    def __init__(self):
        super().__init__(
            name="导出工具测试",
            description="测试 Excel、CSV 等导出功能"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 导入导出模块
        self.log_step("导入导出模块")
        try:
            from src.core.utils.exporters import ExcelExporter
            self.log_step("导出模块导入成功", "PASS")
        except Exception as e:
            self.log_step(f"导出模块导入失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ImportError',
                'message': str(e)
            })
            return

        # 步骤2: 测试 Excel 导出
        self.log_step("测试 Excel 导出")
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

            self.assert_not_none(excel_bytes, "Excel 数据不为空")
            self.assert_greater(len(excel_bytes), 0, "Excel 数据大小 > 0")

            self.log_step(f"Excel 导出成功 ({len(excel_bytes)} 字节)", "PASS")

        except Exception as e:
            self.log_step(f"Excel 导出失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ExportError',
                'message': str(e)
            })


class PerformanceToolsTest(BlackBoxTestCase):
    """性能工具测试"""

    def __init__(self):
        super().__init__(
            name="性能工具测试",
            description="测试缓存、性能监控等工具"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 导入性能工具
        self.log_step("导入性能工具")
        try:
            from src.core.utils.performance import (
                CacheManager,
                cached,
                PerformanceMonitor
            )
            self.log_step("性能工具导入成功", "PASS")
        except Exception as e:
            self.log_step(f"性能工具导入失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ImportError',
                'message': str(e)
            })
            return

        # 步骤2: 测试缓存管理器
        self.log_step("测试缓存管理器")
        try:
            cache = CacheManager()
            cache.set("test_key", "test_value", ttl_seconds=60)
            value = cache.get("test_key")

            self.assert_equal(value, "test_value", "缓存读写一致")
            self.log_step("缓存管理器测试通过", "PASS")

        except Exception as e:
            self.log_step(f"缓存管理器测试失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'CacheError',
                'message': str(e)
            })

        # 步骤3: 测试缓存装饰器
        self.log_step("测试缓存装饰器")
        try:
            call_count = [0]

            @cached(ttl_seconds=60)
            def test_function():
                call_count[0] += 1
                return "result"

            # 第一次调用
            result1 = test_function()
            self.assert_equal(call_count[0], 1, "首次调用执行函数")

            # 第二次调用（应该从缓存获取）
            result2 = test_function()
            self.assert_equal(call_count[0], 1, "第二次调用使用缓存")

            self.log_step("缓存装饰器测试通过", "PASS")

        except Exception as e:
            self.log_step(f"缓存装饰器测试失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'DecoratorError',
                'message': str(e)
            })

        # 步骤4: 测试性能监控
        self.log_step("测试性能监控")
        try:
            import time

            # 清除之前的指标
            PerformanceMonitor._metrics.clear()

            @PerformanceMonitor.measure_time("test_operation")
            def test_operation():
                time.sleep(0.1)
                return "done"

            result = test_operation()
            metrics = PerformanceMonitor.get_metrics()

            self.assert_equal(result, "done", "函数执行正确")
            self.assert_in("test_operation", metrics, "性能指标被记录")

            self.log_step("性能监控测试通过", "PASS")

        except Exception as e:
            self.log_step(f"性能监控测试失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'MonitorError',
                'message': str(e)
            })

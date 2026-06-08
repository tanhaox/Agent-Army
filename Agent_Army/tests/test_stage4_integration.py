"""
阶段4集成测试 - 测试套件
版本: v1.0
日期: 2026-03-21
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSuite:
    """测试套件"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def test_stock_mapper(self):
        """测试股票代码映射功能"""
        print("\n" + "=" * 60)
        print("Test 1: Stock Code Mapper")
        print("=" * 60)

        try:
            from src.utils.stock_code_mapper import (
                get_stock_mapper,
                convert_stock_name_to_code_v2,
                convert_stock_code_to_name
            )

            # 测试1.1: 名称 -> 代码
            print("\n[Test 1.1] Name -> Code")
            test_cases = [
                ("贵州茅台", "600519"),
                ("伊利股份", "600887"),
                ("比亚迪", "002594"),
            ]

            for name, expected_code in test_cases:
                result = convert_stock_name_to_code_v2(name)
                if result == expected_code:
                    print(f"  [PASS] {name} -> {result}")
                    self.passed += 1
                else:
                    print(f"  [FAIL] {name} -> {result} (expected: {expected_code})")
                    self.failed += 1

            # 测试1.2: 代码 -> 名称
            print("\n[Test 1.2] Code -> Name")
            test_cases = [
                ("600519", "贵州茅台"),
                ("600887", "伊利股份"),
                ("002594", "比亚迪"),
            ]

            for code, expected_name in test_cases:
                result = convert_stock_code_to_name(code)
                if result == expected_name:
                    print(f"  [PASS] {code} -> {result}")
                    self.passed += 1
                else:
                    print(f"  [FAIL] {code} -> {result} (expected: {expected_name})")
                    self.failed += 1

            # 测试1.3: 模糊匹配
            print("\n[Test 1.3] Fuzzy Match")
            mapper = get_stock_mapper()

            test_cases = [
                ("茅台", "600519"),
                ("伊利", "600887"),
            ]

            for name, expected_code in test_cases:
                result = mapper.name_to_code_convert(name)
                if result == expected_code:
                    print(f"  [PASS] Fuzzy: {name} -> {result}")
                    self.passed += 1
                else:
                    print(f"  [FAIL] Fuzzy: {name} -> {result} (expected: {expected_code})")
                    self.failed += 1

            print("\n[OK] Stock mapper tests completed")

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            self.failed += 1

    def test_core_modules(self):
        """测试核心模块"""
        print("\n" + "=" * 60)
        print("Test 2: Core Modules Import")
        print("=" * 60)

        modules = [
            ("State Machine", "src.core.state_machine"),
            ("Permission Matrix", "src.core.permission_matrix"),
            ("Task Manager", "src.core.task_manager"),
            ("Logger", "src.core.logger"),
        ]

        for name, module_path in modules:
            try:
                __import__(module_path)
                print(f"  [PASS] {name} ({module_path})")
                self.passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} ({module_path}): {e}")
                self.failed += 1

    def test_agents(self):
        """测试Agent模块"""
        print("\n" + "=" * 60)
        print("Test 3: Agent Modules Import")
        print("=" * 60)

        agents = [
            ("Commander", "src.agents.management.commander"),
            ("HR Agent", "src.agents.management.hr"),
            ("Industry Analysis", "src.agents.business.research.industry_chain_ai"),
            ("Fundamental Analysis", "src.agents.business.analysis.fundamental_analysis_ai"),
        ]

        for name, agent_path in agents:
            try:
                __import__(agent_path)
                print(f"  [PASS] {name} ({agent_path})")
                self.passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} ({agent_path}): {e}")
                self.failed += 1

    def test_pages(self):
        """测试页面模块"""
        print("\n" + "=" * 60)
        print("Test 4: Page Modules Import")
        print("=" * 60)

        pages = [
            ("Home", "src.core.pages.enhanced_home"),
            ("Investment Analysis", "src.core.pages.investment_analysis_v2"),
            ("System Monitor", "src.core.pages.enhanced_agent_status"),
        ]

        for name, page_path in pages:
            try:
                __import__(page_path)
                print(f"  [PASS] {name} ({page_path})")
                self.passed += 1
            except Exception as e:
                print(f"  [FAIL] {name} ({page_path}): {e}")
                self.failed += 1

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Pass rate: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        if self.failed == 0:
            print("\n[SUCCESS] All tests passed!")
        else:
            print(f"\n[WARNING] {self.failed} test(s) failed")


def main():
    """主函数"""
    print("=" * 60)
    print("  Agent Army v2.0 - Stage 4 Integration Tests")
    print("=" * 60)
    print()

    suite = TestSuite()

    # 运行测试
    suite.test_core_modules()
    suite.test_agents()
    suite.test_pages()
    suite.test_stock_mapper()

    # 打印摘要
    suite.print_summary()

    # 返回退出码
    return 0 if suite.failed == 0 else 1


if __name__ == "__main__":
    exit(main())

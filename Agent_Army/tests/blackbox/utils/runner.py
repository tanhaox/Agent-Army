"""
Agent Army - 黑盒测试运行器
负责执行测试用例并生成报告
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import traceback

# 设置UTF-8编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 抑制Streamlit警告
import logging as logging_module
for logger_name in ['streamlit.runtime.caching', 'streamlit.runtime.scriptrunner_utils', 'streamlit.runtime.state']:
    logger = logging_module.getLogger(logger_name)
    logger.setLevel(logging_module.ERROR)
    logger.propagate = False

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """测试运行器"""

    def __init__(self, test_dir: str = None):
        """
        初始化测试运行器

        Args:
            test_dir: 测试目录路径
        """
        if test_dir is None:
            test_dir = Path(__file__).parent.parent

        self.test_dir = Path(test_dir) / "blackbox"
        self.results = {
            'run_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'start_time': datetime.now().isoformat(),
            'test_cases': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        }
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('BlackBoxTestRunner')
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def run_test_case(self, test_case_class: type, **kwargs) -> Dict:
        """
        运行单个测试用例

        Args:
            test_case_class: 测试用例类
            **kwargs: 测试用例参数

        Returns:
            测试结果字典
        """
        try:
            # 创建测试用例实例
            test_case = test_case_class(**kwargs)

            # 运行测试
            if hasattr(test_case, 'run'):
                test_case.run()
            else:
                raise ValueError(f"测试用例 {test_case_class.__name__} 缺少 run() 方法")

            # 获取结果
            result = test_case.finish()
            return result

        except Exception as e:
            self.logger.error(f"测试执行异常: {str(e)}")
            self.logger.error(traceback.format_exc())

            return {
                'test_name': test_case_class.__name__,
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'passed': 0,
                'failed': 1,
                'steps': [],
                'errors': [{
                    'type': 'Exception',
                    'message': str(e),
                    'traceback': traceback.format_exc()
                }]
            }

    def run_all_tests(self, pattern: str = "test_*.py") -> Dict:
        """
        运行所有测试

        Args:
            pattern: 测试文件匹配模式

        Returns:
            测试结果汇总
        """
        self.logger.info("=" * 70)
        self.logger.info("  Agent Army - 黑盒测试系统")
        self.logger.info("=" * 70)
        self.logger.info(f"开始时间: {self.results['start_time']}")
        self.logger.info(f"运行ID: {self.results['run_id']}")
        self.logger.info("")

        # 发现测试文件
        test_files = list(self.test_dir.rglob(pattern))

        if not test_files:
            self.logger.warning(f"未找到测试文件: {pattern}")
            return self.results

        self.logger.info(f"发现 {len(test_files)} 个测试文件")
        self.logger.info("")

        # 运行测试
        for test_file in test_files:
            try:
                # 动态导入测试模块
                module_name = test_file.stem
                spec = __import__(
                    f"tests.blackbox.{test_file.parent.name}.{module_name}",
                    fromlist=['']
                )

                # 查找测试用例类
                for attr_name in dir(spec):
                    attr = getattr(spec, attr_name)
                    if (
                        isinstance(attr, type) and
                        hasattr(attr, 'run') and
                        attr_name.endswith('Test')
                    ):
                        self.logger.info(f"运行测试: {attr.__name__}")
                        result = self.run_test_case(attr)
                        self.results['test_cases'].append(result)

            except Exception as e:
                self.logger.error(f"加载测试文件失败 {test_file}: {str(e)}")

        # 计算汇总统计
        self._calculate_summary()

        # 输出总结
        self._print_summary()

        return self.results

    def run_specific_tests(self, test_names: List[str]) -> Dict:
        """
        运行指定的测试

        Args:
            test_names: 测试名称列表

        Returns:
            测试结果汇总
        """
        self.logger.info("=" * 70)
        self.logger.info("  Agent Army - 黑盒测试系统（指定测试）")
        self.logger.info("=" * 70)
        self.logger.info(f"开始时间: {self.results['start_time']}")
        self.logger.info(f"运行ID: {self.results['run_id']}")
        self.logger.info("")

        for test_name in test_names:
            self.logger.info(f"运行测试: {test_name}")
            # TODO: 实现指定测试的运行逻辑

        return self.results

    def _calculate_summary(self):
        """计算测试统计"""
        total_passed = sum(tc.get('passed', 0) for tc in self.results['test_cases'])
        total_failed = sum(tc.get('failed', 0) for tc in self.results['test_cases'])
        total = total_passed + total_failed

        self.results['summary']['total'] = total
        self.results['summary']['passed'] = total_passed
        self.results['summary']['failed'] = total_failed
        self.results['summary']['success_rate'] = (
            (total_passed / total * 100) if total > 0 else 0
        )

        self.results['end_time'] = datetime.now().isoformat()

    def _print_summary(self):
        """打印测试总结"""
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("  测试总结")
        self.logger.info("=" * 70)

        summary = self.results['summary']
        self.logger.info(f"总断言数: {summary['total']}")
        self.logger.info(f"通过: {summary['passed']}")
        self.logger.info(f"失败: {summary['failed']}")
        self.logger.info(f"成功率: {summary['success_rate']:.1f}%")

        # 列出失败的测试
        failed_tests = [
            tc for tc in self.results['test_cases']
            if not tc.get('success', True)
        ]

        if failed_tests:
            self.logger.info("")
            self.logger.info("❌ 失败的测试:")
            for tc in failed_tests:
                self.logger.info(f"  - {tc.get('test_name', 'Unknown')}")
        else:
            self.logger.info("")
            self.logger.info("✅ 所有测试通过！")

        self.logger.info("=" * 70)

    def save_report(self, output_dir: str = None):
        """
        保存测试报告

        Args:
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = self.test_dir / "reports"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON 报告
        json_file = output_dir / f"test_report_{self.results['run_id']}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        self.logger.info(f"JSON 报告已保存: {json_file}")

        # Markdown 报告
        md_file = output_dir / f"test_report_{self.results['run_id']}.md"
        self._generate_markdown_report(md_file)

        self.logger.info(f"Markdown 报告已保存: {md_file}")

    def _generate_markdown_report(self, output_file: Path):
        """生成 Markdown 报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Agent Army 黑盒测试报告\n\n")
            f.write(f"**运行ID**: {self.results['run_id']}\n")
            f.write(f"**开始时间**: {self.results['start_time']}\n")
            f.write(f"**结束时间**: {self.results.get('end_time', 'N/A')}\n\n")

            # 总结
            summary = self.results['summary']
            f.write("## 测试总结\n\n")
            f.write(f"| 指标 | 数值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 总断言数 | {summary['total']} |\n")
            f.write(f"| 通过 | {summary['passed']} ✅ |\n")
            f.write(f"| 失败 | {summary['failed']} ❌ |\n")
            f.write(f"| 成功率 | {summary['success_rate']:.1f}% |\n\n")

            # 测试用例详情
            f.write("## 测试用例详情\n\n")

            for tc in self.results['test_cases']:
                status_icon = "✅" if tc.get('success', True) else "❌"
                f.write(f"### {status_icon} {tc.get('test_name', 'Unknown')}\n\n")

                if tc.get('description'):
                    f.write(f"**描述**: {tc['description']}\n\n")

                # 统计
                f.write(f"- **通过**: {tc.get('passed', 0)}\n")
                f.write(f"- **失败**: {tc.get('failed', 0)}\n\n")

                # 错误详情
                if tc.get('errors'):
                    f.write("**错误详情**:\n\n")
                    for error in tc['errors']:
                        f.write(f"- **{error.get('type', 'Error')}**: {error.get('message', 'Unknown')}\n")
                    f.write("\n")

                # 测试步骤
                if tc.get('steps'):
                    f.write("**测试步骤**:\n\n")
                    for step in tc['steps']:
                        icon = {
                            'PASS': '✅',
                            'FAIL': '❌',
                            'INFO': '📋'
                        }.get(step.get('status', 'INFO'), '📋')

                        f.write(f"{icon} `{step.get('time', '')}` {step.get('step', '')}\n")
                    f.write("\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Agent Army 黑盒测试运行器')
    parser.add_argument('--pattern', default='test_*.py', help='测试文件匹配模式')
    parser.add_argument('--output', help='报告输出目录')
    parser.add_argument('--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 创建测试运行器
    runner = TestRunner()

    # 运行测试
    runner.run_all_tests(pattern=args.pattern)

    # 保存报告
    runner.save_report(output_dir=args.output)

    # 返回退出码
    summary = runner.results['summary']
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == '__main__':
    main()

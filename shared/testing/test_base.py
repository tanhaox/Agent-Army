"""
测试基类

提供所有测试的通用基类和辅助方法。
"""

import os
import sys
import json
import logging
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class BaseTestCase(unittest.TestCase):
    """
    测试基类

    提供所有测试用例的通用功能：
    - 临时目录管理
    - 日志配置
    - 测试数据管理
    - 断言辅助方法
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.project_root = PROJECT_ROOT
        cls.test_data_dir = cls.project_root / "shared" / "testing" / "test_data"
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        """每个测试用例前的初始化"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_")
        self.temp_path = Path(self.temp_dir)

        # 配置测试日志
        self._setup_test_logging()

    def tearDown(self):
        """每个测试用例后的清理"""
        # 清理临时目录
        if self.temp_path.exists():
            import shutil
            shutil.rmtree(self.temp_path)

    def _setup_test_logging(self):
        """配置测试日志"""
        log_file = self.temp_path / f"test_{self.id()}.log"

        # 配置日志格式
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    def get_test_data(self, filename: str) -> Path:
        """
        获取测试数据文件路径

        Args:
            filename: 测试数据文件名

        Returns:
            测试数据文件的完整路径
        """
        return self.test_data_dir / filename

    def load_json_data(self, filename: str) -> Dict[str, Any]:
        """
        加载 JSON 测试数据

        Args:
            filename: JSON 文件名

        Returns:
            解析后的 JSON 数据
        """
        json_file = self.get_test_data(filename)
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def assertIsValidProjectStructure(self, project_path: Path, project_type: str):
        """
        验证项目结构是否符合规范

        Args:
            project_path: 项目路径
            project_type: 项目类型 (skill/app/tool)
        """
        # 必需的目录
        required_dirs = ["tests", "logs", "docs", "examples"]
        for dir_name in required_dirs:
            dir_path = project_path / dir_name
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"缺少必需目录: {dir_name}"
            )

        # 必需的文件
        required_files = ["README.md", "requirements.txt", ".gitignore"]
        if project_type == "skill":
            required_files.append("_" + project_path.name.replace("-", "_") + ".py")
        else:
            # 查找主文件
            main_files = list(project_path.glob("*.py"))
            self.assertTrue(
                len(main_files) > 0,
                f"未找到主 Python 文件"
            )

        for file_name in required_files:
            file_path = project_path / file_name
            self.assertTrue(
                file_path.exists() and file_path.is_file(),
                f"缺少必需文件: {file_name}"
            )

    def assertIsValidLogFormat(self, log_file: Path):
        """
        验证日志文件格式是否正确

        Args:
            log_file: 日志文件路径
        """
        self.assertTrue(log_file.exists(), "日志文件不存在")

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.assertGreater(len(lines), 0, "日志文件为空")

        # 检查日志格式: YYYY-MM-DD HH:MM:SS - [LEVEL] - message
        for line in lines:
            self.assertRegex(
                line,
                r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
                f"日志格式不正确: {line}"
            )


class BaseSkillTestCase(BaseTestCase):
    """
    技能测试基类

    为技能项目提供特定的测试方法
    """

    def setUp(self):
        """初始化技能测试"""
        super().setUp()
        self.skill_class = None
        self.skill_instance = None

    def create_skill_instance(self, skill_class, **kwargs):
        """
        创建技能实例

        Args:
            skill_class: 技能类
            **kwargs: 技能初始化参数

        Returns:
            技能实例
        """
        self.skill_class = skill_class
        self.skill_instance = skill_class(**kwargs)
        return self.skill_instance

    def assertSkillExecuteSuccess(self, **kwargs):
        """
        断言技能执行成功

        Args:
            **kwargs: 技能执行参数
        """
        self.assertIsNotNone(self.skill_instance, "技能实例未创建")

        result = self.skill_instance.run(**kwargs)

        self.assertIsNotNone(result, "技能返回结果为空")
        self.assertTrue(hasattr(result, 'is_success'), "结果缺少 is_success 方法")
        self.assertTrue(result.is_success(), f"技能执行失败: {result.error}")

    def assertSkillExecuteFailed(self, **kwargs):
        """
        断言技能执行失败

        Args:
            **kwargs: 技能执行参数
        """
        self.assertIsNotNone(self.skill_instance, "技能实例未创建")

        result = self.skill_instance.run(**kwargs)

        self.assertIsNotNone(result, "技能返回结果为空")
        self.assertTrue(hasattr(result, 'is_success'), "结果缺少 is_success 方法")
        self.assertFalse(result.is_success(), "技能应该执行失败")


class BaseAppTestCase(BaseTestCase):
    """
    应用测试基类

    为应用项目提供特定的测试方法
    """

    def setUp(self):
        """初始化应用测试"""
        super().setUp()
        self.app_instance = None

    def assertAppCanStart(self):
        """断言应用可以启动"""
        self.assertIsNotNone(self.app_instance, "应用实例未创建")

        # 检查应用是否有启动方法
        self.assertTrue(
            hasattr(self.app_instance, 'run') or hasattr(self.app_instance, 'start'),
            "应用缺少 run 或 start 方法"
        )


class BaseToolTestCase(BaseTestCase):
    """
    工具测试基类

    为工具项目提供特定的测试方法
    """

    def setUp(self):
        """初始化工具测试"""
        super().setUp()
        self.tool_class = None

    def assertToolHasCLI(self):
        """断言工具有命令行接口"""
        self.assertIsNotNone(self.tool_class, "工具类未设置")

        # 检查工具是否有主函数或命令行接口
        self.assertTrue(
            hasattr(self.tool_class, 'main') or
            hasattr(self.tool_class, 'cli') or
            hasattr(self.tool_class, 'run'),
            "工具缺少命令行接口方法 (main/cli/run)"
        )

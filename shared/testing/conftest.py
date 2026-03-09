"""
pytest 配置文件

定义所有测试共享的 pytest fixtures 和配置。
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime

import pytest

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ==================== 目录 Fixtures ====================

@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """测试数据目录"""
    data_dir = project_root / "shared" / "testing" / "test_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def temp_dir():
    """
    临时目录 fixture

    每个测试用例自动清理
    """
    temp_path = Path(tempfile.mkdtemp(prefix="pytest_test_"))
    yield temp_path

    # 清理
    if temp_path.exists():
        import shutil
        shutil.rmtree(temp_path)


@pytest.fixture
def temp_file(temp_dir):
    """
    临时文件 fixture

    返回一个函数，用于创建临时文件
    """
    def _create_temp_file(filename: str, content: str = "") -> Path:
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path

    return _create_temp_file


# ==================== 日志 Fixtures ====================

@pytest.fixture
def test_log(temp_dir, request):
    """
    测试日志 fixture

    为每个测试用例创建独立的日志文件
    """
    log_file = temp_dir / f"test_{request.node.name}.log"

    # 配置日志
    logger = logging.getLogger(request.node.name)
    logger.setLevel(logging.DEBUG)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    yield logger, log_file

    # 清理
    logger.removeHandler(file_handler)
    logger.removeHandler(console_handler)
    file_handler.close()


# ==================== 配置 Fixtures ====================

@pytest.fixture
def mock_config_env(monkeypatch, temp_dir):
    """
    模拟配置环境 fixture

    设置测试环境变量和配置文件
    """
    # 创建临时配置文件
    config_file = temp_dir / "config.json"
    config_file.write_text('{"test": true}', encoding='utf-8')

    # 设置环境变量
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("CONFIG_PATH", str(config_file))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    return {
        "config_file": config_file,
        "env_vars": {
            "TEST_MODE": "true",
            "CONFIG_PATH": str(config_file),
            "LOG_LEVEL": "DEBUG"
        }
    }


@pytest.fixture
def sample_project(temp_dir):
    """
    示例项目 fixture

    创建一个符合规范的项目结构
    """
    project_dir = temp_dir / "test-skill"
    project_dir.mkdir()

    # 创建标准目录结构
    (project_dir / "tests").mkdir()
    (project_dir / "logs").mkdir()
    (project_dir / "docs").mkdir()
    (project_dir / "examples").mkdir()

    # 创建必需文件
    (project_dir / "README.md").write_text("# Test Skill\n\n测试技能项目", encoding='utf-8')
    (project_dir / "requirements.txt").write_text("pytest>=7.0.0", encoding='utf-8')
    (project_dir / ".gitignore").write_text("*.pyc\n__pycache__/", encoding='utf-8')
    (project_dir / "test_skill.py").write_text("""
# Test Skill
class TestSkill:
    def execute(self):
        return {"status": "success"}
""", encoding='utf-8')

    return project_dir


# ==================== 数据 Fixtures ====================

@pytest.fixture
def sample_json_data(temp_dir):
    """示例 JSON 数据"""
    json_file = temp_dir / "test_data.json"
    data = {
        "name": "test",
        "version": "1.0.0",
        "items": [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"}
        ]
    }
    import json
    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return json_file, data


@pytest.fixture
def sample_log_data(temp_dir):
    """示例日志数据"""
    log_file = temp_dir / "test.log"

    log_lines = [
        "2026-02-08 10:00:00 - [INFO] - 应用启动",
        "2026-02-08 10:00:01 - [DEBUG] - 加载配置",
        "2026-02-08 10:00:02 - [INFO] - 处理请求",
        "2026-02-08 10:00:03 - [ERROR] - 发生错误: Connection failed",
        "2026-02-08 10:00:04 - [INFO] - 应用关闭"
    ]

    log_file.write_text("\n".join(log_lines), encoding='utf-8')
    return log_file, log_lines


# ==================== 性能测试 Fixtures ====================

@pytest.fixture
def performance_thresholds():
    """
    性能阈值配置

    可以为不同操作定义最大允许时间
    """
    return {
        "api_call": 1.0,          # API 调用最大 1 秒
        "file_operation": 0.5,    # 文件操作最大 0.5 秒
        "data_processing": 2.0,   # 数据处理最大 2 秒
        "skill_execution": 3.0,   # 技能执行最大 3 秒
    }


# ==================== pytest 配置 ====================

def pytest_configure(config):
    """pytest 配置钩子"""
    # 自定义标记
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "slow: 慢速测试")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """测试环境初始化（session 级别，自动使用）"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    yield

    # 清理
    os.environ.pop("TESTING", None)
    os.environ.pop("LOG_LEVEL", None)


# ==================== CI/CD Fixtures ====================

@pytest.fixture
def ci_environment(monkeypatch):
    """
    CI 环境模拟 fixture

    用于测试 CI/CD 相关功能
    """
    # 模拟 CI 环境变量
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_RUN_ID", "123456789")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")

    return {
        "platform": "github",
        "run_id": "123456789",
        "branch": "main"
    }

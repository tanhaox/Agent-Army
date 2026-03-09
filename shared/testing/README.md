# AI-Agent-Local 测试框架

**版本**: 1.0.0
**状态**: ✅ 可用于生产环境

---

## 🎯 概述

提供标准化的测试基础设施，包括测试基类、pytest 配置、工具函数、夹具和模板。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements-dev.txt
```

### 2. 运行测试

```bash
# Windows
run_tests.bat

# Linux/Mac
./run_tests.sh

# 或直接使用 pytest
pytest
```

### 3. 查看覆盖率

```bash
pytest --cov=. --cov-report=html
start htmlcov/index.html
```

---

## 📁 目录结构

```
shared/testing/
├── __init__.py              # 框架入口
├── test_base.py             # 测试基类
├── conftest.py              # pytest 配置
├── utils.py                 # 工具函数
├── fixtures/                # 测试夹具
│   ├── __init__.py
│   └── common_fixtures.py
├── templates/               # 测试模板
│   ├── unit_test_template.py
│   ├── integration_test_template.py
│   └── performance_test_template.py
└── examples/                # 测试示例
    ├── example_unit_test.py
    └── example_pytest_test.py
```

---

## 📚 核心 API

### 测试基类

```python
from shared.testing.test_base import BaseSkillTestCase

class TestMySkill(BaseSkillTestCase):
    def test_execute(self):
        self.assertSkillExecuteSuccess(param="value")
```

### pytest Fixtures

```python
def test_temp_file(temp_file):
    file = temp_file("test.txt", "内容")
    assert file.exists()

def test_log_fixture(test_log):
    logger, log_file = test_log
    logger.info("消息")
```

### 工具函数

```python
from shared.testing.utils import (
    assert_valid_json,
    assert_log_contains,
    measure_execution_time
)

assert_valid_json({"key": "value"})
assert_log_contains(log_file, r"\[INFO\]")
result, time = measure_execution_time(my_function)
```

### 测试夹具

```python
from shared.testing.fixtures import mock_api_response, mock_file_system

with mock_api_response({"data": "test"}):
    response = api_client.get("/endpoint")

with mock_file_system({"file.txt": "内容"}) as temp_dir:
    # 使用模拟的文件系统
    pass
```

---

## 🎨 使用模板

```bash
# 复制单元测试模板
cp shared/testing/templates/unit_test_template.py \
   projects/skills/your_skill/tests/test_your_skill.py

# 编辑 TODO 部分
vim projects/skills/your_skill/tests/test_your_skill.py
```

---

## 📖 文档

- **使用指南**: `docs/测试框架使用指南.md`
- **实施报告**: `TESTING_FRAMEWORK_REPORT.md`
- **pytest 文档**: https://docs.pytest.org/

---

## 🧪 测试标记

```bash
pytest -m unit         # 只运行单元测试
pytest -m integration  # 只运行集成测试
pytest -m "not slow"   # 跳过慢速测试
```

---

## 📊 覆盖率目标

- **最低覆盖率**: 70%
- **推荐覆盖率**: 80%
- **优秀覆盖率**: 90%+

---

**维护者**: AI-Agent-Local
**最后更新**: 2026-02-08

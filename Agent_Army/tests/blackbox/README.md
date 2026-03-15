# Agent Army 黑盒测试系统

**版本**: v1.0
**创建日期**: 2026-03-15
**维护者**: omc team qa-tester

---

## 📋 目录

1. [系统概述](#系统概述)
2. [目录结构](#目录结构)
3. [快速开始](#快速开始)
4. [测试用例编写](#测试用例编写)
5. [测试运行](#测试运行)
6. [测试报告](#测试报告)
7. [最佳实践](#最佳实践)

---

## 🎯 系统概述

### 什么是黑盒测试？

黑盒测试（Black-box Testing）是不考虑内部实现细节，只关注**输入和输出**的测试方法。

### 特点

- ✅ **用户视角**：模拟真实用户使用场景
- ✅ **功能验证**：验证功能是否按预期工作
- ✅ **接口测试**：测试 API、UI 等外部接口
- ✅ **端到端测试**：测试完整的工作流程

### 测试覆盖范围

| 类别 | 测试内容 | 测试用例 |
|------|---------|---------|
| **Agent 管理** | Agent 初始化、查询、配置、任务创建 | `test_agents.py` |
| **配置系统** | 配置加载、验证、切换 | `test_config.py` |
| **工具库** | 可视化、导出、缓存、性能 | `test_tools.py` |
| **工作流** | 完整的分析流程 | TODO |

---

## 📁 目录结构

```
tests/blackbox/
├── utils/              # 测试工具
│   ├── base.py        # 测试基类
│   └── runner.py      # 测试运行器
├── workflow/          # 工作流测试
│   ├── test_agents.py # Agent 测试
│   ├── test_config.py # 配置测试
│   └── test_tools.py  # 工具测试
├── api/               # API 测试（待实现）
├── data/              # 测试数据
└── reports/           # 测试报告
```

---

## 🚀 快速开始

### 方式1: 使用批处理脚本（推荐）

```batch
run_blackbox_tests.bat
```

### 方式2: 使用 pytest

```bash
# 运行所有黑盒测试
pytest tests/blackbox/ -v

# 运行特定测试
pytest tests/blackbox/workflow/test_agents.py -v

# 运行特定测试用例
pytest tests/blackbox/workflow/test_agents.py::AgentManagerTest -v

# 生成详细报告
pytest tests/blackbox/ -v --tb=long --cov=src
```

### 方式3: 使用测试运行器

```python
from tests.blackbox.utils.runner import TestRunner

# 创建运行器
runner = TestRunner()

# 运行所有测试
results = runner.run_all_tests()

# 保存报告
runner.save_report()
```

---

## ✍️ 测试用例编写

### 基本结构

所有测试用例必须继承自 `BlackBoxTestCase`：

```python
from tests.blackbox.utils.base import BlackBoxTestCase

class MyTest(BlackBoxTestCase):
    def __init__(self):
        super().__init__(
            name="测试名称",
            description="测试描述"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 准备
        self.log_step("准备测试数据")

        # 步骤2: 执行
        result = some_function()

        # 步骤3: 验证
        self.assert_equal(result, expected, "验证结果")
```

### 断言方法

| 方法 | 说明 | 示例 |
|------|------|------|
| `assert_equal` | 断言相等 | `self.assert_equal(actual, expected)` |
| `assert_true` | 断言为真 | `self.assert_true(condition)` |
| `assert_not_none` | 断言非空 | `self.assert_not_none(value)` |
| `assert_in` | 断言包含 | `self.assert_in(item, container)` |
| `assert_greater` | 断言大于 | `self.assert_greater(value, threshold)` |

### 测试步骤

使用 `log_step()` 记录测试步骤：

```python
def run(self):
    self.log_step("步骤1: 导入模块")
    # ... 代码 ...

    self.log_step("步骤完成", "PASS")  # 或 "FAIL"
```

### 完整示例

```python
from tests.blackbox.utils.base import BlackBoxTestCase

class CalculatorTest(BlackBoxTestCase):
    def __init__(self):
        super().__init__(
            name="计算器测试",
            description="测试基本计算功能"
        )

    def run(self):
        # 导入
        self.log_step("导入计算器模块")
        from myapp import Calculator

        # 创建实例
        self.log_step("创建计算器实例")
        calc = Calculator()
        self.assert_not_none(calc, "计算器创建成功")

        # 测试加法
        self.log_step("测试加法")
        result = calc.add(2, 3)
        self.assert_equal(result, 5, "2 + 3 = 5")

        # 测试除法
        self.log_step("测试除法")
        result = calc.divide(10, 2)
        self.assert_equal(result, 5, "10 / 2 = 5")

        # 测试错误处理
        self.log_step("测试除零错误")
        try:
            calc.divide(10, 0)
            self.log_step("应该抛出异常", "FAIL")
        except ZeroDivisionError:
            self.log_step("正确抛出异常", "PASS")
```

---

## 🏃 测试运行

### 运行选项

```bash
# 1. 运行所有测试
pytest tests/blackbox/ -v

# 2. 运行特定目录
pytest tests/blackbox/workflow/ -v

# 3. 运行特定文件
pytest tests/blackbox/workflow/test_agents.py -v

# 4. 运行特定测试类
pytest tests/blackbox/workflow/test_agents.py::AgentManagerTest -v

# 5. 显示详细输出
pytest tests/blackbox/ -vv

# 6. 显示打印输出
pytest tests/blackbox/ -s

# 7. 生成覆盖率报告
pytest tests/blackbox/ --cov=src --cov-report=html

# 8. 失败时停止
pytest tests/blackbox/ -x

# 9. 重新运行失败的测试
pytest tests/blackbox/ --lf

# 10. 并行运行（需要 pytest-xdist）
pytest tests/blackbox/ -n auto
```

### 持续集成

**GitHub Actions 示例**:

```yaml
name: Black-box Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run black-box tests
      run: |
        pytest tests/blackbox/ -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## 📊 测试报告

### 报告类型

#### 1. JSON 报告

位置：`tests/blackbox/reports/test_report_YYYYMMDD_HHMMSS.json`

```json
{
  "run_id": "20260315_120000",
  "start_time": "2026-03-15T12:00:00",
  "end_time": "2026-03-15T12:01:00",
  "test_cases": [
    {
      "test_name": "Agent 管理器测试",
      "description": "测试 Agent 管理器的初始化、查询等功能",
      "success": true,
      "passed": 5,
      "failed": 0,
      "steps": [...]
    }
  ],
  "summary": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "success_rate": 96.0
  }
}
```

#### 2. Markdown 报告

位置：`tests/blackbox/reports/test_report_YYYYMMDD_HHMMSS.md`

包含：
- 测试总结
- 测试用例详情
- 错误详情
- 测试步骤

#### 3. HTML 覆盖率报告

生成命令：
```bash
pytest tests/blackbox/ --cov=src --cov-report=html
```

位置：`htmlcov/index.html`

---

## 🎯 最佳实践

### 1. 测试命名

**好的命名**:
- ✅ `AgentManagerTest`
- ✅ `ConfigSystemTest`
- ✅ `VisualizationToolsTest`

**不好的命名**:
- ❌ `Test1`
- ❌ `MyTest`
- ❌ `TestSomething`

### 2. 测试独立性

每个测试用例应该独立运行：

```python
# ✅ 好的做法
def run(self):
    # 准备独立的数据
    data = self._prepare_test_data()

    # 执行测试
    result = function(data)

    # 验证
    self.assert_equal(result, expected)

# ❌ 不好的做法（依赖其他测试）
def run(self):
    # 假设之前测试已创建数据
    data = load_data_from_previous_test()
```

### 3. 错误处理

```python
def run(self):
    try:
        # 执行测试
        result = some_function()
        self.assert_equal(result, expected)
    except Exception as e:
        self.log_step(f"测试异常: {str(e)}", "FAIL")
        self.results['errors'].append({
            'type': 'Exception',
            'message': str(e)
        })
```

### 4. 测试数据

使用固定的测试数据，避免随机性：

```python
# ✅ 好的做法
data = {"stock": "000001", "days": 100}

# ❌ 不好的做法（随机数据）
import random
data = {"stock": random.choice(["000001", "000002"])}

# ✅ 如果需要随机性，使用固定种子
import random
random.seed(42)
data = generate_random_data()
```

### 5. 清理资源

```python
def run(self):
    # 准备
    temp_file = "temp_test.txt"
    create_temp_file(temp_file)

    try:
        # 执行测试
        result = process_file(temp_file)
        self.assert_not_none(result)
    finally:
        # 清理
        if os.path.exists(temp_file):
            os.remove(temp_file)
```

---

## 🔧 扩展测试

### 添加新的测试用例

1. 在相应目录创建测试文件
2. 继承 `BlackBoxTestCase`
3. 实现 `run()` 方法
4. 添加断言和日志

### 添加新的测试类别

1. 在 `blackbox/` 下创建新目录
2. 创建测试文件
3. 更新此文档

---

## 📚 相关文档

- [冒烟测试指南](SMOKE_TEST_GUIDE.md) - 快速功能验证
- [集成测试文档](../test_integration_v2.py) - 模块集成测试
- [测试覆盖率报告](TEST_COVERAGE_QUICK_REF.md) - 代码覆盖率

---

## 🆘 常见问题

### Q: 黑盒测试和单元测试的区别？

**A**:
- **单元测试**: 测试单个函数/类，关注内部逻辑
- **黑盒测试**: 测试完整功能，关注输入输出

### Q: 为什么有些测试失败了？

**A**: 检查以下几点：
1. 依赖的服务是否启动
2. 配置文件是否正确
3. 测试数据是否存在
4. 环境变量是否设置

### Q: 如何调试测试？

**A**:
```bash
# 显示详细输出
pytest tests/blackbox/ -vv -s

# 进入调试器
pytest tests/blackbox/ --pdb

# 只运行失败的测试
pytest tests/blackbox/ --lf --pdb
```

---

**版本历史**:
- v1.0 (2026-03-15): 初始版本，包含 Agent、配置、工具测试

---

**🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！**

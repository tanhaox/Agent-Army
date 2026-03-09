# 共享脚本库

提供跨项目复用的脚本和工具。

## 目录结构

```
shared/scripts/
├── connection_handlers/    # 连接处理
│   ├── simple_connection.py      # 简化 API 连接
│   └── connection_manager.py     # 完整连接管理器
├── evaluation_tools/      # 评估工具
│   └── evaluation_helpers.py     # 评估辅助函数
└── utils/                 # 通用工具
    └── common_tools.py           # 通用工具函数
```

## 使用示例

### 连接处理

```python
from shared.scripts.connection_handlers.simple_connection import create_api_client

with create_api_client(
    base_url="https://api.example.com",
    api_key="your-key"
) as client:
    data = client.get("/endpoint")
    print(data)
```

### 评估工具

```python
from shared.testing.evaluation_generator import EvaluationFramework, EvaluationScenario

framework = EvaluationFramework("技能评估")
scenario = EvaluationScenario(
    question="问题",
    answer="答案",
    tools_required=["tool1", "tool2"]
)
framework.add_scenario(scenario)
```

### 通用工具

```python
from shared.scripts.utils.common_tools import (
    read_file, write_file, load_json, save_json,
    format_size, format_duration, retry
)

# 读取文件
content = read_file("path/to/file.txt")

# 写入文件
write_file("path/to/output.txt", "content")

# 格式化大小
size_str = format_size(1024*1024)  # "1.00 MB"

# 重试装饰器
@retry(max_attempts=3, delay=1.0)
def unstable_function():
    # 可能失败的操作
    pass
```

## 添加新脚本

1. 在相应目录创建新的 Python 文件
2. 添加完整的文档字符串
3. 包含使用示例
4. 更新此 README

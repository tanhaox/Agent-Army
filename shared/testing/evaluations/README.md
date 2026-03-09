# 评估场景模板

此目录包含用于测试技能的评估场景。

## 评估场景结构

每个评估文件应包含至少 10 个场景，每个场景必须满足以下标准：

1. **独立** - 不依赖其他问题
2. **只读** - 仅非破坏性操作
3. **复杂** - 需要多个工具调用
4. **现实** - 基于真实用例
5. **可验证** - 单一明确答案
6. **稳定** - 答案不随时间变化

## 创建评估场景

```python
from shared.testing.evaluation_generator import EvaluationFramework, EvaluationScenario

framework = EvaluationFramework("my-skill 评估")

# 添加场景
scenario = EvaluationScenario(
    question="你的问题",
    answer="答案",
    tools_required=["tool1", "tool2"],
    complexity="medium",
    metadata={
        "read_only": True,
        "real_world_use_case": "真实用例说明",
        "time_sensitive": False
    }
)

framework.add_scenario(scenario)
framework.save("tests/evaluations/my_skill_eval.xml")
```

## 运行评估

```bash
# 运行所有评估
pytest tests/evaluations/ -v

# 运行特定评估
pytest tests/evaluations/my_skill_eval.py -v

# 查看覆盖率
pytest --cov=. --cov-report=html
```

## 评估指标

- **准确率** > 80% (良好), > 90% (优秀), > 95% (卓越)
- **平均耗时** < 30s (良好), < 20s (优秀), < 15s (卓越)
- **平均工具调用** 越少越好

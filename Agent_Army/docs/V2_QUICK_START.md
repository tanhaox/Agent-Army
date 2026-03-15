# Agent Army - v2配置系统快速启动指南

**版本**: 2.0
**更新日期**: 2026-03-15
**适用对象**: GLM Coding Plan Max包月用户
**预计启动时间**: 3分钟

---

## ⚡ 3分钟快速启动

### 前置条件

✅ **GLM Coding Plan Max包月用户**
✅ **已安装Python 3.8+**
✅ **已安装项目依赖**

### 步骤1: 验证v2配置（30秒）

```bash
cd C:\AI-Agent-Local\Agent_Army
python -c "from src.core.config import get_model_for_agents; print(get_model_for_agents(['macro_economic']))"
```

**预期输出**:
```
{'macro_economic': 'glm-4.7'}
```

### 步骤2: 启动Web应用（30秒）

```bash
# Windows
start_web.bat

# 或命令行
streamlit run web_app.py
```

**访问地址**: http://localhost:8501

### 步骤3: 配置API密钥（1分钟）

1. 打开浏览器，访问 http://localhost:8501
2. 点击左侧菜单 "⚙️ 系统配置"
3. 点击 "🔑 API配置管理"
4. 填写密钥：
   - **智谱AI API密钥**（必需）
   - **Tushare Token**（必需）
5. 点击 "💾 保存配置"

### 步骤4: 开始分析（1分钟）

1. 点击左侧菜单 "📋 任务管理"
2. 选择 "📊 投资分析" 标签
3. 输入股票代码：`600519`
4. 点击 "🔍 开始分析"
5. 观察Agent工作过程
6. 等待分析完成

**完成！** 🎉

---

## 🎯 v2配置核心特性

### 质量优先

```
所有Agent使用高质量模型：
- GLM-5: 战略决策（2个Agent）
- GLM-4.7: 业务分析（26个Agent）
```

### 配置简单

```python
# 无需复杂的等级分配
from src.core.config import get_model_for_agents

# 自动分配最优模型
models = get_model_for_agents(['news_monitor'])
# {'news_monitor': 'glm-4.7'}
```

### 成本无关

```
包月无限使用 → 无需token优化
专注质量和性能 → 无需动态切换
```

---

## 📊 模型分配查询

### 查询单个Agent

```python
from src.core.config import get_model_config

model = get_model_config('macro_economic')
print(f'模型: {model}')
# 输出: glm-4.7
```

### 查询多个Agent

```python
from src.core.config import get_model_for_agents

agents = [
    'commander',          # Commander Agent
    'hr_agent',           # HR Agent
    'macro_economic',     # 宏观经济AI
    'news_monitor',       # 新闻监控AI
    'financial_health',   # 财务健康AI
    'asset_allocation'    # 资产配置AI
]

models = get_model_for_agents(agents)
for agent, model in models.items():
    print(f'{agent}: {model}')
```

**输出**:
```
commander: glm-5
hr_agent: glm-4.7
macro_economic: glm-4.7
news_monitor: glm-4.7
financial_health: glm-4.7
asset_allocation: glm-5
```

### 查看统计信息

```python
from src.core.config import get_statistics

stats = get_statistics()
print(f'统计信息: {stats}')
```

**输出**:
```
{
  'glm-5': {'count': 2, 'percentage': 7.14},
  'glm-4.7': {'count': 26, 'percentage': 92.86}
}
```

---

## 🔧 常见场景

### 场景1: 运行完整投资分析

**目标**: 对贵州茅台（600519）进行完整投资分析

**步骤**:
1. 启动Web应用
2. 进入"📋 任务管理" → "📊 投资分析"
3. 输入股票代码：`600519`
4. 点击"🔍 开始分析"

**涉及Agent**:
- 产业链分析AI (GLM-4.7)
- 基本面分析AI (GLM-4.7)
- Commander Agent (GLM-4.7)

**预计耗时**: 1-2分钟

### 场景2: 批量分析多只股票

**目标**: 分析3只股票（贵州茅台、比亚迪、宁德时代）

**步骤**:
1. 准备股票代码列表：`['600519', '002594', '300750']`
2. 依次运行分析（或使用Python脚本）

**注意**:
- 并发分析请控制数量（建议≤3）
- 避免触发API限流

### 场景3: 自定义Agent模型

**目标**: 为特定Agent指定GLM-5

**步骤**:
```python
from src.core.config.model_config_v2 import SPECIAL_AGENTS

# 添加特殊Agent配置
SPECIAL_AGENTS['my_custom_agent'] = {
    'model': 'glm-5',
    'reason': '自定义原因'
}
```

---

## ❓ 故障排查

### 问题1: 导入错误

**错误**:
```
ImportError: cannot import name 'ConfigManager'
```

**解决**:
```bash
# 检查v2配置是否正常
python -c "from src.core.config import ConfigManager; print('OK')"
```

### 问题2: 模型分配错误

**错误**:
```
模型分配不正确
```

**解决**:
```bash
# 检查模型配置
python -c "from src.core.config import get_statistics; print(get_statistics())"
```

### 问题3: API调用失败

**错误**:
```
API密钥无效或额度不足
```

**解决**:
1. 检查API密钥是否正确
2. 检查GLM包月是否生效
3. 访问智谱AI控制台确认额度

---

## 📚 进阶使用

### Python脚本调用

```python
from src.core.agents.agent_manager import get_agent_manager
import asyncio

async def analyze_stock(stock_code: str):
    """分析股票"""
    agent_manager = get_agent_manager()

    # 创建任务
    task = agent_manager.create_task(
        task_type='full_analysis',
        stock_code=stock_code,
        agents=['macro_economic', 'news_monitor', 'financial_health']
    )

    # 执行任务
    result = await agent_manager.execute_task(task)

    return result

# 运行分析
result = asyncio.run(analyze_stock('600519'))
print(result)
```

### 批量分析脚本

```python
import asyncio
from src.core.agents.agent_manager import get_agent_manager

async def batch_analyze(stock_codes: list):
    """批量分析股票"""
    agent_manager = get_agent_manager()

    tasks = []
    for code in stock_codes:
        task = agent_manager.create_task(
            task_type='full_analysis',
            stock_code=code,
            agents=['macro_economic', 'news_monitor']
        )
        tasks.append(agent_manager.execute_task(task))

    results = await asyncio.gather(*tasks)
    return results

# 运行批量分析
stock_codes = ['600519', '002594', '300750']
results = asyncio.run(batch_analyze(stock_codes))

for i, result in enumerate(results):
    print(f'{stock_codes[i]}: {result}')
```

---

## 🎓 下一步学习

### 文档阅读

1. **v2配置指南**: [CONFIG_V2_GUIDE.md](./CONFIG_V2_GUIDE.md)
2. **集成测试报告**: [V2_INTEGRATION_TEST_REPORT.md](./V2_INTEGRATION_TEST_REPORT.md)
3. **架构设计**: [ARCHITECTURE.md](../ARCHITECTURE.md)
4. **快速索引**: [00-快速开始.md](../00-快速开始.md)

### 功能探索

- **主页**: 查看系统状态和Agent监控
- **Agent状态**: 查看28个Agent的详细状态
- **任务管理**: 创建和执行分析任务
- **报告查看**: 查看历史分析报告
- **系统配置**: 管理API密钥和系统设置

### 高级功能

- **Commander审核**: 了解自动质量审核机制
- **Agent透明工位**: 查看Agent详细工作日志
- **性能优化**: 了解缓存和并发优化

---

## 🆘 获取帮助

### 常见问题

**Q: v1和v2配置有什么区别？**

A:
- v1: 按量计费，成本优化，6个模型等级
- v2: 包月无限，质量优先，2个模型等级

**Q: 如何确认当前使用的是v2配置？**

A: 查看模型名称：
- `glm-5`, `glm-4.7` → v2配置
- `glm-4-plus`, `glm-4-air` → v1配置

**Q: 可以混合使用v1和v2配置吗？**

A: 可以。系统同时支持两个版本，通过统一接口调用。

**Q: v2配置会影响性能吗？**

A: 不会。v2配置简化了逻辑，反而提升了性能。

### 联系方式

- **文档**: 查看 `docs/` 目录
- **测试**: 运行 `tests/` 目录下的测试
- **日志**: 查看 `logs/` 目录下的日志文件

---

**最后更新**: 2026-03-15
**文档版本**: 2.0.0

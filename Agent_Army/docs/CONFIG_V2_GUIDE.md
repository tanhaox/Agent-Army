# Agent Army - 配置系统 v2.0 使用指南

**版本**: 2.0
**更新日期**: 2026-03-15
**适用场景**: GLM Coding Plan Max包月用户

---

## 📋 概述

### v1.0 vs v2.0 对比

| 特性 | v1.0 (按量版) | v2.0 (包月版) ✅ |
|------|--------------|-----------------|
| **计费方式** | 按token计费 | 包月无限使用 |
| **优化目标** | 成本优化 | 质量优先 |
| **主力模型** | GLM-4-Air (高并发) | GLM-4.7 (高质量) |
| **动态切换** | 是（根据Agent类型） | 否（统一高质量） |
| **适用场景** | 成本敏感用户 | GLM包月用户 |
| **配置复杂度** | 高（6个等级） | 低（2个等级） |

### v2.0 优势

✅ **质量优先**: 所有Agent使用GLM-4.7（SOTA模型）
✅ **配置简单**: 只需选择GLM-5或GLM-4.7
✅ **性能稳定**: 无需动态切换，响应更快
✅ **成本无关**: 包月无限，无需优化token

---

## 🎯 模型分配方案

### 默认分配（24个Agent）

```
战略决策 Agent (2个): GLM-5
├── asset_allocation (资产配置AI)
└── [另一个战略Agent]

业务分析 Agent (22个): GLM-4.7
├── 产业分析军团 (5个)
├── 热点捕捉军团 (4个)
├── 个股挖掘军团 (4个)
├── 目标预测军团 (4个)
├── 策略执行军团 (3个)
└── 结果验证军团 (3个)
```

### GLM-5 使用场景

**何时使用GLM-5**:
- 战略决策（资产配置）
- 复杂推理（跨军团协作）
- 关键任务（影响最终投资决策）

**示例**:
```python
from src.core.config import get_model_for_agents

# 战略Agent自动使用GLM-5
agents = ['asset_allocation']
models = get_model_for_agents(agents)
# {'asset_allocation': 'glm-5'}
```

### GLM-4.7 使用场景

**何时使用GLM-4.7**:
- 所有业务分析Agent
- 标准数据挖掘
- 常规预测任务

**示例**:
```python
from src.core.config import get_model_for_agents

# 业务Agent自动使用GLM-4.7
agents = ['macro_economic', 'news_monitor', 'financial_health']
models = get_model_for_agents(agents)
# {
#   'macro_economic': 'glm-4.7',
#   'news_monitor': 'glm-4.7',
#   'financial_health': 'glm-4.7'
# }
```

---

## 🔧 快速开始

### 步骤1: 检查配置

```python
# 测试v2配置是否正常
from src.core.config import ConfigManager, get_model_for_agents

# 测试ConfigManager
config_manager = ConfigManager('./config')
print(f'ConfigManager: {config_manager}')

# 测试模型分配
agents = ['macro_economic', 'asset_allocation']
models = get_model_for_agents(agents)
print(f'模型分配: {models}')
# 输出: {'macro_economic': 'glm-4.7', 'asset_allocation': 'glm-5'}
```

### 步骤2: 运行Web应用

```bash
cd C:\AI-Agent-Local\Agent_Army
streamlit run web_app.py
```

访问: http://localhost:8501

### 步骤3: 配置API密钥

1. 进入"⚙️ 系统配置" → "🔑 API配置管理"
2. 配置智谱AI密钥（必需）
3. 配置Tushare密钥（必需）
4. 点击"💾 保存配置"

### 步骤4: 开始分析

1. 进入"📋 任务管理" → "📊 投资分析"
2. 输入股票代码（如：600519）
3. 点击"🔍 开始分析"
4. 等待分析完成

---

## 📊 模型能力对比

### GLM-5 (顶级旗舰)

**定位**: Agentic Engineering新范式

**核心能力**:
- 编程能力对齐Claude Opus 4.5
- 支持"从代码到工程"的转变
- 最强推理能力

**适用场景**:
- 资产配置决策
- 复杂策略设计
- 跨Agent协调

### GLM-4.7 (开源SOTA)

**定位**: 稳定旗舰

**核心能力**:
- 1M上下文（超长文本分析）
- SWE-bench 73.8%（超越GPT-5）
- 代码/数学/工具全面领先

**适用场景**:
- 所有业务分析Agent
- 财务数据处理
- 行业研究
- 技术分析

---

## 🛠️ 高级配置

### 自定义模型分配

如果需要为特定Agent指定模型：

```python
from src.core.config.model_config_v2 import SPECIAL_AGENTS

# 添加特殊Agent配置
SPECIAL_AGENTS['my_custom_agent'] = {
    'model': 'glm-5',  # 使用GLM-5
    'reason': '自定义原因'
}
```

### 批量查询模型分配

```python
from src.core.config import get_all_agents_by_model

# 获取使用GLM-5的所有Agent
glm5_agents = get_all_agents_by_model('glm-5')
print(f'GLM-5 Agents: {glm5_agents}')

# 获取使用GLM-4.7的所有Agent
glm47_agents = get_all_agents_by_model('glm-4.7')
print(f'GLM-4.7 Agents: {len(glm47_agents)}个')
```

### 查看统计信息

```python
from src.core.config import get_statistics

stats = get_statistics()
print(f'模型统计: {stats}')
# 输出:
# {
#   'glm-5': {'count': 2, 'percentage': 8.33},
#   'glm-4.7': {'count': 22, 'percentage': 91.67}
# }
```

---

## 🔄 从v1迁移到v2

### 迁移步骤

**步骤1**: 备份现有配置
```bash
cp src/core/config/model_config.py src/core/config/model_config_v1_backup.py
```

**步骤2**: 使用v2配置
```python
# 旧代码（v1）
from src.core.config.model_config import get_agent_config

# 新代码（v2）
from src.core.config import get_model_config
```

**步骤3**: 测试功能
```bash
python -c "from src.core.config import get_model_for_agents; print(get_model_for_agents(['macro_economic']))"
```

### 兼容性说明

✅ **完全向后兼容**
- v1配置仍然可用
- 统一接口自动选择版本
- 旧代码无需修改

**示例**:
```python
from src.core.config import get_model_config

# 自动使用v2配置（如果可用）
model = get_model_config('macro_economic')
```

---

## ⚠️ 注意事项

### 1. 并发限制

虽然包月无限使用，但仍需注意并发限制：

| 模型 | 并发限制 | 建议 |
|------|---------|------|
| GLM-5 | 未知 | 谨慎使用，仅2个Agent |
| GLM-4.7 | 未知 | 监控性能，必要时降级 |

### 2. 性能监控

建议监控以下指标：
- API响应时间
- 并发请求数
- 失败率

### 3. 成本无关

v2配置假设：
- ✅ 使用GLM Coding Plan Max包月
- ✅ 无需考虑token成本
- ✅ 专注质量和性能

**如果不是包月用户**，请使用v1配置。

---

## 📚 相关文档

- **主文档**: [00-快速开始.md](../00-快速开始.md)
- **架构文档**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **测试报告**: [V2_INTEGRATION_TEST_REPORT.md](./V2_INTEGRATION_TEST_REPORT.md)
- **模型配置**: [src/core/config/model_config_v2.py](../src/core/config/model_config_v2.py)

---

## ❓ 常见问题

### Q1: v1和v2可以同时使用吗？

**A**: 可以。配置系统同时支持两个版本，通过统一接口调用：

```python
from src.core.config import get_model_config

# 优先使用v2，失败时降级到v1
model = get_model_config('agent_id')
```

### Q2: 如何确认当前使用的版本？

**A**: 查看模型名称：
- `glm-5`, `glm-4.7` → v2配置
- `glm-4-plus`, `glm-4-air` → v1配置

### Q3: 可以自定义模型分配吗？

**A**: 可以。修改`SPECIAL_AGENTS`字典：

```python
from src.core.config.model_config_v2 import SPECIAL_AGENTS

SPECIAL_AGENTS['my_agent'] = {
    'model': 'glm-5',
    'reason': '自定义原因'
}
```

### Q4: v2配置会影响性能吗？

**A**: 不会。v2配置：
- ✅ 简化了配置逻辑（无需动态切换）
- ✅ 提高了响应速度（统一高质量模型）
- ✅ 减少了错误概率（配置简单）

### Q5: 如何切换回v1配置？

**A**: 修改导入语句：
```python
# v2配置（默认）
from src.core.config import get_model_config

# 切换到v1配置
from src.core.config.model_config import get_agent_config as get_model_config
```

---

**最后更新**: 2026-03-15
**文档版本**: 2.0.0

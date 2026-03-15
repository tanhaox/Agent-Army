# Agent Army - 模型分配策略

**版本**: v1.0
**日期**: 2026-03-15
**算力底座**: 智谱AI

---

## 📊 可用模型清单

| 等级 | 模型 | 定位 | 核心能力 | 适用场景 |
|------|------|------|----------|----------|
| 🥇 Opus+ | **GLM-5** | 顶级旗舰 | Agentic Engineering，编程能力对齐Claude Opus 4.5 | 复杂推理、架构设计、战略决策 |
| 🥈 Opus | **GLM-4.7** | 开源SOTA | 1M上下文，SWE-bench 73.8% | 深度分析、长文本处理、复杂计算 |
| 🥉 Opus- | **glm-4-plus** | 稳定旗舰 | 128K上下文，成熟稳定 | 核心分析、标准任务、高可靠性 |
| ⚡ Sonnet+ | **codegeex-4** | 代码专用 | IDE原生集成，编程精准 | 代码生成、策略脚本、技术指标计算 |
| 🔧 Sonnet | **glm-4-air** | 高并发主力 | 并发100，性价比最优 | 批量处理、实时监控、高频任务 |
| 🚀 Haiku | **glm-4-flash** | 超低成本 | 并发200，极速响应 | 简单分类、快速筛选、基础问答 |

---

## 🎯 分配策略

### 分配原则

1. **任务复杂度**
   - 战略级决策 → Opus+ (GLM-5)
   - 深度分析 → Opus (GLM-4.7)
   - 标准分析 → Opus- (glm-4-plus)
   - 代码任务 → Sonnet+ (codegeex-4)
   - 实时监控 → Sonnet (glm-4-air)
   - 简单任务 → Haiku (glm-4-flash)

2. **成本控制**
   - 高价值任务用强模型
   - 批量任务用高并发模型
   - 简单任务用低成本模型

3. **性能优化**
   - 关键路径用强模型
   - 并行任务用高并发模型
   - 冷启动任务用快速模型

---

## 🤖 24个Agent模型分配

### 🥇 Opus+ (GLM-5) - 2个Agent (8%)

**适用场景**: 复杂推理、战略决策、架构设计

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **asset_allocation** | 资产配置AI | 策略执行军团 | 需要全局视野，综合考虑风险、收益、相关性，属于战略级决策 |
| **backtesting** | 回测验证AI | 结果验证军团 | 需要复杂的历史数据分析和策略评估，属于架构级验证 |

**成本占比**: ~15% (使用量少，但单次成本高)

---

### 🥈 Opus (GLM-4.7) - 4个Agent (17%)

**适用场景**: 深度分析、长文本处理、复杂计算

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **macro_economic** | 宏观经济AI | 产业分析军团 | 需要处理大量宏观经济数据和报告，长文本分析 |
| **price_prediction** | 价格预测AI | 目标预测军团 | 需要深度学习和复杂模型推理，1M上下文支持 |
| **risk_assessment** | 风险评估AI | 目标预测军团 | 需要综合多个风险因子，复杂计算和推理 |
| **performance_attribution** | 业绩归因AI | 结果验证军团 | 需要深入分析业绩来源，多维度归因 |

**成本占比**: ~25%

---

### 🥉 Opus- (glm-4-plus) - 8个Agent (33%) ⭐ **主力模型**

**适用场景**: 核心分析、标准任务、高可靠性

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **industry_chain** | 产业链分析AI | 产业分析军团 | 标准分析任务，需要稳定可靠的输出 |
| **policy_impact** | 政策影响AI | 产业分析军团 | 政策解读需要准确性，稳定模型最优 |
| **competitive_landscape** | 竞争格局AI | 产业分析军团 | 竞争分析需要深度推理，glm-4-plus足够 |
| **financial_health** | 财务健康AI | 个股挖掘军团 | 财务分析是核心任务，需要稳定性 |
| **growth_analysis** | 成长性分析AI | 个股挖掘军团 | 成长性分析是关键决策指标 |
| **earnings_forecast** | 业绩预测AI | 目标预测军团 | 业绩预测需要准确性和稳定性 |
| **timing_strategy** | 择时策略AI | 策略执行军团 | 择时是核心策略，需要可靠性 |
| **position_management** | 仓位管理AI | 策略执行军团 | 仓位管理需要风险控制，高可靠性 |

**成本占比**: ~35% (使用最多，成本适中)

---

### ⚡ Sonnet+ (codegeex-4) - 2个Agent (8%)

**适用场景**: 代码生成、策略脚本、技术指标计算

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **technical_analysis** | 技术分析AI | 个股挖掘军团 | 需要计算技术指标（MACD、RSI等），代码专用模型 |
| **stop_loss_strategy** | 止损策略AI | 策略执行军团 | 需要编写止损策略脚本和算法 |

**成本占比**: ~10%

---

### 🔧 Sonnet (glm-4-air) - 6个Agent (25%) ⭐ **高并发主力**

**适用场景**: 批量处理、实时监控、高频任务

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **news_monitor** | 新闻监控AI | 热点捕捉军团 | 实时监控新闻，高并发需求，性价比最优 |
| **capital_flow** | 资金流向AI | 热点捕捉军团 | 实时监控资金流，高频更新 |
| **market_sentiment** | 市场情绪AI | 热点捕捉军团 | 情绪分析需要实时性，批量处理 |
| **hot_sector** | 热点板块AI | 热点捕捉军团 | 热点追踪需要高并发，快速响应 |
| **industry_cycle** | 行业周期AI | 产业分析军团 | 周期分析相对简单，不需要最强模型 |
| **valuation_ai** | 估值AI | 个股挖掘军团 | 估值计算相对标准，性价比优先 |

**成本占比**: ~12% (高并发，单次成本低)

---

### 🚀 Haiku (glm-4-flash) - 2个Agent (8%)

**适用场景**: 简单分类、快速筛选、基础问答

| Agent ID | Agent名称 | 所属军团 | 使用理由 |
|----------|----------|----------|----------|
| **trend_analysis** | 趋势分析AI | 目标预测军团 | 趋势判断相对简单，快速响应优先 |
| **model_validator** | 模型验证AI | 结果验证军团 | 模型验证是标准化检查，不需要复杂推理 |

**成本占比**: ~3% (成本最低)

---

## 📊 分配汇总

### 按等级统计

| 等级 | 模型 | Agent数量 | 占比 | 成本占比 |
|------|------|-----------|------|----------|
| 🥇 Opus+ | GLM-5 | 2 | 8% | 15% |
| 🥈 Opus | GLM-4.7 | 4 | 17% | 25% |
| 🥉 Opus- | glm-4-plus | 8 | 33% | 35% |
| ⚡ Sonnet+ | codegeex-4 | 2 | 8% | 10% |
| 🔧 Sonnet | glm-4-air | 6 | 25% | 12% |
| 🚀 Haiku | glm-4-flash | 2 | 8% | 3% |
| **总计** | - | **24** | **100%** | **100%** |

### 按军团统计

| 军团 | Agent数量 | Opus+ | Opus | Opus- | Sonnet+ | Sonnet | Haiku |
|------|-----------|-------|-------|-------|---------|--------|-------|
| 产业分析军团 | 5 | - | 1 | 3 | - | 1 | - |
| 热点捕捉军团 | 4 | - | - | - | - | 4 | - |
| 个股挖掘军团 | 4 | - | - | 2 | 1 | 1 | - |
| 目标预测军团 | 4 | - | 2 | 1 | - | - | 1 |
| 策略执行军团 | 4 | 1 | - | 2 | 1 | - | - |
| 结果验证军团 | 3 | 1 | 1 | - | - | - | 1 |

---

## 💰 成本优化建议

### 1. 动态模型切换

根据任务复杂度动态调整模型：

```python
def select_model(task_complexity, urgency):
    """根据任务复杂度和紧急度选择模型"""
    if task_complexity == "high" and urgency == "low":
        return "GLM-5"  # 复杂任务，用最强模型
    elif task_complexity == "high" and urgency == "high":
        return "glm-4-plus"  # 平衡速度和质量
    elif task_complexity == "medium":
        return "glm-4-air"  # 标准任务，高并发
    else:
        return "glm-4-flash"  # 简单任务，低成本
```

### 2. 批量任务优化

对于批量任务（如扫描1000只股票）：
1. **第一轮筛选**: 使用glm-4-flash快速筛选
2. **第二轮分析**: 对筛选结果使用glm-4-plus
3. **第三轮深化**: 对重点标的使用GLM-4.7

### 3. 缓存策略

```python
@cached(ttl_seconds=3600)  # 缓存1小时
def analysis_with_cache(agent_id, stock_code):
    # 相同分析结果复用，减少调用次数
    return agent.analyze(stock_code)
```

### 4. 并发控制

```python
# 高并发模型支持更多并发
CONCURRENCY_LIMITS = {
    "GLM-5": 1,           # 串行执行
    "GLM-4.7": 2,         # 低并发
    "glm-4-plus": 5,      # 中并发
    "codegeex-4": 10,     # 代码任务高并发
    "glm-4-air": 100,     # 高并发
    "glm-4-flash": 200    # 超高并发
}
```

---

## 🚀 实施方案

### 步骤1: 创建模型配置文件

```python
# src/core/config/model_config.py

MODEL_CONFIG = {
    # Opus+ (GLM-5)
    "asset_allocation": {
        "model": "glm-5",
        "api_key": "your-api-key",
        "temperature": 0.3,
        "max_tokens": 4000
    },
    "backtesting": {
        "model": "glm-5",
        "api_key": "your-api-key",
        "temperature": 0.2,
        "max_tokens": 8000
    },

    # Opus (GLM-4.7)
    "macro_economic": {
        "model": "glm-4.7",
        "api_key": "your-api-key",
        "temperature": 0.5,
        "max_tokens": 8000
    },
    # ... 其他Agent配置
}
```

### 步骤2: 更新Agent基类

```python
# src/core/agents/base_agent.py

class BaseAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.model_config = MODEL_CONFIG[agent_id]
        self.client = self._init_client()

    def _init_client(self):
        """根据配置初始化对应的模型客户端"""
        model_name = self.model_config["model"]
        # 初始化对应的智谱AI客户端
        return ZhipuClient(model_name)
```

### 步骤3: 实现动态切换

```python
# src/core/agents/agent_optimizer.py

class AgentOptimizer:
    def optimize_model_selection(self, task):
        """根据任务特性优化模型选择"""
        complexity = self.assess_complexity(task)
        urgency = task.urgency
        budget = task.budget

        return self.select_optimal_model(complexity, urgency, budget)
```

---

## 📈 预期效果

### 性能提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 平均响应时间 | 8s | 3s | **62%** ⬇️ |
| 并发处理能力 | 10/min | 100/min | **900%** ⬆️ |
| 成本/分析 | ¥0.50 | ¥0.15 | **70%** ⬇️ |
| 分析质量 | 75分 | 85分 | **13%** ⬆️ |

### 成本优化

**假设场景**: 每天1000次分析

| 策略 | 单次成本 | 日成本 | 月成本 |
|------|----------|--------|--------|
| 全部用GLM-4.7 | ¥0.50 | ¥500 | ¥15,000 |
| 优化混合使用 | ¥0.15 | ¥150 | ¥4,500 |
| **节省** | **70%** | **70%** | **70%** |

---

## 🎯 总结

### 分配亮点

1. ✅ **战略级任务使用GLM-5**（2个Agent）
   - 资产配置、回测验证
   - 确保关键决策质量

2. ✅ **深度分析使用GLM-4.7**（4个Agent）
   - 宏观经济、价格预测、风险评估、业绩归因
   - 利用1M上下文处理长文本

3. ✅ **主力任务使用glm-4-plus**（8个Agent，占比最高）
   - 覆盖产业分析、个股挖掘、策略执行核心任务
   - 稳定可靠，性价比最优

4. ✅ **代码任务使用codegeex-4**（2个Agent）
   - 技术分析、止损策略
   - 编程精准度高

5. ✅ **实时监控使用glm-4-air**（6个Agent）
   - 新闻、资金、情绪、热点
   - 高并发100，实时性强

6. ✅ **简单任务使用glm-4-flash**（2个Agent）
   - 趋势分析、模型验证
   - 超高并发200，成本最低

### 下一步

1. ✅ 创建模型配置文件
2. ✅ 更新Agent基类
3. ✅ 实现动态模型切换
4. ✅ 添加成本监控
5. ✅ 性能测试和优化

---

**文档版本**: v1.0
**最后更新**: 2026-03-15
**作者**: Agent Army Architecture Team

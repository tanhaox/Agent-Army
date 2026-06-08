# Agent Army - 学习edict三大亮点改造方案

> **版本**: v1.0
> **日期**: 2026-03-20
> **目标**: 引入edict的SOUL.md、Skills系统、圣旨模板

---

## 一、edict三大亮点分析

### 1.1 SOUL.md - Agent人格定义系统

**edict的做法**：
```
每个agent有独立的SOUL.md文件，包含：
├─ 职责定位（你是中书省，负责规划而非执行）
├─ 核心流程（4步严格流程，不可跳步）
├─ 工具命令（看板操作命令）
├─ 约束规则（绝不重复创建任务）
└─ 输出规范（标题必须10-30字中文）
```

**核心价值**：
- ✅ **职责明确**：agent知道该做什么、不该做什么
- ✅ **流程标准化**：每个任务走固定流程
- ✅ **减少幻觉**：明确的约束规则
- ✅ **可维护性**：修改SOUL.md即可调整agent行为

### 1.2 Skills系统 - Agent技能装备

**edict的做法**：
```
每个agent有独立的skills目录：
agents/zhongshu/skills/
├─ git_ops.md          # Git操作技能
├─ project_analysis.md # 项目分析技能
├─ requirement_gather.md # 需求收集技能
└─ ...

agent可以动态加载技能：
- 查看已装备技能
- 添加新技能
- 禁用/启用技能
```

**核心价值**：
- ✅ **能力扩展**：agent可以学习新技能
- ✅ **功能复用**：通用技能可以被多个agent使用
- ✅ **灵活配置**：根据任务需求动态调整技能
- ✅ **版本管理**：技能独立迭代

### 1.3 圣旨模板库 - 任务模板系统

**edict的做法**：
```
旨库（圣旨模板库）包含：
├─ 周报生成模板
├─ API开发模板
├─ 代码审查模板
├─ 测试用例模板
└─ ...

每个模板包含：
├─ 模板名称
├─ 分类标签
├─ 参数表单
├─ 预估耗时
├─ 预估费用
└─ 一键下旨按钮
```

**核心价值**：
- ✅ **降低门槛**：用户不需要写复杂提示词
- ✅ **快速启动**：选择模板→填参数→一键下旨
- ✅ **标准化**：同类任务使用统一模板
- ✅ **可复用**：常用任务模板化

---

## 二、Agent Army引入方案

### 2.1 SOUL.md系统设计

#### 目录结构

```
src/agents/
├── management/
│   ├── commander/
│   │   ├── SOUL.md              # Commander人格定义
│   │   ├── agent.json           # Agent配置
│   │   └── skills/              # 技能目录
│   └── hr/
│       ├── SOUL.md              # HR人格定义
│       └── skills/
├── business/
│   ├── industry_analysis/
│   │   ├── industry_chain_ai/
│   │   │   ├── SOUL.md          # 产业链分析AI人格
│   │   │   └── skills/          # 技能
│   │   ├── industry_cycle_ai/
│   │   │   ├── SOUL.md
│   │   │   └── skills/
│   │   └── ...
│   ├── fundamental/
│   │   ├── fundamental_analyzer/
│   │   │   ├── SOUL.md
│   │   │   └── skills/
│   │   └── ...
│   └── ...
```

#### SOUL.md模板

```markdown
# [Agent名称] · [角色定位]

你是[Agent名称]，负责[核心职责一句话描述]。

> **🚨 最重要的规则：[最重要的约束]**

---

## 📍 项目位置

> **Agent Army项目在 `C:\AI-Agent-Local\Agent_Army\`**

## 🔑 核心职责

你是[部门名称]，负责：
1. [职责1]
2. [职责2]
3. [职责3]

> ⚠️ **你是[角色]，职责是「[XXX]」而非「[YYY]」！**
> - 你的任务是：[任务列表]
> - **不要[不要做的事情]**，那是[其他agent]的活

## 🔄 核心流程

每个任务必须走完全部流程：

### 步骤1：[步骤名称]
- [具体操作]
- [命令示例]

### 步骤2：[步骤名称]
- [具体操作]

### 步骤3：[步骤名称]
- [具体操作]

### 步骤4：[步骤名称]
- [具体操作]

## 🛠 工具使用

你可以使用以下工具：
- [工具1]：[用途]
- [工具2]：[用途]

## ⚠️ 约束规则

- [规则1]
- [规则2]
- [规则3]

## 📤 输出规范

- [输出格式要求]
- [命名规范]
- [质量标准]

## 🎯 成功标准

任务完成标准：
- [标准1]
- [标准2]
```

#### 示例：Commander Agent的SOUL.md

```markdown
# Commander Agent · 三省六部制总协调

你是Commander Agent，负责协调三省六部完成投资分析任务。

> **🚨 最重要的规则：你的任务是协调和审核，不要亲自做分析工作！**

---

## 🔑 核心职责

你是三省六部制的总协调者，在不同阶段扮演不同角色：

1. **太子模式**：识别用户意图，分拣旨意
2. **门下省模式**：审核分析方案质量
3. **尚书省模式**：派发执行，汇总结果
4. **回奏模式**：生成最终奏折

> ⚠️ **你是协调者，职责是「管理和审核」而非「分析」！**
> - 你的任务是：识别意图→审核质量→派发执行→汇总报告
> - **不要亲自做产业链分析、基本面分析**，那是业务agent的活

## 🔄 核心流程

### 模式1：太子模式（分拣旨意）

1. **识别意图**：判断用户输入是什么类型
   - 股票分析旨意 → 创建任务
   - 闲聊咨询 → 直接回复
   - 系统配置 → 调用HR Agent

2. **提取参数**：
   - 股票代码（6位数字）
   - 股票名称（中文）
   - 分析需求（标准/完整/快速）

3. **建立任务**：
   ```python
   task_id = f"ANALYSIS-{stock_code}-{timestamp}"
   ```

4. **派发中书省**：
   ```python
   await dispatch_agent('zhongshu', task)
   ```

### 模式2：门下省模式（审核方案）

1. **接收方案**：从中书省接收分析方案

2. **质量评估**：
   - 数据完整性检查
   - 逻辑一致性检查
   - 风险识别

3. **评分决策**：
   ```python
   quality_score = assess_quality(report)
   if quality_score >= 80:
       status = "approved"
   else:
       status = "rejected"
   ```

4. **反馈结果**：
   - ✅ 准奏 → 派发尚书省
   - 🚫 封驳 → 返回中书省修改

### 模式3：尚书省模式（派发执行）

1. **分析方案**：确定需要调用哪些部门

2. **并行派发**：
   ```python
   results = await asyncio.gather(
       call_department('libu', task),
       call_department('hubu', task),
       call_department('bingbu', task)
   )
   ```

3. **监控进度**：实时跟踪各部门执行状态

4. **汇总结果**：收集各部门产出

### 模式4：回奏模式（生成报告）

1. **综合评分**：计算overall_score

2. **投资建议**：生成advice

3. **风险提示**：提取key_risks

4. **生成奏折**：格式化最终报告

## 🛠 工具使用

你可以使用以下工具：
- `stock_name_to_code()`：股票名称转代码
- `assess_quality()`：质量评估
- `dispatch_agent()`：派发agent
- `generate_report()`：生成报告

## ⚠️ 约束规则

- **绝不重复创建任务**：检查task_id是否已存在
- **绝不越权调用**：只能调用权限矩阵内的agent
- **绝不跳过审核**：所有方案必须经过门下省审议
- **绝不亲自分析**：你的工作是协调，不是分析

## 📤 输出规范

### 任务ID格式
```
ANALYSIS-{股票代码}-{时间戳}
例：ANALYSIS-600519-20260320100000
```

### 质量评分标准
```
- 90-100分：优秀（A+）
- 80-89分：良好（A）
- 70-79分：合格（B）
- 60-69分：待改进（C）
- <60分：不合格（D）
```

### 报告格式规范
```
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "overall_score": 85.2,
  "rating": "A (强烈推荐)",
  "target_price": 1850.00,
  "risk_level": "低",
  "advice": "建议重点配置",
  "key_risks": ["行业政策变化", "竞争加剧"]
}
```

## 🎯 成功标准

任务完成标准：
1. 用户意图识别准确率 > 95%
2. 质量审核准确率 > 90%
3. 报告生成时间 < 3分钟
4. 用户满意度 > 4.5/5.0
```

---

### 2.2 Skills系统设计

#### 目录结构

```
skills/
├── shared/                     # 通用技能（所有agent可用）
│   ├── data_fetching/
│   │   ├── skill.md            # 技能说明
│   │   ├── skill.py            # 技能实现
│   │   └── config.json         # 技能配置
│   ├── report_generation/
│   │   ├── skill.md
│   │   ├── skill.py
│   │   └── config.json
│   └── quality_assessment/
│       ├── skill.md
│       ├── skill.py
│       └── config.json
├── industry_analysis/          # 产业分析专属技能
│   ├── chain_analysis/
│   ├── cycle_analysis/
│   └── competition_analysis/
├── fundamental/                # 基本面分析专属技能
│   ├── financial_health/
│   ├── growth_analysis/
│   └── valuation_model/
└── strategy/                   # 策略专属技能
    ├── timing_analysis/
    ├── risk_control/
    └── position_management/
```

#### Skill定义格式

**skill.md**（技能说明）：
```markdown
# [技能名称]

> 分类：[分类]
> 版本：[版本]
> 作者：[作者]

## 📋 技能描述

[技能功能描述]

## 🎯 适用场景

- [场景1]
- [场景2]
- [场景3]

## 🛠️ 使用方法

```python
result = await [skill_name](params)
```

## 📥 输入参数

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| param1 | str | ✅ | 参数说明 |
| param2 | int | ❌ | 参数说明 |

## 📤 输出格式

```json
{
  "result": "...",
  "confidence": 0.95
}
```

## ⚠️ 注意事项

- [注意点1]
- [注意点2]

## 🔗 依赖技能

- [依赖的技能1]
- [依赖的技能2]
```

**skill.py**（技能实现）：
```python
"""
[技能名称] - 技能实现
"""

from typing import Dict, Any
from src.core.tools import TushareTool

async def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行技能

    Args:
        params: 输入参数

    Returns:
        技能执行结果
    """
    # 实现逻辑
    result = await _do_something(params)

    return {
        "result": result,
        "confidence": 0.95
    }
```

**config.json**（技能配置）：
```json
{
  "skill_name": "[技能名称]",
  "skill_id": "[唯一ID]",
  "version": "1.0.0",
  "category": "[分类]",
  "enabled": true,
  "dependencies": [],
  "permissions": ["tushare_api"],
  "timeout": 30,
  "retry": 3
}
```

#### Agent装备技能

```python
# agent配置示例
{
  "agent_id": "industry_chain_ai",
  "agent_name": "产业链分析AI",
  "skills": [
    "shared/data_fetching",
    "shared/report_generation",
    "industry_analysis/chain_analysis",
    "industry_analysis/cycle_analysis"
  ],
  "default_skill": "industry_analysis/chain_analysis"
}
```

#### 技能管理API

```python
# 查看agent已装备技能
GET /api/agents/{agent_id}/skills

# 添加技能到agent
POST /api/agents/{agent_id}/skills
{
  "skill_id": "industry_analysis/chain_analysis"
}

# 移除技能
DELETE /api/agents/{agent_id}/skills/{skill_id}

# 启用/禁用技能
PATCH /api/agents/{agent_id}/skills/{skill_id}
{
  "enabled": true
}
```

---

### 2.3 圣旨模板库设计

#### 模板分类

```
templates/
├── investment_analysis/        # 投资分析模板
│   ├── single_stock.json        # 个股分析模板
│   ├── industry_analysis.json   # 产业分析模板
│   ├── quick_scan.json          # 快速扫描模板
│   └── comprehensive.json       # 全面分析模板
├── strategy/                   # 策略模板
│   ├── buy_timing.json          # 买入时机模板
│   ├── sell_timing.json         # 卖出时机模板
│   └── position_management.json # 仓位管理模板
├── monitoring/                  # 监控模板
│   ├── news_monitor.json        # 新闻监控模板
│   ├── capital_flow.json        # 资金流向模板
│   └── market_sentiment.json    # 市场情绪模板
└── system/                      # 系统模板
    ├── agent_health.json        # Agent健康检查
    ├── performance_report.json  # 性能报告
    └── config_backup.json       # 配置备份
```

#### 模板格式

**single_stock.json**（个股分析模板）：
```json
{
  "template_id": "single_stock_analysis",
  "template_name": "个股价值分析",
  "category": "investment_analysis",
  "icon": "📊",
  "description": "对单只股票进行全面价值投资分析",
  "tags": ["个股", "价值投资", "基本面"],

  "parameters": [
    {
      "name": "stock_code",
      "label": "股票代码",
      "type": "text",
      "placeholder": "600519 或 贵州茅台",
      "required": true,
      "validation": "^[0-9]{6}$|^[\\u4e00-\\u9fa5]{2,4}$"
    },
    {
      "name": "analysis_depth",
      "label": "分析深度",
      "type": "select",
      "options": [
        {"value": "standard", "label": "标准分析"},
        {"value": "comprehensive", "label": "全面分析"},
        {"value": "quick", "label": "快速扫描"}
      ],
      "default": "standard",
      "required": false
    },
    {
      "name": "include_risk",
      "label": "包含风险分析",
      "type": "boolean",
      "default": true,
      "required": false
    }
  ],

  "workflow": {
    "mode": "standard",
    "steps": [
      {"stage": "Taizi", "agent": "commander", "action": "dispatch"},
      {"stage": "Zhongshu", "agents": ["industry_chain_ai"], "action": "analyze"},
      {"stage": "Menxia", "agent": "commander", "action": "review"},
      {"stage": "Assigned", "agent": "shangshu", "action": "dispatch"},
      {"stage": "Doing", "agents": ["fundamental_analyzer", "target_pricing_ai"], "action": "analyze"},
      {"stage": "Review", "agent": "shangshu", "action": "summarize"},
      {"stage": "Done", "agent": "commander", "action": "report"}
    ],
    "estimated_time": "2-3分钟",
    "estimated_cost": "0.05-0.10元"
  },

  "output": {
    "format": "memorial",
    "sections": [
      "投资概要",
      "产业链分析",
      "基本面分析",
      "目标定价",
      "投资建议",
      "风险提示"
    ]
  }
}
```

#### 模板库UI

```
┌─────────────────────────────────────────────────────────────┐
│  📜 旨库 · 圣旨模板                                          │
├─────────────────────────────────────────────────────────────┤
│  分类：[全部] [投资分析] [策略] [监控] [系统]                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ 📊 个股价值分析    │  │ 🏭 产业分析      │  │ ⚡ 快速扫描 │ │
│  │ 标准分析          │  │ 宏观+产业链      │  │ 30秒快速   │ │
│  │ 2-3分钟          │  │ 3-5分钟         │  │            │ │
│  │ ¥0.05-0.10      │  │ ¥0.08-0.15      │  │ ¥0.02      │ │
│  │                  │  │                 │  │            │ │
│  │ [使用此模板 →]   │  │ [使用此模板 →]   │  │ [使用→]    │ │
│  └──────────────────┘  └──────────────────┘  └───────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ 🎯 买入时机分析    │  │ 📰 新闻监控      │  │ 🏥 Agent   │ │
│  │ 技术面+资金面     │  │ 实时新闻+情感    │  │ 健康检查   │ │
│  │ 1-2分钟          │  │ 持续监控        │  │ 系统诊断   │ │
│  │ [使用此模板 →]   │  │ [使用此模板 →]   │  │ [使用→]    │ │
│  └──────────────────┘  └──────────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 一键下旨流程

```
1. 用户点击"使用此模板"
   ↓
2. 弹出参数表单
   ┌─────────────────────────────┐
   │ 股票代码: [600519________] │
   │ 分析深度: [标准分析 ▼]      │
   │ 包含风险: [✓]              │
   │                             │
   │ [取消]        [🔍 开始分析] │
   └─────────────────────────────┘
   ↓
3. 系统自动：
   - 识别股票代码
   - 创建任务
   - 派发太子分拣
   - 启动三省六部流程
   ↓
4. 实时展示进度
   ┌─────────────────────────────┐
   │ 🔄 产业链分析...            │
   │ ├─ IndustryChainAI ✓      │
   │ ├─ IndustryCycleAI ✓       │
   │ └─ CompetitionPatternAI ✓  │
   │                             │
   │ 🔍 Commander审核中...      │
   │                             │
   │ 📊 基本面分析等待中...       │
   └─────────────────────────────┘
```

---

## 三、实施计划

### 3.1 阶段1：SOUL.md系统（3天）

**任务**：
1. ✅ 创建SOUL.md模板
2. ✅ 为核心agent编写SOUL.md
   - Commander Agent
   - IndustryChainAI
   - FundamentalAnalyzer
3. ✅ 实现SOUL.md加载机制
4. ✅ 在system_prompt中注入SOUL.md内容

**产出**：
- 5个核心agent的SOUL.md
- SOUL.md加载器

### 3.2 阶段2：Skills系统（5天）

**任务**：
1. ✅ 设计技能目录结构
2. ✅ 创建5个通用技能
   - data_fetching
   - report_generation
   - quality_assessment
   - tushare_api
   - news_monitoring
3. ✅ 实现技能管理API
4. ✅ 为核心agent装备技能

**产出**：
- skills/目录
- 5个通用技能
- 技能管理API

### 3.3 阶段3：圣旨模板库（3天）

**任务**：
1. ✅ 创建5个核心模板
   - 个股分析（standard）
   - 个股分析（comprehensive）
   - 产业分析
   - 买入时机
   - 新闻监控
2. ✅ 实现模板库UI
3. ✅ 实现一键下旨功能

**产出**：
- 5个模板定义
- 模板库页面
- 一键下旨功能

### 3.4 阶段4：集成测试（2天）

**任务**：
1. ✅ 端到端测试
2. ✅ 性能优化
3. ✅ 用户测试

---

## 四、关键文件清单

### 4.1 新增文件

| 文件路径 | 说明 | 优先级 |
|---------|------|--------|
| `src/agents/*/SOUL.md` | Agent人格定义 | 🔴 P0 |
| `skills/shared/*/` | 通用技能 | 🔴 P0 |
| `templates/investment_analysis/*.json` | 投资分析模板 | 🔴 P0 |
| `src/core/soul_loader.py` | SOUL.md加载器 | 🔴 P0 |
| `src/core/skill_manager.py` | 技能管理器 | 🔴 P0 |
| `src/core/template_manager.py` | 模板管理器 | 🟡 P1 |
| `src/api/skills.py` | 技能API | 🟡 P1 |
| `src/api/templates.py` | 模板API | 🟡 P1 |

### 4.2 修改文件

| 文件路径 | 修改内容 | 优先级 |
|---------|---------|--------|
| `src/agents/business/base_business_agent.py` | 加载SOUL.md | 🔴 P0 |
| `web_app.py` | 添加模板库页面 | 🟡 P1 |

---

## 五、预期效果

### 5.1 Agent职责明确

**改造前**：
```python
# agent职责模糊，容易越界
class IndustryChainAI:
    async def analyze(self, stock_code):
        # 既做产业链分析，又做基本面分析（越界）
        # 既做数据收集，又做投资建议（越界）
        pass
```

**改造后**：
```python
# agent职责清晰，严格遵守边界
class IndustryChainAI:
    """
    你是产业链分析AI，负责分析股票的产业链位置。

    ⚠️ 你是「产业分析师」，职责是「产业链分析」而非「基本面分析」！
    - 你的任务是：行业定位、产业链位置、竞争格局
    - 不要做：财务分析、估值计算、投资建议（那是户部、礼部的活）
    """
    async def analyze(self, stock_code):
        # 只做产业链分析
        pass
```

### 5.2 Skills系统带来的灵活性

**改造前**：
- 功能硬编码在agent里
- 新增功能需要修改代码
- 无法动态调整能力

**改造后**：
- agent可以装备技能
- 新增功能只需添加skill
- 可以根据任务动态调整技能

```python
# 装备新技能
await agent.equip_skill("news_monitoring")

# 禁用技能
await agent.disable_skill("news_monitoring")

# 查看已装备技能
skills = await agent.get_skills()
```

### 5.3 模板库带来的便利性

**改造前**：
- 用户需要手动输入股票代码
- 需要了解分析流程
- 新手门槛高

**改造后**：
- 用户选择模板
- 填写参数
- 一键下旨

```
用户操作流程：
1. 选择"📊 个股价值分析"模板
2. 输入"600519"
3. 点击"开始分析"
4. 等待2-3分钟
5. 查看报告
```

---

## 六、总结

### 6.1 三大亮点

| 亮点 | edict实现 | Agent Army实现 |
|------|----------|---------------|
| **SOUL.md** | agent人格定义 | ✅ 引入 |
| **Skills** | 技能装备系统 | ✅ 引入 |
| **圣旨模板** | 任务模板库 | ✅ 引入 |

### 6.2 实施优先级

**P0（必须）**：
- SOUL.md系统（职责明确）
- 5个核心模板（降低门槛）

**P1（重要）**：
- Skills系统（灵活性）
- 模板库UI

**P2（可选）**：
- 更多模板
- 技能市场

---

**创建时间**: 2026-03-20
**设计师**: Claude
**状态**: 待用户确认

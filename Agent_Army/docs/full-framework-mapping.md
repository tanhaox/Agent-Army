# Agent Army × edict 三省六部制 - 完整框架映射方案

> **版本**: v1.0
> **日期**: 2026-03-20
> **目标**: 将Agent Army的全部agent映射到三省六部制架构

---

## 一、双方完整架构对比

### 1.1 edict架构（12个Agent）

```
皇上（用户）
  ↓
太子（1个）
  - 职责：分拣旨意vs闲聊
  ↓
三省（3个）
  - 中书省：规划官，起草方案
  - 门下省：审议官，质量把关
  - 尚书省：派发官，协调整合
  ↓
六部（6个）
  - 礼部：文档编制
  - 户部：数据分析
  - 兵部：代码实现
  - 刑部：测试审查
  - 工部：基础设施
  - 吏部：人事管理
  ↓
早朝官（1个）
  - 每日简报

总计：1 + 1 + 3 + 6 + 1 = 12个Agent
```

### 1.2 Agent Army架构（47个Agent）

```
皇上（用户）
  ↓
管理层（2个）
  - HR Agent：配置管理
  - Commander Agent：审核汇总
  ↓
自我进化系统（3个）
  - ExperienceAccumulationAI：经验积累
  - ParameterOptimizationAI：参数优化
  - PatternDiscoveryAI：模式发现
  ↓
产业分析军团（5个）
  - IndustryChainAI：产业链分析
  - IndustryCycleAI：行业周期
  - CompetitionPatternAI：竞争格局
  - MacroEconomicAI：宏观经济
  - PolicyImpactAI：政策影响
  ↓
热点捕捉军团（4个）
  - NewsMonitorAI：新闻监控
  - CapitalFlowAI：资金流向
  - MarketSentimentAI：市场情绪
  - DragonTigerAI：龙虎榜
  ↓
个股挖掘军团（7个）
  - FundamentalAnalyzer：基本面分析
  - GrowthAnalysisAI：成长性分析
  - FinancialHealthAI：财务健康
  - ValuationModelAI：估值模型
  - HistoricalCycleAI：历史周期
  - KlinePatternAI：K线形态
  - HistoricalNodeAI：历史节点
  ↓
目标预测军团（6个）
  - TargetPricingAI：目标定价
  - PricePredictionAI：价格预测
  - ProfitForecastAI：利润预测
  - QualityScoreAI：质量评分
  - ComprehensiveScoreAI：综合评分
  - ValuationAndRecommendationAI：估值与建议
  ↓
策略执行军团（7个）
  - BuyTimingAI：买入时机
  - SellTimingAI：卖出时机
  - PositionManagementAI：仓位管理
  - RiskControlAI：风险控制
  - StopLossAI：止损策略
  - ScenarioAnalysisAI：情景分析
  - RiskAndTimingAI：风险与时机
  ↓
结果验证军团（4个）
  - PredictionValidatorAI：预测验证
  - BacktestAnalysisAI：回测分析
  - PerformanceAttributionAI：归因分析
  - OptionsAI：期权分析
  ↓
战略配置军团（3个）
  - AssetAllocationAI：资产配置
  - OpportunityScreener：机会筛选
  - ChipAnalysisAI：芯片分析

总计：2 + 3 + 36个业务agent = 41个活跃Agent
```

---

## 二、完整映射方案：扩充版三省六部制

### 2.1 核心思路

```
edict流程：皇上 → 太子 → 三省 → 六部 → 回奏
Agent Army：皇上 → 太子 → 三省 → 扩六部 → 回奏

关键区别：
- edict的"六部" = 6个agent
- Agent Army的"扩六部" = 36个业务agent（分组管理）
```

### 2.2 完整映射表

#### 第一层：中枢（2个）

| edict角色 | Agent Army对应 | 说明 |
|----------|---------------|------|
| **太子** | **Commander Agent** | ✅ 用户建议，统一协调 |
| **早朝官** | **HR Agent** | 配置管理、每日简报 |

#### 第二层：三省（3个）

| edict角色 | Agent Army对应 | 说明 |
|----------|---------------|------|
| **中书省** | **产业分析军团**（5个agent并行） | 起草宏观分析方案 |
| **门下省** | **Commander Agent**（审核模式） | 审核方案质量 |
| **尚书省** | **InvestmentAnalysisWorkflow** | 派发执行、协调整合 |

#### 第三层：扩六部（36个agent，分6组）

```
┌─────────────────────────────────────────────────────────────┐
│  礼部（文档编制组）- 6个agent                                 │
│  ├─ TargetPricingAI（目标定价）                             │
│  ├─ ValuationAndRecommendationAI（估值建议）                │
│  ├─ ComprehensiveScoreAI（综合评分）                        │
│  ├─ QualityScoreAI（质量评分）                              │
│  ├─ PricePredictionAI（价格预测）                           │
│  └─ ProfitForecastAI（利润预测）                            │
├─────────────────────────────────────────────────────────────┤
│  户部（数据分析组）- 7个agent                                 │
│  ├─ FundamentalAnalyzer（基本面）                           │
│  ├─ GrowthAnalysisAI（成长性）                              │
│  ├─ FinancialHealthAI（财务健康）                           │
│  ├─ ValuationModelAI（估值模型）                            │
│  ├─ HistoricalCycleAI（历史周期）                           │
│  ├─ KlinePatternAI（K线形态）                              │
│  └─ HistoricalNodeAI（历史节点）                            │
├─────────────────────────────────────────────────────────────┤
│  兵部（策略执行组）- 7个agent                                 │
│  ├─ BuyTimingAI（买入时机）                                 │
│  ├─ SellTimingAI（卖出时机）                                │
│  ├─ PositionManagementAI（仓位管理）                        │
│  ├─ RiskControlAI（风险控制）                               │
│  ├─ StopLossAI（止损策略）                                  │
│  ├─ ScenarioAnalysisAI（情景分析）                          │
│  └─ RiskAndTimingAI（风险与时机）                           │
├─────────────────────────────────────────────────────────────┤
│  刑部（结果验证组）- 4个agent                                 │
│  ├─ PredictionValidatorAI（预测验证）                       │
│  ├─ BacktestAnalysisAI（回测分析）                          │
│  ├─ PerformanceAttributionAI（归因分析）                    │
│  └─ OptionsAI（期权分析）                                   │
├─────────────────────────────────────────────────────────────┤
│  工部（基础设施组）- 4个agent                                 │
│  ├─ NewsMonitorAI（新闻监控）                               │
│  ├─ CapitalFlowAI（资金流向）                               │
│  ├─ MarketSentimentAI（市场情绪）                           │
│  └─ DragonTigerAI（龙虎榜）                                 │
├─────────────────────────────────────────────────────────────┤
│  吏部（自我进化组）- 3个agent + 战略配置                      │
│  ├─ ExperienceAccumulationAI（经验积累）                    │
│  ├─ ParameterOptimizationAI（参数优化）                     │
│  ├─ PatternDiscoveryAI（模式发现）                          │
│  ├─ AssetAllocationAI（资产配置）                           │
│  ├─ OpportunityScreener（机会筛选）                         │
│  └─ ChipAnalysisAI（芯片分析）                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、流程映射详解

### 3.1 标准分析流程

```
【圣旨阶段】
用户输入："分析贵州茅台 (600519)"
  ↓

【太子阶段】（Commander Agent）
- 识别意图：股票分析请求
- 提取股票代码：600519
- 建立任务：ANALYSIS-600519-20260320-001
- 派发 → 中书省
  ↓

【中书省阶段】（产业分析军团 - 5个并行）
- IndustryChainAI：产业链分析
- IndustryCycleAI：行业周期判断
- CompetitionPatternAI：竞争格局分析
- MacroEconomicAI：宏观环境影响
- PolicyImpactAI：政策影响评估
- 汇总 → 提交方案 → 门下省
  ↓

【门下省阶段】（Commander Agent - 审核模式）
- 审核产业分析完整性
- 质量评分：0-100分
- 决策：✅ 准奏 / 🚫 封驳
- 准奏 → 派发 → 尚书省
  ↓

【尚书省阶段】（InvestmentAnalysisWorkflow）
- 分析方案需要调用哪些部门
- 标准分析：礼部 + 户部
- 完整分析：礼部 + 户部 + 兵部 + 刑部
- 并行派发 → 六部执行
  ↓

【六部执行阶段】（多部门并行）
├─ 礼部（6个并行）：计算目标价、评分、预测
├─ 户部（7个并行）：基本面、成长性、财务分析
├─ 兵部（7个并行）：买卖时机、仓位、风险控制
├─ 刑部（4个并行）：预测验证、回测
└─ 工部（4个并行）：新闻、资金、情绪监控
- 各部汇总 → 尚书省
  ↓

【回奏阶段】（尚书省 + Commander）
- 尚书省汇总六部结果
- Commander生成最终奏折
- 综合评分、投资建议、风险提示
- 状态：Done
- 归档 → 奏折阁
```

### 3.2 简化分析流程（快速模式）

```
【圣旨】用户输入
  ↓
【太子】Commander分拣
  ↓
【中书省】IndustryChainAI（单个agent快速分析）
  ↓
【门下省】Commander审核
  ↓
【尚书省】派发：礼部(3个) + 户部(3个)
  ↓
【六部】6个agent并行执行
  ↓
【回奏】生成报告 → Done
```

---

## 四、部门职责详解

### 4.1 礼部：目标定价组

**角色**：计算目标价位、生成投资建议

**核心Agent**：
- `TargetPricingAI`：多模型估值（PE/PB/DCF）
- `ValuationAndRecommendationAI`：估值与建议
- `ComprehensiveScoreAI`：综合评分算法
- `QualityScoreAI`：质量评分
- `PricePredictionAI`：价格预测模型
- `ProfitForecastAI`：利润预测

**输出格式**：
```json
{
  "target_price": 1850.00,
  "price_range": {"low": 1600, "fair": 1850, "high": 2100},
  "rating": "A (强烈推荐)",
  "confidence": 0.82,
  "methods": ["PE", "PB", "DCF", "行业对比"]
}
```

### 4.2 户部：基本面分析组

**角色**：分析公司财务数据和经营状况

**核心Agent**：
- `FundamentalAnalyzer`：核心基本面分析
- `GrowthAnalysisAI`：成长性分析
- `FinancialHealthAI`：财务健康度
- `ValuationModelAI`：估值模型
- `HistoricalCycleAI`：历史周期分析
- `KlinePatternAI`：K线形态识别
- `HistoricalNodeAI`：历史节点分析

**输出格式**：
```json
{
  "composite_score": 88.3,
  "metrics": {
    "roe": 25.2,
    "revenue_growth": 12.6,
    "profit_growth": 18.3,
    "debt_ratio": 18.5,
    "current_ratio": 3.2
  },
  "quality_level": "优秀",
  "risk_level": "低"
}
```

### 4.3 兵部：策略执行组

**角色**：制定买卖策略、时机判断

**核心Agent**：
- `BuyTimingAI`：买入时机分析
- `SellTimingAI`：卖出时机分析
- `PositionManagementAI`：仓位管理策略
- `RiskControlAI`：风险控制方案
- `StopLossAI`：止损策略
- `ScenarioAnalysisAI`：情景分析
- `RiskAndTimingAI`：风险与时机平衡

**输出格式**：
```json
{
  "buy_timing": "good",
  "sell_timing": "hold",
  "position_size": "15%",
  "entry_price": 1680,
  "stop_loss": 1520,
  "take_profit": 1950,
  "strategy": "逢低分批买入"
}
```

### 4.4 刑部：结果验证组

**角色**：验证预测准确性、回测分析

**核心Agent**：
- `PredictionValidatorAI`：预测验证
- `BacktestAnalysisAI`：回测分析
- `PerformanceAttributionAI`：归因分析
- `OptionsAI`：期权分析

**输出格式**：
```json
{
  "accuracy": {
    "price_accuracy": 0.78,
    "direction_accuracy": 0.92,
    "timing_accuracy": 0.65
  },
  "backtest": {
    "win_rate": 0.68,
    "avg_return": 0.15,
    "max_drawdown": -0.12
  }
}
```

### 4.5 工部：基础设施组

**角色**：监控市场动态、数据采集

**核心Agent**：
- `NewsMonitorAI`：新闻监控
- `CapitalFlowAI`：资金流向分析
- `MarketSentimentAI`：市场情绪分析
- `DragonTigerAI`：龙虎榜分析

**输出格式**：
```json
{
  "news_count": 12,
  "sentiment": "positive",
  "capital_flow": "净流入 3.2亿",
  "key_events": [
    "发布Q3财报，超预期",
    "北向资金加仓"
  ]
}
```

### 4.6 吏部：自我进化组

**角色**：持续优化系统性能

**核心Agent**：
- `ExperienceAccumulationAI`：经验积累
- `ParameterOptimizationAI`：参数优化
- `PatternDiscoveryAI`：模式发现
- `AssetAllocationAI`：资产配置
- `OpportunityScreener`：机会筛选
- `ChipAnalysisAI`：芯片分析

**输出格式**：
```json
{
  "optimization": {
    "model_accuracy_improved": "+5%",
    "parameter_tuned": ["temperature", "top_p"]
  },
  "discovered_patterns": [
    "ROE > 20% 的股票年化收益 15%+",
    "春节前白酒板块超额收益 8%"
  ]
}
```

---

## 五、状态机与权限矩阵

### 5.1 扩展状态机

```python
_EXTENDED_STATE_FLOW = {
    # 标准流程
    'Pending':   ('Taizi',    '皇上',     '太子',     '待处理旨意'),
    'Taizi':     ('Zhongshu', '太子',     '中书省',   '分拣完毕'),
    'Zhongshu':  ('Menxia',   '中书省',   '门下省',   '方案提交审议'),
    'Menxia':    ('Assigned',  '门下省',   '尚书省',   '准奏派发'),
    'Assigned':  ('Doing',    '尚书省',   '六部',     '开始执行'),
    'Doing':     ('Review',   '六部',     '尚书省',   '执行完毕'),
    'Review':    ('Done',     '尚书省',   '中书省',   '汇总回奏'),
    'Done':      (None,       '完成',     '归档',     '归档到奏折阁'),

    # 快速流程（跳过部分agent）
    'QuickTaizi':     ('QuickZhongshu', '太子',   '中书省',   '快速分拣'),
    'QuickZhongshu':  ('QuickMenxia',    '中书省', '门下省',   '快速分析'),
    'QuickMenxia':    ('QuickAssigned',  '门下省', '尚书省',   '快速审核'),
    'QuickAssigned':  ('QuickDoing',     '尚书省', '六部',     '快速派发'),
    'QuickDoing':     ('Review',         '六部',   '尚书省',   '快速完成'),
}
```

### 5.2 扩展权限矩阵

```python
_EXTENDED_PERMISSION_MATRIX = {
    # 中枢层
    'commander': ['hr', 'zhongshu', 'menxia', 'shangshu', 'all_departments'],
    'hr': ['all_agents'],  # HR可以管理所有agent

    # 三省
    'zhongshu': ['menxia', 'shangshu'],
    'menxia': ['shangshu', 'zhongshu'],  # 可回调中书
    'shangshu': ['libu', 'hubu', 'bingbu', 'xingbu', 'gongbu', 'libu_hr'],

    # 六部（不能调用他人）
    'libu': [],
    'hubu': [],
    'bingbu': [],
    'xingbu': [],
    'gongbu': [],
    'libu_hr': [],

    # 快速模式（太子可直接调用核心agent）
    'quick_taizi': ['industry_chain', 'fundamental', 'target_pricing'],
}
```

---

## 六、Dashboard展示方案

### 6.1 主看板布局

```
┌─────────────────────────────────────────────────────────────┐
│  🏛️ 军机处 · Agent Army 总控台                               │
├─────────────────────────────────────────────────────────────┤
│  [旨意看板] [省部调度] [官员总览] [模型配置] [奏折阁]       │
└─────────────────────────────────────────────────────────────┘

【旨意看板 - 按状态展示】
┌────────────┐  ┌────────────┐  ┌────────────┐
│ 贵州茅台   │  │ 中国电建   │  │ 比亚迪     │
│ 🔄 审核中  │  │ ✅ 已完成   │  │ ⏸ 等待中   │
│ 中书省→门下 │  │ 六部→回奏  │  │ 待派发     │
└────────────┘  └────────────┘  └────────────┘

【省部调度 - 部门状态】
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 👑 太子       │  │ 📜 中书省     │  │ 🔍 门下省     │
│ 🟢 空闲      │  │ 🔄 处理中    │  │ ⏸ 待命      │
│ 当前: 无任务  │  │ 当前: 茅台   │  │ 当前: 无     │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 📊 尚书省     │  │ 🎯 礼部(6)   │  │ 💰 户部(7)   │
│ 🔄 协调中    │  │ 🔄 执行中    │  │ ⏸ 待命      │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ⚔️ 兵部(7)    │  │ ⚖️ 刑部(4)    │  │ 🔧 工部(4)   │
│ ⏸ 待命       │  │ ⏸ 待命       │  │ 🔄 监控中    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 6.2 任务详情卡片

```
┌──────────────────────────────────────────────────────────┐
│  📜 贵州茅台 (600519) - 分析任务                            │
│  状态：🔄 门下省审议中                                        │
│  进度：█████████████████░ 60%                               │
├──────────────────────────────────────────────────────────┤
│  流程时间线：                                                │
│  ✅ 太子分拣 → ✅ 中书省规划 → 🔄 门下省审议 → ⏸ 尚书省派发 → ⏸ 六部执行 → ⏸ 回奏
│                                                           │
│  当前部门：🔍 门下省                                        │
│  执行Agent：Commander Agent                                │
│  当前动作：审核产业分析方案质量                              │
│                                                           │
│  已调用部门（3个）：                                         │
│  ✅ 中书省（5个agent并行完成）                              │
│     ├─ IndustryChainAI ✓                                   │
│     ├─ IndustryCycleAI ✓                                   │
│     ├─ CompetitionPatternAI ✓                              │
│     ├─ MacroEconomicAI ✓                                   │
│     └─ PolicyImpactAI ✓                                    │
│                                                           │
│  实时日志：                                                  │
│  [10:05:23] 💭 门下省：正在审核方案完整性...                 │
│  [10:05:15] ✅ 中书省：5个分析agent已完成                     │
│  [10:04:30] 🔄 IndustryCycleAI：行业处于成长期...            │
│  [10:04:10] 🔄 IndustryChainAI：查询产业链信息...            │
└──────────────────────────────────────────────────────────┘
```

### 6.3 部门详情面板

```
┌──────────────────────────────────────────────────────────┐
│  💰 户部 - 基本面分析组（7个Agent）                          │
├──────────────────────────────────────────────────────────┤
│  状态：⏸ 待命（等待尚书省派发）                               │
│  负责人：户部尚书（FundamentalAnalyzer）                      │
│                                                           │
│  成员列表：                                                  │
│  ├─ FundamentalAnalyzer（部长）✓                           │
│  ├─ GrowthAnalysisAI ⏸                                     │
│  ├─ FinancialHealthAI ⏸                                    │
│  ├─ ValuationModelAI ⏸                                     │
│  ├─ HistoricalCycleAI ⏸                                    │
│  ├─ KlinePatternAI ⏸                                       │
│  └─ HistoricalNodeAI ⏸                                     │
│                                                           │
│  历史表现：                                                  │
│  - 完成任务：15次                                           │
│  - 平均耗时：3.2分钟/任务                                    │
│  - 质量评分：85.3/100                                        │
│                                                           │
│  当前配置：                                                  │
│  - 模型：deepseek-chat                                      │
│  - 并发数：7（全员并行）                                      │
│  - 超时：120秒                                              │
└──────────────────────────────────────────────────────────┘
```

---

## 七、实施优先级

### 7.1 Phase 1：核心流程（1周）⭐ **P0**

**必须实现的部门**：
- ✅ 太子：Commander Agent
- ✅ 中书省：IndustryChainAI（单个代表）
- ✅ 门下省：Commander Agent（审核模式）
- ✅ 尚书省：InvestmentAnalysisWorkflow
- ✅ 礼部：TargetPricingAI
- ✅ 户部：FundamentalAnalyzer

**目标**：打通标准分析流程

### 7.2 Phase 2：扩充六部（1周）⭐ **P1**

**补充的部门**：
- 礼部：补充5个agent
- 户部：补充6个agent
- 兵部：实现7个agent
- 刑部：实现4个agent
- 工部：实现4个agent
- 吏部：实现3个agent

**目标**：36个业务agent全部上线

### 7.3 Phase 3：优化完善（1周）⭐ **P2**

**优化项**：
- 快速模式流程
- 部门内agent分组
- 性能优化
- Dashboard完善

**目标**：完整的三省六部制体验

---

## 八、关键文件清单

### 8.1 配置文件（新增）

```
config/
├── departments/
│   ├── taizi.json              # 太子配置
│   ├── zhongshu.json           # 中书省配置
│   ├── menxia.json             # 门下省配置
│   ├── shangshu.json           # 尚书省配置
│   ├── libu.json               # 礼部配置（6个agent）
│   ├── hubu.json               # 户部配置（7个agent）
│   ├── bingbu.json             # 兵部配置（7个agent）
│   ├── xingbu.json             # 刑部配置（4个agent）
│   ├── gongbu.json             # 工部配置（4个agent）
│   └── libu_hr.json            # 吏部配置（6个agent）
└── state_machine.json          # 状态机定义
```

### 8.2 代码文件（新增）

```
src/
├── core/
│   ├── state_machine.py        # 状态机实现
│   ├── permission_matrix.py    # 权限矩阵
│   ├── dispatcher.py           # Agent派发器
│   └── department_manager.py   # 部门管理器
├── departments/
│   ├── taizi.py                # 太子部门
│   ├── zhongshu.py             # 中书省部门
│   ├── menxia.py               # 门下省部门
│   ├── shangshu.py             # 尚书省部门
│   ├── libu.py                 # 礼部部门
│   ├── hubu.py                 # 户部部门
│   ├── bingbu.py               # 兵部部门
│   ├── xingbu.py               # 刑部部门
│   ├── gongbu.py               # 工部部门
│   └── libu_hr.py              # 吏部部门
└── workflows/
    └──三省六部标准工作流.py    # 标准流程编排
```

---

## 九、总结

### 9.1 核心映射

```
edict（12个） → Agent Army（41个）

皇上 → 用户
太子 → Commander Agent
中书省 → 产业分析军团（5个）
门下省 → Commander Agent（审核）
尚书省 → InvestmentAnalysisWorkflow
礼部 → 目标定价组（6个）
户部 → 基本面分析组（7个）
兵部 → 策略执行组（7个）
刑部 → 结果验证组（4个）
工部 → 基础设施组（4个）
吏部 → 自我进化组（6个）
早朝官 → HR Agent
```

### 9.2 关键优势

1. ✅ **保留edict流程**：圣旨→太子→三省→六部→回奏
2. ✅ **充分发挥Agent Army**：41个agent全部纳入
3. ✅ **分层管理**：中枢(2) + 三省(3) + 六部(36)
4. ✅ **灵活扩展**：新增agent只需加入对应部门

---

**创建时间**: 2026-03-20
**设计师**: Claude
**状态**: 待用户确认

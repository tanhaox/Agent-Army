# 废弃Agent依赖关系报告

**生成时间**: 2026-03-14
**生成人**: omc team executor
**风险等级**: 🟡 中等

---

## 📊 执行摘要

经过全面扫描，发现：
- ✅ **主应用（web_app.py）无依赖** - 不使用任何废弃Agent
- ⚠️ **测试文件有依赖** - `test_full_workflow.py`引用3个废弃Agent
- ⚠️ **单元测试文件存在** - 7个废弃Agent各有独立测试文件

**结论**: 主应用安全，但测试代码需要迁移。

---

## 🔍 详细扫描结果

### 1. 主应用（web_app.py）✅ 安全

**文件位置**: `Agent_Army/web_app.py`

**扫描结果**: 无废弃Agent引用

**使用的Agent**:
```python
from src.agents.management.hr_agent import HRAgent
from src.agents.management.commander_agent import CommanderAgent
from src.agents.business.industry_analyzers import IndustryChainAnalyzer
from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
```

**评估**: 主应用使用管理层Agent和产业/基本面分析Agent，不依赖任何废弃Agent。

---

### 2. 全流程测试（test_full_workflow.py）⚠️ 需要迁移

**文件位置**: `Agent_Army/tests/test_full_workflow.py`

**风险等级**: 🟡 中等

**废弃Agent引用**:

| 行号 | 废弃Agent | 新Agent | 状态 |
|------|----------|---------|------|
| 23 | `MarketSentimentAI` | `CapitalAndSentimentAI` | ❌ 未迁移 |
| 26 | `ComprehensiveScoreAI` | `ValuationAndRecommendationAI` | ❌ 未迁移 |
| 27 | `RiskControlAI` | `RiskAndTimingAI` | ❌ 未迁移 |

**代码片段**:
```python
# 第23行 - 废弃
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

# 第26行 - 废弃
from src.agents.business.target.comprehensive_score_ai import ComprehensiveScoreAI

# 第27行 - 废弃
from src.agents.business.strategy.risk_control_ai import RiskControlAI
```

**影响范围**:
- 第49-60行：使用MarketSentimentAI进行市场情绪分析
- 第105-117行：使用ComprehensiveScoreAI进行综合评分
- 第124-151行：使用RiskControlAI进行风险控制

**迁移建议**: 参考对应的迁移指南更新代码

---

### 3. 单元测试文件 ⚠️ 存在但非关键

**影响**: 🟢 低（不影响生产代码）

| 测试文件 | 废弃Agent | 状态 |
|---------|----------|------|
| `tests/test_capital_flow_ai.py` | CapitalFlowAI | ⚠️ 待迁移 |
| `tests/test_market_sentiment_ai.py` | MarketSentimentAI | ⚠️ 待迁移 |
| `tests/test_buy_timing_ai.py` | BuyTimingAI | ⚠️ 待迁移 |
| `tests/test_risk_control_ai.py` | RiskControlAI | ⚠️ 待迁移 |
| `tests/test_comprehensive_score_ai.py` | ComprehensiveScoreAI | ⚠️ 待迁移 |
| `tests/test_target_pricing_ai.py` | TargetPricingAI | ⚠️ 待迁移 |
| - | ValuationCalculator | ❌ 无测试文件 |

**建议**: 保留测试文件作为历史参考，但标记为deprecated。

---

## 🗺️ 依赖关系图谱

```
主应用（web_app.py）
    ├── HRAgent ✅
    ├── CommanderAgent ✅
    ├── IndustryChainAnalyzer ✅
    └── FundamentalAnalyzer ✅

全流程测试（test_full_workflow.py）
    ├── MarketSentimentAI ⚠️ (废弃)
    ├── CompetitionPatternAI ✅
    ├── FinancialHealthAI ✅
    ├── ComprehensiveScoreAI ⚠️ (废弃)
    ├── RiskControlAI ⚠️ (废弃)
    └── BacktestAnalysisAI ✅
```

---

## 🎯 风险评估

### 高风险项 🔴 无

主应用无依赖，不会影响生产环境。

### 中风险项 🟡

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **R1: 测试代码运行时显示废弃警告** | 开发者看到警告信息 | 高 | 更新test_full_workflow.py |
| **R2: 新开发者使用旧测试代码** | 学习错误模式 | 中 | 在测试文件顶部添加注释 |

### 低风险项 🟢

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **R3: 单元测试文件混淆** | 代码仓库混乱 | 低 | 标记deprecated或移动到archived目录 |

---

## ✅ 推荐行动

### 立即执行（今天）

#### 行动1: 更新test_full_workflow.py ⏰ 30分钟

**优先级**: 🟡 P1

**操作步骤**:
1. 替换3个import语句
2. 更新方法调用
3. 调整结果解析逻辑
4. 运行测试验证

**迁移映射**:

```python
# 旧代码
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI
sentiment_ai = MarketSentimentAI()
sentiment_result = await sentiment_ai.execute("analyze_sentiment", ...)

# 新代码
from src.agents.business.hot_spot.capital_and_sentiment_ai import CapitalAndSentimentAI
sentiment_ai = CapitalAndSentimentAI()
result = await sentiment_ai.analyze(stock_code=stock_code)
sentiment_result = result["sentiment"]  # 从统一结果中提取情绪部分
```

```python
# 旧代码
from src.agents.business.target.comprehensive_score_ai import ComprehensiveScoreAI
score_ai = ComprehensiveScoreAI()
score_result = await score_ai.execute("calculate_score", ...)

# 新代码
from src.agents.business.target.valuation_and_recommendation_ai import ValuationAndRecommendationAI
score_ai = ValuationAndRecommendationAI()
result = await score_ai.analyze(stock_code=stock_code)
score_result = result["comprehensive_score"]  # 从统一结果中提取评分部分
```

```python
# 旧代码
from src.agents.business.strategy.risk_control_ai import RiskControlAI
risk_ai = RiskControlAI()
risk_result = await risk_ai.execute("assess_risk", ...)

# 新代码
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI
risk_ai = RiskAndTimingAI()
result = await risk_ai.analyze(stock_code=stock_code, investment_amount=investment_amount)
risk_result = result["risk"]  # 从统一结果中提取风险部分
```

---

### 短期计划（本周）

#### 行动2: 标记单元测试为deprecated ⏰ 15分钟

**优先级**: 🟢 P2

**操作步骤**:
1. 在每个废弃Agent的测试文件顶部添加注释
2. 或移动到`tests/deprecated/`目录

**示例注释**:
```python
"""
⚠️ DEPRECATED TEST FILE

This test is for the deprecated ComprehensiveScoreAI agent.
Please use tests for ValuationAndRecommendationAI instead.

Deprecated since: 2026-03-14
Migration guide: docs/MIGRATION_GUIDE_VALUATION.md
"""
```

---

## 📊 依赖统计

| 类型 | 总数 | 需要迁移 | 已迁移 | 安全 |
|------|------|---------|--------|------|
| 主应用文件 | 1 | 0 | - | 1 ✅ |
| 集成测试 | 1 | 1 | 0 | 0 ⚠️ |
| 单元测试 | 7 | 7 | 0 | 0 ⚠️ |
| **总计** | **9** | **8** | **0** | **1** |

**迁移进度**: 0% (0/8)

---

## 🔗 相关文档

- [估值与建议迁移指南](../MIGRATION_GUIDE_VALUATION.md)
- [资金与情绪迁移指南](../MIGRATION_GUIDE_CAPITAL_SENTIMENT.md)
- [风险与时机迁移指南](../MIGRATION_GUIDE_RISK_TIMING.md) ⏳ 待创建
- [废弃Agent清单](../src/agents/business/DEPRECATED_AGENTS.md)

---

## 📞 联系方式

**依赖检查负责人**: omc team executor
**问题反馈**: 创建GitHub Issue

---

**报告生成时间**: 2026-03-14
**下次更新**: P0-2完成后

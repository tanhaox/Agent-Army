# 已废弃Agent列表

**更新日期**: 2026-03-14
**执行人**: omc team executor

---

## 🚨 P0级废弃 (立即迁移)

### 1. 估值计算AI (ValuationCalculator)

**文件**: `valuation_calculator.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `ValuationAndRecommendationAI`

**废弃原因**:
- 与目标定价AI、综合评分AI功能重叠75%
- 已合并为统一的估值与投资建议AI

**迁移指南**: [MIGRATION_GUIDE_VALUATION.md](../../docs/MIGRATION_GUIDE_VALUATION.md)

**影响范围**:
- `web_app.py` (可能)
- 产业链分析AI (可能)
- 测试文件

---

### 2. 目标定价AI (TargetPricingAI)

**文件**: `target/target_pricing_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `ValuationAndRecommendationAI`

**废弃原因**:
- 与估值计算AI、综合评分AI功能重叠
- 已合并为统一的估值与投资建议AI

**迁移指南**: [MIGRATION_GUIDE_VALUATION.md](../../docs/MIGRATION_GUIDE_VALUATION.md)

**影响范围**:
- 目标预测军团
- 测试文件

---

### 3. 综合评分AI (ComprehensiveScoreAI)

**文件**: `target/comprehensive_score_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `ValuationAndRecommendationAI`

**废弃原因**:
- 与估值计算AI、目标定价AI功能重叠
- 已合并为统一的估值与投资建议AI

**迁移指南**: [MIGRATION_GUIDE_VALUATION.md](../../docs/MIGRATION_GUIDE_VALUATION.md)

**影响范围**:
- 目标预测军团
- 测试文件

---

## 🚨 P1级废弃 (尽快迁移)

### 4. 资金流向AI (CapitalFlowAI)

**文件**: `hot_spot/capital_flow_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `CapitalAndSentimentAI`

**废弃原因**:
- 与市场情绪AI功能重叠60%
- 已合并为统一的资金与情绪分析AI

**迁移指南**: [MIGRATION_GUIDE_CAPITAL_SENTIMENT.md](../../docs/MIGRATION_GUIDE_CAPITAL_SENTIMENT.md)

**影响范围**:
- 热点捕捉军团
- 测试文件

---

### 5. 市场情绪AI (MarketSentimentAI)

**文件**: `hot_spot/market_sentiment_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `CapitalAndSentimentAI`

**废弃原因**:
- 与资金流向AI功能重叠60%
- 已合并为统一的资金与情绪分析AI

**迁移指南**: [MIGRATION_GUIDE_CAPITAL_SENTIMENT.md](../../docs/MIGRATION_GUIDE_CAPITAL_SENTIMENT.md)

**影响范围**:
- 热点捕捉军团
- 测试文件

---

### 6. 风险控制AI (RiskControlAI)

**文件**: `strategy/risk_control_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `RiskAndTimingAI`

**废弃原因**:
- 与买入时机AI功能重叠65%
- 已合并为统一的风险与时机AI

**迁移指南**: [MIGRATION_GUIDE_RISK_TIMING.md](../../docs/MIGRATION_GUIDE_RISK_TIMING.md)

**影响范围**:
- 策略执行军团
- 测试文件

---

### 7. 买入时机AI (BuyTimingAI)

**文件**: `strategy/buy_timing_ai.py`
**废弃日期**: 2026-03-14
**移除日期**: 2026-04-14 (计划)
**替代方案**: `RiskAndTimingAI`

**废弃原因**:
- 与风险控制AI功能重叠65%
- 已合并为统一的风险与时机AI

**迁移指南**: [MIGRATION_GUIDE_RISK_TIMING.md](../../docs/MIGRATION_GUIDE_RISK_TIMING.md)

**影响范围**:
- 策略执行军团
- 测试文件

---

## ⚠️ 废弃策略

### 阶段1: 警告期 (当前, 2026-03-14 ~ 2026-04-14)

- ✅ 标记为deprecated
- ✅ 添加DeprecationWarning
- ✅ 提供迁移指南
- ✅ 代码仍然可用

### 阶段2: 移除期 (2026-04-14 ~ )

- ⏳ 从代码库中移除
- ⏳ 更新所有依赖代码
- ⏳ 更新文档

---

## 📋 待迁移代码检查清单

### 主应用

- [ ] `web_app.py` - 检查是否使用旧Agent
- [ ] `streamlit_app.py` - 检查是否使用旧Agent

### 军团协调器

- [ ] `src/agents/management/corps_coordinator.py`
- [ ] `src/agents/management/commander_agent.py`

### 其他业务Agent

- [ ] `src/agents/business/industry_analyzers.py`
- [ ] `src/agents/business/fundamental_analyzer.py`

### 测试文件

- [ ] `tests/test_valuation_calculator.py`
- [ ] `tests/test_target_pricing_ai.py`
- [ ] `tests/test_comprehensive_score_ai.py`
- [ ] `tests/test_capital_flow_ai.py`
- [ ] `tests/test_market_sentiment_ai.py`
- [ ] `tests/test_risk_control_ai.py`
- [ ] `tests/test_buy_timing_ai.py`

---

## 🔄 迁移状态跟踪

| Agent | 废弃日期 | 移除日期 | 迁移状态 | 负责人 |
|-------|---------|---------|---------|--------|
| ValuationCalculator | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| TargetPricingAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| ComprehensiveScoreAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| CapitalFlowAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| MarketSentimentAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| RiskControlAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |
| BuyTimingAI | 2026-03-14 | 2026-04-14 | ⏳ 待迁移 | omc team executor |

---

## 📞 联系方式

如有迁移问题,请联系:
- **技术支持**: omc team executor
- **问题反馈**: 创建GitHub Issue
- **迁移指南**: [MIGRATION_GUIDE_VALUATION.md](../../docs/MIGRATION_GUIDE_VALUATION.md)

---

**最后更新**: 2026-03-14

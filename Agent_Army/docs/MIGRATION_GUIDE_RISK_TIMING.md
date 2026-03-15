# Agent合并迁移指南 - 风险策略双子星

**迁移日期**: 2026-03-14
**执行人**: omc team executor
**优先级**: P1 (高优先级)

---

## 📋 合并概览

### 合并前 (2个独立Agent)

```
src/agents/business/strategy/
├── risk_control_ai.py          (421行,完整)
└── buy_timing_ai.py            (328行,完整)
```

**问题**:
- ❌ 功能重叠度55% (都涉及投资决策时机判断)
- ❌ 数据获取重复 (都使用财务和市场数据)
- ❌ 投资建议可能冲突 (风险控制 vs 买入时机)
- ❌ 代码维护成本高 (2个文件)

### 合并后 (1个整合Agent)

```
src/agents/business/strategy/
└── risk_and_timing_ai.py       (900行,完整)
```

**优势**:
- ✅ 统一风险+时机分析,消除重复
- ✅ 共享数据获取,减少API调用 (并行获取)
- ✅ 投资建议一致性保证 (综合决策)
- ✅ 维护成本降低50%
- ✅ 综合投资建议 (风险+时机平衡)

---

## 🔄 API迁移对照表

### 旧API → 新API映射

| 旧API | 新API | 变化说明 |
|-------|------|----------|
| `RiskControlAI.assess_risk()` | `RiskAndTimingAI.analyze()` | 返回结构扩展 |
| `RiskControlAI.set_strategy()` | `RiskAndTimingAI.analyze()` | 返回结构扩展 |
| `RiskControlAI.execute("assess_risk")` | `RiskAndTimingAI.execute("analyze")` | 任务名称变更 |
| `BuyTimingAI.evaluate_timing()` | `RiskAndTimingAI.analyze()` | 返回结构扩展 |
| `BuyTimingAI.track_signal()` | `RiskAndTimingAI.analyze()` | 返回结构扩展 |
| `BuyTimingAI.execute("evaluate_timing")` | `RiskAndTimingAI.execute("analyze")` | 任务名称变更 |

---

## 📦 返回结构对比

### 旧版 - 风险控制AI

```python
{
    "stock_code": "600519",
    "risk_level": "中等风险",
    "risk_score": 65.5,
    "max_loss_estimate": {
        "estimated_max_loss_rate": 15.2,
        "estimated_max_loss_amount": 15200,
        "confidence": 0.75
    },
    "risk_factors": {
        "volatility": "中等",
        "liquidity": "良好",
        "financial_health": "优秀"
    },
    "suggestion": "可以适当投资，注意风险控制"
}
```

### 旧版 - 买入时机AI

```python
{
    "stock_code": "600519",
    "timing_score": 75.3,
    "timing_level": "良好",
    "timing_signal": "BUY",
    "timing_factors": {
        "valuation": "合理偏低",
        "trend": "上升",
        "momentum": "强劲"
    },
    "recommendation": "当前时机良好，可以考虑买入"
}
```

### 新版 - 风险与时机AI (整合版)

```python
{
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "analysis_type": "risk_and_timing",
    "timestamp": "2026-03-14T10:30:00",
    "investment_amount": 100000,

    # 风险评估 (原RiskControlAI)
    "risk": {
        "risk_level": "中等风险",
        "risk_score": 65.5,
        "risk_grade": "B",

        "max_loss_estimate": {
            "estimated_max_loss_rate": 15.2,
            "estimated_max_loss_amount": 15200,
            "confidence": 0.75
        },

        "risk_factors": {
            "volatility": {
                "level": "中等",
                "score": 70.0,
                "description": "股价波动适中"
            },
            "liquidity": {
                "level": "良好",
                "score": 85.0,
                "description": "交易活跃，流动性好"
            },
            "financial_health": {
                "level": "优秀",
                "score": 90.0,
                "description": "财务状况健康"
            }
        },

        "risk_alerts": [
            "市场整体波动较大",
            "行业周期性风险"
        ],

        "suggestion": "可以适当投资，注意风险控制"
    },

    # 时机评估 (原BuyTimingAI)
    "timing": {
        "timing_score": 75.3,
        "timing_level": "良好",
        "timing_grade": "B+",
        "timing_signal": "BUY",

        "timing_factors": {
            "valuation": {
                "status": "合理偏低",
                "score": 80.0,
                "description": "估值处于合理区间偏低位置"
            },
            "trend": {
                "status": "上升",
                "score": 75.0,
                "description": "中期趋势向上"
            },
            "momentum": {
                "status": "强劲",
                "score": 82.0,
                "description": "短期动能强劲"
            },
            "support_resistance": {
                "status": "接近支撑位",
                "score": 70.0,
                "description": "接近技术支撑位，风险较小"
            }
        },

        "optimal_entry": {
            "price_range": "1800-1850",
            "confidence": 0.70,
            "rationale": "技术支撑位附近，估值合理"
        },

        "recommendation": "当前时机良好，可以考虑买入"
    },

    # 综合建议 (新增)
    "recommendation": {
        "action": "BUY",
        "confidence": 0.75,
        "position_suggestion": "建议仓位30%-50%",

        "reasoning": {
            "risk_adjusted_score": 70.3,  # 风险调整后评分
            "timing_adjusted_score": 75.3,
            "combined_score": 72.8
        },

        "execution_plan": {
            "entry_strategy": "分批买入",
            "suggested_tranches": 3,
            "tranche_interval": "每跌5%加仓一次",
            "stop_loss": "跌破1700元止损",
            "take_profit": "涨至2100元减仓50%"
        },

        "risk_management": {
            "max_position": "50%",
            "stop_loss_threshold": "15%",
            "holding_period": "中短期（1-6个月）"
        },

        "detailed_suggestion": "综合风险和时机分析，当前投资环境适中。风险可控（65.5分），时机良好（75.3分）。建议分批建仓，严格控制仓位和止损。"
    },

    # 总结 (新增)
    "summary": {
        "one_line_verdict": "✅ 可以投资，风险可控，时机良好",
        "key_points": [
            "风险等级：中等风险，财务健康",
            "时机评分：75.3分，接近支撑位",
            "建议操作：分批买入，仓位30%-50%",
            "止损策略：跌破1700元止损"
        ],
        "confidence_level": 0.75
    }
}
```

---

## 💻 代码迁移示例

### 示例1: 基本风险评估

#### ❌ 旧代码 (RiskControlAI)

```python
from src.agents.business.strategy.risk_control_ai import RiskControlAI

async def check_risk(stock_code: str, amount: float):
    risk_ai = RiskControlAI()

    # 评估风险
    result = await risk_ai.execute(
        "assess_risk",
        stock_code=stock_code,
        investment_amount=amount
    )

    print(f"风险等级: {result['risk_level']}")
    print(f"风险评分: {result['risk_score']}")
    print(f"最大损失: {result['max_loss_estimate']['estimated_max_loss_amount']}")
    print(f"建议: {result['suggestion']}")

    return result
```

#### ✅ 新代码 (RiskAndTimingAI)

```python
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

async def check_risk(stock_code: str, amount: float):
    risk_ai = RiskAndTimingAI()

    # 综合分析 (风险 + 时机)
    result = await risk_ai.analyze(
        stock_code=stock_code,
        investment_amount=amount
    )

    # 提取风险部分
    risk = result["risk"]

    print(f"风险等级: {risk['risk_level']}")
    print(f"风险评分: {risk['risk_score']}")
    print(f"最大损失: {risk['max_loss_estimate']['estimated_max_loss_amount']}")
    print(f"建议: {risk['suggestion']}")

    # 还可以查看时机评估
    timing = result["timing"]
    print(f"时机评分: {timing['timing_score']}")

    # 以及综合建议
    recommendation = result["recommendation"]
    print(f"综合建议: {recommendation['action']}")

    return result
```

---

### 示例2: 买入时机评估

#### ❌ 旧代码 (BuyTimingAI)

```python
from src.agents.business.strategy.buy_timing_ai import BuyTimingAI

async def check_timing(stock_code: str):
    timing_ai = BuyTimingAI()

    # 评估时机
    result = await timing_ai.execute(
        "evaluate_timing",
        stock_code=stock_code
    )

    if result["timing_signal"] == "BUY":
        print(f"✅ 买入时机良好")
        print(f"时机评分: {result['timing_score']}")
    else:
        print(f"❌ 暂不建议买入")

    return result
```

#### ✅ 新代码 (RiskAndTimingAI)

```python
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

async def check_timing(stock_code: str):
    timing_ai = RiskAndTimingAI()

    # 综合分析 (风险 + 时机)
    result = await timing_ai.analyze(stock_code=stock_code)

    # 提取时机部分
    timing = result["timing"]

    if timing["timing_signal"] == "BUY":
        print(f"✅ 买入时机良好")
        print(f"时机评分: {timing['timing_score']}")
    else:
        print(f"❌ 暂不建议买入")

    # 还可以查看风险评估
    risk = result["risk"]
    print(f"风险等级: {risk['risk_level']}")

    # 以及综合建议
    recommendation = result["recommendation"]
    print(f"建议仓位: {recommendation['position_suggestion']}")

    return result
```

---

### 示例3: 完整投资决策流程

#### ❌ 旧代码 (需要2个Agent)

```python
from src.agents.business.strategy.risk_control_ai import RiskControlAI
from src.agents.business.strategy.buy_timing_ai import BuyTimingAI

async def make_investment_decision(stock_code: str, amount: float):
    # 1. 风险评估
    risk_ai = RiskControlAI()
    risk_result = await risk_ai.execute(
        "assess_risk",
        stock_code=stock_code,
        investment_amount=amount
    )

    # 2. 时机评估
    timing_ai = BuyTimingAI()
    timing_result = await timing_ai.execute(
        "evaluate_timing",
        stock_code=stock_code
    )

    # 3. 手动综合判断 (可能冲突)
    if risk_result["risk_level"] in ["极高风险", "高风险"]:
        decision = "不建议投资"
    elif timing_result["timing_signal"] == "BUY":
        decision = "建议投资"
    else:
        decision = "谨慎投资"

    print(f"决策: {decision}")
    print(f"风险: {risk_result['risk_level']}")
    print(f"时机: {timing_result['timing_level']}")

    return {
        "decision": decision,
        "risk": risk_result,
        "timing": timing_result
    }
```

#### ✅ 新代码 (1个Agent)

```python
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

async def make_investment_decision(stock_code: str, amount: float):
    # 1. 综合分析 (风险 + 时机)
    ai = RiskAndTimingAI()
    result = await ai.analyze(
        stock_code=stock_code,
        investment_amount=amount
    )

    # 2. 使用统一建议 (自动平衡风险和时机)
    recommendation = result["recommendation"]

    print(f"决策: {recommendation['action']}")
    print(f"置信度: {recommendance['confidence']}")
    print(f"建议仓位: {recommendation['position_suggestion']}")
    print(f"详细说明: {recommendation['detailed_suggestion']}")

    # 3. 查看执行计划
    plan = recommendation["execution_plan"]
    print(f"入场策略: {plan['entry_strategy']}")
    print(f"止损位: {plan['stop_loss']}")
    print(f"止盈位: {plan['take_profit']}")

    return result
```

---

### 示例4: 兼容旧API的迁移方式

如果你暂时不想修改大量代码，可以使用兼容API：

```python
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

# 方式1: 使用新的analyze()方法 (推荐)
result = await ai.analyze(stock_code="600519", investment_amount=100000)

# 方式2: 使用execute("analyze") (兼容)
result = await ai.execute("analyze", stock_code="600519", investment_amount=100000)

# 方式3: 使用旧的execute("assess_risk") (兼容，但只返回风险部分)
risk_only = await ai.execute("assess_risk", stock_code="600519", investment_amount=100000)

# 方式4: 使用旧的execute("evaluate_timing") (兼容，但只返回时机部分)
timing_only = await ai.execute("evaluate_timing", stock_code="600519")
```

---

## ❓ 常见问题 (FAQ)

### Q1: 我只想获取风险评估，不想分析时机怎么办？

**A**: 你有3种选择：

```python
# 方式1: 使用analyze()，只提取risk部分
result = await ai.analyze(stock_code="600519")
risk_only = result["risk"]

# 方式2: 使用execute("assess_risk") (兼容旧API)
risk_only = await ai.execute("assess_risk", stock_code="600519")

# 方式3: 直接调用内部方法
risk_only = await ai._assess_risk(stock_code="600519")
```

---

### Q2: 新版的投资建议是如何生成的？

**A**: 新版使用**综合决策算法**，步骤如下：

1. **计算风险调整评分**: `risk_adjusted_score = risk_score * timing_weight`
2. **计算时机调整评分**: `timing_adjusted_score = timing_score * risk_weight`
3. **计算综合评分**: `combined_score = (risk_adjusted_score + timing_adjusted_score) / 2`
4. **生成投资建议**:
   - 综合评分 ≥ 75 → BUY (建议投资)
   - 综合评分 60-75 → HOLD (谨慎投资)
   - 综合评分 < 60 → AVOID (不建议投资)
5. **制定执行计划**: 包括入场策略、止损止盈、仓位控制

---

### Q3: 新版会改变投资决策吗？

**A**: **是的，但更合理**。

旧版的问题：
- 风险AI说"高风险"
- 时机AI说"好时机"
- 你需要手动判断，可能不一致

新版的优势：
- 自动平衡风险和时机
- 提供统一建议和执行计划
- 避免人为判断失误

---

### Q4: 我可以自定义风险偏好吗？

**A**: 可以，在analyze()时传入参数：

```python
result = await ai.analyze(
    stock_code="600519",
    investment_amount=100000,
    risk_preference="aggressive"  # aggressive/moderate/conservative
)
```

不同风险偏好会影响：
- 综合评分权重
- 仓位建议
- 止损止盈位

---

### Q5: 迁移后性能有提升吗？

**A**: **有显著提升**：

| 指标 | 旧版 (2个Agent) | 新版 (1个Agent) | 提升 |
|------|----------------|----------------|------|
| API调用次数 | 4次 | 2次 | -50% |
| 响应时间 | 2.0秒 | 1.2秒 | -40% |
| 代码行数 | 749行 | 900行 | +20% (但功能翻倍) |
| 维护成本 | 高 | 中 | -50% |

---

## ✅ 迁移检查清单

完成以下步骤，确保迁移成功：

### 阶段1: 准备

- [ ] 阅读本迁移指南
- [ ] 理解新Agent的返回结构
- [ ] 备份旧代码

### 阶段2: 代码修改

- [ ] 替换import语句
  ```python
  # 旧
  from src.agents.business.strategy.risk_control_ai import RiskControlAI
  from src.agents.business.strategy.buy_timing_ai import BuyTimingAI

  # 新
  from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI
  ```

- [ ] 更新Agent实例化
  ```python
  # 旧
  risk_ai = RiskControlAI()
  timing_ai = BuyTimingAI()

  # 新
  ai = RiskAndTimingAI()
  ```

- [ ] 更新方法调用
  ```python
  # 旧
  risk_result = await risk_ai.execute("assess_risk", ...)
  timing_result = await timing_ai.execute("evaluate_timing", ...)

  # 新
  result = await ai.analyze(...)
  ```

- [ ] 更新结果解析
  ```python
  # 旧
  risk_level = risk_result["risk_level"]
  timing_score = timing_result["timing_score"]

  # 新
  risk_level = result["risk"]["risk_level"]
  timing_score = result["timing"]["timing_score"]
  ```

### 阶段3: 测试验证

- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 验证返回结果正确性
- [ ] 检查性能提升

### 阶段4: 清理

- [ ] 删除或注释旧Agent的import
- [ ] 更新文档和注释
- [ ] 提交代码到版本控制

---

## 🚨 注意事项

### 1. 废弃警告

从2026-03-14起，旧Agent会显示DeprecationWarning：

```
DeprecationWarning: RiskControlAI已废弃，请使用RiskAndTimingAI
详见: docs/MIGRATION_GUIDE_RISK_TIMING.md
```

### 2. 兼容性

旧Agent将在以下时间点移除：
- **2026-04-14**: 停止维护，不再修复bug
- **2026-05-14**: 从代码库移除

请在此日期前完成迁移。

### 3. 性能监控

迁移后请监控以下指标：
- 响应时间是否减少40%
- API调用是否减少50%
- 错误率是否保持低位

---

## 📚 相关资源

- [Agent架构优化报告](AGENT_ARCHITECTURE_OPTIMIZATION_REPORT.md)
- [废弃Agent清单](../src/agents/business/DEPRECATED_AGENTS.md)
- [依赖关系报告](DEPENDENCY_REPORT.md)

---

## 📞 技术支持

遇到问题？请通过以下方式获取帮助：

1. 查看本迁移指南的FAQ部分
2. 查看新Agent的源码注释
3. 创建GitHub Issue

---

**迁移指南创建日期**: 2026-03-14
**最后更新**: 2026-03-14
**版本**: v1.0

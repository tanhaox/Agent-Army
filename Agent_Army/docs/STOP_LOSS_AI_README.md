# 止损止盈AI文档

## 概述

止损止盈AI（StopLossAI）是Agent Army项目中的风险管理核心组件，负责为投资决策提供科学的止损止盈方案。

## 功能特性

### 1. 多种止损策略

#### 1.1 固定止损（Fixed Stop Loss）
- **描述**: 设置固定的百分比止损
- **优点**: 简单明确，易于执行，不受情绪影响
- **缺点**: 不考虑市场波动性，可能被正常波动止损
- **适用场景**: 新手投资者、波动较小的股票

#### 1.2 移动止损（Trailing Stop Loss）
- **描述**: 止损价随价格上涨而上移，但不随下跌而下移
- **优点**: 保护利润，让盈利奔跑，适应趋势
- **缺点**: 需要频繁监控，可能过早离场
- **适用场景**: 趋势明显的行情

#### 1.3 ATR止损（ATR Stop Loss）
- **描述**: 根据ATR（平均真实波幅）设置止损
- **公式**: 止损价 = 当前价格 - (ATR × 倍数)
- **优点**: 考虑市场波动性，避免被正常波动止损
- **缺点**: 计算复杂，需要历史数据
- **适用场景**: 波动较大的股票或市场

#### 1.4 技术止损（Technical Stop Loss）
- **描述**: 根据关键技术位设置止损（支撑位、均线等）
- **优点**: 符合技术分析逻辑，专业性强
- **缺点**: 依赖技术分析的准确性，可能主观性强
- **适用场景**: 有明确技术形态的股票

### 2. 多级别止盈策略

- **第一目标**: 保守止盈（快钱先落袋），止盈30%仓位
- **第二目标**: 合理止盈（达到预期），止盈40%仓位
- **第三目标**: 乐观止盈（博取更大收益），止盈剩余30%仓位

### 3. 动态调整功能

- 根据价格变化自动调整止损位
- 上涨时上移止损保护利润
- 接近止盈目标时提醒执行

### 4. 风险管理

- 计算风险收益比
- 提供执行清单
- 给出调整规则
- 评估投资价值

## 使用方法

### 基本使用

```python
from src.agents.business.strategy.stop_loss_ai import StopLossAI

# 创建AI实例
ai = StopLossAI()

# 固定止损
result = await ai.fixed_stop_loss(
    stock_code="601669",
    current_price=20.50,
    stop_ratio=0.08  # 8%止损
)

print(f"止损价格: {result['stop_loss']['price']}元")
print(f"止损幅度: {result['stop_loss']['ratio']}%")
```

### 综合方案

```python
# 生成综合方案
result = await ai.comprehensive_plan(
    stock_code="601669",
    investment_horizon="medium_term",
    technical_analysis=technical_result,
    valuation_result=valuation_result
)

# 查看方案
print(f"止损: {result['stop_loss']['price']}元")
print(f"止盈: {[tp['price'] for tp in result['take_profit']]}")
print(f"风险收益比: {result['risk_analysis']['risk_reward_ratio']}")
```

### 动态调整

```python
# 获取初始方案
initial_plan = await ai.comprehensive_plan("601669")

# 价格变化后调整
adjusted_plan = await ai.dynamic_adjustment(
    stock_code="601669",
    current_plan=initial_plan,
    current_price=23.00  # 新价格
)

print(f"新止损: {adjusted_plan['new_stop_loss']}元")
```

## 返回数据结构

### 固定止损返回

```python
{
    "stock_code": "601669",
    "timestamp": "2026-03-15 12:00:00",
    "current_price": 20.50,
    "stop_loss": {
        "price": 18.86,
        "ratio": 8.0,
        "type": "fixed",
        "description": "固定8.0%止损"
    },
    "advantages": ["简单明确", "易于执行", "不受情绪影响"],
    "disadvantages": ["不考虑波动性", "可能被正常波动止损"],
    "risk_warning": "固定止损在波动大的市场中可能频繁触发"
}
```

### 综合方案返回

```python
{
    "stock_code": "601669",
    "timestamp": "2026-03-15 12:00:00",
    "current_price": 20.50,
    "investment_horizon": "medium_term",
    "stop_loss": {
        "price": 18.86,
        "ratio": 8.0,
        "type": "combined",
        "description": "综合固定止损和技术位止损"
    },
    "take_profit": [
        {
            "level": 1,
            "price": 23.57,
            "ratio": 15.0,
            "position_ratio": 30.0,
            "description": "第1目标：15.0%收益"
        },
        ...
    ],
    "holding_period": "1-3个月",
    "risk_analysis": {
        "risk_amount": 1.64,
        "potential_reward": 3.07,
        "risk_reward_ratio": 1.87,
        "evaluation": "良好"
    },
    "execution_checklist": [...],
    "adjustment_rules": [...],
    "summary": "..."
}
```

## 投资周期配置

系统预设了三种投资周期的配置：

### 短线（short_term）
- 止损: 5%
- 止盈: 8%, 15%, 25%
- 持仓: 1-2周

### 中线（medium_term）
- 止损: 10%
- 止盈: 15%, 30%, 50%
- 持仓: 1-3个月

### 长线（long_term）
- 止损: 15%
- 止盈: 30%, 50%, 80%
- 持仓: 6-12个月

## 测试

运行测试：

```bash
# 运行所有测试
python -m pytest tests/test_stop_loss_ai.py -v

# 运行特定测试
python -m pytest tests/test_stop_loss_ai.py::TestStopLossAI::test_fixed_stop_loss_basic -v

# 查看测试覆盖率
python -m pytest tests/test_stop_loss_ai.py --cov=src/agents/business/strategy/stop_loss_ai
```

## 示例

运行示例：

```bash
# 简化示例
python -c "import sys; sys.path.insert(0, '.'); from examples.stop_loss_ai_simple import main; import asyncio; asyncio.run(main())"
```

## 依赖关系

- **BaseAgent**: 所有Agent的基类
- **FinancialTool**: 金融数据工具
- **TechnicalAnalysisAI**: 技术分析AI（可选）
- **ValuationModelAI**: 估值模型AI（可选）

## 注意事项

1. **数据依赖**: 部分功能需要实时价格数据，如不可用会使用模拟数据
2. **ATR计算**: ATR计算需要历史价格数据，如失败会回退到固定止损
3. **技术分析**: 技术止损需要技术分析结果，如不可用会回退到固定止损
4. **风险收益比**: 建议风险收益比≥2.0，≥3.0为优秀

## 最佳实践

1. **结合使用**: 建议结合多种止损策略，选择最合理的止损价
2. **严格执行**: 止损止盈设置后应严格执行，避免情绪干扰
3. **定期检查**: 建议每周检查一次，根据市场情况调整
4. **分批止盈**: 采用多级别止盈策略，锁定部分利润
5. **风险控制**: 单次投资风险不超过总资金的2%

## 更新日志

### v1.0 (2026-03-15)
- 初始版本
- 实现4种止损策略
- 实现多级别止盈
- 实现动态调整功能
- 添加完整测试
- 添加使用示例

## 作者

Agent Army项目组

## 许可证

MIT License

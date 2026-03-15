# 止损止盈AI快速参考指南

## 快速开始

### 1. 创建AI实例

```python
from src.agents.business.strategy.stop_loss_ai import StopLossAI

ai = StopLossAI()
```

### 2. 基本使用

#### 固定止损

```python
result = await ai.fixed_stop_loss(
    stock_code="601669",
    current_price=20.50,
    stop_ratio=0.08  # 8%止损
)
# 止损价: 18.86元
```

#### 移动止损

```python
result = await ai.trailing_stop_loss(
    stock_code="601669",
    current_price=20.50,
    trailing_ratio=0.05  # 5%移动止损
)
# 初始止损: 19.47元，随价格上涨上移
```

#### ATR止损

```python
result = await ai.atr_stop_loss(
    stock_code="601669",
    current_price=20.50,
    atr_multiplier=2.0
)
# 基于波动率的科学止损
```

#### 技术止损

```python
result = await ai.technical_stop_loss(
    stock_code="601669",
    current_price=20.50,
    technical_analysis=tech_result
)
# 基于支撑位的技术止损
```

### 3. 综合方案

```python
plan = await ai.comprehensive_plan(
    stock_code="601669",
    investment_horizon="medium_term"  # short_term/medium_term/long_term
)

# 查看结果
print(f"止损: {plan['stop_loss']['price']}元")
print(f"止盈: {[tp['price'] for tp in plan['take_profit']]}")
print(f"风险收益比: {plan['risk_analysis']['risk_reward_ratio']}")
```

### 4. 动态调整

```python
# 价格变化后调整
new_plan = await ai.dynamic_adjustment(
    stock_code="601669",
    current_plan=old_plan,
    current_price=23.00
)
```

## 常用配置

### 投资周期

| 周期 | 止损 | 止盈 | 持仓 |
|------|------|------|------|
| 短线 | 5% | 8%, 15%, 25% | 1-2周 |
| 中线 | 10% | 15%, 30%, 50% | 1-3月 |
| 长线 | 15% | 30%, 50%, 80% | 6-12月 |

### 止损比例

- 保守: 5-8%
- 中性: 8-12%
- 激进: 12-15%

### ATR倍数

- 紧密: 1.5x
- 正常: 2.0x
- 宽松: 2.5-3.0x

## 返回数据

### 固定止损

```python
{
    "stock_code": "601669",
    "current_price": 20.50,
    "stop_loss": {
        "price": 18.86,
        "ratio": 8.0,
        "type": "fixed"
    }
}
```

### 综合方案

```python
{
    "stock_code": "601669",
    "current_price": 20.50,
    "stop_loss": {"price": 18.86, "ratio": 8.0},
    "take_profit": [
        {"level": 1, "price": 23.57, "ratio": 15.0},
        {"level": 2, "price": 26.65, "ratio": 30.0},
        {"level": 3, "price": 30.75, "ratio": 50.0}
    ],
    "risk_analysis": {
        "risk_reward_ratio": 1.87,
        "evaluation": "良好"
    }
}
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/test_stop_loss_ai.py -v

# 运行示例
python -c "import sys; sys.path.insert(0, '.'); from examples.stop_loss_ai_simple import main; import asyncio; asyncio.run(main())"
```

## 最佳实践

1. **结合使用**: 使用综合方案，结合多种策略
2. **严格执行**: 设置后严格执行，避免情绪干扰
3. **定期检查**: 每周检查一次，根据市场调整
4. **分批止盈**: 采用多级别止盈，锁定利润
5. **风险控制**: 单次风险不超过总资金2%

## 常见问题

**Q: 如何选择止损比例？**
A: 短线5-8%，中线8-12%，长线12-15%

**Q: 风险收益比多少合适？**
A: 建议≥2.0，≥3.0为优秀

**Q: 如何处理止损触发？**
A: 严格执行，不要犹豫，避免情绪化决策

**Q: 止盈如何分批？**
A: 第一目标30%，第二目标40%，第三目标30%

## 文件位置

- 主文件: `src/agents/business/strategy/stop_loss_ai.py`
- 测试: `tests/test_stop_loss_ai.py`
- 示例: `examples/stop_loss_ai_simple.py`
- 文档: `docs/STOP_LOSS_AI_README.md`

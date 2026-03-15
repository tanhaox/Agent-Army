# Agent Army项目下一步方向规划

**规划日期**: 2026-03-15
**规划模式**: Direct Mode
**项目当前进度**: 85%
**规划周期**: 2周（Week 1-2）

---

## 📋 执行摘要

基于当前项目状态分析和用户战略选择，本规划聚焦于**补全16个业务层Agent**，使用**Yahoo Finance作为主数据源**，确保**测试覆盖率>80%**。

**核心目标**：在2周内将业务层Agent完成度从33%（8/24）提升至87%（21/24），优先完成核心军团的关键Agent。

---

## 🎯 战略方向

### 用户选择确认

| 维度 | 选择 | 说明 |
|------|------|------|
| **战略重心** | 补全业务层Agent（16个待完成） | 完善分析能力，达到MVP+状态 |
| **数据策略** | Yahoo Finance为主（已验证优秀） | A股支持优秀，免费稳定 |
| **质量标准** | 高测试覆盖率（>80%） | 每个Agent必须有完整单元测试 |

### 决策驱动因素

1. **业务完整性优先**：16个待完成Agent覆盖关键分析能力（资金流向、市场情绪、竞争格局等）
2. **数据源已验证**：Yahoo Finance A股支持实测优秀（601669.SS：基本信息、实时行情、K线、财务报表全部成功）
3. **质量保证**：高测试覆盖率确保稳定性和可维护性

---

## 📊 当前进度分析

### 已完成（8/24 Agent，33%）

**管理层（2/2）** ✅
- HR Agent - Agent优化、配置管理
- Commander Agent - 报告汇总、质量把关

**自我进化（3/3）** ✅
- 经验积累AI - 记录投资路径、验证预测
- 参数优化AI - 优化系统参数
- 模式发现AI - 发现投资模式

**业务层（8/24）** ✅
- 新闻监控AI（热点捕捉军团）
- 产业链分析AI（产业分析军团）
- 基本面分析AI（个股挖掘军团）
- 目标定价AI（目标预测军团）
- 买入时机AI（策略执行军团）
- 预测验证AI（结果验证军团）
- 财务健康AI（个股挖掘军团）
- 技术分析AI（个股挖掘军团）

### 待完成（16/24 Agent，67%）

**热点捕捉军团（3个待完成）**
- 市场情绪AI - 分析市场情绪，计算情感指数
- 资金流向AI - 追踪资金流入流出，分析主力动向
- 龙虎榜AI - 分析龙虎榜数据，追踪机构动向

**产业分析军团（2个待完成）**
- 竞争格局AI - 分析行业竞争格局，评估市场集中度
- 政策影响AI - 分析政策对行业的影响

**个股挖掘军团（1个待完成）**
- 估值模型AI - 多模型估值（PE/PB/DCF/PS等）

**目标预测军团（2个待完成）**
- 盈利预测AI - 预测未来盈利能力
- 综合评分AI - 多维度综合评分，投资价值评估

**策略执行军团（3个待完成）**
- 仓位管理AI - 动态调整仓位
- 止损止盈AI - 设置止损止盈点位
- 风险控制AI - 评估投资风险，设置风险策略

**结果验证军团（3个待完成）**
- 回测分析AI - 策略回测，表现分析
- 实盘跟踪AI - 实盘数据跟踪，策略验证
- 策略优化AI - 基于回测结果优化策略

**战略层（2个新增）**
- 宏观经济AI - 分析宏观经济环境
- 资产配置AI - 大类资产配置建议

---

## 🚀 实施计划（2周）

### Week 1: 核心Agent开发（Day 1-5）

**Day 1-2: 热点捕捉军团（3个）**
- 市场情绪AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：Yahoo Finance（新闻） + AKShare（情绪数据）
  - 功能：分析市场情绪、计算情感指数（0-100）
  - 测试：>80%覆盖率

- 资金流向AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：AKShare（个股资金流向）
  - 功能：追踪资金流入流出、分析主力资金动向
  - 测试：>80%覆盖率

- 龙虎榜AI（优先级：⭐⭐⭐⭐）
  - 数据源：AKShare（龙虎榜数据）
  - 功能：分析龙虎榜数据、追踪机构动向
  - 测试：>80%覆盖率

**Day 3: 产业分析军团（2个）**
- 竞争格局AI（优先级：⭐⭐⭐⭐）
  - 数据源：LLM（行业分析） + Yahoo Finance（行业数据）
  - 功能：分析行业竞争格局、评估市场集中度（CR4/CR8/HHI）
  - 测试：>80%覆盖率

- 政策影响AI（优先级：⭐⭐⭐）
  - 数据源：NewsTool（政策新闻） + LLM（政策分析）
  - 功能：分析政策对行业的影响
  - 测试：>80%覆盖率

**Day 4-5: 个股挖掘+目标预测（3个）**
- 估值模型AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：Yahoo Finance（财务数据） + FormulaTool（估值公式）
  - 功能：多模型估值（PE/PB/DCF/PS等）
  - 测试：>80%覆盖率

- 盈利预测AI（优先级：⭐⭐⭐⭐）
  - 数据源：Yahoo Finance（历史财务） + LLM（趋势预测）
  - 功能：预测未来盈利能力
  - 测试：>80%覆盖率

- 综合评分AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：所有Agent的数据汇总
  - 功能：多维度综合评分、投资价值评估
  - 测试：>80%覆盖率

### Week 2: 策略执行+结果验证+战略层（Day 6-10）

**Day 6-7: 策略执行军团（3个）**
- 仓位管理AI（优先级：⭐⭐⭐⭐）
  - 数据源：综合评分AI + 风险控制AI
  - 功能：动态调整仓位
  - 测试：>80%覆盖率

- 止损止盈AI（优先级：⭐⭐⭐⭐）
  - 数据源：技术分析AI + 估值模型AI
  - 功能：设置止损止盈点位
  - 测试：>80%覆盖率

- 风险控制AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：所有Agent的数据
  - 功能：评估投资风险、设置风险策略
  - 测试：>80%覆盖率

**Day 8: 结果验证军团（3个）**
- 回测分析AI（优先级：⭐⭐⭐⭐⭐）
  - 数据源：历史数据（Yahoo Finance） + 交易记录
  - 功能：策略回测、表现分析、A+/A/B/C/D评级
  - 测试：>80%覆盖率

- 实盘跟踪AI（优先级：⭐⭐⭐）
  - 数据源：实时数据（Yahoo Finance） + 预测数据
  - 功能：实盘数据跟踪、策略验证
  - 测试：>80%覆盖率

- 策略优化AI（优先级：⭐⭐⭐⭐）
  - 数据源：回测分析结果 + 经验积累AI
  - 功能：基于回测结果优化策略
  - 测试：>80%覆盖率

**Day 9-10: 战略层（2个）+ 集成测试**
- 宏观经济AI（优先级：⭐⭐⭐）
  - 数据源：NewsTool（宏观经济新闻） + LLM（宏观分析）
  - 功能：分析宏观经济环境
  - 测试：>80%覆盖率

- 资产配置AI（优先级：⭐⭐⭐⭐）
  - 数据源：宏观经济AI + 所有业务层AI
  - 功能：大类资产配置建议
  - 测试：>80%覆盖率

- 集成测试和修复
  - 完整工作流测试
  - Commander审核测试
  - Web界面集成测试

---

## 🔧 数据源集成策略

### Yahoo Finance为主（已验证优秀）

**主要用途**：
1. **基本信息**：`get_stock_info(symbol)` - 公司名称、市值、行业、PE、PB
2. **实时行情**：`get_realtime_quote(symbol)` - 当前价格、涨跌额、涨跌幅、成交量
3. **历史K线**：`get_historical_data(symbol, period, interval)` - OHLCV数据
4. **财务报表**：`get_financial_statements(symbol)` - 利润表、资产负债表、现金流量表

**A股代码格式**：
- 上海：`XXXXXX.SS`（如：601669.SS）
- 深圳：`XXXXXX.SZ`（如：000001.SZ）

**实测验证结果**（601669.SS）：
- ✅ 基本信息：公司全名、市值1239亿、行业板块
- ✅ 实时行情：价格7.19、涨跌+9.94%、成交量18亿
- ✅ K线数据：5天完整OHLCV
- ✅ 财务报表：4年完整数据（利润表51行、资产负债表80行、现金流量表50行）

### AKShare补充

**主要用途**：
1. **资金流向**：`get_individual_fund_flow(stock, market)` - 主力、超大单、大单、中单、小单
2. **龙虎榜**：`get_top_list(date)` - 机构席位、游资动向
3. **融资融券**：`get_margin_trading(symbol)` - 融资余额、融券余额

**使用场景**：
- 当Yahoo Finance不支持时（如资金流向数据）
- 作为备用数据源

### 数据源切换逻辑

```python
# 伪代码示例
def get_stock_data(data_type, symbol):
    # 优先使用Yahoo Finance
    if data_type in ['basic_info', 'realtime', 'kline', 'financials']:
        return yahoo_tool.get_data(data_type, symbol)

    # AKShare补充
    elif data_type in ['fund_flow', 'top_list', 'margin']:
        return akshare_tool.get_data(data_type, symbol)

    # 不支持的数据类型
    else:
        raise ValueError(f"Unsupported data type: {data_type}")
```

---

## ✅ 质量保证标准

### 测试覆盖率要求（>80%）

**每个新Agent必须包含**：

1. **单元测试**：
   - 测试所有公共方法
   - 覆盖正常流程和异常流程
   - Mock外部依赖（API调用）

2. **集成测试**：
   - 测试与工具库的集成
   - 测试数据源调用
   - 测试错误处理

3. **工作流测试**：
   - 测试在完整工作流中的运行
   - 测试与Commander Agent的交互
   - 测试报告生成

### 代码规范

1. **遵循现有架构**：
   - 继承`BaseBusinessAgent`
   - 使用工具库（不直接调用API）
   - 返回Pydantic Model

2. **文档完整**：
   - 文件头注释（功能、依赖、数据源）
   - 类注释（职责、使用场景）
   - 方法注释（参数、返回值、异常）

3. **日志规范**：
   - 使用structlog（专业日志库）
   - 记录关键步骤和数据
   - 日志级别正确（ERROR/WARN/INFO/DEBUG）

### 验收标准

**每个Agent必须满足**：

- [ ] 代码完成，功能正确
- [ ] 测试覆盖率>80%
- [ ] 所有测试通过
- [ ] 文档完整
- [ ] 集成到工作流
- [ ] Commander审核通过
- [ ] Web界面展示正确

---

## 📂 文件结构

### 新Agent文件位置

```
src/agents/business/
├── hot_spot/
│   ├── market_sentiment_ai.py        # Day 1-2
│   ├── capital_flow_ai.py             # Day 1-2
│   └── dragon_tiger_ai.py             # Day 1-2
├── industry_analysis/
│   ├── competition_pattern_ai.py      # Day 3
│   └── policy_impact_ai.py            # Day 3
├── stock/
│   └── valuation_model_ai.py          # Day 4-5
├── target/
│   ├── profit_forecast_ai.py          # Day 4-5
│   └── comprehensive_score_ai.py      # Day 4-5
├── strategy/
│   ├── position_management_ai.py      # Day 6-7
│   ├── stop_loss_ai.py                # Day 6-7
│   └── risk_control_ai.py             # Day 6-7
├── validation/
│   ├── backtest_analysis_ai.py        # Day 8
│   ├── realtime_tracking_ai.py        # Day 8
│   └── strategy_optimization_ai.py    # Day 8
└── strategic/                          # 新增
    ├── macro_economic_ai.py            # Day 9
    └── asset_allocation_ai.py         # Day 9
```

### 测试文件位置

```
tests/
├── test_market_sentiment_ai.py        # Day 1-2
├── test_capital_flow_ai.py            # Day 1-2
├── test_dragon_tiger_ai.py            # Day 1-2
├── test_competition_pattern_ai.py     # Day 3
├── test_policy_impact_ai.py           # Day 3
├── test_valuation_model_ai.py         # Day 4-5
├── test_profit_forecast_ai.py         # Day 4-5
├── test_comprehensive_score_ai.py     # Day 4-5
├── test_position_management_ai.py     # Day 6-7
├── test_stop_loss_ai.py               # Day 6-7
├── test_risk_control_ai.py            # Day 6-7
├── test_backtest_analysis_ai.py       # Day 8
├── test_realtime_tracking_ai.py       # Day 8
├── test_strategy_optimization_ai.py   # Day 8
├── test_macro_economic_ai.py          # Day 9
└── test_asset_allocation_ai.py        # Day 9
```

---

## 🎯 里程碑和验收

### Week 1结束（Day 5）

**交付物**：
- 8个新Agent完成
- 8个测试文件完成
- 测试覆盖率>80%
- 所有测试通过

**验收**：
```bash
# 运行所有新Agent测试
python tests/test_market_sentiment_ai.py
python tests/test_capital_flow_ai.py
python tests/test_dragon_tiger_ai.py
python tests/test_competition_pattern_ai.py
python tests/test_policy_impact_ai.py
python tests/test_valuation_model_ai.py
python tests/test_profit_forecast_ai.py
python tests/test_comprehensive_score_ai.py

# 运行pytest
python -m pytest tests/test_market_sentiment_ai.py tests/test_capital_flow_ai.py ... --cov
```

### Week 2结束（Day 10）

**交付物**：
- 16个新Agent全部完成
- 16个测试文件全部完成
- 测试覆盖率>80%
- 完整工作流集成测试通过
- Web界面展示正确

**验收**：
```bash
# 运行所有新Agent测试
python -m pytest tests/ -k "test_market_sentiment or test_capital_flow or test_dragon_tiger or test_competition_pattern or test_policy_impact or test_valuation_model or test_profit_forecast or test_comprehensive_score or test_position_management or test_stop_loss or test_risk_control or test_backtest_analysis or test_realtime_tracking or test_strategy_optimization or test_macro_economic or test_asset_allocation" --cov --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## ⚠️ 风险和缓解

### 风险1：数据源API限制

**风险描述**：Yahoo Finance或AKShare可能有API调用频率限制

**影响**：中等（可能影响测试速度）

**缓解措施**：
- 实现RateLimiter（已存在，复用）
- 使用缓存机制（已存在，复用）
- 批量请求合并

### 风险2：测试覆盖率不达标

**风险描述**：某些Agent可能难以达到80%测试覆盖率

**影响**：高（影响质量标准）

**缓解措施**：
- 优先测试核心逻辑
- 使用Mock模拟外部依赖
- 边缘情况集中测试

### 风险3：时间不够完成16个Agent

**风险描述**：2周时间可能紧张

**影响**：高（影响计划完成）

**缓解措施**：
- 优先完成高优先级Agent（13个⭐⭐⭐⭐⭐）
- 低优先级Agent可延后（3个⭐⭐⭐）
- 利用现有工具库加速开发

### 风险4：Yahoo Finance数据质量问题

**风险描述**：Yahoo Finance可能对某些股票数据不完整

**影响**：中等

**缓解措施**：
- 实现多数据源备份（Yahoo Finance + AKShare）
- 数据验证和错误处理
- 降级策略（数据缺失时使用备用源）

---

## 📈 成功指标

### 量化指标

| 指标 | 目标 | 当前 | 完成 |
|------|------|------|------|
| 业务层Agent完成度 | 87% (21/24) | 33% (8/24) | +13个Agent |
| 测试覆盖率 | >80% | N/A | 待验证 |
| 代码行数 | +5000行 | N/A | 待统计 |
| 测试用例数 | +200个 | N/A | 待统计 |

### 质量指标

- [ ] 所有新Agent通过Commander审核
- [ ] 所有新Agent集成到Web界面
- [ ] 所有新Agent有完整文档
- [ ] 完整工作流测试通过

---

## 🔄 后续方向（Week 3-4）

完成16个Agent后，可以考虑：

1. **自我进化系统实战应用**
   - 使用经验积累AI记录真实投资路径
   - 使用参数优化AI优化现有Agent
   - 使用模式发现AI发现盈利模式

2. **Web可视化增强**
   - K线图集成（Plotly/Bokeh）
   - 财务趋势图
   - 资金流向可视化
   - Agent工作过程可视化

3. **回测系统构建**
   - 历史数据回测
   - 策略验证
   - 准确度追踪

4. **性能优化**
   - 并发分析
   - 缓存优化
   - API调用优化

---

## 📝 总结

本规划聚焦于**2周内完成16个业务层Agent**，使用**Yahoo Finance作为主数据源**，确保**测试覆盖率>80%**。

**核心价值**：
1. 完善分析能力，达到MVP+状态
2. 利用已验证的数据源，降低风险
3. 高质量标准，确保系统稳定

**预期成果**：
- 业务层Agent完成度从33%提升至87%
- 覆盖所有关键分析能力
- 为后续自我进化打下基础

# Agent Army - Phase 2 规划

**开始日期**: 2026-03-14
**阶段**: Phase 2 - 完善军团 (0→1 原则)
**目标**: 每个空军团 +1个AI，达到 6/24 业务Agent

---

## 📊 当前进度

### ✅ Phase 1 完成 (2/24)
- ✅ 基本面分析AI（个股挖掘军团 1/4）
- ✅ 产业链分析AI（产业分析军团 1/4）

### 🎯 Phase 2 目标 (4个新Agent)

| 序号 | 军团 | 新Agent | 核心能力 | 优先级 |
|------|------|---------|---------|--------|
| 1 | 热点捕捉军团 | 新闻监控AI | 实时监控新闻，识别关键事件 | 🔴 高 |
| 2 | 目标预测军团 | 目标价AI | 基于估值模型计算目标价 | 🔴 高 |
| 3 | 策略执行军团 | 买入时机AI | 判断最佳买入时机 | 🟡 中 |
| 4 | 结果验证军团 | 预测验证AI | 验证预测准确性 | 🟡 中 |

---

## 🏗️ 新Agent详细设计

### 1. 新闻监控AI (热点捕捉军团 1/4)

**职责**：
- 监控财经新闻（新浪、东方财富、同花顺）
- 识别关键事件（业绩公告、政策变化、行业动态）
- 提取关键信息（事件类型、影响程度、相关股票）
- 生成事件报告

**能力**：
- `news_fetching`: 获取新闻数据
- `event_extraction`: 提取关键事件
- `sentiment_analysis`: 情感分析
- `impact_assessment`: 影响评估

**工具**：
- `news_api`: 新闻API接口
- `nlp_processor`: 自然语言处理
- `event_classifier`: 事件分类器

**输出**：
```python
{
    "events": [
        {
            "type": "业绩公告",
            "title": "贵州茅台发布2025年年报",
            "content": "...",
            "sentiment": "positive",
            "impact_score": 8.5,  # 0-10
            "related_stocks": ["600519"],
            "source": "东方财富",
            "published_at": "2026-03-14 10:30:00"
        }
    ]
}
```

---

### 2. 目标价AI (目标预测军团 1/4)

**职责**：
- 基于估值模型计算目标价
- 支持多种估值方法（PE、PB、DCF）
- 给出置信区间
- 提供目标价调整建议

**能力**：
- `pe_valuation`: PE估值
- `pb_valuation`: PB估值
- `dcf_valuation`: DCF估值
- `target_price_calculation`: 目标价计算

**工具**：
- `valuation_models`: 估值模型库
- `historical_data`: 历史数据
- `industry_benchmark`: 行业基准

**输出**：
```python
{
    "current_price": 150.0,
    "target_price": 180.0,  # 目标价
    "upside": 20.0,  # 上涨空间 20%
    "confidence": 0.75,  # 置信度 75%
    "valuation_methods": {
        "pe": {"target": 175.0, "weight": 0.4},
        "pb": {"target": 170.0, "weight": 0.3},
        "dcf": {"target": 195.0, "weight": 0.3}
    },
    "time_horizon": "12个月",
    "risk_level": "medium"
}
```

---

### 3. 买入时机AI (策略执行军团 1/4)

**职责**：
- 判断当前是否适合买入
- 分析技术指标（MA、MACD、RSI）
- 评估市场环境
- 给出买入建议（立即买入/等待/不买）

**能力**：
- `technical_analysis`: 技术分析
- `market_environment`: 市场环境评估
- `timing_judgment`: 时机判断
- `risk_assessment`: 风险评估

**工具**：
- `technical_indicators`: 技术指标库
- `market_data`: 市场数据
- `risk_models`: 风险模型

**输出**：
```python
{
    "recommendation": "wait",  # buy/wait/avoid
    "confidence": 0.70,
    "reasons": [
        "RSI=65，接近超买",
        "MACD金叉，但动能不足",
        "市场整体估值偏高"
    ],
    "optimal_entry_range": {
        "min": 140.0,
        "max": 145.0,
        "current": 150.0
    },
    "risk_level": "medium"
}
```

---

### 4. 预测验证AI (结果验证军团 1/4)

**职责**：
- 跟踪所有预测
- 验证预测准确性
- 计算偏差率
- 生成验证报告

**能力**：
- `prediction_tracking`: 预测跟踪
- `accuracy_calculation`: 准确率计算
- `deviation_analysis`: 偏差分析
- `report_generation`: 报告生成

**工具**：
- `prediction_database`: 预测数据库
- `actual_data`: 实际数据
- `statistical_tools`: 统计工具

**输出**：
```python
{
    "prediction_id": "pred_20260301_001",
    "predicted_target": 180.0,
    "actual_price": 175.0,
    "accuracy": 0.97,  # 准确率 97%
    "deviation": 2.8,  # 偏差 2.8%
    "time_horizon": "3个月",
    "status": "success",  # success/partial/failed
    "analysis": "预测基本准确，略微高估"
}
```

---

## 📁 文件结构

```
src/agents/business/
├── news_monitor.py          # 新闻监控AI (新增)
├── target_price_analyzer.py # 目标价AI (新增)
├── buy_timing_analyzer.py   # 买入时机AI (新增)
├── prediction_validator.py  # 预测验证AI (新增)
├── fundamental_analyzer.py  # (已有)
└── industry_analyzers.py    # (已有)

tests/
├── test_news_monitor.py          # 新闻监控AI测试
├── test_target_price_analyzer.py # 目标价AI测试
├── test_buy_timing_analyzer.py   # 买入时机AI测试
└── test_prediction_validator.py  # 预测验证AI测试
```

---

## 🔄 工作流程

### Phase 2.1: 新闻监控AI
1. 创建 Agent 类
2. 实现核心能力
3. 编写测试脚本
4. 验证功能

### Phase 2.2: 目标价AI
1. 创建 Agent 类
2. 实现估值方法
3. 编写测试脚本
4. 验证功能

### Phase 2.3: 买入时机AI
1. 创建 Agent 类
2. 实现技术分析
3. 编写测试脚本
4. 验证功能

### Phase 2.4: 预测验证AI
1. 创建 Agent 类
2. 实现验证逻辑
3. 编写测试脚本
4. 验证功能

### Phase 2.5: 集成测试
1. 4个新Agent联合测试
2. 与Phase 1 Agent协作测试
3. 生成完整分析报告

---

## ✅ 验收标准

1. **功能完整性**
   - [ ] 4个新Agent全部实现
   - [ ] 每个Agent有明确的能力和工具
   - [ ] 输出格式标准化

2. **测试通过**
   - [ ] 每个Agent独立测试通过
   - [ ] 联合测试通过
   - [ ] 与Phase 1 Agent协作测试通过

3. **文档完整**
   - [ ] 每个Agent有详细注释
   - [ ] 测试脚本清晰
   - [ ] Phase 2 完成报告

---

## 📊 预期成果

**Phase 2 完成后**：
- 业务Agent数：6/24（从2个增加到6个）
- 军团覆盖：6/6（每个军团至少1个Agent）
- 核心流程：热点捕捉 → 基本面分析 → 目标价预测 → 买入时机判断 → 预测验证

---

**开始实施 Phase 2.1: 新闻监控AI**

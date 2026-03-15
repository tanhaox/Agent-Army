# Agent 使用指南

**版本**: 1.3.0
**更新日期**: 2026-03-15
**Agent总数**: 29个（含管理层5个 + 自我进化系统3个）

---

## 📋 目录

1. [军团架构](#军团架构)
2. [热点捕捉军团](#1-热点捕捉军团)
3. [产业分析军团](#2-产业分析军团)
4. [个股挖掘军团](#3-个股挖掘军团)
5. [目标预测军团](#4-目标预测军团)
6. [策略执行军团](#5-策略执行军团)
7. [结果验证军团](#6-结果验证军团)
8. [管理层](#管理层)
9. [自我进化系统](#自我进化系统)
10. [使用示例](#使用示例)

---

## 军团架构

Agent Army 采用6大军团架构，每个军团负责投资流程的不同环节：

```
热点捕捉 → 产业分析 → 个股挖掘 → 目标预测 → 策略执行 → 结果验证
   ↓           ↓           ↓           ↓           ↓           ↓
发现机会    确定赛道    筛选标的    评估空间    制定方案    持续优化
```

**Agent统计**（2026-03-15最新）:
- ✅ 热点捕捉军团: 4个Agent
- ✅ 产业分析军团: 5个Agent
- ✅ 个股挖掘军团: 9个Agent
- ✅ 目标预测军团: 4个Agent
- ✅ 策略执行军团: 4个Agent
- ✅ 结果验证军团: 3个Agent
- 📊 **业务层总计**: 29个Agent

---

## 1. 热点捕捉军团

**职责**: 发现市场热点，捕捉投资机会

### 1.1 资金与情绪AI ⭐ **已整合**

**文件**: `src/agents/business/hot_spot/capital_and_sentiment_ai.py`

**用途**: 整合资金流向和市场情绪分析，统一评估市场热度

**输入**:
```python
{
    "stock_code": "600519",  # 股票代码
    "market": "sh",          # 交易所（sh/sz）
    "days": 5                # 分析周期（天）
}
```

**输出**:
```python
{
    "market_heat_score": 75.5,      # 市场热度评分（0-100）
    "capital_trend": "inflow",       # 资金趋势（inflow/outflow/neutral）
    "main_net_inflow": 12500.0,      # 主力净流入（万元）
    "retail_net_inflow": 3200.0,     # 散户净流入（万元）
    "sentiment_index": 68.2,         # 情感指数（0-100）
    "market_mood": "bullish",        # 市场情绪（bullish/neutral/bearish）
    "conclusion": "市场热度高，资金持续流入，情绪乐观"
}
```

**使用示例**:
```python
from src.agents.business.hot_spot.capital_and_sentiment_ai import CapitalAndSentimentAI

ai = CapitalAndSentimentAI()
result = await ai.analyze(stock_code="600519", market="sh", days=5)

print(f"市场热度: {result.market_heat_score}/100")
print(f"资金趋势: {result.capital_trend}")
print(f"市场情绪: {result.market_mood}")
```

**优势**: 减少40%响应时间，统一资金情绪评分

---

### 1.2 新闻监控AI

**文件**: `src/agents/business/hot_spot/news_monitor_ai.py`

**用途**: 监控财经新闻，识别关键事件

**输入**:
```python
{
    "stock_code": "600519",
    "days": 7,                # 新闻时间范围
    "keywords": ["业绩", "分红"]  # 关键词过滤（可选）
}
```

**输出**:
```python
{
    "important_events": [      # 重要事件列表
        {
            "title": "贵州茅台2025年净利润增长15%",
            "time": "2025-03-14",
            "sentiment": "positive",
            "impact": "high"
        }
    ],
    "event_count": 5,
    "sentiment_distribution": {
        "positive": 3,
        "neutral": 1,
        "negative": 1
    }
}
```

**使用示例**:
```python
from src.agents.business.hot_spot.news_monitor_ai import NewsMonitorAI

ai = NewsMonitorAI()
result = await ai.analyze(stock_code="600519", days=7)

for event in result.important_events:
    print(f"[{event.time}] {event.title}")
    print(f"影响: {event.impact}, 情感: {event.sentiment}")
```

---

### 1.3 龙虎榜AI

**文件**: `src/agents/business/hot_spot/dragon_tiger_ai.py`

**用途**: 分析龙虎榜数据，追踪机构动向

**输入**:
```python
{
    "stock_code": "600519",
    "market": "sh",
    "days": 5
}
```

**输出**:
```python
{
    "institution_activity": "active",     # 机构活跃度
    "top_buyers": ["机构A", "机构B"],      # 前N大买家
    "top_sellers": ["机构C"],              # 前N大卖家
    "net_buy_amount": 5000.0,             # 净买入金额（万元）
    "conclusion": "机构大幅买入，看好后市"
}
```

---

### 1.4 竞争格局AI

**文件**: `src/agents/business/hot_spot/competition_pattern_ai.py`

**用途**: 分析行业竞争格局，识别龙头地位

**输入**:
```python
{
    "stock_code": "600519",
    "industry": "白酒"
}
```

**输出**:
```python
{
    "market_position": "leader",          # 市场地位（leader/challenger/niche）
    "market_share": 35.2,                 # 市场份额（%）
    "competitive_advantage": ["品牌", "渠道"],  # 竞争优势
    "main_competitors": ["五粮液", "洋河"],    # 主要竞争对手
    "conclusion": "行业龙头，品牌护城河深厚"
}
```

---

## 2. 产业分析军团

**职责**: 分析产业趋势，确定投资赛道

### 2.1 产业链分析AI

**文件**: `src/agents/business/industry_analysis/industry_chain_ai.py`

**用途**: 分析产业链结构，识别关键环节

**输入**:
```python
{
    "industry": "新能源汽车",
    "focus_segment": "电池"  # 关注环节（可选）
}
```

**输出**:
```python
{
    "upstream": ["锂矿", "钴矿"],         # 上游
    "midstream": ["电池制造", "电机"],    # 中游
    "downstream": ["整车", "充电桩"],     # 下游
    "key_links": ["电池制造"],           # 关键环节
    "investment_opportunities": ["上游资源", "中游技术"]
}
```

---

### 2.2 政策影响AI

**文件**: `src/agents/business/industry_analysis/policy_impact_ai.py`

**用途**: 分析政策对行业的影响

**输入**:
```python
{
    "industry": "新能源汽车",
    "policy_type": "subsidy"  # 政策类型（可选）
}
```

**输出**:
```python
{
    "policy_impact_score": 85.0,         # 政策影响评分（0-100）
    "impact_direction": "positive",       # 影响方向（positive/negative/neutral）
    "key_policies": [                    # 关键政策
        "新能源汽车购置补贴延续",
        "双积分政策趋严"
    ],
    "conclusion": "政策大力支持，行业景气度高"
}
```

---

### 2.3 景气度分析AI

**文件**: `src/agents/business/industry_analysis/prosperity_analysis_ai.py`

**用途**: 分析行业景气度，判断周期位置

**输入**:
```python
{
    "industry": "半导体",
    "indicators": ["产量", "价格", "库存"]  # 关注指标（可选）
}
```

**输出**:
```python
{
    "prosperity_index": 72.5,            # 景气指数（0-100）
    "cycle_position": "expansion",        # 周期位置（expansion/peak/contraction/trough）
    "trend": "upward",                    # 趋势（upward/downward/stable）
    "conclusion": "行业处于扩张期，景气度上行"
}
```

---

### 2.4 技术趋势AI

**文件**: `src/agents/business/industry_analysis/tech_trend_ai.py`

**用途**: 分析行业技术发展趋势

**输入**:
```python
{
    "industry": "人工智能"
}
```

**输出**:
```python
{
    "tech_maturity": "growth",            # 技术成熟度（emerging/growth/mature/declining）
    "key_technologies": [                # 关键技术
        "大语言模型",
        "计算机视觉",
        "自动驾驶"
    ],
    "breakthrough_potential": "high",    # 突破潜力
    "conclusion": "技术快速发展，突破潜力大"
}
```

---

### 2.5 估值比较AI

**文件**: `src/agents/business/industry_analysis/valuation_comparison_ai.py`

**用途**: 比较行业内公司估值水平

**输入**:
```python
{
    "stock_code": "600519",
    "industry": "白酒",
    "metrics": ["PE", "PB"]  # 对比指标（可选）
}
```

**输出**:
```python
{
    "industry_avg_pe": 25.5,             # 行业平均PE
    "stock_pe": 30.2,                    # 目标股票PE
    "percentile": 60,                    # 百分位（%）
    "valuation_level": "reasonable",     # 估值水平（cheap/reasonable/expensive）
    "conclusion": "估值略高于行业平均，处于合理区间"
}
```

---

## 3. 个股挖掘军团

**职责**: 深度分析个股，筛选投资标的

### 3.1 基本面分析AI

**文件**: `src/agents/business/stock/fundamental_analyzer.py`

**用途**: 分析财务数据，评估公司质量

**输入**:
```python
{
    "stock_code": "600519",
    "year": 2024                        # 分析年份（可选）
}
```

**输出**:
```python
{
    "revenue": 125.5,                   # 营业收入（亿元）
    "net_profit": 58.2,                 # 净利润（亿元）
    "roe": 28.5,                        # ROE（%）
    "roa": 18.2,                        # ROA（%）
    "debt_ratio": 15.3,                 # 资产负债率（%）
    "quality_score": 85.0,              # 质量评分（0-100）
    "conclusion": "财务健康，盈利能力强"
}
```

**使用示例**:
```python
from src.agents.business.stock.fundamental_analyzer import FundamentalAnalyzer

ai = FundamentalAnalyzer()
result = await ai.analyze(stock_code="600519")

print(f"营业收入: {result.revenue}亿元")
print(f"ROE: {result.roe}%")
print(f"质量评分: {result.quality_score}/100")
```

---

### 3.2 财务健康AI

**文件**: `src/agents/business/stock/financial_health_ai.py`

**用途**: 评估公司财务健康状况

**输入**:
```python
{
    "stock_code": "600519"
}
```

**输出**:
```python
{
    "health_score": 88.5,               # 健康评分（0-100）
    "solvency": "excellent",            # 偿债能力
    "liquidity": "good",                # 流动性
    "profitability": "excellent",       # 盈利能力
    "growth": "good",                   # 成长性
    "risk_factors": ["营收增速放缓"],   # 风险因素
    "conclusion": "财务状况优秀，无明显风险"
}
```

---

### 3.3 增长分析AI

**文件**: `src/agents/business/stock/growth_analysis_ai.py`

**用途**: 分析公司成长性

**输入**:
```python
{
    "stock_code": "600519",
    "years": 3                          # 分析年数
}
```

**输出**:
```python
{
    "revenue_cagr": 12.5,               # 营收CAGR（%）
    "profit_cagr": 15.2,                # 利润CAGR（%）
    "growth_stability": "stable",       # 增长稳定性
    "growth_driver": ["量价齐升"],      # 增长驱动力
    "conclusion": "增长稳定，持续性强"
}
```

---

### 3.4 技术分析AI ⭐ **完整版**

**文件**: `src/agents/business/technical_analyzer.py`

**用途**: 完整技术分析，包括趋势、指标、量价、形态

**输入**:
```python
{
    "stock_code": "600519",
    "period": "daily",                  # 周期（daily/weekly/monthly）
    "indicators": ["MACD", "KDJ", "RSI"]  # 指标（可选）
}
```

**输出**:
```python
{
    "trend": "uptrend",                 # 趋势（uptrend/downtway/sideways）
    "support_level": 1650.0,            # 支撑位
    "resistance_level": 1820.0,         # 压力位
    "indicators": {                     # 技术指标
        "MACD": {"signal": "buy", "value": 0.5},
        "KDJ": {"signal": "neutral", "value": 50},
        "RSI": {"signal": "buy", "value": 65}
    },
    "volume_analysis": {                # 量价分析
        "trend": "价涨量增",
        "health": "healthy"
    },
    "pattern": [                        # 形态识别
        "双底",
        "均线多头排列"
    ],
    "conclusion": "上升趋势，技术面健康"
}
```

**使用示例**:
```python
from src.agents.business.technical_analyzer import TechnicalAnalyzer

ai = TechnicalAnalyzer()
result = await ai.analyze(stock_code="600519", period="daily")

print(f"趋势: {result.trend}")
print(f"支撑位: {result.support_level}, 压力位: {result.resistance_level}")
print(f"MACD信号: {result.indicators['MACD']['signal']}")
```

---

### 3.5 资金规律AI

**文件**: `src/agents/business/stock/capital_regular_ai.py`

**用途**: 分析资金流动规律

**输入**:
```python
{
    "stock_code": "600519",
    "days": 30
}
```

**输出**:
```python
{
    "capital_pattern": "stable_inflow", # 资金规律
    "main_force_behavior": "持续买入", # 主力行为
    "retail_behavior": "跟随",         # 散户行为
    "conclusion": "资金持续流入，主力控盘"
}
```

---

### 3.6 历史周期AI

**文件**: `src/agents/business/stock/historical_cycle_ai.py`

**用途**: 分析历史周期规律

**输入**:
```python
{
    "stock_code": "600519",
    "cycle_type": "seasonal"            # 周期类型（seasonal/business）
}
```

**输出**:
```python
{
    "cycle_length": 365,                # 周期长度（天）
    "current_phase": "expansion",       # 当前阶段
    "next_phase": "peak",               # 下一阶段
    "historical_performance": {         # 历史表现
        "expansion": "+15%",
        "peak": "+5%",
        "contraction": "-10%"
    }
}
```

---

### 3.7 历史节点AI

**文件**: `src/agents/business/stock/historical_node_ai.py`

**用途**: 识别历史关键节点

**输入**:
```python
{
    "stock_code": "600519"
}
```

**输出**:
```python
{
    "key_nodes": [                      # 关键节点
        {
            "date": "2024-01-15",
            "event": "业绩预告超预期",
            "price_change": "+8%"
        }
    ],
    "pattern": "业绩驱动型",            # 股价模式
    "conclusion": "业绩发布前后常有超额收益"
}
```

---

### 3.8 K线形态AI

**文件**: `src/agents/business/stock/kline_pattern_ai.py`

**用途**: 识别K线形态特征

**输入**:
```python
{
    "stock_code": "600519",
    "days": 5                           # 分析天数
}
```

**输出**:
```python
{
    "patterns": [                       # 识别的形态
        "早晨之星",
        "锤子线"
    ],
    "reliability": "high",              # 可靠性
    "signal": "bullish",                # 信号方向
    "conclusion": "出现看涨形态，后市看涨"
}
```

---

### 3.9 芯片分析AI

**文件**: `src/agents/business/chip_analysis_ai.py`

**用途**: 分析筹码分布和集中度

**输入**:
```python
{
    "stock_code": "600519"
}
```

**输出**:
```python
{
    "chip_concentration": "high",       # 筹码集中度
    "main_cost": 1680.0,                # 主力成本
    "profit_ratio": 85.5,               # 盈利比例（%）
    "conclusion": "筹码高度集中，主力控盘"
}
```

---

## 4. 目标预测军团

**职责**: 预测目标价格，评估投资空间

### 4.1 估值与投资建议AI ⭐ **已整合**

**文件**: `src/agents/business/target/valuation_and_recommendation_ai.py`

**用途**: 整合估值、定价、评分，统一投资建议

**输入**:
```python
{
    "stock_code": "600519",
    "valuation_method": "DCF"           # 估值方法（DCF/PE/PB）
}
```

**输出**:
```python
{
    "intrinsic_value": 1850.0,          # 内在价值（元）
    "current_price": 1720.0,            # 当前价格（元）
    "safety_margin": 7.0,               # 安全边际（%）
    "target_price": 1950.0,             # 目标价格（元）
    "recommendation": "buy",            # 投资建议（buy/hold/sell）
    "confidence": 85.5,                 # 置信度（%）
    "price_space": "+13.4%",            # 价格空间
    "key_reasons": [                    # 核心理由
        "品牌护城河深厚",
        "业绩稳健增长",
        "估值合理"
    ]
}
```

**使用示例**:
```python
from src.agents.business.target.valuation_and_recommendation_ai import ValuationAndRecommendationAI

ai = ValuationAndRecommendationAI()
result = await ai.analyze(stock_code="600519")

print(f"内在价值: {result.intrinsic_value}元")
print(f"当前价格: {result.current_price}元")
print(f"投资建议: {result.recommendation}")
print(f"目标价格: {result.target_price}元")
print(f"价格空间: {result.price_space}")
```

**优势**:
- 消除估值、定价、评分之间的建议冲突
- API调用减少67%（3次 → 1次）
- 投资建议统一准确

---

### 4.2 利润预测AI

**文件**: `src/agents/business/target/profit_forecast_ai.py`

**用途**: 预测未来利润

**输入**:
```python
{
    "stock_code": "600519",
    "years": 3                          # 预测年数
}
```

**输出**:
```python
{
    "forecast_years": [2025, 2026, 2027],
    "predicted_profits": [65.2, 73.5, 82.8],  # 预测利润（亿元）
    "growth_rate": 12.5,                # 增长率（%）
    "confidence": 75.0,                 # 预测置信度（%）
    "conclusion": "未来3年利润稳定增长"
}
```

---

### 4.3 价格预测AI

**文件**: `src/agents/business/target/price_prediction_ai.py`

**用途**: 预测未来股价

**输入**:
```python
{
    "stock_code": "600519",
    "method": "monte_carlo"             # 预测方法
}
```

**输出**:
```python
{
    "predicted_prices": {               # 预测价格
        "3months": 1780.0,
        "6months": 1850.0,
        "12months": 1950.0
    },
    "probability": {                    # 涨跌概率
        "up": 65.5,
        "down": 34.5
    },
    "conclusion": "12个月目标价1950元"
}
```

---

### 4.4 质量评分AI

**文件**: `src/agents/business/target/quality_score_ai.py`

**用途**: 综合评分公司质量

**输入**:
```python
{
    "stock_code": "600519"
}
```

**输出**:
```python
{
    "quality_score": 88.5,              # 质量评分（0-100）
    "dimension_scores": {               # 维度评分
        "financial": 90.0,
        "management": 85.0,
        "competitiveness": 92.0,
        "growth": 85.0
    },
    "rating": "excellent",              # 评级
    "percentile": 95,                   # 行业百分位
    "conclusion": "优质公司，行业领先"
}
```

---

## 5. 策略执行军团

**职责**: 制定执行策略，控制投资风险

### 5.1 风险与时机AI ⭐ **已整合**

**文件**: `src/agents/business/strategy/risk_and_timing_ai.py`

**用途**: 整合风险控制和买入时机，综合投资建议

**输入**:
```python
{
    "stock_code": "600519",
    "target_price": 1950.0,             # 目标价格
    "risk_tolerance": "medium"          # 风险偏好
}
```

**输出**:
```python
{
    "risk_level": "medium",             # 风险等级
    "risk_score": 45.5,                 # 风险评分（0-100）
    "buy_timing": "good",               # 买入时机（excellent/good/neutral/bad）
    "timing_score": 75.0,               # 时机评分（0-100）
    "entry_zone": [1680, 1750],         # 建仓区间（元）
    "position_suggestion": "30%",       # 仓位建议
    "stop_loss": 1600.0,                # 止损价（元）
    "take_profit": 1950.0,              # 止盈价（元）
    "execution_plan": [                 # 执行计划
        "第一阶段（1680-1700）：建仓20%",
        "第二阶段（1700-1750）：加仓10%"
    ],
    "conclusion": "风险可控，时机良好，建议分批建仓"
}
```

**使用示例**:
```python
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

ai = RiskAndTimingAI()
result = await ai.analyze(
    stock_code="600519",
    target_price=1950.0,
    risk_tolerance="medium"
)

print(f"风险等级: {result.risk_level}")
print(f"买入时机: {result.buy_timing}")
print(f"建仓区间: {result.entry_zone[0]}-{result.entry_zone[1]}元")
print(f"仓位建议: {result.position_suggestion}")
print(f"止损价: {result.stop_loss}元, 止盈价: {result.take_profit}元")
```

**优势**:
- 综合评估风险和时机
- 提供完整的执行计划
- 明确止损止盈策略

---

### 5.2 场景分析AI

**文件**: `src/agents/business/strategy/scenario_analysis_ai.py`

**用途**: 分析不同市场场景下的表现

**输入**:
```python
{
    "stock_code": "600519",
    "scenarios": ["bull", "bear", "neutral"]  # 分析场景
}
```

**输出**:
```python
{
    "scenarios": {
        "bull": {"expected_return": "+25%", "probability": 60},
        "neutral": {"expected_return": "+5%", "probability": 30},
        "bear": {"expected_return": "-15%", "probability": 10}
    },
    "expected_return": "+16.5%",         # 期望收益
    "conclusion": "牛市概率高，期望收益可观"
}
```

---

### 5.3 仓位管理AI

**文件**: `src/agents/business/strategy/position_management_ai.py`

**用途**: 制定仓位管理策略

**输入**:
```python
{
    "stock_code": "600519",
    "total_capital": 100000,            # 总资金（元）
    "risk_tolerance": "medium"
}
```

**输出**:
```python
{
    "suggested_position": 30000,        # 建议仓位（元）
    "position_ratio": "30%",            # 仓位比例
    "build_strategy": [                 # 建仓策略
        {"phase": 1, "price": 1700, "ratio": "20%"},
        {"phase": 2, "price": 1650, "ratio": "10%"}
    ],
    "risk_control": {
        "max_loss": "-5%",
        "stop_loss": "1600"
    }
}
```

---

### 5.4 止损策略AI

**文件**: `src/agents/business/strategy/stop_loss_ai.py`

**用途**: 制定止损策略

**输入**:
```python
{
    "stock_code": "600519",
    "entry_price": 1720.0,              # 成本价
    "risk_tolerance": "medium"
}
```

**输出**:
```python
{
    "stop_loss_price": 1600.0,          # 止损价（元）
    "stop_loss_ratio": "-6.98%",        # 止损幅度
    "trailing_stop": True,              # 移动止损
    "stop_loss_script": """             # 止损脚本
        if price < stop_loss_price:
            sell()
    """,
    "conclusion": "建议设置1600元为止损价"
}
```

---

## 6. 结果验证军团

**职责**: 验证预测结果，持续优化改进

### 6.1 预测验证AI

**文件**: `src/agents/business/validation/prediction_validator_ai.py`

**用途**: 验证历史预测准确性

**输入**:
```python
{
    "stock_code": "600519",
    "prediction_type": "price"          # 预测类型
}
```

**输出**:
```python
{
    "accuracy": 75.5,                   # 准确率（%）
    "predictions": [                    # 历史预测
        {
            "date": "2024-01-15",
            "predicted": 1800.0,
            "actual": 1850.0,
            "error": "+2.8%"
        }
    ],
    "conclusion": "预测准确率较高"
}
```

---

### 6.2 回测分析AI

**文件**: `src/agents/business/validation/backtest_analysis_ai.py`

**用途**: 回测策略表现

**输入**:
```python
{
    "strategy": "value_investing",      # 策略名称
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
}
```

**输出**:
```python
{
    "total_return": "+125.5%",          # 总收益率
    "annual_return": "+22.5%",          # 年化收益率
    "max_drawdown": "-15.2%",           # 最大回撤
    "sharpe_ratio": 1.85,               # 夏普比率
    "win_rate": 65.5,                   # 胜率（%）
    "conclusion": "策略表现优秀"
}
```

---

### 6.3 实时追踪AI

**文件**: `src/agents/business/validation/realtime_tracking_ai.py`

**用途**: 实时追踪投资组合表现

**输入**:
```python
{
    "portfolio": ["600519", "000001"]   # 持仓股票
}
```

**输出**:
```python
{
    "total_value": 150000,              # 总市值（元）
    "total_return": "+12.5%",           # 总收益率
    "position_performance": [           # 个股表现
        {"code": "600519", "return": "+15.2%"},
        {"code": "000001", "return": "+8.5%"}
    ],
    "risk_alert": ["000001跌破支撑位"], # 风险提示
    "conclusion": "组合表现良好"
}
```

---

## 管理层

### Commander Agent（指挥官）

**文件**: `src/agents/management/commander_agent.py`

**职责**:
- 汇总各军团Agent的分析结果
- 质量把关（报告不合格打回去重做，最多4次）
- 生成最终投资报告

**输入**:
```python
{
    "stock_code": "600519",
    "agent_results": {                  # 各Agent结果
        "market_sentiment": {...},
        "fundamental": {...},
        "valuation": {...}
    }
}
```

**输出**:
```python
{
    "final_report": {                   # 最终报告
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "investment_rating": "推荐",     # 投资评级
        "target_price": 1950.0,
        "confidence": 85.5,
        "key_reasons": [                # 核心理由
            "品牌护城河深厚",
            "业绩稳健增长",
            "市场情绪乐观"
        ],
        "risk_warnings": [              # 风险提示
            "估值略高",
            "行业竞争加剧"
        ],
        "executive_summary": "..."      # 执行摘要
    }
}
```

---

### HR Agent（人力资源）

**文件**: `src/agents/management/hr_agent.py`

**职责**:
- 监控Agent性能
- 优化Agent配置
- 提升Agent能力

**输入**:
```python
{
    "agent_id": "market_sentiment",
    "performance_data": {               # 性能数据
        "accuracy": 75.5,
        "response_time": 1.2
    }
}
```

**输出**:
```python
{
    "optimization_plan": [              # 优化计划
        "调整温度参数",
        "增加上下文长度"
    ],
    "new_config": {                     # 新配置
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

---

## 自我进化系统

### 经验积累AI

**文件**: `src/agents/business/evolution/experience_accumulation_ai.py`

**职责**: 记录投资路径，建立经验数据库

**功能**:
- ✅ 记录投资路径（6维度分析 + 6核心指标预测）
- ✅ 验证预测准确性
- ✅ 案例分类（成功/失败/待验证）
- ✅ 经验查询和统计

**数据库**: `data/experience_db.json`

---

### 参数优化AI

**文件**: `src/agents/business/evolution/parameter_optimization_ai.py`

**职责**: 根据验证结果调整系统参数

**功能**:
- ✅ 分析系统性能表现
- ✅ 生成参数优化提案
- ✅ 安全边界控制（每次调整幅度<10%）
- ✅ 应用优化配置

**可优化参数**: PB/PE/ROE阈值、权重配置等

---

### 模式发现AI

**文件**: `src/agents/business/evolution/pattern_discovery_ai.py`

**职责**: 从经验案例中发现新的投资模式

**功能**:
- ✅ 从成功/失败案例中发现模式
- ✅ 验证模式有效性
- ✅ 模式库管理

**数据库**: `data/pattern_db.json`

---

## 使用示例

### 完整工作流示例

```python
"""
完整投资分析工作流
从热点捕捉到策略执行的完整流程
"""
import asyncio
from src.agents.business.hot_spot.capital_and_sentiment_ai import CapitalAndSentimentAI
from src.agents.business.stock.fundamental_analyzer import FundamentalAnalyzer
from src.agents.business.target.valuation_and_recommendation_ai import ValuationAndRecommendationAI
from src.agents.business.strategy.risk_and_timing_ai import RiskAndTimingAI

async def full_workflow(stock_code: str):
    """完整工作流"""

    # 1. 热点捕捉：资金与情绪分析
    sentiment_ai = CapitalAndSentimentAI()
    sentiment_result = await sentiment_ai.analyze(stock_code, market="sh", days=5)
    print(f"市场热度: {sentiment_result.market_heat_score}/100")
    print(f"情绪: {sentiment_result.market_mood}")

    # 2. 个股挖掘：基本面分析
    fundamental_ai = FundamentalAnalyzer()
    fundamental_result = await fundamental_ai.analyze(stock_code)
    print(f"质量评分: {fundamental_result.quality_score}/100")

    # 3. 目标预测：估值与投资建议
    valuation_ai = ValuationAndRecommendationAI()
    valuation_result = await valuation_ai.analyze(stock_code)
    print(f"内在价值: {valuation_result.intrinsic_value}元")
    print(f"投资建议: {valuation_result.recommendation}")

    # 4. 策略执行：风险与时机
    timing_ai = RiskAndTimingAI()
    timing_result = await timing_ai.analyze(
        stock_code,
        target_price=valuation_result.target_price,
        risk_tolerance="medium"
    )
    print(f"买入时机: {timing_result.buy_timing}")
    print(f"建仓区间: {timing_result.entry_zone[0]}-{timing_result.entry_zone[1]}元")

    # 汇总结果
    return {
        "sentiment": sentiment_result,
        "fundamental": fundamental_result,
        "valuation": valuation_result,
        "timing": timing_result
    }

# 运行工作流
result = asyncio.run(full_workflow("600519"))
```

---

## ✅ Agent使用检查清单

使用Agent前确认:

- [ ] 了解Agent职责和功能
- [ ] 准备输入参数（股票代码、市场等）
- [ ] 确认数据源可用（Yahoo Finance、AKShare等）
- [ ] 配置API密钥（智谱AI等）
- [ ] 运行测试验证功能
- [ ] 查看日志排查问题

---

## 📚 相关文档

- [快速开始指南](QUICK_START_GUIDE.md) - 环境搭建和基础使用
- [架构设计文档](ARCHITECTURE.md) - 系统架构详解
- [API参考文档](API.md) - 完整API文档
- [v2配置指南](CONFIG_V2_GUIDE.md) - GLM包月版配置

---

**最后更新**: 2026-03-15
**版本**: 1.3.0
**维护**: Agent Army Team

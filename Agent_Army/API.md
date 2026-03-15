# Agent Army - API 参考文档

**版本**: v2.0.0
**最后更新**: 2026-03-15
**API状态**: ✅ 稳定
**Agent总数**: 35个（管理层5个 + 业务层29个 + 自我进化3个）

---

## 📚 目录

- [管理层Agent API](#管理层agent-api)
  - [Commander Agent](#commander-agent)
  - [HR Agent](#hr-agent)
  - [自我进化系统](#自我进化系统)
- [业务层Agent API](#业务层agent-api)
  - [热点捕捉军团](#热点捕捉军团)
  - [产业分析军团](#产业分析军团)
  - [个股挖掘军团](#个股挖掘军团)
  - [目标预测军团](#目标预测军团)
  - [策略执行军团](#策略执行军团)
  - [结果验证军团](#结果验证军团)
- [工具库API](#工具库api)
- [数据模型](#数据模型)

---

## 管理层Agent API

### Commander Agent

**文件位置**: `src/agents/management/commander_agent.py`

#### 核心方法

##### `aggregate_reports(reports: List[Dict]) -> Dict`

汇总所有业务层AI的报告

**参数**:
- `reports`: 业务层AI报告列表

**返回**:
```python
{
    "summary": "汇总摘要",
    "key_findings": ["关键发现1", "关键发现2"],
    "recommendations": ["建议1", "建议2"],
    "risk_warnings": ["风险1", "风险2"],
    "confidence_scores": {"agent_1": 0.85, "agent_2": 0.92}
}
```

##### `quality_check(report: Dict, agent_name: str) -> Dict`

检查报告质量

**参数**:
- `report`: 待检查的报告
- `agent_name`: Agent名称

**返回**:
```python
{
    "passed": True,
    "score": 0.92,
    "issues": [],
    "suggestions": []
}
```

##### `monitor_accuracy(agent_name: str, prediction: Dict, actual: Dict) -> Dict`

监控预测准确度

**参数**:
- `agent_name`: Agent名称
- `prediction`: 预测结果
- `actual`: 实际结果

**返回**:
```python
{
    "accuracy": 0.85,
    "deviation": 0.12,
    "trend": "improving"
}
```

---

### HR Agent

**文件位置**: `src/agents/management/hr_agent.py`

#### 核心方法

##### `monitor_performance(agent_name: str) -> Dict`

监控Agent性能

**参数**:
- `agent_name`: Agent名称

**返回**:
```python
{
    "agent_name": "fundamental_analyzer",
    "performance_score": 0.88,
    "response_time": 1.2,
    "accuracy": 0.85,
    "last_update": "2026-03-15 10:00:00"
}
```

##### `optimize_agent_config(agent_name: str, config: Dict) -> Dict`

优化Agent配置

**参数**:
- `agent_name`: Agent名称
- `config`: 新配置

**返回**:
```python
{
    "optimized": True,
    "old_config": {...},
    "new_config": {...},
    "improvement": "15% faster"
}
```

---

### 自我进化系统

**文件位置**: `src/agents/business/evolution/`

#### 1. ExperienceAccumulationAI（经验积累AI）

##### `record_investment_path(stock_code, dimensions, prediction, analysis_date)`

记录投资路径

**参数**:
- `stock_code` (str): 股票代码
- `dimensions` (dict): 6维度分析数据
- `prediction` (dict): 预测结果
- `analysis_date` (date, optional): 分析日期

**返回**: `record_id` (str)

**示例**:
```python
from src.agents.business.evolution import ExperienceAccumulationAI

ai = ExperienceAccumulationAI()
record_id = await ai.record_investment_path(
    stock_code="300750",
    dimensions={
        "fundamental": {"pb": 0.8, "roe": 15.0},
        "technical": {"trend": "up"},
        # ... 其他维度
    },
    prediction={
        "stop_loss": 10.00,
        "buy_price": 10.80,
        "target_price": 13.50,
        "time_window": "3个月",
        "confidence": 0.75
    }
)
# 返回: "300750_20260315"
```

##### `verify_prediction(record_id, actual_stop_loss, actual_buy_price, actual_target_price, current_price)`

验证预测准确性

**参数**:
- `record_id` (str): 记录ID
- `actual_stop_loss` (float, optional): 实际止损价
- `actual_buy_price` (float, optional): 实际买入价
- `actual_target_price` (float, optional): 实际目标价
- `current_price` (float, optional): 当前价格

**返回**:
```python
{
    "record_id": "300750_20260315",
    "case_type": "success",  # success/failure/pending
    "accuracy": 1.0,
    "deviation": 0.037,
    "verification_summary": "Predict: Target 13.50 | Buy 10.80 | Stop 10.00 | Actual 14.00 | [OK] Accurate"
}
```

##### `query_experience(stock_code=None, case_type=None, status=None, limit=10)`

查询经验案例

**参数**:
- `stock_code` (str, optional): 股票代码筛选
- `case_type` (str, optional): 案例类型（success/failure/pending）
- `status` (str, optional): 状态筛选
- `limit` (int): 返回数量限制

**返回**: 案例列表 (List[Dict])

##### `get_statistics()`

获取经验数据库统计

**返回**:
```python
{
    "total_cases": 150,
    "success_cases": 90,
    "failure_cases": 30,
    "pending_cases": 30,
    "success_rate": 0.60
}
```

---

#### 2. ParameterOptimizationAI（参数优化AI）

##### `analyze_performance(validation_results)`

分析参数表现

**参数**:
- `validation_results` (List[Dict]): 验证结果列表

**返回**:
```python
{
    "total_cases": 50,
    "average_accuracy": 0.75,
    "success_rate": 0.68,
    "weak_points": ["整体准确率偏低", "目标价预测偏差较大"],
    "recommendations": ["建议调整基本面分析权重", "建议收紧PB/PE阈值范围"]
}
```

##### `optimize_parameters(performance_report, current_config=None)`

生成参数优化提案

**参数**:
- `performance_report` (dict): 性能报告
- `current_config` (dict, optional): 当前配置

**返回**:
```python
{
    "optimization_id": "opt_20260315100000",
    "parameter_adjustments": [
        {
            "parameter": "pb_min",
            "old_value": 0.8,
            "new_value": 0.84,
            "reason": "提高PB下限，筛选更优质标的"
        }
    ],
    "weight_adjustments": [
        {
            "dimension": "fundamental",
            "old_weight": 0.30,
            "new_weight": 0.32,
            "reason": "提高基本面权重，增强安全边际"
        }
    ],
    "expected_improvement": "预计提升准确率5-10%，降低风险偏好",
    "risk_assessment": "低风险：参数调整幅度<10%，在安全范围内"
}
```

##### `apply_optimization(proposal, auto_apply=False)`

应用优化配置

**参数**:
- `proposal` (dict): 优化提案
- `auto_apply` (bool): 是否自动应用（默认False，需人工确认）

**返回**:
```python
{
    "optimization_id": "opt_20260315100000",
    "applied": True,
    "applied_at": "2026-03-15 10:05:00",
    "changes": ["pb_min: 0.8 -> 0.84", "weights.fundamental: 0.30 -> 0.32"],
    "new_config": {...}
}
```

---

#### 3. PatternDiscoveryAI（模式发现AI）

##### `discover_patterns(experience_cases, min_support=3)`

从经验库中发现模式

**参数**:
- `experience_cases` (List[Dict]): 经验案例列表
- `min_support` (int): 最小支持度（至少出现几次才算模式）

**返回**: 发现的模式列表

**示例**:
```python
from src.agents.business.evolution import PatternDiscoveryAI

ai = PatternDiscoveryAI()
patterns = await ai.discover_patterns(
    experience_cases=experience_cases,
    min_support=3
)

# 返回:
# [
#     {
#         "pattern_id": "success_low_pb_high_roe_20260315",
#         "pattern_name": "低PB高ROE盈利模式",
#         "pattern_type": "success",
#         "description": "PB<1.0 且 ROE>10% 的股票表现优异",
#         "conditions": {"pb_max": 1.0, "roe_min": 10},
#         "support": 15,
#         "confidence": 0.85,
#         "examples": ["300750_20260315", "600036_20260314"]
#     },
#     ...
# ]
```

##### `verify_pattern(pattern, new_cases)`

验证模式有效性

**参数**:
- `pattern` (dict): 待验证的模式
- `new_cases` (List[Dict]): 新的案例数据

**返回**:
```python
{
    "pattern_id": "success_low_pb_high_roe_20260315",
    "verified": True,
    "matched_count": 10,
    "verification_rate": 0.80,  # >= 0.6 为通过验证
    "original_confidence": 0.85,
    "verified_at": "2026-03-15 10:10:00"
}
```

##### `search_patterns(stock_code=None, pattern_type=None, limit=10)`

搜索模式

**参数**:
- `stock_code` (str, optional): 股票代码筛选
- `pattern_type` (str, optional): 模式类型（success/failure）
- `limit` (int): 返回数量限制

**返回**: 匹配的模式列表

---

## 业务层Agent API

### 热点捕捉军团

#### 1. CapitalAndSentimentAI（资金与情绪AI）

**文件位置**: `src/agents/business/hot_spot/capital_and_sentiment_ai.py`

##### `analyze_market_sentiment(stock_code)`

分析市场情绪

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "sentiment_score": 0.75,
    "capital_flow": "in",
    "market_heat": "high",
    "analysis": {
        "sentiment": {
            "score": 0.75,
            "trend": "up",
            "key_factors": ["政策利好", "业绩超预期"]
        },
        "capital": {
            "flow": "in",
            "net_inflow": 150000000,
            "main_force_inflow": 120000000
        },
        "combined_score": 0.72  # 60%资金 + 40%情绪
    }
}
```

#### 2. DragonTigerAI（龙虎榜AI）

**文件位置**: `src/agents/business/hot_spot/dragon_tiger_ai.py`

##### `analyze_dragon_tiger(stock_code, days=5)`

分析龙虎榜数据

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 查询天数

**返回**:
```python
{
    "stock_code": "300750",
    "appearances": 3,
    "reasons": ["涨幅偏离值达7%", "换手率达20%"],
    "top_buyers": ["机构专用", "华泰证券"],
    "top_sellers": ["中信证券", "国泰君安"],
    "net_buy": 50000000,
    "signal": "bullish"
}
```

#### 3. ChipAnalysisAI（筹码分析AI）

**文件位置**: `src/agents/business/hot_spot/chip_analysis_ai.py`

##### `analyze_chip_distribution(stock_code)`

分析筹码分布

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "concentration_ratio": 0.65,
    "main_force_holding": 0.55,
    "retail_holding": 0.30,
    "institution_holding": 0.15,
    "chip_distribution": {
        "10yuan": 0.15,
        "20yuan": 0.25,
        "30yuan": 0.35,
        "40yuan": 0.25
    }
}
```

#### 4. NewsMonitorAI（新闻监控AI）

**文件位置**: `src/agents/business/hot_spot/news_monitor_ai.py`

##### `monitor_news(stock_code, days=7)`

监控新闻动态

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 监控天数

**返回**:
```python
{
    "stock_code": "300750",
    "news_count": 15,
    "key_events": [
        {
            "title": "宁德时代发布钠离子电池",
            "impact": "positive",
            "importance": "high"
        }
    ],
    "sentiment_trend": "up",
    "attention_score": 0.85
}
```

---

### 产业分析军团

#### 1. MacroEconomicAI（宏观经济AI）

**文件位置**: `src/agents/business/industry_analysis/macro_economic_ai.py`

##### `analyze_macro_economic(industry)`

分析宏观经济环境

**参数**:
- `industry` (str): 行业名称

**返回**:
```python
{
    "industry": "新能源",
    "gdp_growth": 6.5,
    "cpi": 2.1,
    "ppi": -0.5,
    "monetary_policy": "neutral",
    "fiscal_policy": "expansionary",
    "impact": "positive",
    "key_factors": ["政策支持", "产业升级"]
}
```

#### 2. IndustryChainAI（产业链AI）

**文件位置**: `src/agents/business/industry_analysis/industry_chain_ai.py`

##### `analyze_industry_chain(stock_code)`

分析产业链位置

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "industry": "锂电池",
    "position": "中游",
    "upstream": ["锂矿开采", "锂盐提炼"],
    "downstream": ["新能源汽车", "储能系统"],
    "competitive_position": "leading",
    "bargaining_power": "strong"
}
```

#### 3. CompetitionPatternAI（竞争格局AI）

**文件位置**: `src/agents/business/industry_analysis/competition_pattern_ai.py`

##### `analyze_competition(stock_code)`

分析竞争格局

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "market_share": 0.32,
    "ranking": 1,
    "competitors": ["比亚迪", "国轩高科"],
    "competitive_advantage": ["技术领先", "规模效应"],
    "market_concentration": "high"
}
```

#### 4. PolicyImpactAI（政策影响AI）

**文件位置**: `src/agents/business/industry_analysis/policy_impact_ai.py`

##### `analyze_policy_impact(stock_code)`

分析政策影响

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "policy_environment": "supportive",
    "key_policies": ["新能源补贴政策", "双碳目标"],
    "impact_level": "high",
    "impact_duration": "long-term",
    "risk_factors": ["补贴退坡"]
}
```

#### 5. IndustryCycleAI（产业周期AI）

**文件位置**: `src/agents/business/industry_analysis/industry_cycle_ai.py`

##### `analyze_industry_cycle(stock_code)`

分析产业周期

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "industry": "锂电池",
    "cycle_phase": "growth",
    "cycle_characteristics": ["需求旺盛", "产能扩张"],
    "phase_duration": "3-5年",
    "key_indicators": {
        "capacity_utilization": 0.85,
        "investment_growth": 0.35
    }
}
```

---

### 个股挖掘军团

#### 1. FundamentalAnalyzer（基本面分析AI）

**文件位置**: `src/agents/business/fundamental_analyzer.py`

##### `analyze(stock_code)`

分析基本面

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "company_name": "宁德时代",
    "financial_health": {
        "roe": 18.5,
        "roa": 12.3,
        "debt_ratio": 45.2,
        "current_ratio": 1.8,
        "score": 0.85
    },
    "growth_analysis": {
        "revenue_growth": 35.2,
        "profit_growth": 42.1,
        "score": 0.90
    },
    "valuation": {
        "pe": 45.2,
        "pb": 8.5,
        "ps": 5.2,
        "score": 0.75
    },
    "overall_score": 0.83,
    "recommendation": "buy"
}
```

#### 2. TechnicalAnalyzer（技术分析AI）

**文件位置**: `src/agents/business/technical_analyzer.py`

##### `analyze(stock_code)`

分析技术面

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "trend": "up",
    "indicators": {
        "macd": {"value": 0.5, "signal": "buy"},
        "kdj": {"k": 80, "d": 75, "signal": "overbought"},
        "rsi": {"value": 65, "signal": "neutral"},
        "bollinger": {"upper": 15.2, "middle": 14.0, "lower": 12.8}
    },
    "support_levels": [13.5, 13.0, 12.5],
    "resistance_levels": [14.5, 15.0, 15.5],
    "volume_analysis": {
        "trend": "increasing",
        "ratio": 1.5
    },
    "signal": "bullish"
}
```

#### 3. FinancialHealthAI（财务健康AI）

**文件位置**: `src/agents/business/stock/financial_health_ai.py`

##### `analyze_financial_health(stock_code)`

分析财务健康度

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "health_score": 0.88,
    "debt_ratio": 0.45,
    "current_ratio": 1.8,
    "quick_ratio": 1.2,
    "cash_flow": "positive",
    "financial_stability": "strong"
}
```

#### 4. GrowthAnalysisAI（成长分析AI）

**文件位置**: `src/agents/business/stock/growth_analysis_ai.py`

##### `analyze_growth(stock_code)`

分析成长性

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "revenue_growth": 0.35,
    "profit_growth": 0.42,
    "growth_sustainability": "high",
    "growth_drivers": ["市场需求", "技术优势"],
    "growth_stage": "rapid"
}
```

#### 5. ValuationModelAI（估值模型AI）

**文件位置**: `src/agents/business/stock/valuation_model_ai.py`

##### `calculate_valuation_model(stock_code)`

计算估值模型

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "intrinsic_value": 15.50,
    "current_price": 14.20,
    "upside_potential": 0.092,
    "valuation_methods": {
        "pe": 16.50,
        "pb": 15.80,
        "dcf": 14.20
    }
}
```

#### 6. KlinePatternAI（K线形态AI）

**文件位置**: `src/agents/business/stock/kline_pattern_ai.py`

##### `analyze_kline_pattern(stock_code)`

分析K线形态

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "patterns": ["早晨之星", "MACD金叉"],
    "reliability": 0.75,
    "signal": "bullish",
    "target_price": 15.50
}
```

#### 7. HistoricalNodeAI（历史节点AI）

**文件位置**: `src/agents/business/stock/historical_node_ai.py`

##### `analyze_historical_nodes(stock_code)`

分析历史关键节点

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "key_nodes": [
        {"date": "2025-01-15", "event": "发布业绩预告", "impact": "positive"},
        {"date": "2025-03-10", "event": "进入产业扩张期", "impact": "positive"}
    ],
    "current_phase": "成长期",
    "next_catalyst": "新产品发布"
}
```

#### 8. HistoricalCycleAI（历史周期AI）

**文件位置**: `src/agents/business/stock/historical_cycle_ai.py`

##### `analyze_historical_cycle(stock_code)`

分析历史周期

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "cycle_length": "3年",
    "current_phase": "上升期",
    "cycle_position": 0.6,
    "historical_performance": {
        "up_cycles": 4,
        "down_cycles": 3,
        "avg_up_duration": "18个月"
    }
}
```

#### 9. CapitalRegularAI（资金规律AI）

**文件位置**: `src/agents/business/stock/capital_regular_ai.py`

##### `analyze_capital_pattern(stock_code)`

分析资金规律

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "capital_pattern": "持续流入",
    "main_force_activity": "active",
    "retail_sentiment": "bullish",
    "fund_flow_cycle": "季度末流入"
}
```

---

### 目标预测军团

#### 1. ValuationAndRecommendationAI（估值与投资建议AI）

**文件位置**: `src/agents/business/target/valuation_and_recommendation_ai.py`

##### `calculate_valuation(stock_code)`

计算估值

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "intrinsic_value": 15.50,
    "current_price": 14.20,
    "safety_margin": 0.085,  # 8.5%
    "methods": {
        "pe_method": 16.50,
        "pb_method": 15.80,
        "dcf_method": 14.20
    },
    "target_price": 15.50,
    "recommendation": "buy",
    "confidence": 0.85
}
```

#### 2. PricePredictionAI（价格预测AI）

**文件位置**: `src/agents/business/target/price_prediction_ai.py`

##### `predict_price(stock_code, timeframe)`

预测价格

**参数**:
- `stock_code` (str): 股票代码
- `timeframe` (str): 时间窗口（1m/3m/6m/1y）

**返回**:
```python
{
    "stock_code": "300750",
    "current_price": 14.20,
    "timeframe": "3m",
    "predicted_price": 15.50,
    "upside_potential": 0.092,  # 9.2%
    "probability": 0.75,
    "scenarios": {
        "bullish": {"price": 16.50, "probability": 0.30},
        "base": {"price": 15.50, "probability": 0.50},
        "bearish": {"price": 13.50, "probability": 0.20}
    }
}
```

#### 3. QualityScoreAI（质量评分AI）

**文件位置**: `src/agents/business/target/quality_score_ai.py`

##### `calculate_quality_score(stock_code)`

计算质量评分

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "quality_score": 0.88,
    "score_components": {
        "fundamental": 0.90,
        "technical": 0.85,
        "growth": 0.92,
        "financial_health": 0.86
    },
    "rating": "excellent",
    "percentile": 95
}
```

#### 4. ProfitForecastAI（盈利预测AI）

**文件位置**: `src/agents/business/target/profit_forecast_ai.py`

##### `forecast_profit(stock_code, quarters=4)`

预测盈利

**参数**:
- `stock_code` (str): 股票代码
- `quarters` (int): 预测季度数

**返回**:
```python
{
    "stock_code": "300750",
    "forecast_quarters": [
        {"quarter": "2026Q1", "profit": 12.5, "growth": 0.35},
        {"quarter": "2026Q2", "profit": 13.8, "growth": 0.38}
    ],
    "annual_profit": 52.5,
    "confidence": 0.80
}
```

---

### 策略执行军团

#### 1. RiskAndTimingAI（风险与时机AI）

**文件位置**: `src/agents/business/strategy/risk_and_timing_ai.py`

##### `analyze_risk_and_timing(stock_code)`

分析风险和时机

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "current_price": 14.20,
    "risk_analysis": {
        "risk_level": "medium",
        "risk_score": 0.45,
        "max_drawdown": 0.12,
        "volatility": 0.25
    },
    "timing_analysis": {
        "signal": "buy",
        "entry_price": 14.20,
        "stop_loss": 13.00,
        "target_price": 15.50,
        "time_window": "3个月"
    },
    "position_sizing": {
        "recommended_position": 0.15,  # 15%仓位
        "risk_per_trade": 0.02
    }
}
```

#### 2. PositionManagementAI（仓位管理AI）

**文件位置**: `src/agents/business/strategy/position_management_ai.py`

##### `calculate_position(stock_code, account_value, risk_tolerance)`

计算仓位

**参数**:
- `stock_code` (str): 股票代码
- `account_value` (float): 账户总值
- `risk_tolerance` (str): 风险偏好（conservative/moderate/aggressive）

**返回**:
```python
{
    "stock_code": "300750",
    "account_value": 1000000,
    "recommended_position": 150000,  # 15%仓位
    "position_percentage": 0.15,
    "shares": 10563,
    "risk_amount": 3000,
    "pyramid_plan": [
        {"price": 14.20, "position": 0.40},
        {"price": 13.80, "position": 0.35},
        {"price": 13.50, "position": 0.25}
    ]
}
```

#### 3. ScenarioAnalysisAI（情景分析AI）

**文件位置**: `src/agents/business/strategy/scenario_analysis_ai.py`

##### `analyze_scenarios(stock_code)`

分析情景

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "scenarios": {
        "bullish": {"probability": 0.30, "return": 0.25},
        "base": {"probability": 0.50, "return": 0.10},
        "bearish": {"probability": 0.20, "return": -0.15}
    },
    "expected_return": 0.105,
    "risk_adjusted_return": 0.18
}
```

#### 4. SellTimingAI（卖出时机AI）

**文件位置**: `src/agents/business/strategy/sell_timing_ai.py`

##### `analyze_sell_timing(stock_code, buy_price)`

分析卖出时机

**参数**:
- `stock_code` (str): 股票代码
- `buy_price` (float): 买入价格

**返回**:
```python
{
    "stock_code": "300750",
    "buy_price": 14.20,
    "current_price": 15.50,
    "sell_signals": [
        {"signal": "target_reached", "action": "sell_50%"},
        {"signal": "technical_overbought", "action": "sell_30%"}
    ],
    "recommended_sell_price": 16.00
}
```

---

### 结果验证军团

#### 1. BacktestAnalysisAI（回测分析AI）

**文件位置**: `src/agents/business/validation/backtest_analysis_ai.py`

##### `backtest(strategy, start_date, end_date)`

回测策略

**参数**:
- `strategy` (dict): 策略定义
- `start_date` (str): 开始日期
- `end_date` (str): 结束日期

**返回**:
```python
{
    "strategy_name": "低PB高ROE策略",
    "period": "2023-01-01 to 2024-12-31",
    "total_return": 0.35,  # 35%
    "annual_return": 0.18,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.12,
    "win_rate": 0.65,
    "trades": 50,
    "benchmark_return": 0.10,
    "excess_return": 0.25
}
```

#### 2. PredictionValidatorAI（预测验证AI）

**文件位置**: `src/agents/business/validation/prediction_validator_ai.py`

##### `validate_prediction(record_id, actual_data)`

验证预测

**参数**:
- `record_id` (str): 记录ID
- `actual_data` (dict): 实际数据

**返回**:
```python
{
    "record_id": "300750_20260315",
    "prediction": {
        "target_price": 15.50,
        "buy_price": 14.20,
        "stop_loss": 13.00
    },
    "actual": {
        "target_price": 16.00,
        "buy_price": 14.20,
        "stop_loss": 13.50
    },
    "accuracy": {
        "target_price": 0.97,
        "buy_price": 1.00,
        "stop_loss": 0.96
    },
    "overall_accuracy": 0.98,
    "case_type": "success"
}
```

#### 3. RealtimeTrackingAI（实时跟踪AI）

**文件位置**: `src/agents/business/validation/realtime_tracking_ai.py`

##### `track_realtime(stock_code, prediction)`

实时跟踪

**参数**:
- `stock_code` (str): 股票代码
- `prediction` (dict): 预测数据

**返回**:
```python
{
    "stock_code": "300750",
    "current_price": 15.20,
    "target_price": 15.50,
    "progress": 0.85,
    "status": "on_track",
    "alert": None
}
```

#### 4. StrategyOptimizationAI（策略优化AI）

**文件位置**: `src/agents/business/validation/strategy_optimization_ai.py`

##### `optimize_strategy(backtest_results)`

优化策略

**参数**:
- `backtest_results` (dict): 回测结果

**返回**:
```python
{
    "original_sharpe": 1.5,
    "optimized_sharpe": 1.8,
    "improvement": 0.20,
    "optimization_suggestions": [
        "提高止损阈值",
        "延长持有周期"
    ]
}
```

#### 5. PerformanceAttributionAI（业绩归因AI）

**文件位置**: `src/agents/business/validation/performance_attribution_ai.py`

##### `attribute_performance(portfolio_returns)`

业绩归因

**参数**:
- `portfolio_returns` (dict): 组合收益

**返回**:
```python
{
    "total_return": 0.25,
    "attribution": {
        "stock_selection": 0.15,
        "timing": 0.05,
        "industry_allocation": 0.05
    },
    "benchmark_return": 0.10,
    "excess_return": 0.15
}
```

#### 6. RiskAttributionAI（风险归因AI）

**文件位置**: `src/agents/business/validation/risk_attribution_ai.py`

##### `attribute_risk(portfolio_risk)`

风险归因

**参数**:
- `portfolio_risk` (dict): 组合风险

**返回**:
```python
{
    "total_risk": 0.18,
    "attribution": {
        "market_risk": 0.10,
        "industry_risk": 0.05,
        "specific_risk": 0.03
    }
}
```

#### 7. OptionsAI（期权分析AI）

**文件位置**: `src/agents/business/validation/options_ai.py`

##### `analyze_options(stock_code)`

分析期权

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "options_available": True,
    "put_call_ratio": 0.65,
    "implied_volatility": 0.25,
    "options_sentiment": "bullish"
}
```

---

## 工具库API

### NewsTool（新闻工具）

**文件位置**: `src/core/tools/data_source/news_tool.py`

#### `fetch_news(stock_code, days=7)`

获取新闻

**参数**:
- `stock_code` (str): 股票代码
- `days` (int): 查询天数

**返回**:
```python
[
    {
        "title": "宁德时代发布钠离子电池",
        "content": "...",
        "publish_time": "2026-03-15 09:30:00",
        "source": "财联社",
        "url": "https://..."
    },
    ...
]
```

#### `analyze_sentiment(text)`

分析情感

**参数**:
- `text` (str): 文本内容

**返回**:
```python
{
    "sentiment": "positive",  # positive/negative/neutral
    "score": 0.75,
    "confidence": 0.85
}
```

---

### FinancialTool（财务工具）

**文件位置**: `src/core/tools/data_source/financial_tool.py`

#### `get_financials(stock_code)`

获取财务数据

**参数**:
- `stock_code` (str): 股票代码

**返回**:
```python
{
    "stock_code": "300750",
    "company_name": "宁德时代",
    "financials": {
        "revenue": 369000000000,
        "net_profit": 45000000000,
        "roe": 18.5,
        "debt_ratio": 45.2
    },
    "valuation": {
        "pe": 45.2,
        "pb": 8.5,
        "market_cap": 650000000000
    }
}
```

---

### LLMTool（大模型工具）

**文件位置**: `src/core/tools/ai_service/llm_tool.py`

#### `generate(prompt, model="glm-4")`

生成文本

**参数**:
- `prompt` (str): 提示词
- `model` (str): 模型名称

**返回**:
```python
{
    "text": "生成的文本内容",
    "model": "glm-4",
    "tokens_used": 1500,
    "cost": 0.01
}
```

---

### FormulaTool（公式工具）

**文件位置**: `src/core/tools/calculation/formula_tool.py`

#### `calculate(formula_name, data)`

计算公式

**参数**:
- `formula_name` (str): 公式名称
- `data` (dict): 输入数据

**返回**:
```python
{
    "formula_name": "roe",
    "result": 18.5,
    "unit": "%"
}
```

---

## 数据模型

### 投资决策数据模型

```python
class InvestmentDecision(BaseModel):
    stock_code: str
    analysis_date: date

    # 6维度分析
    fundamental: Dict[str, Any]
    technical: Dict[str, Any]
    capital: Dict[str, Any]
    policy: Dict[str, Any]
    historical: Dict[str, Any]
    industry: Dict[str, Any]

    # 预测结果
    prediction: Prediction

    # 置信度
    confidence: float
```

### 预测结果数据模型

```python
class Prediction(BaseModel):
    stop_loss: float
    buy_price: float
    cost_price: float
    resistance: List[float]
    time_window: str
    target_price: float
    confidence: float
```

### 验证结果数据模型

```python
class ValidationResult(BaseModel):
    record_id: str
    stock_code: str
    case_type: str  # success/failure/pending
    accuracy: float
    deviation: float
    verification_summary: str
```

---

## 错误处理

所有API方法在遇到错误时会返回统一格式的错误响应：

```python
{
    "success": False,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {}
    }
}
```

### 常见错误代码

- `INVALID_STOCK_CODE`: 股票代码无效
- `DATA_NOT_AVAILABLE`: 数据不可用
- `API_RATE_LIMIT`: API调用频率限制
- `INSUFFICIENT_DATA`: 数据不足
- `CALCULATION_ERROR`: 计算错误

---

## 版本历史

- **v2.0.0** (2026-03-15): 添加自我进化系统API，补充所有遗漏Agent（共35个）
- **v1.3.0** (2026-03-15): 添加自我进化系统API
- **v1.2.0** (2026-03-14): 添加整合Agent API（4个整合Agent）
- **v1.1.0** (2026-03-10): 添加工具库API
- **v1.0.0** (2026-03-01): 初始版本

---

**文档维护**: Agent Army开发团队
**最后更新**: 2026-03-15
**Agent总数**: 35个（管理层5个 + 业务层29个 + 自我进化3个）
**API状态**: ✅ 稳定

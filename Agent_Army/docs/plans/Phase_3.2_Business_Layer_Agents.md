# Phase 3.2 - 业务层Agent开发计划

**创建日期**: 2026-03-14
**当前进度**: 6/24个业务层Agent已完成（25%）
**目标**: 完成18个业务层Agent

---

## 📊 当前状态

### ✅ 已完成（6个）

| 军团 | Agent | 文件 | 状态 |
|------|-------|------|------|
| 热点捕捉军团 | 新闻监控AI | `hot_spot/news_monitor.py` | ✅ 已重构 |
| 产业分析军团 | 产业链分析AI | `industry/industry_analyzer.py` | ✅ 已完成 |
| 个股挖掘军团 | 基本面分析AI | `stock/fundamental_analyzer.py` | ✅ 已重构 |
| 目标预测军团 | 目标定价AI | `target/target_pricing_ai.py` | ✅ 已完成 |
| 策略执行军团 | 买入时机AI | `strategy/buy_timing_ai.py` | ✅ 已完成 |
| 结果验证军团 | 预测验证AI | `validation/prediction_validator_ai.py` | ✅ 已完成 |

---

## 📋 待完成计划（18个）

### 🎯 批次1：热点捕捉军团（3个）

#### 1.1 市场情绪AI (Market Sentiment AI)
- **文件**: `hot_spot/market_sentiment_ai.py`
- **职责**: 分析市场情绪、舆论导向
- **输入**: 新闻、社交媒体、论坛数据
- **输出**: 情感指数、热度排名
- **工具**: NewsTool, NLPTool
- **预计**: 2小时

#### 1.2 资金流向AI (Capital Flow AI)
- **文件**: `hot_spot/capital_flow_ai.py`
- **职责**: 追踪资金流入流出
- **输入**: 股票交易数据、资金数据
- **输出**: 资金流向报告、主力资金分析
- **工具**: FinancialTool
- **预计**: 2小时

#### 1.3 龙虎榜AI (Dragon Tiger List AI)
- **文件**: `hot_spot/dragon_tiger_ai.py`
- **职责**: 分析龙虎榜数据
- **输入**: 龙虎榜数据
- **输出**: 机构动向、游资跟踪
- **工具**: FinancialTool
- **预计**: 2小时

---

### 🎯 批次2：产业分析军团（2个）

#### 2.1 竞争格局AI (Competition Pattern AI)
- **文件**: `industry/competition_pattern_ai.py`
- **职责**: 分析行业竞争态势
- **输入**: 行业数据、公司数据
- **输出**: 竞争格局报告、龙头识别
- **工具**: FinancialTool, NLPTool
- **预计**: 2小时

#### 2.2 政策影响AI (Policy Impact AI)
- **文件**: `industry/policy_impact_ai.py`
- **职责**: 解读行业政策影响
- **输入**: 政策文件、新闻
- **输出**: 政策影响评估
- **工具**: NewsTool, NLPTool
- **预计**: 2小时

---

### 🎯 批次3：个股挖掘军团（2个）

#### 3.1 技术分析AI (Technical Analysis AI)
- **文件**: `stock/technical_analyzer.py`
- **职责**: 分析技术指标、走势形态
- **输入**: 股价数据、成交量
- **输出**: 技术分析报告、买卖信号
- **工具**: FinancialTool, FormulaTool
- **预计**: 2小时

#### 3.2 财务健康AI (Financial Health AI)
- **文件**: `stock/financial_health_ai.py`
- **职责**: 评估财务健康度
- **输入**: 财务数据
- **输出**: 财务健康评分、风险预警
- **工具**: FinancialTool, FormulaTool
- **预计**: 2小时

---

### 🎯 批次4：目标预测军团（3个）

#### 4.1 盈利预测AI (Earnings Forecast AI)
- **文件**: `target/earnings_forecast_ai.py`
- **职责**: 预测公司盈利
- **输入**: 财务数据、行业数据
- **输出**: 盈利预测报告
- **工具**: FinancialTool, FormulaTool, LLMTool
- **预计**: 2小时

#### 4.2 估值模型AI (Valuation Model AI)
- **文件**: `target/valuation_model_ai.py`
- **职责**: 多模型估值
- **输入**: 财务数据、市场数据
- **输出**: 估值报告（DCF、PE、PB等）
- **工具**: FinancialTool, FormulaTool
- **预计**: 2小时

#### 4.3 综合评分AI (Composite Score AI)
- **文件**: `target/composite_score_ai.py`
- **职责**: 综合多维度评分
- **输入**: 所有分析结果
- **输出**: 综合评分、投资建议
- **工具**: FormulaTool, LLMTool
- **预计**: 2小时

---

### 🎯 批次5：策略执行军团（3个）

#### 5.1 仓位管理AI (Position Management AI)
- **文件**: `strategy/position_management_ai.py`
- **职责**: 计算最优仓位配置
- **输入**: 风险偏好、资金量、标的分析
- **输出**: 仓位分配方案
- **工具**: FormulaTool, LLMTool
- **预计**: 2小时

#### 5.2 止损止盈AI (Stop Loss Profit AI)
- **文件**: `strategy/stop_loss_profit_ai.py`
- **职责**: 设置止损止盈点位
- **输入**: 风险承受度、波动率
- **输出**: 止损止盈方案
- **工具**: FormulaTool
- **预计**: 2小时

#### 5.3 风险控制AI (Risk Control AI)
- **文件**: `strategy/risk_control_ai.py`
- **职责**: 管理投资风险
- **输入**: 仓位、市场数据、风险指标
- **输出**: 风险评估报告、风险控制建议
- **工具**: FinancialTool, FormulaTool
- **预计**: 2小时

---

### 🎯 批次6：结果验证军团（3个）

#### 6.1 回测分析AI (Backtest Analysis AI)
- **文件**: `validation/backtest_analysis_ai.py`
- **职责**: 回测投资策略
- **输入**: 历史数据、策略
- **输出**: 回测报告、策略表现
- **工具**: FinancialTool, FormulaTool
- **预计**: 2小时

#### 6.2 实盘跟踪AI (Live Tracking AI)
- **文件**: `validation/live_tracking_ai.py`
- **职责**: 跟踪实盘表现
- **输入**: 实时数据、持仓信息
- **输出**: 持仓报告、收益分析
- **工具**: FinancialTool
- **预计**: 2小时

#### 6.3 策略优化AI (Strategy Optimization AI)
- **文件**: `validation/strategy_optimization_ai.py`
- **职责**: 优化投资策略
- **输入**: 回测结果、实盘表现
- **输出**: 优化建议、调整方案
- **工具**: LLMTool, FormulaTool
- **预计**: 2小时

---

## 📅 执行计划

### Week 1: 热点捕捉军团（3个）
- Day 1-2: 市场情绪AI
- Day 3-4: 资金流向AI
- Day 5-6: 龙虎榜AI

### Week 2: 产业分析 + 个股挖掘（4个）
- Day 1-2: 竞争格局AI
- Day 3-4: 政策影响AI
- Day 5-6: 技术分析AI
- Day 7: 财务健康AI

### Week 3: 目标预测军团（3个）
- Day 1-2: 盈利预测AI
- Day 3-4: 估值模型AI
- Day 5-6: 综合评分AI

### Week 4: 策略执行军团（3个）
- Day 1-2: 仓位管理AI
- Day 3-4: 止损止盈AI
- Day 5-6: 风险控制AI

### Week 5: 结果验证军团（3个）
- Day 1-2: 回测分析AI
- Day 3-4: 实盘跟踪AI
- Day 5-6: 策略优化AI

---

## 🎯 开发原则

### 1. 复用工具库
- ✅ 优先使用现有工具（NewsTool, FinancialTool, LLMTool等）
- ✅ 避免重复造轮子
- ✅ 保持代码简洁（200-300行/Agent）

### 2. 标准化结构
```python
class NewAI(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AI名称",
            role="职责",
            capabilities=[...],
            tools=[...]
        )

    async def execute(self, task: str, **kwargs):
        # 统一入口
        if task == "analyze":
            return await self.analyze(...)

    async def analyze(self, ...):
        # 核心分析逻辑
        # 1. 获取数据（使用工具）
        # 2. 分析处理
        # 3. 生成报告
        return report
```

### 3. 测试驱动
- ✅ 每个Agent创建后立即编写测试
- ✅ 测试文件：`tests/test_xxx_ai.py`
- ✅ 验证核心功能

### 4. 文档同步
- ✅ 更新 `00-快速开始.md`
- ✅ 更新 `README.md`
- ✅ 更新 `ARCHITECTURE.md`

---

## 📊 进度追踪

| 批次 | 军团 | 数量 | 状态 | 完成日期 |
|------|------|------|------|---------|
| - | 已完成 | 6 | ✅ | - |
| 批次1 | 热点捕捉 | 3 | ⏳ 待开始 | - |
| 批次2 | 产业分析 | 2 | ⏳ 待开始 | - |
| 批次3 | 个股挖掘 | 2 | ⏳ 待开始 | - |
| 批次4 | 目标预测 | 3 | ⏳ 待开始 | - |
| 批次5 | 策略执行 | 3 | ⏳ 待开始 | - |
| 批次6 | 结果验证 | 3 | ⏳ 待开始 | - |
| **总计** | **24** | **24** | **25%** | **预计5周** |

---

## 🚀 开始执行

**下一步**: 创建批次1 - 热点捕捉军团的市场情绪AI

**执行命令**:
```bash
# 创建Agent文件
touch src/agents/business/hot_spot/market_sentiment_ai.py

# 创建测试文件
touch tests/test_market_sentiment_ai.py

# 运行测试
python tests/test_market_sentiment_ai.py
```

---

**计划创建完成！准备开始执行 Phase 3.2！**

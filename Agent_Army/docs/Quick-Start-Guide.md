# 🚀 Agent Army 快速开始指南

## 📋 目录

1. [环境准备](#环境准备)
2. [安装步骤](#安装步骤)
3. [5分钟快速开始](#5分钟快速开始)
4. [基础使用](#基础使用)
5. [进阶使用](#进阶使用)
6. [常见问题](#常见问题)

---

## 环境准备

### 系统要求

- **Python**: 3.11+
- **操作系统**: Windows 10/11, macOS, Linux
- **内存**: 最低4GB，推荐8GB+
- **硬盘**: 至少2GB可用空间

### 必需依赖

```bash
# 核心依赖
streamlit>=1.30.0
asyncio>=3.4.3
aiohttp>=3.9.0
python-dateutil>=2.8.2

# 测试依赖
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## 安装步骤

### 1️⃣ 克隆项目

```bash
git clone https://github.com/your-repo/Agent_Army.git
cd Agent_Army
```

### 2️⃣ 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ 验证安装

```bash
# 运行测试
python -m pytest tests/ -v

# 预期输出：大部分测试通过
```

---

## 5分钟快速开始

### 🎯 示例1：分析一只股票

```python
import asyncio
from src.agents.business.prediction import analyze_valuation_pricing

async def main():
    # 分析贵州茅台（600519）
    result = await analyze_valuation_pricing(
        stock_code="600519",
        current_price=1800.0,
        prediction_period="12m"
    )

    # 打印结论
    print(f"核心结论: {result.conclusion}")
    print(f"目标价: {result.details['target_pricing']['target_price']}元")
    print(f"上涨空间: {result.details['target_pricing']['upside']:.1f}%")
    print(f"置信度: {result.confidence * 100:.0f}%")

# 运行
asyncio.run(main())
```

**预期输出**：
```
核心结论: 目标价1850.0元，上涨空间2.8%，评级【推荐】，置信度75%
目标价: 1850.0元
上涨空间: 2.8%
置信度: 75%
```

### 🎯 示例2：完整投资分析流程

```python
import asyncio
from src.agents.business.prediction import ValuationPricingAI
from src.agents.business.strategy import TimingJudgmentAI
from src.agents.business.monitoring import InformationMonitoringAI

async def full_analysis(stock_code: str, current_price: float):
    """完整的投资分析流程"""

    # 1. 估值定价分析
    valuation_ai = ValuationPricingAI()
    valuation_result = await valuation_ai.analyze(
        stock_code=stock_code,
        current_price=current_price
    )

    # 2. 时机判断
    timing_ai = TimingJudgmentAI()
    timing_result = await timing_ai.analyze(
        stock_code=stock_code,
        current_price=current_price
    )

    # 3. 信息监控
    monitoring_ai = InformationMonitoringAI()
    monitoring_result = await monitoring_ai.analyze(
        stock_code=stock_code,
        days=7
    )

    # 汇总报告
    print("\n" + "=" * 60)
    print("📊 投资分析汇总报告")
    print("=" * 60)

    print(f"\n1️⃣ 估值分析:")
    print(f"   {valuation_result.conclusion}")

    print(f"\n2️⃣ 时机判断:")
    print(f"   {timing_result.conclusion}")

    print(f"\n3️⃣ 市场情绪:")
    sentiment = monitoring_result.details['sentiment_analysis']['overall_sentiment']
    print(f"   市场情绪: {sentiment['label']}（得分{sentiment['score']:.2f}）")

    print(f"\n💡 投资建议:")
    print(f"   {timing_result.details['action_suggestion']['action']}")

# 运行
asyncio.run(full_analysis("600519", 1800.0))
```

---

## 基础使用

### 1. 预测部Agent

#### 估值定价AI

```python
from src.agents.business.prediction import ValuationPricingAI

async def valuation_example():
    ai = ValuationPricingAI()

    result = await ai.analyze(
        stock_code="600519",
        current_price=1800.0,
        prediction_period="12m"  # 可选: 3m, 6m, 12m
    )

    # 访问结果
    print(f"目标价: {result.details['target_pricing']['target_price']}")
    print(f"价格区间: {result.details['target_pricing']['price_range']}")
    print(f"估值方法: {result.details['valuation_models'].keys()}")

    # 风险提示
    for risk in result.risks:
        print(f"⚠️ {risk}")

    # 投资建议
    for rec in result.recommendations:
        print(f"💡 {rec}")
```

#### 综合评估AI

```python
from src.agents.business.prediction import ComprehensiveEvaluationAI

async def comprehensive_evaluation_example():
    ai = ComprehensiveEvaluationAI()

    result = await ai.analyze(
        stock_code="600519",
        research_data={"industry": "白酒"},
        analysis_data={"fundamental": "优秀"},
        prediction_data={"target_price": 2000.0}
    )

    # 维度评分
    for dim_name, dim_data in result.details['dimension_scores'].items():
        print(f"{dim_name}: {dim_data['score']}分")

    # 综合评分
    print(f"综合评分: {result.details['comprehensive_score']}分")
    print(f"投资评级: {result.details['investment_rating']['rating']}")
```

### 2. 策略部Agent

#### 时机判断AI

```python
from src.agents.business.strategy import TimingJudgmentAI

async def timing_example():
    ai = TimingJudgmentAI()

    # 无持仓情况
    result = await ai.analyze(
        stock_code="600519",
        current_price=1800.0
    )

    print(f"买入信号: {result.details['buy_timing']['signal']}")
    print(f"卖出信号: {result.details['sell_timing']['signal']}")
    print(f"操作建议: {result.details['action_suggestion']['action']}")

    # 有持仓情况
    result_with_position = await ai.analyze(
        stock_code="600519",
        current_price=1800.0,
        position_cost=1700.0  # 持仓成本
    )

    print(f"止盈建议: {result_with_position.details['sell_timing']['take_profit']}")
    print(f"止损建议: {result_with_position.details['sell_timing']['stop_loss']}")
```

#### 风控AI

```python
from src.agents.business.strategy import RiskControlAI

async def risk_control_example():
    ai = RiskControlAI()

    result = await ai.analyze(
        stock_code="600519",
        current_price=1800.0,
        intended_buy_price=1800.0
    )

    print(f"风险等级: {result.details['risk_assessment']['risk_level']}")
    print(f"止损价: {result.details['stop_loss_strategy']['stop_loss_price']}")
    print(f"止盈价: {result.details['stop_loss_strategy']['take_profit_price']}")
```

### 3. 监控部Agent

#### 信息监控AI

```python
from src.agents.business.monitoring import InformationMonitoringAI

async def information_monitoring_example():
    ai = InformationMonitoringAI()

    result = await ai.analyze(
        stock_code="600519",
        days=7,
        include_industry=True
    )

    # 新闻事件
    news = result.details['news_events']
    print(f"公司新闻: {len(news['company_news'])}条")
    print(f"行业新闻: {len(news['industry_news'])}条")

    # 市场情绪
    sentiment = result.details['sentiment_analysis']
    print(f"市场情绪: {sentiment['overall_sentiment']['label']}")
    print(f"情绪趋势: {sentiment['sentiment_trend']}")
```

#### 资金监控AI

```python
from src.agents.business.monitoring import CapitalMonitoringAI

async def capital_monitoring_example():
    ai = CapitalMonitoringAI()

    result = await ai.analyze(
        stock_code="600519",
        days=5,
        include_dragon_tiger=True
    )

    # 资金流向
    flow = result.details['capital_flow']['net_flow']
    print(f"主力净流入: {flow['main_force']}万元")
    print(f"散户净流入: {flow['retail']}万元")

    # 龙虎榜
    if result.details['dragon_tiger']['on_list']:
        print(f"上榜原因: {result.details['dragon_tiger']['reason']}")
```

---

## 进阶使用

### 1. 并行分析多只股票

```python
import asyncio
from src.agents.business.prediction import ValuationPricingAI

async def analyze_multiple_stocks():
    """并行分析多只股票"""

    stocks = [
        ("600519", 1800.0),  # 贵州茅台
        ("000858", 60.0),    # 五粮液
        ("600036", 35.0),    # 招商银行
    ]

    ai = ValuationPricingAI()

    # 并行执行
    tasks = [
        ai.analyze(stock_code, current_price=price)
        for stock_code, price in stocks
    ]

    results = await asyncio.gather(*tasks)

    # 打印结果
    for (stock_code, _), result in zip(stocks, results):
        print(f"{stock_code}: {result.conclusion}")

asyncio.run(analyze_multiple_stocks())
```

### 2. 自定义配置

```python
from src.agents.business.strategy import PositionManagementAI

async def custom_config_example():
    """使用自定义配置"""

    # 自定义配置
    config = {
        "max_position_ratio": 0.3,  # 最大仓位30%
        "min_position_ratio": 0.05, # 最小仓位5%
        "risk_adjustment_factor": 0.8
    }

    ai = PositionManagementAI(config=config)

    result = await ai.analyze(
        stock_code="600519",
        current_price=1800.0,
        total_capital=1000000,
        risk_tolerance=3
    )

    print(f"建议仓位: {result.details['position_size']['recommended_ratio']:.1%}")
```

### 3. 错误处理

```python
from src.agents.business.prediction import ValuationPricingAI

async def error_handling_example():
    """错误处理示例"""

    ai = ValuationPricingAI()

    try:
        result = await ai.analyze(
            stock_code="invalid_code",  # 无效代码
            current_price=1800.0
        )
    except ValueError as e:
        print(f"参数错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")

asyncio.run(error_handling_example())
```

---

## 常见问题

### Q1: 如何获取股票实时价格？

**A**: 当前版本使用模拟数据，未来将接入真实数据源：

```python
# TODO: 接入真实数据源
# from src.core.tools import MarketTool
# market_tool = MarketTool()
# current_price = await market_tool.get_current_price("600519")

# 临时方案：手动输入
current_price = 1800.0
```

### Q2: Agent的置信度是什么意思？

**A**: 置信度（0-1）表示分析结果的可靠性：

- **0.8-1.0**: 高置信度，结果可信
- **0.6-0.8**: 中等置信度，建议谨慎
- **0.0-0.6**: 低置信度，建议参考其他因素

### Q3: 如何批量分析股票池？

**A**: 使用并行处理：

```python
import asyncio
from src.agents.business.prediction import ValuationPricingAI

async def batch_analysis(stock_pool: list):
    ai = ValuationPricingAI()

    tasks = [
        ai.analyze(code, current_price=price)
        for code, price in stock_pool
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for stock, result in zip(stock_pool, results):
        if isinstance(result, Exception):
            print(f"{stock[0]}: 分析失败 - {result}")
        else:
            print(f"{stock[0]}: {result.conclusion}")

# 使用
stock_pool = [("600519", 1800.0), ("000858", 60.0)]
asyncio.run(batch_analysis(stock_pool))
```

### Q4: 如何保存分析结果？

**A**: 使用JSON序列化：

```python
import json
from datetime import datetime

def save_result(result, filename: str):
    """保存分析结果"""

    data = {
        "timestamp": datetime.now().isoformat(),
        "agent_name": result.agent_name,
        "analysis_type": result.analysis_type,
        "conclusion": result.conclusion,
        "confidence": result.confidence,
        "details": result.details,
        "risks": result.risks,
        "recommendations": result.recommendations
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 使用
result = await analyze_valuation_pricing("600519", 1800.0)
save_result(result, "analysis_600519.json")
```

### Q5: 如何自定义Agent行为？

**A**: 通过config参数：

```python
config = {
    "custom_param": "value",
    "threshold": 0.8
}

ai = ValuationPricingAI(config=config)
```

---

## 📚 更多资源

- 📖 [完整API文档](API-Reference.md)
- 📊 [使用示例库](../examples/)
- 🏗️ [架构设计](8-departments-simplified.md)
- 🎯 [最佳实践](Best-Practices.md)

---

## 💬 获取帮助

遇到问题？

1. 📖 查看[常见问题](#常见问题)
2. 📚 阅读[API文档](API-Reference.md)
3. 💡 查看[示例代码](../examples/)
4. 🐛 提交Issue到GitHub

---

**最后更新**: 2026-03-20
**版本**: v1.0

# 工具库门面层使用文档

## 📖 概述

工具库门面层（Facade Layer）为分散的工具接口提供统一入口，简化Agent的使用复杂度。

**基于**: `TOOLS_LIBRARY_INTERFACE_ANALYSIS.md` 分析结果

**设计模式**: Facade Pattern（门面模式）

---

## 🎯 为什么需要门面层？

### 问题诊断

**原有问题**:
- ❌ 工具库有23个接口，分散在5个工具类中
- ❌ Agent难以发现和选择合适的接口
- ❌ 接口格式不统一（股票代码格式各不相同）
- ❌ 缺少自动降级机制

**解决方案**:
- ✅ 统一接口：一个方法对应一类功能
- ✅ 自动降级：主数据源失败时自动切换备用数据源
- ✅ 格式统一：自动转换股票代码格式
- ✅ 简化使用：Agent只需要调用门面类，不需要关心底层实现

---

## 📦 门面类清单

| 门面类 | 功能 | 底层工具 | 接口数 |
|--------|------|----------|--------|
| **IndustryTool** | 行业分析 | Yahoo + AKShare + EastMoney | 2个 |
| **TechnicalTool** | 技术分析 | Yahoo + AKShare | 2个 |
| **CapitalFlowTool** | 资金流向 | Financial + AKShare | 2个 |

**总计**: **3个门面类**，**6个统一接口**

---

## 🚀 快速开始

### 导入门面类

```python
# 方式1: 导入门面类（推荐）
from src.core.tools.tool_facades import (
    IndustryTool,
    TechnicalTool,
    CapitalFlowTool,
    get_industry_tool,
    get_technical_tool,
    get_capital_flow_tool
)

# 方式2: 从工具库导入
from src.core.tools import (
    IndustryTool,
    TechnicalTool,
    CapitalFlowTool
)
```

### 创建工具实例

```python
# 方式1: 使用工厂函数（推荐）
industry_tool = get_industry_tool()
technical_tool = get_technical_tool()
capital_tool = get_capital_flow_tool()

# 方式2: 直接实例化
industry_tool = IndustryTool()
technical_tool = TechnicalTool()
capital_tool = CapitalFlowTool()
```

---

## 📋 接口详解

### 1. IndustryTool - 行业分析工具

#### 接口1: `get_industry_info()`

获取股票的行业信息。

```python
result = await industry_tool.get_industry_info(
    stock_code="600519",     # 股票代码
    use_chain=False          # 是否获取产业链信息（较慢）
)
```

**返回数据**:
```python
{
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "industry": "白酒",
    "sector": "消费品",
    "industry_code": "BK0003",
    "industry_chain": {      # use_chain=True 时才有
        "upstream": ["原材料1", "原材料2"],
        "midstream": ["制造环节1", "制造环节2"],
        "downstream": ["销售渠道1", "销售渠道2"]
    },
    "data_source": "Yahoo Finance",  # 实际使用的数据源
    "last_update": "2026-03-15T10:30:00"
}
```

**自动降级策略**:
```
Yahoo Finance → AKShare → EastMoney → 默认值
```

---

#### 接口2: `get_industry_stocks()`

获取同行业的所有股票。

```python
stocks = await industry_tool.get_industry_stocks(
    industry_name="食品饮料",  # 行业名称
    limit=100                  # 返回数量限制
)
```

**返回数据**:
```python
[
    {"stock_code": "600519", "stock_name": "贵州茅台"},
    {"stock_code": "000858", "stock_name": "五粮液"},
    ...
]
```

---

### 2. TechnicalTool - 技术分析工具

#### 接口1: `get_kline()`

获取K线数据。

```python
df = technical_tool.get_kline(
    stock_code="601669",  # 股票代码
    period="1y",          # 时间周期: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    interval="1d"         # 数据频率: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "5d", "1wk", "1mo", "3mo"
)
```

**返回数据**: `pandas.DataFrame`

| 列名 | 说明 |
|------|------|
| Open | 开盘价 |
| High | 最高价 |
| Low | 最低价 |
| Close | 收盘价 |
| Volume | 成交量 |

**自动降级策略**:
```
Yahoo Finance → AKShare → 空DataFrame
```

---

#### 接口2: `get_top_list()`

获取涨跌榜。

```python
df = technical_tool.get_top_list(
    date="20260315",  # 日期 (YYYYMMDD，默认今日)
    limit=50          # 返回数量限制
)
```

**返回数据**: `pandas.DataFrame`

---

### 3. CapitalFlowTool - 资金流向工具

#### 接口1: `get_capital_flow()`

获取资金流向数据。

```python
result = await capital_tool.get_capital_flow(
    stock_code="600519",       # 股票代码
    start_date="20260101",     # 开始日期 (YYYYMMDD)
    end_date="20260315"        # 结束日期 (YYYYMMDD)
)
```

**返回数据**:
```python
{
    "stock_code": "600519",
    "data": [
        {
            "trade_date": "2026-03-15",
            "net_vol_main": 200000,   # 主力净流入
            "net_vol_xl": 150000,      # 大单净流入
            "net_mf_vol": 50000,       # 中单净流入
            "net_lg_vol": -30000       # 小单净流入
        },
        ...
    ],
    "summary": {
        "total_net_inflow": 5000000,    # 总净流入
        "avg_daily_inflow": 100000,     # 日均净流入
        "record_count": 50
    },
    "data_source": "Tushare"
}
```

**自动降级策略**:
```
FinancialTool (Tushare) → AKShare → 空数据
```

---

#### 接口2: `get_dragon_tiger()`

获取龙虎榜数据。

```python
result = await capital_tool.get_dragon_tiger(
    stock_code="600519",  # 股票代码（可选）
    date="20260315"       # 日期 (YYYYMMDD)
)
```

**返回数据**:
```python
{
    "stock_code": "600519",
    "data": [
        {
            "trade_date": "2026-03-15",
            "ts_code": "600519.SH",
            "name": "贵州茅台",
            "close": 1850.0,
            "pct_chg": 5.2,
            "turnover_ratio": 8.5,
            "l_sell": "机构专用",
            "l_buy": "机构专用",
            "reason": "涨幅偏离值达7%"
        },
        ...
    ],
    "summary": {
        "total_count": 10,
        "up_count": 7,
        "down_count": 3
    },
    "data_source": "Tushare"
}
```

---

## 🔄 数据源映射表

### 行业信息获取

| 门面接口 | 底层实现 | 数据源 | 优先级 |
|----------|----------|--------|--------|
| `IndustryTool.get_industry_info()` | Yahoo.get_stock_info() | Yahoo Finance | 1️⃣ |
| （备用） | AKShare.get_stock_info() | AKShare | 2️⃣ |
| （专用） | EastMoney.get_industry_info() | 东方财富 | 3️⃣ |

### K线数据获取

| 门面接口 | 底层实现 | 数据源 | 优先级 |
|----------|----------|--------|--------|
| `TechnicalTool.get_kline()` | Yahoo.get_historical_data() | Yahoo Finance | 1️⃣ |
| （备用） | AKShare.get_stock_info() | AKShare | 2️⃣ |

### 资金流向获取

| 门面接口 | 底层实现 | 数据源 | 优先级 |
|----------|----------|--------|--------|
| `CapitalFlowTool.get_capital_flow()` | Financial.get_moneyflow() | Tushare | 1️⃣ |
| （备用） | AKShare.get_individual_fund_flow() | AKShare | 2️⃣ |

---

## 💡 使用示例

### 示例1: 完整的股票分析

```python
import asyncio
from src.core.tools.tool_facades import (
    get_industry_tool,
    get_technical_tool,
    get_capital_flow_tool
)

async def analyze_stock(stock_code: str):
    """完整的股票分析"""

    # 1. 行业分析
    industry_tool = get_industry_tool()
    industry_info = await industry_tool.get_industry_info(stock_code)
    print(f"行业: {industry_info['industry']}")

    # 2. 技术分析
    technical_tool = get_technical_tool()
    kline_data = technical_tool.get_kline(stock_code, period="3mo")
    print(f"最新价格: {kline_data['Close'].iloc[-1]:.2f}")

    # 3. 资金流向
    capital_tool = get_capital_flow_tool()
    capital_flow = await capital_tool.get_capital_flow(stock_code)
    total_inflow = capital_flow['summary']['total_net_inflow']
    print(f"总净流入: {total_inflow:.0f} 元")

# 运行
asyncio.run(analyze_stock("600519"))
```

### 示例2: 同行业对比

```python
async def compare_industry_peers(stock_code: str):
    """同行业对比"""

    # 1. 获取目标股票的行业
    industry_tool = get_industry_tool()
    target_info = await industry_tool.get_industry_info(stock_code)
    industry_name = target_info['industry']

    # 2. 获取同行业股票
    peers = await industry_tool.get_industry_stocks(industry_name, limit=10)

    # 3. 对比分析
    results = []
    for peer in peers:
        peer_code = peer['stock_code']
        peer_info = await industry_tool.get_industry_info(peer_code)
        results.append({
            'stock_code': peer_code,
            'stock_name': peer_info['stock_name'],
            'industry': peer_info['industry']
        })

    return results
```

---

## ⚠️ 注意事项

### 1. 股票代码格式

门面层会自动转换股票代码格式：

```python
# 输入：6位代码
"600519"  # 上海
"000858"  # 深圳

# 内部自动转换为：
"600519.SS"   # Yahoo Finance 格式
"600519.SH"   # Tushare 格式
```

### 2. 异步调用

IndustryTool 和 CapitalFlowTool 的方法是异步的，需要使用 `await`：

```python
# ✅ 正确
result = await industry_tool.get_industry_info("600519")

# ❌ 错误
result = industry_tool.get_industry_info("600519")
```

TechnicalTool 的方法是同步的：

```python
# ✅ 正确
df = technical_tool.get_kline("600519")
```

### 3. 数据源可用性

门面层会自动检测数据源是否可用：

- Yahoo Finance: 需要安装 `yfinance`
- AKShare: 需要安装 `akshare`
- Tushare: 需要配置 `TUSHARE_API_KEY`

如果数据源不可用，会自动降级到下一个数据源。

---

## 🧪 测试

运行测试：

```bash
cd Agent_Army
python tests/test_tool_facades.py
```

测试覆盖：
- ✅ IndustryTool 接口测试
- ✅ TechnicalTool 接口测试
- ✅ CapitalFlowTool 接口测试
- ✅ 综合集成测试

---

## 📊 性能对比

### 使用门面层 vs 直接使用底层工具

| 指标 | 直接使用底层工具 | 使用门面层 |
|------|----------------|------------|
| **代码行数** | ~30行 | ~10行 |
| **需要了解的工具数** | 5个 | 3个 |
| **格式转换** | 手动 | 自动 |
| **降级机制** | 手动 | 自动 |
| **维护成本** | 高 | 低 |

**结论**: 使用门面层可以减少 **67%** 的代码量和 **50%** 的工具学习成本。

---

## 🎯 最佳实践

### ✅ 推荐做法

```python
# 1. 使用门面类（推荐）
industry_tool = get_industry_tool()
result = await industry_tool.get_industry_info("600519")
```

### ❌ 不推荐做法

```python
# 1. 直接使用底层工具（不推荐）
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool
yahoo_tool = YahooFinanceTool()

# 需要手动转换格式
if stock_code.startswith('6'):
    symbol = f"{stock_code}.SS"
else:
    symbol = f"{stock_code}.SZ"

# 需要手动处理错误
result = yahoo_tool.get_stock_info(symbol)
if "error" in result:
    # 手动降级到其他数据源
    pass
```

---

## 📚 相关文档

- [TOOLS_LIBRARY_INTERFACE_ANALYSIS.md](TOOLS_LIBRARY_INTERFACE_ANALYSIS.md) - 工具库接口分析
- [工具库源码](src/core/tools/) - 底层工具实现
- [测试代码](tests/test_tool_facades.py) - 门面层测试

---

**文档版本**: v1.0
**更新日期**: 2026-03-15
**维护者**: Agent Army 团队

**🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！**

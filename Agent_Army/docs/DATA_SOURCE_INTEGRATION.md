# 新数据源工具集成文档

## 概述

本次更新为Agent Army项目集成了三个新的数据源工具，大幅扩展了数据获取能力：

1. **YahooFinanceTool** - 国际标准股票数据
2. **AKShareTool** - 中国金融数据
3. **EastMoneyScraper** - 动态网页爬虫

---

## 一、Yahoo Finance工具

### 功能特性

- ✅ 实时行情数据
- ✅ 历史K线数据（支持多种周期）
- ✅ 财务报表（利润表、资产负债表、现金流量表）
- ✅ 股票基本信息（市值、行业、PE、PB等）
- ✅ 免费使用，无需注册

### 使用示例

```python
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool

# 初始化工具
tool = YahooFinanceTool()

# 获取股票信息
info = tool.get_stock_info("601669.SS")  # A股后缀：.SS上海，.SZ深圳
print(f"公司名称: {info['name']}")
print(f"市值: {info['market_cap']}")

# 获取实时行情
quote = tool.get_realtime_quote("601669.SS")
print(f"当前价格: {quote['current_price']}")
print(f"涨跌幅: {quote['change_percent']}%")

# 获取历史K线数据
hist = tool.get_historical_data("601669.SS", period="1y", interval="1d")
print(hist.head())

# 获取财务报表
financials = tool.get_financial_statements("601669.SS")
```

### A股代码格式

| 市场 | 代码格式 | 示例 |
|------|---------|------|
| 上海 | `XXXXXX.SS` | `601669.SS` (中国电建) |
| 深圳 | `XXXXXX.SZ` | `000001.SZ` (平安银行) |
| 美股 | `Symbol` | `AAPL`, `TSLA` |

### A股实测数据质量 (2026-03-15)

```python
# 测试股票：601669.SS (中国电建)
info = tool.get_stock_info("601669.SS")
# {
#     "name": "Power Construction Corporation of China, Ltd",
#     "market_cap": 123856093184,  # 1239亿
#     "industry": "Engineering & Construction",
#     "sector": "Industrials",
#     "previous_close": 6.54,
#     "52_week_change": 0.45%
# }

quote = tool.get_realtime_quote("601669.SS")
# {
#     "current_price": 7.19,
#     "change": 0.65,
#     "change_percent": 9.94,  # 实时数据
#     "volume": 1800476985
# }

financials = tool.get_financial_statements("601669.SS")
# {
#     "income_statement": {"shape": [51, 4]},  # 4年完整数据
#     "balance_sheet": {"shape": [80, 4]},
#     "cash_flow": {"shape": [50, 4]}
# }
```

---

## 二、AKShare工具

### 功能特性

- ✅ 个股资金流向数据（主力、超大单、大单、中单、小单）
- ✅ 实时行情数据
- ✅ 龙虎榜数据
- ✅ 融资融券数据
- ✅ 概念板块成分股
- ✅ 专注A股市场

### 使用示例

```python
from src.core.tools.data_source.akshare_tool import AKShareTool

# 初始化工具
tool = AKShareTool()

# 获取资金流向数据
df = tool.get_individual_fund_flow("601669", market="sh")
print(df.head())

# 获取实时行情
quote = tool.get_realtime_quote("601669")
print(f"股票名称: {quote['name']}")
print(f"当前价格: {quote['current_price']}")
print(f"涨跌幅: {quote['change_percent']}%")

# 获取龙虎榜数据
df = tool.get_top_list(date="20260315")
print(df.head())
```

### 数据字段说明

资金流向数据包含：
- 主力净流入
- 超大单净流入
- 大单净流入
- 中单净流入
- 小单净流入

---

## 三、EastMoney爬虫工具

### 功能特性

- ✅ 抓取东方财富数据中心
- ✅ 资金流向汇总数据（今日、5日、10日）
- ✅ 动态渲染页面支持
- ✅ 数据自动解析和清洗

### 使用示例

```python
import asyncio
from src.core.tools.data_source.eastmoney_scraper import EastMoneyScraper

# 初始化爬虫
scraper = EastMoneyScraper()

# 抓取资金流向数据（异步）
async def scrape():
    result = await scraper.scrape_capital_flow("601669")
    print(f"今日净流入: {result['net_inflow']} 亿元")
    print(f"主力净流入: {result['main_net']} 亿元")
    print(f"超大单净流入: {result['super_large_net']} 亿元")

asyncio.run(scrape())

# 同步方式包装函数
from src.core.tools.data_source.eastmoney_scraper import scrape_capital_flow_sync
result = scrape_capital_flow_sync("601669")
```

---

## 四、快速开始

### 安装依赖

运行安装脚本：

```bash
cd Agent_Army
install_data_source_tools.bat
```

或手动安装：

```bash
pip install yfinance
pip install akshare
pip install playwright
playwright install chromium
```

### 运行测试

```bash
python tests\test_data_source_tools.py
```

### 在Agent中使用

```python
from src.core.tools import YahooFinanceTool, AKShareTool

class MyAgent(BaseBusinessAgent):
    def __init__(self):
        super().__init__()

        # 初始化工具
        self.yahoo_tool = YahooFinanceTool()
        self.akshare_tool = AKShareTool()

    async def analyze(self, stock_code: str):
        # 使用Yahoo Finance获取基本信息
        info = self.yahoo_tool.get_stock_info(f"{stock_code}.SS")

        # 使用AKShare获取资金流向
        df = self.akshare_tool.get_individual_fund_flow(stock_code, "sh")

        # 分析逻辑...
        return result
```

---

## 五、数据源对比

| 特性 | Yahoo Finance | AKShare | EastMoney爬虫 |
|------|--------------|---------|--------------|
| 实时行情 | ✅ | ✅ | ✅ |
| 历史K线 | ✅ | ✅ | ❌ |
| 财务报表 | ✅ (4年完整) | ✅ | ❌ |
| 资金流向 | ❌ | ✅ | ✅ |
| 龙虎榜 | ❌ | ✅ | ✅ |
| 免费使用 | ✅ | ✅ | ✅ |
| A股支持 | ✅ 优秀 | ✅ 优秀 | ⚠️ 部分 |
| 美股支持 | ✅ | ❌ | ❌ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 速度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**测试验证** (2026-03-15, 601669.SS):
- ✅ Yahoo Finance: 基本信息、K线、实时行情、财务报表全部获取成功
- ✅ 财务报表: 利润表51行、资产负债表80行、现金流量表50列（4年完整数据）

**推荐使用策略**：
- **首选Yahoo Finance**：A股基本信息、实时行情、K线、财务报表（免费稳定、数据完整）
- **补充AKShare**：资金流向、龙虎榜等Yahoo Finance不支持的数据
- **EastMoney爬虫**：作为备用数据源，抓取特定网站数据

---

## 六、常见问题

### Q1: Yahoo Finance对A股支持如何？

A: **实测支持非常好**！（2026-03-15测试）：

测试股票：601669.SS (中国电建)
- ✅ 基本信息：公司全名、市值1239亿、行业板块
- ✅ 实时行情：价格7.19，涨跌+9.94%
- ✅ K线数据：5天完整OHLCV数据
- ✅ 财务报表：利润表51行、资产负债表80行、现金流量表50行

**结论**：Yahoo Finance对A股支持优秀，可作为A股主要数据源。

### Q2: A股代码格式是什么？

A: Yahoo Finance A股代码格式：

| 市场 | 代码格式 | 示例 |
|------|---------|------|
| 上海 | `XXXXXX.SS` | `601669.SS` (中国电建) |
| 深圳 | `XXXXXX.SZ` | `000001.SZ` (平安银行) |
| 美股 | `Symbol` | `AAPL`, `TSLA` |

### Q3: AKShare数据为空？

A: 可能原因：
- 市场休市时间
- 股票代码格式错误
- API限流

解决：
```python
# 检查工具可用性
tool = AKShareTool()
if tool.is_available():
    df = tool.get_individual_fund_flow("601669", "sh")
```

### Q4: Playwright安装失败？

A: 使用国内镜像：
```bash
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
playwright install chromium
```

---

## 七、后续计划

- [ ] 集成更多数据源（Tushare、Wind等）
- [ ] 添加数据缓存机制
- [ ] 实现数据源智能切换
- [ ] 添加更多技术指标计算

---

## 八、更新日志

**2026-03-15**
- ✅ 创建YahooFinanceTool
- ✅ 创建AKShareTool
- ✅ 创建EastMoneyScraper
- ✅ 添加工具测试
- ✅ 更新工具库导出
- ✅ 编写集成文档

---

**作者**: Agent Army Team
**版本**: v1.0
**最后更新**: 2026-03-15

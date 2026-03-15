# 雅虎财经 vs AKShare - A股数据接口对比

**对比时间**: 2026-03-12
**目的**: 选择最优的A股数据源

---

## 📊 核心API对比

| 功能 | 雅虎财经 | AKShare | 推荐度 |
|------|---------|---------|--------|
| **历史K线** | ✅ `get_historical_stock_prices` | ✅ `stock_zh_a_hist` | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **个股信息** | ✅ `get_stock_info` | ✅ `stock_individual_info_em` | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **实时行情** | ✅ 内置支持 | ⚠️ 不稳定 | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **财务报表** | ✅ `get_financial_statement` | ⚠️ 需付费/不稳定 | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **股东信息** | ✅ `get_major_holders` | ❌ 不支持 | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **分红拆股** | ✅ `get_dividends` | ⚠️ 部分支持 | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **分钟数据** | ✅ 1m-90m（60天） | ❌ 不支持 | 雅虎财经 ⭐⭐⭐⭐⭐ |
| **数据稳定性** | ✅ 全球API，成熟稳定 | ⚠️ 依赖国内网站 | 雅虎财经 ⭐⭐⭐⭐⭐ |

---

## 🏆 雅虎财经API的优势

### 1. 完整的A股数据覆盖

**支持的交易所**:
- ✅ 上海交易所 (.SS) - 600xxx, 601xxx, 603xxx, 605xxx, 688xxx(科创板)
- ✅ 深圳交易所 (.SZ) - 000xxx, 002xxx, 003xxx, 300xxx(创业板), 301xxx

**代码示例**:
```python
# 上海交易所
"600519.SS"  # 贵州茅台
"688981.SS"  # 中芯国际（科创板）

# 深圳交易所
"000001.SZ"  # 平安银行
"300750.SZ"  # 宁德时代（创业板）
```

---

### 2. 丰富的API接口

#### 股票基本信息（`get_stock_info`）

**数据字段**（100+个）:
- 股价信息: 当前价、开盘价、最高价、最低价、成交量
- 公司信息: 名称、行业、板块、网站、员工数
- 财务指标: 市值、市盈率、市净率、PEG比率
- 盈利数据: 总收入、净利润、EPS、收入增长
- 利润率: ROE、ROA、利润率
- 风险指标: Beta系数、52周高低

**示例**:
```python
from mshtools import get_data_source

result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_stock_info",
    params={
        "ticker": "600519.SS",      # 贵州茅台
        "file_path": "/path/to/output.csv"
    }
)
```

---

#### 历史K线数据（`get_historical_stock_prices`）

**参数灵活性**:
- `period`: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
- `interval`: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

**数据字段**:
- Date, Open, High, Low, Close, Adj Close, Volume

**示例**:
```python
# 获取5分钟数据（最近5天）
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_historical_stock_prices",
    params={
        "ticker": "600519.SS",
        "period": "5d",          # 最近5天
        "interval": "5m",        # 5分钟间隔
        "file_path": "/path/to/output.csv"
    }
)

# 获取10年日线数据
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_historical_stock_prices",
    params={
        "ticker": "600519.SS",
        "period": "10y",         # 10年
        "interval": "1d",        # 日线
        "file_path": "/path/to/output.csv"
    }
)
```

---

#### 财务报表（`get_financial_statement`）

**支持三种报表**:
- 利润表（income）
- 资产负债表（balance_sheet）
- 现金流量表（cash_flow）

**时间范围**:
- 年度数据: 过去4年
- 季度数据: 最近4个季度

**示例**:
```python
# 获取年度利润表
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_financial_statement",
    params={
        "ticker": "600519.SS",
        "statement_type": "income",
        "period_type": "annual",
        "file_path": "/path/to/output.csv"
    }
)
```

---

#### 股东信息（`get_major_holders`）

**数据内容**:
- 主要机构股东
- 持股比例
- 持股变化

**示例**:
```python
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_major_holders",
    params={
        "ticker": "600519.SS",
        "file_path": "/path/to/output.csv"
    }
)
```

---

#### 分红拆股（`get_dividends`）

**数据内容**:
- 分红历史
- 拆股记录
- 除权除息日期

**示例**:
```python
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_dividends",
    params={
        "ticker": "600519.SS",
        "file_path": "/path/to/output.csv"
    }
)
```

---

## 🔥 关键优势：全球API，无限制！

### 1. 无IP限制

**雅虎财经**:
- ✅ 全球可用
- ✅ 国内服务器可用
- ✅ 海外服务器可用
- ✅ 无需代理

**AKShare**:
- ⚠️ 依赖国内网站（东方财富、新浪等）
- ⚠️ 海外IP可能被限制
- ⚠️ 实时行情接口不稳定

---

### 2. 数据稳定性

**雅虎财经**:
- ✅ 成熟的全球API
- ✅ 数据质量高
- ✅ 更新及时
- ✅ 长期维护保证

**AKShare**:
- ⚠️ 依赖第三方网站
- ⚠️ 网站改版可能导致失效
- ⚠️ 反爬机制频繁

---

### 3. 分钟级数据支持

**雅虎财经**:
- ✅ 1分钟、2分钟、5分钟、15分钟、30分钟、60分钟、90分钟
- ✅ 1小时数据
- ✅ 最近60天分钟数据

**AKShare**:
- ❌ 不支持分钟数据
- ❌ 只有日线、周线、月线

---

### 4. 财务数据完整

**雅虎财经**:
- ✅ 完整财务三表
- ✅ 4年年度数据
- ✅ 4季度数据
- ✅ 免费获取

**AKShare**:
- ⚠️ 财务数据接口不稳定
- ⚠️ 部分需要付费
- ⚠️ 字段不完整

---

## 💡 最终推荐

### ⭐⭐⭐⭐⭐ 推荐方案：雅虎财经为主

**原因**:
1. ✅ 数据稳定性最高
2. ✅ API接口最完整
3. ✅ 无IP限制（全球可用）
4. ✅ 支持分钟数据
5. ✅ 财务数据完整
6. ✅ 长期维护保证

---

### 使用场景

#### 场景1: 基础数据需求

**推荐**: 雅虎财经 ⭐⭐⭐⭐⭐

```python
# 历史K线 + 个股信息
get_historical_stock_prices()  # K线数据
get_stock_info()               # 个股信息
```

---

#### 场景2: 高频交易/日内分析

**推荐**: 雅虎财经 ⭐⭐⭐⭐⭐（唯一选择）

```python
# 5分钟数据
get_historical_stock_prices(
    interval="5m",    # 5分钟
    period="5d"      # 最近5天
)
```

**AKShare无法实现！**

---

#### 场景3: 财务分析

**推荐**: 雅虎财经 ⭐⭐⭐⭐⭐

```python
# 财务三表
get_financial_statement(statement_type="income")          # 利润表
get_financial_statement(statement_type="balance_sheet")  # 资产负债表
get_financial_statement(statement_type="cash_flow")      # 现金流量表
```

**AKShare财务数据不稳定！**

---

#### 场景4: 资金流数据

**推荐**: Playwright爬虫 ⭐⭐⭐

```python
# 雅虎财经和AKShare都没有资金流数据
# 需要使用Playwright爬虫从东方财富获取
capital_flow_scraper_v2.py
```

---

## 🏗️ 最终架构方案

```
┌─────────────────────────────────────────────────────────┐
│              A股数据获取架构（雅虎财经版）               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │  Yahoo Finance│   │ Playwright   │    │  DuckDB    ││
│  │  (主数据源)   │ +  │  (资金流补充) │ →  │  (数据库)   ││
│  │   ⭐⭐⭐⭐⭐    │    │   ⭐⭐⭐      │    │            ││
│  └──────────────┘    └──────────────┘    └────────────┘│
│         ↓                    ↓                    ↓        │
│  ┌─────────────────────────────────────────────────────┐│
│  │  数据分层                                           ││
│  ├─────────────────────────────────────────────────────┤│
│  │  K线数据 (1m-1d)     → Yahoo Finance ✅            ││
│  │  个股信息 (100+字段)  → Yahoo Finance ✅            ││
│  │  财务报表 (三表)       → Yahoo Finance ✅            ││
│  │  股东信息             → Yahoo Finance ✅            ││
│  │  分红拆股             → Yahoo Finance ✅            ││
│  │  资金流向             → Playwright爬虫 ✅            ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 快速开始

### 安装依赖

```bash
# 雅虎财经使用内置的mshtools，无需额外安装
pip install pandas matplotlib numpy  # 可选：数据处理和可视化
```

### 基础使用

```python
from mshtools import get_data_source

# 1. 获取历史K线
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_historical_stock_prices",
    params={
        "ticker": "600519.SS",
        "period": "1y",
        "interval": "1d",
        "file_path": "/path/to/output.csv"
    }
)

# 2. 获取个股信息
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_stock_info",
    params={
        "ticker": "600519.SS",
        "file_path": "/path/to/output.csv"
    }
)

# 3. 获取财务报表
result = get_data_source(
    data_source_name="yahoo_finance",
    api_name="get_financial_statement",
    params={
        "ticker": "600519.SS",
        "statement_type": "income",
        "period_type": "annual",
        "file_path": "/path/to/output.csv"
    }
)
```

---

## 🎯 总结

**雅虎财经API是A股数据的最优选择！**

**核心优势**:
1. 🌍 全球API，无IP限制
2. 📊 数据完整，字段丰富
3. ⚡ 稳定可靠，长期维护
4. 🔥 支持分钟级数据
5. 💰 完全免费
6. 📈 财务数据完整

**推荐部署**:
- ✅ 新加坡服务器（DigitalOcean）
- ✅ 雅虎财经API（主数据源）
- ✅ Playwright（资金流补充）
- ✅ DuckDB（数据存储）

---

**文档来源**: [雅虎财经A股数据获取使用大全.md](雅虎财经A股数据获取使用大全.md)
**分析人**: AI Agent
**版本**: v1.0
**日期**: 2026-03-12

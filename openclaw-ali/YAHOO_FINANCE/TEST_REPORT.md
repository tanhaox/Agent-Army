# Yahoo Finance本地测试报告

**测试时间**: 2026-03-13
**测试工具**: yfinance库
**测试股票**: 贵州茅台（600519.SS）

---

## ✅ 测试结果总结

### 测试1：历史K线数据

| 项目 | 结果 |
|------|------|
| 数据获取 | ✅ 成功 |
| 数据行数 | 5天 |
| 字段数量 | 7个 |
| 字段完整性 | ✅ 无缺失值 |

**字段列表**：
1. Open（开盘）
2. High（最高）
3. Low（最低）
4. Close（收盘）
5. Volume（成交量）
6. Dividends（分红）
7. Stock Splits（拆股）

**数据样例**：
```
日期              开盘      最高      收盘      成交量
2026-03-06      1395.00   1407.50   -       -
2026-03-09      1390.00   1404.90   -       -
2026-03-10      1404.90   1409.49   -       -
2026-03-11      1402.99   1405.99   -       -
2026-03-12      1395.00   1403.95   -       -
```

---

### 测试2：个股信息

| 项目 | 结果 |
|------|------|
| 信息获取 | ✅ 成功 |
| 字段数量 | 158个 |
| 信息类型 | 公司信息、财务指标、风险指标等 |

**示例字段**（前20个）：
```
1. address1 = Maotai Town
2. city = Renhuai
3. zip = 564501
4. country = China
5. phone = 86 85 1223 86002
6. website = https://www.moutaichina.com
7. industry = Beverages - Wineries & Distilleries
8. sector = Consumer Defensive
9. fullTimeEmployees = 34750
10. longBusinessSummary = Kweichow Moutai Co., Ltd....
```

---

## ❌ CSV到数据库集成问题

### 问题1：字段数量不匹配 🔴 **严重**

```
Yahoo Finance:    7个字段
AKShare数据库:   11个字段
差异:           4个字段
```

**缺失字段**：
- `code` - 股票代码
- `name` - 股票名称
- `amount` - 成交额
- `pct_change` - 涨跌幅
- `turnover_rate` - 换手率

---

### 问题2：字段名称映射 🟡 **重要**

需要将Yahoo Finance字段名映射为数据库字段名：

| Yahoo Finance | AKShare数据库 | 状态 |
|--------------|--------------|------|
| Open | open | ✅ |
| High | high | ✅ |
| Low | low | ✅ |
| Close | close | ✅ |
| Volume | volume | ✅ |
| Date (索引) | date | ⚠️ 需要转换 |
| - | code | ❌ 缺失 |
| - | name | ❌ 缺失 |
| - | amount | ❌ 缺失 |
| - | pct_change | ❌ 缺失 |
| - | turnover_rate | ❌ 缺失 |

---

### 问题3：数据类型转换 🟡 **重要**

**Datetime索引转换**：
```python
# Yahoo Finance的CSV
# 索引: DatetimeIndex
# 示例: 2026-03-06 00:00:00+08:00

# 需要转换为:
# date字段: '2026-03-06' (字符串或DATE类型)

# 转换代码:
df.index = pd.to_datetime(df.index)
df['date'] = df.index.strftime('%Y-%m-%d')
```

---

### 问题4：缺失字段处理 🟡 **重要**

Yahoo Finance **没有以下字段**，需要特殊处理：

| 字段 | 处理方案 |
|------|---------|
| `code` | 从ticker参数手动添加 |
| `name` | 从info['shortName']获取，或手动维护映射表 |
| `amount` | 计算生成：`open * volume`（近似）或设为NULL |
| `pct_change` | 计算生成：`(close - prev_close) / prev_close * 100` |
| `turnover_rate` | 设为NULL（Yahoo Finance无此数据） |

---

### 问题5：CSV表顺序 vs 数据库表顺序 🟢 **次要**

```python
# Yahoo Finance CSV列顺序
['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']

# AKShare数据库列顺序
['code', 'name', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change', 'turnover_rate']

# 解决方案：使用字典映射，不依赖列顺序
data = {
    'code': '600519',
    'name': '贵州茅台',
    'date': '2026-03-12',
    'open': row['Open'],
    'high': row['High'],
    # ...
}
```

---

## 💡 解决方案

### 方案1：统一数据源表（推荐）⭐⭐⭐⭐⭐

**优点**：
- 兼容Yahoo Finance和AKShare
- 保留所有字段，无数据丢失
- 清晰标注数据来源
- 易于扩展更多数据源

**实现**：
```sql
CREATE TABLE stock_kline_unified (
    id INTEGER PRIMARY KEY,
    source VARCHAR NOT NULL,        -- 数据源：yahoo/akshare
    code VARCHAR NOT NULL,          -- 股票代码
    name VARCHAR,                   -- 股票名称
    date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,               -- Yahoo特有，AKShare为NULL
    volume BIGINT,
    amount DOUBLE,                  -- AKShare特有，Yahoo为NULL
    pct_change DOUBLE,              -- 计算生成或AKShare提供
    turnover_rate DOUBLE,           -- AKShare特有，Yahoo为NULL
    dividends DOUBLE,               -- Yahoo特有
    stock_splits DOUBLE,            -- Yahoo特有
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, code, date)
);

CREATE INDEX idx_source_code_date ON stock_kline_unified(source, code, date);
```

**数据插入**（Yahoo Finance）：
```python
import yfinance as yf
import duckdb

ticker = yf.Ticker('600519.SS')
df = ticker.history(period='5d')

con = duckdb.connect('stock_market.db')

for idx, row in df.iterrows():
    date_str = idx.strftime('%Y-%m-%d')

    # 计算涨跌幅
    pct_change = None
    if len(df) > 0 and idx != df.index[0]:
        prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
        pct_change = (row['Close'] - prev_close) / prev_close * 100

    con.execute('''
        INSERT OR REPLACE INTO stock_kline_unified
        (source, code, name, date, open, high, low, close, adj_close, volume,
         amount, pct_change, turnover_rate, dividends, stock_splits)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'yahoo',                    -- source
        '600519',                   -- code
        '贵州茅台',                  -- name
        date_str,                   -- date
        row['Open'],                -- open
        row['High'],                -- high
        row['Low'],                 -- low
        row['Close'],               -- close
        row.get('Adj Close'),       -- adj_close
        row['Volume'],              -- volume
        None,                       -- amount (Yahoo无此数据)
        pct_change,                 -- pct_change (计算生成)
        None,                       -- turnover_rate (Yahoo无此数据)
        row['Dividends'],           -- dividends
        row['Stock Splits']         -- stock_splits
    ))
```

**数据插入**（AKShare）：
```python
import akshare as ak
import duckdb

df = ak.stock_zh_a_hist(symbol='600519', period='daily', adjust='qfq')

con = duckdb.connect('stock_market.db')

for idx, row in df.iterrows():
    con.execute('''
        INSERT OR REPLACE INTO stock_kline_unified
        (source, code, name, date, open, high, low, close, adj_close, volume,
         amount, pct_change, turnover_rate, dividends, stock_splits)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'akshare',
        '600519',
        row['股票名称'],
        row['日期'],
        row['开盘'],
        row['最高'],
        row['最低'],
        row['收盘'],
        None,                       -- adj_close (AKShare无此数据)
        row['成交量'],
        row['成交额'],
        row['涨跌幅'],
        row['换手率'],
        None,                       -- dividends
        None                        -- stock_splits
    ))
```

**数据查询示例**：
```sql
-- 查询特定股票的最新数据
SELECT * FROM stock_kline_unified
WHERE code = '600519'
ORDER BY date DESC
LIMIT 10;

-- 对比不同数据源
SELECT
    date,
    MAX(CASE WHEN source='yahoo' THEN close END) as yahoo_close,
    MAX(CASE WHEN source='akshare' THEN close END) as akshare_close
FROM stock_kline_unified
WHERE code = '600519'
GROUP BY date
ORDER BY date DESC;

-- 获取完整数据（优先使用Yahoo，补充AKShare特有字段）
SELECT
    y.code,
    y.date,
    y.close as yahoo_close,
    a.close as akshare_close,
    y.adj_close,
    a.amount,           -- AKShare特有
    a.turnover_rate     -- AKShare特有
FROM stock_kline_unified y
LEFT JOIN stock_kline_unified a
    ON y.code = a.code
    AND y.date = a.date
    AND a.source = 'akshare'
WHERE y.source = 'yahoo'
ORDER BY y.date DESC;
```

---

### 方案2：保持原AKShare表，新建Yahoo表

```sql
-- AKShare数据（原表保持不变）
CREATE TABLE stock_kline_akshare (
    code VARCHAR,
    name VARCHAR,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    amount DOUBLE,
    pct_change DOUBLE,
    turnover_rate DOUBLE,
    PRIMARY KEY (code, date)
);

-- Yahoo Finance数据（新建）
CREATE TABLE stock_kline_yahoo (
    code VARCHAR,
    name VARCHAR,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    dividends DOUBLE,
    stock_splits DOUBLE,
    pct_change DOUBLE,          -- 计算生成
    PRIMARY KEY (code, date)
);

-- 创建视图统一查询
CREATE VIEW stock_kline_combined AS
SELECT
    COALESCE(a.code, y.code) as code,
    COALESCE(a.name, y.name) as name,
    COALESCE(a.date, y.date) as date,
    a.open,
    a.high,
    a.low,
    COALESCE(a.close, y.close) as close,
    y.adj_close,
    COALESCE(a.volume, y.volume) as volume,
    a.amount,
    a.pct_change,
    a.turnover_rate,
    y.dividends,
    y.stock_splits
FROM stock_kline_akshare a
FULL OUTER JOIN stock_kline_yahoo y
    ON a.code = y.code
    AND a.date = y.date;
```

---

### 方案3：扩展AKShare表（不推荐）

**缺点**：
- Yahoo特有字段（adj_close, dividends, stock_splits）在AKShare行中为NULL
- AKShare特有字段（amount, turnover_rate）在Yahoo行中为NULL
- 大量NULL值，浪费存储空间

---

## 📋 实现清单

### 阶段1：数据库准备（0.5小时）

- [ ] 创建`stock_kline_unified`表
- [ ] 创建索引
- [ ] 测试表结构

### 阶段2：Yahoo Finance集成（2小时）

- [ ] 安装yfinance
- [ ] 实现数据获取函数
- [ ] 实现数据插入函数
- [ ] 处理缺失字段（code, name, amount, pct_change, turnover_rate）
- [ ] 测试单只股票
- [ ] 测试批量股票

### 阶段3：AKShare集成（1小时）

- [ ] 迁移现有akshare_sync.py到新表
- [ ] 测试数据迁移
- [ ] 验证数据完整性

### 阶段4：测试和验证（1小时）

- [ ] 对比Yahoo和AKShare数据
- [ ] 验证数据一致性
- [ ] 测试查询性能
- [ ] 编写使用文档

---

## 🎯 最终建议

### 采用方案1：统一数据源表

**理由**：
1. ✅ **灵活性高** - 支持多数据源，易于扩展
2. ✅ **数据完整** - 保留所有字段，无数据丢失
3. ✅ **可追溯** - 清晰标注数据来源
4. ✅ **查询方便** - 一张表完成所有查询
5. ✅ **易于维护** - 统一的插入和查询逻辑

**下一步**：
1. 创建`stock_kline_unified`表
2. 编写Yahoo Finance数据同步脚本
3. 迁移AKShare数据到新表
4. 部署到新加坡服务器

---

**报告人**: AI Agent
**完成时间**: 2026-03-13
**测试环境**: Windows 11, Python 3.x, yfinance

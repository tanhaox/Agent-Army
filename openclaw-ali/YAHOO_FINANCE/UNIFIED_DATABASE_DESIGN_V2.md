# 股票数据统一存储架构设计（支持多数据源扩展）

**设计目标**：支持任意数量数据源的灵活接入和数据补全

**版本**: v2.0
**更新时间**: 2026-03-13

---

## 🏗️ 设计原则

### 1. **数据源无关性**
- 每个数据源独立存储，互不干扰
- 支持部分字段（某个数据源只提供部分字段）
- 新增数据源无需修改现有结构

### 2. **可扩展性**
- 新增字段通过ALTER TABLE添加
- 支持JSON存储非结构化数据
- 预留扩展字段

### 3. **数据可追溯**
- 记录数据来源
- 记录数据更新时间
- 记录数据质量指标

### 4. **查询便利性**
- 提供统一视图
- 优先级策略（哪个数据源优先）
- 自动合并多源数据

---

## 📊 核心表设计

### 表1：stock_kline_unified（统一K线表）⭐ **核心**

```sql
CREATE TABLE stock_kline_unified (
    -- 主键和基础字段
    id INTEGER PRIMARY KEY,

    -- 数据来源标识（关键！）
    source VARCHAR NOT NULL,              -- 数据源：yahoo/akshare/playwright/sina/eastmoney/...
    source_id VARCHAR,                    -- 数据源内部ID（可选）
    source_version VARCHAR,               -- 数据源版本（如API版本）

    -- 股票标识
    code VARCHAR NOT NULL,                -- 标准化代码（6位数字）
    name VARCHAR,                         -- 股票名称（可能为空）
    exchange VARCHAR,                     -- 交易所：SH/SZ
    market VARCHAR,                       -- 市场：主板/创业板/科创板

    -- 时间字段
    date DATE NOT NULL,                   -- 日期
    time TIME,                            -- 时间（分钟数据用）
    timestamp TIMESTAMP,                  -- 完整时间戳

    -- Yahoo Finance核心字段
    open DOUBLE,                          -- 开盘价
    high DOUBLE,                          -- 最高价
    low DOUBLE,                           -- 最低价
    close DOUBLE,                         -- 收盘价
    adj_close DOUBLE,                     -- 复权价
    volume BIGINT,                        -- 成交量（股）

    -- AKShare特有字段
    amount DOUBLE,                        -- 成交额（元）
    pct_change DOUBLE,                    -- 涨跌幅（%）
    turnover_rate DOUBLE,                 -- 换手率（%）

    -- 分红拆股（Yahoo提供）
    dividends DOUBLE,                     -- 分红
    stock_splits DOUBLE,                  -- 拆股

    -- 技术指标（可后续计算添加）
    ma5 DOUBLE,                           -- 5日均线
    ma10 DOUBLE,                          -- 10日均线
    ma20 DOUBLE,                          -- 20日均线
    ema12 DOUBLE,                         -- 12日指数均线
    ema26 DOUBLE,                         -- 26日指数均线

    -- 资金流向（Playwright爬虫提供）
    net_inflow DOUBLE,                    -- 净流入
    main_inflow DOUBLE,                   -- 主力流入
    super_large_inflow DOUBLE,            -- 超大单流入
    large_inflow DOUBLE,                  -- 大单流入
    medium_inflow DOUBLE,                 -- 中单流入
    small_inflow DOUBLE,                  -- 小单流入

    -- 数据质量指标
    data_quality VARCHAR DEFAULT 'normal',-- 数据质量：excellent/good/normal/suspicious/missing
    completeness DOUBLE,                  -- 完整度（0-100）
    confidence DOUBLE,                    -- 置信度（0-1）

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,               -- 最后同步时间

    -- 扩展字段（JSON格式，存储任意额外数据）
    extra_data JSON,                      -- 扩展数据

    -- 唯一约束（同一数据源、同一股票、同一日期只能有一条）
    UNIQUE(source, code, date, time)
);

-- 索引优化
CREATE INDEX idx_source_code_date ON stock_kline_unified(source, code, date);
CREATE INDEX idx_code_date ON stock_kline_unified(code, date);
CREATE INDEX idx_date ON stock_kline_unified(date);
CREATE INDEX idx_data_quality ON stock_kline_unified(data_quality);

-- 注释
COMMENT ON TABLE stock_kline_unified IS '统一K线数据表，支持多数据源';
COMMENT ON COLUMN stock_kline_unified.source IS '数据源标识：yahoo/akshare/playwright/sina/eastmoney/...'
```

### 表2：stock_info_unified（统一股票信息表）

```sql
CREATE TABLE stock_info_unified (
    id INTEGER PRIMARY KEY,

    -- 数据来源
    source VARCHAR NOT NULL,              -- 数据源
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 股票标识
    code VARCHAR PRIMARY KEY,
    name VARCHAR,
    pinyin VARCHAR,
    short_name VARCHAR,

    -- 分类信息
    industry VARCHAR,                     -- 行业
    sector VARCHAR,                       -- 板块
    concept VARCHAR,                      -- 概念（JSON数组）
    tags VARCHAR,                         -- 标签（JSON数组）

    -- 市场信息
    exchange VARCHAR,                     -- 交易所
    market VARCHAR,                       -- 市场
    list_date DATE,                       -- 上市日期
    delist_date DATE,                     -- 退市日期
    status VARCHAR DEFAULT 'active',      -- 状态

    -- Yahoo Finance提供的字段（158个）
    website VARCHAR,
    phone VARCHAR,
    address VARCHAR,
    city VARCHAR,
    country VARCHAR,
    fullTimeEmployees INTEGER,
    businessSummary TEXT,                 -- 业务摘要
    longBusinessSummary TEXT,             -- 长业务摘要

    -- 市值指标
    market_cap BIGINT,                    -- 总市值
    market_cap_basic BIGINT,              -- 基础市值
    shares_outstanding BIGINT,            -- 流通股本
    shares_percent_float DOUBLE,          -- 流通比例

    -- 估值指标
    pe_ratio DOUBLE,                      -- 市盈率
    peg_ratio DOUBLE,                     -- PEG比率
    ps_ratio DOUBLE,                      -- 市销率
    pb_ratio DOUBLE,                      -- 市净率
    ev_to_ebitda DOUBLE,                  -- EV/EBITDA

    -- 财务指标
    total_revenue DOUBLE,                 -- 总收入
    revenue_per_share DOUBLE,             -- 每股收入
    profit_margin DOUBLE,                 -- 利润率
    operating_margin DOUBLE,              -- 营业利润率
    roe DOUBLE,                           -- ROE
    roa DOUBLE,                           -- ROA
    return_on_assets DOUBLE,              -- 总资产回报率
    quarterly_revenue_growth DOUBLE,      -- 季度收入增长
    quarterly_earnings_growth DOUBLE,     -- 季度盈利增长

    -- 分红相关
    dividend_rate DOUBLE,                 -- 分红收益率
    dividend_yield DOUBLE,                -- 股息率
    last_dividend_date DATE,              -- 最后分红日期
    ex_dividend_date DATE,                -- 除息日

    -- 风险指标
    beta DOUBLE,                          -- Beta系数
    fifty_two_week_high DOUBLE,           -- 52周最高
    fifty_two_week_low DOUBLE,            -- 52周最低

    -- 分析师评级
    target_price DOUBLE,                  -- 目标价
    recommendation_grade VARCHAR,         -- 评级等级

    -- 扩展字段
    extra_data JSON
);
```

### 表3：data_source_registry（数据源注册表）⭐ **新增**

```sql
CREATE TABLE data_source_registry (
    id INTEGER PRIMARY KEY,
    source_name VARCHAR UNIQUE NOT NULL,  -- 数据源名称
    display_name VARCHAR,                 -- 显示名称
    source_type VARCHAR,                  -- 类型：api/crawler/database/manual

    -- 能力描述
    capabilities JSON,                    -- 提供哪些字段
    """
    {
        "kline": true,
        "info": true,
        "financials": false,
        "dividends": true,
        "realtime": false,
        "minute_data": true,
        "capital_flow": false
    }
    """

    -- 优先级配置
    priority INTEGER DEFAULT 0,           -- 优先级（数字越大优先级越高）
    quality_score DOUBLE DEFAULT 0.5,     -- 质量评分（0-1）

    -- 可用性
    is_active BOOLEAN DEFAULT true,
    requires_auth BOOLEAN DEFAULT false,
    rate_limit INTEGER,                   -- 速率限制（次/分钟）

    -- 成本
    cost_per_request DOUBLE DEFAULT 0,    -- 每次请求成本
    cost_per_month DOUBLE DEFAULT 0,      -- 每月成本

    -- 技术信息
    api_version VARCHAR,
    documentation_url VARCHAR,
    last_test_time TIMESTAMP,
    last_test_status VARCHAR,

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 初始化数据源
INSERT INTO data_source_registry (source_name, display_name, source_type, priority, quality_score) VALUES
    ('yahoo', 'Yahoo Finance', 'api', 90, 0.9),
    ('akshare', 'AKShare', 'api', 80, 0.8),
    ('playwright', 'Playwright爬虫', 'crawler', 70, 0.6),
    ('sina', '新浪财经', 'api', 60, 0.7),
    ('eastmoney', '东方财富', 'crawler', 65, 0.7),
    ('manual', '手动录入', 'manual', 100, 1.0);
```

### 表4：data_source_field_mapping（字段映射表）⭐ **新增**

```sql
CREATE TABLE data_source_field_mapping (
    id INTEGER PRIMARY KEY,

    -- 数据源信息
    source VARCHAR NOT NULL,              -- 数据源
    source_field VARCHAR NOT NULL,        -- 数据源字段名

    -- 统一字段名
    unified_field VARCHAR NOT NULL,       -- 统一字段名

    -- 转换规则
    data_type VARCHAR,                    -- 数据类型
    transform_rule VARCHAR,               -- 转换规则（JSON）
    """
    {
        "type": "datetime_to_date",
        "format": "%Y-%m-%d",
        "timezone": "Asia/Shanghai"
    }
    """

    -- 默认值
    default_value VARCHAR,

    -- 验证规则
    validation_rule VARCHAR,              -- 验证规则（JSON）
    """
    {
        "min": 0,
        "max": 1000000,
        "required": false
    }
    """

    -- 状态
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source, source_field, unified_field)
);

-- 初始化字段映射
INSERT INTO data_source_field_mapping (source, source_field, unified_field, data_type) VALUES
    -- Yahoo Finance字段映射
    ('yahoo', 'Open', 'open', 'DOUBLE'),
    ('yahoo', 'High', 'high', 'DOUBLE'),
    ('yahoo', 'Low', 'low', 'DOUBLE'),
    ('yahoo', 'Close', 'close', 'DOUBLE'),
    ('yahoo', 'Volume', 'volume', 'BIGINT'),
    ('yahoo', 'Adj Close', 'adj_close', 'DOUBLE'),
    ('yahoo', 'Dividends', 'dividends', 'DOUBLE'),
    ('yahoo', 'Stock Splits', 'stock_splits', 'DOUBLE'),

    -- AKShare字段映射
    ('akshare', '开盘', 'open', 'DOUBLE'),
    ('akshare', '最高', 'high', 'DOUBLE'),
    ('akshare', '最低', 'low', 'DOUBLE'),
    ('akshare', '收盘', 'close', 'DOUBLE'),
    ('akshare', '成交量', 'volume', 'DOUBLE'),
    ('akshare', '成交额', 'amount', 'DOUBLE'),
    ('akshare', '涨跌幅', 'pct_change', 'DOUBLE'),
    ('akshare', '换手率', 'turnover_rate', 'DOUBLE');
```

---

## 🔄 数据插入流程

### 标准插入流程

```python
def insert_stock_data(source: str, data: dict, db_conn):
    """
    通用数据插入函数

    Args:
        source: 数据源标识（yahoo/akshare/playwright/...）
        data: 数据字典
        db_conn: 数据库连接
    """

    # 1. 检查数据源是否注册
    source_info = db_conn.execute('''
        SELECT * FROM data_source_registry
        WHERE source_name = ? AND is_active = true
    ''', (source,)).fetchone()

    if not source_info:
        raise ValueError(f'未注册的数据源: {source}')

    # 2. 字段映射（根据数据源自动转换）
    mapped_data = apply_field_mapping(source, data, db_conn)

    # 3. 添加元数据
    mapped_data['source'] = source
    mapped_data['created_at'] = datetime.now()
    mapped_data['updated_at'] = datetime.now()
    mapped_data['last_sync_at'] = datetime.now()

    # 4. 计算数据质量指标
    mapped_data['completeness'] = calculate_completeness(mapped_data)
    mapped_data['data_quality'] = assess_data_quality(mapped_data)

    # 5. 插入数据库
    columns = list(mapped_data.keys())
    placeholders = ', '.join(['?' for _ in columns])
    sql = f'''
        INSERT OR REPLACE INTO stock_kline_unified
        ({', '.join(columns)})
        VALUES ({placeholders})
    '''

    db_conn.execute(sql, list(mapped_data.values()))


def apply_field_mapping(source: str, data: dict, db_conn) -> dict:
    """应用字段映射规则"""

    # 查询该数据源的字段映射
    mappings = db_conn.execute('''
        SELECT source_field, unified_field, data_type, transform_rule
        FROM data_source_field_mapping
        WHERE source = ? AND is_active = true
    ''', (source,)).fetchall()

    mapped_data = {}

    for source_field, unified_field, data_type, transform_rule in mappings:
        if source_field in data:
            value = data[source_field]

            # 应用转换规则
            if transform_rule:
                value = apply_transform(value, transform_rule)

            mapped_data[unified_field] = value

    # 未映射的字段直接保留
    for key, value in data.items():
        if key not in mapped_data:
            mapped_data[key] = value

    return mapped_data


def calculate_completeness(data: dict) -> double:
    """计算数据完整度"""

    core_fields = ['open', 'high', 'low', 'close', 'volume']
    filled_count = sum(1 for field in core_fields if field in data and data[field] is not None)

    return (filled_count / len(core_fields)) * 100
```

### Yahoo Finance数据插入示例

```python
import yfinance as yf

def sync_yahoo_data(code: str, period: str = '1mo'):
    """同步Yahoo Finance数据"""

    ticker = yf.Ticker(f'{code}.SS')
    df = ticker.history(period=period)

    for idx, row in df.iterrows():
        data = {
            'code': code,
            'date': idx.strftime('%Y-%m-%d'),
            'Open': row['Open'],
            'High': row['High'],
            'Low': row['Low'],
            'Close': row['Close'],
            'Volume': row['Volume'],
            'Dividends': row['Dividends'],
            'Stock Splits': row['Stock Splits']
        }

        insert_stock_data('yahoo', data, db_conn)
```

### Playwright爬虫数据插入示例

```python
def sync_playwright_capital_flow(code: str):
    """同步Playwright爬取的资金流数据"""

    data = scrape_capital_flow(code)  # 爬虫函数

    # 只插入资金流相关字段，其他字段为NULL
    insert_data = {
        'code': code,
        'date': data['date'],
        'net_inflow': data['net_inflow'],
        'main_inflow': data['main_inflow'],
        'super_large_inflow': data['super_large_inflow'],
        'large_inflow': data['large_inflow'],
        'medium_inflow': data['medium_inflow'],
        'small_inflow': data['small_inflow']
    }

    insert_stock_data('playwright', insert_data, db_conn)
```

---

## 🔍 数据查询策略

### 视图1：stock_kline_merged（自动合并视图）

```sql
CREATE VIEW stock_kline_merged AS
WITH ranked_data AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY code, date
            ORDER BY
                -- 优先级1：手动录入
                CASE WHEN source = 'manual' THEN 100 ELSE 0 END +
                -- 优先级2：数据源配置的优先级
                (SELECT priority FROM data_source_registry WHERE source_name = stock_kline_unified.source) DESC
        ) as rank
    FROM stock_kline_unified
)
SELECT
    code,
    date,
    MAX(CASE WHEN rank = 1 THEN open END) as open,
    MAX(CASE WHEN rank = 1 THEN high END) as high,
    MAX(CASE WHEN rank = 1 THEN low END) as low,
    MAX(CASE WHEN rank = 1 THEN close END) as close,
    MAX(CASE WHEN rank = 1 THEN volume END) as volume,

    -- 合并多源数据（取非NULL值）
    MAX(adj_close) as adj_close,
    MAX(amount) as amount,
    MAX(pct_change) as pct_change,
    MAX(turnover_rate) as turnover_rate,

    -- 资金流数据（通常来自Playwright）
    MAX(net_inflow) as net_inflow,
    MAX(main_inflow) as main_inflow,

    -- 数据来源标识
    MAX(CASE WHEN rank = 1 THEN source END) as primary_source,

    -- 元数据
    MAX(data_quality) as data_quality,
    MAX(completeness) as completeness
FROM ranked_data
GROUP BY code, date;
```

### 查询示例

```sql
-- 查询某只股票的最新数据（自动合并多源）
SELECT * FROM stock_kline_merged
WHERE code = '600519'
ORDER BY date DESC
LIMIT 10;

-- 查询特定数据源的原始数据
SELECT * FROM stock_kline_unified
WHERE source = 'yahoo' AND code = '600519'
ORDER BY date DESC;

-- 查询数据来源分布
SELECT
    code,
    date,
    GROUP_CONCAT(source) as sources,
    COUNT(*) as source_count
FROM stock_kline_unified
WHERE code = '600519'
GROUP BY code, date
ORDER BY date DESC;
```

---

## 🛠️ 扩展新数据源

### 步骤1：注册数据源

```sql
INSERT INTO data_source_registry (
    source_name,
    display_name,
    source_type,
    priority,
    quality_score,
    capabilities
) VALUES (
    'tushare',
    'Tushare Pro',
    'api',
    85,
    0.85,
    '{"kline": true, "info": true, "financials": true, "realtime": false}'
);
```

### 步骤2：配置字段映射

```sql
INSERT INTO data_source_field_mapping (source, source_field, unified_field, data_type) VALUES
    ('tushare', 'open', 'open', 'DOUBLE'),
    ('tushare', 'high', 'high', 'DOUBLE'),
    ('tushare', 'low', 'low', 'DOUBLE'),
    ('tushare', 'close', 'close', 'DOUBLE'),
    ('tushare', 'vol', 'volume', 'BIGINT');
```

### 步骤3：实现数据同步函数

```python
def sync_tushare_data(code: str):
    """同步Tushare数据"""
    import tushare as ts

    df = ts.pro_bar(ts_code=f'{code}.SZ', start_date='20200101')

    for idx, row in df.iterrows():
        data = {
            'code': code,
            'date': row['trade_date'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'vol': row['vol']
        }

        insert_stock_data('tushare', data, db_conn)
```

### 完成！

新数据源自动集成到统一视图，无需修改其他代码。

---

## 📋 实现清单

### 阶段1：数据库表创建（1小时）
- [ ] 创建stock_kline_unified表
- [ ] 创建stock_info_unified表
- [ ] 创建data_source_registry表
- [ ] 创建data_source_field_mapping表
- [ ] 创建索引和视图

### 阶段2：核心功能实现（3小时）
- [ ] 实现insert_stock_data通用函数
- [ ] 实现apply_field_mapping函数
- [ ] 实现calculate_completeness函数
- [ ] 实现assess_data_quality函数

### 阶段3：数据源集成（4小时）
- [ ] Yahoo Finance集成
- [ ] AKShare集成
- [ ] Playwright集成（资金流）

### 阶段4：测试验证（2小时）
- [ ] 单数据源测试
- [ ] 多数据源合并测试
- [ ] 数据完整性验证
- [ ] 性能测试

**总计：约10小时**

---

## 🎯 优势总结

### ✅ 与之前方案相比

| 特性 | 方案1（旧） | 方案2（新） |
|------|-----------|-----------|
| **扩展性** | 需要修改表结构 | 无需修改，通过配置表添加 |
| **灵活性** | 固定字段 | JSON扩展字段 + 可配置映射 |
| **可维护性** | 硬编码逻辑 | 数据驱动的映射规则 |
| **数据溯源** | 只有source字段 | 完整的注册表 + 映射表 |
| **优先级控制** | 硬编码 | 可配置的priority |
| **新数据源** | 需要修改代码 | 只需配置表 + 插入函数 |
| **字段转换** | 硬编码 | 可配置的transform_rule |

### 🚀 未来可扩展的数据源

- ✅ **Tushare Pro** - 专业金融数据
- ✅ **Wind（万得）** - 机构级别数据
- ✅ **Choice（东方财富）** - 金融终端数据
- ✅ **Bloomberg** - 国际金融数据
- ✅ **Reuters** - 路透社数据
- ✅ **手动录入** - 人工修正数据
- ✅ **第三方API** - 任何其他API

---

**设计人**: AI Agent
**版本**: v2.0
**更新时间**: 2026-03-13

# 股票数据系统 - 分阶段实现计划

**架构理念**：设计支持多数据源（API + 爬虫），实施分阶段进行

**阶段划分**：
- 🥇 **阶段1**：雅虎财经为主（快速验证）
- 🥈 **阶段2**：东方财富爬虫补充（完善数据）
- 🥉 **阶段3**：其他数据源扩展（可选）

---

## 🏗️ 统一架构设计（支持多数据源）

### 核心表设计

```sql
-- ============================================
-- 统一K线表（支持雅虎API + 东方财富爬虫）
-- ============================================
CREATE TABLE stock_kline_unified (
    id INTEGER PRIMARY KEY,

    -- 数据源标识（关键！）
    source VARCHAR NOT NULL,              -- 数据源：yahoo/eastmoney/10jqka/akshare/...
    source_type VARCHAR NOT NULL,         -- 数据源类型：api/crawler/manual

    -- 股票标识
    code VARCHAR NOT NULL,                -- 标准化代码（6位数字）
    name VARCHAR,                         -- 股票名称

    -- 时间字段
    date DATE NOT NULL,
    time TIME,                            -- 分钟数据用

    -- 雅虎财经字段（阶段1核心）
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,                     -- 复权价（雅虎特有）
    volume BIGINT,

    -- 雅虎财经特有
    dividends DOUBLE,
    stock_splits DOUBLE,

    -- 东方财富字段（阶段2添加）
    amount DOUBLE,                        -- 成交额
    pct_change DOUBLE,                    -- 涨跌幅
    turnover_rate DOUBLE,                 -- 换手率
    amplitude DOUBLE,                     -- 振幅
    pe_ratio DOUBLE,                      -- 市盈率（动态）
    market_cap DOUBLE,                    -- 总市值

    -- 东方财富资金流（阶段2添加）
    main_net_inflow DOUBLE,               -- 主力净流入
    super_large_net_inflow DOUBLE,
    large_net_inflow DOUBLE,
    medium_net_inflow DOUBLE,
    small_net_inflow DOUBLE,

    -- 爬虫元数据（阶段2使用）
    crawl_time TIMESTAMP,                 -- 爬取时间
    crawl_url VARCHAR,                    -- 爬取URL
    crawl_status VARCHAR,                 -- 状态：success/failed

    -- 数据质量
    data_quality VARCHAR DEFAULT 'unknown', -- excellent/good/normal/suspicious
    completeness DOUBLE,                  -- 完整度（0-100）

    -- 统一元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 扩展字段（JSON，存储任意额外数据）
    extra_data JSON,

    -- 唯一约束（同一数据源、同一股票、同一日期只能有一条）
    UNIQUE(source, code, date, time)
);

-- 索引
CREATE INDEX idx_source_code_date ON stock_kline_unified(source, code, date);
CREATE INDEX idx_code_date ON stock_kline_unified(code, date);
CREATE INDEX idx_source_type ON stock_kline_unified(source_type);

-- ============================================
-- 统一股票信息表
-- ============================================
CREATE TABLE stock_info_unified (
    id INTEGER PRIMARY KEY,

    source VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,

    code VARCHAR PRIMARY KEY,
    name VARCHAR,
    industry VARCHAR,
    sector VARCHAR,

    -- 雅虎财经提供（158个字段）
    market_cap BIGINT,
    pe_ratio DOUBLE,
    pb_ratio DOUBLE,
    dividend_yield DOUBLE,
    beta DOUBLE,
    website VARCHAR,
    phone VARCHAR,
    businessSummary TEXT,

    -- 东方财富提供（阶段2）
    list_date DATE,
    total_shares BIGINT,
    circulating_shares BIGINT,
    main_business TEXT,

    extra_data JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 数据源注册表（管理所有数据源）
-- ============================================
CREATE TABLE data_source_registry (
    id INTEGER PRIMARY KEY,

    source_name VARCHAR UNIQUE NOT NULL,  -- 数据源名称
    display_name VARCHAR,
    source_type VARCHAR,                  -- api/crawler/manual

    -- 能力描述（JSON）
    capabilities JSON,
    """
    阶段1（雅虎）：
    {
        "kline_daily": true,
        "kline_minute": true,
        "info": true,
        "dividends": true,
        "realtime": false
    }

    阶段2（东方财富）：
    {
        "kline_daily": true,
        "kline_minute": true,
        "capital_flow": true,
        "financials": true,
        "realtime": true
    }
    """

    -- 优先级配置
    priority INTEGER DEFAULT 0,
    quality_score DOUBLE DEFAULT 0.5,

    -- 可用性
    is_active BOOLEAN DEFAULT true,
    requires_auth BOOLEAN DEFAULT false,
    rate_limit INTEGER,

    -- 阶段标识
    stage VARCHAR DEFAULT 'phase1',       -- phase1/phase2/phase3

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化阶段1数据源
INSERT INTO data_source_registry (source_name, display_name, source_type, priority, quality_score, stage, capabilities) VALUES
    ('yahoo', 'Yahoo Finance', 'api', 90, 0.9, 'phase1',
     '{"kline_daily": true, "kline_minute": true, "info": true, "dividends": true}' ),

    ('akshare', 'AKShare', 'api', 80, 0.8, 'phase1',
     '{"kline_daily": true, "info": true}' );

-- 预注册阶段2数据源（不激活）
INSERT INTO data_source_registry (source_name, display_name, source_type, priority, stage, is_active, capabilities) VALUES
    ('eastmoney', '东方财富', 'crawler', 95, 'phase2', false,
     '{"kline_daily": true, "kline_minute": true, "capital_flow": true, "realtime": true}' ),

    ('10jqka', '同花顺', 'crawler', 85, 'phase2', false,
     '{"realtime": true, "kline_minute": true}' );
```

---

## 📅 阶段1：雅虎财经为主（预计4小时）

### 目标
- ✅ 验证统一架构可行性
- ✅ 实现核心K线数据获取
- ✅ 建立基础数据流

### 实现清单

#### 1.1 数据库初始化（30分钟）
```python
# init_database_phase1.py
import duckdb

DB_PATH = 'C:/AI-Agent-Local/openclaw-ali/data/stock_market.db'

def init_database():
    con = duckdb.connect(DB_PATH)

    # 创建统一K线表
    con.execute('''
        CREATE TABLE stock_kline_unified (
            ... (见上面的SQL)
        )
    ''')

    # 创建统一信息表
    con.execute('''
        CREATE TABLE stock_info_unified (
            ... (见上面的SQL)
        )
    ''')

    # 创建数据源注册表
    con.execute('''
        CREATE TABLE data_source_registry (
            ... (见上面的SQL)
        )
    ''')

    # 初始化雅虎数据源
    con.execute('''
        INSERT INTO data_source_registry (source_name, display_name, source_type, priority)
        VALUES ('yahoo', 'Yahoo Finance', 'api', 90)
    ''')

    print('✅ 数据库初始化完成')
```

#### 1.2 雅虎财经数据同步脚本（2小时）
```python
# sync_yahoo_finance.py
import yfinance as yf
import duckdb
from datetime import datetime

def sync_yahoo_kline(code: str, period: str = '1mo'):
    """同步雅虎财经K线数据"""

    # 获取数据
    ticker = yf.Ticker(f'{code}.SS')
    df = ticker.history(period=period)

    # 连接数据库
    con = duckdb.connect(DB_PATH)

    # 插入数据
    for idx, row in df.iterrows():
        date_str = idx.strftime('%Y-%m-%d')

        # 计算涨跌幅
        pct_change = None
        if idx != df.index[0]:
            prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
            pct_change = (row['Close'] - prev_close) / prev_close * 100

        con.execute('''
            INSERT OR REPLACE INTO stock_kline_unified
            (source, source_type, code, name, date, open, high, low, close,
             adj_close, volume, dividends, stock_splits, pct_change,
             data_quality, completeness, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'yahoo',                          -- source
            'api',                            -- source_type
            code,                             -- code
            None,                             -- name（从info表获取）
            date_str,                         -- date
            row['Open'],                      -- open
            row['High'],                      -- high
            row['Low'],                       -- low
            row['Close'],                     -- close
            row.get('Adj Close'),             -- adj_close
            row['Volume'],                    -- volume
            row['Dividends'],                 -- dividends
            row['Stock Splits'],              -- stock_splits
            pct_change,                       -- pct_change
            'good',                           -- data_quality
            100.0,                            -- completeness（雅虎数据完整）
            datetime.now(),                   -- created_at
            datetime.now()                    -- updated_at
        ))

    print(f'✅ {code} 同步完成：{len(df)} 条记录')

def sync_yahoo_info(code: str):
    """同步雅虎财经个股信息"""

    ticker = yf.Ticker(f'{code}.SS')
    info = ticker.info

    con = duckdb.connect(DB_PATH)

    con.execute('''
        INSERT OR REPLACE INTO stock_info_unified
        (source, source_type, code, name, industry, sector, market_cap,
         pe_ratio, pb_ratio, dividend_yield, beta, website, phone,
         businessSummary, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'yahoo', 'api',
        code,
        info.get('shortName'),
        info.get('industry'),
        info.get('sector'),
        info.get('marketCap'),
        info.get('trailingPE'),
        info.get('priceToBook'),
        info.get('dividendYield'),
        info.get('beta'),
        info.get('website'),
        info.get('phone'),
        info.get('longBusinessSummary'),
        datetime.now()
    ))

    print(f'✅ {code} 信息同步完成')

# 测试脚本
if __name__ == '__main__':
    # 测试股票列表
    test_stocks = [
        ('600519', '贵州茅台'),
        ('000001', '平安银行'),
        ('601669', '中国电建'),
        ('002594', '比亚迪'),
        ('300750', '宁德时代')
    ]

    for code, name in test_stocks:
        sync_yahoo_kline(code, period='1mo')
        sync_yahoo_info(code)
```

#### 1.3 数据查询和验证（1小时）
```python
# verify_yahoo_data.py
import duckdb

def verify_data():
    con = duckdb.connect(DB_PATH)

    print('=== 数据验证 ===')

    # 1. 检查记录数
    count = con.execute('SELECT COUNT(*) FROM stock_kline_unified').fetchone()[0]
    print(f'总记录数: {count}')

    # 2. 检查股票数
    stocks = con.execute('SELECT COUNT(DISTINCT code) FROM stock_kline_unified').fetchone()[0]
    print(f'股票数: {stocks}')

    # 3. 检查日期范围
    date_range = con.execute('SELECT MIN(date), MAX(date) FROM stock_kline_unified').fetchone()
    print(f'日期范围: {date_range[0]} 至 {date_range[1]}')

    # 4. 检查数据源
    sources = con.execute('SELECT source, COUNT(*) FROM stock_kline_unified GROUP BY source').fetchall()
    print('数据源分布:')
    for source, count in sources:
        print(f'  {source}: {count} 条')

    # 5. 查看样例数据
    print()
    print('样例数据（贵州茅台最新5条）:')
    df = con.execute('''
        SELECT * FROM stock_kline_unified
        WHERE code = '600519'
        ORDER BY date DESC
        LIMIT 5
    ''').fetchdf()
    print(df)

if __name__ == '__main__':
    verify_data()
```

#### 1.4 文档和测试（30分钟）
- [ ] 编写使用文档
- [ ] 本地测试验证
- [ ] 性能测试

---

## 📅 阶段2：东方财富爬虫补充（预计6小时）

### 前提条件
- ✅ 阶段1架构验证通过
- ✅ 数据库表结构支持爬虫数据

### 目标
- ✅ 补充成交额、换手率等雅虎没有的字段
- ✅ 添加资金流向数据
- ✅ 提供实时数据支持

### 实现清单

#### 2.1 Playwright环境准备（30分钟）
```bash
# 安装Playwright
pip install playwright
playwright install chromium

# 验证安装
python -m playwright install
```

#### 2.2 东方财富K线爬虫（2小时）
```python
# crawlers/eastmoney_kline_crawler.py
import asyncio
from playwright.async_api import async_playwright
import duckdb
from datetime import datetime

class EastMoneyKlineCrawler:
    """东方财富K线爬虫"""

    def __init__(self):
        self.db_path = DB_PATH

    async def crawl(self, code: str, start_date: str, end_date: str):
        """爬取K线数据（补充成交额、换手率）"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 构造URL
            url = f'http://push2.eastmoney.com/api/qt/stock/klt?secid={code}&fields1=&fields2=&klt=1&fqt=1&beg={start_date}&end={end_date}'

            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            # 提取数据
            data = await page.evaluate('() => { return window.quotationCodeTableData || []; }')

            # 连接数据库
            con = duckdb.connect(self.db_path)

            # 插入数据（补充雅虎没有的字段）
            for row in data:
                # 检查是否已有雅虎数据
                existing = con.execute('''
                    SELECT * FROM stock_kline_unified
                    WHERE source = 'yahoo' AND code = ? AND date = ?
                ''', (code, row['date'])).fetchone()

                if existing:
                    # 更新雅虎记录，补充东方财富字段
                    con.execute('''
                        UPDATE stock_kline_unified
                        SET
                            amount = ?,
                            turnover_rate = ?,
                            amplitude = ?,
                            pe_ratio = ?,
                            market_cap = ?,
                            updated_at = ?
                        WHERE source = 'yahoo' AND code = ? AND date = ?
                    ''', (
                        row.get('amount'),
                        row.get('turnoverRate'),
                        row.get('amplitude'),
                        row.get('peRatio'),
                        row.get('marketCap'),
                        datetime.now(),
                        code,
                        row['date']
                    ))
                else:
                    # 插入纯东方财富数据
                    con.execute('''
                        INSERT INTO stock_kline_unified
                        (source, source_type, code, date, open, high, low, close, volume,
                         amount, pct_change, turnover_rate, amplitude, pe_ratio, market_cap,
                         crawl_time, crawl_status, data_quality, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'eastmoney',
                        'crawler',
                        code,
                        row['date'],
                        row['open'],
                        row['high'],
                        row['low'],
                        row['close'],
                        row['volume'],
                        row['amount'],           # 成交额（雅虎没有）
                        row['changePercent'],    # 涨跌幅
                        row['turnoverRate'],     # 换手率（雅虎没有）
                        row['amplitude'],        # 振幅（雅虎没有）
                        row['peRatio'],          # 市盈率（雅虎没有）
                        row['marketCap'],        # 市值（雅虎没有）
                        datetime.now(),          # crawl_time
                        'success',               # crawl_status
                        'good',                  # data_quality
                        datetime.now()           # created_at
                    ))

            await browser.close()

        print(f'✅ {code} 东方财富数据同步完成')

# 测试
async def main():
    crawler = EastMoneyKlineCrawler()
    await crawler.crawl('600519', '20240201', '20240313')

if __name__ == '__main__':
    asyncio.run(main())
```

#### 2.3 东方财富资金流爬虫（2小时）
```python
# crawlers/eastmoney_capital_crawler.py
class EastMoneyCapitalCrawler:
    """东方财富资金流爬虫"""

    async def crawl(self, code: str):
        """爬取资金流向数据"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 访问资金流页面
            url = f'http://data.eastmoney.com/zjlx/detail/{code}.html'
            await page.goto(url)
            await page.wait_for_selector('.data-view')

            # 提取资金流数据
            data = await page.evaluate('''() => {
                // 解析页面数据
                return {
                    date: document.querySelector('.date').textContent,
                    mainNetInflow: parseFloat(document.querySelector('.main-inflow').textContent),
                    superLargeNetInflow: parseFloat(document.querySelector('.super-large-inflow').textContent),
                    largeNetInflow: parseFloat(document.querySelector('.large-inflow').textContent),
                    mediumNetInflow: parseFloat(document.querySelector('.medium-inflow').textContent),
                    smallNetInflow: parseFloat(document.querySelector('.small-inflow').textContent)
                };
            }''')

            # 插入数据库（更新雅虎记录，添加资金流字段）
            con = duckdb.connect(self.db_path)

            con.execute('''
                UPDATE stock_kline_unified
                SET
                    main_net_inflow = ?,
                    super_large_net_inflow = ?,
                    large_net_inflow = ?,
                    medium_net_inflow = ?,
                    small_net_inflow = ?,
                    crawl_time = ?,
                    crawl_url = ?,
                    updated_at = ?
                WHERE code = ? AND date = ?
            ''', (
                data['mainNetInflow'],
                data['superLargeNetInflow'],
                data['largeNetInflow'],
                data['mediumNetInflow'],
                data['smallNetInflow'],
                datetime.now(),           # crawl_time
                url,                      # crawl_url
                datetime.now(),           # updated_at
                code,
                data['date']
            ))

            await browser.close()

        print(f'✅ {code} 资金流数据同步完成')
```

#### 2.4 爬虫调度系统（1小时）
```python
# scheduler/crawler_scheduler.py
class CrawlerScheduler:
    """爬虫调度器"""

    def __init__(self):
        self.kline_crawler = EastMoneyKlineCrawler()
        self.capital_crawler = EastMoneyCapitalCrawler()

    async def run_daily_sync(self):
        """每日同步（收盘后执行）"""

        stocks = ['600519', '000001', '601669', '002594', '300750']

        # 同步K线数据
        for code in stocks:
            await self.kline_crawler.crawl(code, '20240201', '20240313')

        # 同步资金流数据
        for code in stocks:
            await self.capital_crawler.crawl(code)

    async def run_realtime_sync(self):
        """实时同步（交易时间）"""
        while True:
            # 检查是否交易时间
            if self.is_trading_time():
                for code in stocks:
                    await self.capital_crawler.crawl(code)

            # 每5分钟同步一次
            await asyncio.sleep(300)
```

#### 2.5 数据质量监控（30分钟）
```python
# monitoring/data_quality_monitor.py
def monitor_data_quality():
    """监控数据质量"""

    con = duckdb.connect(DB_PATH)

    # 检查数据完整性
    print('=== 数据质量报告 ===')

    # 1. 雅虎数据完整性
    yahoo_complete = con.execute('''
        SELECT code, COUNT(*) as total,
               SUM(CASE WHEN close IS NOT NULL THEN 1 ELSE 0 END) as has_close
        FROM stock_kline_unified
        WHERE source = 'yahoo'
        GROUP BY code
    ''').fetchdf()

    print('雅虎数据完整性:')
    print(yahoo_complete)

    # 2. 东方财富补充字段覆盖率
    eastmoney_coverage = con.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN amount IS NOT NULL THEN 1 ELSE 0 END) as has_amount,
            SUM(CASE WHEN turnover_rate IS NOT NULL THEN 1 ELSE 0 END) as has_turnover,
            SUM(CASE WHEN main_net_inflow IS NOT NULL THEN 1 ELSE 0 END) as has_inflow
        FROM stock_kline_unified
        WHERE source = 'yahoo'
    ''').fetchone()

    print()
    print('东方财富字段覆盖率:')
    print(f'  总记录数: {eastmoney_coverage[0]}')
    print(f'  成交额: {eastmoney_coverage[1]} ({eastmoney_coverage[1]/eastmoney_coverage[0]*100:.1f}%)')
    print(f'  换手率: {eastmoney_coverage[2]} ({eastmoney_coverage[2]/eastmoney_coverage[0]*100:.1f}%)')
    print(f'  资金流: {eastmoney_coverage[3]} ({eastmemory_coverage[3]/eastmoney_coverage[0]*100:.1f}%)')
```

---

## 📅 阶段3：其他数据源扩展（可选）

### 可能的数据源
- AKShare（已有）
- Tushare Pro
- 新浪财经
- 同花顺

---

## 🎯 实现优先级

### 🔴 **立即开始**（阶段1）
- [ ] 数据库初始化（30分钟）
- [ ] 雅虎财经同步脚本（2小时）
- [ ] 数据验证（1小时）
- [ ] 文档编写（30分钟）

### 🟡 **近期计划**（阶段2）
- [ ] Playwright环境准备
- [ ] 东方财富K线爬虫
- [ ] 东方财富资金流爬虫
- [ ] 爬虫调度系统

### 🟢 **长期规划**（阶段3）
- [ ] 其他数据源接入
- [ ] 实时数据推送
- [ ] 数据分析功能

---

## 📁 项目结构

```
openclaw-ali/
├── data/
│   └── stock_market.db              # 统一数据库
├── scripts/
│   ├── init_database_phase1.py      # 阶段1：数据库初始化
│   ├── sync_yahoo_finance.py        # 阶段1：雅虎同步
│   └── verify_yahoo_data.py         # 阶段1：数据验证
├── crawlers/                        # 阶段2：爬虫模块
│   ├── __init__.py
│   ├── base_crawler.py              # 爬虫基类
│   ├── eastmoney_kline_crawler.py   # 东方财富K线
│   └── eastmoney_capital_crawler.py # 东方财富资金流
└── scheduler/                       # 阶段2：调度模块
    └── crawler_scheduler.py
```

---

**计划制定人**: AI Agent
**版本**: v1.0
**日期**: 2026-03-13

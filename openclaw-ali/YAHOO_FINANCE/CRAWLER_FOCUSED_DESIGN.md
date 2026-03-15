# 爬虫为中心的股票数据架构设计

**设计理念**：爬虫是主要数据源，API是补充

**核心数据源**：
- 🥇 东方财富（eastmoney） - K线、资金流、财务数据、股东信息
- 🥈 同花顺（10jqka） - 实时行情、技术指标、资讯
- 🥉 新浪财经（sina） - 实时行情
- ➕ Yahoo Finance - 海外市场、基础数据补充
- ➕ AKShare - 国内API补充

**版本**: v3.0
**更新时间**: 2026-03-13

---

## 🕷️ 爬虫数据源分析

### 东方财富（数据最全）

| 数据类型 | 爬取难度 | 更新频率 | 反爬虫 | 价值 |
|---------|---------|---------|--------|------|
| **历史K线** | ⭐ 简单 | 日收盘后 | 低 | ⭐⭐⭐ |
| **分钟K线** | ⭐⭐ 中等 | 实时 | 低 | ⭐⭐⭐⭐⭐ |
| **资金流向** | ⭐⭐⭐ 较难 | 实时 | 中 | ⭐⭐⭐⭐⭐ |
| **龙虎榜** | ⭐⭐ 中等 | 日收盘后 | 低 | ⭐⭐⭐⭐ |
| **财务报表** | ⭐⭐⭐ 较难 | 季度 | 中 | ⭐⭐⭐⭐ |
| **股东信息** | ⭐⭐ 中等 | 季度 | 低 | ⭐⭐⭐ |
| **公告信息** | ⭐⭐⭐ 较难 | 实时 | 高 | ⭐⭐⭐ |
| **研报** | ⭐⭐⭐⭐ 难 | 日 | 高 | ⭐⭐⭐⭐ |

**关键URL**：
```
K线数据：http://push2.eastmoney.com/api/qt/stock/klt?
资金流：http://data.eastmoney.com/zjlx/detail/
龙虎榜：http://data.eastmoney.com/longhu/
财务数据：http://data.eastmoney.com/bbsj/
```

### 同花顺（实时性好）

| 数据类型 | 爬取难度 | 更新频率 | 反爬虫 | 价值 |
|---------|---------|---------|--------|------|
| **实时行情** | ⭐⭐ 中等 | 实时 | 中 | ⭐⭐⭐⭐⭐ |
| **技术指标** | ⭐⭐⭐ 较难 | 实时 | 中 | ⭐⭐⭐⭐ |
| **资金流** | ⭐⭐⭐ 较难 | 实时 | 中 | ⭐⭐⭐⭐ |
| **F10资料** | ⭐⭐⭐ 较难 | 不定期 | 中 | ⭐⭐⭐⭐ |
| **资讯** | ⭐⭐⭐⭐ 难 | 实时 | 高 | ⭐⭐⭐ |

**关键URL**：
```
实时行情：http://q.10jqka.com.cn/
资金流：http://data.10jqka.com.cn/market/zjlx/
F10：http://basic.10jqka.com.cn/
```

---

## 🏗️ 数据库设计（爬虫优化版）

### 表1：stock_kline_eastmoney（东方财富K线表）

```sql
CREATE TABLE stock_kline_eastmoney (
    id INTEGER PRIMARY KEY,

    -- 爬虫元数据（重要！）
    crawl_source VARCHAR NOT NULL,        -- 爬虫来源：eastmoney/10jqka/sina
    crawl_method VARCHAR NOT NULL,        -- 爬取方式：api/html/websocket
    crawl_url VARCHAR,                    -- 爬取URL
    crawl_time TIMESTAMP NOT NULL,        -- 爬取时间
    crawl_status VARCHAR,                 -- 状态：success/failed/timeout
    crawl_retry_count INTEGER DEFAULT 0,  -- 重试次数

    -- 股票信息
    code VARCHAR NOT NULL,
    name VARCHAR,
    date DATE NOT NULL,
    time TIME,                            -- 分钟数据

    -- 东方财富字段（最全）
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    amount DOUBLE,                        -- 成交额（重要）
    turnover_rate DOUBLE,                 -- 换手率（重要）
    pct_change DOUBLE,                    -- 涨跌幅（重要）

    -- 东方财富特有字段
    amplitude DOUBLE,                     -- 振幅
    pe_ratio DOUBLE,                      -- 市盈率（动态）
    market_cap DOUBLE,                    -- 总市值
    circulating_cap DOUBLE,              -- 流通市值
    limit_status VARCHAR,                 -- 涨跌停状态

    -- 数据质量
    data_quality VARCHAR DEFAULT 'unknown',
    is_complete BOOLEAN DEFAULT false,
    suspicious_flags JSON,                -- 可疑标记
    """
    {
        "abnormal_volume": false,
        "missing_fields": [],
        "inconsistent_values": []
    }
    """

    -- 扩展字段
    extra_data JSON,

    -- 唯一约束
    UNIQUE(crawl_source, code, date, time)
);

CREATE INDEX idx_code_date ON stock_kline_eastmoney(code, date);
CREATE INDEX idx_crawl_time ON stock_kline_eastmoney(crawl_time);
CREATE INDEX idx_data_quality ON stock_kline_eastmoney(data_quality);
```

### 表2：capital_flow_eastmoney（东方财富资金流表）

```sql
CREATE TABLE capital_flow_eastmoney (
    id INTEGER PRIMARY KEY,

    -- 爬虫元数据
    crawl_time TIMESTAMP NOT NULL,
    crawl_url VARCHAR,
    crawl_status VARCHAR,

    -- 股票和日期
    code VARCHAR NOT NULL,
    name VARCHAR,
    date DATE NOT NULL,

    -- 当日资金流（核心数据）
    main_net_inflow DOUBLE,               -- 主力净流入
    super_large_net_inflow DOUBLE,        -- 超大单净流入
    large_net_inflow DOUBLE,              -- 大单净流入
    medium_net_inflow DOUBLE,             -- 中单净流入
    small_net_inflow DOUBLE,              -- 小单净流入

    -- 当日资金流占比
    main_net_ratio DOUBLE,                -- 主力净流入率
    super_large_net_ratio DOUBLE,
    large_net_ratio DOUBLE,
    medium_net_ratio DOUBLE,
    small_net_ratio DOUBLE,

    -- 5日累计
    main_net_5d DOUBLE,
    main_net_ratio_5d DOUBLE,

    -- 10日累计
    main_net_10d DOUBLE,
    main_net_ratio_10d DOUBLE,

    -- 排名
    flow_rank INTEGER,                    -- 流入排名

    -- 数据质量
    data_quality VARCHAR DEFAULT 'unknown',

    UNIQUE(crawl_source, code, date)
);

CREATE INDEX idx_code_date ON capital_flow_eastmoney(code, date);
CREATE INDEX idx_main_inflow ON capital_flow_eastmoney(main_net_inflow);
```

### 表3：crawler_registry（爬虫注册表）⭐ **核心**

```sql
CREATE TABLE crawler_registry (
    id INTEGER PRIMARY KEY,

    -- 爬虫标识
    crawler_name VARCHAR UNIQUE NOT NULL,  -- 爬虫名称
    display_name VARCHAR,
    target_site VARCHAR NOT NULL,         -- 目标网站：eastmoney/10jqka/sina

    -- 爬虫能力
    data_types JSON,                      -- 能爬取的数据类型
    """
    {
        "kline_daily": true,
        "kline_minute": true,
        "capital_flow": true,
        "longhubang": true,
        "financials": false,
        "realtime": true
    }
    """

    -- 技术信息
    crawl_method VARCHAR,                 -- api/html/websocket
    base_url VARCHAR,
    rate_limit INTEGER,                   -- 每分钟最大请求数

    -- 反爬虫处理
    requires_headers BOOLEAN DEFAULT false,
    requires_cookies BOOLEAN DEFAULT false,
    requires_login BOOLEAN DEFAULT false,
    proxy_support BOOLEAN DEFAULT false,
    user_agent_rotation BOOLEAN DEFAULT false,

    -- 稳定性评估
    stability_score DOUBLE DEFAULT 0.5,   -- 稳定性评分（0-1）
    success_rate DOUBLE DEFAULT 0,        -- 成功率
    avg_response_time DOUBLE,             -- 平均响应时间（毫秒）
    last_check_time TIMESTAMP,

    -- 调度配置
    schedule VARCHAR,                     -- 调度策略：realtime/daily/hourly
    priority INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT true,

    -- Playwright配置
    headless BOOLEAN DEFAULT true,
    screenshot_on_error BOOLEAN DEFAULT false,
    wait_strategy VARCHAR,                -- wait/load/networkidle

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 初始化爬虫注册
INSERT INTO crawler_registry (crawler_name, display_name, target_site, data_types, crawl_method, priority) VALUES
    ('eastmoney_kline', '东方财富K线', 'eastmoney',
     '{"kline_daily": true, "kline_minute": true}',
     'api', 90),

    ('eastmoney_capital', '东方财富资金流', 'eastmoney',
     '{"capital_flow": true}',
     'html', 85),

    ('10jqka_realtime', '同花顺实时行情', '10jqka',
     '{"realtime": true, "kline_minute": true}',
     'html', 80),

    ('sina_realtime', '新浪实时行情', 'sina',
     '{"realtime": true}',
     'api', 70);
```

### 表4：crawler_execution_log（爬虫执行日志）⭐ **重要**

```sql
CREATE TABLE crawler_execution_log (
    id INTEGER PRIMARY KEY,

    -- 执行信息
    crawler_name VARCHAR NOT NULL,
    execution_id VARCHAR NOT NULL,        -- 执行ID（UUID）
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,                  -- 执行时长（毫秒）

    -- 执行参数
    target_codes VARCHAR,                 -- 目标股票代码（JSON数组）
    date_range VARCHAR,                   -- 日期范围

    -- 执行结果
    status VARCHAR NOT NULL,              -- success/failed/timeout/partial
    records_fetched INTEGER DEFAULT 0,    -- 获取记录数
    records_inserted INTEGER DEFAULT 0,   -- 插入记录数
    records_failed INTEGER DEFAULT 0,     -- 失败记录数

    -- 错误信息
    error_type VARCHAR,                   -- 错误类型
    error_message TEXT,                   -- 错误消息
    error_stack TEXT,                     -- 错误堆栈

    -- 性能指标
    requests_count INTEGER,               -- 请求数量
    avg_response_time_ms DOUBLE,          -- 平均响应时间
    memory_used_mb DOUBLE,                -- 内存使用

    -- 反爬虫事件
    blocked BOOLEAN DEFAULT false,        -- 是否被封
    captcha_triggered BOOLEAN DEFAULT false, -- 是否触发验证码
    ip_banned BOOLEAN DEFAULT false,      -- IP是否被封

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crawler_time ON crawler_execution_log(crawler_name, start_time);
CREATE INDEX idx_status ON crawler_execution_log(status);
```

### 表5：crawler_config（爬虫配置表）⭐ **动态配置**

```sql
CREATE TABLE crawler_config (
    id INTEGER PRIMARY KEY,

    crawler_name VARCHAR NOT NULL,
    config_key VARCHAR NOT NULL,
    config_value JSON,                    -- 配置值（JSON格式）
    description VARCHAR,

    UNIQUE(crawler_name, config_key)
);

-- 示例配置
INSERT INTO crawler_config (crawler_name, config_key, config_value) VALUES
    ('eastmoney_kline', 'max_retries', '{"value": 3}'),
    ('eastmoney_kline', 'retry_delay', '{"value": 1000, "unit": "ms"}'),
    ('eastmoney_kline', 'timeout', '{"value": 30, "unit": "s"}'),
    ('eastmoney_kline', 'headers', '{"User-Agent": "Mozilla/5.0...", "Referer": "http://eastmoney.com"}'),

    ('eastmoney_capital', 'playwright_options', '{"headless": true, "timeout": 30000}'),
    ('eastmoney_capital', 'wait_selector', '{"selector": ".data-view", "timeout": 5000}'),
    ('eastmoney_capital', 'screenshot_on_error', '{"enabled": true, "path": "./screenshots/"}');
```

---

## 🕷️ 爬虫基类设计

### 基础爬虫类

```python
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, crawler_name: str, db_conn):
        self.crawler_name = crawler_name
        self.db_conn = db_conn
        self.logger = logging.getLogger(f'crawler.{crawler_name}')

        # 从注册表加载配置
        self.config = self._load_crawler_config()

        # 创建执行ID
        self.execution_id = str(uuid.uuid4())

    @abstractmethod
    async def crawl(self, **kwargs) -> List[Dict]:
        """爬取数据（子类实现）"""
        pass

    def _load_crawler_config(self) -> Dict:
        """从数据库加载爬虫配置"""
        config_rows = self.db_conn.execute('''
            SELECT config_key, config_value
            FROM crawler_config
            WHERE crawler_name = ?
        ''', (self.crawler_name,)).fetchall()

        config = {}
        for key, value in config_rows:
            config[key] = json.loads(value)

        return config

    async def _create_playwright_context(self):
        """创建Playwright上下文"""
        playwright = await async_playwright().start()

        browser = await playwright.chromium.launch(
            headless=self.config.get('headless', True),
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        context = await browser.new_context(
            user_agent=self.config.get('user_agent'),
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        return playwright, browser, context, page

    def _log_execution(self, status: str, **kwargs):
        """记录执行日志"""
        self.db_conn.execute('''
            INSERT INTO crawler_execution_log
            (crawler_name, execution_id, start_time, status, ...)
            VALUES (?, ?, ?, ?, ...)
        ''', (self.crawler_name, self.execution_id, datetime.now(), status, ...))

    async def run_with_retry(self, max_retries: int = 3):
        """带重试的执行"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f'执行爬虫 (尝试 {attempt + 1}/{max_retries})')

                data = await self.crawl()

                self._log_execution('success', records_fetched=len(data))

                return data

            except Exception as e:
                self.logger.error(f'尝试 {attempt + 1} 失败: {e}')

                if attempt == max_retries - 1:
                    self._log_execution('failed', error_message=str(e))
                    raise
                else:
                    await asyncio.sleep(self.config.get('retry_delay', 1000) / 1000)
```

### 东方财富K线爬虫

```python
class EastMoneyKlineCrawler(BaseCrawler):
    """东方财富K线爬虫"""

    async def crawl(self, codes: List[str], start_date: str, end_date: str) -> List[Dict]:
        """爬取K线数据"""

        playwright, browser, context, page = await self._create_playwright_context()

        results = []

        for code in codes:
            try:
                # 构造URL
                url = self._build_url(code, start_date, end_date)

                # 访问页面
                await page.goto(url, wait_until='networkidle')

                # 等待数据加载
                await page.wait_for_selector('.data-view', timeout=5000)

                # 提取数据
                data = await page.evaluate('''() => {
                    // 从页面JavaScript变量中提取数据
                    return window.quotationCodeTableData || [];
                }''')

                # 转换为标准格式
                for row in data:
                    results.append({
                        'code': code,
                        'date': row['date'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume'],
                        'amount': row['amount'],
                        'pct_change': row['changePercent'],
                        'turnover_rate': row['turnoverRate'],
                        'crawl_time': datetime.now(),
                        'crawl_status': 'success'
                    })

            except Exception as e:
                self.logger.error(f'爬取 {code} 失败: {e}')

                # 记录失败
                results.append({
                    'code': code,
                    'crawl_status': 'failed',
                    'error_message': str(e)
                })

        await browser.close()

        return results

    def _build_url(self, code: str, start_date: str, end_date: str) -> str:
        """构造东方财富K线URL"""
        # 东方财富K线API
        return f'http://push2.eastmoney.com/api/qt/stock/klt?secid={code}&fields1=&fields2=&klt=1&fqt=1&beg={start_date}&end={end_date}'
```

### 同花顺实时行情爬虫

```python
class TonghuashunRealtimeCrawler(BaseCrawler):
    """同花顺实时行情爬虫"""

    async def crawl(self, codes: List[str]) -> List[Dict]:
        """爬取实时行情"""

        playwright, browser, context, page = await self._create_playwright_context()

        results = []

        for code in codes:
            try:
                # 同花顺行情URL
                url = f'http://q.10jqka.com.cn/{code}'

                await page.goto(url, wait_until='networkidle')

                # 等待价格加载
                await page.wait_for_selector('.price', timeout=5000)

                # 提取实时数据
                data = await page.evaluate('''() => {
                    return {
                        'price': document.querySelector('.price')?.textContent,
                        'change': document.querySelector('.change')?.textContent,
                        'volume': document.querySelector('.volume')?.textContent,
                        ...
                    };
                }''')

                results.append({
                    'code': code,
                    'price': data['price'],
                    'change': data['change'],
                    'crawl_time': datetime.now(),
                    'crawl_status': 'success'
                })

            except Exception as e:
                self.logger.error(f'爬取 {code} 失败: {e}')

        await browser.close()

        return results
```

---

## 🔄 爬虫调度系统

### 调度器

```python
class CrawlerScheduler:
    """爬虫调度器"""

    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.logger = logging.getLogger('crawler.scheduler')

    async def schedule_crawlers(self):
        """调度爬虫任务"""

        # 查询活跃爬虫
        crawlers = self.db_conn.execute('''
            SELECT crawler_name, schedule, priority, is_active
            FROM crawler_registry
            WHERE is_active = true
            ORDER BY priority DESC
        ''').fetchall()

        for crawler_name, schedule, priority, is_active in crawlers:
            # 根据调度策略执行
            if schedule == 'realtime':
                asyncio.create_task(self._run_realtime(crawler_name))
            elif schedule == 'daily':
                asyncio.create_task(self._run_daily(crawler_name))
            elif schedule == 'hourly':
                asyncio.create_task(self._run_hourly(crawler_name))

    async def _run_realtime(self, crawler_name: str):
        """实时爬取"""
        while True:
            try:
                # 获取爬虫实例
                crawler = self._get_crawler_instance(crawler_name)

                # 执行爬取
                await crawler.run_with_retry()

                # 实时爬取间隔（避免被封）
                await asyncio.sleep(60)  # 1分钟

            except Exception as e:
                self.logger.error(f'实时爬取失败: {e}')
                await asyncio.sleep(300)  # 出错后等待5分钟

    def _get_crawler_instance(self, crawler_name: str) -> BaseCrawler:
        """获取爬虫实例"""
        if crawler_name == 'eastmoney_kline':
            return EastMoneyKlineCrawler(crawler_name, self.db_conn)
        elif crawler_name == 'eastmoney_capital':
            return EastMoneyCapitalCrawler(crawler_name, self.db_conn)
        elif crawler_name == '10jqka_realtime':
            return TonghuashunRealtimeCrawler(crawler_name, self.db_conn)
        else:
            raise ValueError(f'未知的爬虫: {crawler_name}')
```

---

## 🛡️ 反爬虫应对策略

### 1. 请求频率控制

```python
class RateLimiter:
    """频率限制器"""

    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """获取请求许可"""
        async with self.lock:
            now = time.time()

            # 清除1分钟前的记录
            self.requests = [r for r in self.requests if now - r < 60]

            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                sleep_time = 60 - (now - self.requests[0])
                await asyncio.sleep(sleep_time)

            self.requests.append(now)
```

### 2. User-Agent轮换

```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...',
    ...
]

class UserAgentRotator:
    """User-Agent轮换"""

    def __init__(self):
        self.user_agents = USER_AGENTS
        self.current_index = 0

    def get_next(self) -> str:
        """获取下一个User-Agent"""
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua
```

### 3. 代理IP池

```python
class ProxyPool:
    """代理IP池"""

    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.failed = {}  # 记录失败的代理

    async def get_proxy(self) -> Optional[str]:
        """获取可用代理"""
        for proxy in self.proxies:
            if proxy not in self.failed or time.time() - self.failed[proxy] > 3600:
                return proxy
        return None

    def mark_failed(self, proxy: str):
        """标记失败代理"""
        self.failed[proxy] = time.time()
```

---

## 📊 数据质量保证

### 数据验证

```python
class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_kline(data: Dict) -> Dict:
        """验证K线数据"""

        issues = []

        # 检查必填字段
        required_fields = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            if field not in data or data[field] is None:
                issues.append(f'缺失字段: {field}')

        # 检查逻辑关系
        if all(k in data for k in ['high', 'low', 'open', 'close']):
            if data['high'] < data['low']:
                issues.append('最高价 < 最低价')

            if data['high'] < max(data['open'], data['close']):
                issues.append('最高价 < 开盘价/收盘价')

            if data['low'] > min(data['open'], data['close']):
                issues.append('最低价 > 开盘价/收盘价')

        # 检查异常值
        if 'pct_change' in data:
            if abs(data['pct_change']) > 20:  # A股涨跌停限制
                issues.append(f'涨跌幅异常: {data["pct_change"]}%')

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'data_quality': 'excellent' if len(issues) == 0 else 'suspicious'
        }
```

---

## 📋 实现清单

### 阶段1：数据库创建（1小时）
- [ ] 创建爬虫相关表（5个表）
- [ ] 初始化爬虫注册表
- [ ] 创建索引

### 阶段2：基类实现（2小时）
- [ ] BaseCrawler基类
- [ ] 数据验证器
- [ ] 日志记录器

### 阶段3：东方财富爬虫（3小时）
- [ ] K线爬虫
- [ ] 资金流爬虫
- [ ] 龙虎榜爬虫

### 阶段4：同花顺爬虫（2小时）
- [ ] 实时行情爬虫
- [ ] 技术指标爬虫

### 阶段5：调度系统（2小时）
- [ ] 调度器
- [ ] 频率限制器
- [ ] 错误处理

### 阶段6：反爬虫（2小时）
- [ ] User-Agent轮换
- [ ] 代理IP池
- [ ] 请求延迟

**总计：约12小时**

---

## 🎯 架构优势

### ✅ 以爬虫为中心

| 特性 | API方案 | 爬虫方案 |
|------|---------|---------|
| **数据完整性** | 受API限制 | 完整（所有网页数据） |
| **时效性** | 依赖API更新 | 实时爬取 |
| **成本** | 部分API收费 | 免费 |
| **稳定性** | API可能变动 | 网页变动但可适应 |
| **数据深度** | API提供的基础数据 | 可爬取深度数据 |

### 🚀 聚焦核心数据源

1. **东方财富**（主力）
   - K线数据（日/分钟）
   - 资金流向（实时）
   - 财务数据
   - 股东信息

2. **同花顺**（补充）
   - 实时行情
   - 技术指标
   - F10资料

3. **其他**（补充）
   - Yahoo Finance：海外市场
   - AKShare：国内API补充

---

**设计人**: AI Agent
**版本**: v3.0（爬虫优化版）
**更新时间**: 2026-03-13

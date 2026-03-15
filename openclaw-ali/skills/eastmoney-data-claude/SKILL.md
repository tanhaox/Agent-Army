---
name: eastmoney-data-claude
description: A股数据补充 - 资金流向、龙虎榜、涨跌停、板块、北向资金等核心数据
---

# A股数据补充 Skill 🇨🇳

## 功能说明

这个Skill帮助你从东方财富、同花顺获取A股市场核心数据，补充雅虎财经的数据缺口。

### 核心数据类型

#### 1. 资金流向数据 ⭐⭐⭐⭐⭐
- 主力资金净流入/流出
- 超大单、大单、中单、小单资金流向
- 资金净流入占比
- 个股资金流向排行

#### 2. 涨跌停数据 ⭐⭐⭐⭐⭐
- 当日涨停家数、跌停家数
- 封板资金、炸板率
- 涨停股票列表
- 按板块分类统计

#### 3. 龙虎榜数据 ⭐⭐⭐⭐
- 上榜股票及原因
- 机构席位买卖情况
- 游资席位动向
- 北向资金席位买卖

#### 4. 板块数据 ⭐⭐⭐⭐
- 行业板块涨跌幅排行
- 概念板块涨跌幅排行
- 板块资金流向
- 板块内个股表现

#### 5. 北向资金数据 ⭐⭐⭐⭐
- 沪股通、深股通净流入
- 个股北向持股比例
- 北向持股变化

#### 6. 融资融券数据 ⭐⭐⭐⭐
- 融资余额、融券余额
- 融资买入额、融券卖出量
- 融资融券余额变化

#### 7. 股东数据 ⭐⭐⭐
- 股东户数变化
- 户均持股
- 大股东增减持

#### 8. 限售股解禁 ⭐⭐⭐
- 解禁日期、数量
- 解禁市值
- 占总股本比例

## 数据存储

所有数据存储在DuckDB数据库：`/root/.openclaw/workspace/data/a_market.duckdb`

### 表结构

```sql
-- 资金流向
CREATE TABLE stock_money_flow (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    main_net_inflow DOUBLE,        -- 主力净流入
    super_large_net DOUBLE,         -- 超大单净流入
    large_net DOUBLE,              -- 大单净流入
    medium_net DOUBLE,             -- 中单净流入
    small_net DOUBLE,              -- 小单净流入
    main_net_inflow_ratio DOUBLE,  -- 主力净流入占比
    PRIMARY KEY (date, code)
);

-- 涨跌停
CREATE TABLE stock_limit_stats (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    limit_type VARCHAR(10),        -- '涨停' / '跌停'
    limit_time TIME,               -- 涨停时间
    seal_amount DOUBLE,            -- 封板资金
    break_times INT,               -- 炸板次数
    PRIMARY KEY (date, code, limit_type)
);

-- 龙虎榜
CREATE TABLE dragon_tiger_list (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    reason VARCHAR(100),           -- 上榜原因
    buy_amount DOUBLE,             -- 买入总额
    sell_amount DOUBLE,            -- 卖出总额
    net_buy DOUBLE,                -- 净买入
    institution_net DOUBLE,        -- 机构净买卖
    PRIMARY KEY (date, code)
);

-- 板块数据
CREATE TABLE sector_performance (
    date DATE,
    sector_name VARCHAR(50),
    sector_type VARCHAR(20),       -- '行业' / '概念'
    change_pct DOUBLE,             -- 涨跌幅
    money_flow DOUBLE,             -- 资金净流入
    leading_stock VARCHAR(10),     -- 龙头股票
    PRIMARY KEY (date, sector_name, sector_type)
);

-- 北向资金
CREATE TABLE north_money_flow (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    hold_ratio DOUBLE,             -- 持股比例
    hold_amount DOUBLE,            -- 持股金额
    hold_change DOUBLE,            -- 持股变化
    PRIMARY KEY (date, code)
);

-- 融资融券
CREATE TABLE margin_trading (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    margin_balance DOUBLE,         -- 融资余额
    short_balance DOUBLE,          -- 融券余额
    margin_buy DOUBLE,             -- 融资买入额
    short_sell DOUBLE,             -- 融券卖出量
    PRIMARY KEY (date, code)
);
```

## 使用方法

### 1. 获取个股资金流向
```
同步伊利股份的资金流向数据
```

### 2. 获取今日涨跌停统计
```
获取今日涨跌停数据
```

### 3. 获取龙虎榜数据
```
获取最新龙虎榜
```

### 4. 获取板块排行
```
获取行业板块涨跌幅排行
```

### 5. 获取北向资金流向
```
获取北向资金今日流向
```

### 6. 批量更新
```
更新所有A股补充数据
```

## 数据查询

### 查询示例
```python
# 查询某股票最近5天资金流向
query_a_market("""
    SELECT * FROM stock_money_flow
    WHERE code = '600887'
    ORDER BY date DESC
    LIMIT 5
""")
```

## 更新频率

- **实时数据**: 资金流向、涨跌停（盘中实时）
- **日终数据**: 龙虎榜、板块、北向资金（每日收盘后）
- **建议更新时间**: 每日 15:30 之后

## 技术说明

- **数据源**: 东方财富 (eastmoney.com)、同花顺 (10jqka.com.cn)
- **数据格式**: JSON API
- **存储方式**: DuckDB
- **更新方式**: 增量更新（只获取新数据）

## 注意事项

1. 东方财富API可能有限流，建议合理控制请求频率
2. 某些数据在盘中不可用，需等到收盘后
3. 数据保留时间：建议保留1年以上历史数据
4. 建议与雅虎财经数据配合使用

## 版本

- **当前版本**: 1.0.0
- **发布日期**: 2025-03-13
- **作者**: Claude AI Assistant

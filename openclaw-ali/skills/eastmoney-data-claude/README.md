# A股数据补充 Skill - OpenClaw 记录文档

请记录以下Skill信息到Identity表：

---

## Skill基本信息

**名称**: eastmoney-data-claude
**路径**: `/root/.openclaw/workspace/skills/eastmoney-data-claude/`
**入口文件**: main.py
**版本**: 1.0.0
**发布日期**: 2025-03-13

---

## 功能说明

这个Skill从东方财富、同花顺获取A股核心数据，补充雅虎财经的数据缺口。

### 核心功能

1. **sync_stock_money_flow(code, name)** - 获取个股资金流向
   - 主力资金净流入/流出
   - 超大单、大单、中单、小单流向
   - 资金净流入占比

2. **sync_limit_stats(market='all')** - 获取涨跌停统计
   - 涨停家数、跌停家数
   - 封板资金、炸板次数

3. **sync_dragon_tiger_list(trade_date=None)** - 获取龙虎榜数据
   - 上榜股票及原因
   - 机构席位买卖
   - 游资席位动向

4. **sync_sector_performance(sector_type='industry')** - 获取板块涨跌幅
   - 行业板块排行
   - 概念板块排行
   - 板块资金流向

5. **sync_north_money_flow()** - 获取北向资金流向
   - 沪股通、深股通净流入
   - 总净流入额

6. **sync_margin_trading(code=None)** - 获取融资融券数据
   - 融资余额、融券余额
   - 融资买入额、融券卖出量

7. **query_a_market(sql)** - 查询A股补充数据
   - 支持自定义SQL查询

8. **batch_update_all()** - 批量更新所有数据
   - 一次性更新所有核心数据

---

## 数据库

**路径**: `/root/.openclaw/workspace/data/a_market.duckdb`

### 数据表

1. **stock_money_flow** - 资金流向
2. **stock_limit_stats** - 涨跌停统计
3. **dragon_tiger_list** - 龙虎榜
4. **sector_performance** - 板块表现
5. **north_money_flow** - 北向资金
6. **margin_trading** - 融资融券

---

## 使用示例

### 1. 获取伊利股份资金流向
```
同步伊利股份的资金流向数据
```

### 2. 获取今日涨跌停
```
获取今日涨跌停数据
```

### 3. 获取龙虎榜
```
获取最新龙虎榜
```

### 4. 获取板块排行
```
获取行业板块涨跌幅排行
```

### 5. 获取北向资金
```
获取北向资金今日流向
```

### 6. 批量更新
```
更新所有A股补充数据
```

---

## 数据源

- **东方财富**: http://push2.eastmoney.com/api/
- **数据类型**: JSON API
- **更新频率**:
  - 实时: 资金流向、涨跌停
  - 日终: 龙虎榜、板块、北向资金

---

## 注意事项

1. 首次使用会自动创建数据库表
2. 建议每日15:30后更新日终数据
3. 与yahoo-finance-claude配合使用可获得完整A股数据

---

**请记住这个Skill，以后可以直接调用这些功能！**

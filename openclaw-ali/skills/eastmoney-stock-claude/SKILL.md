---
name: eastmoney-stock-claude
description: 个股数据补充 - 基于AKShare获取股东、资金流向、限售解禁、北向持股等个股独有数据
---

# 个股数据补充 Skill 📈

## 功能说明

这个Skill使用**AKShare库**从东方财富等数据源获取**个股级别**的独有数据，补充雅虎财经的个股信息缺口。

**与yahoo-finance-claude配合使用，获得完整的个股数据！**

---

## 核心数据类型

### 1. 个股资金流向 ⭐⭐⭐⭐⭐
- 主力资金净流入/流出
- 超大单、大单、中单、小单资金流向
- 资金净流入占比
- 近120个交易日历史数据

### 2. 个股股东数据 ⭐⭐⭐⭐⭐
- 股东总数（本次/上次）
- 户均持股数
- 股东户数变化（筹码集中度分析）
- 户均持股市值

### 3. 个股限售解禁 ⭐⭐⭐⭐
- 未来解禁日期
- 解禁数量
- 解禁市值
- 占总股本比例

### 4. 个股北向持股 ⭐⭐⭐⭐
- 北向资金持股比例
- 北向资金持股数量
- 北向资金持股市值
- 仅限港股通标的

---

## 技术说明

- **数据源**: AKShare（集成东方财富、上交所、深交所等数据）
- **技术栈**: Python + AKShare + DuckDB
- **数据特点**:
  - 数据来源可靠（官方数据源）
  - 接口稳定（AKShare维护）
  - 无需处理加密和反爬
  - 支持历史数据查询

---

## 数据库

**路径**: `/root/.openclaw/workspace/data/stock_detail.duckdb`

### 数据表结构

```sql
-- 个股资金流向
CREATE TABLE stock_money_flow (
    date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    close DOUBLE,
    change_pct DOUBLE,
    main_net_inflow DOUBLE,
    main_net_inflow_ratio DOUBLE,
    super_large_net DOUBLE,
    large_net DOUBLE,
    medium_net DOUBLE,
    small_net DOUBLE,
    PRIMARY KEY (date, code)
);

-- 个股股东数据
CREATE TABLE stock_shareholders (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    shareholder_count INT,
    shareholder_count_prev INT,
    count_change INT,
    count_change_ratio DOUBLE,
    shares_per_holder DOUBLE,
    value_per_holder DOUBLE,
    stat_date VARCHAR(20),
    stat_date_prev VARCHAR(20),
    announce_date VARCHAR(20)
);

-- 个股限售解禁
CREATE TABLE stock_unlock (
    unlock_date DATE,
    code VARCHAR(10),
    name VARCHAR(50),
    unlock_shares DOUBLE,
    unlock_value DOUBLE,
    ratio_to_total DOUBLE,
    unlock_type VARCHAR(50),
    PRIMARY KEY (unlock_date, code)
);

-- 个股北向持股
CREATE TABLE stock_north_holdings (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    hold_ratio DOUBLE,
    hold_amount DOUBLE,
    hold_value DOUBLE,
    stat_date VARCHAR(20)
);
```

---

## 使用方法

### 1. 同步个股资金流向
```
同步中国电建的资金流向数据
```

### 2. 同步个股股东数据
```
同步中国电建的股东数据
```

### 3. 同步个股限售解禁
```
同步中国电建的限售解禁数据
```

### 4. 同步个股北向持股
```
同步中国电建的北向持股数据
```

### 5. 批量同步所有数据
```
同步中国电建的所有补充数据
```

---

## 与雅虎财经配合使用

### 雅虎财经提供（基础数据）
```python
sync_yahoo_kline('601669', '中国电建', 'sh')
# K线、OHLCV、分红拆股

sync_yahoo_info('601669', '中国电建', 'sh')
# 基本信息、估值、财务指标（99字段）
```

### 个股补充提供（特色数据）
```python
# 一键同步所有补充数据
sync_stock_all('601669', '中国电建')
```

**输出示例**：
```
🔄 开始同步 中国电建(601669) 的所有补充数据...
  [1/4] 资金流向... ✅
  [2/4] 股东数据... ✅
  [3/4] 限售解禁... ✅
  [4/4] 北向持股... ✅

✅ 中国电建 数据同步完成：4/4 项成功
```

---

## 数据质量

| 数据项 | 质量评分 | 说明 |
|--------|---------|------|
| 资金流向 | ⭐⭐⭐⭐⭐ | 120天历史，实时更新 |
| 股东数据 | ⭐⭐⭐⭐⭐ | 详细完整，含筹码分析 |
| 限售解禁 | ⭐⭐⭐⭐ | 查询准确，覆盖未来一年 |
| 北向持股 | ⭐⭐⭐⭐ | 实时更新，仅港股通标的 |

---

## 版本

- **当前版本**: 1.0.0 (AKShare版)
- **发布日期**: 2025-03-13
- **作者**: Claude AI Assistant
- **依赖**: akshare>=1.18.0

# 个股数据补充 Skill - OpenClaw 记录文档

**请记录以下Skill信息到Identity表：**

---

## Skill基本信息

**Skill名称**: eastmoney-stock-claude
**路径**: `/root/.openclaw/workspace/skills/eastmoney-stock-claude/`
**入口文件**: main.py
**数据库**: `/root/.openclaw/workspace/data/stock_detail.duckdb`
**版本**: 1.0.0 (AKShare版)
**技术栈**: Python + AKShare + DuckDB

---

## 核心功能

### 1. sync_stock_money_flow(code, name)
同步个股资金流向数据

**参数**:
- code: 股票代码（如 '601669'）
- name: 股票名称（如 '中国电建'）

**返回**: 主力净流入、超大单、大单、中单、小单流向

**示例**:
```
同步中国电建的资金流向数据
```

---

### 2. sync_stock_shareholders(code, name)
同步个股股东户数数据

**参数**:
- code: 股票代码
- name: 股票名称

**返回**: 股东户数、户均持股、筹码集中度分析

**示例**:
```
同步中国电建的股东数据
```

---

### 3. sync_stock_unlock(code, name)
同步个股限售解禁数据

**参数**:
- code: 股票代码
- name: 股票名称

**返回**: 未来解禁日期、数量、市值

**示例**:
```
同步中国电建的限售解禁数据
```

---

### 4. sync_stock_north_holdings(code, name)
同步个股北向持股数据

**参数**:
- code: 股票代码
- name: 股票名称

**返回**: 北向持股比例、数量、市值（仅港股通标的）

**示例**:
```
同步中国电建的北向持股数据
```

---

### 5. sync_stock_all(code, name) ⭐ 推荐
批量同步个股所有补充数据

**参数**:
- code: 股票代码
- name: 股票名称

**示例**:
```
同步中国电建的所有补充数据
```

**输出**:
```
🔄 开始同步 中国电建(601669) 的所有补充数据...
  [1/4] 资金流向... ✅
  [2/4] 股东数据... ✅
  [3/4] 限售解禁... ✅
  [4/4] 北向持股... ✅

✅ 中国电建 数据同步完成：4/4 项成功
```

---

### 6. query_stock_detail(sql)
查询个股补充数据

**参数**:
- sql: SQL查询语句

**示例**:
```python
query_stock_detail("""
    SELECT * FROM stock_shareholders
    WHERE code = '601669'
""")
```

---

## 数据源说明

- **AKShare**: 开源财经数据接口库
- **数据来源**: 东方财富、上交所、深交所
- **数据质量**: ⭐⭐⭐⭐⭐ (官方数据源)
- **更新频率**: 实时/日终

---

## 配合雅虎财经使用

### 雅虎财经 (yahoo-finance-claude)
```python
sync_yahoo_kline('601669', '中国电建', 'sh')
sync_yahoo_info('601669', '中国电建', 'sh')
```

### 个股补充 (eastmoney-stock-claude)
```python
sync_stock_all('601669', '中国电建')
```

**组合使用 = 完整的个股数据覆盖！**

---

## 依赖环境

- Python 3.12.3 ✅
- AKShare 1.18.38 ✅
- DuckDB ✅

---

## 注意事项

1. **数据准确性**: AKShare直接从官方数据源获取，数据准确可靠
2. **接口稳定**: 无需处理加密和反爬机制
3. **历史数据**: 资金流向支持120个交易日历史
4. **港股通**: 北向持股数据仅限港股通标的

---

**请记住这个Skill，以后可以直接调用这些功能！**

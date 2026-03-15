# 东方财富板块数据网页爬虫 Skill

通过网页抓取获取东方财富板块数据，绕过API限制。

## 功能特点

- ✅ **板块资金流向**：获取50个行业板块的资金流向数据
- ✅ **涨跌幅排行**：实时板块涨跌幅统计
- ✅ **主力资金分析**：超大单、大单、中单、小单资金流向
- ✅ **无需API**：直接爬取网页，完全免费
- ✅ **反爬免疫**：使用WebReader工具绕过反爬机制

## 数据来源

- 网址：https://data.eastmoney.com/bkzj/hy.html
- 更新频率：实时
- 数据范围：50个行业板块

## 使用方法

### 1. 初始化数据库

```python
from main import init_db
init_db()
```

### 2. 同步板块资金流向

```python
from main import sync_sector_fund_flow_from_html

# 首先从网页获取HTML内容（使用WebReader）
html_content = get_html_from_webreader()  # 需要实现

# 然后解析并保存
result = sync_sector_fund_flow_from_html(html_content)
```

### 3. 查询板块数据

```python
from main import get_sector_fund_flow, query_sector_data

# 获取所有板块资金流向
data = get_sector_fund_flow()

# 查询指定板块
construction = get_sector_fund_flow(sector_name="煤炭开采")

# 查询指定日期
today = get_sector_fund_flow(date="2025-03-13")
```

## 数据字段

### sector_fund_flow 表

| 字段 | 类型 | 说明 |
|------|------|------|
| date | DATE | 日期 |
| rank | INT | 排名 |
| sector_name | VARCHAR | 板块名称 |
| change_pct | DOUBLE | 涨跌幅(%) |
| main_net_inflow | DOUBLE | 主力净流入(元) |
| main_net_inflow_ratio | DOUBLE | 主力净流入占比(%) |

## 工作流程

```
WebReader获取网页
    ↓
提取表格数据
    ↓
解析为结构化数据
    ↓
存储到DuckDB
    ↓
OpenClaw查询使用
```

## 注意事项

1. **数据来源**：网页爬虫，依赖网页结构稳定性
2. **更新频率**：建议每日收盘后更新一次
3. **数据量**：50个行业板块 × 每日1条记录
4. **存储空间**：约1MB/年

## 下一步优化

- [ ] 添加概念板块数据
- [ ] 添加地域板块数据
- [ ] 添加板块成分股爬取
- [ ] 添加历史数据回溯功能

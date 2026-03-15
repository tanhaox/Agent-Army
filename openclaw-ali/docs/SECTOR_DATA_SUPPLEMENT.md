# 板块数据补充 - 缺失数据分析

## 📋 缺失数据清单

### 1. 板块指数数据 ⭐⭐⭐⭐⭐

**需求**: 建筑工程板块指数涨跌幅、成交量、技术指标

**数据源**: AKShare
**接口**: `stock_board_industry_spot_em()`

**实现方案**:
```python
def sync_sector_index(sector_name: str = '建筑工程') -> dict:
    """
    同步行业板块指数数据

    Returns:
        板块名称、最新价、涨跌幅、成交量、成交额、领涨股、涨跌数
    """
    df = ak.stock_board_industry_spot_em()
    sector = df[df['板块名称'] == sector_name]
    return {
        'sector_name': sector['板块名称'],
        'latest_price': sector['最新价'],
        'change_pct': sector['涨跌幅'],
        'volume': sector['成交量'],
        'amount': sector['成交额'],
        'leader_stock': sector['领涨股'],
        'up_count': sector['上涨公司数'],
        'down_count': sector['下跌公司数']
    }
```

---

### 2. 板块成分股数据 ⭐⭐⭐⭐⭐

**需求**: 建筑工程板块成分股列表、权重、涨跌幅

**数据源**: AKShare
**接口**: `stock_board_industry_cons_em(symbol='建筑工程')`

**实现方案**:
```python
def sync_sector_constituents(sector_name: str = '建筑工程') -> dict:
    """
    同步板块成分股数据

    Returns:
        成分股代码、名称、涨跌幅、最新价、成交量、成交额、总市值、流通市值
    """
    df = ak.stock_board_industry_cons_em(symbol=sector_name)
    return {
        'stocks': df.to_dict('records'),
        'count': len(df),
        'top_gainer': df.nlargest(1, '涨跌幅').iloc[0].to_dict(),
        'top_loser': df.nsmallest(1, '涨跌幅').iloc[0].to_dict()
    }
```

---

### 3. 板块资金流向数据 ⭐⭐⭐⭐⭐

**需求**: 建筑工程板块资金流向（流入、流出、净流入）

**数据源**: AKShare
**接口**: `stock_sector_fund_flow_rank()`

**实现方案**:
```python
def sync_sector_fund_flow(sector_name: str = '建筑工程') -> dict:
    """
    同步板块资金流向数据

    Returns:
        主力净流入、超大单、大单、中单、小单流向
    """
    # 先获取板块列表找到对应板块
    df_all = ak.stock_sector_fund_flow_rank(symbol="行业板块", indicator="今日")
    sector = df_all[df_all['名称'] == sector_name]
    return {
        'sector_name': sector_name,
        'main_net_inflow': sector['净流入'],
        'main_net_inflow_ratio': sector['净流入率'],
        'super_large_net': sector['超大单净流入'],
        'large_net': sector['大单净流入'],
        'medium_net': sector['中单净流入'],
        'small_net': sector['小单净流入']
    }
```

---

### 4. 板块龙头股数据 ⭐⭐⭐⭐

**需求**: 建筑工程板块龙头股（涨停股、涨跌幅）

**数据源**: AKShare
**接口**: `stock_board_industry_cons_em()` + 数据处理

**实现方案**:
```python
def sync_sector_leaders(sector_name: str = '建筑工程') -> dict:
    """
    同步板块龙头股数据

    Returns:
        涨幅榜前5、跌幅榜前5、成交额前5、涨停股票
    """
    df = ak.stock_board_industry_cons_em(symbol=sector_name)
    return {
        'top_gainers': df.nlargest(5, '涨跌幅').to_dict('records'),
        'top_losers': df.nsmallest(5, '涨跌幅').to_dict('records'),
        'top_volume': df.nlargest(5, '成交量').to_dict('records'),
        'limit_up_stocks': df[df['涨跌幅'] >= 9.9].to_dict('records')
    }
```

---

## 🎯 集成方案

### 方案A: 扩展 eastmoney-data-claude

在现有的 `eastmoney-data-claude`（全市场数据）中添加板块功能：

**新增函数**:
```python
# main.py 新增
__all__ = [
    # ... 现有函数
    'sync_sector_index',           # 板块指数
    'sync_sector_constituents',     # 板块成分股
    'sync_sector_fund_flow',        # 板块资金流向
    'sync_sector_leaders',          # 板块龙头股
    'sync_sector_all'               # 一键同步板块数据
]
```

**数据库表**:
```sql
CREATE TABLE sector_index (
    date DATE,
    sector_name VARCHAR(50),
    latest_price DOUBLE,
    change_pct DOUBLE,
    volume DOUBLE,
    amount DOUBLE,
    leader_stock VARCHAR(10),
    up_count INT,
    down_count INT,
    PRIMARY KEY (date, sector_name)
);

CREATE TABLE sector_constituents (
    date DATE,
    sector_name VARCHAR(50),
    stock_code VARCHAR(10),
    stock_name VARCHAR(50),
    change_pct DOUBLE,
    close_price DOUBLE,
    volume DOUBLE,
    amount DOUBLE,
    market_cap DOUBLE,
    PRIMARY KEY (date, sector_name, stock_code)
);
```

---

### 方案B: 创建独立的 sector-data-claude

创建专门的板块数据Skill：

**优势**:
- 专注板块数据
- 不影响现有Skill
- 可以扩展更多板块分析功能

---

## 📊 数据质量评估

| 数据项 | AKShare支持 | 数据质量 | 更新频率 |
|--------|-------------|---------|---------|
| 板块指数 | ✅ | ⭐⭐⭐⭐⭐ | 实时 |
| 成分股 | ✅ | ⭐⭐⭐⭐⭐ | 实时 |
| 资金流向 | ✅ | ⭐⭐⭐⭐⭐ | 日终 |
| 龙头股 | ✅（计算） | ⭐⭐⭐⭐ | 实时 |

---

## 💡 建议

**推荐方案A**: 扩展 `eastmoney-data-claude`

**理由**:
1. 板块数据属于"全市场数据"范畴
2. 避免创建太多Skill
3. 统一管理全市场相关数据

**实施步骤**:
1. 在 `eastmoney-data-claude/tool.py` 添加板块函数
2. 在 `eastmoney-data-claude/main.py` 暴露新接口
3. 添加数据库表
4. 重新部署

**需要我立即实现吗？**

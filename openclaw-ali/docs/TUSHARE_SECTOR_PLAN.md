# 板块数据补充方案 - Tushare实施计划

## 📋 数据映射关系

### 东方财富 → Tushare

| 东方财富数据 | Tushare接口 | 说明 |
|------------|------------|------|
| 行业板块列表 | `index_classify(level='L1', src='SW')` | 申万一级行业 |
| 建筑工程成分股 | `index_member(index_code='801010')` | SW2021建筑 |
| 板块指数行情 | `index_daily(ts_code='801010.SH')` | 指数日线 |
| 板块资金流向 | `moneyflow()` | 个股资金流 |

## 🔧 实施方案

### Step 1: 获取Tushare Token

1. 注册：https://tushare.pro/register
2. 登录后获取Token（免费版每日5000次调用）
3. 免费版足够采集所有板块数据

### Step 2: 安装依赖

```bash
pip install tushare --break-system-packages
```

### Step 3: 创建板块数据Skill

**项目结构**：
```
tushare-sector-claude/
├── _meta.json
├── .clawhub/
│   └── origin.json
├── SKILL.md
├── main.py
└── tool.py
```

### Step 4: 核心函数设计

```python
import tushare as ts

def init_db():
    """初始化数据库表"""
    pass

def get_sector_list():
    """获取所有行业板块"""
    pro = ts.pro_api('your_token')
    df = pro.index_classify(level='L1', src='SW')
    return df

def get_sector_constituents(sector_code):
    """获取板块成分股"""
    pro = ts.pro_api('your_token')
    df = pro.index_member(index_code=sector_code)
    return df

def get_sector_daily(sector_code, start_date, end_date):
    """获取板块日线行情"""
    pro = ts.pro_api('your_token')
    df = pro.index_daily(ts_code=sector_code,
                        start_date=start_date,
                        end_date=end_date)
    return df

def sync_sector_all():
    """一键同步所有板块数据"""
    sectors = get_sector_list()
    for sector in sectors['index_code']:
        # 采集成分股
        constituents = get_sector_constituents(sector)
        # 采集行情数据
        daily = get_sector_daily(sector, '20240101', '')
    return {"status": "success"}
```

### Step 5: 数据库表设计

```sql
-- 板块列表
CREATE TABLE sector_list (
    index_code VARCHAR(10) PRIMARY KEY,
    index_name VARCHAR(50),
    market VARCHAR(10),
    publisher VARCHAR(50),
    updated_at TIMESTAMP
);

-- 板块成分股
CREATE TABLE sector_constituents (
    index_code VARCHAR(10),
    con_code VARCHAR(10),
    con_name VARCHAR(50),
    in_date DATE,
    out_date DATE,
    is_new INT,
    PRIMARY KEY (index_code, con_code)
);

-- 板块行情
CREATE TABLE sector_daily (
    ts_code VARCHAR(10),
    trade_date DATE,
    close DOUBLE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    vol DOUBLE,
    amount DOUBLE,
    PRIMARY KEY (ts_code, trade_date)
);
```

## 📊 建筑工程板块映射

| 东方财富 | Tushare | 说明 |
|---------|---------|------|
| 建筑工程 | 801010.SH | 申万一级行业-建筑装饰 |
| 建筑材料 | 801020.SH | - |
| 基础建设 | 801170.SH | - |

## ⚡ 关键优势

1. **稳定性**：官方API，不会突然失效
2. **免费额度**：每日5000次足够
3. **完整数据**：板块、成分股、行情全覆盖
4. **文档完善**：https://tushare.pro/document/2

## ❓ 下一步

**需要您确认**：
1. 是否注册Tushare账号？
2. 是否开始开发 `tushare-sector-claude` Skill？
3. Token配置方式：环境变量 / 配置文件？

**预计开发时间**：30分钟
**预计测试时间**：10分钟

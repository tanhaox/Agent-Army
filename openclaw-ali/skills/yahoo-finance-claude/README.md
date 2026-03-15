# 雅虎财经 Skill - OpenClaw

## 📈 功能概述

这个Skill为OpenClaw添加了雅虎财经A股数据同步功能，可以获取：
- K线数据（开盘价、最高价、最低价、收盘价、成交量等）
- 个股信息（市值、市盈率、财务数据、分红数据等99个字段）

## 📁 文件结构

```
skills/yahoo-finance/
├── SKILL.md           # Skill定义文件（OpenClaw读取）
├── tool.py            # 工具包装器（可独立运行）
└── README.md          # 本文档
```

## 🚀 安装步骤

### 步骤1：复制Skill到OpenClaw工作目录

```bash
# 复制整个skill目录
cp -r openclaw-ali/skills/yahoo-finance ~/.openclaw/skills/

# 或者复制到特定agent的工作空间
cp -r openclaw-ali/skills/yahoo-finance ~/.openclaw/workspace/skills/
```

### 步骤2：刷新OpenClaw

在OpenClaw中输入：
```
refresh skills
```

或者重启Gateway。

### 步骤3：验证安装

在OpenClaw中询问：
```
列出可用的skills
```

应该能看到 `yahoo_finance` skill。

## 💡 使用方法

### 在OpenClaw中使用

#### 同步单只股票
```
同步贵州茅台的雅虎财经数据
```

```
获取600519.SS的K线和个股信息
```

#### 同步多只股票
```
同步以下股票：贵州茅台、平安银行、比亚迪
```

#### 查询数据
```
查询股息率超过3%的股票
```

```
显示市盈率低于20的股票
```

```
查询伊利股份的最新市值和市盈率
```

### 命令行使用

```bash
# 同步K线数据
cd ~/.openclaw/skills/yahoo-finance
python tool.py sync_kline 600519 贵州茅台 SS 1mo

# 同步个股信息
python tool.py sync_info 600519 贵州茅台 SS

# 完整版同步
python tool.py sync_complete

# 查询数据
python tool.py query "SELECT code, name, market_cap FROM stock_info_unified"
```

## 📊 数据库结构

### stock_kline_unified（K线表）
- 31个字段
- 包含：日期、开盘价、最高价、最低价、收盘价、成交量等
- 支持多数据源（source字段区分）

### stock_info_unified（个股信息表）
- 99个字段
- 包含：基本信息、估值指标、财务数据、分红数据等
- 每只股票一条记录

## 🔧 工具函数

### sync_yahoo_kline(code, name, exchange, period='1mo')
同步K线数据

**参数**:
- `code`: 股票代码（如 "600519"）
- `name`: 股票名称（如 "贵州茅台"）
- `exchange`: 交易所（"SS" 或 "SZ"）
- `period`: 时间范围（"1mo", "3mo", "6mo", "1y"）

**返回**:
```json
{
  "status": "success",
  "message": "贵州茅台 K线数据同步完成",
  "code": "600519",
  "inserted": 15
}
```

### sync_yahoo_info(code, name, exchange)
同步个股信息

**参数**:
- `code`: 股票代码
- `name`: 股票名称
- `exchange`: 交易所

**返回**:
```json
{
  "status": "success",
  "message": "贵州茅台 个股信息同步完成",
  "code": "600519",
  "valid_fields": 20
}
```

### query_stock_data(sql)
查询数据

**参数**:
- `sql`: SQL查询语句

**返回**:
```json
{
  "status": "success",
  "columns": ["code", "name", "market_cap"],
  "rows": [...],
  "count": 5
}
```

## 📋 依赖要求

- Python 3.7+
- yfinance库（自动安装）
- duckdb库

## ⚠️ 注意事项

1. **请求频率**: 雅虎财经有频率限制，建议每次同步间隔1秒以上
2. **数据完整性**: 个股信息字段可能为空（取决于雅虎财经提供的数据）
3. **股票代码格式**:
   - 上海: `600519.SS`
   - 深圳: `000001.SZ`
4. **数据库位置**: `{baseDir}/openclaw-ali/data/stock_market_v2.db`

## 🔄 更新记录

- **2026-03-13**: 初始版本
  - K线数据同步
  - 个股信息同步（99个字段）
  - 数据查询功能
  - 100%雅虎财经字段利用率

## 📞 支持

如有问题，请查看：
- [SKILL.md](./SKILL.md) - 详细的Skill定义
- [UPGRADE_TO_COMPLETE_REPORT.md](../../UPGRADE_TO_COMPLETE_REPORT.md) - 完整版升级报告
- [sync_yahoo_complete.py](../../scripts/sync_yahoo_complete.py) - 完整版同步脚本

## 🌟 特性

✅ 100%雅虎财经字段利用率（K线7个+个股信息99个=106个字段）
✅ 支持A股上海和深圳交易所
✅ DELETE+INSERT策略，避免重复数据
✅ 自动处理日期格式转换
✅ 完整的错误处理和日志记录
✅ 可独立运行或通过OpenClaw调用

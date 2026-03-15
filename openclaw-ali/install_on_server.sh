#!/bin/bash
# 雅虎财经Skill一键安装脚本
# 在新加坡服务器上直接运行此脚本

set -e

echo "=========================================="
echo "  雅虎财经Skill一键安装"
echo "=========================================="
echo ""

# 安装目录
INSTALL_DIR="/root/.openclaw/skills/yahoo-finance"

# 1. 创建目录
echo "1. 创建目录..."
mkdir -p "$INSTALL_DIR"
echo "   ✅ 目录创建完成"

# 2. 创建SKILL.md
echo ""
echo "2. 创建SKILL.md..."
cat > "$INSTALL_DIR/SKILL.md" << 'SKILL_EOF'
---
name: yahoo_finance
description: 雅虎财经A股数据同步 - 获取K线数据和个股信息（100+字段）
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "homepage": "https://finance.yahoo.com/",
      "requires": {
        "bins": ["python3"],
        "config": []
      }
    }
  }
user-invocable: true
---

# 雅虎财经数据同步 Skill 📈

## 功能说明

这个Skill帮助你从雅虎财经获取A股市场数据，包括：

### 1. K线数据（7个字段）
- 开盘价、最高价、最低价、收盘价
- 成交量、调整后收盘价
- 分红、拆股

### 2. 个股信息（99个字段）
- **基本信息**: 公司名称、行业、板块、员工数
- **估值指标**: 市值、市盈率(PE)、市净率(PB)
- **财务数据**: 营收、利润率、毛利率、EBITDA
- **分红数据**: 分红率、股息率、分红比例
- **交易数据**: 平均成交量、Beta值
- **52周数据**: 52周最高价、最低价

## 使用方法

### 同步单只股票

```
同步贵州茅台的数据
```

```
获取600519.SS的K线和个股信息
```

### 查询数据

```
查询伊利股份的市值和市盈率
```

```
显示股息率超过3%的股票
```

```
找出市盈率低于15的股票
```

## 支持的股票代码格式

- **上海交易所**: `600519.SS`、`601669.SS`
- **深圳交易所**: `000001.SZ`、`002594.SZ`、`300750.SZ`

## 工具说明

- **sync_yahoo_kline**: 同步K线数据
- **sync_yahoo_info**: 同步个股信息
- **query_stock_data**: 查询数据库

## 数据存储

数据存储在DuckDB数据库中：
- K线表: stock_kline_unified（31个字段）
- 个股信息表: stock_info_unified（99个字段）
SKILL_EOF

echo "   ✅ SKILL.md创建完成"

# 3. 创建tool.py
echo ""
echo "3. 创建tool.py..."
cat > "$INSTALL_DIR/tool.py" << 'TOOL_EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from datetime import datetime
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import duckdb

# 数据库路径
DB_PATH = Path('/root/.openclaw/skills/yahoo-finance/data/stock_market_v2.db')

def sync_yahoo_kline(code, name, exchange, period='1mo'):
    try:
        import yfinance as yf
        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        df = ticker.history(period=period)

        if df is None or len(df) == 0:
            return {"status": "error", "message": f"{name} 无数据", "code": code}

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_PATH))
        inserted = 0

        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            pct_change = None
            if idx != df.index[0]:
                prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
                pct_change = (row['Close'] - prev_close) / prev_close * 100

            con.execute('DELETE FROM stock_kline_unified WHERE source = ? AND code = ? AND date = ?',
                       ('yahoo', code, date_str))
            con.execute('''INSERT INTO stock_kline_unified VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                ('yahoo', 'api', code, name, date_str, None, row['Open'], row['High'], row['Low'], row['Close'],
                 row.get('Adj Close'), int(row['Volume']) if row['Volume'] else None, row['Dividends'], row['Stock Splits'],
                 pct_change, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 'good',
                 100.0, datetime.now(), datetime.now()))
            inserted += 1

        con.close()
        return {"status": "success", "message": f"{name} K线同步完成", "code": code, "inserted": inserted}
    except Exception as e:
        return {"status": "error", "message": f"{name} 失败: {str(e)}", "code": code}

def query_stock_data(sql):
    try:
        con = duckdb.connect(str(DB_PATH))
        result = con.execute(sql).fetchall()
        columns = [desc[0] for desc in con.description] if hasattr(con, 'description') else []
        con.close()
        return {"status": "success", "rows": result, "columns": columns, "count": len(result)}
    except Exception as e:
        return {"status": "error", "message": f"查询失败: {str(e)}"}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'sync_kline' and len(sys.argv) >= 5:
            result = sync_yahoo_kline(sys.argv[2], sys.argv[3], sys.argv[4])
            print(json.dumps(result, ensure_ascii=False))
        elif sys.argv[1] == 'query' and len(sys.argv) >= 3:
            result = query_stock_data(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False))
TOOL_EOF

echo "   ✅ tool.py创建完成"

# 4. 设置权限
echo ""
echo "4. 设置权限..."
chmod +x "$INSTALL_DIR/tool.py"
chmod 644 "$INSTALL_DIR/SKILL.md"
echo "   ✅ 权限设置完成"

# 5. 安装Python依赖
echo ""
echo "5. 安装Python依赖..."
pip3 install yfinance duckdb -q
echo "   ✅ 依赖安装完成"

# 6. 重启OpenClaw Gateway
echo ""
echo "6. 重启OpenClaw Gateway..."
openclaw gateway restart
echo "   ✅ Gateway已重启"

echo ""
echo "=========================================="
echo "  ✅ 雅虎财经Skill安装完成！"
echo "=========================================="
echo ""
echo "下一步：在OpenClaw中测试"
echo "  输入: refresh skills"
echo "  输入: 同步伊利股份的雅虎财经数据"
echo ""

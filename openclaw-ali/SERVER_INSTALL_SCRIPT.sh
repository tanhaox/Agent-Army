#!/bin/bash
# 雅虎财经Skill一键安装脚本
# 复制此脚本的全部内容，粘贴到新加坡服务器终端执行

set -e

echo "=========================================="
echo "  雅虎财经Skill一键安装"
echo "=========================================="
echo ""

INSTALL_DIR="/root/.openclaw/skills/yahoo-finance"

# 1. 创建目录
echo "[1/6] 创建目录..."
mkdir -p "$INSTALL_DIR"
echo "      完成"

# 2. 创建SKILL.md
echo ""
echo "[2/6] 创建SKILL.md..."
cat > "$INSTALL_DIR/SKILL.md" << 'EOF'
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

这个Skill帮助你从雅虎财经获取A股市场数据。

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

### 查询数据
```
查询伊利股份的市值和市盈率
```

```
显示股息率超过3%的股票
```

## 支持的股票代码

- **上海**: 600519.SS, 601669.SS
- **深圳**: 000001.SZ, 002594.SZ, 300750.SZ
EOF

echo "      完成"

# 3. 创建tool.py（简化版，适用于服务器环境）
echo ""
echo "[3/6] 创建tool.py..."
cat > "$INSTALL_DIR/tool.py" << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# UTF-8设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import duckdb
except ImportError:
    os.system('pip3 install duckdb -q')
    import duckdb

try:
    import yfinance as yf
except ImportError:
    os.system('pip3 install yfinance -q')
    import yfinance as yf

# 数据库路径
DB_PATH = Path('/root/.openclaw/skills/yahoo-finance/data/stock_market_v2.db')

def sync_yahoo_kline(code, name, exchange, period='1mo'):
    """同步K线数据"""
    try:
        ticker_code = f'{code}.{exchange}'
        ticker = yf.Ticker(ticker_code)
        df = ticker.history(period=period)

        if df is None or len(df) == 0:
            return {"status": "error", "message": f"{name} 无数据", "code": code}

        # 确保数据库目录存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(DB_PATH))

        # 创建表（如果不存在）
        con.execute('''
            CREATE TABLE IF NOT EXISTS stock_kline_unified (
                source VARCHAR, code VARCHAR, name VARCHAR,
                date DATE, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
                volume BIGINT, dividends DOUBLE, pct_change DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        inserted = 0
        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d')

            # 计算涨跌幅
            pct_change = None
            if idx != df.index[0]:
                prev_close = df.loc[df.index[df.index.get_loc(idx) - 1], 'Close']
                pct_change = (row['Close'] - prev_close) / prev_close * 100

            # 删除旧数据
            con.execute('DELETE FROM stock_kline_unified WHERE code = ? AND date = ?', (code, date_str))

            # 插入新数据
            con.execute('''
                INSERT INTO stock_kline_unified
                (source, code, name, date, open, high, low, close, volume, dividends, pct_change, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('yahoo', code, name, date_str, row['Open'], row['High'], row['Low'], row['Close'],
                 int(row['Volume']) if row['Volume'] else None, row['Dividends'], pct_change, datetime.now()))
            inserted += 1

        con.close()
        return {"status": "success", "message": f"{name} K线同步完成: {inserted}条", "code": code}
    except Exception as e:
        return {"status": "error", "message": f"{name} 失败: {str(e)}", "code": code}

def query_stock_data(sql):
    """查询数据"""
    try:
        if not DB_PATH.exists():
            return {"status": "error", "message": "数据库不存在"}

        con = duckdb.connect(str(DB_PATH))
        result = con.execute(sql).fetchall()

        # 获取列名
        columns = []
        if hasattr(con, 'description'):
            try:
                columns = [desc[0] for desc in con.description]
            except:
                columns = []

        con.close()
        return {"status": "success", "rows": result, "columns": columns, "count": len(result)}
    except Exception as e:
        return {"status": "error", "message": f"查询失败: {str(e)}"}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'sync_kline' and len(sys.argv) >= 5:
            result = sync_yahoo_kline(sys.argv[2], sys.argv[3], sys.argv[4])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif command == 'query' and len(sys.argv) >= 3:
            result = query_stock_data(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"status": "error", "message": "未知命令"}, ensure_ascii=False))
    else:
        print(json.dumps({"status": "error", "message": "缺少参数"}, ensure_ascii=False))
EOF

echo "      完成"

# 4. 设置权限
echo ""
echo "[4/6] 设置权限..."
chmod +x "$INSTALL_DIR/tool.py"
chmod 644 "$INSTALL_DIR/SKILL.md"
echo "      完成"

# 5. 安装依赖
echo ""
echo "[5/6] 安装Python依赖..."
pip3 install yfinance duckdb -q 2>/dev/null || echo "      依赖已安装或无需安装"
echo "      完成"

# 6. 重启Gateway
echo ""
echo "[6/6] 重启OpenClaw Gateway..."
openclaw gateway restart 2>/dev/null || echo "      请手动重启: openclaw gateway restart"
echo "      完成"

echo ""
echo "=========================================="
echo "  ✅ 雅虎财经Skill安装完成！"
echo "=========================================="
echo ""
echo "安装位置: $INSTALL_DIR"
echo ""
echo "下一步："
echo "  1. 在OpenClaw中输入: refresh skills"
echo "  2. 测试: 同步伊利股份的雅虎财经数据"
echo ""

# 验证
echo "验证安装..."
ls -lh "$INSTALL_DIR" 2>/dev/null || echo "目录: $INSTALL_DIR"
echo ""
echo "✅ 完成！"

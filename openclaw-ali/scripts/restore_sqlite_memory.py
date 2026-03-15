#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记忆系统同步脚本 - 恢复使用SQLite版本"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"

def restore_sqlite_memory():
    print("="*70)
    print(" 恢复sync_memory.py使用SQLite数据库")
    print("="*70)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 备份旧版本
        print("[1] 备份当前sync_memory.py...")
        stdin, stdout, stderr = ssh.exec_command(
            "cp /root/.openclaw/workspace/sync_memory.py /root/.openclaw/workspace/sync_memory.py.backup_http"
        )
        stdout.read()
        print("  ✅ 已备份")
        print()

        # 通过cat命令直接创建文件
        print("[2] 创建SQLite版本的sync_memory.py...")
        create_script = '''cat > /root/.openclaw/workspace/sync_memory.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""
记忆系统同步脚本
自动将每日分析结果同步到SQLite记忆数据库
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = '/root/.openclaw/workspace/stock_data.db'

def remember(content, thought_type, keywords=None, importance=80, related_to=None, context=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    keywords_str = ','.join(keywords) if keywords else None

    try:
        cursor.execute(
            "INSERT INTO memories (content, thought_type, keywords, importance, related_to, context) VALUES (?, ?, ?, ?, ?, ?)",
            (content, thought_type, keywords_str, importance, related_to, context)
        )
        conn.commit()
        print(f"✅ 记忆已存储: {thought_type}")
        return {"success": True}
    except Exception as e:
        print(f"❌ 存储失败: {e}")
        return {"success": False}
    finally:
        conn.close()

def watch_stock(symbol, name, buy_price, quantity, target_price, current_price):
    content = f"关注股票: {name} ({symbol})"
    content += f" 买入价: ¥{buy_price}, 数量: {quantity}股"
    content += f"  目标价: ¥{target_price}, 当前价: ¥{current_price}"

    return remember(
        content=content,
        thought_type="股票关注",
        keywords=["股票", symbol, name],
        importance=90,
        related_to=f"stock_{symbol}"
    )

def sync_daily_summary(summary_file):
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"\\n{'='*60}")
    print(f"开始同步每日总结: {today}")
    print(f"{'='*60}")

    remember(
        content=f"{today} 基金经理工作完成：选股分析、持仓监控、策略优化",
        thought_type="工作日志",
        importance=80,
        keywords=["基金经理", "工作日志", today]
    )

    try:
        with open('/root/.openclaw/workspace/daily_summaries/screening_results.json', 'r') as f:
            results = json.load(f)

        strong_stocks = [x for x in results if x['strength'] == '中']
        if strong_stocks:
            content = f"{today} 中强度推荐："
            for s in strong_stocks:
                content += f"{s['code']} ¥{s['price']:.2f} {','.join(s['signals'])}; "

            remember(
                content=content,
                thought_type="选股推荐",
                importance=90,
                keywords=["选股", "推荐", "中强度", today],
                related_to="daily_screening"
            )
            print(f"✅ 选股推荐已存储 ({len(strong_stocks)}只)")
    except Exception as e:
        print(f"⚠️  读取选股结果失败: {e}")

    print(f"{'='*60}")
    print(f"✅ 同步完成")
    print(f"{'='*60}\\n")

if __name__ == "__main__":
    sync_daily_summary(None)
ENDOFFILE
'''

        stdin, stdout, stderr = ssh.exec_command(create_script)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if error and "error" in error.lower():
            print(f"  错误: {error}")
        else:
            print("  ✅ 文件已创建")
        print()

        # 验证更新
        print("[3] 验证更新...")
        stdin, stdout, stderr = ssh.exec_command(
            "head -25 /root/.openclaw/workspace/sync_memory.py"
        )
        content = stdout.read().decode().strip()
        print(content)
        print()

        # 测试运行
        print("[4] 测试新的sync_memory.py...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/.openclaw/workspace && python3 sync_memory.py 2>&1"
        )
        test_result = stdout.read().decode().strip()
        print(test_result)
        print()

        ssh.close()

        print("="*70)
        print(" 恢复完成!")
        print("="*70)
        print()
        print("sync_memory.py已改回使用SQLite数据库")
        print("  数据库: /root/.openclaw/workspace/stock_data.db")
        print("  方式: 直接SQLite连接")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    restore_sqlite_memory()

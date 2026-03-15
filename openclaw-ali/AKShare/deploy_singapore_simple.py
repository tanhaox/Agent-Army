#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡服务器 - AKShare数据同步简化版
快速测试和部署
"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = '157.245.195.58'
KEY_PATH = 'C:/Users/tanha/.ssh/digitalocean_openclaw'
USERNAME = 'root'

print('=' * 100)
print('  新加坡服务器 - AKShare快速部署')
print('=' * 100)

try:
    # 连接服务器
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, port=22, username=USERNAME, pkey=key, timeout=30)
    print('✅ 连接成功\n')

    # 简化的同步脚本
    sync_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import akshare as ak
import duckdb
from datetime import datetime, timedelta
import time

# 配置
DB_PATH = '/root/data/stock_market.db'
LOG_PATH = '/root/logs/akshare_sync.log'

# 股票列表
STOCK_LIST = [
    {'code': '601669', 'name': '中国电建'},
    {'code': '600519', 'name': '贵州茅台'},
    {'code': '000001', 'name': '平安银行'},
    {'code': '002594', 'name': '比亚迪'},
    {'code': '300750', 'name': '宁德时代'},
]

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    s = f'[{timestamp}] {msg}'
    print(s)
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(s + '\\n')
    except:
        pass

def init_db():
    log('初始化数据库...')
    con = duckdb.connect(DB_PATH)
    con.execute('''
        CREATE TABLE IF NOT EXISTS stock_kline (
            code VARCHAR, name VARCHAR, date DATE,
            open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
            volume DOUBLE, amount DOUBLE,
            pct_change DOUBLE, turnover_rate DOUBLE,
            PRIMARY KEY (code, date)
        )
    ''')
    con.close()

def sync_stock(code, name):
    log(f'同步 {name} ({code})')

    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )

        if df is not None and len(df) > 0:
            con = duckdb.connect(DB_PATH)

            for _, row in df.iterrows():
                try:
                    con.execute('''
                        INSERT OR REPLACE INTO stock_kline
                        (code, name, date, open, high, low, close, volume, amount, pct_change, turnover_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        code, name, row['日期'],
                        row['开盘'], row['最高'], row['最低'], row['收盘'],
                        row['成交量'], row['成交额'], row['涨跌幅'], row['换手率']
                    ))
                except:
                    pass

            con.close()
            log(f'  OK {len(df)} 条')
            return True
    except Exception as e:
        log(f'  失败: {e}')
        return False

def main():
    log('=' * 60)
    log('AKShare数据同步开始')
    log(f'股票: {len(STOCK_LIST)} 只')

    init_db()

    success = 0
    for i, stock in enumerate(STOCK_LIST, 1):
        if sync_stock(stock['code'], stock['name']):
            success += 1
        time.sleep(1)

    log('')
    log('=' * 60)
    log(f'完成: 成功 {success}/{len(STOCK_LIST)}')
    log('=' * 60)

if __name__ == '__main__':
    main()
"""

    # 上传脚本
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir('/root/memory')
        sftp.mkdir('/root/data')
        sftp.mkdir('/root/logs')
    except:
        pass

    sftp.file('/root/memory/akshare_sync.py', 'w').write(sync_script.encode('utf-8'))
    sftp.close()
    print('✅ 脚本已上传\n')

    # 运行
    print('=' * 100)
    print('  运行数据同步')
    print('=' * 100)
    print()

    stdin, stdout, stderr = ssh.exec_command(
        'cd /root/memory && python3 akshare_sync.py',
        get_pty=True
    )

    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip('\n'))

    exit_status = stdout.channel.recv_exit_status()

    # 验证
    print()
    print('=' * 100)
    print('  数据验证')
    print('=' * 100)
    print()

    stdin, stdout, stderr = ssh.exec_command('''
python3 -c "import duckdb; con=duckdb.connect('/root/data/stock_market.db'); r=con.execute('SELECT code, name, COUNT(*) as cnt FROM stock_kline GROUP BY code ORDER BY code').fetchall(); print(f'{"代码":<8} {"名称":<12} {"记录数":<8}'); print("-" * 35); [print(f'{row[0]:<8} {row[1]:<12} {row[2]:<8}') for row in r] if r else print('无数据')"
''')

    print(stdout.read().decode('utf-8'))

    ssh.close()

    print()
    print('=' * 100)
    print(f'  {"✅ 部署完成" if exit_status == 0 else "⚠️ 部署警告"}')
    print('=' * 100)

except Exception as e:
    print(f'\n❌ 错误: {e}')
    import traceback
    traceback.print_exc()

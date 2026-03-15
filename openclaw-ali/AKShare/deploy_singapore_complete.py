#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡服务器 - AKShare数据同步完整版
服务器: DigitalOcean 157.245.195.58
功能: K线数据 + 个股信息 + 数据库存储
"""
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新加坡服务器配置
HOST = '157.245.195.58'
KEY_PATH = 'C:/Users/tanha/.ssh/digitalocean_openclaw'
USERNAME = 'root'

print('=' * 100)
print('  新加坡服务器 - AKShare完整部署方案')
print('=' * 100)
print(f'服务器: {HOST}')
print()

try:
    # 读取SSH密钥（自动检测格式）
    key = None
    for key_class in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]:
        try:
            key = key_class.from_private_key_file(KEY_PATH)
            print(f'✅ SSH密钥: {key_class.__name__}')
            break
        except:
            continue

    if key is None:
        raise Exception("无法读取SSH密钥")

    # 连接服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, port=22, username=USERNAME, pkey=key, timeout=30)
    print('✅ 服务器连接成功\n')

    # 完整的数据同步脚本
    sync_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
AKShare A股数据同步脚本（生产环境）
功能：
1. 获取多只股票的历史K线数据
2. 获取个股详细信息
3. 存储到DuckDB数据库
4. 支持增量更新和全量更新
\"\"\"
import akshare as ak
import duckdb
from datetime import datetime, timedelta
import time
import sys
import os

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

def log(message):
    \"\"\"记录日志\"\"\"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f'[{timestamp}] {message}'
    print(log_msg)
    try:
        os.makedirs('/root/logs', exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\\n')
    except:
        pass

def init_database():
    \"\"\"初始化数据库表\"\"\"
    log('初始化数据库...')

    con = duckdb.connect(DB_PATH)

    # 创建K线数据表
    con.execute('''
        CREATE TABLE IF NOT EXISTS stock_kline (
            code VARCHAR,
            name VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            amount DOUBLE,
            amplitude DOUBLE,
            pct_change DOUBLE,
            change_amount DOUBLE,
            turnover_rate DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (code, date)
        )
    ''')

    # 创建个股信息表
    con.execute('''
        CREATE TABLE IF NOT EXISTS stock_info (
            code VARCHAR PRIMARY KEY,
            name VARCHAR,
            market_cap DOUBLE,
            circulating_cap DOUBLE,
            industry VARCHAR,
            list_date VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    con.close()
    log('✅ 数据库初始化完成')

def get_stock_kline(code, days=30):
    \"\"\"获取股票K线数据\"\"\"
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )

        if df is not None and len(df) > 0:
            # 重命名列
            df = df.rename(columns={
                '股票代码': 'code',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate'
            })

            return df
        return None
    except Exception as e:
        log(f'❌ 获取{code} K线失败: {e}')
        return None

def get_stock_info(code):
    \"\"\"获取个股信息\"\"\"
    try:
        df = ak.stock_individual_info_em(symbol=code)

        if df is not None and len(df) > 0:
            info_dict = dict(zip(df['item'], df['value']))

            return {
                'code': info_dict.get('股票代码', code),
                'name': info_dict.get('股票名称', ''),
                'market_cap': float(info_dict.get('总市值', 0)) if info_dict.get('总市值') else None,
                'circulating_cap': float(info_dict.get('流通市值', 0)) if info_dict.get('流通市值') else None,
                'industry': info_dict.get('行业', ''),
                'list_date': info_dict.get('上市时间', '')
            }
        return None
    except Exception as e:
        log(f'❌ 获取{code} 信息失败: {e}')
        return None

def save_to_database(kline_df, info_dict, stock_name):
    \"\"\"保存数据到数据库\"\"\"
    con = duckdb.connect(DB_PATH)

    try:
        # 保存K线数据
        if kline_df is not None:
            kline_df['name'] = stock_name

            for _, row in kline_df.iterrows():
                con.execute('''
                    INSERT OR REPLACE INTO stock_kline
                    (code, name, date, open, high, low, close, volume, amount,
                     amplitude, pct_change, change_amount, turnover_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['code'], row['name'], row['日期'],
                    row['open'], row['high'], row['low'], row['close'],
                    row['volume'], row['amount'], row['amplitude'],
                    row['pct_change'], row['change_amount'], row['turnover_rate']
                ))

            log(f'✅ 保存 {len(kline_df)} 条K线数据')

        # 保存个股信息
        if info_dict:
            con.execute('''
                INSERT OR REPLACE INTO stock_info
                (code, name, market_cap, circulating_cap, industry, list_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                info_dict['code'], info_dict['name'],
                info_dict['market_cap'], info_dict['circulating_cap'],
                info_dict['industry'], info_dict['list_date']
            ))

            log(f'✅ 保存个股信息')

        con.close()
        return True

    except Exception as e:
        log(f'❌ 保存数据失败: {e}')
        con.close()
        return False

def sync_stock_data(stock, days=30):
    \"\"\"同步单只股票数据\"\"\"
    code = stock['code']
    name = stock['name']

    log(f'\\n📊 开始同步: {name} ({code})')

    # 获取K线数据
    kline_df = get_stock_kline(code, days)
    if kline_df is not None:
        log(f'  ✅ K线数据: {len(kline_df)} 条')
        # 显示最新数据
        latest = kline_df.iloc[-1]
        log(f'     最新: {latest[\"日期\"]} 收盘{latest[\"close\"]:.2f} 涨跌{latest[\"pct_change\"]:.2f}%')
    else:
        log(f'  ❌ K线数据获取失败')
        return False

    time.sleep(0.5)  # 间隔0.5秒

    # 获取个股信息
    info_dict = get_stock_info(code)
    if info_dict:
        log(f'  ✅ 个股信息: {info_dict[\"industry\"]} 市值{info_dict[\"market_cap\"]/1e8:.1f}亿')
    else:
        log(f'  ⚠️  个股信息获取失败（不影响K线数据）')

    # 保存到数据库
    if save_to_database(kline_df, info_dict, name):
        log(f'  ✅ 数据已保存到数据库')
        return True
    else:
        log(f'  ❌ 数据保存失败')
        return False

def main():
    \"\"\"主函数\"\"\"
    log('=' * 80)
    log('AKShare数据同步开始')
    log('=' * 80)
    log(f'AKShare版本: {ak.__version__}')
    log(f'股票数量: {len(STOCK_LIST)}')
    log()

    # 初始化数据库
    init_database()

    # 同步数据
    success_count = 0
    fail_count = 0

    for i, stock in enumerate(STOCK_LIST, 1):
        log(f'\\n进度: [{i}/{len(STOCK_LIST)}]')

        try:
            if sync_stock_data(stock, days=30):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            log(f'同步异常: {e}')
            fail_count += 1

        # 股票之间间隔
        if i < len(STOCK_LIST):
            time.sleep(1)

    # 统计结果
    log('\\n' + '=' * 80)
    log('同步完成')
    log('=' * 80)
    log(f'成功: {success_count} 只')
    log(f'失败: {fail_count} 只')
    log(f'成功率: {success_count/len(STOCK_LIST)*100:.1f}%')
    log(f'数据库: {DB_PATH}')
    log('=' * 80)

if __name__ == '__main__':
    main()
"""

    # 上传脚本
    print('正在上传脚本到服务器...\n')
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir('/root/memory')
        sftp.mkdir('/root/data')
        sftp.mkdir('/root/logs')
    except:
        pass

    sftp.file('/root/memory/akshare_sync.py', 'w').write(sync_script.encode('utf-8'))
    sftp.close()
    print('✅ 脚本已上传: /root/memory/akshare_sync.py\n')

    # 运行测试
    print('=' * 100)
    print('  运行数据同步测试')
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

    # 验证数据库
    print('\n' + '=' * 100)
    print('  验证数据库数据')
    print('=' * 100)
    print()

    verify_script = """
import duckdb

con = duckdb.connect('/root/data/stock_market.db')

# 查询K线数据
print('📊 K线数据统计:')
result = con.execute('''
    SELECT code, name, COUNT(*) as records,
           MIN(date) as start_date, MAX(date) as end_date
    FROM stock_kline
    GROUP BY code, name
    ORDER BY code
''').fetchall()

if result:
    print(f'{"股票代码":<8} {"名称":<12} {"记录数":<8} {"开始日期":<12} {"结束日期":<12}')
    print('-' * 70)
    for row in result:
        print(f'{row[0]:<8} {row[1]:<12} {row[2]:<8} {str(row[3]):<12} {str(row[4]):<12}')
else:
    print('❌ 没有数据')

print()

# 查询个股信息
print('📋 个股信息:')
result = con.execute('SELECT * FROM stock_info ORDER BY code').fetchall()

if result:
    print(f'{"股票代码":<8} {"名称":<12} {"行业":<12} {"市值(亿)":<12}')
    print('-' * 60)
    for row in result:
        market_cap = f"{row[3]/1e8:.1f}" if row[3] else "N/A"
        print(f'{row[0]:<8} {row[1]:<12} {row[5]:<12} {market_cap:<12}')
else:
    print('❌ 没有数据')

con.close()
"""

    sftp = ssh.open_sftp()
    sftp.file('/root/memory/verify_db.py', 'w').write(verify_script.encode('utf-8'))
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command('cd /root/memory && python3 verify_db.py')

    print(stdout.read().decode('utf-8', errors='ignore'))

    ssh.close()

    print()
    print('=' * 100)
    if exit_status == 0:
        print('  ✅ 部署完成')
    else:
        print(f'  ⚠️  退出状态: {exit_status}')
    print('=' * 100)

except Exception as e:
    print(f'\n❌ [错误] {e}')
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""Final database check with corrected sector query"""
import paramiko
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Server connection info
KEY_FILE = r'C:\Users\tanha\.ssh\digitalocean_openclaw'
KEY_PASSWORD = 'a19571004'

try:
    # Load SSH key
    key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)

    # Connect to server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='157.245.195.58', port=2323, username='root', pkey=key, timeout=15)
    print("Connected to server\n")

    # Check scipy
    print('=' * 70)
    print('1. Scipy Installation')
    print('=' * 70)
    stdin, stdout, stderr = ssh.exec_command('python3 -c "import scipy; print(scipy.__version__)"')
    scipy_output = stdout.read().decode().strip()
    print(f'Version: {scipy_output}\n')

    # Check sector_member table
    print('=' * 70)
    print('2. Sector Member Table (sector_member)')
    print('=' * 70)
    cmd = """cd /root/.openclaw/workspace/data/ && python3 << 'PYEOF'
import duckdb
conn = duckdb.connect('market_data.db', read_only=True)

print("Schema:")
result = conn.execute("DESCRIBE sector_member")
for row in result.fetchall():
    print(f"  {row[0]:20} {row[1]:15} {row[2]:5}")

print("\\nSample rows (first 5):")
result = conn.execute("SELECT * FROM sector_member LIMIT 5")
for row in result.fetchall():
    print(f"  {row}")

print("\\nDistinct sectors (sector_code, sector_name):")
result = conn.execute("SELECT DISTINCT sector_code, sector_name FROM sector_member ORDER BY sector_code")
for row in result.fetchall():
    print(f"  {row[0]:10} - {row[1]}")

conn.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    # Check finance table details
    print('\n' + '=' * 70)
    print('3. Finance Table Summary')
    print('=' * 70)
    cmd = """cd /root/.openclaw/workspace/data/ && python3 << 'PYEOF'
import duckdb
conn = duckdb.connect('market_data.db', read_only=True)

print("Available fields for finance indicators:")
result = conn.execute("DESCRIBE finance")
fields = list(result.fetchall())
for row in fields:
    print(f"  - {row[0]:20} {row[1]:10}")

print("\\nTable statistics:")
result = conn.execute("SELECT COUNT(*) as total, COUNT(DISTINCT stock_code) as stocks FROM finance")
stats = result.fetchone()
print(f"  Total records: {stats[0]}")
print(f"  Distinct stocks: {stats[1]}")

conn.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    # Check daily_kline table
    print('\n' + '=' * 70)
    print('4. Daily Kline Table Summary')
    print('=' * 70)
    cmd = """cd /root/.openclaw/workspace/data/ && python3 << 'PYEOF'
import duckdb
conn = duckdb.connect('market_data.db', read_only=True)

print("Key columns for liquidity analysis:")
print("  - amount:交易金额 (DOUBLE)")
print("  - turnover:换手率 (DOUBLE)")
print("  - volume:成交量 (BIGINT)")

print("\\nTable statistics:")
result = conn.execute("SELECT COUNT(*) as total, COUNT(DISTINCT stock_code) as stocks, MIN(date) as min_date, MAX(date) as max_date FROM daily_kline")
stats = result.fetchone()
print(f"  Total records: {stats[0]:,}")
print(f"  Distinct stocks: {stats[1]:,}")
print(f"  Date range: {stats[2]} to {stats[3]}")

print("\\nSample data (showing liquidity fields):")
result = conn.execute("SELECT stock_code, date, close, volume, amount, turnover FROM daily_kline LIMIT 3")
for row in result.fetchall():
    print(f"  {row[0]} {row[1]} | price: {row[2]:.2f} | vol: {row[3]:,} | amt: {row[4]:,.0f} | turnover: {row[5]}")

conn.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    # Check current_holdings
    print('\n' + '=' * 70)
    print('5. Current Holdings Summary')
    print('=' * 70)
    cmd = """cd /root/.openclaw/workspace/data/ && python3 << 'PYEOF'
import duckdb
conn = duckdb.connect('holdings.db', read_only=True)

result = conn.execute("SELECT code, name, shares, cost_price, current_price, profit_loss, profit_loss_pct, market_value FROM current_holdings")
holdings = result.fetchall()

print(f"Total holdings: {len(holdings)}")
print("\\n Holdings detail:")
print(f"{'Code':15} {'Name':10} {'Shares':>8} {'Cost':>8} {'Current':>8} {'P/L':>10} {'P/L%':>8} {'Value':>12}")
print("-" * 85)
for h in holdings:
    print(f"{h[0]:15} {h[1]:10} {h[2]:8} {h[3]:8.2f} {h[4]:8.2f} {h[5]:10.2f} {h[6]:7.2f}% {h[7]:12,.0f}")

conn.close()
PYEOF
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    ssh.close()
    print("\n" + "=" * 70)
    print("✅ Database check completed successfully")
    print("=" * 70)

except Exception as e:
    print(f'Error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

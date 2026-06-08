"""
股票代码映射初始化脚本
从 AKShare 获取最新股票代码映射并缓存到本地

使用方法：
    python scripts/init_stock_mapper.py
"""

import sys
import os
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.stock_code_mapper import StockCodeMapper
import time


def main():
    print("=" * 60)
    print("  Stock Code Mapper Initializer")
    print("=" * 60)
    print()

    # 创建映射管理器
    print("[1/3] Creating mapper...")
    mapper = StockCodeMapper(cache_dir="./data", cache_expiry_hours=24)

    # 检查缓存状态
    print("\n[2/3] Checking cache status...")
    stats = mapper.get_stats()

    if stats['cache_exists']:
        age = stats['cache_age_hours']
        print(f"   [OK] Cache exists, age: {age:.1f} hours")

        if age < 24:
            print(f"   [OK] Cache is fresh (< 24 hours)")
            user_input = input("   Update anyway? (y/N): ").strip().lower()
            if user_input != 'y':
                print("   [SKIP] Skipping update")
                print()
                print(f"   [INFO] Current mapping: {stats['total_stocks']} stocks")
                return
    else:
        print("   [INFO] Cache not found, creating...")

    # 从 AKShare 获取映射
    print("\n[3/3] Fetching stock mapping from AKShare...")
    start_time = time.time()

    success = mapper.fetch_from_akshare()

    elapsed = time.time() - start_time

    # 重新获取统计信息（fetch后更新）
    stats = mapper.get_stats()

    if success:
        print()
        print("=" * 60)
        print("  [SUCCESS] Initialization Complete!")
        print("=" * 60)
        print(f"   [INFO] Stock count: {stats['total_stocks']}")
        print(f"   [INFO] Time elapsed: {elapsed:.2f} seconds")
        print(f"   [INFO] Cache location: {mapper.cache_file}")
        print()
        print("   You can now use stock names for queries!")
        print()
    else:
        print()
        print("=" * 60)
        print("  [ERROR] Initialization Failed")
        print("=" * 60)
        print()
        print("   Please check:")
        print("   1. AKShare installed (pip install akshare)")
        print("   2. Network connection")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] User cancelled")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

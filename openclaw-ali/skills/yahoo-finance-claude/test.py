#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经Skill测试脚本
验证所有工具函数是否正常工作
"""
import sys
import os
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加skill目录到路径
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

# 导入工具函数
from tool import sync_yahoo_kline, sync_yahoo_info, query_stock_data

def test_sync_kline():
    """测试K线数据同步"""
    print("=" * 60)
    print("测试1: 同步K线数据")
    print("=" * 60)

    result = sync_yahoo_kline(
        code='600887',
        name='伊利股份',
        exchange='SS',
        period='1mo'
    )

    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    if result['status'] == 'success':
        print(f"插入记录: {result['inserted']}条")

    print()
    return result['status'] == 'success'

def test_sync_info():
    """测试个股信息同步"""
    print("=" * 60)
    print("测试2: 同步个股信息")
    print("=" * 60)

    result = sync_yahoo_info(
        code='600887',
        name='伊利股份',
        exchange='SS'
    )

    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    if result['status'] == 'success':
        print(f"有效字段: {result['valid_fields']}+")

    print()
    return result['status'] == 'success'

def test_query_data():
    """测试数据查询"""
    print("=" * 60)
    print("测试3: 查询数据")
    print("=" * 60)

    sql = """
    SELECT code, name, industry, market_cap, trailing_pe, dividend_yield
    FROM stock_info_unified
    ORDER BY market_cap DESC
    LIMIT 5
    """

    result = query_stock_data(sql)

    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"查询到: {result['count']}条记录")
        print("\n数据预览:")
        print(f"{'列名': <10} {'值'}")
        print("-" * 60)
        for col in result['columns'][:6]:
            print(f"{col: <10}")
        print("-" * 60)
        for row in result['rows'][:3]:
            for i, val in enumerate(row):
                if i < 6:
                    print(f"{str(val): <10}", end=" ")
            print()
    else:
        print(f"错误: {result['message']}")

    print()
    return result['status'] == 'success'

def test_query_high_dividend():
    """测试查询高分红股票"""
    print("=" * 60)
    print("测试4: 查询高分红股票")
    print("=" * 60)

    sql = """
    SELECT code, name, dividend_yield, market_cap
    FROM stock_info_unified
    WHERE dividend_yield > 3
    ORDER BY dividend_yield DESC
    """

    result = query_stock_data(sql)

    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"找到 {result['count']}只高分红股票")
        print("\n股票列表:")
        for row in result['rows']:
            print(f"  {row['code']} {row['name']}: 股息率 {row['dividend_yield']:.2f}%")
    else:
        print(f"错误: {result['message']}")

    print()
    return result['status'] == 'success'

def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  雅虎财经Skill测试".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # 运行测试
    try:
        results.append(("K线同步", test_sync_kline()))
    except Exception as e:
        print(f"❌ K线同步测试失败: {e}")
        results.append(("K线同步", False))
        print()

    try:
        results.append(("个股信息", test_sync_info()))
    except Exception as e:
        print(f"❌ 个股信息测试失败: {e}")
        results.append(("个股信息", False))
        print()

    try:
        results.append(("数据查询", test_query_data()))
    except Exception as e:
        print(f"❌ 数据查询测试失败: {e}")
        results.append(("数据查询", False))
        print()

    try:
        results.append(("高分红筛选", test_query_high_dividend()))
    except Exception as e:
        print(f"❌ 高分红筛选测试失败: {e}")
        results.append(("高分红筛选", False))
        print()

    # 输出测试总结
    print("=" * 60)
    print("  测试总结")
    print("=" * 60)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name: <20} {status}")

    print()
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print()

    if passed == total:
        print("🎉 所有测试通过！Skill可以正常使用。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

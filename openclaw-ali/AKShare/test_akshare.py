# -*- coding: utf-8 -*-
"""
AKShare股票数据接口本地测试
根据《AKShare股票数据全面接入服务器使用手册》进行测试
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_stock_realtime():
    """测试A股实时行情"""
    print_section("测试1: A股实时行情 (stock_zh_a_spot_em)")

    try:
        df = ak.stock_zh_a_spot_em()
        print(f"[OK] 成功获取数据，共 {len(df)} 条记录")
        print(f"\n前5条记录:")
        print(df.head().to_string())
        print(f"\n数据字段: {list(df.columns)}")
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_stock_history():
    """测试个股历史数据"""
    print_section("测试2: 个股历史数据 (stock_zh_a_hist)")

    try:
        # 获取平安银行(000001)最近30天的数据
        end_date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20250201",
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        print(f"[OK] 成功获取平安银行历史数据，共 {len(df)} 条记录")
        print(f"\n最新5条记录:")
        print(df.tail().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_stock_info():
    """测试个股详细信息"""
    print_section("测试3: 个股详细信息 (stock_individual_info_em)")

    try:
        df = ak.stock_individual_info_em(symbol="000001")
        print(f"[OK] 成功获取平安银行详细信息")
        print(df.to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_fund_etf():
    """测试ETF基金数据"""
    print_section("测试4: ETF基金实时行情 (fund_etf_spot_em)")

    try:
        df = ak.fund_etf_spot_em()
        print(f"[OK] 成功获取ETF数据，共 {len(df)} 条记录")
        print(f"\n前5条记录:")
        print(df.head().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_hk_stock():
    """测试港股数据"""
    print_section("测试5: 港股实时行情 (stock_hk_spot_em)")

    try:
        df = ak.stock_hk_spot_em()
        print(f"[OK] 成功获取港股数据，共 {len(df)} 条记录")
        print(f"\n前5条记录:")
        print(df.head().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_us_stock():
    """测试美股数据"""
    print_section("测试6: 美股实时行情 (stock_us_spot_em)")

    try:
        df = ak.stock_us_spot_em()
        print(f"[OK] 成功获取美股数据，共 {len(df)} 条记录")
        print(f"\n前5条记录:")
        print(df.head().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_macro_cpi():
    """测试宏观经济数据-CPI"""
    print_section("测试7: CPI数据 (macro_china_cpi)")

    try:
        df = ak.macro_china_cpi()
        print(f"[OK] 成功获取CPI数据，共 {len(df)} 条记录")
        print(f"\n最新5条记录:")
        print(df.tail().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def test_futures():
    """测试期货数据"""
    print_section("测试8: 期货实时行情 (futures_zh_realtime)")

    try:
        df = ak.futures_zh_realtime()
        print(f"[OK] 成功获取期货数据，共 {len(df)} 条记录")
        print(f"\n前5条记录:")
        print(df.head().to_string())
    except Exception as e:
        print(f"[FAIL] 失败: {e}")

def main():
    """主测试函数"""
    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  AKShare股票数据接口本地测试".center(78) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)

    # 验证AKShare版本
    print(f"\n[版本] AKShare版本: {ak.__version__}")
    print(f"[版本] Pandas版本: {pd.__version__}")

    # 运行所有测试
    tests = [
        test_stock_realtime,
        test_stock_history,
        test_stock_info,
        test_fund_etf,
        test_hk_stock,
        test_us_stock,
        test_macro_cpi,
        test_futures,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] 测试异常: {e}")
            failed += 1

    # 测试总结
    print("\n" + "#" * 80)
    print(f"#  测试完成: 通过 {passed} 项，失败 {failed} 项")
    print("#" * 80)

if __name__ == "__main__":
    main()

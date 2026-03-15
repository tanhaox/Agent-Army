"""
测试新数据源工具（Yahoo Finance、AKShare、EastMoney爬虫）
"""
import pytest

import sys
import io
import asyncio
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_yahoo_tool():
    """测试Yahoo Finance工具"""

    print("\n" + "=" * 70)
    print("  测试 Yahoo Finance 工具")
    print("=" * 70)

    from src.core.tools.data_source.yahoo_tool import YahooFinanceTool

    tool = YahooFinanceTool()

    if not tool.is_available():
        print("❌ yfinance未安装")
        print("请运行: pip install yfinance")
        return False

    print("✅ Yahoo Finance工具初始化成功")

    # 测试1: 获取股票信息
    print("\n[1] 测试获取股票信息: 601669.SS (中国电建)")
    info = tool.get_stock_info("601669.SS")

    if "error" not in info:
        print(f"✅ 获取成功!")
        print(f"   公司名称: {info.get('name')}")
        print(f"   市值: {info.get('market_cap')}")
        print(f"   行业: {info.get('industry')}")
    else:
        print(f"❌ 获取失败: {info['error']}")
        return False

    # 测试2: 获取历史数据
    print("\n[2] 测试获取历史K线数据")
    hist = tool.get_historical_data("601669.SS", period="5d", interval="1d")

    if not hist.empty:
        print(f"✅ 获取成功! {len(hist)} 条记录")
        print(f"   列名: {hist.columns.tolist()}")
    else:
        print("❌ 未获取到数据")

    # 测试3: 获取实时行情
    print("\n[3] 测试获取实时行情")
    quote = tool.get_realtime_quote("601669.SS")

    if "error" not in quote:
        print(f"✅ 获取成功!")
        print(f"   当前价格: {quote.get('current_price')}")
        print(f"   涨跌幅: {quote.get('change_percent', 0):.2f}%")
        print(f"   成交量: {quote.get('volume')}")
    else:
        print(f"❌ 获取失败: {quote['error']}")

    return True


def test_akshare_tool():
    """测试AKShare工具"""

    print("\n" + "=" * 70)
    print("  测试 AKShare 工具")
    print("=" * 70)

    from src.core.tools.data_source.akshare_tool import AKShareTool

    tool = AKShareTool()

    if not tool.is_available():
        print("❌ akshare未安装")
        print("请运行: pip install akshare")
        return False

    print("✅ AKShare工具初始化成功")

    # 测试1: 获取资金流向
    print("\n[1] 测试获取个股资金流向: 601669 (中国电建)")
    df = tool.get_individual_fund_flow("601669", "sh")

    if not df.empty:
        print(f"✅ 获取成功! {len(df)} 条记录")
        print(f"   列名: {df.columns.tolist()}")
        if len(df) > 0:
            print(f"   最新数据:")
            print(df.head(2).to_string())
    else:
        print("⚠️  未获取到数据（可能需要等待市场开盘时间）")

    # 测试2: 获取实时行情
    print("\n[2] 测试获取实时行情")
    quote = tool.get_realtime_quote("601669")

    if "error" not in quote:
        print(f"✅ 获取成功!")
        print(f"   股票名称: {quote.get('name')}")
        print(f"   当前价格: {quote.get('current_price')}")
        print(f"   涨跌幅: {quote.get('change_percent', 0):.2f}%")
    else:
        print(f"❌ 获取失败: {quote['error']}")

    # 测试3: 获取龙虎榜
    print("\n[3] 测试获取龙虎榜数据")
    df = tool.get_top_list()

    if not df.empty:
        print(f"✅ 获取成功! {len(df)} 条记录")
    else:
        print("⚠️  未获取到数据（可能今日无龙虎榜数据）")

    return True


@pytest.mark.asyncio
async def test_eastmoney_scraper():
    """测试EastMoney爬虫工具"""

    print("\n" + "=" * 70)
    print("  测试 EastMoney 爬虫工具")
    print("=" * 70)

    from src.core.tools.data_source.eastmoney_scraper import EastMoneyScraper

    scraper = EastMoneyScraper()

    if not scraper.is_available():
        print("❌ playwright未安装")
        print("请运行: pip install playwright && playwright install chromium")
        return False

    print("✅ EastMoney爬虫初始化成功")

    # 测试1: 抓取资金流向
    print("\n[1] 测试抓取资金流向数据: 601669 (中国电建)")
    print("   (这可能需要20-30秒...)")

    result = await scraper.scrape_capital_flow("601669", timeout=30000)

    if "error" not in result:
        print(f"✅ 抓取成功!")
        print(f"   股票代码: {result['stock_code']}")
        print(f"   日期: {result['date']}")
        print(f"   今日净流入: {result.get('net_inflow', 'N/A')} 亿元")
        print(f"   主力净流入: {result.get('main_net', 'N/A')} 亿元")
        print(f"   超大单净流入: {result.get('super_large_net', 'N/A')} 亿元")
        print(f"   大单净流入: {result.get('large_net', 'N/A')} 亿元")
    else:
        print(f"❌ 抓取失败: {result['error']}")

    return True


def test_all_tools():
    """测试所有新数据源工具"""

    print("\n" + "=" * 70)
    print("  新数据源工具集成测试")
    print("=" * 70)

    results = {}

    # 测试 Yahoo Finance
    try:
        results['yahoo'] = test_yahoo_tool()
    except Exception as e:
        print(f"❌ Yahoo Finance测试异常: {e}")
        results['yahoo'] = False

    # 测试 AKShare
    try:
        results['akshare'] = test_akshare_tool()
    except Exception as e:
        print(f"❌ AKShare测试异常: {e}")
        results['akshare'] = False

    # 测试 EastMoney爬虫
    try:
        results['eastmoney'] = asyncio.run(test_eastmoney_scraper())
    except Exception as e:
        print(f"❌ EastMoney爬虫测试异常: {e}")
        results['eastmoney'] = False

    # 汇总结果
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)

    for tool_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{tool_name.upper():15} : {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ 所有测试通过!")
    else:
        print("  ⚠️  部分测试失败，请检查错误信息")
    print("=" * 70)

    print("\n新数据源工具功能:")
    print("1. ✅ YahooFinanceTool: 国际标准股票数据（实时行情、历史K线、财务报表）")
    print("2. ✅ AKShareTool: 中国金融数据（资金流向、龙虎榜、融资融券）")
    print("3. ✅ EastMoneyScraper: 动态网页爬虫（东方财富数据中心）")

    print("\n数据源优势:")
    print("• Yahoo Finance: 免费稳定，全球市场覆盖")
    print("• AKShare:      专注A股，接口丰富")
    print("• EastMoney:    动态数据，实时更新")

    return all_passed


if __name__ == "__main__":
    test_all_tools()

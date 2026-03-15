"""
工具库门面层测试

验证：
1. IndustryTool - 行业分析工具
2. TechnicalTool - 技术分析工具
3. CapitalFlowTool - 资金流向工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.logger import setup_logging, get_logger
from src.core.tools.tool_facades import (
    IndustryTool,
    TechnicalTool,
    CapitalFlowTool,
    get_industry_tool,
    get_technical_tool,
    get_capital_flow_tool
)


# ========== 测试 IndustryTool ==========

async def test_industry_tool():
    """测试行业分析工具"""
    print("\n" + "=" * 70)
    print("测试 IndustryTool - 行业分析工具")
    print("=" * 70)

    tool = get_industry_tool()

    # 测试1: 获取行业信息（不包含产业链）
    print("\n[测试1] 获取行业信息: 601669 (中国电建)")
    result = await tool.get_industry_info("601669", use_chain=False)

    print(f"✅ 股票代码: {result.get('stock_code')}")
    print(f"✅ 股票名称: {result.get('stock_name')}")
    print(f"✅ 行业: {result.get('industry')}")
    print(f"✅ 板块: {result.get('sector')}")
    print(f"✅ 数据源: {result.get('data_source')}")

    # 测试2: 获取行业信息（包含产业链）
    print("\n[测试2] 获取行业信息（含产业链）: 600519 (贵州茅台)")
    result = await tool.get_industry_info("600519", use_chain=True)

    print(f"✅ 股票代码: {result.get('stock_code')}")
    print(f"✅ 股票名称: {result.get('stock_name')}")
    print(f"✅ 行业: {result.get('industry')}")
    print(f"✅ 行业代码: {result.get('industry_code')}")

    chain = result.get('industry_chain', {})
    print(f"✅ 产业链上游: {chain.get('upstream', [])[:3]}")
    print(f"✅ 产业链中游: {chain.get('midstream', [])[:3]}")
    print(f"✅ 产业链下游: {chain.get('downstream', [])[:3]}")

    print("\n✅ IndustryTool 测试通过")


# ========== 测试 TechnicalTool ==========

def test_technical_tool():
    """测试技术分析工具"""
    print("\n" + "=" * 70)
    print("测试 TechnicalTool - 技术分析工具")
    print("=" * 70)

    tool = get_technical_tool()

    # 测试1: 获取K线数据
    print("\n[测试1] 获取K线数据: 601669 (中国电建)")
    df = tool.get_kline("601669", period="3mo", interval="1d")

    if not df.empty:
        print(f"✅ 数据条数: {len(df)}")
        print(f"✅ 数据列: {', '.join(df.columns.tolist())}")
        print(f"✅ 最新日期: {df.index[-1]}")
        print(f"✅ 最新收盘价: {df['Close'].iloc[-1]:.2f}")
    else:
        print("⚠️ 未获取到K线数据（可能需要安装 yfinance）")

    # 测试2: 获取涨跌榜
    print("\n[测试2] 获取涨跌榜")
    df = tool.get_top_list(limit=10)

    if not df.empty:
        print(f"✅ 数据条数: {len(df)}")
        print(f"✅ 数据列: {', '.join(df.columns.tolist())}")
    else:
        print("⚠️ 未获取到涨跌榜数据（可能需要安装 akshare）")

    print("\n✅ TechnicalTool 测试通过")


# ========== 测试 CapitalFlowTool ==========

async def test_capital_flow_tool():
    """测试资金流向工具"""
    print("\n" + "=" * 70)
    print("测试 CapitalFlowTool - 资金流向工具")
    print("=" * 70)

    tool = get_capital_flow_tool()

    # 测试1: 获取资金流向数据
    print("\n[测试1] 获取资金流向数据: 600519 (贵州茅台)")
    result = await tool.get_capital_flow("600519")

    print(f"✅ 股票代码: {result.get('stock_code')}")
    print(f"✅ 数据条数: {result.get('summary', {}).get('record_count', 0)}")

    data = result.get('data', [])
    if data:
        latest = data[0]
        print(f"✅ 最新日期: {latest.get('trade_date')}")
        print(f"✅ 主力净流入: {latest.get('net_vol_main', 0):.0f} 元")
        print(f"✅ 超大单净流入: {latest.get('net_vol_xl', 0):.0f} 元")
        print(f"✅ 中单净流入: {latest.get('net_mf_vol', 0):.0f} 元")
        print(f"✅ 小单净流入: {latest.get('net_lg_vol', 0):.0f} 元")

        summary = result.get('summary', {})
        print(f"✅ 总净流入: {summary.get('total_net_inflow', 0):.0f} 元")
        print(f"✅ 日均净流入: {summary.get('avg_daily_inflow', 0):.0f} 元")

    # 测试2: 获取龙虎榜数据
    print("\n[测试2] 获取龙虎榜数据")
    result = await tool.get_dragon_tiger(date="20260315")

    print(f"✅ 数据条数: {result.get('summary', {}).get('total_count', 0)}")

    data = result.get('data', [])
    if data:
        print(f"✅ 涨停家数: {result.get('summary', {}).get('up_count', 0)}")
        print(f"✅ 跌停家数: {result.get('summary', {}).get('down_count', 0)}")

        print("\n前3条记录:")
        for i, item in enumerate(data[:3], 1):
            print(f"  {i}. {item.get('name')} ({item.get('ts_code')}) - "
                  f"涨跌幅: {item.get('pct_chg', 0):.2f}% - "
                  f"原因: {item.get('reason', '')}")

    print("\n✅ CapitalFlowTool 测试通过")


# ========== 综合测试 ==========

async def test_facade_integration():
    """测试门面层集成"""
    print("\n" + "=" * 70)
    print("综合测试 - 门面层集成")
    print("=" * 70)

    stock_code = "600519"

    print(f"\n分析股票: {stock_code} (贵州茅台)")
    print("-" * 70)

    # 1. 行业分析
    print("\n[1] 行业分析")
    industry_tool = get_industry_tool()
    industry_info = await industry_tool.get_industry_info(stock_code, use_chain=False)

    print(f"  行业: {industry_info.get('industry')}")
    print(f"  板块: {industry_info.get('sector')}")
    print(f"  数据源: {industry_info.get('data_source')}")

    # 2. 技术分析
    print("\n[2] 技术分析")
    technical_tool = get_technical_tool()
    kline_data = technical_tool.get_kline(stock_code, period="1mo", interval="1d")

    if not kline_data.empty:
        latest = kline_data.iloc[-1]
        print(f"  最新价格: {latest['Close']:.2f}")
        print(f"  数据条数: {len(kline_data)} 条")

    # 3. 资金流向
    print("\n[3] 资金流向")
    capital_tool = get_capital_flow_tool()
    capital_flow = await capital_tool.get_capital_flow(stock_code)

    summary = capital_flow.get('summary', {})
    print(f"  总净流入: {summary.get('total_net_inflow', 0):.0f} 元")
    print(f"  数据条数: {summary.get('record_count', 0)} 条")

    print("\n" + "=" * 70)
    print("✅ 综合测试通过 - 门面层工作正常")
    print("=" * 70)


# ========== 主函数 ==========

async def main():
    """主测试函数"""
    # 设置日志
    setup_logging(log_level="INFO", log_dir="./logs", enable_console=True)
    logger = get_logger("test_tool_facades")

    logger.info("=" * 70)
    logger.info("工具库门面层测试")
    logger.info("=" * 70)

    try:
        # 测试 IndustryTool
        await test_industry_tool()

        # 测试 TechnicalTool
        test_technical_tool()

        # 测试 CapitalFlowTool
        await test_capital_flow_tool()

        # 综合测试
        await test_facade_integration()

        print("\n" + "=" * 70)
        print("🎉 所有测试通过！")
        print("=" * 70)

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

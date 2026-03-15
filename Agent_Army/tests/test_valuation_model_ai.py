"""
测试估值模型AI
"""
import pytest

import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.agents.business.stock.valuation_model_ai import ValuationModelAI


@pytest.mark.asyncio
async def test_valuation_model_ai():
    """测试估值模型AI"""
    print("=" * 70)
    print("估值模型AI测试")
    print("=" * 70)

    # 初始化AI
    ai = ValuationModelAI()

    # 测试股票代码
    test_stock = "600519"  # 贵州茅台

    print(f"\n测试股票: {test_stock}")
    print("-" * 70)

    # 测试1: PE估值
    print("\n[1] 测试PE估值")
    try:
        pe_result = await ai.pe_valuation(test_stock)
        print(f"股票名称: {pe_result.get('stock_name')}")
        print(f"EPS: {pe_result['data']['eps']}")
        print(f"合理PE倍数: {pe_result['data']['industry_pe_multiple']}")
        print(f"合理价值: {pe_result['valuation']['fair_value']}")
        print(f"当前价格: {pe_result['valuation']['current_price']}")
        print(f"上行空间: {pe_result['valuation']['upside']:.2%}")
        print(f"评级: {pe_result['valuation']['rating']}")
    except Exception as e:
        print(f"❌ PE估值失败: {e}")

    # 测试2: PB估值
    print("\n[2] 测试PB估值")
    try:
        pb_result = await ai.pb_valuation(test_stock)
        print(f"BVPS: {pb_result['data']['bvps']}")
        print(f"合理PB倍数: {pb_result['data']['industry_pb_multiple']}")
        print(f"合理价值: {pb_result['valuation']['fair_value']}")
        print(f"当前价格: {pb_result['valuation']['current_price']}")
        print(f"上行空间: {pb_result['valuation']['upside']:.2%}")
        print(f"评级: {pb_result['valuation']['rating']}")
    except Exception as e:
        print(f"❌ PB估值失败: {e}")

    # 测试3: DCF估值
    print("\n[3] 测试DCF估值")
    try:
        dcf_result = await ai.dcf_valuation(test_stock)
        print(f"自由现金流: {dcf_result['data']['free_cash_flow']}亿元")
        print(f"WACC: {dcf_result['data']['wacc']:.2%}")
        print(f"增长率: {dcf_result['data']['growth_rate']:.2%}")
        print(f"合理价值: {dcf_result['valuation']['fair_value']}")
        print(f"当前价格: {dcf_result['valuation']['current_price']}")
        print(f"上行空间: {dcf_result['valuation']['upside']:.2%}")
        print(f"评级: {dcf_result['valuation']['rating']}")
    except Exception as e:
        print(f"❌ DCF估值失败: {e}")

    # 测试4: PS估值
    print("\n[4] 测试PS估值")
    try:
        ps_result = await ai.ps_valuation(test_stock)
        print(f"营收: {ps_result['data']['revenue_billion']}亿元")
        print(f"当前PS: {ps_result['data']['current_ps']}")
        print(f"合理PS倍数: {ps_result['data']['industry_ps_multiple']}")
        print(f"合理价值: {ps_result['valuation']['fair_value']}")
        print(f"当前价格: {ps_result['valuation']['current_price']}")
        print(f"上行空间: {ps_result['valuation']['upside']:.2%}")
        print(f"评级: {ps_result['valuation']['rating']}")
    except Exception as e:
        print(f"❌ PS估值失败: {e}")

    # 测试5: 综合估值
    print("\n[5] 测试综合估值")
    try:
        composite_result = await ai.composite_valuation(test_stock)
        print(f"股票名称: {composite_result.get('stock_name')}")
        print(f"使用的模型: {composite_result['composite_valuation']['models_used']}")
        print(f"综合估值: {composite_result['composite_valuation']['composite_value']}")
        print(f"当前价格: {composite_result['composite_valuation']['current_price']}")
        print(f"上行空间: {composite_result['composite_valuation']['upside']:.2%}")
        print(f"评级: {composite_result['composite_valuation']['rating']}")
        print(f"\n权重分配:")
        for model, weight in composite_result['composite_valuation']['weights_applied'].items():
            print(f"  {model.upper()}: {weight:.0%}")
    except Exception as e:
        print(f"❌ 综合估值失败: {e}")

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_valuation_model_ai())

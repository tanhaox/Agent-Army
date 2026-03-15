"""
估值模型AI使用示例
演示如何使用ValuationModelAI进行股票估值分析
"""

import asyncio
import json
from src.agents.business.stock.valuation_model_ai import ValuationModelAI


async def example_single_stock():
    """示例1: 单股票估值分析"""
    print("=" * 70)
    print("示例1: 单股票估值分析")
    print("=" * 70)

    # 初始化AI
    ai = ValuationModelAI()

    # 分析贵州茅台
    stock_code = "600519"
    result = await ai.composite_valuation(stock_code)

    # 打印结果
    print(f"\n股票代码: {result['stock_code']}")
    print(f"股票名称: {result['stock_name']}")
    print(f"\n估值结果:")
    print(f"  综合估值: {result['composite_valuation']['composite_value']:.2f}元")
    print(f"  当前价格: {result['composite_valuation']['current_price']:.2f}元")
    print(f"  上行空间: {result['composite_valuation']['upside']:.2%}")
    print(f"  投资评级: {result['composite_valuation']['rating']}")

    print(f"\n各模型估值:")
    for model_name, model_data in result['valuation_models'].items():
        if model_data:
            print(f"  {model_name}:")
            print(f"    合理价值: {model_data['valuation']['fair_value']:.2f}元")
            print(f"    评级: {model_data['valuation']['rating']}")


async def example_multiple_stocks():
    """示例2: 批量股票估值"""
    print("\n" + "=" * 70)
    print("示例2: 批量股票估值")
    print("=" * 70)

    ai = ValuationModelAI()

    # 分析多只股票
    stock_list = ["600519", "000858", "600036"]  # 茅台、五粮液、招商银行

    results = []
    for stock_code in stock_list:
        try:
            result = await ai.composite_valuation(stock_code)
            results.append(result)
            print(f"\n{stock_code}: {result['stock_name']}")
            print(f"  综合估值: {result['composite_valuation']['composite_value']:.2f}")
            print(f"  评级: {result['composite_valuation']['rating']}")
        except Exception as e:
            print(f"\n{stock_code}: 估值失败 - {e}")

    # 找出最具投资价值的股票
    print("\n最具投资价值排序:")
    results.sort(key=lambda x: x['composite_valuation']['upside'], reverse=True)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['stock_code']} - {result['stock_name']}")
        print(f"   上行空间: {result['composite_valuation']['upside']:.2%}")


async def example_pe_only():
    """示例3: 仅使用PE估值"""
    print("\n" + "=" * 70)
    print("示例3: 仅使用PE估值")
    print("=" * 70)

    ai = ValuationModelAI()

    stock_code = "600519"
    result = await ai.pe_valuation(stock_code)

    print(f"\n股票: {result['stock_name']}")
    print(f"PE估值分析:")
    print(f"  每股收益(EPS): {result['data']['eps']:.2f}元")
    print(f"  合理PE倍数: {result['data']['industry_pe_multiple']:.2f}")
    print(f"  合理价值: {result['valuation']['fair_value']:.2f}元")
    print(f"  当前价格: {result['valuation']['current_price']:.2f}元")
    print(f"  上行空间: {result['valuation']['upside']:.2%}")
    print(f"  评级: {result['valuation']['rating']}")


async def example_export_json():
    """示例4: 导出JSON格式"""
    print("\n" + "=" * 70)
    print("示例4: 导出JSON格式")
    print("=" * 70)

    ai = ValuationModelAI()

    stock_code = "600519"
    result = await ai.composite_valuation(stock_code)

    # 转换为JSON并保存
    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    # 保存到文件
    filename = f"valuation_{stock_code}_{result['timestamp'][:10]}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_str)

    print(f"\n估值结果已保存到: {filename}")
    print(f"\nJSON预览:")
    print(json_str[:500] + "...")


async def main():
    """运行所有示例"""
    await example_single_stock()
    await example_multiple_stocks()
    await example_pe_only()
    await example_export_json()

    print("\n" + "=" * 70)
    print("所有示例运行完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

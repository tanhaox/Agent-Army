"""
预测部Agent演示脚本

演示3个预测部Agent的实际运行效果
"""

import asyncio
from src.agents.business.prediction import (
    ValuationPricingAI,
    ComprehensiveEvaluationAI,
    PriceForecastAI
)


async def demo_valuation_pricing():
    """演示估值定价AI"""
    print("\n" + "=" * 60)
    print("1. 估值定价AI演示")
    print("=" * 60)

    agent = ValuationPricingAI()
    result = await agent.analyze(
        stock_code="600519",
        current_price=50.0,
        prediction_period="12m"
    )

    print(f"\n【核心结论】{result.conclusion}")
    print(f"【置信度】{result.confidence * 100:.0f}%")
    print(f"\n【目标定价】")
    target_pricing = result.details["target_pricing"]
    print(f"  目标价: {target_pricing['target_price']}元")
    print(f"  上涨空间: {target_pricing['upside']:.1f}%")
    print(f"  价格区间: {target_pricing['price_range']['lower']}-{target_pricing['price_range']['upper']}元")

    print(f"\n【估值建议】")
    valuation_advice = result.details["valuation_advice"]
    print(f"  评级: {valuation_advice['rating']}")
    print(f"  操作: {valuation_advice['action']}")
    print(f"  建议: {valuation_advice['recommendations'][0]}")

    print(f"\n【风险提示】")
    for risk in result.risks[:3]:
        print(f"  [!] {risk}")


async def demo_comprehensive_evaluation():
    """演示综合评估AI"""
    print("\n" + "=" * 60)
    print("2. 综合评估AI演示")
    print("=" * 60)

    agent = ComprehensiveEvaluationAI()

    # 模拟输入数据
    research_data = {
        "industry": "白酒",
        "market_position": "领先"
    }
    analysis_data = {
        "fundamental": "优秀",
        "growth": "强劲"
    }
    prediction_data = {
        "target_price": 60.0,
        "confidence": 0.8
    }

    result = await agent.analyze(
        stock_code="600519",
        research_data=research_data,
        analysis_data=analysis_data,
        prediction_data=prediction_data
    )

    print(f"\n【核心结论】{result.conclusion}")
    print(f"【置信度】{result.confidence * 100:.0f}%")

    print(f"\n【综合评分】")
    comprehensive_score = result.details["comprehensive_score"]
    print(f"  综合得分: {comprehensive_score}分")

    print(f"\n【维度评分】")
    dimension_scores = result.details["dimension_scores"]
    for dim_name, dim_data in dimension_scores.items():
        print(f"  {dim_data['description']}: {dim_data['score']}分（权重{dim_data['weight']*100:.0f}%）")

    print(f"\n【质量评估】")
    quality_assessment = result.details["quality_assessment"]
    print(f"  质量等级: {quality_assessment['quality_grade']}（{quality_assessment['quality_description']}）")
    print(f"  优势: {quality_assessment['strengths'][0]}")
    print(f"  劣势: {quality_assessment['weaknesses'][0]}")

    print(f"\n【投资评级】")
    investment_rating = result.details["investment_rating"]
    print(f"  评级: {investment_rating['rating']}")
    print(f"  操作: {investment_rating['action']}")
    print(f"  风险: {investment_rating['risk_level']}")


async def demo_price_forecast():
    """演示预测AI"""
    print("\n" + "=" * 60)
    print("3. 预测AI演示")
    print("=" * 60)

    agent = PriceForecastAI()
    result = await agent.analyze(
        stock_code="600519",
        current_price=50.0,
        forecast_period="12m"
    )

    print(f"\n【核心结论】{result.conclusion}")
    print(f"【置信度】{result.confidence * 100:.0f}%")

    print(f"\n【价格预测】")
    price_forecast = result.details["price_forecast"]
    print(f"  预测价格: {price_forecast['forecast_price']}元")
    print(f"  上涨空间: {price_forecast['upside']:.1f}%")
    print(f"  价格区间: {price_forecast['price_range']['lower']}-{price_forecast['price_range']['upper']}元")
    print(f"  趋势: {price_forecast['trend']}")

    print(f"\n【利润预测】")
    profit_forecast = result.details["profit_forecast"]
    print(f"  预测利润: {profit_forecast['forecast_profit']}亿元")
    print(f"  利润增长: {profit_forecast['profit_growth']:.1f}%")
    print(f"  预测EPS: {profit_forecast['forecast_eps']}元")

    print(f"\n【趋势预测】")
    trend_forecast = result.details["trend_forecast"]
    print(f"  趋势强度: {trend_forecast['trend_strength']}")
    print(f"  趋势质量: {trend_forecast['trend_quality']}")
    print(f"  可持续性: {trend_forecast['sustainability']}")

    print(f"\n【情景分析】")
    scenario_analysis = result.details["scenario_analysis"]
    print(f"  乐观情景: {scenario_analysis['optimistic']['price']}元（概率{scenario_analysis['optimistic']['probability']*100:.0f}%）")
    print(f"  中性情景: {scenario_analysis['neutral']['price']}元（概率{scenario_analysis['neutral']['probability']*100:.0f}%）")
    print(f"  悲观情景: {scenario_analysis['pessimistic']['price']}元（概率{scenario_analysis['pessimistic']['probability']*100:.0f}%）")
    print(f"  期望值: {scenario_analysis['expected_value']}元")

    print(f"\n【风险提示】")
    for risk in result.risks[:3]:
        print(f"  [!] {risk}")


async def main():
    """主演示函数"""
    print("\n" + "=" * 60)
    print("  Agent Army - 预测部演示")
    print("  8部门制精简架构（24个Agent）")
    print("=" * 60)

    await demo_valuation_pricing()
    await demo_comprehensive_evaluation()
    await demo_price_forecast()

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

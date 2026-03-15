"""
完整投资分析流程演示

演示6个军团协同工作，完成一次完整的投资分析
"""

import sys
import os
from pathlib import Path

# Windows控制台UTF-8编码支持
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI
from src.agents.business.industry_analysis.competition_pattern_ai import CompetitionPatternAI
from src.agents.business.stock.financial_health_ai import FinancialHealthAI
from src.agents.business.target.comprehensive_score_ai import ComprehensiveScoreAI
from src.agents.business.strategy.risk_control_ai import RiskControlAI
from src.agents.business.validation.backtest_analysis_ai import BacktestAnalysisAI


async def main():
    """完整投资分析流程"""
    stock_code = "600519"  # 贵州茅台
    investment_amount = 100000  # 10万元

    print("\n" + "╔"+"═"*70+"╗")
    print("║" + " "*20 + "🚀 Agent Army 投资分析系统" + " "*20 + "║")
    print("║" + " "*25 + "完整流程演示" + " "*25 + "║")
    print("╚"+"═"*70+"╝")

    print(f"\n📊 分析目标: {stock_code}（贵州茅台）")
    print(f"💰 投资金额: {investment_amount:,}元")

    # ========== 第1步：热点捕捉 ==========
    print("\n" + "="*70)
    print("【第1步】热点捕捉军团 - 市场情绪分析")
    print("="*70)

    sentiment_ai = MarketSentimentAI()
    sentiment_result = await sentiment_ai.execute(
        "analyze_sentiment",
        stock_code=stock_code,
        time_range="1d"
    )

    print(f"\n📈 市场情绪分析结果:")
    print(f"   情绪指数: {sentiment_result['sentiment_index']}")
    print(f"   情绪评级: {sentiment_result['sentiment_rating']}")
    print(f"   新闻数量: {sentiment_result['news_count']}")
    print(f"   建议: {sentiment_result['recommendation']}")

    # ========== 第2步：产业分析 ==========
    print("\n" + "="*70)
    print("【第2步】产业分析军团 - 竞争格局分析")
    print("="*70)

    competition_ai = CompetitionPatternAI()
    # 假设白酒行业代码
    competition_result = await competition_ai.execute(
        "analyze_competition",
        industry_code="BZ001",
        time_range="1y"
    )

    print(f"\n🏭 竞争格局分析结果:")
    print(f"   市场集中度: {competition_result['concentration']['cr4']:.1f}%")
    print(f"   竞争态势: {competition_result['competition_status']['status']}")
    print(f"   竞争强度: {competition_result['competition_status']['intensity']}")
    print(f"   建议: {competition_result['recommendation']}")

    # ========== 第3步：个股挖掘 ==========
    print("\n" + "="*70)
    print("【第3步】个股挖掘军团 - 财务健康分析")
    print("="*70)

    financial_ai = FinancialHealthAI()
    financial_result = await financial_ai.execute(
        "analyze_health",
        stock_code=stock_code,
        years=3
    )

    print(f"\n💰 财务健康分析结果:")
    print(f"   健康度评分: {financial_result['health_score']}")
    print(f"   健康度等级: {financial_result['health_grade']}")
    print(f"   偿债能力: {financial_result['health_metrics']['偿债能力']['status']}")
    print(f"   盈利能力: {financial_result['health_metrics']['盈利能力']['status']}")
    print(f"   建议: {financial_result['recommendation']}")

    # ========== 第4步：目标预测 ==========
    print("\n" + "="*70)
    print("【第4步】目标预测军团 - 综合评分")
    print("="*70)

    score_ai = ComprehensiveScoreAI()
    score_result = await score_ai.execute(
        "calculate_score",
        stock_code=stock_code
    )

    print(f"\n⭐ 综合评分结果:")
    print(f"   综合评分: {score_result['comprehensive_score']}")
    print(f"   评级: {score_result['rating']}")
    print(f"\n   各维度评分:")
    for dim_name, dim_data in score_result['dimension_scores'].items():
        print(f"      {dim_name}: {dim_data['score']}分 (权重{dim_data['weight']*100:.0f}%)")
    print(f"\n   建议: {score_result['recommendation']}")

    # ========== 第5步：策略执行 ==========
    print("\n" + "="*70)
    print("【第5步】策略执行军团 - 风险控制")
    print("="*70)

    risk_ai = RiskControlAI()

    # 评估投资风险
    risk_result = await risk_ai.execute(
        "assess_risk",
        stock_code=stock_code,
        investment_amount=investment_amount
    )

    print(f"\n⚠️ 风险评估结果:")
    print(f"   风险等级: {risk_result['risk_level']}")
    print(f"   风险评分: {risk_result['risk_score']}")
    print(f"   最大损失估算: {risk_result['max_loss_estimate']['estimated_max_loss_amount']:.0f}元")
    print(f"   最大损失率: {risk_result['max_loss_estimate']['estimated_max_loss_rate']:.1f}%")
    print(f"   建议: {risk_result['suggestion']}")

    # 设置风险策略
    strategy_result = await risk_ai.execute(
        "set_strategy",
        risk_preference="moderate",
        investment_amount=investment_amount
    )

    print(f"\n📋 风险控制策略:")
    print(f"   策略类型: {strategy_result['strategy']['name']}")
    print(f"   单只最大仓位: {strategy_result['strategy']['单只股票最大仓位']}")
    print(f"   止损线: {strategy_result['strategy']['止损线']}")
    print(f"   止盈线: {strategy_result['strategy']['止盈线']}")

    # ========== 第6步：结果验证 ==========
    print("\n" + "="*70)
    print("【第6步】结果验证军团 - 回测分析")
    print("="*70)

    backtest_ai = BacktestAnalysisAI()
    backtest_result = await backtest_ai.execute(
        "run_backtest",
        strategy_name="综合策略",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=investment_amount
    )

    print(f"\n📊 回测分析结果:")
    print(f"   总收益: {backtest_result['performance']['total_return']:.2f}%")
    print(f"   年化收益: {backtest_result['performance']['annualized_return']:.2f}%")
    print(f"   夏普比率: {backtest_result['risk_metrics']['sharpe_ratio']:.2f}")
    print(f"   最大回撤: {backtest_result['risk_metrics']['max_drawdown']:.2f}%")
    print(f"   评估: {backtest_result['evaluation']}")

    # ========== 最终决策 ==========
    print("\n" + "╔"+"═"*70+"╗")
    print("║" + " "*25 + "📊 最终投资决策" + " "*25 + "║")
    print("╚"+"═"*70+"╝")

    print(f"\n【综合分析】")
    print(f"   市场情绪: {sentiment_result['sentiment_rating']}")
    print(f"   行业竞争: {competition_result['competition_status']['status']}")
    print(f"   财务健康: {financial_result['health_grade']}级")
    print(f"   综合评分: {score_result['comprehensive_score']}分（{score_result['rating']}）")
    print(f"   风险等级: {risk_result['risk_level']}")

    print(f"\n【投资建议】")

    # 综合决策逻辑
    decision_score = 0

    # 情绪加分
    if sentiment_result['sentiment_index'] >= 55:
        decision_score += 1

    # 财务加分
    if financial_result['health_score'] >= 65:
        decision_score += 2

    # 综合评分加分
    if score_result['comprehensive_score'] >= 75:
        decision_score += 2
    elif score_result['comprehensive_score'] >= 65:
        decision_score += 1

    # 风险减分
    if risk_result['risk_level'] in ["极高风险", "高风险"]:
        decision_score -= 1

    # 给出最终建议
    if decision_score >= 4:
        final_decision = "✅ 建议投资"
        action = "可以建仓，建议分批买入"
    elif decision_score >= 2:
        final_decision = "⚠️ 谨慎投资"
        action = "可以小仓位尝试，严格止损"
    else:
        final_decision = "❌ 不建议投资"
        action = "建议观望或寻找其他机会"

    print(f"   决策评分: {decision_score}/5")
    print(f"   最终决策: {final_decision}")
    print(f"   操作建议: {action}")

    print(f"\n【风险提示】")
    print(f"   ⚠️ 最大可能损失: {risk_result['max_loss_estimate']['estimated_max_loss_amount']:.0f}元")
    print(f"   ⚠️ 建议止损位: {strategy_result['risk_limits']['止损金额']:.0f}元")
    print(f"   ⚠️ 单只最大金额: {strategy_result['risk_limits']['单只最大金额']:.0f}元")

    print("\n" + "╔"+"═"*70+"╗")
    print("║" + " "*20 + "✅ 分析完成！感谢使用 Agent Army" + " "*19 + "║")
    print("╚"+"═"*70+"╝")


if __name__ == "__main__":
    asyncio.run(main())

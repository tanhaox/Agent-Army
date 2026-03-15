"""
回测分析AI - Backtest Analysis AI

职责：
- 回测投资策略
- 分析历史表现
- 评估策略有效性

输入：
- 策略参数
- 回测周期

输出：
- 回测报告
- 收益统计
- 风险指标
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class BacktestAnalysisAI(BaseAgent, LoggerMixin):
    """回测分析AI - 回测投资策略"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="回测分析AI",
            role="回测投资策略，分析历史表现，评估策略有效性",
            capabilities=[
                AgentCapability(
                    name="strategy_backtest",
                    description="策略回测",
                    input_type="strategy_params",
                    output_type="backtest_report"
                ),
                AgentCapability(
                    name="performance_analysis",
                    description="表现分析",
                    input_type="backtest_data",
                    output_type="performance_report"
                ),
                AgentCapability(
                    name="strategy_evaluation",
                    description="策略评估",
                    input_type="strategy_results",
                    output_type="evaluation_report"
                )
            ],
            tools=[
                AgentTool(
                    name="backtest_engine",
                    description="回测引擎工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("回测分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "run_backtest":
            return await self.run_backtest(
                kwargs.get("strategy_name"),
                kwargs.get("start_date"),
                kwargs.get("end_date"),
                kwargs.get("initial_capital", 1000000)
            )
        elif task == "analyze_performance":
            return await self.analyze_performance(
                kwargs.get("backtest_data")
            )
        elif task == "evaluate_strategy":
            return await self.evaluate_strategy(
                kwargs.get("strategy_name"),
                kwargs.get("backtest_period", "1y")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def run_backtest(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000
    ) -> Dict[str, Any]:
        """运行策略回测"""
        self.logger.info(
            f"开始策略回测",
            extra={
                "strategy": strategy_name,
                "start": start_date,
                "end": end_date
            }
        )

        # 1. 获取回测数据
        backtest_data = await self._generate_backtest_data(
            start_date,
            end_date,
            initial_capital
        )

        # 2. 计算收益指标
        performance = self._calculate_performance(backtest_data, initial_capital)

        # 3. 计算风险指标
        risk_metrics = self._calculate_risk_metrics(backtest_data)

        # 4. 生成回测报告
        report = {
            "strategy_name": strategy_name,
            "timestamp": datetime.now().isoformat(),
            "backtest_period": f"{start_date} 至 {end_date}",
            "initial_capital": initial_capital,
            "final_capital": backtest_data[-1]["capital"],
            "performance": performance,
            "risk_metrics": risk_metrics,
            "trade_count": len([d for d in backtest_data if d.get("trade")]),
            "summary": self._generate_backtest_summary(performance, risk_metrics),
            "evaluation": self._evaluate_backtest_result(performance, risk_metrics)
        }

        self.logger.info(
            f"策略回测完成",
            extra={
                "strategy": strategy_name,
                "return": performance["total_return"]
            }
        )

        return report

    async def analyze_performance(
        self,
        backtest_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """分析回测表现"""
        self.logger.info("开始分析回测表现")

        # 如果没有提供数据，生成示例数据
        if not backtest_data:
            backtest_data = await self._generate_backtest_data(
                "2023-01-01",
                "2023-12-31",
                1000000
            )

        # 分析月度表现
        monthly_performance = self._analyze_monthly_performance(backtest_data)

        # 分析胜率
        win_rate_analysis = self._analyze_win_rate(backtest_data)

        # 分析回撤
        drawdown_analysis = self._analyze_drawdown(backtest_data)

        return {
            "timestamp": datetime.now().isoformat(),
            "monthly_performance": monthly_performance,
            "win_rate_analysis": win_rate_analysis,
            "drawdown_analysis": drawdown_analysis,
            "summary": self._generate_performance_summary(
                monthly_performance,
                win_rate_analysis,
                drawdown_analysis
            )
        }

    async def evaluate_strategy(
        self,
        strategy_name: str,
        backtest_period: str = "1y"
    ) -> Dict[str, Any]:
        """评估策略有效性"""
        self.logger.info(
            f"评估策略有效性",
            extra={"strategy": strategy_name}
        )

        # 运行回测
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 if backtest_period == "1y" else 180)

        backtest_result = await self.run_backtest(
            strategy_name,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        # 评估策略
        evaluation = {
            "strategy_name": strategy_name,
            "timestamp": datetime.now().isoformat(),
            "overall_rating": self._rate_strategy(backtest_result),
            "strengths": self._identify_strengths(backtest_result),
            "weaknesses": self._identify_weaknesses(backtest_result),
            "suitability": self._assess_suitability(backtest_result),
            "recommendation": self._generate_strategy_recommendation(backtest_result)
        }

        return evaluation

    # ========== 辅助方法 ==========

    async def _generate_backtest_data(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float
    ) -> List[Dict[str, Any]]:
        """生成回测数据（模拟）"""
        import random

        data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        capital = initial_capital

        while current_date <= end:
            # 模拟每日收益
            daily_return = random.uniform(-0.03, 0.03)
            capital = capital * (1 + daily_return)

            # 模拟交易
            trade = None
            if random.random() < 0.1:  # 10%概率有交易
                trade = {
                    "type": "buy" if random.random() < 0.6 else "sell",
                    "stock": f"股票{random.randint(1, 10)}",
                    "amount": random.randint(100, 1000),
                    "price": round(random.uniform(10, 100), 2)
                }

            data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "capital": round(capital, 2),
                "daily_return": round(daily_return * 100, 2),
                "trade": trade
            })

            current_date += timedelta(days=1)

        return data

    def _calculate_performance(
        self,
        backtest_data: List[Dict[str, Any]],
        initial_capital: float
    ) -> Dict[str, Any]:
        """计算收益指标"""
        final_capital = backtest_data[-1]["capital"]
        total_return = ((final_capital - initial_capital) / initial_capital) * 100

        # 计算年化收益
        days = len(backtest_data)
        annualized_return = ((final_capital / initial_capital) ** (365 / days) - 1) * 100

        # 计算平均日收益
        daily_returns = [d["daily_return"] for d in backtest_data]
        avg_daily_return = sum(daily_returns) / len(daily_returns)

        return {
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized_return, 2),
            "avg_daily_return": round(avg_daily_return, 2),
            "final_capital": round(final_capital, 2),
            "profit": round(final_capital - initial_capital, 2)
        }

    def _calculate_risk_metrics(
        self,
        backtest_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算风险指标"""
        daily_returns = [d["daily_return"] for d in backtest_data]

        # 计算波动率（标准差）
        avg_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
        volatility = (variance ** 0.5) * (252 ** 0.5)  # 年化波动率

        # 计算最大回撤
        capitals = [d["capital"] for d in backtest_data]
        max_drawdown = 0
        peak = capitals[0]

        for capital in capitals:
            if capital > peak:
                peak = capital
            drawdown = (peak - capital) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 计算夏普比率（假设无风险利率3%）
        annualized_return = ((capitals[-1] / capitals[0]) ** (365 / len(capitals)) - 1) * 100
        sharpe_ratio = (annualized_return - 3) / volatility if volatility > 0 else 0

        return {
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2)
        }

    def _analyze_monthly_performance(
        self,
        backtest_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析月度表现"""
        monthly_data = {}

        for day_data in backtest_data:
            month = day_data["date"][:7]  # YYYY-MM
            if month not in monthly_data:
                monthly_data[month] = {
                    "month": month,
                    "start_capital": day_data["capital"],
                    "end_capital": day_data["capital"],
                    "trade_count": 0
                }
            monthly_data[month]["end_capital"] = day_data["capital"]
            if day_data.get("trade"):
                monthly_data[month]["trade_count"] += 1

        # 计算月度收益
        result = []
        for month_data in monthly_data.values():
            monthly_return = (
                (month_data["end_capital"] - month_data["start_capital"]) /
                month_data["start_capital"] * 100
            )
            result.append({
                "month": month_data["month"],
                "return": round(monthly_return, 2),
                "trade_count": month_data["trade_count"]
            })

        return result

    def _analyze_win_rate(
        self,
        backtest_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析胜率"""
        positive_days = sum(1 for d in backtest_data if d["daily_return"] > 0)
        negative_days = sum(1 for d in backtest_data if d["daily_return"] < 0)
        total_days = len(backtest_data)

        win_rate = (positive_days / total_days * 100) if total_days > 0 else 0

        return {
            "win_days": positive_days,
            "loss_days": negative_days,
            "win_rate": round(win_rate, 2),
            "avg_win": round(
                sum(d["daily_return"] for d in backtest_data if d["daily_return"] > 0) /
                positive_days if positive_days > 0 else 0,
                2
            ),
            "avg_loss": round(
                sum(d["daily_return"] for d in backtest_data if d["daily_return"] < 0) /
                negative_days if negative_days > 0 else 0,
                2
            )
        }

    def _analyze_drawdown(
        self,
        backtest_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析回撤"""
        capitals = [d["capital"] for d in backtest_data]
        drawdowns = []
        peak = capitals[0]
        peak_date = backtest_data[0]["date"]

        for i, capital in enumerate(capitals):
            if capital > peak:
                peak = capital
                peak_date = backtest_data[i]["date"]

            drawdown = (peak - capital) / peak * 100
            if drawdown > 0:
                drawdowns.append({
                    "date": backtest_data[i]["date"],
                    "drawdown": round(drawdown, 2),
                    "from_peak": round(peak, 2),
                    "current": round(capital, 2)
                })

        max_drawdown = max((d["drawdown"] for d in drawdowns), default=0)

        return {
            "max_drawdown": round(max_drawdown, 2),
            "drawdown_count": len(drawdowns),
            "avg_drawdown": round(
                sum(d["drawdown"] for d in drawdowns) / len(drawdowns)
                if drawdowns else 0,
                2
            )
        }

    def _rate_strategy(self, backtest_result: Dict[str, Any]) -> str:
        """评级策略"""
        total_return = backtest_result["performance"]["total_return"]
        sharpe = backtest_result["risk_metrics"]["sharpe_ratio"]
        max_dd = backtest_result["risk_metrics"]["max_drawdown"]

        # 综合评分
        score = 0
        if total_return > 20:
            score += 3
        elif total_return > 10:
            score += 2
        elif total_return > 0:
            score += 1

        if sharpe > 1.5:
            score += 3
        elif sharpe > 1.0:
            score += 2
        elif sharpe > 0.5:
            score += 1

        if max_dd < 10:
            score += 3
        elif max_dd < 20:
            score += 2
        elif max_dd < 30:
            score += 1

        # 评级
        if score >= 8:
            return "A+"
        elif score >= 6:
            return "A"
        elif score >= 4:
            return "B"
        elif score >= 2:
            return "C"
        else:
            return "D"

    def _identify_strengths(self, backtest_result: Dict[str, Any]) -> List[str]:
        """识别优势"""
        strengths = []

        if backtest_result["performance"]["total_return"] > 15:
            strengths.append(f"收益率优秀（{backtest_result['performance']['total_return']:.1f}%）")

        if backtest_result["risk_metrics"]["sharpe_ratio"] > 1.0:
            strengths.append(f"夏普比率良好（{backtest_result['risk_metrics']['sharpe_ratio']:.2f}）")

        if backtest_result["risk_metrics"]["max_drawdown"] < 15:
            strengths.append(f"风险控制优秀（最大回撤{backtest_result['risk_metrics']['max_drawdown']:.1f}%）")

        return strengths if strengths else ["无明显优势"]

    def _identify_weaknesses(self, backtest_result: Dict[str, Any]) -> List[str]:
        """识别劣势"""
        weaknesses = []

        if backtest_result["performance"]["total_return"] < 5:
            weaknesses.append(f"收益率偏低（{backtest_result['performance']['total_return']:.1f}%）")

        if backtest_result["risk_metrics"]["sharpe_ratio"] < 0.5:
            weaknesses.append(f"夏普比率较低（{backtest_result['risk_metrics']['sharpe_ratio']:.2f}）")

        if backtest_result["risk_metrics"]["max_drawdown"] > 25:
            weaknesses.append(f"风险较大（最大回撤{backtest_result['risk_metrics']['max_drawdown']:.1f}%）")

        return weaknesses if weaknesses else ["无明显劣势"]

    def _assess_suitability(self, backtest_result: Dict[str, Any]) -> str:
        """评估适用性"""
        total_return = backtest_result["performance"]["total_return"]
        max_dd = backtest_result["risk_metrics"]["max_drawdown"]

        if total_return > 15 and max_dd < 15:
            return "适合稳健型投资者"
        elif total_return > 20 and max_dd < 25:
            return "适合平衡型投资者"
        elif total_return > 30:
            return "适合激进型投资者"
        else:
            return "建议谨慎使用"

    def _generate_strategy_recommendation(self, backtest_result: Dict[str, Any]) -> str:
        """生成策略建议"""
        rating = backtest_result.get("rating", "C")

        if rating in ["A+", "A"]:
            return "策略表现优秀，建议实盘使用"
        elif rating == "B":
            return "策略表现良好，可以小资金尝试"
        elif rating == "C":
            return "策略表现一般，建议优化后再使用"
        else:
            return "策略表现较差，不建议实盘使用"

    def _generate_backtest_summary(
        self,
        performance: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> str:
        """生成回测摘要"""
        return (
            f"总收益{performance['total_return']:.2f}%，"
            f"年化收益{performance['annualized_return']:.2f}%，"
            f"夏普比率{risk_metrics['sharpe_ratio']:.2f}，"
            f"最大回撤{risk_metrics['max_drawdown']:.2f}%"
        )

    def _evaluate_backtest_result(
        self,
        performance: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> str:
        """评估回测结果"""
        if performance["total_return"] > 15 and risk_metrics["sharpe_ratio"] > 1.0:
            return "策略表现优秀"
        elif performance["total_return"] > 0 and risk_metrics["sharpe_ratio"] > 0.5:
            return "策略表现良好"
        else:
            return "策略需要改进"

    def _generate_performance_summary(
        self,
        monthly_performance: List[Dict[str, Any]],
        win_rate_analysis: Dict[str, Any],
        drawdown_analysis: Dict[str, Any]
    ) -> str:
        """生成表现摘要"""
        return (
            f"胜率{win_rate_analysis['win_rate']:.1f}%，"
            f"最大回撤{drawdown_analysis['max_drawdown']:.1f}%，"
            f"平均盈利{win_rate_analysis['avg_win']:.2f}%，"
            f"平均亏损{win_rate_analysis['avg_loss']:.2f}%"
        )

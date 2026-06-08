"""
验证回测AI - Validation and Backtest AI

验证部成员 (1/2)

职责：
1. 预测验证 - 验证预测模型的准确性
2. 回测分析 - 历史数据回测分析

合并来源：
- 预测验证AI
- 回测分析AI

使用工具：
- FinancialTool（历史数据）
- LLMTool（智能分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from src.agents.business.base_business_agent import BusinessAgent, AnalysisResult
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import get_logger


class ValidationBacktestAI(BusinessAgent):
    """
    验证回测AI - 验证部成员 (1/2)

    核心能力:
    1. 预测验证 - 验证预测准确率
    2. 回测分析 - 历史表现分析

    使用工具:
    - FinancialTool (历史数据)
    - LLMTool (智能分析)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="验证回测AI",
            role="验证预测准确性，分析历史回测表现",
            corps="validation",
            analysis_type="validation_backtest",
            capabilities=[
                AgentCapability(
                    name="prediction_validation",
                    description="预测验证",
                    input_type="stock_code",
                    output_type="validation_accuracy"
                ),
                AgentCapability(
                    name="backtest_analysis",
                    description="回测分析",
                    input_type="stock_code",
                    output_type="backtest_results"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="历史数据工具",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="llm_tool",
                    description="智能分析工具",
                    tool_type="ai_service",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("验证回测AI初始化完成")

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行验证回测分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - predictions: 历史预测数据（必需）
                - actual_prices: 实际价格数据（必需）
                - backtest_period: 回测周期（默认1y）

        Returns:
            分析结果
        """
        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        predictions = kwargs.get("predictions")
        if not predictions:
            raise ValueError("缺少predictions参数")

        actual_prices = kwargs.get("actual_prices")
        if not actual_prices:
            raise ValueError("缺少actual_prices参数")

        backtest_period = kwargs.get("backtest_period", "1y")

        self.logger.info(
            f"开始验证回测分析",
            extra={
                "stock_code": stock_code,
                "backtest_period": backtest_period,
                "predictions_count": len(predictions) if isinstance(predictions, list) else 1
            }
        )

        # ========== 1. 预测准确性验证 ==========
        validation_metrics = await self._validate_predictions(
            predictions,
            actual_prices
        )

        # ========== 2. 回测分析 ==========
        backtest_results = await self._run_backtest(
            predictions,
            actual_prices
        )

        # ========== 3. 改进建议生成 ==========
        improvement_suggestions = self._generate_improvements(
            validation_metrics,
            backtest_results
        )

        # ========== 4. 风险识别 ==========
        risks = self._identify_validation_risks(
            validation_metrics,
            backtest_results
        )

        # ========== 5. 构建分析结果 ==========
        details = {
            "stock_code": stock_code,
            "backtest_period": backtest_period,

            # 验证指标
            "validation_metrics": validation_metrics,

            # 回测结果
            "backtest_results": backtest_results,

            # 改进建议
            "improvements": improvement_suggestions,

            # 时间戳
            "timestamp": datetime.now().isoformat()
        }

        result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(validation_metrics, backtest_results),
            confidence=validation_metrics["overall_accuracy"],
            details=details,
            risks=risks,
            recommendations=improvement_suggestions
        )

        self.logger.info(
            f"验证回测分析完成",
            extra={
                "stock_code": stock_code,
                "accuracy": validation_metrics["overall_accuracy"],
                "total_return": backtest_results["total_return"]
            }
        )

        return result

    # ========== 核心验证方法 ==========

    async def _validate_predictions(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证预测准确性

        Args:
            predictions: 预测数据列表
            actual_prices: 实际价格数据列表

        Returns:
            验证指标
        """
        # TODO: 接入真实历史数据
        # 当前使用模拟数据

        # 1. 准确率计算
        accuracy_metrics = self._calculate_accuracy(predictions, actual_prices)

        # 2. 方向性预测准确率
        direction_accuracy = self._calculate_direction_accuracy(predictions, actual_prices)

        # 3. 误差分布分析
        error_distribution = self._analyze_error_distribution(predictions, actual_prices)

        # 4. 置信度校准
        confidence_calibration = self._calibrate_confidence(predictions, actual_prices)

        return {
            "overall_accuracy": accuracy_metrics["overall_accuracy"],
            "mae": accuracy_metrics["mae"],
            "rmse": accuracy_metrics["rmse"],
            "mape": accuracy_metrics["mape"],
            "direction_accuracy": direction_accuracy,
            "error_distribution": error_distribution,
            "confidence_calibration": confidence_calibration
        }

    async def _run_backtest(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        运行回测分析

        Args:
            predictions: 预测数据
            actual_prices: 实际价格

        Returns:
            回测结果
        """
        # TODO: 实现真实回测逻辑
        # 模拟回测数据

        # 假设回测参数
        initial_capital = 100000  # 初始资金
        position_size = 0.95  # 仓位比例

        # 模拟交易信号
        trades = self._generate_trades(predictions, actual_prices)

        # 计算收益
        total_return = self._calculate_total_return(trades, initial_capital)

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(trades)

        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio(trades)

        # 胜率分析
        win_rate = self._calculate_win_rate(trades)

        # 盈亏比
        profit_loss_ratio = self._calculate_profit_loss_ratio(trades)

        return {
            "initial_capital": initial_capital,
            "final_capital": initial_capital * (1 + total_return),
            "total_return": total_return,
            "annualized_return": self._annualize_return(total_return, period="1y"),
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "total_trades": len(trades),
            "winning_trades": sum(1 for t in trades if t["pnl"] > 0),
            "losing_trades": sum(1 for t in trades if t["pnl"] < 0)
        }

    # ========== 准确率计算 ==========

    def _calculate_accuracy(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算预测准确率"""
        # TODO: 接入真实数据
        # 模拟计算结果

        # 假设有10个预测点
        n = len(predictions)

        # 模拟误差
        errors = [(p.get("target_price", 50) - a.get("price", 50))
                  for p, a in zip(predictions, actual_prices)]

        # 平均绝对误差 (MAE)
        mae = sum(abs(e) for e in errors) / n

        # 均方根误差 (RMSE)
        rmse = (sum(e ** 2 for e in errors) / n) ** 0.5

        # 平均绝对百分比误差 (MAPE)
        mape = sum(abs(e / a.get("price", 50)) for e, a in zip(errors, actual_prices)) / n * 100

        # 总体准确率（基于MAPE）
        overall_accuracy = max(0, 1 - mape / 100)

        return {
            "overall_accuracy": round(overall_accuracy, 3),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2)
        }

    def _calculate_direction_accuracy(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算方向性预测准确率"""
        # TODO: 接入真实数据

        correct_directions = 0
        total_predictions = len(predictions)

        for i in range(1, len(predictions)):
            pred_direction = 1 if predictions[i].get("target_price", 50) > predictions[i-1].get("target_price", 50) else -1
            actual_direction = 1 if actual_prices[i].get("price", 50) > actual_prices[i-1].get("price", 50) else -1

            if pred_direction == actual_direction:
                correct_directions += 1

        direction_accuracy = correct_directions / total_predictions if total_predictions > 0 else 0

        return {
            "accuracy": round(direction_accuracy, 3),
            "correct_predictions": correct_directions,
            "total_predictions": total_predictions
        }

    def _analyze_error_distribution(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析误差分布"""
        # TODO: 接入真实数据

        errors = [(p.get("target_price", 50) - a.get("price", 50))
                  for p, a in zip(predictions, actual_prices)]

        errors_sorted = sorted(errors)

        n = len(errors)
        q1_idx = n // 4
        median_idx = n // 2
        q3_idx = 3 * n // 4

        return {
            "min_error": round(min(errors), 2),
            "max_error": round(max(errors), 2),
            "median_error": round(errors_sorted[median_idx], 2),
            "q1_error": round(errors_sorted[q1_idx], 2),
            "q3_error": round(errors_sorted[q3_idx], 2),
            "std_error": round((sum(e ** 2 for e in errors) / n) ** 0.5, 2)
        }

    def _calibrate_confidence(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """置信度校准"""
        # TODO: 实现真实校准逻辑

        high_conf_correct = 0
        high_conf_total = 0
        low_conf_correct = 0
        low_conf_total = 0

        for p, a in zip(predictions, actual_prices):
            confidence = p.get("confidence", 0.5)
            error = abs(p.get("target_price", 50) - a.get("price", 50))

            # 判断预测是否正确（误差小于5%）
            is_correct = error < a.get("price", 50) * 0.05

            if confidence >= 0.7:
                high_conf_total += 1
                if is_correct:
                    high_conf_correct += 1
            else:
                low_conf_total += 1
                if is_correct:
                    low_conf_correct += 1

        high_conf_accuracy = high_conf_correct / high_conf_total if high_conf_total > 0 else 0
        low_conf_accuracy = low_conf_correct / low_conf_total if low_conf_total > 0 else 0

        return {
            "high_confidence_accuracy": round(high_conf_accuracy, 3),
            "low_confidence_accuracy": round(low_conf_accuracy, 3),
            "calibration_score": round(high_conf_accuracy - low_conf_accuracy, 3)
        }

    # ========== 回测计算 ==========

    def _generate_trades(
        self,
        predictions: List[Dict[str, Any]],
        actual_prices: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成交易信号"""
        # TODO: 实现真实交易逻辑

        trades = []

        for i in range(1, len(predictions)):
            pred_price = predictions[i].get("target_price", 50)
            current_price = actual_prices[i].get("price", 50)
            prev_price = actual_prices[i-1].get("price", 50)

            # 买入信号：预测上涨
            if pred_price > current_price * 1.05:
                entry_price = current_price
                exit_price = actual_prices[min(i+1, len(actual_prices)-1)].get("price", current_price)
                pnl = (exit_price - entry_price) / entry_price

                trades.append({
                    "type": "long",
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "entry_date": predictions[i].get("date", datetime.now().isoformat()),
                    "exit_date": actual_prices[min(i+1, len(actual_prices)-1)].get("date", datetime.now().isoformat())
                })

        return trades

    def _calculate_total_return(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float
    ) -> float:
        """计算总收益"""
        capital = initial_capital

        for trade in trades:
            capital *= (1 + trade["pnl"])

        total_return = (capital - initial_capital) / initial_capital

        return round(total_return, 4)

    def _calculate_max_drawdown(
        self,
        trades: List[Dict[str, Any]]
    ) -> float:
        """计算最大回撤"""
        # TODO: 实现真实回撤计算
        # 简化版本：基于交易序列

        peak = 0
        max_dd = 0

        cumulative_return = 0

        for trade in trades:
            cumulative_return += trade["pnl"]

            if cumulative_return > peak:
                peak = cumulative_return

            drawdown = (peak - cumulative_return) / peak if peak > 0 else 0

            if drawdown > max_dd:
                max_dd = drawdown

        return round(max_dd, 4)

    def _calculate_sharpe_ratio(
        self,
        trades: List[Dict[str, Any]],
        risk_free_rate: float = 0.03
    ) -> float:
        """计算夏普比率"""
        # TODO: 实现真实夏普比率计算
        # 简化版本

        returns = [t["pnl"] for t in trades]

        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)

        # 计算标准差
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        # 年化夏普比率
        sharpe = (avg_return - risk_free_rate / len(returns)) / std_dev if std_dev > 0 else 0

        return round(sharpe, 3)

    def _calculate_win_rate(
        self,
        trades: List[Dict[str, Any]]
    ) -> float:
        """计算胜率"""
        if not trades:
            return 0.0

        winning_trades = sum(1 for t in trades if t["pnl"] > 0)

        return round(winning_trades / len(trades), 3)

    def _calculate_profit_loss_ratio(
        self,
        trades: List[Dict[str, Any]]
    ) -> float:
        """计算盈亏比"""
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]

        if not winning_trades or not losing_trades:
            return 0.0

        avg_profit = sum(t["pnl"] for t in winning_trades) / len(winning_trades)
        avg_loss = sum(abs(t["pnl"]) for t in losing_trades) / len(losing_trades)

        return round(avg_profit / avg_loss, 2)

    def _annualize_return(
        self,
        total_return: float,
        period: str = "1y"
    ) -> float:
        """年化收益"""
        # TODO: 根据不同周期计算年化收益
        # 简化版本：假设1年周期

        if period == "1y":
            return round(total_return, 4)
        elif period == "6m":
            return round((1 + total_return) ** 2 - 1, 4)
        elif period == "3m":
            return round((1 + total_return) ** 4 - 1, 4)
        else:
            return round(total_return, 4)

    # ========== 改进建议生成 ==========

    def _generate_improvements(
        self,
        validation_metrics: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        improvements = []

        # 准确率改进
        accuracy = validation_metrics["overall_accuracy"]
        if accuracy < 0.70:
            improvements.append(f"预测准确率较低（{accuracy:.1%}），建议优化模型参数")
        elif accuracy < 0.80:
            improvements.append(f"预测准确率一般（{accuracy:.1%}），建议增加特征工程")
        else:
            improvements.append(f"预测准确率良好（{accuracy:.1%}），当前模型表现稳定")

        # 方向性预测改进
        direction_acc = validation_metrics["direction_accuracy"]["accuracy"]
        if direction_acc < 0.60:
            improvements.append(f"方向预测准确率低（{direction_acc:.1%}），建议优化趋势识别算法")

        # 回撤改进
        max_dd = backtest_results["max_drawdown"]
        if max_dd > 0.20:
            improvements.append(f"最大回撤较高（{max_dd:.1%}），建议增加止损机制")
        elif max_dd > 0.15:
            improvements.append(f"最大回撤偏高（{max_dd:.1%}），建议优化仓位管理")

        # 夏普比率改进
        sharpe = backtest_results["sharpe_ratio"]
        if sharpe < 1.0:
            improvements.append(f"夏普比率偏低（{sharpe:.2f}），建议优化风险调整后收益")
        elif sharpe >= 2.0:
            improvements.append(f"夏普比率优秀（{sharpe:.2f}），风险调整后收益表现良好")

        # 胜率改进
        win_rate = backtest_results["win_rate"]
        if win_rate < 0.50:
            improvements.append(f"胜率低于50%（{win_rate:.1%}），建议优化入场时机")

        # 盈亏比改进
        pl_ratio = backtest_results["profit_loss_ratio"]
        if pl_ratio < 1.5:
            improvements.append(f"盈亏比偏低（{pl_ratio:.2f}），建议优化止盈止损策略")

        return improvements

    def _identify_validation_risks(
        self,
        validation_metrics: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> List[str]:
        """识别验证风险"""
        risks = []

        # 过拟合风险
        if validation_metrics["overall_accuracy"] > 0.95:
            risks.append("预测准确率过高，可能存在过拟合风险")

        # 样本量风险
        if backtest_results["total_trades"] < 30:
            risks.append("回测样本量较小，统计显著性不足")

        # 回撤风险
        if backtest_results["max_drawdown"] > 0.25:
            risks.append(f"最大回撤过大（{backtest_results['max_drawdown']:.1%}），存在较大风险")

        # 置信度校准风险
        calib_score = validation_metrics["confidence_calibration"]["calibration_score"]
        if calib_score < 0.1:
            risks.append("置信度校准较差，高置信度预测未必准确")

        if not risks:
            risks.append("未发现明显验证风险")

        return risks

    def _generate_conclusion(
        self,
        validation_metrics: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> str:
        """生成核心结论"""
        accuracy = validation_metrics["overall_accuracy"]
        total_return = backtest_results["total_return"]
        sharpe = backtest_results["sharpe_ratio"]

        return (
            f"预测准确率{accuracy:.1%}，"
            f"回测收益{total_return:.1%}，"
            f"夏普比率{sharpe:.2f}，"
            f"胜率{backtest_results['win_rate']:.1%}"
        )


# 便捷函数
async def analyze_validation_backtest(
    stock_code: str,
    predictions: List[Dict[str, Any]],
    actual_prices: List[Dict[str, Any]],
    backtest_period: str = "1y"
) -> AnalysisResult:
    """
    验证回测分析（便捷函数）

    Args:
        stock_code: 股票代码
        predictions: 历史预测数据
        actual_prices: 实际价格数据
        backtest_period: 回测周期

    Returns:
        分析结果
    """
    ai = ValidationBacktestAI()
    return await ai.analyze(
        stock_code,
        predictions=predictions,
        actual_prices=actual_prices,
        backtest_period=backtest_period
    )

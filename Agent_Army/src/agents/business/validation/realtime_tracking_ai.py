"""
实盘跟踪AI - 结果验证军团 (2/4)

职责：
- 实盘数据跟踪
- 策略验证和对比
- 实时监控和预警
- 预测vs实际对比分析
- 盈亏跟踪和分析

数据源：
- Yahoo Finance API（实时行情）
- 历史预测记录（对比分析）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool


class RealtimeTrackingAI(BusinessAgent):
    """
    实盘跟踪AI - 结果验证军团 (2/4)

    功能：
    1. 实时跟踪预测股票的价格变化
    2. 对比预测价格与实际价格
    3. 计算预测准确率和偏差
    4. 跟踪盈亏情况
    5. 生成预警信息
    6. 支持多股票并行跟踪
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="实盘跟踪AI",
            role="实盘数据跟踪与策略验证",
            corps="result_validation",
            analysis_type="realtime_tracking",
            capabilities=[
                AgentCapability(
                    name="realtime_tracking",
                    description="实时跟踪",
                    input_type="stock_list_with_predictions",
                    output_type="tracking_report"
                ),
                AgentCapability(
                    name="strategy_validation",
                    description="策略验证",
                    input_type="predictions_vs_actual",
                    output_type="validation_report"
                ),
                AgentCapability(
                    name="alert_generation",
                    description="预警生成",
                    input_type="tracking_data",
                    output_type="alerts"
                )
            ],
            tools=[],
            config=config
        )

        # 初始化Yahoo Finance工具
        self.yahoo_tool = YahooFinanceTool()

        # 预警阈值配置
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "deviation_warning": 10.0,  # 偏差超过10%预警
            "deviation_critical": 20.0,  # 偏差超过20%严重预警
            "loss_warning": -5.0,  # 亏损超过5%预警
            "loss_critical": -10.0,  # 亏损超过10%严重预警
        })

        # 线程池（用于并行获取数据）
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.logger.info("实盘跟踪AI初始化完成")

    async def analyze(
        self,
        stock_list: List[str],
        predictions: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行实盘跟踪分析

        Args:
            stock_list: 股票代码列表 ["601669.SS", "600519.SS"]
            predictions: 预测数据列表 [{"stock_code": "601669.SS", "predicted_price": 10.5, ...}]
            **kwargs: 其他参数
                - target_prices: 目标价格字典 {stock_code: target_price}
                - stop_losses: 止损价格字典 {stock_code: stop_loss}
                - tracking_days: 跟踪天数（默认1天）

        Returns:
            跟踪报告
        """
        self.logger.info(
            f"开始实盘跟踪",
            extra={
                "stock_count": len(stock_list),
                "has_predictions": predictions is not None
            }
        )

        # 构建预测价格映射
        prediction_map = {}
        if predictions:
            for pred in predictions:
                stock_code = pred.get("stock_code")
                if stock_code:
                    prediction_map[stock_code] = {
                        "predicted_price": pred.get("predicted_price", 0),
                        "target_price": pred.get("target_price"),
                        "stop_loss": pred.get("stop_loss"),
                        "confidence": pred.get("confidence", 0.5),
                        "prediction_date": pred.get("prediction_date")
                    }

        # 并行获取实时数据
        tracking_data = await self._track_stocks_parallel(stock_list, prediction_map)

        # 生成汇总统计
        summary = self._calculate_summary(tracking_data)

        # 生成预警信息
        alerts = self._generate_alerts(tracking_data, summary)

        result = {
            "analysis_type": "realtime_tracking",
            "tracking_date": datetime.now().isoformat(),
            "stocks": tracking_data,
            "summary": summary,
            "alerts": alerts,
            "metadata": {
                "total_stocks": len(stock_list),
                "successful_tracking": len([d for d in tracking_data if "error" not in d]),
                "failed_tracking": len([d for d in tracking_data if "error" in d]),
            }
        }

        self.logger.info(
            f"实盘跟踪完成",
            extra={
                "accuracy_rate": summary["accuracy_rate"],
                "total_pnl": summary["total_pnl"],
                "alert_count": len(alerts)
            }
        )

        return result

    async def _track_stocks_parallel(
        self,
        stock_list: List[str],
        prediction_map: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """
        并行跟踪多只股票

        Args:
            stock_list: 股票代码列表
            prediction_map: 预测数据映射

        Returns:
            跟踪数据列表
        """
        loop = asyncio.get_event_loop()
        tasks = []

        for stock_code in stock_list:
            task = loop.run_in_executor(
                self.executor,
                self._track_single_stock,
                stock_code,
                prediction_map.get(stock_code, {})
            )
            tasks.append(task)

        # 等待所有任务完成
        tracking_data = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        return [
            data for data in tracking_data
            if not isinstance(data, Exception) and data
        ]

    def _track_single_stock(
        self,
        stock_code: str,
        prediction_data: Dict
    ) -> Optional[Dict[str, Any]]:
        """
        跟踪单只股票

        Args:
            stock_code: 股票代码
            prediction_data: 预测数据

        Returns:
            跟踪结果
        """
        try:
            # 获取实时行情
            quote = self.yahoo_tool.get_realtime_quote(stock_code)

            if "error" in quote:
                return {
                    "stock_code": stock_code,
                    "error": quote["error"]
                }

            current_price = quote.get("current_price", 0)
            predicted_price = prediction_data.get("predicted_price", 0)

            # 计算偏差和盈亏
            deviation = self._calculate_deviation(current_price, predicted_price)
            pnl = self._calculate_pnl(current_price, predicted_price)
            accuracy = self._calculate_accuracy(current_price, predicted_price)

            # 判断状态
            status = self._determine_status(deviation, pnl)

            return {
                "stock_code": stock_code,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "target_price": prediction_data.get("target_price"),
                "stop_loss": prediction_data.get("stop_loss"),
                "prediction_accuracy": accuracy,
                "deviation": deviation,
                "pnl": pnl,
                "pnl_ratio": pnl / predicted_price * 100 if predicted_price > 0 else 0,
                "status": status,
                "confidence": prediction_data.get("confidence", 0.5),
                "prediction_date": prediction_data.get("prediction_date"),
                "market_data": {
                    "change": quote.get("change", 0),
                    "change_percent": quote.get("change_percent", 0),
                    "volume": quote.get("volume", 0),
                    "high": quote.get("high", 0),
                    "low": quote.get("low", 0),
                    "open": quote.get("open", 0),
                },
                "timestamp": quote.get("timestamp")
            }

        except Exception as e:
            self.logger.error(f"跟踪股票 {stock_code} 失败: {e}")
            return {
                "stock_code": stock_code,
                "error": str(e)
            }

    def _calculate_deviation(self, current: float, predicted: float) -> float:
        """
        计算偏差百分比

        Args:
            current: 当前价格
            predicted: 预测价格

        Returns:
            偏差百分比（正数表示上涨，负数表示下跌）
        """
        if not predicted or predicted == 0:
            return 0.0
        return round((current - predicted) / predicted * 100, 2)

    def _calculate_pnl(self, current: float, predicted: float) -> float:
        """
        计算盈亏

        Args:
            current: 当前价格
            predicted: 预测价格（假设为买入价格）

        Returns:
            盈亏金额
        """
        if not predicted:
            return 0.0
        return round(current - predicted, 2)

    def _calculate_accuracy(self, current: float, predicted: float) -> float:
        """
        计算预测准确率

        Args:
            current: 当前价格
            predicted: 预测价格

        Returns:
            准确率（0-100）
        """
        if not predicted or predicted == 0:
            return 0.0

        deviation = abs(current - predicted) / predicted
        accuracy = max(0, 100 - deviation * 100)
        return round(accuracy, 2)

    def _determine_status(self, deviation: float, pnl: float) -> str:
        """
        判断股票状态

        Args:
            deviation: 偏差百分比
            pnl: 盈亏金额

        Returns:
            状态描述
        """
        if deviation > 10:
            return "超预期"
        elif deviation < -10:
            return "低于预期"
        elif pnl > 0:
            return "盈利"
        elif pnl < 0:
            return "亏损"
        else:
            return "符合预期"

    def _calculate_summary(self, tracking_data: List[Dict]) -> Dict[str, Any]:
        """
        计算汇总统计

        Args:
            tracking_data: 跟踪数据列表

        Returns:
            汇总统计
        """
        # 过滤有效数据（必须有预测价格且预测价格>0）
        valid_data = [
            d for d in tracking_data
            if "error" not in d and d.get("predicted_price") is not None and d.get("predicted_price", 0) > 0
        ]

        if not valid_data:
            return {
                "total_stocks": 0,
                "accurate_predictions": 0,
                "accuracy_rate": 0.0,
                "average_deviation": 0.0,
                "total_pnl": 0.0,
                "profitable_stocks": 0,
                "loss_stocks": 0,
                "win_rate": 0.0
            }

        total_stocks = len(valid_data)

        # 计算准确率（准确率>80%算准确）
        accurate_predictions = len([
            d for d in valid_data
            if d.get("prediction_accuracy", 0) >= 80
        ])

        # 计算平均偏差
        deviations = [abs(d.get("deviation", 0)) for d in valid_data]
        average_deviation = round(sum(deviations) / len(deviations), 2) if deviations else 0.0

        # 计算总盈亏
        total_pnl = round(sum(d.get("pnl", 0) for d in valid_data), 2)

        # 盈利和亏损股票数
        profitable_stocks = len([d for d in valid_data if d.get("pnl", 0) > 0])
        loss_stocks = len([d for d in valid_data if d.get("pnl", 0) < 0])

        # 计算总体准确率
        accuracy_rate = round(
            sum(d.get("prediction_accuracy", 0) for d in valid_data) / total_stocks,
            2
        )

        return {
            "total_stocks": total_stocks,
            "accurate_predictions": accurate_predictions,
            "accuracy_rate": accuracy_rate,
            "average_deviation": average_deviation,
            "total_pnl": total_pnl,
            "profitable_stocks": profitable_stocks,
            "loss_stocks": loss_stocks,
            "win_rate": round(profitable_stocks / total_stocks * 100, 2) if total_stocks > 0 else 0.0
        }

    def _generate_alerts(
        self,
        tracking_data: List[Dict],
        summary: Dict
    ) -> List[str]:
        """
        生成预警信息

        Args:
            tracking_data: 跟踪数据
            summary: 汇总统计

        Returns:
            预警列表
        """
        alerts = []
        thresholds = self.alert_thresholds

        # 单股票预警
        for data in tracking_data:
            if "error" in data:
                continue

            stock_code = data.get("stock_code")
            deviation = data.get("deviation", 0)
            pnl_ratio = data.get("pnl_ratio", 0)

            # 偏差预警
            if abs(deviation) >= thresholds["deviation_critical"]:
                alerts.append(
                    f"🚨 严重预警 [{stock_code}]: 偏差达到 {deviation:.2f}%，"
                    f"远超预期{thresholds['deviation_critical']}%"
                )
            elif abs(deviation) >= thresholds["deviation_warning"]:
                alerts.append(
                    f"⚠️ 预警 [{stock_code}]: 偏差达到 {deviation:.2f}%，"
                    f"超过预警阈值{thresholds['deviation_warning']}%"
                )

            # 亏损预警
            if pnl_ratio <= thresholds["loss_critical"]:
                alerts.append(
                    f"🚨 严重预警 [{stock_code}]: 亏损达到 {pnl_ratio:.2f}%，"
                    f"超过严重亏损阈值{thresholds['loss_critical']}%"
                )
            elif pnl_ratio <= thresholds["loss_warning"]:
                alerts.append(
                    f"⚠️ 预警 [{stock_code}]: 亏损达到 {pnl_ratio:.2f}%，"
                    f"超过亏损预警阈值{thresholds['loss_warning']}%"
                )

        # 总体预警
        if summary["accuracy_rate"] < 60:
            alerts.append(
                f"⚠️ 总体准确率偏低: {summary['accuracy_rate']:.2f}%，"
                f"低于60%阈值"
            )

        if summary["total_pnl"] < 0 and abs(summary["total_pnl"]) > 100:
            alerts.append(
                f"⚠️ 总体亏损较大: {summary['total_pnl']:.2f}元"
            )

        if summary["win_rate"] < 40:
            alerts.append(
                f"⚠️ 胜率偏低: {summary['win_rate']:.2f}%，"
                f"低于40%阈值"
            )

        return alerts if alerts else ["✅ 所有指标正常，无需预警"]

    async def validate_strategy(
        self,
        predictions: List[Dict],
        actual_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        验证策略有效性

        Args:
            predictions: 预测列表
            actual_results: 实际结果列表

        Returns:
            策略验证报告
        """
        self.logger.info(f"开始策略验证", extra={"prediction_count": len(predictions)})

        # 构建股票列表
        stock_codes = [p.get("stock_code") for p in predictions]

        # 执行实盘跟踪
        tracking_result = await self.analyze(stock_codes, predictions)

        # 策略验证指标
        validation_metrics = {
            "prediction_accuracy": tracking_result["summary"]["accuracy_rate"],
            "deviation_control": tracking_result["summary"]["average_deviation"],
            "profitability": tracking_result["summary"]["total_pnl"],
            "win_rate": tracking_result["summary"]["win_rate"],
            "risk_control": len([a for a in tracking_result["alerts"] if "严重预警" in a]),
        }

        # 策略评级
        strategy_score = self._calculate_strategy_score(validation_metrics)
        strategy_grade = self._determine_strategy_grade(strategy_score)

        result = {
            "validation_type": "strategy_validation",
            "timestamp": datetime.now().isoformat(),
            "tracking_result": tracking_result,
            "validation_metrics": validation_metrics,
            "strategy_score": strategy_score,
            "strategy_grade": strategy_grade,
            "recommendation": self._generate_strategy_recommendation(validation_metrics, strategy_grade)
        }

        self.logger.info(
            f"策略验证完成",
            extra={
                "score": strategy_score,
                "grade": strategy_grade
            }
        )

        return result

    def _calculate_strategy_score(self, metrics: Dict) -> float:
        """计算策略评分"""
        score = 0.0

        # 准确率权重40%
        score += metrics["prediction_accuracy"] * 0.4

        # 胜率权重30%
        score += metrics["win_rate"] * 0.3

        # 偏差控制权重20%（偏差越小越好）
        deviation_score = max(0, 100 - metrics["deviation_control"] * 2)
        score += deviation_score * 0.2

        # 风险控制权重10%（预警越少越好）
        risk_score = max(0, 100 - metrics["risk_control"] * 10)
        score += risk_score * 0.1

        return round(score, 2)

    def _determine_strategy_grade(self, score: float) -> str:
        """确定策略评级"""
        if score >= 80:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "及格"
        else:
            return "不及格"

    def _generate_strategy_recommendation(
        self,
        metrics: Dict,
        grade: str
    ) -> List[str]:
        """生成策略建议"""
        recommendations = []

        if metrics["prediction_accuracy"] < 70:
            recommendations.append("建议优化预测模型，提高准确率")

        if metrics["win_rate"] < 50:
            recommendations.append("建议调整选股策略，提高胜率")

        if metrics["deviation_control"] > 15:
            recommendations.append("建议加强风险管理，控制预测偏差")

        if metrics["risk_control"] > 3:
            recommendations.append("建议优化止损策略，减少严重预警")

        if grade == "优秀":
            recommendations.append("策略表现优秀，继续保持")

        return recommendations if recommendations else ["策略表现良好"]


# 便捷函数
async def track_stocks_realtime(
    stock_list: List[str],
    predictions: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    实时跟踪股票（便捷函数）

    Args:
        stock_list: 股票代码列表
        predictions: 预测数据列表

    Returns:
        跟踪报告
    """
    ai = RealtimeTrackingAI()
    return await ai.analyze(stock_list, predictions)


async def validate_investment_strategy(
    predictions: List[Dict],
    actual_results: List[Dict]
) -> Dict[str, Any]:
    """
    验证投资策略（便捷函数）

    Args:
        predictions: 预测列表
        actual_results: 实际结果列表

    Returns:
        策略验证报告
    """
    ai = RealtimeTrackingAI()
    return await ai.validate_strategy(predictions, actual_results)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test_realtime_tracking():
        print("=" * 70)
        print("实盘跟踪AI测试")
        print("=" * 70)

        # 初始化AI
        ai = RealtimeTrackingAI()

        # 测试数据
        stock_list = ["601669.SS", "600519.SS"]

        # 模拟预测数据
        predictions = [
            {
                "stock_code": "601669.SS",
                "predicted_price": 5.5,
                "target_price": 6.5,
                "stop_loss": 5.0,
                "confidence": 0.75,
                "prediction_date": "2026-03-14"
            },
            {
                "stock_code": "600519.SS",
                "predicted_price": 1750.0,
                "target_price": 1900.0,
                "stop_loss": 1650.0,
                "confidence": 0.80,
                "prediction_date": "2026-03-14"
            }
        ]

        # 执行跟踪
        print("\n[1] 测试实时跟踪...")
        result = await ai.analyze(stock_list, predictions)

        print(f"\n跟踪日期: {result['tracking_date']}")
        print(f"成功跟踪: {result['metadata']['successful_tracking']}")
        print(f"失败跟踪: {result['metadata']['failed_tracking']}")

        print("\n汇总统计:")
        for key, value in result['summary'].items():
            print(f"  {key}: {value}")

        print("\n股票详情:")
        for stock in result['stocks']:
            if "error" not in stock:
                print(f"\n  {stock['stock_code']}:")
                print(f"    当前价格: {stock['current_price']}")
                print(f"    预测价格: {stock['predicted_price']}")
                print(f"    偏差: {stock['deviation']}%")
                print(f"    盈亏: {stock['pnl']}")
                print(f"    准确率: {stock['prediction_accuracy']}%")
                print(f"    状态: {stock['status']}")

        print("\n预警信息:")
        for alert in result['alerts']:
            print(f"  {alert}")

        print("\n" + "=" * 70)
        print("测试完成")

    asyncio.run(test_realtime_tracking())

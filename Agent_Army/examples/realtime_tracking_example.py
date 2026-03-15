"""
实盘跟踪AI使用示例
演示如何使用RealtimeTrackingAI进行实盘跟踪和策略验证
"""

import asyncio
from datetime import datetime
from src.agents.business.validation.realtime_tracking_ai import RealtimeTrackingAI


async def example_basic_tracking():
    """示例1: 基本实盘跟踪"""
    print("\n" + "=" * 70)
    print("示例1: 基本实盘跟踪")
    print("=" * 70)

    # 初始化AI
    ai = RealtimeTrackingAI()

    # 股票列表
    stock_list = ["601669.SS", "600519.SS"]

    # 预测数据（假设这些是之前AI预测的结果）
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
    result = await ai.analyze(stock_list, predictions)

    # 显示结果
    print(f"\n跟踪时间: {result['tracking_date']}")
    print(f"成功跟踪: {result['metadata']['successful_tracking']} 只")
    print(f"失败跟踪: {result['metadata']['failed_tracking']} 只")

    print("\n汇总统计:")
    summary = result['summary']
    print(f"  总股票数: {summary['total_stocks']}")
    print(f"  准确预测: {summary['accurate_predictions']} 只")
    print(f"  总体准确率: {summary['accuracy_rate']:.2f}%")
    print(f"  平均偏差: {summary['average_deviation']:.2f}%")
    print(f"  总盈亏: {summary['total_pnl']:.2f} 元")
    print(f"  盈利股票: {summary['profitable_stocks']} 只")
    print(f"  亏损股票: {summary['loss_stocks']} 只")
    print(f"  胜率: {summary['win_rate']:.2f}%")

    print("\n股票详情:")
    for stock in result['stocks']:
        if "error" not in stock:
            print(f"\n  股票: {stock['stock_code']}")
            print(f"    当前价格: {stock['current_price']:.2f}")
            print(f"    预测价格: {stock['predicted_price']:.2f}")
            print(f"    偏差: {stock['deviation']:.2f}%")
            print(f"    盈亏: {stock['pnl']:.2f} 元")
            print(f"    准确率: {stock['prediction_accuracy']:.2f}%")
            print(f"    状态: {stock['status']}")

    if result['alerts']:
        print("\n预警信息:")
        for alert in result['alerts']:
            print(f"  {alert}")


async def example_strategy_validation():
    """示例2: 策略验证"""
    print("\n" + "=" * 70)
    print("示例2: 投资策略验证")
    print("=" * 70)

    # 初始化AI
    ai = RealtimeTrackingAI()

    # 历史预测数据
    predictions = [
        {
            "stock_code": "601669.SS",
            "predicted_price": 5.5,
            "target_price": 6.5,
            "stop_loss": 5.0,
            "confidence": 0.75
        },
        {
            "stock_code": "600519.SS",
            "predicted_price": 1750.0,
            "target_price": 1900.0,
            "stop_loss": 1650.0,
            "confidence": 0.80
        }
    ]

    # 实际结果（当前价格）
    actual_results = [
        {"stock_code": "601669.SS", "actual_price": 5.8},
        {"stock_code": "600519.SS", "actual_price": 1760.0}
    ]

    # 执行策略验证
    result = await ai.validate_strategy(predictions, actual_results)

    # 显示验证结果
    print(f"\n验证时间: {result['timestamp']}")

    print("\n验证指标:")
    metrics = result['validation_metrics']
    print(f"  预测准确率: {metrics['prediction_accuracy']:.2f}%")
    print(f"  偏差控制: {metrics['deviation_control']:.2f}%")
    print(f"  盈利能力: {metrics['profitability']:.2f} 元")
    print(f"  胜率: {metrics['win_rate']:.2f}%")
    print(f"  风险控制: {metrics['risk_control']} 个严重预警")

    print(f"\n策略评分: {result['strategy_score']:.2f}")
    print(f"策略评级: {result['strategy_grade']}")

    print("\n策略建议:")
    for recommendation in result['recommendation']:
        print(f"  - {recommendation}")


async def example_custom_thresholds():
    """示例3: 自定义预警阈值"""
    print("\n" + "=" * 70)
    print("示例3: 自定义预警阈值")
    print("=" * 70)

    # 自定义配置
    config = {
        "alert_thresholds": {
            "deviation_warning": 5.0,   # 偏差超过5%预警（更严格）
            "deviation_critical": 15.0,  # 偏差超过15%严重预警
            "loss_warning": -3.0,        # 亏损超过3%预警
            "loss_critical": -7.0,       # 亏损超过7%严重预警
        }
    }

    # 使用自定义配置初始化
    ai = RealtimeTrackingAI(config=config)

    print("\n自定义预警阈值:")
    print(f"  偏差预警: {ai.alert_thresholds['deviation_warning']}%")
    print(f"  偏差严重预警: {ai.alert_thresholds['deviation_critical']}%")
    print(f"  亏损预警: {ai.alert_thresholds['loss_warning']}%")
    print(f"  亏损严重预警: {ai.alert_thresholds['loss_critical']}%")

    # 执行跟踪（使用模拟数据）
    stock_list = ["601669.SS"]
    predictions = [
        {
            "stock_code": "601669.SS",
            "predicted_price": 5.5,
            "target_price": 6.5,
            "stop_loss": 5.0
        }
    ]

    result = await ai.analyze(stock_list, predictions)

    # 显示预警
    if result['alerts']:
        print("\n生成的预警:")
        for alert in result['alerts']:
            print(f"  {alert}")


async def example_batch_tracking():
    """示例4: 批量跟踪多只股票"""
    print("\n" + "=" * 70)
    print("示例4: 批量跟踪多只股票")
    print("=" * 70)

    # 初始化AI
    ai = RealtimeTrackingAI()

    # 大批量股票（并行处理）
    stock_list = [
        "601669.SS",  # 中国电建
        "600519.SS",  # 贵州茅台
        "000001.SZ",  # 平安银行
        "000002.SZ",  # 万科A
        "600036.SS",  # 招商银行
    ]

    # 简化的预测数据
    predictions = [
        {
            "stock_code": stock,
            "predicted_price": 10.0,
            "target_price": 12.0,
            "stop_loss": 9.0
        }
        for stock in stock_list
    ]

    print(f"\n开始跟踪 {len(stock_list)} 只股票...")

    # 执行跟踪（并行）
    import time
    start = time.time()
    result = await ai.analyze(stock_list, predictions)
    elapsed = time.time() - start

    print(f"跟踪完成，耗时: {elapsed:.2f} 秒")

    # 显示汇总
    summary = result['summary']
    print(f"\n汇总:")
    print(f"  成功跟踪: {result['metadata']['successful_tracking']} 只")
    print(f"  平均准确率: {summary['accuracy_rate']:.2f}%")
    print(f"  总盈亏: {summary['total_pnl']:.2f} 元")
    print(f"  胜率: {summary['win_rate']:.2f}%")


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("实盘跟踪AI (RealtimeTrackingAI) 使用示例")
    print("=" * 70)

    # 注意：这些示例需要网络连接和YahooFinance工具
    # 如果无法连接，请使用Mock数据进行测试

    try:
        # 运行示例1: 基本跟踪
        # await example_basic_tracking()

        # 运行示例2: 策略验证
        # await example_strategy_validation()

        # 运行示例3: 自定义阈值
        # await example_custom_thresholds()

        # 运行示例4: 批量跟踪
        # await example_batch_tracking()

        print("\n✅ 所有示例可以独立运行，请取消注释以测试不同功能")
        print("⚠️ 注意: 需要网络连接访问Yahoo Finance API")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("提示: 请确保已安装yfinance: pip install yfinance")


if __name__ == "__main__":
    asyncio.run(main())

"""
预测验证AI - 结果验证军团 (1/4)

职责：
- 验证预测准确性
- 评估分析效果
- 识别错误模式
- 提供改进建议
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool


class PredictionValidatorAI(BusinessAgent):
    """预测验证AI - 结果验证军团 (1/4)"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="预测验证AI",
            role="验证预测准确性",
            corps="result_validation",
            analysis_type="prediction_validation",
            capabilities=[
                AgentCapability(
                    name="prediction_verification",
                    description="预测验证",
                    input_type="prediction_vs_actual",
                    output_type="accuracy_report"
                )
            ],
            tools=[],
            config=config
        )

        self.logger.info("预测验证AI初始化完成")

    async def analyze(
        self,
        predictions: List[Dict],
        actual_results: List[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """
        验证预测准确性

        Args:
            predictions: 预测列表 [{prediction, timestamp, ...}]
            actual_results: 实际结果列表 [{actual, timestamp, ...}]
            **kwargs: 其他参数

        Returns:
            验证报告
        """
        self.logger.info(f"开始预测验证", extra={"prediction_count": len(predictions)})

        # 业务逻辑：计算准确率
        accuracy_metrics = self._calculate_accuracy(predictions, actual_results)

        # 业务逻辑：识别错误模式
        error_patterns = self._identify_error_patterns(predictions, actual_results)

        # 业务逻辑：生成改进建议
        improvements = self._generate_improvements(error_patterns)

        result = {
            "analysis_type": "prediction_validation",
            "timestamp": datetime.now().isoformat(),
            "sample_size": len(predictions),

            # 准确性指标
            "accuracy": {
                "overall": accuracy_metrics["overall"],
                "direction": accuracy_metrics["direction"],  # 涨跌方向准确率
                "magnitude": accuracy_metrics["magnitude"]   # 幅度准确率
            },

            # 错误模式
            "error_patterns": error_patterns,

            # 改进建议
            "improvements": improvements,

            # 评分
            "score": accuracy_metrics["overall"],
            "grade": self._determine_grade(accuracy_metrics["overall"]),

            # 总结
            "summary": self._generate_summary(accuracy_metrics, improvements)
        }

        self.logger.info(
            f"预测验证完成",
            extra={
                "accuracy": result["accuracy"]["overall"],
                "grade": result["grade"]
            }
        )

        return result

    def _calculate_accuracy(
        self,
        predictions: List[Dict],
        actual_results: List[Dict]
    ) -> Dict[str, float]:
        """计算准确性（业务逻辑）"""
        if not predictions or not actual_results:
            return {
                "overall": 0.0,
                "direction": 0.0,
                "magnitude": 0.0
            }

        # 简化计算（实际应对比预测值与实际值）
        # 这里使用模拟数据
        direction_correct = 0  # 方向预测正确数
        magnitude_errors = []   # 幅度误差

        for pred, actual in zip(predictions, actual_results):
            # 方向准确性（涨/跌判断）
            pred_direction = pred.get("direction", "up")
            actual_direction = actual.get("direction", "up")

            if pred_direction == actual_direction:
                direction_correct += 1

            # 幅度准确性
            pred_value = pred.get("value", 0)
            actual_value = actual.get("value", 0)

            if actual_value != 0:
                error = abs(pred_value - actual_value) / actual_value
                magnitude_errors.append(error)

        # 计算准确率
        direction_accuracy = (direction_correct / len(predictions)) * 100
        magnitude_accuracy = max(0, 100 - (sum(magnitude_errors) / len(magnitude_errors)) * 100) if magnitude_errors else 0
        overall = (direction_accuracy * 0.6 + magnitude_accuracy * 0.4)

        return {
            "overall": round(overall, 1),
            "direction": round(direction_accuracy, 1),
            "magnitude": round(magnitude_accuracy, 1)
        }

    def _identify_error_patterns(
        self,
        predictions: List[Dict],
        actual_results: List[Dict]
    ) -> List[str]:
        """识别错误模式（业务逻辑）"""
        patterns = []

        # 简化版错误模式识别
        accuracy = self._calculate_accuracy(predictions, actual_results)

        if accuracy["direction"] < 60:
            patterns.append("方向预测准确率偏低")

        if accuracy["magnitude"] < 60:
            patterns.append("幅度预测偏差较大")

        if not patterns:
            patterns.append("未发现明显错误模式")

        return patterns

    def _generate_improvements(self, error_patterns: List[str]) -> List[str]:
        """生成改进建议（业务逻辑）"""
        improvements = []

        for pattern in error_patterns:
            if "方向" in pattern:
                improvements.append("建议加强趋势分析能力")
            elif "幅度" in pattern:
                improvements.append("建议优化估值模型参数")

        if not improvements:
            improvements.append("预测质量良好，继续保持")

        return improvements

    def _determine_grade(self, accuracy: float) -> str:
        """确定评级（业务逻辑）"""
        if accuracy >= 80:
            return "A"
        elif accuracy >= 70:
            return "B"
        elif accuracy >= 60:
            return "C"
        else:
            return "D"

    def _generate_summary(
        self,
        accuracy_metrics: Dict,
        improvements: List[str]
    ) -> str:
        """生成总结（业务逻辑）"""
        return (
            f"预测准确率{accuracy_metrics['overall']}%，"
            f"评级{self._determine_grade(accuracy_metrics['overall'])}，"
            f"{improvements[0] if improvements else '无改进建议'}"
        )


# 便捷函数
async def validate_predictions(
    predictions: List[Dict],
    actual_results: List[Dict]
) -> Dict[str, Any]:
    """验证预测（便捷函数）"""
    ai = PredictionValidatorAI()
    return await ai.analyze(predictions, actual_results)

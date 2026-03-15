"""
Parameter Optimization AI - 根据验证结果调整系统参数
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.logger import LoggerMixin


class ParameterOptimizationAI(BaseAgent, LoggerMixin):
    """
    参数优化AI

    职责：
    1. 根据验证结果分析参数表现
    2. 调整分析参数（PB阈值、PE阈值、权重配置）
    3. 生成优化提案
    4. 安全边界：每次调整幅度<10%，参数范围有限制
    """

    # 安全边界（参数范围限制）
    SAFE_RANGES = {
        "pb_min": (0.5, 1.5),      # PB阈值范围
        "pb_max": (1.5, 3.0),
        "pe_min": (5, 30),         # PE阈值范围
        "pe_max": (30, 60),
        "roe_min": (5, 15),        # ROE阈值范围
        "debt_max": (40, 80),      # 负债率上限范围
        "time_window_min": (1, 6), # 时间窗口下限（月）
        "time_window_max": (6, 24) # 时间窗口上限（月）
    }

    # 权重配置范围
    WEIGHT_RANGES = {
        "fundamental": (0.1, 0.5),
        "technical": (0.1, 0.5),
        "capital": (0.1, 0.5),
        "policy": (0.1, 0.5),
        "historical": (0.1, 0.5),
        "industry": (0.1, 0.5)
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.config_path = Path(config.get("config_path", "config/agent_config.json"))
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            name="Parameter Optimization AI",
            role="根据验证结果调整系统参数",
            capabilities=[
                AgentCapability(
                    name="analyze_performance",
                    description="分析参数表现",
                    input_type="validation_results",
                    output_type="performance_report"
                ),
                AgentCapability(
                    name="optimize_parameters",
                    description="优化参数配置",
                    input_type="performance_report",
                    output_type="optimization_proposal"
                ),
                AgentCapability(
                    name="apply_optimization",
                    description="应用优化配置",
                    input_type="optimization_proposal",
                    output_type="config_update"
                ),
            ]
        )

        # 加载当前配置
        self.current_config = self._load_config()
        self.optimization_history = []

        self.logger.info(f"Parameter Optimization AI initialized")
        self.logger.info(f"Config path: {self.config_path}")

    async def analyze_performance(
        self,
        validation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析参数表现

        Args:
            validation_results: 验证结果列表

        Returns:
            性能报告
        """
        self.logger.info(f"Analyzing performance with {len(validation_results)} results")

        if not validation_results:
            return {
                "total_cases": 0,
                "average_accuracy": 0,
                "success_rate": 0,
                "weak_points": [],
                "recommendations": []
            }

        # 计算平均准确率
        accuracies = [r.get("accuracy", 0.5) for r in validation_results]
        avg_accuracy = sum(accuracies) / len(accuracies)

        # 计算成功率
        success_count = sum(1 for r in validation_results if r.get("case_type") == "success")
        success_rate = success_count / len(validation_results)

        # 分析弱点
        weak_points = []
        if avg_accuracy < 0.7:
            weak_points.append("整体准确率偏低")
        if success_rate < 0.6:
            weak_points.append("成功率偏低")

        # 分析目标价预测
        target_deviations = []
        for r in validation_results:
            pred = r.get("prediction", {})
            actual = r.get("actual_result", {})
            if pred.get("target_price") and actual.get("actual_target_price"):
                deviation = abs(actual["actual_target_price"] - pred["target_price"]) / pred["target_price"]
                target_deviations.append(deviation)

        if target_deviations:
            avg_target_deviation = sum(target_deviations) / len(target_deviations)
            if avg_target_deviation > 0.3:
                weak_points.append("目标价预测偏差较大")

        # 生成建议
        recommendations = []
        if avg_accuracy < 0.7:
            recommendations.append("建议调整基本面分析权重")
            recommendations.append("建议优化估值模型参数")
        if "目标价预测偏差较大" in weak_points:
            recommendations.append("建议收紧PB/PE阈值范围")

        report = {
            "total_cases": len(validation_results),
            "average_accuracy": avg_accuracy,
            "success_rate": success_rate,
            "weak_points": weak_points,
            "recommendations": recommendations,
            "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.logger.info(f"Performance analysis completed: accuracy={avg_accuracy:.1%}, success_rate={success_rate:.1%}")

        return report

    async def optimize_parameters(
        self,
        performance_report: Dict[str, Any],
        current_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成参数优化提案

        Args:
            performance_report: 性能报告
            current_config: 当前配置（可选）

        Returns:
            优化提案
        """
        self.logger.info("Generating optimization proposal")

        config = current_config or self.current_config
        proposal = {
            "optimization_id": f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "based_on_report": performance_report,
            "parameter_adjustments": [],
            "weight_adjustments": [],
            "expected_improvement": "",
            "risk_assessment": "",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 根据弱点生成参数调整
        weak_points = performance_report.get("weak_points", [])

        if "整体准确率偏低" in weak_points:
            # 调整PB阈值（收紧）
            pb_min = config.get("pb_min", 0.8)
            new_pb_min = min(pb_min * 1.05, self.SAFE_RANGES["pb_min"][1])
            if abs(new_pb_min - pb_min) / pb_min < 0.1:  # 确保调整幅度<10%
                proposal["parameter_adjustments"].append({
                    "parameter": "pb_min",
                    "old_value": pb_min,
                    "new_value": round(new_pb_min, 2),
                    "reason": "提高PB下限，筛选更优质标的"
                })

        if "目标价预测偏差较大" in weak_points:
            # 调整PE阈值（收紧）
            pe_min = config.get("pe_min", 10)
            new_pe_min = min(pe_min * 1.05, self.SAFE_RANGES["pe_min"][1])
            if abs(new_pe_min - pe_min) / pe_min < 0.1:
                proposal["parameter_adjustments"].append({
                    "parameter": "pe_min",
                    "old_value": pe_min,
                    "new_value": round(new_pe_min, 2),
                    "reason": "提高PE下限，降低估值风险"
                })

        # 调整权重配置
        if performance_report.get("average_accuracy", 0) < 0.7:
            # 提高基本面权重
            current_fundamental_weight = config.get("weights", {}).get("fundamental", 0.3)
            new_weight = min(current_fundamental_weight * 1.08, self.WEIGHT_RANGES["fundamental"][1])
            if abs(new_weight - current_fundamental_weight) < 0.1:  # 确保调整幅度<10%
                proposal["weight_adjustments"].append({
                    "dimension": "fundamental",
                    "old_weight": current_fundamental_weight,
                    "new_weight": round(new_weight, 2),
                    "reason": "提高基本面权重，增强安全边际"
                })

                # 需要降低其他维度权重以保持总和=1
                # 这里简化处理，实际应用中需要更复杂的权重平衡逻辑

        # 生成预期改进说明
        if proposal["parameter_adjustments"] or proposal["weight_adjustments"]:
            proposal["expected_improvement"] = "预计提升准确率5-10%，降低风险偏好"
            proposal["risk_assessment"] = "低风险：参数调整幅度<10%，在安全范围内"
        else:
            proposal["expected_improvement"] = "无需调整，当前配置表现良好"
            proposal["risk_assessment"] = "无风险"

        self.logger.info(f"Optimization proposal generated: {len(proposal['parameter_adjustments'])} parameter changes, {len(proposal['weight_adjustments'])} weight changes")

        return proposal

    async def apply_optimization(
        self,
        proposal: Dict[str, Any],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        应用优化配置

        Args:
            proposal: 优化提案
            auto_apply: 是否自动应用（否则需要人工确认）

        Returns:
            应用结果
        """
        self.logger.info(f"Applying optimization: {proposal['optimization_id']}")

        result = {
            "optimization_id": proposal["optimization_id"],
            "applied": False,
            "applied_at": None,
            "changes": [],
            "new_config": None
        }

        # 检查是否需要人工确认
        if not auto_apply:
            self.logger.warning("Auto-apply is disabled. Manual confirmation required.")
            result["status"] = "pending_approval"
            return result

        # 应用参数调整
        new_config = self.current_config.copy()

        for adj in proposal.get("parameter_adjustments", []):
            param = adj["parameter"]
            old_value = adj["old_value"]
            new_value = adj["new_value"]

            # 检查安全边界
            if param in self.SAFE_RANGES:
                min_val, max_val = self.SAFE_RANGES[param]
                if not (min_val <= new_value <= max_val):
                    self.logger.error(f"Parameter {new_value} out of safe range [{min_val}, {max_val}]")
                    continue

            new_config[param] = new_value
            result["changes"].append(f"{param}: {old_value} -> {new_value}")
            self.logger.info(f"Adjusted {param}: {old_value} -> {new_value}")

        # 应用权重调整
        if "weights" not in new_config:
            new_config["weights"] = {}

        for adj in proposal.get("weight_adjustments", []):
            dimension = adj["dimension"]
            old_weight = adj["old_weight"]
            new_weight = adj["new_weight"]

            # 检查安全边界
            if dimension in self.WEIGHT_RANGES:
                min_val, max_val = self.WEIGHT_RANGES[dimension]
                if not (min_val <= new_weight <= max_val):
                    self.logger.error(f"Weight {new_weight} out of safe range [{min_val}, {max_val}]")
                    continue

            new_config["weights"][dimension] = new_weight
            result["changes"].append(f"weights.{dimension}: {old_weight} -> {new_weight}")
            self.logger.info(f"Adjusted weight {dimension}: {old_weight} -> {new_weight}")

        # 保存新配置
        self._save_config(new_config)
        self.current_config = new_config

        result["applied"] = True
        result["applied_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result["new_config"] = new_config
        result["status"] = "applied"

        # 记录到历史
        self.optimization_history.append({
            "optimization_id": proposal["optimization_id"],
            "applied_at": result["applied_at"],
            "changes": result["changes"]
        })

        self.logger.info(f"Optimization applied: {len(result['changes'])} changes")

        return result

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
                return self._get_default_config()
        else:
            # 创建默认配置
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "pb_min": 0.8,
            "pb_max": 2.0,
            "pe_min": 10,
            "pe_max": 50,
            "roe_min": 10,
            "debt_max": 60,
            "time_window_min": 3,
            "time_window_max": 12,
            "weights": {
                "fundamental": 0.30,
                "technical": 0.20,
                "capital": 0.15,
                "policy": 0.15,
                "historical": 0.10,
                "industry": 0.10
            }
        }

    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Config saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    async def execute(self, task: str, **kwargs) -> Any:
        """
        执行任务

        Args:
            task: 任务名称
            **kwargs: 任务参数

        Returns:
            任务结果
        """
        if task == "analyze":
            return await self.analyze_performance(
                validation_results=kwargs.get("validation_results", [])
            )
        elif task == "optimize":
            return await self.optimize_parameters(
                performance_report=kwargs.get("performance_report", {}),
                current_config=kwargs.get("current_config")
            )
        elif task == "apply":
            return await self.apply_optimization(
                proposal=kwargs.get("proposal", {}),
                auto_apply=kwargs.get("auto_apply", False)
            )
        else:
            raise ValueError(f"Unknown task: {task}")

    async def get_optimization_history(self) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history

    async def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.current_config

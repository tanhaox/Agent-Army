"""
评估场景生成器
基于 mcp-builder 的 6 个评估标准创建测试场景

评估标准：
1. 独立 (Independent) - 不依赖其他问题
2. 只读 (Read-only) - 仅需要非破坏性操作
3. 复杂 (Complex) - 需要多个工具调用和深入探索
4. 现实 (Realistic) - 基于真实用例
5. 可验证 (Verifiable) - 可通过字符串比较验证的单一明确答案
6. 稳定 (Stable) - 答案不会随时间变化
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class EvaluationScenario:
    """评估场景"""
    question: str
    answer: str
    category: str = "general"
    tools_required: List[str] = field(default_factory=list)
    complexity: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> tuple[bool, Optional[str]]:
        """验证场景是否符合 6 个标准"""
        # 1. 独立性检查
        if self.metadata.get("depends_on_question"):
            return False, "问题不独立：依赖其他问题"

        # 2. 只读检查
        if not self.metadata.get("read_only", True):
            return False, "问题不是只读：包含破坏性操作"

        # 3. 复杂度检查
        if len(self.tools_required) < 2:
            return False, "问题不够复杂：需要至少 2 个工具调用"

        # 4. 现实性检查
        if not self.metadata.get("real_world_use_case"):
            return False, "问题不现实：缺少真实用例说明"

        # 5. 可验证性检查
        if not self.answer or not isinstance(self.answer, (str, int, float)):
            return False, "答案不可验证：必须是明确类型的值"

        # 6. 稳定性检查
        if self.metadata.get("time_sensitive"):
            return False, "答案不稳定：随时间变化"

        return True, None

    def to_xml_element(self) -> ET.Element:
        """转换为 XML 元素"""
        qa_elem = ET.Element("qa_pair")

        question_elem = ET.SubElement(qa_elem, "question")
        question_elem.text = self.question

        answer_elem = ET.SubElement(qa_elem, "answer")
        answer_elem.text = str(self.answer)

        # 添加元数据
        meta_elem = ET.SubElement(qa_elem, "metadata")
        for key, value in self.metadata.items():
            item = ET.SubElement(meta_elem, key)
            item.text = str(value)

        return qa_elem


class EvaluationFramework:
    """评估框架"""

    def __init__(self, name: str = "技能评估"):
        self.name = name
        self.scenarios: List[EvaluationScenario] = []
        self.created_at = datetime.now()

    def add_scenario(self, scenario: EvaluationScenario):
        """添加评估场景"""
        is_valid, error = scenario.validate()
        if not is_valid:
            raise ValueError(f"场景验证失败: {error}")

        self.scenarios.append(scenario)

    def generate_scenarios_from_tools(
        self,
        tools: List[str],
        count: int = 10
    ) -> List[EvaluationScenario]:
        """
        从工具列表生成评估场景（辅助方法）

        Args:
            tools: 可用工具列表
            count: 要生成的场景数量

        Returns:
            生成的场景列表
        """
        scenarios = []

        for i in range(count):
            # 这里是场景生成的模板
            # 实际使用时需要根据具体工具定制
            scenario = EvaluationScenario(
                question=f"示例问题 {i+1}",
                answer=f"答案 {i+1}",
                tools_required=tools[:3],  # 使用前 3 个工具
                complexity="medium",
                metadata={
                    "read_only": True,
                    "real_world_use_case": True,
                    "time_sensitive": False
                }
            )
            scenarios.append(scenario)

        return scenarios

    def to_xml(self) -> str:
        """导出为 XML 格式"""
        evaluation = ET.Element("evaluation")

        # 添加评估元数据
        metadata = ET.SubElement(evaluation, "metadata")
        ET.SubElement(metadata, "name").text = self.name
        ET.SubElement(metadata, "created_at").text = self.created_at.isoformat()
        ET.SubElement(metadata, "total_scenarios").text = str(len(self.scenarios))

        # 添加所有场景
        for scenario in self.scenarios:
            evaluation.append(scenario.to_xml_element())

        return ET.tostring(evaluation, encoding='unicode')

    def to_json(self) -> str:
        """导出为 JSON 格式"""
        data = {
            "metadata": {
                "name": self.name,
                "created_at": self.created_at.isoformat(),
                "total_scenarios": len(self.scenarios)
            },
            "scenarios": [asdict(s) for s in self.scenarios]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, path: Path, format: str = "xml"):
        """保存到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "xml":
            content = self.to_xml()
        elif format == "json":
            content = self.to_json()
        else:
            raise ValueError(f"不支持的格式: {format}")

        path.write_text(content, encoding='utf-8')


class EvaluationMetrics:
    """评估指标收集器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start_evaluation(self):
        """开始评估"""
        import time
        self.start_time = time.time()

    def record_result(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        tool_calls: int,
        duration: float,
        success: bool,
        feedback: str = ""
    ):
        """记录单个评估结果"""
        result = {
            "question": question,
            "expected_answer": expected_answer,
            "actual_answer": actual_answer,
            "tool_calls": tool_calls,
            "duration": duration,
            "success": success,
            "feedback": feedback
        }
        self.results.append(result)

    def calculate_metrics(self) -> Dict[str, Any]:
        """计算评估指标"""
        if not self.results:
            return {}

        total = len(self.results)
        correct = sum(1 for r in self.results if r["success"])

        metrics = {
            "accuracy": correct / total if total > 0 else 0,
            "total_questions": total,
            "correct_answers": correct,
            "wrong_answers": total - correct,
            "avg_duration": sum(r["duration"] for r in self.results) / total,
            "avg_tool_calls": sum(r["tool_calls"] for r in self.results) / total,
            "total_duration": self.end_time - self.start_time if self.end_time and self.start_time else 0
        }

        # 性能分级
        if metrics["accuracy"] >= 0.95 and metrics["avg_duration"] < 15:
            metrics["grade"] = "卓越"
        elif metrics["accuracy"] >= 0.90 and metrics["avg_duration"] < 20:
            metrics["grade"] = "优秀"
        elif metrics["accuracy"] >= 0.80 and metrics["avg_duration"] < 30:
            metrics["grade"] = "良好"
        else:
            metrics["grade"] = "需改进"

        return metrics

    def generate_report(self) -> str:
        """生成评估报告"""
        metrics = self.calculate_metrics()

        report = f"""
{'='*60}
评估报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

📊 准确率: {metrics.get('accuracy', 0):.1%}
✅ 正确: {metrics.get('correct_answers', 0)} / {metrics.get('total_questions', 0)}
❌ 错误: {metrics.get('wrong_answers', 0)}
⏱️  平均时长: {metrics.get('avg_duration', 0):.2f}秒
🔧 平均工具调用: {metrics.get('avg_tool_calls', 0):.1f}次
📈 总时长: {metrics.get('total_duration', 0):.2f}秒
⭐ 评级: {metrics.get('grade', '未知')}

详细结果:
{'-'*60}
"""

        for i, result in enumerate(self.results, 1):
            status = "✅" if result["success"] else "❌"
            report += f"\n{i}. {status} {result['question'][:50]}...\n"
            report += f"   预期: {result['expected_answer']}\n"
            report += f"   实际: {result['actual_answer']}\n"
            report += f"   工具调用: {result['tool_calls']}次, 耗时: {result['duration']:.2f}秒\n"
            if result["feedback"]:
                report += f"   反馈: {result['feedback']}\n"

        return report


class EvaluationRunner:
    """评估运行器"""

    def __init__(self, framework: EvaluationFramework):
        self.framework = framework
        self.metrics = EvaluationMetrics()

    def run(self, skill_instance) -> EvaluationMetrics:
        """
        运行评估

        Args:
            skill_instance: 要评估的技能实例

        Returns:
            评估指标
        """
        import time

        self.metrics.start_evaluation()

        for scenario in self.framework.scenarios:
            start = time.time()

            try:
                # 这里是评估逻辑的占位符
                # 实际使用时需要调用技能并验证结果
                result = skill_instance.execute(
                    question=scenario.question,
                    tools=scenario.tools_required
                )

                duration = time.time() - start

                # 验证答案
                success = str(result.data) == str(scenario.answer)

                self.metrics.record_result(
                    question=scenario.question,
                    expected_answer=scenario.answer,
                    actual_answer=str(result.data) if result.data else "",
                    tool_calls=len(scenario.tools_required),
                    duration=duration,
                    success=success,
                    feedback=result.message if not success else ""
                )

            except Exception as e:
                duration = time.time() - start
                self.metrics.record_result(
                    question=scenario.question,
                    expected_answer=scenario.answer,
                    actual_answer=f"ERROR: {str(e)}",
                    tool_calls=0,
                    duration=duration,
                    success=False,
                    feedback=str(e)
                )

        import time
        self.metrics.end_time = time.time()

        return self.metrics


# ==================== 工具函数 ====================

def create_evaluation_from_template(
    name: str,
    tool_list: List[str],
    scenarios_data: List[Dict[str, Any]]
) -> EvaluationFramework:
    """
    从模板创建评估框架

    Args:
        name: 评估名称
        tool_list: 可用工具列表
        scenarios_data: 场景数据列表

    Returns:
        配置好的评估框架
    """
    framework = EvaluationFramework(name)

    for data in scenarios_data:
        scenario = EvaluationScenario(
            question=data["question"],
            answer=data["answer"],
            category=data.get("category", "general"),
            tools_required=data.get("tools_required", []),
            complexity=data.get("complexity", "medium"),
            metadata=data.get("metadata", {})
        )

        try:
            framework.add_scenario(scenario)
        except ValueError as e:
            print(f"警告: 跳过无效场景 - {e}")

    return framework


# ==================== 示例使用 ====================

if __name__ == "__main__":
    # 创建评估框架
    framework = EvaluationFramework("示例技能评估")

    # 添加示例场景
    scenarios = [
        EvaluationScenario(
            question="查找包含特定关键词的项目数量",
            answer="3",
            tools_required=["search_projects", "filter_results", "count_items"],
            complexity="medium",
            metadata={
                "read_only": True,
                "real_world_use_case": "用户需要统计包含特定功能的项目",
                "time_sensitive": False,
                "requires_judgment": False
            }
        ),
        EvaluationScenario(
            question="列出所有状态为活跃的技能名称",
            answer="api_manager, ollama_ai, local_ocr",
            tools_required=["list_skills", "filter_by_status", "format_output"],
            complexity="low",
            metadata={
                "read_only": True,
                "real_world_use_case": "开发者需要查看可用技能",
                "time_sensitive": False,
                "requires_judgment": False
            }
        ),
    ]

    for scenario in scenarios:
        framework.add_scenario(scenario)

    # 导出评估
    print("=== XML 格式 ===")
    print(framework.to_xml())

    print("\n=== JSON 格式 ===")
    print(framework.to_json())

    # 保存到文件
    framework.save(Path("tests/evaluations/example_evaluation.xml"), format="xml")
    print("\n评估已保存到: tests/evaluations/example_evaluation.xml")

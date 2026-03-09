"""
AI-Agent-Local 评估驱动开发工作流
基于 4 阶段开发模式 + 子代理框架

核心流程：
1. Research - 研究阶段
2. Implementation - 实现阶段（子代理执行）
3. Review - 审查阶段（代码审查）
4. Evaluation - 评估阶段（质量评估）

Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

# 导入子代理框架
from dispatcher import Task, TaskStatus, SubAgentResult, Dispatcher, create_task
from reviewer import CodeReviewer, CodeReview, create_reviewer
from progress_tracker import TrackedDispatcher, ProgressTracker

# 导入评估框架
import sys
sys.path.append(str(Path(__file__).parent.parent / "testing"))
try:
    from evaluation_generator import EvaluationFramework, EvaluationScenario
except ImportError:
    # 如果评估框架不可用，使用简单版本
    EvaluationFramework = None
    EvaluationScenario = None

logger = logging.getLogger(__name__)


# ==================== 工作流阶段 ====================

class WorkflowStage(Enum):
    """工作流阶段"""
    RESEARCH = "research"           # 研究
    IMPLEMENTATION = "implementation"  # 实现
    REVIEW = "review"                # 审查
    EVALUATION = "evaluation"        # 评估
    COMPLETE = "complete"            # 完成


class QualityGate(Enum):
    """质量门控标准"""
    EXCELLENT = "excellent"    # 优秀（9.0+ 分）
    GOOD = "good"              # 良好（7.0+ 分）
    ACCEPTABLE = "acceptable"  # 可接受（5.0+ 分）
    NEEDS_WORK = "needs_work"  # 需改进（< 5.0 分）


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    stage: WorkflowStage
    success: bool
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "stage": self.stage.value,
            "success": self.success,
            "score": self.score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


# ==================== 评估驱动开发工作流 ====================

class EvaluationDrivenWorkflow:
    """
    评估驱动开发工作流

    实现完整的 4 阶段开发流程
    """

    def __init__(
        self,
        dispatcher: Optional[TrackedDispatcher] = None,
        reviewer: Optional[CodeReviewer] = None,
        quality_threshold: float = 7.0,
        max_iterations: int = 3
    ):
        """
        初始化工作流

        Args:
            dispatcher: 子代理调度器
            reviewer: 代码审查器
            quality_threshold: 质量阈值（低于此值需要重新迭代）
            max_iterations: 最大迭代次数
        """
        self.dispatcher = dispatcher or TrackedDispatcher()
        self.reviewer = reviewer or create_reviewer()
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        self.logger = logging.getLogger("workflow")

        # 工作流状态
        self.current_stage = WorkflowStage.RESEARCH
        self.iteration_count = 0
        self.results_history: List[WorkflowResult] = []

    async def execute(
        self,
        tasks: List[Task],
        mode: str = "sequential"
    ) -> List[WorkflowResult]:
        """
        执行完整工作流

        Args:
            tasks: 任务列表
            mode: 执行模式

        Returns:
            各阶段的结果列表
        """
        self.logger.info(f"[工作流] 开始执行评估驱动开发工作流")
        self.logger.info(f"[工作流] 任务数: {len(tasks)}, 模式: {mode}")

        # 阶段 1: 研究
        research_result = await self._research_stage(tasks)
        self.results_history.append(research_result)

        if not research_result.success:
            return self.results_history

        # 迭代执行实现 → 审查 → 评估
        for iteration in range(self.max_iterations):
            self.iteration_count = iteration + 1
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(f"[工作流] 迭代 {iteration + 1}/{self.max_iterations}")
            self.logger.info(f"{'=' * 60}\n")

            # 阶段 2: 实现
            impl_result = await self._implementation_stage(tasks, mode)
            self.results_history.append(impl_result)

            if not impl_result.success:
                self.logger.error(f"[工作流] 实现阶段失败")
                break

            # 阶段 3: 审查
            review_result = await self._review_stage(tasks, impl_result.metadata.get("results", []))
            self.results_history.append(review_result)

            # 阶段 4: 评估
            eval_result = await self._evaluation_stage(tasks, review_result)
            self.results_history.append(eval_result)

            # 检查是否达到质量标准
            if eval_result.score >= self.quality_threshold:
                self.logger.info(f"[工作流] 达到质量标准 ({eval_result.score:.1f} >= {self.quality_threshold})")
                self.results_history.append(WorkflowResult(
                    stage=WorkflowStage.COMPLETE,
                    success=True,
                    score=eval_result.score,
                    metadata={"total_iterations": iteration + 1}
                ))
                break
            else:
                self.logger.warning(
                    f"[工作流] 未达到质量标准 ({eval_result.score:.1f} < {self.quality_threshold})"
                )
                self.logger.info(f"[工作流] 准备下一次迭代...")

                # 根据反馈调整任务
                tasks = await self._adjust_tasks_based_on_feedback(tasks, eval_result)

        return self.results_history

    async def _research_stage(self, tasks: List[Task]) -> WorkflowResult:
        """
        研究阶段

        分析需求，识别关键问题，制定计划

        Args:
            tasks: 任务列表

        Returns:
            研究结果
        """
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"[阶段 1] 研究")
        self.logger.info(f"{'=' * 60}\n")

        try:
            # 分析任务
            total_complexity = sum(
                1 if t.complexity == "high" else 0.5 if t.complexity == "medium" else 0.25
                for t in tasks
            )

            # 识别潜在问题
            issues = []
            if total_complexity > len(tasks):
                issues.append(f"项目复杂度较高（{total_complexity:.1f}），建议分阶段实施")

            # 生成建议
            recommendations = [
                "使用子代理框架并行处理独立任务",
                "启用代码审查以确保质量",
                "创建评估场景以验证实现"
            ]

            self.logger.info(f"[研究] 分析完成")
            self.logger.info(f"[研究] 任务数: {len(tasks)}")
            self.logger.info(f"[研究] 复杂度: {total_complexity:.1f}")
            self.logger.info(f"[研究] 问题: {len(issues)}")
            self.logger.info(f"[研究] 建议: {len(recommendations)}")

            return WorkflowResult(
                stage=WorkflowStage.RESEARCH,
                success=True,
                issues=issues,
                recommendations=recommendations,
                metadata={
                    "total_tasks": len(tasks),
                    "complexity_score": total_complexity
                }
            )

        except Exception as e:
            self.logger.error(f"[研究] 研究阶段失败: {e}")
            return WorkflowResult(
                stage=WorkflowStage.RESEARCH,
                success=False,
                issues=[f"研究失败: {str(e)}"]
            )

    async def _implementation_stage(
        self,
        tasks: List[Task],
        mode: str
    ) -> WorkflowResult:
        """
        实现阶段

        使用子代理框架执行任务

        Args:
            tasks: 任务列表
            mode: 执行模式

        Returns:
            实现结果
        """
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"[阶段 2] 实现")
        self.logger.info(f"{'=' * 60}\n")

        try:
            # 使用调度器执行任务
            results = await self.dispatcher.execute(tasks, mode)

            # 分析结果
            successful = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
            failed = sum(1 for r in results if r.status == TaskStatus.FAILED)

            success_rate = successful / len(results) if results else 0
            score = success_rate * 10.0

            issues = []
            if failed > 0:
                issues.append(f"{failed} 个任务执行失败")

            self.logger.info(f"[实现] 执行完成")
            self.logger.info(f"[实现] 成功: {successful}/{len(results)}")
            self.logger.info(f"[实现] 失败: {failed}")
            self.logger.info(f"[实现] 得分: {score:.1f}/10.0")

            return WorkflowResult(
                stage=WorkflowStage.IMPLEMENTATION,
                success=failed == 0,
                score=score,
                issues=issues,
                metadata={"results": results, "success_rate": success_rate}
            )

        except Exception as e:
            self.logger.error(f"[实现] 实现阶段失败: {e}")
            return WorkflowResult(
                stage=WorkflowStage.IMPLEMENTATION,
                success=False,
                issues=[f"实现失败: {str(e)}"]
            )

    async def _review_stage(
        self,
        tasks: List[Task],
        impl_results: List[SubAgentResult]
    ) -> WorkflowResult:
        """
        审查阶段

        对代码进行质量审查

        Args:
            tasks: 任务列表
            impl_results: 实现结果

        Returns:
            审查结果
        """
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"[阶段 3] 审查")
        self.logger.info(f"{'=' * 60}\n")

        try:
            # 收集所有变更的文件
            all_reviews = []

            for task, result in zip(tasks, impl_results):
                if not result.files_changed:
                    continue

                # 读取文件内容
                code_content = ""
                for file_path in result.files_changed:
                    try:
                        full_path = Path(task.directory) / file_path if task.directory else Path(file_path)
                        if full_path.exists():
                            code_content += f"\n# --- {file_path} ---\n"
                            code_content += full_path.read_text(encoding='utf-8')
                    except Exception as e:
                        self.logger.warning(f"[审查] 无法读取 {file_path}: {e}")

                if code_content:
                    review = await self.reviewer.review(
                        code=code_content,
                        file_path=file_path,
                        task_id=task.id
                    )
                    all_reviews.append(review)

            # 合并审查结果
            if all_reviews:
                total_score = sum(r.score for r in all_reviews) / len(all_reviews)
                all_issues = []
                all_strengths = []
                for review in all_reviews:
                    all_issues.extend(review.issues)
                    all_strengths.extend(review.strengths)

                self.logger.info(f"[审查] 审查完成")
                self.logger.info(f"[审查] 文件数: {len(all_reviews)}")
                self.logger.info(f"[审查] 得分: {total_score:.1f}/10.0")
                self.logger.info(f"[审查] 问题: {len(all_issues)}")
                self.logger.info(f"[审查] 优点: {len(all_strengths)}")

                # 按严重程度分类问题
                critical_issues = [i for i in all_issues if i.severity.value == "critical"]
                important_issues = [i for i in all_issues if i.severity.value == "important"]

                issues = []
                if critical_issues:
                    issues.append(f"{len(critical_issues)} 个关键问题需要立即修复")
                if important_issues:
                    issues.append(f"{len(important_issues)} 个重要问题建议修复")

                return WorkflowResult(
                    stage=WorkflowStage.REVIEW,
                    success=len(critical_issues) == 0,
                    score=total_score,
                    issues=issues,
                    recommendations=[f"优点: {len(all_strengths)}"],
                    metadata={
                        "reviews": all_reviews,
                        "critical_count": len(critical_issues),
                        "important_count": len(important_issues)
                    }
                )
            else:
                self.logger.warning(f"[审查] 没有文件需要审查")
                return WorkflowResult(
                    stage=WorkflowStage.REVIEW,
                    success=True,
                    score=8.0,  # 默认分数
                    metadata={"message": "没有文件需要审查"}
                )

        except Exception as e:
            self.logger.error(f"[审查] 审查阶段失败: {e}")
            return WorkflowResult(
                stage=WorkflowStage.REVIEW,
                success=False,
                issues=[f"审查失败: {str(e)}"]
            )

    async def _evaluation_stage(
        self,
        tasks: List[Task],
        review_result: WorkflowResult
    ) -> WorkflowResult:
        """
        评估阶段

        评估整体质量和完成度

        Args:
            tasks: 任务列表
            review_result: 审查结果

        Returns:
            评估结果
        """
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"[阶段 4] 评估")
        self.logger.info(f"{'=' * 60}\n")

        try:
            # 综合评分
            impl_score = review_result.metadata.get("impl_score", review_result.score)
            review_score = review_result.score

            # 加权平均
            final_score = impl_score * 0.6 + review_score * 0.4

            # 质量门控
            quality_gate = self._get_quality_gate(final_score)

            # 生成建议
            recommendations = []
            if quality_gate == QualityGate.EXCELLENT:
                recommendations.append("代码质量优秀，可以直接部署")
            elif quality_gate == QualityGate.GOOD:
                recommendations.append("代码质量良好，建议进行小优化")
            elif quality_gate == QualityGate.ACCEPTABLE:
                recommendations.append("代码质量可接受，建议修复重要问题")
            else:
                recommendations.append("代码质量不足，需要重新实现")

            self.logger.info(f"[评估] 评估完成")
            self.logger.info(f"[评估] 实现得分: {impl_score:.1f}")
            self.logger.info(f"[评估] 审查得分: {review_score:.1f}")
            self.logger.info(f"[评估] 最终得分: {final_score:.1f}/10.0")
            self.logger.info(f"[评估] 质量等级: {quality_gate.value}")

            return WorkflowResult(
                stage=WorkflowStage.EVALUATION,
                success=final_score >= self.quality_threshold,
                score=final_score,
                issues=review_result.issues,
                recommendations=recommendations,
                metadata={
                    "impl_score": impl_score,
                    "review_score": review_score,
                    "quality_gate": quality_gate.value
                }
            )

        except Exception as e:
            self.logger.error(f"[评估] 评估阶段失败: {e}")
            return WorkflowResult(
                stage=WorkflowStage.EVALUATION,
                success=False,
                issues=[f"评估失败: {str(e)}"]
            )

    async def _adjust_tasks_based_on_feedback(
        self,
        tasks: List[Task],
        eval_result: WorkflowResult
    ) -> List[Task]:
        """
        根据评估反馈调整任务

        Args:
            tasks: 原始任务列表
            eval_result: 评估结果

        Returns:
            调整后的任务列表
        """
        # 根据问题创建修复任务
        adjusted_tasks = []

        for issue in eval_result.issues:
            # 为每个问题创建修复任务
            fix_task = create_task(
                task_id=f"fix-{len(adjusted_tasks)}",
                name=f"修复问题: {issue[:50]}",
                description=f"解决: {issue}",
                requirements=f"1. 分析问题\n2. 实施修复\n3. 验证结果",
                priority=0,  # 高优先级
                complexity="medium",
                task_type="development"
            )
            adjusted_tasks.append(fix_task)

        # 如果没有具体问题，返回优化任务
        if not adjusted_tasks:
            adjusted_tasks = [
                create_task(
                    task_id="optimize",
                    name="优化代码质量",
                    description="优化代码结构和性能",
                    requirements="1. 代码审查\n2. 性能优化\n3. 文档完善",
                    priority=1,
                    complexity="medium",
                    task_type="refactoring"
                )
            ]

        self.logger.info(f"[工作流] 创建了 {len(adjusted_tasks)} 个修复任务")

        return adjusted_tasks

    def _get_quality_gate(self, score: float) -> QualityGate:
        """
        获取质量门控等级

        Args:
            score: 分数

        Returns:
            质量等级
        """
        if score >= 9.0:
            return QualityGate.EXCELLENT
        elif score >= 7.0:
            return QualityGate.GOOD
        elif score >= 5.0:
            return QualityGate.ACCEPTABLE
        else:
            return QualityGate.NEEDS_WORK

    def generate_report(self) -> str:
        """
        生成工作流报告

        Returns:
            格式化的报告字符串
        """
        lines = [
            "\n" + "=" * 70,
            "📋 评估驱动开发工作流报告",
            "=" * 70,
            f"总迭代次数: {self.iteration_count}",
            f"质量阈值: {self.quality_threshold:.1f}",
            "",
            "各阶段结果:",
            "-" * 70
        ]

        for result in self.results_history:
            status = "✅" if result.success else "❌"
            lines.append(
                f"{status} {result.stage.value.upper():15} - "
                f"分数: {result.score:.1f}/10.0"
            )

            if result.issues:
                for issue in result.issues:
                    lines.append(f"    ⚠️  {issue}")

            if result.recommendations:
                for rec in result.recommendations[:2]:  # 只显示前2条
                    lines.append(f"    💡 {rec}")

        lines.append("=" * 70)

        return "\n".join(lines)


# ==================== 工厂函数 ====================

def create_workflow(
    quality_threshold: float = 7.0,
    max_iterations: int = 3,
    enable_review: bool = True,
    enable_progress_tracking: bool = True
) -> EvaluationDrivenWorkflow:
    """
    创建评估驱动开发工作流

    Args:
        quality_threshold: 质量阈值
        max_iterations: 最大迭代次数
        enable_review: 是否启用代码审查
        enable_progress_tracking: 是否启用进度跟踪

    Returns:
        EvaluationDrivenWorkflow 实例
    """
    dispatcher = TrackedDispatcher(
        enable_review=enable_review,
        enable_progress_tracking=enable_progress_tracking
    )
    reviewer = create_reviewer()

    return EvaluationDrivenWorkflow(
        dispatcher=dispatcher,
        reviewer=reviewer,
        quality_threshold=quality_threshold,
        max_iterations=max_iterations
    )


# ==================== 示例使用 ====================

if __name__ == "__main__":
    import asyncio

    async def main():
        # 创建测试任务
        tasks = [
            create_task(
                task_id="task-1",
                name="实现用户认证",
                description="JWT 认证功能",
                requirements="1. 登录接口\n2. 注册接口\n3. JWT 验证",
                priority=1,
                complexity="high",
                task_type="development"
            ),
            create_task(
                task_id="task-2",
                name="编写测试",
                description="单元测试",
                requirements="1. 测试登录\n2. 测试注册",
                priority=2,
                complexity="medium",
                task_type="testing"
            ),
        ]

        # 创建工作流
        workflow = create_workflow(
            quality_threshold=7.0,
            max_iterations=2
        )

        # 执行工作流
        results = await workflow.execute(tasks, mode="sequential")

        # 生成报告
        print(workflow.generate_report())

    # 运行示例
    asyncio.run(main())

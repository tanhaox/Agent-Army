"""
Commander Agent - 主帅Agent（CEO）

核心职责：
- 📊 汇总所有报告（核心）
- ✅ 检查报告质量（打回去重做，多次不行叫HR）
- 📈 监控准确度（实时）⭐ 管理权来源
- 🎯 对AI提要求（管理权）
- 📝 向用户汇报汇总结果

管理权来源：
1. 质量把关权 - 检查报告，不合格打回去重做
2. 准确度监控权 - 实时监控预测准确度，发现问题立即介入
3. 调用HR权 - 多次质量不合格，叫HR来优化AI
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin


class ReportRecord:
    """报告记录"""

    def __init__(self, report: dict):
        self.report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.report = report
        self.agent_name = report.get("agent_name", "unknown")
        self.stock_code = report.get("stock_code", "unknown")
        self.created_at = datetime.now()

        # 提取预测
        self.predictions = self._extract_predictions(report)

        # 计算验证日期
        timeframe = report.get("timeframe", "3个月")
        self.verification_date = self._calculate_verification_date(timeframe)

        # 状态
        self.status = "pending"  # pending/verified
        self.verification_result = None
        self.accuracy = None

    def _extract_predictions(self, report: dict) -> List[dict]:
        """从报告中提取预测"""
        predictions = []

        if "target_price" in report:
            predictions.append({
                "type": "target_price",
                "predicted_value": report["target_price"],
                "timeframe": report.get("timeframe", "3个月")
            })

        if "recommendation" in report:
            predictions.append({
                "type": "recommendation",
                "predicted_value": report["recommendation"],
                "timeframe": "立即"
            })

        return predictions

    def _calculate_verification_date(self, timeframe: str) -> datetime:
        """计算验证日期"""
        if "天" in timeframe:
            days = int(timeframe.replace("天", ""))
            return self.created_at + timedelta(days=days)
        elif "周" in timeframe:
            weeks = int(timeframe.replace("周", ""))
            return self.created_at + timedelta(weeks=weeks)
        elif "月" in timeframe:
            months = int(timeframe.replace("个月", "").replace("月", ""))
            return self.created_at + timedelta(days=months*30)
        else:
            return self.created_at + timedelta(days=90)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "agent_name": self.agent_name,
            "stock_code": self.stock_code,
            "created_at": self.created_at.isoformat(),
            "verification_date": self.verification_date.isoformat(),
            "predictions": self.predictions,
            "status": self.status,
            "accuracy": self.accuracy
        }


class VerificationResult:
    """验证结果"""

    def __init__(self, report_record: ReportRecord):
        self.report_id = report_record.report_id
        self.verification_date = datetime.now()
        self.predictions = report_record.predictions
        self.actual_results = []
        self.accuracy_metrics = {}
        self.overall_accuracy = 0.0
        self.grade = "F"

    def calculate_accuracy(self, actual_data: dict):
        """计算准确率"""
        total_accuracy = 0
        count = 0

        for pred in self.predictions:
            if pred["type"] == "target_price":
                # 价格准确率
                predicted = pred["predicted_value"]
                actual = actual_data.get("current_price", 0)

                if actual > 0:
                    error_rate = abs(predicted - actual) / actual
                    accuracy = max(0, 100 - error_rate * 100)
                    pred["actual_value"] = actual
                    pred["accuracy"] = accuracy
                    total_accuracy += accuracy
                    count += 1

            elif pred["type"] == "recommendation":
                # 建议准确率
                price_change = actual_data.get("price_change_percent", 0)
                predicted_action = pred["predicted_value"]

                if predicted_action == "BUY":
                    correct = price_change > 0
                elif predicted_action == "SELL":
                    correct = price_change < 0
                else:  # HOLD
                    correct = abs(price_change) < 5

                pred["actual_value"] = f"{price_change:.2f}%"
                pred["correct"] = correct
                accuracy = 100 if correct else 0
                pred["accuracy"] = accuracy
                total_accuracy += accuracy
                count += 1

        if count > 0:
            self.overall_accuracy = total_accuracy / count

        # 评级
        self.grade = self._calculate_grade(self.overall_accuracy)

        return self.overall_accuracy

    def _calculate_grade(self, accuracy: float) -> str:
        """计算评级"""
        if accuracy >= 90:
            return "A+"
        elif accuracy >= 85:
            return "A"
        elif accuracy >= 80:
            return "B+"
        elif accuracy >= 75:
            return "B"
        elif accuracy >= 70:
            return "C"
        else:
            return "F"

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "verification_date": self.verification_date.isoformat(),
            "predictions": self.predictions,
            "overall_accuracy": self.overall_accuracy,
            "grade": self.grade
        }


class CommanderAgent(BaseAgent, LoggerMixin):
    """
    Commander Agent - 主帅Agent（CEO）

    核心职责：报告准确度和专业度
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 报告跟踪系统
        self.report_registry = {}  # 报告注册表
        self.pending_verifications = []  # 待验证队列
        self.verification_history = []  # 验证历史

        # AI准确率统计
        self.agent_accuracy_stats = {}

        # 待用户审批的提案
        self.user_approval_queue = []

        # 预审重试计数器
        self.retry_counts = {}  # {agent_name: count}
        self.hr_adjusted = {}   # {agent_name: True/False}

        super().__init__(
            name="Commander Agent",
            role="报告准确度和专业度负责，结果跟踪验证",
            capabilities=[
                AgentCapability(
                    name="report_tracking",
                    description="报告跟踪",
                    input_type="report",
                    output_type="tracking_record"
                ),
                AgentCapability(
                    name="result_verification",
                    description="结果验证",
                    input_type="report_id",
                    output_type="verification_result"
                ),
                AgentCapability(
                    name="accuracy_assessment",
                    description="准确度评估",
                    input_type="verification_data",
                    output_type="accuracy_report"
                ),
                AgentCapability(
                    name="hr_proposal_review",
                    description="HR提案审查",
                    input_type="hr_proposal",
                    output_type="review_decision"
                ),
                AgentCapability(
                    name="user_report",
                    description="向用户汇报",
                    input_type="proposal",
                    output_type="board_report"
                )
            ],
            tools=[
                AgentTool(
                    name="verification_system",
                    description="验证系统",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="accuracy_tracker",
                    description="准确率跟踪器",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("Commander Agent初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "register_report":
            return await self.register_report(kwargs.get("report"))
        elif task == "verify_report":
            return await self.verify_report(kwargs.get("report_id"))
        elif task == "collect_and_review_reports":
            return await self.collect_and_review_reports(kwargs.get("reports"))
        elif task == "reject_report":
            return await self.reject_report(
                kwargs.get("report"),
                kwargs.get("reason"),
                kwargs.get("retry_count", 0)
            )
        elif task == "call_hr_for_help":
            return await self.call_hr_for_help(
                kwargs.get("agent_name"),
                kwargs.get("issue")
            )
        elif task == "review_hr_proposal":
            return await self.review_hr_proposal(kwargs.get("proposal"))
        elif task == "submit_to_user":
            return await self.submit_to_user(kwargs.get("proposal"))
        elif task == "run_daily_verification":
            return await self.run_daily_verification()
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能：报告跟踪 ==========

    async def register_report(self, report: dict) -> dict:
        """注册报告开始跟踪"""
        self.logger.info(f"注册报告", extra={"stock_code": report.get("stock_code")})

        # 创建报告记录
        record = ReportRecord(report)

        # 注册到系统
        self.report_registry[record.report_id] = record

        # 添加到待验证队列
        self.pending_verifications.append({
            "report_id": record.report_id,
            "verify_at": record.verification_date
        })

        self.logger.info(
            f"报告已注册，开始跟踪",
            extra={
                "report_id": record.report_id,
                "verification_date": record.verification_date.isoformat()
            }
        )

        return {
            "report_id": record.report_id,
            "status": "registered",
            "verification_date": record.verification_date.isoformat(),
            "message": f"报告已注册，将在{record.verification_date.strftime('%Y-%m-%d')}验证"
        }

    # ========== 核心功能：结果验证 ==========

    async def verify_report(self, report_id: str) -> dict:
        """验证报告准确性"""
        record = self.report_registry.get(report_id)
        if not record:
            raise ValueError(f"报告不存在: {report_id}")

        self.logger.info(f"开始验证报告", extra={"report_id": report_id})

        # 获取实际数据（简化版，实际应该调用数据源）
        actual_data = await self._get_actual_data(record)

        # 计算准确率
        verification = VerificationResult(record)
        accuracy = verification.calculate_accuracy(actual_data)

        # 更新记录
        record.status = "verified"
        record.verification_result = verification
        record.accuracy = accuracy

        # 更新AI准确率统计
        self._update_agent_accuracy(record.agent_name, accuracy)

        # 移动到历史
        self.verification_history.append(record)

        # 生成验证报告
        verification_report = self._generate_verification_report(record, verification)

        self.logger.info(
            f"报告验证完成",
            extra={
                "report_id": report_id,
                "accuracy": accuracy,
                "grade": verification.grade
            }
        )

        return {
            "report_id": report_id,
            "accuracy": accuracy,
            "grade": verification.grade,
            "verification_report": verification_report
        }

    async def run_daily_verification(self) -> dict:
        """每日验证任务"""
        self.logger.info("开始每日验证任务")

        today = datetime.now()
        verified_count = 0
        results = []

        # 检查所有待验证的报告
        for task in self.pending_verifications[:]:  # 使用切片创建副本
            if task["verify_at"].date() <= today.date():
                # 时间到了，开始验证
                result = await self.verify_report(task["report_id"])
                results.append(result)
                verified_count += 1

                # 从待验证队列移除
                self.pending_verifications.remove(task)

        return {
            "verified_count": verified_count,
            "results": results,
            "message": f"今日验证了{verified_count}份报告"
        }

    async def _get_actual_data(self, record: ReportRecord) -> dict:
        """获取实际数据（简化版）"""
        # 实际应该调用FinancialTool或其他数据源
        # 这里返回模拟数据
        report = record.report

        # 模拟：假设价格有小幅波动
        current_price = report.get("target_price", 0) * 0.95  # 95%的目标价
        original_price = report.get("current_price", 0)

        if original_price > 0:
            price_change_percent = ((current_price - original_price) / original_price) * 100
        else:
            price_change_percent = 0

        return {
            "current_price": current_price,
            "price_change_percent": price_change_percent
        }

    def _update_agent_accuracy(self, agent_name: str, accuracy: float):
        """更新AI准确率统计"""
        if agent_name not in self.agent_accuracy_stats:
            self.agent_accuracy_stats[agent_name] = {
                "total_reports": 0,
                "total_accuracy": 0,
                "average_accuracy": 0,
                "history": []
            }

        stats = self.agent_accuracy_stats[agent_name]
        stats["total_reports"] += 1
        stats["total_accuracy"] += accuracy
        stats["average_accuracy"] = stats["total_accuracy"] / stats["total_reports"]
        stats["history"].append({
            "date": datetime.now().isoformat(),
            "accuracy": accuracy
        })

    def _generate_verification_report(self, record: ReportRecord, verification: VerificationResult) -> str:
        """生成验证报告"""
        report = f"""
【报告验证结果】
━━━━━━━━━━━━━━━━━━━━━━━━━━
报告ID: {record.report_id}
AI: {record.agent_name}
股票: {record.stock_code}
━━━━━━━━━━━━━━━━━━━━━━━━━━

验证日期: {verification.verification_date.strftime('%Y-%m-%d')}
总体准确率: {verification.overall_accuracy:.1f}%
评级: {verification.grade}

详细对比:
"""

        for pred in verification.predictions:
            if pred["type"] == "target_price":
                report += f"""
  目标价格:
    预测: {pred['predicted_value']:.2f}元
    实际: {pred['actual_value']:.2f}元
    准确率: {pred['accuracy']:.1f}%
"""

            elif pred["type"] == "recommendation":
                report += f"""
  投资建议:
    预测: {pred['predicted_value']}
    实际涨跌: {pred['actual_value']}
    判断正确: {'✅' if pred['correct'] else '❌'}
    准确率: {pred['accuracy']:.1f}%
"""

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━
结论: {self._get_conclusion(verification.grade)}
"""

        return report

    def _get_conclusion(self, grade: str) -> str:
        """获取结论"""
        conclusions = {
            "A+": "表现卓越，继续保持！",
            "A": "表现优秀，符合预期！",
            "B+": "表现良好，有提升空间。",
            "B": "表现合格，需要改进。",
            "C": "表现一般，亟需优化。",
            "F": "表现不佳，必须重构！"
        }
        return conclusions.get(grade, "未知评级")

    # ========== 核心功能：HR提案审查 ==========

    async def review_hr_proposal(self, proposal: dict) -> dict:
        """审查HR提案"""
        self.logger.info(
            f"审查HR提案",
            extra={"proposal_id": proposal.get("proposal_id")}
        )

        # 1. 检查是否能提升报告质量
        improves_quality = self._check_quality_improvement(proposal)

        # 2. 检查是否需要花钱
        requires_cost = proposal.get("requires_cost", False)

        # 3. 检查是否涉及安全权限
        requires_permission = proposal.get("requires_permission", False)

        # 4. 做出决策
        if requires_cost or requires_permission:
            # 需要用户审批
            return {
                "approved": False,
                "requires_user_approval": True,
                "reason": "涉及花钱或安全权限，需要用户审批",
                "endorsement": self._create_endorsement(proposal, True)
            }
        elif improves_quality:
            # 批准
            return {
                "approved": True,
                "requires_user_approval": False,
                "reason": "能提升报告质量，批准执行",
                "endorsement": self._create_endorsement(proposal, True)
            }
        else:
            # 拒绝
            return {
                "approved": False,
                "requires_user_approval": False,
                "reason": "不能提升报告质量，拒绝提案",
                "endorsement": self._create_endorsement(proposal, False)
            }

    def _check_quality_improvement(self, proposal: dict) -> bool:
        """检查是否能提升报告质量"""
        benefits = proposal.get("benefits", {})

        # 检查是否有准确率提升
        accuracy_improvement = benefits.get("accuracy_improvement", 0)
        performance_gain = benefits.get("performance_gain", 0)

        return accuracy_improvement > 0 or performance_gain > 0

    def _create_endorsement(self, proposal: dict, endorsed: bool) -> dict:
        """创建背书"""
        return {
            "proposal_id": proposal.get("proposal_id"),
            "endorsed": endorsed,
            "endorser": "Commander Agent",
            "timestamp": datetime.now().isoformat(),
            "reason": "能提升报告准确度和专业度" if endorsed else "不能提升报告质量"
        }

    # ========== 核心功能：向用户汇报 ==========

    async def submit_to_user(self, proposal: dict) -> dict:
        """提交给用户审批"""
        self.logger.info(
            f"提交用户审批",
            extra={"proposal_id": proposal.get("proposal_id")}
        )

        # 创建董事会报告
        board_report = self._create_board_report(proposal)

        # 添加到用户审批队列
        self.user_approval_queue.append({
            "proposal": proposal,
            "board_report": board_report,
            "submitted_at": datetime.now()
        })

        return {
            "status": "submitted",
            "message": "已提交给用户审批",
            "board_report": board_report
        }

    def _create_board_report(self, proposal: dict) -> str:
        """创建董事会报告"""
        costs = proposal.get("costs", {})
        benefits = proposal.get("benefits", {})

        report = f"""
╔═══════════════════════════════════════════════════════════╗
║                    📊 董事会报告                           ║
║              Agent Army 变更提案                          ║
╚═══════════════════════════════════════════════════════════╝

【提案编号】{proposal.get('proposal_id', 'N/A')}
【提案时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}
【提案人】HR Agent

═══════════════════════════════════════════════════════════
📋 提案摘要
═══════════════════════════════════════════════════════════

变更类型：{proposal.get('proposal_type', 'N/A')}
变更目标：{proposal.get('target_agent', 'N/A')}
变更原因：{proposal.get('description', 'N/A')}

═══════════════════════════════════════════════════════════
💰 成本分析
═══════════════════════════════════════════════════════════

一次性成本：¥{costs.get('one_time_cost', 0):,}
月度成本：¥{costs.get('monthly_cost', 0):,}/月
年度总成本：¥{costs.get('annual_cost', 0):,}

═══════════════════════════════════════════════════════════
📈 收益分析
═══════════════════════════════════════════════════════════

准确率提升：{benefits.get('accuracy_improvement', 0)}%
性能提升：{benefits.get('performance_gain', 0)}%

═══════════════════════════════════════════════════════════
👔 主帅背书意见
═══════════════════════════════════════════════════════════

{'✅ 同意背书' if proposal.get('commander_approval') else '❌ 拒绝背书'}

理由：{'能提升报告质量' if proposal.get('commander_approval') else '不能提升报告质量'}

═══════════════════════════════════════════════════════════
📝 请您决策
═══════════════════════════════════════════════════════════

[1] ✅ 批准执行
[2] ❌ 拒绝提案
[3] ❓ 需要更多信息

═══════════════════════════════════════════════════════════
"""
        return report

    # ========== 统计和报告 ==========

    def get_accuracy_dashboard(self) -> dict:
        """获取准确率仪表板"""
        return {
            "总览": {
                "总报告数": len(self.report_registry),
                "已验证": len(self.verification_history),
                "待验证": len(self.pending_verifications)
            },
            "各AI准确率": {
                agent: {
                    "平均准确率": f"{stats['average_accuracy']:.1f}%",
                    "报告数": stats["total_reports"]
                }
                for agent, stats in self.agent_accuracy_stats.items()
            },
            "最近验证": [
                {
                    "report_id": r.report_id,
                    "agent": r.agent_name,
                    "accuracy": f"{r.accuracy:.1f}%",
                    "grade": r.verification_result.grade if r.verification_result else "N/A"
                }
                for r in self.verification_history[-5:]  # 最近5份
            ]
        }

    # ========== 核心功能：汇总和质量管理 ==========

    async def collect_and_review_reports(self, reports: List[dict]) -> dict:
        """
        汇总和检查所有报告（核心职责）

        Args:
            reports: 所有AI生成的报告列表

        Returns:
            汇总结果和质量检查报告
        """
        self.logger.info(f"开始汇总和检查{len(reports)}份报告")

        # 1. 汇总报告
        summary = {
            "total_reports": len(reports),
            "reports_by_corps": {},
            "quality_issues": [],
            "accuracy_warnings": [],
            "approved_reports": [],
            "rejected_reports": []
        }

        # 2. 检查每份报告的质量
        for report in reports:
            agent_name = report.get("agent_name", "unknown")
            corps = report.get("corps", "unknown")

            # 按军团分类
            if corps not in summary["reports_by_corps"]:
                summary["reports_by_corps"][corps] = []
            summary["reports_by_corps"][corps].append(report)

            # 质量检查
            quality_check = await self._check_report_quality(report)

            if quality_check["approved"]:
                summary["approved_reports"].append({
                    "agent_name": agent_name,
                    "report_id": report.get("report_id"),
                    "quality_score": quality_check["quality_score"]
                })
            else:
                summary["rejected_reports"].append({
                    "agent_name": agent_name,
                    "report_id": report.get("report_id"),
                    "issues": quality_check["issues"],
                    "retry_count": report.get("retry_count", 0)
                })

        # 3. 生成汇总报告
        summary_report = self._generate_summary_report(summary)

        return {
            "summary": summary,
            "summary_report": summary_report,
            "message": f"汇总完成：{len(summary['approved_reports'])}份通过，{len(summary['rejected_reports'])}份需要重做"
        }

    async def _check_report_quality(self, report: dict) -> dict:
        """检查报告质量"""
        issues = []
        quality_score = 100

        # 1. 检查完整度
        required_fields = ["stock_code", "analysis", "recommendation", "timestamp"]
        for field in required_fields:
            if field not in report:
                issues.append(f"缺少必要字段：{field}")
                quality_score -= 20

        # 2. 检查专业度
        analysis = report.get("analysis", "")
        if len(analysis) < 100:
            issues.append("分析内容过短，不够详细")
            quality_score -= 15

        # 3. 检查准确度指标（如果有历史数据）
        agent_name = report.get("agent_name")
        if agent_name in self.agent_accuracy_stats:
            avg_accuracy = self.agent_accuracy_stats[agent_name]["average_accuracy"]
            if avg_accuracy < 70:
                issues.append(f"该AI历史准确率过低：{avg_accuracy:.1f}%")
                quality_score -= 25

        # 4. 检查建议合理性
        recommendation = report.get("recommendation")
        if recommendation not in ["BUY", "SELL", "HOLD", "STRONG_BUY"]:
            issues.append(f"投资建议不合规：{recommendation}")
            quality_score -= 20

        approved = len(issues) == 0 and quality_score >= 70

        return {
            "approved": approved,
            "quality_score": quality_score,
            "issues": issues
        }

    async def reject_report(self, report: dict, reason: str, retry_count: int = 0) -> dict:
        """
        打回去重做

        Args:
            report: 被拒绝的报告
            reason: 拒绝原因
            retry_count: 已重试次数

        Returns:
            拒绝决策
        """
        agent_name = report.get("agent_name", "unknown")

        self.logger.warning(
            f"打回去重做",
            extra={
                "agent_name": agent_name,
                "reason": reason,
                "retry_count": retry_count
            }
        )

        # 检查重试次数
        if retry_count >= 3:
            # 多次不行，叫HR来优化
            return await self.call_hr_for_help(
                agent_name,
                {
                    "issue_type": "quality_failure",
                    "description": f"{agent_name}连续{retry_count}次质量不合格",
                    "reason": reason,
                    "retry_count": retry_count
                }
            )

        # 打回去重做
        return {
            "action": "reject_and_retry",
            "agent_name": agent_name,
            "reason": reason,
            "retry_count": retry_count + 1,
            "message": f"报告质量不合格，打回去重做（第{retry_count + 1}次）",
            "requirements": self._generate_improvement_requirements(reason)
        }

    async def call_hr_for_help(self, agent_name: str, issue: dict) -> dict:
        """
        叫HR来优化AI

        Args:
            agent_name: 有问题的AI名称
            issue: 问题描述

        Returns:
            HR介入决策
        """
        self.logger.error(
            f"叫HR来优化AI",
            extra={
                "agent_name": agent_name,
                "issue": issue
            }
        )

        # 生成HR优化请求
        hr_request = {
            "request_id": f"HR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "target_agent": agent_name,
            "issue": issue,
            "requested_by": "Commander Agent",
            "timestamp": datetime.now().isoformat(),
            "priority": "HIGH" if issue.get("retry_count", 0) >= 3 else "MEDIUM"
        }

        return {
            "action": "call_hr",
            "hr_request": hr_request,
            "message": f"{agent_name}多次质量不合格，已叫HR来优化",
            "next_steps": [
                "HR将分析该AI的性能问题",
                "HR将提出优化方案",
                "Commander审批后HR执行优化",
                "优化后该AI重新提交报告"
            ]
        }

    def _generate_improvement_requirements(self, reason: str) -> List[str]:
        """生成改进要求"""
        requirements = []

        if "缺少必要字段" in reason:
            requirements.append("确保报告包含所有必要字段")
        if "分析内容过短" in reason:
            requirements.append("增加分析深度，至少200字")
        if "准确率过低" in reason:
            requirements.append("检查数据源和计算逻辑")
        if "投资建议不合规" in reason:
            requirements.append("使用标准的投资建议术语")

        return requirements

    def _generate_summary_report(self, summary: dict) -> str:
        """生成汇总报告给用户"""
        report = f"""
╔═══════════════════════════════════════════════════════════╗
║                    📊 主帅汇总报告                          ║
║              Agent Army 投资分析汇总                        ║
╚═══════════════════════════════════════════════════════════╝

【报告时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}
【汇总人】Commander Agent（主帅）

═══════════════════════════════════════════════════════════
📋 总体情况
═══════════════════════════════════════════════════════════

总报告数：{summary['total_reports']}
✅ 通过质检：{len(summary['approved_reports'])}份
❌ 需要重做：{len(summary['rejected_reports'])}份

═══════════════════════════════════════════════════════════
🎖️ 各军团报告情况
═══════════════════════════════════════════════════════════
"""

        for corps, reports in summary["reports_by_corps"].items():
            report += f"\n{corps}：{len(reports)}份报告\n"

        if summary["approved_reports"]:
            report += f"""
═══════════════════════════════════════════════════════════
✅ 通过质检的报告
═══════════════════════════════════════════════════════════
"""
            for approved in summary["approved_reports"]:
                report += f"  • {approved['agent_name']}: 质量分{approved['quality_score']}分\n"

        if summary["rejected_reports"]:
            report += f"""
═══════════════════════════════════════════════════════════
❌ 需要重做的报告
═══════════════════════════════════════════════════════════
"""
            for rejected in summary["rejected_reports"]:
                report += f"  • {rejected['agent_name']}: {', '.join(rejected['issues'])}\n"
                if rejected['retry_count'] >= 3:
                    report += f"    ⚠️ 已重试{rejected['retry_count']}次，已叫HR介入\n"

        report += """
═══════════════════════════════════════════════════════════
📝 主帅意见
═══════════════════════════════════════════════════════════
"""

        if len(summary["rejected_reports"]) == 0:
            report += "✅ 所有报告质量合格，可以据此做出投资决策。\n"
        else:
            report += f"⚠️ {len(summary['rejected_reports'])}份报告需要重做，请等待更新后再决策。\n"

        report += """
═══════════════════════════════════════════════════════════
"""
        return report

    # ========== 核心功能：增量预审（方案C v2）==========

    async def precheck_report(
        self,
        agent_name: str,
        report_type: str,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        预审单个Agent的报告（增量审核）

        Args:
            agent_name: Agent名称
            report_type: 报告类型（industry/fundamental）
            report_data: 报告数据

        Returns:
            {
                "approved": True/False,
                "critical_error": True/False,  # 严重错误（工具坏了）
                "error_type": str,             # 错误类型
                "quality_score": 0-100,
                "issues": ["问题1", "问题2"],
                "missing_content": ["需要补充1", "需要补充2"],
                "status": "待用"/"不合格"/"系统错误"/"放弃",
                "give_up": True/False,         # 是否放弃该Agent
                "retry_count": int,            # 重试次数
                "action": "retry"/"notify_user"/"call_hr"
            }
        """
        self.logger.info(
            f"预审报告",
            extra={
                "agent_name": agent_name,
                "report_type": report_type
            }
        )

        # Step 1: 检测严重错误（工具坏了）
        if self._is_critical_error(report_data):
            error_type = self._detect_error_type(report_data)
            self.logger.error(
                f"检测到严重错误",
                extra={
                    "agent_name": agent_name,
                    "error_type": error_type
                }
            )
            return {
                "approved": False,
                "critical_error": True,
                "error_type": error_type,
                "quality_score": 0,
                "issues": [f"系统错误: {error_type}"],
                "missing_content": [],
                "status": "系统错误",
                "action": "notify_user",
                "message": f"检测到严重错误（{error_type}），已停止分析任务"
            }

        # Step 2: 检查重试次数
        retry_count = self.retry_counts.get(agent_name, 0)
        hr_adjusted = self.hr_adjusted.get(agent_name, False)

        # Step 3: 执行预审
        if report_type == "industry":
            result = await self._precheck_industry(report_data)
        elif report_type == "fundamental":
            result = await self._precheck_fundamental(report_data)
        else:
            result = {
                "approved": False,
                "quality_score": 0,
                "issues": ["未知报告类型"],
                "missing_content": []
            }

        # Step 4: 处理预审结果
        if result["approved"]:
            # 通过预审，重置计数器
            self.retry_counts[agent_name] = 0
            result["status"] = "待用"
            result["retry_count"] = 0
            self.logger.info(
                f"预审通过",
                extra={
                    "agent_name": agent_name,
                    "quality_score": result["quality_score"]
                }
            )
        else:
            # 未通过预审
            if retry_count >= 4:
                # Agent重试3次（retry_count 1-3）+ HR调整后重试1次（retry_count 4）= 总共4次
                # 仍然不合格，放弃该Agent
                self.logger.error(
                    f"放弃该Agent",
                    extra={
                        "agent_name": agent_name,
                        "retry_count": retry_count,
                        "hr_adjusted": True
                    }
                )
                result["give_up"] = True
                result["status"] = "放弃"
                result["reason"] = f"{agent_name}经过{retry_count}次尝试（含HR调整）后仍不合格，已放弃该部分分析"
                result["fallback"] = "使用警告标记继续"
                result["retry_count"] = retry_count
                result["hr_adjusted"] = True
            elif retry_count == 3:
                # Agent已重试3次，标记需要HR调整
                result["action"] = "call_hr"
                result["retry_count"] = retry_count + 1
                result["status"] = "不合格-需HR调整"

                # 更新重试计数器
                self.retry_counts[agent_name] = retry_count + 1
                # 标记已由HR调整（模拟）
                self.hr_adjusted[agent_name] = True

                self.logger.warning(
                    f"预审未通过，需要HR介入",
                    extra={
                        "agent_name": agent_name,
                        "retry_count": retry_count + 1,
                        "issues": result["issues"]
                    }
                )
            else:
                # 需要重试
                result["action"] = "retry"
                result["retry_count"] = retry_count + 1
                result["status"] = "不合格"

                # 更新重试计数器
                self.retry_counts[agent_name] = retry_count + 1

                self.logger.warning(
                    f"预审未通过",
                    extra={
                        "agent_name": agent_name,
                        "retry_count": retry_count + 1,
                        "issues": result["issues"]
                    }
                )

        return result

    def _is_critical_error(self, data: Dict[str, Any]) -> bool:
        """
        检测严重错误（工具坏了）

        Args:
            data: 报告数据

        Returns:
            是否为严重错误
        """
        # 1. API欠费或配额不足
        if data.get("error_code") in ["API_PAYMENT_REQUIRED", "API_QUOTA_EXCEEDED", "INSUFFICIENT_BALANCE"]:
            return True

        # 2. 网络不通
        if data.get("error_code") in ["NETWORK_ERROR", "TIMEOUT", "CONNECTION_FAILED"]:
            return True

        # 3. 完全没有数据
        if not data or len(data) == 0:
            return True

        # 4. 数据源返回错误
        if "error" in data and data.get("data") is None:
            return True

        # 5. 数据为空字典或只有错误信息
        if len(data) == 1 and "error" in data:
            return True

        return False

    def _detect_error_type(self, data: Dict[str, Any]) -> str:
        """
        检测错误类型

        Args:
            data: 报告数据

        Returns:
            错误类型描述
        """
        error_code = data.get("error_code", "")

        if "PAYMENT" in error_code or "QUOTA" in error_code or "BALANCE" in error_code:
            return "API欠费或配额不足"
        elif "NETWORK" in error_code or "TIMEOUT" in error_code or "CONNECTION" in error_code:
            return "网络连接失败"
        elif not data or len(data) == 0:
            return "数据源无返回数据"
        elif "error" in data:
            return f"数据源错误: {data.get('error', '未知错误')}"
        else:
            return "未知错误"

    async def _precheck_industry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预审产业链分析报告

        Args:
            data: 产业链分析报告数据

        Returns:
            预审结果
        """
        issues = []
        missing_content = []

        # 检查必需字段
        if not data.get("industry_name"):
            issues.append("缺少行业名称")
            missing_content.append("需要补充行业名称")

        if not data.get("growth_driver") or len(data.get("growth_driver", [])) == 0:
            issues.append("缺少成长驱动因素")
            missing_content.append("产业链分析缺少足够的成长驱动因素（至少需要2-3个）")

        if not data.get("risk_factors") or len(data.get("risk_factors", [])) == 0:
            issues.append("缺少风险因素")
            missing_content.append("缺少足够的风险提示（至少需要2条）")

        if data.get("score", 0) == 0:
            issues.append("行业评分为0")
            missing_content.append("行业评分计算异常，请检查数据源")

        # 计算质量评分
        quality_score = 100 - len(issues) * 20

        return {
            "approved": len(issues) == 0,
            "quality_score": max(0, quality_score),
            "issues": issues,
            "missing_content": missing_content
        }

    async def _precheck_fundamental(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预审基本面分析报告

        Args:
            data: 基本面分析报告数据

        Returns:
            预审结果
        """
        issues = []
        missing_content = []

        # 检查必需字段
        if not data.get("stock_name"):
            issues.append("缺少股票名称")
            missing_content.append("需要补充股票名称")

        if data.get("composite_score", 0) == 0:
            issues.append("综合评分为0，数据可能不完整")
            missing_content.append("基本面数据不完整，需要补充财务数据")

        key_metrics = data.get("key_metrics", {})
        if not key_metrics:
            issues.append("缺少核心财务指标")
            missing_content.append("需要补充ROE、EPS等核心财务指标")
        else:
            if key_metrics.get("roe", 0) == 0:
                issues.append("ROE为0，可能缺少关键财务数据")
                missing_content.append("缺少ROE（净资产收益率）数据")

        scores = data.get("scores", {})
        if not scores:
            issues.append("缺少评分细项")
            missing_content.append("需要补充财务质量、盈利能力等评分细项")

        # 计算质量评分
        quality_score = 100 - len(issues) * 20

        return {
            "approved": len(issues) == 0,
            "quality_score": max(0, quality_score),
            "issues": issues,
            "missing_content": missing_content
        }

    async def handle_precheck_failure(
        self,
        agent_name: str,
        precheck_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理预审失败

        Args:
            agent_name: Agent名称
            precheck_result: 预审结果

        Returns:
            处理决策
        """
        # 严重错误 → 通知用户
        if precheck_result.get("critical_error"):
            return {
                "action": "notify_user",
                "error_type": precheck_result["error_type"],
                "message": precheck_result["message"],
                "stop_analysis": True
            }

        # 放弃该Agent → 用警告继续
        if precheck_result.get("give_up"):
            return {
                "action": "continue_with_warning",
                "message": f"{agent_name}已放弃，其他Agent继续工作",
                "warnings": [precheck_result["reason"]]
            }

        retry_count = precheck_result["retry_count"]

        # Agent重试 ≤ 3次
        if retry_count <= 3:
            return {
                "action": "retry_agent",
                "retry_count": retry_count,
                "requirements": precheck_result["missing_content"],
                "message": f"{agent_name}需要补充内容后重新提交（第{retry_count}次重试）"
            }
        else:
            # Agent重试3次失败，叫HR
            return {
                "action": "call_hr",
                "agent_name": agent_name,
                "issue": {
                    "type": "quality_failure",
                    "retry_count": retry_count,
                    "issues": precheck_result["issues"],
                    "missing_content": precheck_result["missing_content"]
                },
                "message": f"{agent_name}重试{retry_count}次仍不合格，已呼叫HR介入"
            }

    def mark_hr_adjusted(self, agent_name: str):
        """标记Agent已由HR调整"""
        self.hr_adjusted[agent_name] = True
        self.logger.info(f"Agent已由HR调整", extra={"agent_name": agent_name})

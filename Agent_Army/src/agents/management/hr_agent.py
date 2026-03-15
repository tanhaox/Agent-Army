"""
HR Agent - 人力资源Agent

职责：
- Agent性能监控
- Agent优化配置
- Agent能力评估
- 提出改进提案
- 执行已批准的改进方案

权限分级：
- 自主执行：参数微调、配置优化（不花钱不涉权）
- 需主帅批准：代码重构、算法优化
- 需用户批准：花钱（API费用）、安全权限（代码生成能力）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import yaml
import json

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin


class AgentPerformanceRecord:
    """Agent性能记录"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.average_response_time = 0.0
        self.accuracy_rate = 0.0
        self.last_updated = datetime.now()

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / max(self.total_tasks, 1) * 100,
            "average_response_time": self.average_response_time,
            "accuracy_rate": self.accuracy_rate,
            "last_updated": self.last_updated.isoformat()
        }


class HRProposal:
    """HR提案"""

    def __init__(
        self,
        proposal_id: str,
        target_agent: str,
        proposal_type: str,
        description: str,
        costs: dict = None,
        benefits: dict = None
    ):
        self.proposal_id = proposal_id
        self.target_agent = target_agent
        self.proposal_type = proposal_type  # optimization/upgrade/refactor
        self.description = description
        self.costs = costs or {}
        self.benefits = benefits or {}

        # 判断是否需要特殊审批
        self.requires_cost = self._check_requires_cost()
        self.requires_permission = self._check_requires_permission()

        # 审批状态
        self.commander_approval = None
        self.user_approval = None
        self.status = "pending"  # pending/approved/rejected/executed

    def _check_requires_cost(self) -> bool:
        """检查是否需要花钱"""
        return self.costs.get("annual_cost", 0) > 0

    def _check_requires_permission(self) -> bool:
        """检查是否需要特殊权限"""
        return self.proposal_type in ["code_generation", "security_change"]

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "target_agent": self.target_agent,
            "proposal_type": self.proposal_type,
            "description": self.description,
            "costs": self.costs,
            "benefits": self.benefits,
            "requires_cost": self.requires_cost,
            "requires_permission": self.requires_permission,
            "commander_approval": self.commander_approval,
            "user_approval": self.user_approval,
            "status": self.status
        }


class HRAgent(BaseAgent, LoggerMixin):
    """
    HR Agent - 人力资源Agent

    负责agent的优化、配置管理和性能监控
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化性能记录
        self.agent_registry = {}  # agent注册表
        self.performance_records = {}  # 性能记录
        self.proposals = {}  # 提案记录

        # 配置文件路径
        self.config_path = Path("config/agents.yaml")

        super().__init__(
            name="HR Agent",
            role="Agent性能优化和配置管理",
            capabilities=[
                AgentCapability(
                    name="agent_monitoring",
                    description="监控agent性能",
                    input_type="agent_list",
                    output_type="performance_report"
                ),
                AgentCapability(
                    name="performance_analysis",
                    description="分析性能数据",
                    input_type="performance_data",
                    output_type="analysis_report"
                ),
                AgentCapability(
                    name="config_management",
                    description="管理配置文件",
                    input_type="config_changes",
                    output_type="config_status"
                ),
                AgentCapability(
                    name="optimization_proposal",
                    description="提出优化方案",
                    input_type="performance_issues",
                    output_type="optimization_proposal"
                )
            ],
            tools=[
                AgentTool(
                    name="config_editor",
                    description="配置文件编辑器",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="performance_tracker",
                    description="性能跟踪器",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("HR Agent初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "monitor_agents":
            return await self.monitor_all_agents()
        elif task == "analyze_performance":
            return await self.analyze_performance(kwargs.get("agent_name"))
        elif task == "propose_optimization":
            return await self.propose_optimization(
                kwargs.get("agent_name"),
                kwargs.get("issue")
            )
        elif task == "execute_optimization":
            return await self.execute_optimization(kwargs.get("proposal_id"))
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def register_agent(self, agent_info: dict):
        """注册agent到HR系统"""
        agent_name = agent_info["name"]
        self.agent_registry[agent_name] = agent_info
        self.performance_records[agent_name] = AgentPerformanceRecord(agent_name)

        self.logger.info(f"Agent已注册", extra={"agent_name": agent_name})

    async def monitor_all_agents(self) -> Dict[str, Any]:
        """监控所有agent性能"""
        self.logger.info("开始监控所有agent")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.agent_registry),
            "agents": {}
        }

        for agent_name, agent_info in self.agent_registry.items():
            performance = self.performance_records.get(agent_name)
            if performance:
                report["agents"][agent_name] = performance.to_dict()

        # 识别问题agent
        report["issues"] = self._identify_issues()

        return report

    async def analyze_performance(self, agent_name: str) -> Dict[str, Any]:
        """分析单个agent性能"""
        self.logger.info(f"分析agent性能", extra={"agent_name": agent_name})

        performance = self.performance_records.get(agent_name)
        if not performance:
            raise ValueError(f"Agent未注册: {agent_name}")

        analysis = {
            "agent_name": agent_name,
            "performance": performance.to_dict(),
            "trend": self._calculate_trend(agent_name),
            "issues": self._identify_agent_issues(performance),
            "recommendations": self._generate_recommendations(performance)
        }

        return analysis

    async def propose_optimization(
        self,
        agent_name: str,
        issue: dict
    ) -> Dict[str, Any]:
        """提出优化方案"""
        self.logger.info(
            f"提出优化方案",
            extra={"agent_name": agent_name, "issue": issue}
        )

        # 生成提案ID
        proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.proposals)+1:03d}"

        # 分析问题和收益
        proposal_type = self._determine_proposal_type(issue)
        costs = self._estimate_costs(issue)
        benefits = self._estimate_benefits(issue)

        # 创建提案
        proposal = HRProposal(
            proposal_id=proposal_id,
            target_agent=agent_name,
            proposal_type=proposal_type,
            description=issue.get("description", ""),
            costs=costs,
            benefits=benefits
        )

        self.proposals[proposal_id] = proposal

        # 判断审批流程
        approval_flow = self._determine_approval_flow(proposal)

        return {
            "proposal_id": proposal_id,
            "proposal": proposal.to_dict(),
            "approval_flow": approval_flow,
            "message": f"提案已创建，需要{approval_flow}审批"
        }

    async def execute_optimization(self, proposal_id: str) -> Dict[str, Any]:
        """执行优化方案"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"提案不存在: {proposal_id}")

        # 检查审批状态
        if proposal.status != "approved":
            raise ValueError(f"提案未批准，当前状态: {proposal.status}")

        self.logger.info(
            f"执行优化方案",
            extra={"proposal_id": proposal_id}
        )

        # 执行优化（根据类型）
        if proposal.proposal_type == "config_change":
            result = await self._execute_config_change(proposal)
        elif proposal.proposal_type == "algorithm_optimization":
            result = await self._execute_algorithm_optimization(proposal)
        else:
            result = await self._execute_generic_optimization(proposal)

        # 更新状态
        proposal.status = "executed"

        return {
            "proposal_id": proposal_id,
            "status": "executed",
            "result": result
        }

    # ========== 辅助方法 ==========

    def _identify_issues(self) -> List[dict]:
        """识别有问题的agent"""
        issues = []

        for agent_name, performance in self.performance_records.items():
            # 准确率低于70%
            if performance.accuracy_rate < 70:
                issues.append({
                    "agent_name": agent_name,
                    "issue_type": "low_accuracy",
                    "severity": "HIGH",
                    "value": performance.accuracy_rate,
                    "threshold": 70
                })

            # 成功率低于95%
            success_rate = performance.successful_tasks / max(performance.total_tasks, 1) * 100
            if success_rate < 95:
                issues.append({
                    "agent_name": agent_name,
                    "issue_type": "low_success_rate",
                    "severity": "MEDIUM",
                    "value": success_rate,
                    "threshold": 95
                })

            # 响应时间超过3秒
            if performance.average_response_time > 3:
                issues.append({
                    "agent_name": agent_name,
                    "issue_type": "slow_response",
                    "severity": "LOW",
                    "value": performance.average_response_time,
                    "threshold": 3
                })

        return issues

    def _identify_agent_issues(self, performance: AgentPerformanceRecord) -> List[dict]:
        """识别单个agent的问题"""
        issues = []

        if performance.accuracy_rate < 70:
            issues.append({
                "type": "low_accuracy",
                "description": f"准确率{performance.accuracy_rate:.1f}%低于70%",
                "severity": "HIGH"
            })

        success_rate = performance.successful_tasks / max(performance.total_tasks, 1) * 100
        if success_rate < 95:
            issues.append({
                "type": "low_success_rate",
                "description": f"成功率{success_rate:.1f}%低于95%",
                "severity": "MEDIUM"
            })

        return issues

    def _generate_recommendations(self, performance: AgentPerformanceRecord) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if performance.accuracy_rate < 70:
            recommendations.append("考虑优化算法或升级模型")
            recommendations.append("增加训练数据或调整参数")

        if performance.average_response_time > 3:
            recommendations.append("优化查询逻辑")
            recommendations.append("考虑缓存机制")

        return recommendations

    def _calculate_trend(self, agent_name: str) -> str:
        """计算性能趋势"""
        # 简化版本：实际应该基于历史数据
        return "stable"  # stable/improving/declining

    def _determine_proposal_type(self, issue: dict) -> str:
        """确定提案类型"""
        issue_type = issue.get("issue_type", "")

        if issue_type == "low_accuracy":
            return "algorithm_optimization"
        elif issue_type == "slow_response":
            return "performance_optimization"
        else:
            return "config_change"

    def _estimate_costs(self, issue: dict) -> dict:
        """估算成本"""
        # 如果issue中包含costs信息，直接使用
        if "costs" in issue:
            return issue["costs"]

        # 简化版本：实际应该详细估算
        return {
            "one_time_cost": 0,
            "monthly_cost": 0,
            "annual_cost": 0
        }

    def _estimate_benefits(self, issue: dict) -> dict:
        """估算收益"""
        # 简化版本：实际应该详细估算
        return {
            "accuracy_improvement": 10,  # 预计提升10%
            "performance_gain": 20       # 性能提升20%
        }

    def _determine_approval_flow(self, proposal: HRProposal) -> str:
        """确定审批流程"""
        if proposal.requires_cost or proposal.requires_permission:
            return "user"  # 需要用户审批
        elif proposal.proposal_type in ["algorithm_optimization", "code_refactor"]:
            return "commander"  # 需要主帅审批
        else:
            return "hr_auto"  # HR自主决策

    async def _execute_config_change(self, proposal: HRProposal) -> dict:
        """执行配置变更"""
        self.logger.info(f"执行配置变更: {proposal.proposal_id}")

        # 读取配置
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        # 修改配置（示例）
        # 实际应该根据proposal具体内容修改

        # 保存配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

        return {"status": "success", "message": "配置已更新"}

    async def _execute_algorithm_optimization(self, proposal: HRProposal) -> dict:
        """执行算法优化"""
        self.logger.info(f"执行算法优化: {proposal.proposal_id}")
        # 实际应该调用具体的优化逻辑
        return {"status": "success", "message": "算法已优化"}

    async def _execute_generic_optimization(self, proposal: HRProposal) -> dict:
        """执行通用优化"""
        self.logger.info(f"执行通用优化: {proposal.proposal_id}")
        return {"status": "success", "message": "优化已完成"}

    # ========== 便捷方法 ==========

    def update_agent_performance(
        self,
        agent_name: str,
        success: bool,
        response_time: float,
        accuracy: Optional[float] = None
    ):
        """更新agent性能数据"""
        performance = self.performance_records.get(agent_name)
        if performance:
            performance.total_tasks += 1
            if success:
                performance.successful_tasks += 1
            else:
                performance.failed_tasks += 1

            # 更新平均响应时间
            performance.average_response_time = (
                (performance.average_response_time * (performance.total_tasks - 1) + response_time)
                / performance.total_tasks
            )

            # 更新准确率（如果提供）
            if accuracy is not None:
                performance.accuracy_rate = accuracy

            performance.last_updated = datetime.now()

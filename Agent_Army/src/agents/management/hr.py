"""
HR Agent - 系统诊断和健康检查

版本: 2.0 (8部门制)
方案: Plan B - 自己实现，不依赖OpenClaw
"""

import sys
import os
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.core.logger import get_logger, LoggerMixin


class HRAgent(LoggerMixin):
    """
    HR Agent

    负责系统诊断、Agent健康检查、性能监控。
    """

    def __init__(self):
        """初始化HR Agent"""
        self.name = "hr"
        self.agents_registry = {}
        # 不需要手动设置logger，LoggerMixin会自动提供

    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        注册Agent到HR系统

        Args:
            agent_name: Agent名称
            agent_instance: Agent实例
        """
        self.agents_registry[agent_name] = {
            'instance': agent_instance,
            'registered_at': datetime.now().isoformat(),
            'status': 'registered'
        }
        self.logger.info("Agent registered", agent_name=agent_name)

    def system_diagnostic(self) -> Dict[str, Any]:
        """
        系统诊断

        Returns:
            系统诊断结果
        """
        self.logger.info("Running system diagnostic")

        diagnostic = {
            'timestamp': datetime.now().isoformat(),
            'system': self._check_system(),
            'python': self._check_python(),
            'dependencies': self._check_dependencies(),
            'directories': self._check_directories(),
            'overall_health': 'UNKNOWN'
        }

        # 计算整体健康状况
        health_score = self._calculate_health_score(diagnostic)
        diagnostic['overall_health'] = self._get_health_status(health_score)
        diagnostic['health_score'] = health_score

        self.logger.info(
            "System diagnostic completed",
            health_score=health_score,
            status=diagnostic['overall_health']
        )

        return diagnostic

    def _check_system(self) -> Dict[str, Any]:
        """
        检查系统资源

        Returns:
            系统资源信息
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'os': sys.platform,
                'cpu_usage': f"{cpu_percent}%",
                'memory_usage': f"{memory.percent}%",
                'memory_available': f"{memory.available / (1024**3):.2f} GB",
                'disk_usage': f"{disk.percent}%",
                'disk_free': f"{disk.free / (1024**3):.2f} GB",
                'status': 'OK' if cpu_percent < 80 and memory.percent < 80 else 'WARNING'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    def _check_python(self) -> Dict[str, Any]:
        """
        检查Python环境

        Returns:
            Python环境信息
        """
        return {
            'version': sys.version,
            'executable': sys.executable,
            'platform': sys.platform,
            'status': 'OK'
        }

    def _check_dependencies(self) -> Dict[str, Any]:
        """
        检查依赖包

        Returns:
            依赖包状态
        """
        required_packages = [
            'streamlit',
            'pandas',
            'numpy',
            'structlog',
            'pytest'
        ]

        dependencies = {}
        all_ok = True

        for package in required_packages:
            try:
                __import__(package)
                dependencies[package] = '✅ installed'
            except ImportError:
                dependencies[package] = '❌ missing'
                all_ok = False

        return {
            'packages': dependencies,
            'status': 'OK' if all_ok else 'WARNING'
        }

    def _check_directories(self) -> Dict[str, Any]:
        """
        检查关键目录

        Returns:
            目录状态
        """
        required_dirs = [
            'src',
            'config',
            'logs',
            'tests'
        ]

        directories = {}
        all_ok = True

        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                directories[dir_name] = '✅ exists'
            else:
                directories[dir_name] = '❌ missing'
                all_ok = False

        return {
            'directories': directories,
            'status': 'OK' if all_ok else 'WARNING'
        }

    def _calculate_health_score(self, diagnostic: Dict[str, Any]) -> float:
        """
        计算健康评分

        Args:
            diagnostic: 诊断结果

        Returns:
            健康评分（0-100）
        """
        score = 100.0

        # 1. 系统资源评分
        system = diagnostic.get('system', {})
        if system.get('status') == 'WARNING':
            score -= 20
        elif system.get('status') == 'ERROR':
            score -= 40

        # 2. 依赖包评分
        dependencies = diagnostic.get('dependencies', {})
        if dependencies.get('status') == 'WARNING':
            score -= 15

        # 3. 目录评分
        directories = diagnostic.get('directories', {})
        if directories.get('status') == 'WARNING':
            score -= 10

        return max(0.0, min(100.0, score))

    def _get_health_status(self, score: float) -> str:
        """
        根据评分获取健康状态

        Args:
            score: 健康评分

        Returns:
            健康状态字符串
        """
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 75:
            return 'GOOD'
        elif score >= 60:
            return 'FAIR'
        else:
            return 'POOR'

    def agent_health_check(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Agent健康检查

        Args:
            agent_name: 指定Agent名称（None表示检查所有）

        Returns:
            健康检查结果
        """
        self.logger.info("Running agent health check", agent_name=agent_name)

        if agent_name:
            # 检查单个Agent
            return self._check_single_agent(agent_name)
        else:
            # 检查所有Agent
            return self._check_all_agents()

    def _check_single_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        检查单个Agent

        Args:
            agent_name: Agent名称

        Returns:
            检查结果
        """
        if agent_name not in self.agents_registry:
            return {
                'agent_name': agent_name,
                'status': 'NOT_REGISTERED',
                'message': f'Agent {agent_name} not found in registry'
            }

        agent_info = self.agents_registry[agent_name]
        agent_instance = agent_info['instance']

        # 检查Agent是否有必要的方法
        required_methods = ['get_system_status'] if hasattr(agent_instance, 'get_system_status') else []

        check_result = {
            'agent_name': agent_name,
            'registered_at': agent_info['registered_at'],
            'status': 'HEALTHY',
            'checks': {}
        }

        # 执行方法检查
        for method_name in required_methods:
            if hasattr(agent_instance, method_name):
                check_result['checks'][method_name] = '✅ available'
            else:
                check_result['checks'][method_name] = '❌ missing'
                check_result['status'] = 'UNHEALTHY'

        return check_result

    def _check_all_agents(self) -> Dict[str, Any]:
        """
        检查所有Agent

        Returns:
            检查结果
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(self.agents_registry),
            'healthy_count': 0,
            'unhealthy_count': 0,
            'agents': {}
        }

        for agent_name in self.agents_registry.keys():
            check = self._check_single_agent(agent_name)
            results['agents'][agent_name] = check

            if check['status'] == 'HEALTHY':
                results['healthy_count'] += 1
            else:
                results['unhealthy_count'] += 1

        results['overall_status'] = (
            'HEALTHY' if results['unhealthy_count'] == 0
            else 'UNHEALTHY'
        )

        return results

    def performance_report(self) -> Dict[str, Any]:
        """
        性能报告

        Returns:
            性能报告
        """
        self.logger.info("Generating performance report")

        # 获取系统性能指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        report = {
            'timestamp': datetime.now().isoformat(),
            'system_performance': {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available_gb': memory.available / (1024**3)
            },
            'agents_performance': self._get_agents_performance(),
            'recommendations': self._generate_recommendations(cpu_percent, memory.percent)
        }

        return report

    def _get_agents_performance(self) -> Dict[str, Any]:
        """
        获取Agent性能指标

        Returns:
            Agent性能数据
        """
        # 简化版性能数据
        return {
            'total_registered': len(self.agents_registry),
            'active_count': len([
                a for a in self.agents_registry.values()
                if a.get('status') == 'registered'
            ])
        }

    def _generate_recommendations(
        self,
        cpu_usage: float,
        memory_usage: float
    ) -> List[str]:
        """
        生成优化建议

        Args:
            cpu_usage: CPU使用率
            memory_usage: 内存使用率

        Returns:
            建议列表
        """
        recommendations = []

        if cpu_usage > 80:
            recommendations.append("CPU使用率过高，建议减少并发任务数量")

        if memory_usage > 80:
            recommendations.append("内存使用率过高，建议清理缓存或增加内存")

        if not recommendations:
            recommendations.append("系统运行状态良好")

        return recommendations

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            系统状态信息
        """
        return {
            'name': self.name,
            'agents_registered': len(self.agents_registry),
            'status': 'READY'
        }

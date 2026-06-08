"""
监控部 - Monitoring Department

监控部包含2个AI Agent:
1. 信息监控AI (InformationMonitoringAI) - 新闻监控 + 市场情绪
2. 资金监控AI (CapitalMonitoringAI) - 资金流向 + 龙虎榜

精简说明：
- 原有4个Agent精简为2个Agent（-50%）
- 信息监控AI = 新闻监控AI + 市场情绪AI（2合1）
- 资金监控AI = 资金流向AI + 龙虎榜AI（2合1）
"""

from src.agents.business.monitoring.information_monitoring_ai import (
    InformationMonitoringAI,
    analyze_information_monitoring
)
from src.agents.business.monitoring.capital_monitoring_ai import (
    CapitalMonitoringAI,
    analyze_capital_monitoring
)

__all__ = [
    # Agent类
    "InformationMonitoringAI",
    "CapitalMonitoringAI",

    # 便捷函数
    "analyze_information_monitoring",
    "analyze_capital_monitoring"
]

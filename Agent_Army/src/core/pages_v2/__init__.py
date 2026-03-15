"""
Agent Army - Pages v2.0
24个Agent完整版页面
Phase 1 + Phase 2 完整版
"""

# Phase 1: 核心页面
from .dashboard import render_dashboard
from .agent_status import render_agent_status
from .task_management import render_task_management

# Phase 2: 高级功能页面
from .analysis_reports import render_analysis_reports
from .portfolio import render_portfolio
from .market_monitor import render_market_monitor
from .data_center import render_data_center
from .system_config import render_system_config

__all__ = [
    # Phase 1
    'render_dashboard',
    'render_agent_status',
    'render_task_management',
    # Phase 2
    'render_analysis_reports',
    'render_portfolio',
    'render_market_monitor',
    'render_data_center',
    'render_system_config'
]

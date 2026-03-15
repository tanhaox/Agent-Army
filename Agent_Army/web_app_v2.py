"""
Agent Army - Web界面 v2.0
基于24个Agent完整版设计
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Agent Army v2.0",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Agent Army v2.0\n24个Agent | 6大军团 | 100%完成"
    }
)

# ==================== Session State初始化 ====================
if 'initialized' not in st.session_state:
    try:
        from src.core.logger import setup_logging, get_logger
        from src.core.config import ConfigManager
        from src.agents.management.hr_agent import HRAgent
        from src.agents.management.commander_agent import CommanderAgent

        # 设置日志
        setup_logging(log_level="INFO", log_dir="./logs", enable_console=False)
        st.session_state.logger = get_logger("web_v2")

        # 加载配置
        st.session_state.config_manager = ConfigManager("./config")

        # 初始化管理层Agent
        st.session_state.hr_agent = HRAgent(
            config=st.session_state.config_manager.get("hr_agent", {})
        )
        st.session_state.commander_agent = CommanderAgent(
            config=st.session_state.config_manager.get("commander_agent", {})
        )

        # 任务历史
        st.session_state.task_history = []

        # 自动填充的股票代码（从指令模式传递）
        st.session_state.auto_stock_code = ""

        # 任务管理页面的活动标签（0=指令模式, 1=投资分析）
        st.session_state.active_tab = 0

        st.session_state.initialized = True
        st.session_state.logger.info("Web界面v2.0初始化完成")
    except Exception as e:
        st.error(f"初始化失败: {str(e)}")
        st.exception(e)
        st.stop()

# ==================== 侧边栏 ====================
st.sidebar.title("🎖️ Agent Army")
st.sidebar.markdown("**v2.0 - 24个Agent**")
st.sidebar.markdown("---")

# 页面选择
page = st.sidebar.radio(
    "导航",
    [
        "🏠 主页",
        "🤖 Agent状态",
        "📋 任务管理",
        "📊 分析报告",
        "📖 导航指南",
        "⚙️ 系统配置"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# 快速信息
st.sidebar.markdown(f"**当前时间**")
st.sidebar.markdown(datetime.now().strftime('%Y-%m-%d'))
st.sidebar.markdown(datetime.now().strftime('%H:%M:%S'))

st.sidebar.markdown("---")

# 统计信息
task_count = len(st.session_state.get('task_history', []))
st.sidebar.metric("今日任务", task_count)

# ==================== 主页 ====================
if page == "🏠 主页":
    from src.core.pages_v2.dashboard_v2 import render_dashboard
    render_dashboard()

# ==================== Agent状态 ====================
elif page == "🤖 Agent状态":
    from src.core.pages_v2.agent_status_v3 import render_agent_status_v3
    render_agent_status_v3()

# ==================== 任务管理 ====================
elif page == "📋 任务管理":
    from src.core.pages_v2.task_management_v3 import render_task_management_v3
    render_task_management_v3()

# ==================== 分析报告 ====================
elif page == "📊 分析报告":
    from src.core.pages_v2.analysis_reports_v3 import render_analysis_reports_v3
    render_analysis_reports_v3()

# ==================== 投资组合 ====================
elif page == "💹 投资组合":
    st.title("💹 投资组合")
    st.markdown("---")
    st.info("💹 此页面将展示投资组合管理功能，包括：持仓管理、风险分析、业绩归因")

# ==================== 市场监控 ====================
elif page == "📰 市场监控":
    st.title("📰 市场监控")
    st.markdown("---")
    st.info("📰 此页面将展示市场监控功能，包括：新闻监控、资金流向、市场情绪、热点追踪")

# ==================== 数据中心 ====================
elif page == "📈 数据中心":
    st.title("📈 数据中心")
    st.markdown("---")
    st.info("📈 此页面将展示数据查询功能，包括：股票数据、行业数据、宏观数据、期权数据")

# ==================== 系统配置 ====================
elif page == "⚙️ 系统配置":
    from src.core.pages_v2.system_config_v3 import render_system_config_v3
    render_system_config_v3()

# ==================== 导航指南 ====================
elif page == "📖 导航指南":
    from src.core.pages_v2.navigation_guide_v3 import render_navigation_guide_v3
    render_navigation_guide_v3()

# ==================== 页脚 ====================
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 12px;'>
        <p>🎖️ Agent Army</p>
        <p>24个Agent | 6大军团</p>
        <p>Powered by omc team</p>
    </div>
    """,
    unsafe_allow_html=True
)

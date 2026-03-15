"""
Agent Army - Agent状态页 (v2.1 优化版)
集成Agent管理器和性能优化
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入性能优化工具
from src.core.utils.performance import (
    cached,
    LazyLoader,
    PerformanceMonitor
)

# 导入Agent管理器
from src.core.agents.agent_manager import (
    get_agent_manager,
    AgentStatus
)


@cached(ttl_seconds=60)  # 1分钟缓存
@PerformanceMonitor.measure_time("load_agent_data")
def load_agent_data():
    """
    加载Agent数据（带缓存）
    """
    agent_manager = get_agent_manager()
    all_agents = agent_manager.get_all_agents()

    # 按军团分组
    armies = {}
    for agent_id, agent_info in all_agents.items():
        army_name = agent_info['army']
        if army_name not in armies:
            armies[army_name] = []
        armies[army_name].append({
            'id': agent_id,
            **agent_info
        })

    # 统计数据
    total_agents = len(all_agents)
    idle_count = sum(1 for a in all_agents.values() if a['status'] == AgentStatus.IDLE)
    busy_count = sum(1 for a in all_agents.values() if a['status'] == AgentStatus.BUSY)
    error_count = sum(1 for a in all_agents.values() if a['status'] == AgentStatus.ERROR)

    return {
        'armies': armies,
        'all_agents': all_agents,
        'stats': {
            'total': total_agents,
            'idle': idle_count,
            'busy': busy_count,
            'error': error_count
        }
    }


def render_agent_status_optimized():
    """渲染优化版Agent状态页面"""

    st.title("🤖 Agent状态监控")
    st.markdown("**实时监控24个Agent运行状态**")
    st.markdown("---")

    # 加载数据（使用缓存）
    agent_data = load_agent_data()

    # ========== 顶部统计卡片 ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Agent总数",
            value=str(agent_data['stats']['total']),
            delta="100%在线"
        )

    with col2:
        st.metric(
            label="✅ 空闲",
            value=str(agent_data['stats']['idle']),
            delta="可接受任务"
        )

    with col3:
        st.metric(
            label="🔄 忙碌",
            value=str(agent_data['stats']['busy']),
            delta="处理中"
        )

    with col4:
        st.metric(
            label="❌ 错误",
            value=str(agent_data['stats']['error']),
            delta="需要关注"
        )

    st.markdown("---")

    # ========== 标签页 ==========
    tab_names = ["📊 总览"] + list(agent_data['armies'].keys())
    tabs = st.tabs(tab_names)

    # 总览标签页
    with tabs[0]:
        render_overview_tab(agent_data)

    # 各军团标签页
    for i, (army_name, agents) in enumerate(agent_data['armies'].items(), 1):
        with tabs[i]:
            render_army_tab(army_name, agents)

    # ========== 性能指标 ==========
    if st.checkbox("显示性能指标", key="show_agent_perf_metrics"):
        PerformanceMonitor.show_performance_metrics()


def render_overview_tab(agent_data):
    """渲染总览标签页"""

    st.markdown("### 📊 Agent总览")

    # Agent状态分布饼图
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 状态分布")

        fig_pie = go.Figure(data=[go.Pie(
            labels=['空闲', '忙碌', '错误'],
            values=[
                agent_data['stats']['idle'],
                agent_data['stats']['busy'],
                agent_data['stats']['error']
            ],
            hole=0.3,
            marker_colors=['#00ff00', '#ffaa00', '#ff0000']
        )])

        fig_pie.update_layout(
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("#### 军团Agent数量")

        army_names = list(agent_data['armies'].keys())
        army_counts = [len(agents) for agents in agent_data['armies'].values()]

        fig_bar = go.Figure(data=[go.Bar(
            x=army_names,
            y=army_counts,
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        )])

        fig_bar.update_layout(
            height=400,
            xaxis_title="军团",
            yaxis_title="Agent数量",
            showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Agent性能表
    st.markdown("#### 📈 Agent性能监控")

    # 准备数据
    performance_data = []
    for agent_id, agent_info in agent_data['all_agents'].items():
        performance_data.append({
            'Agent ID': agent_id,
            'Agent名称': agent_info['name'],
            '所属军团': agent_info['army'],
            '状态': agent_info['status'].value,
            '任务数': 0,  # TODO: 实际统计
            '成功率': '100%',  # TODO: 实际统计
            '平均耗时': '0.5s',  # TODO: 实际统计
            '评分': '⭐⭐⭐⭐'  # TODO: 实际统计
        })

    df = pd.DataFrame(performance_data)

    # 使用Streamlit数据编辑器
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '状态': st.column_config.TextColumn(
                '状态',
                help='Agent当前状态',
                width='small'
            ),
            '评分': st.column_config.TextColumn(
                '评分',
                help='Agent性能评分',
                width='small'
            )
        }
    )


def render_army_tab(army_name, agents):
    """渲染军团标签页"""

    st.markdown(f"### {army_name}")
    st.markdown(f"**Agent数量**: {len(agents)}")
    st.markdown("---")

    # 统计卡片
    idle = sum(1 for a in agents if a['status'] == AgentStatus.IDLE)
    busy = sum(1 for a in agents if a['status'] == AgentStatus.BUSY)
    error = sum(1 for a in agents if a['status'] == AgentStatus.ERROR)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总数", len(agents))

    with col2:
        st.metric("空闲", idle, delta="✅")

    with col3:
        st.metric("忙碌", busy, delta="🔄")

    with col4:
        st.metric("错误", error, delta="❌" if error > 0 else "✅")

    st.markdown("---")

    # Agent卡片
    for i in range(0, len(agents), 2):
        cols = st.columns(2)

        for j in range(2):
            if i + j < len(agents):
                with cols[j]:
                    render_agent_card(agents[i + j])


def render_agent_card(agent):
    """渲染Agent卡片"""

    status_emoji = {
        AgentStatus.IDLE: "✅",
        AgentStatus.BUSY: "🔄",
        AgentStatus.ERROR: "❌",
        AgentStatus.OFFLINE: "⚫"
    }.get(agent['status'], "❓")

    status_color = {
        AgentStatus.IDLE: "green",
        AgentStatus.BUSY: "orange",
        AgentStatus.ERROR: "red",
        AgentStatus.OFFLINE: "gray"
    }.get(agent['status'], "gray")

    with st.container():
        st.markdown(f"**{status_emoji} {agent['name']}**")
        st.markdown(f"*ID*: `{agent['id']}`")
        st.markdown(f"*描述*: {agent['description']}")
        st.markdown(f"*状态*: :{status_color}[{agent['status'].value}]")

        # 模拟性能指标
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("任务数", 0, delta="今日")

        with col2:
            st.metric("成功率", "100%", delta="⭐")

        with col3:
            st.metric("平均耗时", "0.5s", delta="快速")

        # 操作按钮
        if st.button("查看详情", key=f"detail_{agent['id']}", use_container_width=True):
            st.info(f"Agent详情功能开发中... (ID: {agent['id']})")

    st.markdown("---")


# 如果直接运行此文件
if __name__ == "__main__":
    render_agent_status_optimized()

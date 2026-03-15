"""
Agent Army - 任务管理页 (v2.1 优化版)
集成Agent管理器和性能优化
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
import time

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入性能优化工具
from src.core.utils.performance import (
    cached,
    render_pagination,
    PerformanceMonitor
)

# 导入Agent管理器
from src.core.agents.agent_manager import (
    get_agent_manager,
    TaskStatus
)


@cached(ttl_seconds=10)  # 10秒缓存
@PerformanceMonitor.measure_time("load_task_data")
def load_task_data():
    """
    加载任务数据（带缓存）
    """
    agent_manager = get_agent_manager()
    tasks = agent_manager.get_all_tasks()
    all_agents = agent_manager.get_all_agents()

    # 统计任务状态
    pending_count = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    running_count = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)
    completed_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed_count = sum(1 for t in tasks if t.status == TaskStatus.FAILED)

    return {
        'tasks': tasks,
        'agents': all_agents,
        'stats': {
            'total': len(tasks),
            'pending': pending_count,
            'running': running_count,
            'completed': completed_count,
            'failed': failed_count
        }
    }


def render_task_management_optimized():
    """渲染优化版任务管理页面"""

    st.title("📋 任务管理")
    st.markdown("**创建、监控和管理Agent分析任务**")
    st.markdown("---")

    # 加载数据（使用缓存）
    task_data = load_task_data()

    # ========== 顶部统计卡片 ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 总任务数",
            value=str(task_data['stats']['total']),
            delta="全部"
        )

    with col2:
        st.metric(
            label="⏳ 待执行",
            value=str(task_data['stats']['pending']),
            delta="队列中"
        )

    with col3:
        st.metric(
            label="🔄 执行中",
            value=str(task_data['stats']['running']),
            delta="处理中"
        )

    with col4:
        completed_delta = f"{task_data['stats']['completed']}/{task_data['stats']['total']}"
        st.metric(
            label="✅ 已完成",
            value=str(task_data['stats']['completed']),
            delta=completed_delta
        )

    st.markdown("---")

    # ========== 标签页 ==========
    tab1, tab2, tab3 = st.tabs([
        "➕ 创建任务",
        "📋 任务列表",
        "📊 执行监控"
    ])

    with tab1:
        render_create_task_tab(task_data)

    with tab2:
        render_task_list_tab(task_data)

    with tab3:
        render_execution_monitor_tab(task_data)

    # ========== 性能指标 ==========
    if st.checkbox("显示性能指标", key="show_task_perf_metrics"):
        PerformanceMonitor.show_performance_metrics()


def render_create_task_tab(task_data):
    """渲染创建任务标签页"""

    st.markdown("### ➕ 创建新任务")

    agent_manager = get_agent_manager()

    # 任务类型选择
    col1, col2 = st.columns(2)

    with col1:
        task_type = st.selectbox(
            "任务类型",
            [
                "full_analysis:全量分析（24个Agent）",
                "industry:产业分析（5个Agent）",
                "hot_topics:热点捕捉（4个Agent）",
                "custom:自定义（选择Agent）"
            ],
            key="task_type_v2"
        )

        # 解析任务类型
        task_type_key = task_type.split(":")[0]

    with col2:
        stock_code = st.text_input(
            "股票代码",
            placeholder="输入股票代码（如：000001）",
            key="stock_code_v2"
        )

    st.markdown("---")

    # Agent选择（仅自定义任务）
    selected_agents = []

    if task_type_key == "custom":
        st.markdown("### 🤖 选择Agent")

        # 按军团分组显示Agent
        armies = {}
        for agent_id, agent_info in task_data['agents'].items():
            army_name = agent_info['army']
            if army_name not in armies:
                armies[army_name] = []
            armies[army_name].append({
                'id': agent_id,
                'name': agent_info['name']
            })

        # 多选框
        for army_name, agents in armies.items():
            with st.expander(f"**{army_name}** ({len(agents)}个Agent)"):
                for agent in agents:
                    if st.checkbox(
                        f"{agent['name']} ({agent['id']})",
                        key=f"agent_{agent['id']}_v2"
                    ):
                        selected_agents.append(agent['id'])

        st.markdown("---")

    # 高级选项
    with st.expander("⚙️ 高级选项"):
        col1, col2 = st.columns(2)

        with col1:
            analysis_depth = st.select_slider(
                "分析深度",
                options=["快速", "标准", "深度"],
                value="标准",
                key="analysis_depth_v2"
            )

            time_range = st.selectbox(
                "时间范围",
                ["最近1个月", "最近3个月", "最近6个月", "最近1年"],
                key="time_range_v2"
            )

        with col2:
            data_sources = st.multiselect(
                "数据源",
                ["Tushare", "Akshare", "东方财富", "同花顺"],
                default=["Tushare", "Akshare"],
                key="data_sources_v2"
            )

            enable_backtest = st.checkbox(
                "启用回测",
                value=False,
                key="enable_backtest_v2"
            )

    # 创建按钮
    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if st.button("🗑️ 重置", use_container_width=True, key="reset_task_v2"):
            st.rerun()

    with col3:
        if st.button("🚀 创建任务", type="primary", use_container_width=True, key="create_task_v2"):
            if not stock_code:
                st.warning("⚠️ 请输入股票代码")
            elif task_type_key == "custom" and len(selected_agents) < 3:
                st.warning("⚠️ 自定义任务至少选择3个Agent")
            else:
                # 根据任务类型确定Agent列表
                if task_type_key == "full_analysis":
                    agents_to_use = list(task_data['agents'].keys())
                elif task_type_key == "industry":
                    agents_to_use = [
                        "macro_economic",
                        "industry_chain",
                        "policy_impact",
                        "industry_cycle",
                        "competitive_landscape"
                    ]
                elif task_type_key == "hot_topics":
                    agents_to_use = [
                        "news_monitor",
                        "capital_flow",
                        "market_sentiment",
                        "hot_sector"
                    ]
                else:  # custom
                    agents_to_use = selected_agents

                # 创建任务
                task = agent_manager.create_task(
                    task_type=task_type_key,
                    stock_code=stock_code,
                    agents=agents_to_use
                )

                st.success(f"✅ 任务创建成功！任务ID: {task.task_id}")
                st.info("💡 前往【任务列表】或【执行监控】查看进度")

                # 自动执行任务（模拟）
                with st.spinner("正在执行任务..."):
                    result = agent_manager.execute_task(task)
                    st.success("✅ 任务执行完成！")
                    st.balloons()

                    # 显示结果摘要
                    with st.expander("📊 查看结果摘要"):
                        for agent_id, agent_result in result.items():
                            st.markdown(
                                f"**{agent_result['agent_name']}**: "
                                f"评分 {agent_result['score']}/100, "
                                f"推荐 {agent_result['recommendation']}"
                            )


def render_task_list_tab(task_data):
    """渲染任务列表标签页"""

    st.markdown("### 📋 任务列表")

    # 筛选器
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "待执行", "执行中", "已完成", "失败"],
            key="status_filter_v2"
        )

    with col2:
        type_filter = st.selectbox(
            "类型筛选",
            ["全部", "full_analysis", "industry", "hot_topics", "custom"],
            key="type_filter_v2"
        )

    with col3:
        date_filter = st.date_input(
            "日期筛选",
            value=None,
            key="date_filter_v2"
        )

    with col4:
        if st.button("🔄 刷新", use_container_width=True, key="refresh_tasks_v2"):
            st.rerun()

    st.markdown("---")

    # 任务列表
    tasks = task_data['tasks']

    if not tasks:
        st.info("暂无任务，请前往【创建任务】创建新任务")
    else:
        # 使用分页
        page_size = 10
        current_page = render_pagination(len(tasks), page_size, key="task_list_pagination")

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_tasks = tasks[start_idx:end_idx]

        # 显示任务
        for task in page_tasks:
            render_task_item(task)


def render_task_item(task):
    """渲染任务项"""

    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌"
    }.get(task.status, "⏳")

    status_color = {
        TaskStatus.PENDING: "gray",
        TaskStatus.RUNNING: "orange",
        TaskStatus.COMPLETED: "green",
        TaskStatus.FAILED: "red"
    }.get(task.status, "gray")

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{status_emoji} {task.task_id}**")
            st.markdown(f"股票: {task.stock_code} | 类型: {task.task_type}")

        with col2:
            st.markdown(f"状态: :{status_color}[{task.status.value}]")
            st.markdown(f"Agent数: {len(task.agents)}")

        with col3:
            # 进度条
            st.progress(task.progress / 100)
            st.markdown(f"进度: {task.progress:.0f}%")

        with col4:
            if task.status == TaskStatus.COMPLETED:
                if st.button("查看", key=f"view_{task.task_id}", use_container_width=True):
                    st.json(task.result)

    st.markdown("---")


def render_execution_monitor_tab(task_data):
    """渲染执行监控标签页"""

    st.markdown("### 📊 执行监控")

    # 获取执行中的任务
    running_tasks = [
        t for t in task_data['tasks']
        if t.status == TaskStatus.RUNNING
    ]

    if not running_tasks:
        st.info("当前没有执行中的任务")
    else:
        # 实时进度更新
        for task in running_tasks:
            with st.container():
                st.markdown(f"**任务ID**: {task.task_id}")
                st.markdown(f"**股票**: {task.stock_code}")

                # 进度条
                progress_bar = st.progress(task.progress / 100)
                st.markdown(f"**进度**: {task.progress:.1f}%")

                # 执行时间
                if task.started_at:
                    elapsed = (datetime.now() - task.started_at).total_seconds()
                    st.markdown(f"**已耗时**: {elapsed:.1f}秒")

                # 模拟实时更新
                if task.progress < 100:
                    time.sleep(0.1)
                    task.progress += 10
                    if task.progress >= 100:
                        task.progress = 100
                        task.status = TaskStatus.COMPLETED
                    st.rerun()

            st.markdown("---")

    # 任务执行日志（模拟）
    st.markdown("#### 📝 执行日志")

    log_container = st.container()

    with log_container:
        st.code(
            """
[2026-03-15 14:30:05] INFO  任务 task_abc123 开始执行
[2026-03-15 14:30:05] INFO  启动Agent: macro_economic
[2026-03-15 14:30:06] INFO  Agent macro_economic 执行完成
[2026-03-15 14:30:06] INFO  启动Agent: financial_health
[2026-03-15 14:30:07] INFO  Agent financial_health 执行完成
[2026-03-15 14:30:07] INFO  任务 task_abc123 执行完成
            """.strip(),
            language="log"
        )


# 如果直接运行此文件
if __name__ == "__main__":
    render_task_management_optimized()

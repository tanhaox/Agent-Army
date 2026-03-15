"""
Agent Army - 主页Dashboard (v2.1 优化版)
集成性能优化和Agent管理器
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入性能优化工具
from src.core.utils.performance import (
    cached,
    PerformanceMonitor,
    render_pagination
)

# 导入Agent管理器
from src.core.agents.agent_manager import (
    get_agent_manager,
    TaskStatus
)


@cached(ttl_seconds=300)  # 5分钟缓存
@PerformanceMonitor.measure_time("load_dashboard_data")
def load_dashboard_data():
    """
    加载Dashboard数据（带缓存）
    """
    agent_manager = get_agent_manager()

    # 获取所有Agent
    all_agents = agent_manager.get_all_agents()

    # 统计Agent状态
    idle_count = sum(1 for a in all_agents.values() if a['status'].value == 'idle')
    busy_count = sum(1 for a in all_agents.values() if a['status'].value == 'busy')

    # 获取任务列表
    tasks = agent_manager.get_all_tasks()

    return {
        'total_agents': len(all_agents),
        'idle_agents': idle_count,
        'busy_agents': busy_count,
        'total_tasks': len(tasks),
        'agents': all_agents,
        'tasks': tasks
    }


def render_dashboard_optimized():
    """渲染优化版主页Dashboard"""

    # 记录页面开始时间
    if 'page_start_time' not in st.session_state:
        st.session_state.page_start_time = datetime.now()

    # 页面标题
    st.title("🎖️ Agent Army - AI价值投资分析系统")
    st.markdown(f"**版本**: v2.1 (优化版) | **当前时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")

    # 加载数据（使用缓存）
    dashboard_data = load_dashboard_data()

    # ========== 顶部统计卡片 ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🤖 Agent总数",
            value=str(dashboard_data['total_agents']),
            delta="100%完成"
        )

    with col2:
        st.metric(
            label="🏭 军团数量",
            value="6",
            delta="全部完成"
        )

    with col3:
        st.metric(
            label="📊 完成率",
            value="100%",
            delta="24/24"
        )

    with col4:
        st.metric(
            label="🎯 活跃任务",
            value=str(dashboard_data['total_tasks']),
            delta=f"空闲:{dashboard_data['idle_agents']} 忙碌:{dashboard_data['busy_agents']}"
        )

    st.markdown("---")

    # ========== 快速分析区域 ==========
    st.markdown("### 🎯 快速分析")

    agent_manager = get_agent_manager()

    col_left, col_right = st.columns([3, 1])

    with col_left:
        stock_code = st.text_input(
            "股票代码",
            placeholder="输入股票代码（如：000001）",
            key="quick_stock_code_v2",
            label_visibility="collapsed"
        )

    with col_right:
        analyze_button = st.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )

    if analyze_button and stock_code:
        # 使用真实Agent管理器创建任务
        key_agents = [
            "macro_economic",      # 宏观经济AI
            "financial_health",    # 财务健康AI
            "valuation",           # 估值AI
            "technical_analysis",  # 技术分析AI
            "news_monitor"         # 新闻监控AI
        ]

        task = agent_manager.create_task(
            task_type="quick_analysis",
            stock_code=stock_code,
            agents=key_agents
        )

        st.success(f"✅ 分析任务已创建！任务ID: {task.task_id}")
        st.info("💡 请前往【📋 任务管理】页面查看进度")

    st.markdown("---")

    # ========== 今日任务 & 热点新闻 ==========
    col_tasks, col_news = st.columns(2)

    with col_tasks:
        st.markdown("### 📋 今日任务")

        # 获取今日任务（使用缓存数据）
        tasks = dashboard_data['tasks']

        if tasks:
            # 使用分页显示任务
            page_size = 5
            current_page = render_pagination(len(tasks), page_size, key="task_pagination")

            start_idx = (current_page - 1) * page_size
            end_idx = start_idx + page_size
            page_tasks = tasks[start_idx:end_idx]

            for task in page_tasks:
                status_emoji = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌"
                }.get(task.status, "⏳")

                st.markdown(
                    f"{status_emoji} **{task.stock_code}** - "
                    f"{task.task_type} "
                    f"({task.status.value}) - "
                    f"进度: {task.progress:.0f}%"
                )
        else:
            st.info("暂无任务，开始创建第一个分析任务吧！")

        # 查看更多按钮
        if st.button("查看全部任务 →", key="view_all_tasks_v2"):
            st.info("请点击左侧导航栏的【📋 任务管理】")

    with col_news:
        st.markdown("### 🔥 热点新闻")

        # 模拟新闻数据（实际应从新闻监控AI获取）
        news_items = [
            {
                "title": "央行降准利好银行股",
                "time": "14:30",
                "impact": "正面",
                "stocks": "平安银行、招商银行"
            },
            {
                "title": "新能源汽车销量创新高",
                "time": "13:45",
                "impact": "正面",
                "stocks": "比亚迪、宁德时代"
            },
            {
                "title": "科技股受资金追捧",
                "time": "11:20",
                "impact": "正面",
                "stocks": "中兴通讯、立讯精密"
            }
        ]

        for news in news_items:
            impact_color = {
                "正面": "🟢",
                "负面": "🔴",
                "中性": "🟡"
            }.get(news['impact'], "🟡")

            st.markdown(
                f"**{impact_color} {news['time']}** {news['title']}  \n"
                f"关联: {news['stocks']}"
            )
            st.markdown("")

        # 查看更多按钮
        if st.button("查看更多新闻 →", key="view_more_news_v2"):
            st.info("请点击左侧导航栏的【📰 市场监控】")

    st.markdown("---")

    # ========== 实时Agent活动 ==========
    st.markdown("### 📈 实时Agent活动")

    # 6大军团状态概览
    armies = [
        {"name": "🏭 产业分析军团", "agents": 5, "army_filter": "产业分析军团"},
        {"name": "🔥 热点捕捉军团", "agents": 4, "army_filter": "热点捕捉军团"},
        {"name": "📊 个股挖掘军团", "agents": 4, "army_filter": "个股挖掘军团"},
        {"name": "🎯 目标预测军团", "agents": 5, "army_filter": "目标预测军团"},
        {"name": "⚡ 策略执行军团", "agents": 5, "army_filter": "策略执行军团"},
        {"name": "✅ 结果验证军团", "agents": 5, "army_filter": "结果验证军团"}
    ]

    for army in armies:
        with st.container():
            # 获取该军团的Agent
            army_agents = agent_manager.get_agents_by_army(army['army_filter'])

            # 统计状态
            idle = sum(1 for a in army_agents if a['status'].value == 'idle')
            busy = sum(1 for a in army_agents if a['status'].value == 'busy')

            col1, col2, col3, col4 = st.columns([3, 1, 2, 3])

            with col1:
                st.markdown(f"**{army['name']}**")

            with col2:
                st.markdown(f"{army['agents']}个Agent")

            with col3:
                status_text = f"空闲:{idle} 忙碌:{busy}"
                st.markdown(f"状态: {status_text}")

            with col4:
                # 显示最近的任务
                recent_task = next(
                    (t for t in tasks if any(
                        agent in t.agents
                        for agent in [a['id'] for a in army_agents]
                    )),
                    None
                )
                if recent_task:
                    st.markdown(f"活跃: {recent_task.stock_code} ({recent_task.status.value})")
                else:
                    st.markdown("状态: 等待任务")

        st.markdown("---")

    # ========== 快速入口 ==========
    st.markdown("### 🚀 快速入口")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🤖 查看Agent", use_container_width=True, key="btn_agent_v2"):
            st.info("请点击左侧导航栏的【🤖 Agent状态】")

    with col2:
        if st.button("📋 创建任务", use_container_width=True, key="btn_task_v2"):
            st.info("请点击左侧导航栏的【📋 任务管理】")

    with col3:
        if st.button("📊 查看报告", use_container_width=True, key="btn_report_v2"):
            st.info("请点击左侧导航栏的【📊 分析报告】")

    with col4:
        if st.button("📰 市场监控", use_container_width=True, key="btn_market_v2"):
            st.info("请点击左侧导航栏的【📰 市场监控】")

    # ========== 性能指标（开发者模式） ==========
    if st.checkbox("显示性能指标", key="show_perf_metrics"):
        PerformanceMonitor.show_performance_metrics()

    # ========== 底部信息 ==========
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！</p>
            <p>24个Agent | 6大军团 | 100%完成 | Powered by omc team | v2.1 优化版</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# 如果直接运行此文件
if __name__ == "__main__":
    render_dashboard_optimized()

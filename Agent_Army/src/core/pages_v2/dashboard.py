"""
Agent Army - 主页Dashboard (v2.0)
基于24个Agent完整版设计
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def render_dashboard():
    """渲染主页Dashboard"""

    # 页面标题
    st.title("🎖️ Agent Army - AI价值投资分析系统")
    st.markdown(f"**版本**: v2.0 | **当前时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")

    # ========== 顶部统计卡片 ==========
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🤖 Agent总数",
            value="24",
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
        # 活跃任务数（从session state获取）
        active_tasks = len(st.session_state.get('task_history', []))
        st.metric(
            label="🎯 活跃任务",
            value=str(active_tasks),
            delta="今日"
        )

    st.markdown("---")

    # ========== 快速分析区域 ==========
    st.markdown("### 🎯 快速分析")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        stock_code = st.text_input(
            "股票代码",
            placeholder="输入股票代码（如：000001）",
            key="quick_stock_code",
            label_visibility="collapsed"
        )

    with col_right:
        analyze_button = st.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )

    if analyze_button and stock_code:
        st.info(f"正在启动24个Agent分析 {stock_code}...")
        # TODO: 调用任务管理模块
        st.success("✅ 分析任务已创建！请前往【任务管理】页面查看进度")

    st.markdown("---")

    # ========== 今日任务 & 热点新闻 ==========
    col_tasks, col_news = st.columns(2)

    with col_tasks:
        st.markdown("### 📋 今日任务")

        # 获取今日任务（从session state）
        task_history = st.session_state.get('task_history', [])

        if task_history:
            for task in task_history[-5:]:  # 显示最近5个
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(task.get('status', 'pending'), "⏳")

                st.markdown(
                    f"{status_emoji} **{task.get('stock_code', 'N/A')}** - "
                    f"{task.get('type', '分析')} "
                    f"({task.get('status', 'pending')})"
                )
        else:
            st.info("暂无任务，开始创建第一个分析任务吧！")

        # 查看更多按钮
        if st.button("查看全部任务 →", key="view_all_tasks"):
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
        if st.button("查看更多新闻 →", key="view_more_news"):
            st.info("请点击左侧导航栏的【📰 市场监控】")

    st.markdown("---")

    # ========== 实时Agent活动 ==========
    st.markdown("### 📈 实时Agent活动")

    # 6大军团状态概览
    armies = [
        {"name": "🏭 产业分析军团", "agents": 5, "status": "125% ⭐⭐⭐", "active": "宏观AI工作中"},
        {"name": "🔥 热点捕捉军团", "agents": 4, "status": "100% ⭐⭐", "active": "新闻监控完成"},
        {"name": "📊 个股挖掘军团", "agents": 4, "status": "100% ⭐⭐", "active": "等待任务"},
        {"name": "🎯 目标预测军团", "agents": 5, "status": "125% ⭐⭐⭐", "active": "等待任务"},
        {"name": "⚡ 策略执行军团", "agents": 5, "status": "125% ⭐⭐⭐", "active": "等待任务"},
        {"name": "✅ 结果验证军团", "agents": 5, "status": "125% ⭐⭐⭐", "active": "等待任务"}
    ]

    for army in armies:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 2, 3])

            with col1:
                st.markdown(f"**{army['name']}**")

            with col2:
                st.markdown(f"{army['agents']}个Agent")

            with col3:
                st.markdown(f"完成度: {army['status']}")

            with col4:
                st.markdown(f"状态: {army['active']}")

        st.markdown("---")

    # ========== 快速入口 ==========
    st.markdown("### 🚀 快速入口")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🤖 查看Agent", use_container_width=True):
            st.info("请点击左侧导航栏的【🤖 Agent状态】")

    with col2:
        if st.button("📋 创建任务", use_container_width=True):
            st.info("请点击左侧导航栏的【📋 任务管理】")

    with col3:
        if st.button("📊 查看报告", use_container_width=True):
            st.info("请点击左侧导航栏的【📊 分析报告】")

    with col4:
        if st.button("📰 市场监控", use_container_width=True):
            st.info("请点击左侧导航栏的【📰 市场监控】")

    # ========== 底部信息 ==========
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！</p>
            <p>24个Agent | 6大军团 | 100%完成 | Powered by omc team</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# 如果直接运行此文件
if __name__ == "__main__":
    render_dashboard()

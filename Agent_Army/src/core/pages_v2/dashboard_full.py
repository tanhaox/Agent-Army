"""
Agent Army - Dashboard页面 (v2.0)
主页Dashboard实现
"""

import streamlit as st
from datetime import datetime


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
        # 创建任务
        task = {
            "id": len(st.session_state.get('task_history', [])) + 1,
            "type": "个股完整分析 (24个Agent)",
            "stock_code": stock_code,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat()
        }

        if 'task_history' not in st.session_state:
            st.session_state.task_history = []

        st.session_state.task_history.append(task)
        st.success("✅ 分析任务已创建！请前往【📋 任务管理】页面查看进度")

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
                    f"{task.get('type', '分析').split('(')[0]} "
                    f"({task.get('status', 'pending')})"
                )
        else:
            st.info("暂无任务，开始创建第一个分析任务吧！")

    with col_news:
        st.markdown("### 🔥 热点新闻")

        # 模拟新闻数据
        news_items = [
            {"title": "央行降准利好银行股", "time": "14:30", "impact": "🟢"},
            {"title": "新能源汽车销量创新高", "time": "13:45", "impact": "🟢"},
            {"title": "科技股受资金追捧", "time": "11:20", "impact": "🟢"}
        ]

        for news in news_items:
            st.markdown(
                f"**{news['impact']} {news['time']}** {news['title']}"
            )

    st.markdown("---")

    # ========== 实时Agent活动 ==========
    st.markdown("### 📈 实时Agent活动")

    armies = [
        {"name": "🏭 产业分析军团", "agents": 5, "status": "125% ⭐⭐⭐"},
        {"name": "🔥 热点捕捉军团", "agents": 4, "status": "100% ⭐⭐"},
        {"name": "📈 个股挖掘军团", "agents": 4, "status": "100% ⭐⭐"},
        {"name": "🎯 目标预测军团", "agents": 5, "status": "125% ⭐⭐⭐"},
        {"name": "⚡ 策略执行军团", "agents": 5, "status": "125% ⭐⭐⭐"},
        {"name": "✅ 结果验证军团", "agents": 5, "status": "125% ⭐⭐⭐"}
    ]

    for army in armies:
        col1, col2, col3 = st.columns([3, 1, 2])

        with col1:
            st.markdown(f"**{army['name']}**")

        with col2:
            st.markdown(f"{army['agents']}个Agent")

        with col3:
            st.markdown(f"完成度: {army['status']}")

        st.markdown("---")

    # ========== 底部信息 ==========
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！</p>
            <p>24个Agent | 6大军团 | 100%完成 | Powered by omc team</p>
        </div>
        """,
        unsafe_allow_html=True
    )

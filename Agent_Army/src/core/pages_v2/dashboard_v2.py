"""
Agent Army - 主页Dashboard (v2.1 - 重构版)
基于Phase 1设计系统重构
风格统一、用户体验优秀、无隐藏功能
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入设计系统
from src.core import (
    DesignTokens,
    apply_global_styles,
    apply_loading_styles,
    apply_error_styles,
    apply_feedback_styles,
    get_army_color,
    rgba,
    show_skeleton_card,
    show_progress_bar,
    show_error_card,
    show_empty_state,
    toast_success,
    toast_error,
    show_loading_overlay
)


def render_stat_card(label: str, value: str, delta: str, icon: str, color: str):
    """
    渲染统计卡片

    Args:
        label: 标签
        value: 数值
        delta: 变化趋势
        icon: 图标
        color: 主题色
    """
    st.markdown(
        f"""
        <div class="metric-card" style="
            border-left: 4px solid {color};
            background: {rgba(color, 0.05)};
        ">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value" style="color: {color};">{value}</div>
            <div style="color: {DesignTokens.Colors.SUCCESS}; font-size: 14px; margin-top: 4px;">
                {delta}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_news_card(title: str, time: str, impact: str, stocks: str):
    """
    渲染新闻卡片

    Args:
        title: 新闻标题
        time: 发布时间
        impact: 影响（正面/负面/中性）
        stocks: 关联股票
    """
    impact_colors = {
        "正面": DesignTokens.Colors.SUCCESS,
        "负面": DesignTokens.Colors.ERROR,
        "中性": DesignTokens.Colors.WARNING
    }
    impact_icons = {
        "正面": "🟢",
        "负面": "🔴",
        "中性": "🟡"
    }

    color = impact_colors.get(impact, DesignTokens.Colors.INFO)
    icon = impact_icons.get(impact, "⚪")

    st.markdown(
        f"""
        <div style="
            border-left: 3px solid {color};
            padding: 12px;
            margin-bottom: 12px;
            border-radius: {DesignTokens.Radius.MD};
            background: {DesignTokens.Colors.WHITE};
            box-shadow: {DesignTokens.Shadow.XS};
        ">
            <div style="color: {DesignTokens.Colors.TEXT_HINT}; font-size: {DesignTokens.Typography.XSMALL}; margin-bottom: 4px;">
                {icon} {time}
            </div>
            <div style="font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD}; color: {DesignTokens.Colors.TEXT_PRIMARY}; margin-bottom: 6px;">
                {title}
            </div>
            <div style="font-size: {DesignTokens.Typography.XSMALL}; color: {DesignTokens.Colors.TEXT_SECONDARY};">
                关联: <span style="background: {rgba(color, 0.1)}; color: {color}; padding: 2px 8px; border-radius: 4px;">{stocks}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_army_card(name: str, icon: str, agent_count: int, completion: str, stars: int, status: str):
    """
    渲染军团卡片

    Args:
        name: 军团名称
        icon: 图标
        agent_count: Agent数量
        completion: 完成度描述
        stars: 星级（1-3）
        status: 当前状态
    """
    # 获取军团主题色
    army_color = get_army_color(name)

    # 生成星级
    star_display = "⭐" * stars

    st.markdown(
        f"""
        <div class="army-card" style="
            background: {rgba(army_color, 0.05)};
            border-left: 4px solid {army_color};
            border-radius: {DesignTokens.Radius.MD};
            padding: 16px;
            box-shadow: {DesignTokens.Shadow.SM};
            margin-bottom: 12px;
            transition: {DesignTokens.Animation.TRANSITION_NORMAL};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD}; color: {DesignTokens.Colors.TEXT_PRIMARY}; font-size: {DesignTokens.Typography.BODY};">
                    {icon} {name}
                </div>
                <div style="color: {army_color}; font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM}; font-size: {DesignTokens.Typography.SMALL};">
                    {agent_count}个Agent
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span style="color: {DesignTokens.Colors.WARNING}; font-size: 18px;">{star_display}</span>
                <span style="color: {DesignTokens.Colors.TEXT_SECONDARY}; font-size: {DesignTokens.Typography.SMALL}; margin-left: 8px;">
                    {completion}
                </span>
            </div>
            <div style="margin-top: 6px; font-size: {DesignTokens.Typography.SMALL}; color: {DesignTokens.Colors.TEXT_SECONDARY};">
                {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_task_item(stock_code: str, task_type: str, status: str):
    """
    渲染任务列表项

    Args:
        stock_code: 股票代码
        task_type: 任务类型
        status: 状态
    """
    status_config = {
        "pending": {
            "icon": "⏳",
            "color": DesignTokens.Colors.WARNING,
            "label": "待处理"
        },
        "running": {
            "icon": "🔄",
            "color": DesignTokens.Colors.INFO,
            "label": "分析中"
        },
        "completed": {
            "icon": "✅",
            "color": DesignTokens.Colors.SUCCESS,
            "label": "已完成"
        },
        "failed": {
            "icon": "❌",
            "color": DesignTokens.Colors.ERROR,
            "label": "失败"
        }
    }

    config = status_config.get(status, status_config["pending"])

    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            padding: 10px;
            border-left: 3px solid {config['color']};
            background: {rgba(config['color'], 0.05)};
            border-radius: {DesignTokens.Radius.SM};
            margin-bottom: 8px;
        ">
            <span style="font-size: 20px; margin-right: 10px;">{config['icon']}</span>
            <div style="flex: 1;">
                <div style="font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM}; color: {DesignTokens.Colors.TEXT_PRIMARY};">
                    {stock_code} - {task_type}
                </div>
            </div>
            <span style="
                background: {rgba(config['color'], 0.15)};
                color: {config['color']};
                padding: 2px 8px;
                border-radius: {DesignTokens.Radius.SM};
                font-size: {DesignTokens.Typography.XSMALL};
                font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};
            ">
                {config['label']}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_dashboard():
    """渲染主页Dashboard (v2.1重构版)"""

    # ========== 应用全局样式 ==========
    apply_global_styles()
    apply_loading_styles()
    apply_error_styles()
    apply_feedback_styles()

    # ========== 页面头部 ==========
    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: {DesignTokens.Spacing.M_LG};
        ">
            <div>
                <h1 style="color: {DesignTokens.Colors.PRIMARY}; margin: 0;">
                    🎖️ Agent Army V2.0
                </h1>
                <p style="color: {DesignTokens.Colors.TEXT_SECONDARY}; margin: 4px 0 0 0;">
                    AI价值投资分析系统 | 24个Agent | 100%完成
                </p>
            </div>
            <div style="text-align: right;">
                <div style="color: {DesignTokens.Colors.TEXT_HINT}; font-size: {DesignTokens.Typography.XSMALL};">
                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"<hr style='border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT}; margin: {DesignTokens.Spacing.M_MD} 0;'>", unsafe_allow_html=True)

    # ========== 顶部统计卡片 ==========
    st.markdown("### 📊 系统概览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_stat_card(
            label="Agent总数",
            value="24",
            delta="↑ 100%完成",
            icon="🤖",
            color=DesignTokens.Colors.PRIMARY
        )

    with col2:
        render_stat_card(
            label="军团数量",
            value="6",
            delta="全部完成",
            icon="🏭",
            color=DesignTokens.Colors.SECONDARY
        )

    with col3:
        render_stat_card(
            label="完成率",
            value="100%",
            delta="24/24",
            icon="📈",
            color=DesignTokens.Colors.SUCCESS
        )

    with col4:
        active_tasks = len(st.session_state.get('task_history', []))
        render_stat_card(
            label="活跃任务",
            value=str(active_tasks),
            delta="今日",
            icon="🎯",
            color=DesignTokens.Colors.ACCENT
        )

    st.markdown("")  # 间距

    # ========== 快速分析区域 ==========
    st.markdown("### 🎯 快速分析")

    # 使用容器包裹
    st.markdown(
        f"""
        <div style="
            background: {rgba(DesignTokens.Colors.PRIMARY, 0.03)};
            border: 1px solid {rgba(DesignTokens.Colors.PRIMARY, 0.2)};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD}; color: {DesignTokens.Colors.PRIMARY}; margin-bottom: {DesignTokens.Spacing.M_SM};">
                🚀 开始新的分析
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns([4, 1])

    with col_left:
        stock_code = st.text_input(
            "股票代码",
            placeholder="输入股票代码（如：000001、600519）",
            key="quick_stock_code_v2",
            label_visibility="visible"
        )

    with col_right:
        # 垂直对齐按钮
        st.markdown("<br>", unsafe_allow_html=True)  # 对齐
        analyze_button = st.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )

    if analyze_button and stock_code:
        # 显示加载状态
        with show_loading_overlay("正在创建分析任务...", "spinner"):
            import time

            # 真正创建任务到session_state
            if 'task_history' not in st.session_state:
                st.session_state.task_history = []

            # 创建新任务
            new_task = {
                "id": len(st.session_state.task_history) + 1,
                "type": "个股分析",
                "stock_code": stock_code,
                "depth": "标准",
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now().isoformat()
            }

            # 添加到任务历史
            st.session_state.task_history.append(new_task)

            # 保存股票代码到session_state，供任务管理页面使用
            st.session_state.auto_stock_code = stock_code
            st.session_state.auto_jump_to_tab = 1  # 跳转到第2个标签页（投资分析）

            time.sleep(0.5)  # 短暂等待

        # 显示成功提示
        toast_success(f"分析任务已创建！正在分析 {stock_code}")

        # 自动跳转提示
        st.success(f"✅ 任务已创建！正在跳转到任务管理页面...")

        # 使用JavaScript自动跳转
        import streamlit.components.v1 as components
        components.html("""
        <script>
            // 自动点击"任务管理"导航项
            setTimeout(function() {
                // 查找包含"任务管理"文本的导航项
                var navItems = window.parent.document.querySelectorAll('label');
                for (var i = 0; i < navItems.length; i++) {
                    if (navItems[i].textContent.includes('任务管理')) {
                        navItems[i].click();
                        break;
                    }
                }
            }, 500);
        </script>
        """, height=0)

        st.info(f"💡 如果没有自动跳转，请点击左侧【📋 任务管理】查看 {stock_code} 的分析进度")

    st.markdown("")  # 间距

    # ========== 今日任务 & 热点新闻 ==========
    col_tasks, col_news = st.columns(2)

    with col_tasks:
        st.markdown("### 📋 今日任务")

        # 获取今日任务
        task_history = st.session_state.get('task_history', [])

        if task_history:
            for task in task_history[-5:]:  # 显示最近5个
                render_task_item(
                    stock_code=task.get('stock_code', 'N/A'),
                    task_type=task.get('type', '分析'),
                    status=task.get('status', 'pending')
                )
        else:
            show_empty_state(
                title="暂无任务",
                description="还没有任何分析任务，在上方输入股票代码开始分析",
                icon="📋",
                action_label="创建第一个任务",
                action_key="create_first_task"
            )

        if st.button("查看全部任务 →", key="view_all_tasks_v2"):
            st.info("👉 请点击左侧导航栏的【📋 任务管理】查看所有任务")

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
            render_news_card(
                title=news['title'],
                time=news['time'],
                impact=news['impact'],
                stocks=news['stocks']
            )

        if st.button("查看更多新闻 →", key="view_more_news_v2"):
            st.info("👉 请点击左侧导航栏的【📰 市场监控】查看更多新闻")

    st.markdown("")  # 间距

    # ========== 军团活动状态 ==========
    st.markdown("### 🏭 军团活动状态")

    # 6大军团状态（网格布局：3列 × 2行）
    armies = [
        {
            "name": "产业分析军团",
            "icon": "🏭",
            "agent_count": 5,
            "completion": "125%完成",
            "stars": 3,
            "status": "宏观AI工作中"
        },
        {
            "name": "热点捕捉军团",
            "icon": "🔥",
            "agent_count": 4,
            "completion": "100%完成",
            "stars": 2,
            "status": "新闻监控完成"
        },
        {
            "name": "个股挖掘军团",
            "icon": "📊",
            "agent_count": 4,
            "completion": "100%完成",
            "stars": 2,
            "status": "等待任务"
        },
        {
            "name": "目标预测军团",
            "icon": "🎯",
            "agent_count": 5,
            "completion": "125%完成",
            "stars": 3,
            "status": "等待任务"
        },
        {
            "name": "策略执行军团",
            "icon": "⚡",
            "agent_count": 5,
            "completion": "125%完成",
            "stars": 3,
            "status": "等待任务"
        },
        {
            "name": "结果验证军团",
            "icon": "✅",
            "agent_count": 5,
            "completion": "125%完成",
            "stars": 3,
            "status": "等待任务"
        }
    ]

    # 网格布局：3列
    for i in range(0, len(armies), 3):
        col1, col2, col3 = st.columns(3)

        cols = [col1, col2, col3]

        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(armies):
                with col:
                    army = armies[idx]
                    render_army_card(
                        name=army['name'],
                        icon=army['icon'],
                        agent_count=army['agent_count'],
                        completion=army['completion'],
                        stars=army['stars'],
                        status=army['status']
                    )

    st.markdown("")  # 间距

    # ========== 快速入口 ==========
    st.markdown("### 🚀 快速入口")

    col1, col2, col3, col4 = st.columns(4)

    quick_actions = [
        {"icon": "🤖", "label": "Agent状态", "page": "Agent状态"},
        {"icon": "📋", "label": "任务管理", "page": "任务管理"},
        {"icon": "📊", "label": "分析报告", "page": "分析报告"},
        {"icon": "📰", "label": "市场监控", "page": "市场监控"}
    ]

    with col1:
        if st.button(f"{quick_actions[0]['icon']} {quick_actions[0]['label']}", use_container_width=True, key="quick_agents"):
            st.info(f"👉 请点击左侧导航栏的【{quick_actions[0]['page']}】")

    with col2:
        if st.button(f"{quick_actions[1]['icon']} {quick_actions[1]['label']}", use_container_width=True, key="quick_tasks"):
            st.info(f"👉 请点击左侧导航栏的【{quick_actions[1]['page']}】")

    with col3:
        if st.button(f"{quick_actions[2]['icon']} {quick_actions[2]['label']}", use_container_width=True, key="quick_reports"):
            st.info(f"👉 请点击左侧导航栏的【{quick_actions[2]['page']}】")

    with col4:
        if st.button(f"{quick_actions[3]['icon']} {quick_actions[3]['label']}", use_container_width=True, key="quick_monitor"):
            st.info(f"👉 请点击左侧导航栏的【{quick_actions[3]['page']}】")

    # ========== 底部信息 ==========
    st.markdown(f"<hr style='border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT}; margin: {DesignTokens.Spacing.M_LG} 0;'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="
            text-align: center;
            color: {DesignTokens.Colors.TEXT_HINT};
            padding: {DesignTokens.Spacing.P_LG} 0;
            font-size: {DesignTokens.Typography.SMALL};
        ">
            <p style="margin: {DesignTokens.Spacing.M_XS} 0;">
                🎖️ <strong>Agent Army V2.0</strong> - 让AI价值投资更智能、更透明、更高效！
            </p>
            <p style="margin: {DesignTokens.Spacing.M_XS} 0;">
                24个Agent | 6大军团 | 100%完成 | Powered by Phase 1设计系统
            </p>
            <p style="margin: {DesignTokens.Spacing.M_XS} 0; color: {DesignTokens.Colors.TEXT_HINT}; font-size: {DesignTokens.Typography.XSMALL};">
                v2.1 - Dashboard重构版 | {datetime.now().strftime('%Y-%m-%d')}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# 如果直接运行此文件
if __name__ == "__main__":
    render_dashboard()

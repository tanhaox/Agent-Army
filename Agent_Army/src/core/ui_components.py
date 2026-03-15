"""
UI组件库 - 可复用的前端组件

创建日期: 2026-03-14
设计师: OMC Team Designer
版本: v1.0

包含:
- 指标卡片组件
- 状态徽章组件
- 实时日志查看器
- Agent工作站组件
- 渐变横幅组件
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime


# ==================== 色彩系统 ====================

class Colors:
    """主题色彩系统"""

    # 主要颜色
    PRIMARY = "#1E88E5"      # 蓝色
    SECONDARY = "#43A047"    # 绿色
    ACCENT = "#FB8C00"       # 橙色
    ERROR = "#E53935"        # 红色
    WARNING = "#FDD835"      # 黄色
    INFO = "#00ACC1"         # 青色

    # 背景色
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F5F5F5"
    BG_CARD = "#FFFFFF"

    # 文字色
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"


# ==================== 指标卡片组件 ====================

def create_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: str = "primary"
):
    """
    创建指标卡片

    Args:
        title: 标题
        value: 数值
        delta: 变化值（可选）
        description: 描述（可选）
        icon: 图标（可选）
        color: 颜色（primary/success/warning/error/info）
    """
    color_map = {
        "primary": Colors.PRIMARY,
        "success": Colors.SECONDARY,
        "warning": Colors.ACCENT,
        "error": Colors.ERROR,
        "info": Colors.INFO
    }

    selected_color = color_map.get(color, Colors.PRIMARY)

    card_html = f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid {selected_color};
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            {f'<span style="font-size: 2rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''}
            <span style="font-size: 0.875rem; color: #757575; font-weight: 500;">{title}</span>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: {selected_color}; margin-bottom: 0.25rem;">
            {value}
        </div>
        {f'<div style="font-size: 0.875rem; color: #757575; margin-top: 0.5rem;">{description}</div>' if description else ''}
        {f'<div style="font-size: 0.875rem; color: #43A047; margin-top: 0.5rem; font-weight: 500;">{delta}</div>' if delta else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


# ==================== 状态徽章组件 ====================

def get_status_badge(status: str) -> str:
    """
    获取状态徽章HTML

    Args:
        status: 状态（运行中/空闲/异常/已停止）

    Returns:
        HTML字符串
    """
    badges = {
        "运行中": '<span style="background: #E8F5E9; color: #43A047; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">● 运行中</span>',
        "空闲": '<span style="background: #E3F2FD; color: #1E88E5; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">● 空闲</span>',
        "异常": '<span style="background: #FFEBEE; color: #E53935; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">● 异常</span>',
        "已停止": '<span style="background: #F5F5F5; color: #757575; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">● 已停止</span>',
        "待执行": '<span style="background: #FFF3E0; color: #FB8C00; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">● 待执行</span>',
        "已完成": '<span style="background: #E8F5E9; color: #43A047; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 500;">✅ 已完成</span>',
    }
    return badges.get(status, badges["空闲"])


def get_tool_tag(tool_name: str) -> str:
    """
    获取工具标签HTML

    Args:
        tool_name: 工具名称

    Returns:
        HTML字符串
    """
    return f'<span style="background: #E3F2FD; color: #1E88E5; padding: 4px 8px; border-radius: 8px; font-size: 0.75rem; margin-right: 4px;">🔧 {tool_name}</span>'


# ==================== 实时日志查看器 ====================

def create_live_log_viewer(
    logs: List[Dict[str, str]],
    auto_scroll: bool = True,
    max_height: int = 300,
    title: str = "工作日志"
):
    """
    创建实时日志查看器

    Args:
        logs: 日志列表 [{"time": "...", "level": "...", "message": "..."}]
        auto_scroll: 是否自动滚动到底部
        max_height: 最大高度（像素）
        title: 标题
    """
    level_colors = {
        "INFO": "#4FC3F7",
        "SUCCESS": "#66BB6A",
        "WARNING": "#FFD54F",
        "ERROR": "#EF5350",
        "DEBUG": "#BDBDBD"
    }

    log_html = f"""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.875rem; font-weight: 500; color: #757575; margin-bottom: 0.5rem;">
            📋 {title}
        </div>
        <div style="
            background: #263238;
            color: #ECEFF1;
            padding: 1rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            max-height: {max_height}px;
            overflow-y: auto;
            line-height: 1.6;
        ">
    """

    for log in logs:
        color = level_colors.get(log.get("level", "INFO"), "#ECEFF1")
        time_str = log.get("time", datetime.now().strftime("%H:%M:%S"))
        level = log.get("level", "INFO")
        message = log.get("message", "")

        log_html += f'<div style="margin-bottom: 0.5rem;">'
        log_html += f'<span style="color: #757575;">{time_str}</span> '
        log_html += f'<span style="color: {color}; font-weight: 600;">[{level}]</span> '
        log_html += f'<span>{message}</span>'
        log_html += '</div>'

    log_html += '</div>'

    if auto_scroll:
        log_html += """
        <script>
            var logContainers = document.querySelectorAll('div[style*="overflow-y: auto"]');
            logContainers.forEach(function(container) {
                container.scrollTop = container.scrollHeight;
            });
        </script>
        """

    log_html += '</div>'

    st.markdown(log_html, unsafe_allow_html=True)


# ==================== Agent工作站组件 ====================

def create_agent_workstation_card(
    agent_name: str,
    agent_role: str,
    status: str,
    progress: int,
    tools: List[str],
    logs: List[Dict[str, str]],
    elapsed_time: str = "0秒"
):
    """
    创建Agent工作站卡片

    Args:
        agent_name: Agent名称
        agent_role: Agent角色
        status: 状态（运行中/空闲/异常）
        progress: 进度（0-100）
        tools: 工具列表
        logs: 日志列表
        elapsed_time: 已用时间
    """
    with st.container():
        # 卡片容器（带阴影）
        st.markdown(f"""
        <div style="
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
        """, unsafe_allow_html=True)

        # 标题栏
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### 🤖 {agent_name}")
            st.caption(f"职责: {agent_role}")
        with col2:
            st.markdown(get_status_badge(status), unsafe_allow_html=True)

        st.markdown("---")

        # 主体内容
        col1, col2 = st.columns([1, 3])

        with col1:
            # 状态面板
            st.markdown("**工作状态**")

            # 进度条
            progress_color = Colors.SECONDARY if progress == 100 else Colors.PRIMARY
            progress_text = "✅ 已完成" if progress == 100 else f"{progress}%"
            st.progress(progress / 100, text=progress_text)

            # 工具列表
            st.markdown("**使用工具**")
            tools_html = " ".join([get_tool_tag(tool) for tool in tools])
            st.markdown(tools_html, unsafe_allow_html=True)

            # 耗时
            st.markdown(f"**耗时**: ⏱️ {elapsed_time}")

        with col2:
            # 工作日志
            create_live_log_viewer(logs, max_height=250, title="实时日志")

        # 关闭卡片容器
        st.markdown("</div>", unsafe_allow_html=True)


# ==================== 渐变横幅组件 ====================

def create_gradient_banner(
    title: str,
    subtitle: str,
    gradient_start: str = "#1E88E5",
    gradient_end: str = "#43A047"
):
    """
    创建渐变横幅

    Args:
        title: 主标题
        subtitle: 副标题
        gradient_start: 渐变起始颜色
        gradient_end: 渐变结束颜色
    """
    banner_html = f"""
    <div style="
        background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    ">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">{title}</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.125rem; opacity: 0.9;">{subtitle}</p>
    </div>
    """

    st.markdown(banner_html, unsafe_allow_html=True)


# ==================== 时间线组件 ====================

def create_timeline_item(
    time: str,
    title: str,
    description: str,
    status: str = "completed"
):
    """
    创建时间线项

    Args:
        time: 时间
        title: 标题
        description: 描述
        status: 状态（completed/active/pending）
    """
    status_colors = {
        "completed": Colors.SECONDARY,
        "active": Colors.PRIMARY,
        "pending": Colors.TEXT_DISABLED
    }

    color = status_colors.get(status, Colors.TEXT_DISABLED)
    icon = "✅" if status == "completed" else ("🔵" if status == "active" else "⚪")

    timeline_html = f"""
    <div style="
        display: flex;
        margin-bottom: 1rem;
    ">
        <div style="
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: {color};
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            font-size: 1.25rem;
        ">
            {icon}
        </div>
        <div style="flex: 1;">
            <div style="font-size: 0.875rem; color: #757575;">{time}</div>
            <div style="font-size: 1rem; font-weight: 500; color: #212121;">{title}</div>
            <div style="font-size: 0.875rem; color: #757575;">{description}</div>
        </div>
    </div>
    """

    st.markdown(timeline_html, unsafe_allow_html=True)


# ==================== 信息卡片组件 ====================

def create_info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    color: str = "info"
):
    """
    创建信息卡片

    Args:
        title: 标题
        content: 内容
        icon: 图标
        color: 颜色主题（info/success/warning/error）
    """
    color_map = {
        "info": (Colors.INFO, "#E0F7FA"),
        "success": (Colors.SECONDARY, "#E8F5E9"),
        "warning": (Colors.ACCENT, "#FFF3E0"),
        "error": (Colors.ERROR, "#FFEBEE")
    }

    border_color, bg_color = color_map.get(color, color_map["info"])

    card_html = f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {border_color};
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <span style="font-weight: 600; color: {border_color};">{title}</span>
        </div>
        <div style="color: #424242; line-height: 1.6;">
            {content}
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


# ==================== 示例使用 ====================

def demo_components():
    """演示所有组件"""

    st.title("🎨 UI组件库演示")

    # 1. 渐变横幅
    create_gradient_banner(
        title="🎖️ Agent Army",
        subtitle="股票价值投资AI军团 - Phase 3 性能优化版本"
    )

    # 2. 指标卡片
    st.markdown("### 📊 性能指标")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        create_metric_card(
            title="并发性能提升",
            value="4.76倍",
            delta="+376%",
            icon="🚀",
            color="success"
        )

    with col2:
        create_metric_card(
            title="缓存命中率",
            value="50-80%",
            description="减少API调用",
            icon="💾",
            color="info"
        )

    with col3:
        create_metric_card(
            title="API节流控制",
            value="运行中",
            description="避免限流风险",
            icon="⚡",
            color="warning"
        )

    with col4:
        create_metric_card(
            title="后台监控",
            value="运行中",
            description="自动清理过期缓存",
            icon="👁️",
            color="success"
        )

    # 3. Agent工作站
    st.markdown("### 🤖 Agent工作站")
    create_agent_workstation_card(
        agent_name="产业链分析AI",
        agent_role="分析产业链上下游关系",
        status="运行中",
        progress=65,
        tools=["FinancialTool", "LLMTool"],
        logs=[
            {"time": "09:23:15", "level": "INFO", "message": "正在查询产业链数据..."},
            {"time": "09:23:16", "level": "SUCCESS", "message": "✅ 产业链数据获取成功"},
            {"time": "09:23:17", "level": "INFO", "message": "正在分析上下游关系..."},
        ],
        elapsed_time="12.5秒"
    )

    # 4. 信息卡片
    st.markdown("### 📋 信息卡片")
    col1, col2 = st.columns(2)

    with col1:
        create_info_card(
            title="系统提示",
            content="这是一个现代化的UI组件库，支持多种组件类型。",
            icon="💡",
            color="info"
        )

    with col2:
        create_info_card(
            title="成功提示",
            content="所有组件已成功加载并可以使用！",
            icon="✅",
            color="success"
        )


if __name__ == "__main__":
    demo_components()

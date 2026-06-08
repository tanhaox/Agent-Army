"""
UI 组件模块 - Agent Army v2.0

提供可复用的 UI 组件
"""

from typing import Optional


class Colors:
    """颜色常量"""
    PRIMARY = "#1E88E5"
    SUCCESS = "#43A047"
    WARNING = "#FFA000"
    DANGER = "#E53935"
    INFO = "#039BE5"
    LIGHT = "#F5F5F5"
    DARK = "#212121"


def create_gradient_banner(
    title: str,
    subtitle: str = "",
    height: int = 200,
    color_start: str = "#1E88E5",
    color_end: str = "#43A047"
):
    """
    创建渐变色横幅

    Args:
        title: 标题
        subtitle: 副标题
        height: 高度（像素）
        color_start: 渐变起始颜色
        color_end: 渐变结束颜色
    """
    import streamlit as st

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color_start} 0%, {color_end} 100%);
        padding: 40px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <h1 style="
            margin: 0;
            font-size: 48px;
            font-weight: bold;
            color: white;
        ">{title}</h1>
        <p style="
            margin: 10px 0 0 0;
            font-size: 20px;
            color: rgba(255,255,255,0.9);
        ">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def create_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    description: Optional[str] = None,
    icon: str = "",
    color: str = "primary"
):
    """
    创建指标卡片

    Args:
        title: 标题
        value: 值
        delta: 变化量
        description: 描述文本
        icon: 图标
        color: 颜色主题
    """
    import streamlit as st

    # 颜色映射
    color_map = {
        "primary": "#1E88E5",
        "success": "#43A047",
        "warning": "#FFA000",
        "danger": "#E53935",
        "info": "#039BE5"
    }

    border_color = color_map.get(color, color_map["primary"])

    # 构建卡片 HTML
    card_html = f"""
    <div style="
        border-left: 4px solid {border_color};
        padding: 15px 20px;
        margin: 10px 0;
        background: {border_color}10;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="font-size: 14px; color: #757575; margin-bottom: 5px;">
            {icon} {title}
        </div>
        <div style="font-size: 24px; font-weight: bold; color: #212121; margin-bottom: 5px;">
            {value}
        </div>
    """

    if delta:
        card_html += f"""
        <div style="font-size: 14px; color: {border_color}; font-weight: 500;">
            {delta}
        </div>
        """

    if description:
        card_html += f"""
        <div style="font-size: 12px; color: #757575; margin-top: 5px;">
            {description}
        </div>
        """

    card_html += "</div>"

    st.markdown(card_html, unsafe_allow_html=True)


def create_info_card(
    title: str,
    content: str,
    icon: str = "ℹ️",
    color: str = "#039BE5"
):
    """
    创建信息卡片

    Args:
        title: 标题
        content: 内容
        icon: 图标
        color: 颜色
    """
    import streamlit as st

    st.markdown(f"""
    <div style="
        border-left: 4px solid {color};
        padding: 15px 20px;
        margin: 10px 0;
        background: {color}10;
        border-radius: 5px;
    ">
        <h4 style="margin: 0 0 10px 0; color: {color};">
            {icon} {title}
        </h4>
        <p style="margin: 0; color: #424242;">
            {content}
        </p>
    </div>
    """, unsafe_allow_html=True)


def get_status_badge(status: str) -> str:
    """
    获取状态徽章HTML

    Args:
        status: 状态文本

    Returns:
        HTML字符串
    """
    # 状态颜色映射
    status_colors = {
        "active": "#43A047",
        "running": "#1E88E5",
        "completed": "#43A047",
        "failed": "#E53935",
        "pending": "#FFA000",
        "idle": "#757575",
    }

    # 获取颜色
    color = status_colors.get(status.lower(), "#757575")

    # 状态显示名称映射
    status_names = {
        "active": "运行中",
        "running": "运行中",
        "completed": "已完成",
        "failed": "失败",
        "pending": "等待中",
        "idle": "空闲",
    }

    display_name = status_names.get(status.lower(), status)

    return f"""
    <span style="
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        background: {color}20;
        color: {color};
        font-size: 12px;
        font-weight: 500;
    ">
        {display_name}
    </span>
    """


def get_tool_tag(tool_name: str, version: str = "") -> str:
    """
    获取工具标签HTML

    Args:
        tool_name: 工具名称
        version: 版本号

    Returns:
        HTML字符串
    """
    version_text = f" v{version}" if version else ""

    return f"""
    <span style="
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        background: #E3F2FD;
        color: #1976D2;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 4px;
    ">
        {tool_name}{version_text}
    </span>
    """


__all__ = [
    'Colors',
    'create_gradient_banner',
    'create_metric_card',
    'create_info_card',
    'get_status_badge',
    'get_tool_tag',
]

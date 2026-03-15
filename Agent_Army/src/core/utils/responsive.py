"""
Agent Army - 响应式设计优化
移动端适配、自定义CSS样式
"""

import streamlit as st


# ========== 自定义CSS样式 ==========

CUSTOM_CSS = """
<style>
    /* ========== 全局样式 ========== */
    .main {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ========== 移动端优化 ========== */
    @media only screen and (max-width: 768px) {
        /* 减少内边距 */
        .main {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        /* 标题字体缩小 */
        h1 {
            font-size: 1.5rem !important;
        }

        h2 {
            font-size: 1.25rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
        }

        /* 按钮全宽 */
        .stButton > button {
            width: 100%;
        }

        /* 数据表格优化 */
        .stDataFrame {
            font-size: 0.8rem;
        }

        /* 图表高度调整 */
        .plotly {
            height: 300px !important;
        }
    }

    /* ========== 平板优化 ========== */
    @media only screen and (min-width: 769px) and (max-width: 1024px) {
        .main {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            font-size: 2rem !important;
        }
    }

    /* ========== 卡片样式 ========== */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    /* ========== 渐变按钮 ========== */
    .gradient-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        transition: all 0.3s;
    }

    .gradient-button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    /* ========== 加载动画 ========== */
    .loading-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* ========== 提示框样式 ========== */
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }

    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }

    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }

    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }

    /* ========== 侧边栏样式 ========== */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* ========== 表格样式 ========== */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }

    .data-table th {
        background-color: #667eea;
        color: white;
        padding: 0.75rem;
        text-align: left;
        font-weight: bold;
    }

    .data-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #ddd;
    }

    .data-table tr:hover {
        background-color: #f5f5f5;
    }

    /* ========== 进度条样式 ========== */
    .progress-bar {
        width: 100%;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }

    /* ========== 徽章样式 ========== */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }

    .badge-success {
        background-color: #4caf50;
        color: white;
    }

    .badge-warning {
        background-color: #ff9800;
        color: white;
    }

    .badge-danger {
        background-color: #f44336;
        color: white;
    }

    .badge-info {
        background-color: #2196f3;
        color: white;
    }

    /* ========== 阴影效果 ========== */
    .shadow-sm {
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .shadow-md {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .shadow-lg {
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
</style>
"""


def apply_custom_styles():
    """应用自定义样式"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: str,
    delta: str = None,
    icon: str = "📊"
):
    """
    渲染指标卡片

    Args:
        title: 标题
        value: 值
        delta: 变化
        icon: 图标
    """
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2rem;">{icon}</div>
        <div style="font-size: 0.875rem; opacity: 0.8;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: bold;">{value}</div>
        {f'<div style="font-size: 0.875rem;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def render_info_box(message: str, box_type: str = "info"):
    """
    渲染提示框

    Args:
        message: 消息内容
        box_type: 类型 (info, success, warning, error)
    """
    box_classes = {
        "info": "info-box",
        "success": "success-box",
        "warning": "warning-box",
        "error": "error-box"
    }

    box_class = box_classes.get(box_type, "info-box")

    st.markdown(
        f'<div class="{box_class}">{message}</div>',
        unsafe_allow_html=True
    )


def render_badge(text: str, badge_type: str = "info"):
    """
    渲染徽章

    Args:
        text: 文本
        badge_type: 类型 (success, warning, danger, info)
    """
    badge_classes = {
        "success": "badge-success",
        "warning": "badge-warning",
        "danger": "badge-danger",
        "info": "badge-info"
    }

    badge_class = badge_classes.get(badge_type, "badge-info")

    st.markdown(
        f'<span class="badge {badge_class}">{text}</span>',
        unsafe_allow_html=True
    )


def render_progress_bar(
    progress: float,
    label: str = None
):
    """
    渲染进度条

    Args:
        progress: 进度 (0-100)
        label: 标签
    """
    st.markdown(f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
    </div>
    {f'<div style="text-align: center; font-size: 0.875rem;">{label}: {progress:.1f}%</div>' if label else ''}
    """, unsafe_allow_html=True)


def get_device_type() -> str:
    """
    获取设备类型

    Returns:
        'mobile', 'tablet', 'desktop'
    """
    try:
        screen_width = st.context.get("screen_width", 1200)

        if screen_width < 768:
            return "mobile"
        elif screen_width < 1024:
            return "tablet"
        else:
            return "desktop"
    except:
        return "desktop"


def is_mobile() -> bool:
    """是否移动设备"""
    return get_device_type() == "mobile"


def is_tablet() -> bool:
    """是否平板设备"""
    return get_device_type() == "tablet"


def is_desktop() -> bool:
    """是否桌面设备"""
    return get_device_type() == "desktop"


def responsive_columns(
    desktop_cols: int = 4,
    tablet_cols: int = 2,
    mobile_cols: int = 1
):
    """
    响应式列数

    Args:
        desktop_cols: 桌面列数
        tablet_cols: 平板列数
        mobile_cols: 移动列数

    Returns:
        列数
    """
    device = get_device_type()

    if device == "mobile":
        return mobile_cols
    elif device == "tablet":
        return tablet_cols
    else:
        return desktop_cols


# 导出
__all__ = [
    'CUSTOM_CSS',
    'apply_custom_styles',
    'render_metric_card',
    'render_info_box',
    'render_badge',
    'render_progress_bar',
    'get_device_type',
    'is_mobile',
    'is_tablet',
    'is_desktop',
    'responsive_columns'
]

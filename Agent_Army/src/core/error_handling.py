"""
错误处理组件

提供用户友好的错误显示和处理组件，包括错误卡片、警告提示等。

用途：改善错误处理体验，提供清晰的错误信息和恢复操作
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Callable
from .design_tokens import DesignTokens, rgba
from .global_styles import apply_global_styles


def apply_error_styles():
    """应用错误处理相关的CSS样式"""
    error_styles = f"""
    <style>
    /* ========== 错误卡片样式 ========== */

    .error-card {{
        background: {rgba(DesignTokens.Colors.ERROR, 0.05)};
        border-left: 4px solid {DesignTokens.Colors.ERROR};
        border-radius: {DesignTokens.Radius.MD};
        padding: {DesignTokens.Spacing.P_MD};
        margin: {DesignTokens.Spacing.M_MD} 0;
        display: flex;
        align-items: flex-start;
        gap: {DesignTokens.Spacing.M_MD};
    }}

    .error-card.warning {{
        background: {rgba(DesignTokens.Colors.WARNING, 0.05)};
        border-left-color: {DesignTokens.Colors.WARNING};
    }}

    .error-card.info {{
        background: {rgba(DesignTokens.Colors.INFO, 0.05)};
        border-left-color: {DesignTokens.Colors.INFO};
    }}

    .error-card.success {{
        background: {rgba(DesignTokens.Colors.SUCCESS, 0.05)};
        border-left-color: {DesignTokens.Colors.SUCCESS};
    }}

    .error-icon {{
        flex-shrink: 0;
        width: 24px;
        height: 24px;
        font-size: 24px;
    }}

    .error-content {{
        flex: 1;
    }}

    .error-title {{
        font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
        font-size: {DesignTokens.Typography.BODY};
        color: {DesignTokens.Colors.TEXT_PRIMARY};
        margin-bottom: {DesignTokens.Spacing.M_XS};
    }}

    .error-message {{
        font-size: {DesignTokens.Typography.SMALL};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        line-height: {DesignTokens.Typography.LINE_HEIGHT_BODY};
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .error-details {{
        font-size: {DesignTokens.Typography.XSMALL};
        color: {DesignTokens.Colors.TEXT_HINT};
        background: {DesignTokens.Colors.WHITE};
        padding: {DesignTokens.Spacing.P_SM};
        border-radius: {DesignTokens.Radius.SM};
        font-family: 'Courier New', monospace;
        overflow-x: auto;
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .error-actions {{
        display: flex;
        gap: {DesignTokens.Spacing.M_SM};
        flex-wrap: wrap;
    }}

    /* ========== 警告框样式 ========== */

    .alert {{
        padding: {DesignTokens.Spacing.P_MD};
        border-radius: {DesignTokens.Radius.MD};
        margin-bottom: {DesignTokens.Spacing.M_MD};
        display: flex;
        align-items: flex-start;
        gap: {DesignTokens.Spacing.M_SM};
    }}

    .alert-danger {{
        background: {rgba(DesignTokens.Colors.ERROR, 0.1)};
        border: 1px solid {rgba(DesignTokens.Colors.ERROR, 0.3)};
        color: {DesignTokens.Colors.ERROR};
    }}

    .alert-warning {{
        background: {rgba(DesignTokens.Colors.WARNING, 0.1)};
        border: 1px solid {rgba(DesignTokens.Colors.WARNING, 0.3)};
        color: {DesignTokens.Colors.WARNING};
    }}

    .alert-info {{
        background: {rgba(DesignTokens.Colors.INFO, 0.1)};
        border: 1px solid {rgba(DesignTokens.Colors.INFO, 0.3)};
        color: {DesignTokens.Colors.INFO};
    }}

    .alert-success {{
        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
        border: 1px solid {rgba(DesignTokens.Colors.SUCCESS, 0.3)};
        color: {DesignTokens.Colors.SUCCESS};
    }}

    .alert-icon {{
        flex-shrink: 0;
        font-size: 20px;
    }}

    .alert-content {{
        flex: 1;
    }}

    .alert-heading {{
        font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
        margin-bottom: {DesignTokens.Spacing.M_XS};
    }}

    .alert-text {{
        font-size: {DesignTokens.Typography.SMALL};
    }}

    /* ========== 空状态样式 ========== */

    .empty-state {{
        text-align: center;
        padding: {DesignTokens.Spacing.P_XL} {DesignTokens.Spacing.P_MD};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
    }}

    .empty-state-icon {{
        font-size: 64px;
        margin-bottom: {DesignTokens.Spacing.M_MD};
        opacity: 0.5;
    }}

    .empty-state-title {{
        font-size: {DesignTokens.Typography.H4};
        font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
        color: {DesignTokens.Colors.TEXT_PRIMARY};
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .empty-state-description {{
        font-size: {DesignTokens.Typography.BODY};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        margin-bottom: {DesignTokens.Spacing.M_MD};
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
    }}

    .empty-state-action {{
        margin-top: {DesignTokens.Spacing.M_MD};
    }}

    /* ========== 错误边界样式 ========== */

    .error-boundary {{
        background: {DesignTokens.Colors.BG_PRIMARY};
        border: 2px dashed {DesignTokens.Colors.BORDER_DEFAULT};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_XL};
        text-align: center;
        margin: {DesignTokens.Spacing.M_LG} 0;
    }}

    .error-boundary-icon {{
        font-size: 48px;
        margin-bottom: {DesignTokens.Spacing.M_MD};
    }}

    .error-boundary-title {{
        font-size: {DesignTokens.Typography.H3};
        font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
        color: {DesignTokens.Colors.TEXT_PRIMARY};
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .error-boundary-message {{
        font-size: {DesignTokens.Typography.BODY};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        margin-bottom: {DesignTokens.Spacing.M_MD};
    }}
    </style>
    """

    st.markdown(error_styles, unsafe_allow_html=True)


def show_error_card(
    title: str,
    message: str,
    icon: str = "❌",
    details: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None
):
    """
    显示错误卡片

    Args:
        title: 错误标题
        message: 错误消息
        icon: 错误图标（默认：❌）
        details: 详细信息（可选）
        actions: 操作按钮列表（可选）
            格式：[{"label": "重试", "key": "retry"}, ...]
    """
    details_html = ""
    if details:
        details_html = f'<div class="error-details">{details}</div>'

    actions_html = ""
    if actions:
        buttons_html = ""
        for action in actions:
            label = action.get("label", "操作")
            key = action.get("key", f"action_{label}")
            buttons_html += f'<button class="btn" data-key="{key}">{label}</button>'

        actions_html = f'<div class="error-actions">{buttons_html}</div>'

    st.markdown(
        f"""
        <div class="error-card">
            <div class="error-icon">{icon}</div>
            <div class="error-content">
                <div class="error-title">{title}</div>
                <div class="error-message">{message}</div>
                {details_html}
                {actions_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 处理按钮点击（返回被点击的key）
    if actions:
        for action in actions:
            key = action.get("key")
            if key and st.button(action.get("label", "操作"), key=key):
                return key

    return None


def show_warning_card(
    title: str,
    message: str,
    icon: str = "⚠️",
    details: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None
):
    """
    显示警告卡片

    Args:
        title: 警告标题
        message: 警告消息
        icon: 警告图标（默认：⚠️）
        details: 详细信息（可选）
        actions: 操作按钮列表（可选）
    """
    details_html = ""
    if details:
        details_html = f'<div class="error-details">{details}</div>'

    actions_html = ""
    if actions:
        buttons_html = ""
        for action in actions:
            label = action.get("label", "操作")
            key = action.get("key", f"action_{label}")
            buttons_html += f'<button class="btn" data-key="{key}">{label}</button>'

        actions_html = f'<div class="error-actions">{buttons_html}</div>'

    st.markdown(
        f"""
        <div class="error-card warning">
            <div class="error-icon">{icon}</div>
            <div class="error-content">
                <div class="error-title">{title}</div>
                <div class="error-message">{message}</div>
                {details_html}
                {actions_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if actions:
        for action in actions:
            key = action.get("key")
            if key and st.button(action.get("label", "操作"), key=key):
                return key

    return None


def show_alert(
    message: str,
    alert_type: str = "info",
    heading: Optional[str] = None,
    icon: Optional[str] = None
):
    """
    显示警告框

    Args:
        message: 消息内容
        alert_type: 类型（danger/warning/info/success）
        heading: 标题（可选）
        icon: 图标（可选）
    """
    icons = {
        "danger": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅"
    }

    icon_html = icon or icons.get(alert_type, "ℹ️")

    heading_html = ""
    if heading:
        heading_html = f'<div class="alert-heading">{heading}</div>'

    st.markdown(
        f"""
        <div class="alert alert-{alert_type}">
            <div class="alert-icon">{icon_html}</div>
            <div class="alert-content">
                {heading_html}
                <div class="alert-text">{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_empty_state(
    title: str,
    description: str,
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_key: Optional[str] = None
):
    """
    显示空状态

    Args:
        title: 标题
        description: 描述文本
        icon: 图标（默认：📭）
        action_label: 操作按钮标签（可选）
        action_key: 操作按钮key（可选）

    Returns:
        如果点击了操作按钮，返回True
    """
    action_html = ""
    if action_label and action_key:
        action_html = f'<div class="empty-state-action"><button data-key="{action_key}">{action_label}</button></div>'

    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-description">{description}</div>
            {action_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    if action_label and action_key and st.button(action_label, key=action_key):
        return True

    return False


def show_error_boundary(
    title: str = "出错了",
    message: str = "应用程序遇到了一个错误",
    icon: str = "💥",
    show_reload: bool = True
):
    """
    显示错误边界（重大错误）

    Args:
        title: 错误标题
        message: 错误消息
        icon: 错误图标（默认：💥）
        show_reload: 是否显示重新加载按钮
    """
    reload_html = ""
    if show_reload:
        reload_html = """
        <div class="empty-state-action">
            <button onclick="location.reload()">重新加载页面</button>
        </div>
        """

    st.markdown(
        f"""
        <div class="error-boundary">
            <div class="error-boundary-icon">{icon}</div>
            <div class="error-boundary-title">{title}</div>
            <div class="error-boundary-message">{message}</div>
            {reload_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def exception_to_dict(exception: Exception) -> Dict[str, Any]:
    """
    将异常转换为字典

    Args:
        exception: 异常对象

    Returns:
        包含异常信息的字典
    """
    import traceback

    return {
        "type": type(exception).__name__,
        "message": str(exception),
        "traceback": traceback.format_exc()
    }


def handle_exception(
    exception: Exception,
    title: Optional[str] = None,
    show_traceback: bool = False,
    actions: Optional[List[Dict[str, Any]]] = None
):
    """
    处理并显示异常

    Args:
        exception: 异常对象
        title: 自定义标题（可选）
        show_traceback: 是否显示堆栈跟踪
        actions: 操作按钮列表（可选）
    """
    error_info = exception_to_dict(exception)

    default_title = f"{error_info['type']}错误"
    title = title or default_title

    details = error_info["traceback"] if show_traceback else None

    return show_error_card(
        title=title,
        message=error_info["message"],
        details=details,
        actions=actions
    )


# 便捷装饰器：自动处理异常
def catch_errors(
    default_message: str = "操作失败",
    show_traceback: bool = False,
    alert_type: str = "danger"
):
    """
    装饰器：自动捕获并显示异常

    Args:
        default_message: 默认错误消息
        show_traceback: 是否显示堆栈跟踪
        alert_type: 警告框类型
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if show_traceback:
                    handle_exception(e, show_traceback=True)
                else:
                    show_alert(
                        message=f"{default_message}: {str(e)}",
                        alert_type=alert_type,
                        heading="错误"
                    )
                return None
        return wrapper
    return decorator


# 示例：在Streamlit应用中使用
if __name__ == "__main__":
    apply_global_styles()
    apply_error_styles()

    st.title("错误处理组件示例")

    # 错误卡片
    st.subheader("错误卡片")
    show_error_card(
        title="连接失败",
        message="无法连接到服务器，请检查网络连接",
        details="ConnectionError: Connection refused",
        actions=[
            {"label": "重试", "key": "retry"},
            {"label": "取消", "key": "cancel"}
        ]
    )

    # 警告卡片
    st.subheader("警告卡片")
    show_warning_card(
        title="数据同步警告",
        message="上次同步时间是2小时前，数据可能不是最新的"
    )

    # 警告框
    st.subheader("警告框")
    show_alert("这是一条重要信息", "info", "提示")

    # 空状态
    st.subheader("空状态")
    show_empty_state(
        title="暂无数据",
        description="还没有任何数据，点击下方按钮开始添加",
        icon="📊",
        action_label="添加数据",
        action_key="add_data"
    )

    # 使用装饰器捕获异常
    @catch_errors("计算失败", show_traceback=True)
    def risky_function():
        raise ValueError("这是一个测试错误")

    if st.button("测试错误处理"):
        risky_function()

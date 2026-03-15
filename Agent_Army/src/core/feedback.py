"""
反馈系统组件

提供用户操作反馈组件，包括Toast通知、成功消息、进度提示等。

用途：为用户操作提供即时反馈，提升用户体验
"""

import streamlit as st
import time
from typing import Optional, List
from enum import Enum
from .design_tokens import DesignTokens, rgba
from .global_styles import apply_global_styles


class ToastType(Enum):
    """Toast类型"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def apply_feedback_styles():
    """应用反馈系统相关的CSS样式"""
    feedback_styles = f"""
    <style>
    /* ========== Toast容器 ========== */

    .toast-container {{
        position: fixed;
        top: {DesignTokens.Spacing.M_LG};
        right: {DesignTokens.Spacing.M_LG};
        z-index: {DesignTokens.ZIndex.TOOLTIP};
        max-width: 400px;
        width: 100%;
        pointer-events: none;
    }}

    /* ========== Toast卡片 ========== */

    .toast {{
        background: {DesignTokens.Colors.WHITE};
        border-radius: {DesignTokens.Radius.MD};
        box-shadow: {DesignTokens.Shadow.LG};
        padding: {DesignTokens.Spacing.P_MD};
        margin-bottom: {DesignTokens.Spacing.M_SM};
        display: flex;
        align-items: flex-start;
        gap: {DesignTokens.Spacing.M_SM};
        animation: toast-slide-in 0.3s {DesignTokens.Animation.EASING_OUT};
        pointer-events: auto;
        border-left: 4px solid transparent;
    }}

    .toast.success {{
        border-left-color: {DesignTokens.Colors.SUCCESS};
    }}

    .toast.error {{
        border-left-color: {DesignTokens.Colors.ERROR};
    }}

    .toast.warning {{
        border-left-color: {DesignTokens.Colors.WARNING};
    }}

    .toast.info {{
        border-left-color: {DesignTokens.Colors.INFO};
    }}

    .toast.removing {{
        animation: toast-slide-out 0.3s {DesignTokens.Animation.EASING_IN} forwards;
    }}

    @keyframes toast-slide-in {{
        from {{
            transform: translateX(100%);
            opacity: 0;
        }}
        to {{
            transform: translateX(0);
            opacity: 1;
        }}
    }}

    @keyframes toast-slide-out {{
        from {{
            transform: translateX(0);
            opacity: 1;
        }}
        to {{
            transform: translateX(100%);
            opacity: 0;
        }}
    }}

    /* Toast内容 */
    .toast-icon {{
        font-size: 24px;
        flex-shrink: 0;
    }}

    .toast-content {{
        flex: 1;
        min-width: 0;
    }}

    .toast-title {{
        font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
        font-size: {DesignTokens.Typography.BODY};
        color: {DesignTokens.Colors.TEXT_PRIMARY};
        margin-bottom: {DesignTokens.Spacing.M_XS};
    }}

    .toast-message {{
        font-size: {DesignTokens.Typography.SMALL};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        line-height: {DesignTokens.Typography.LINE_HEIGHT_BODY};
    }}

    .toast-close {{
        flex-shrink: 0;
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: {DesignTokens.Colors.TEXT_HINT};
        padding: {DesignTokens.Spacing.P_XS};
        transition: color {DesignTokens.Animation.DURATION_FAST} {DesignTokens.Animation.EASING_DEFAULT};
    }}

    .toast-close:hover {{
        color: {DesignTokens.Colors.TEXT_PRIMARY};
    }}

    /* ========== 成功提示 ========== */

    .success-message {{
        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
        border: 1px solid {rgba(DesignTokens.Colors.SUCCESS, 0.3)};
        color: {DesignTokens.Colors.SUCCESS};
        padding: {DesignTokens.Spacing.P_MD};
        border-radius: {DesignTokens.Radius.MD};
        display: flex;
        align-items: center;
        gap: {DesignTokens.Spacing.M_SM};
        margin: {DesignTokens.Spacing.M_SM} 0;
        animation: fade-in 0.3s {DesignTokens.Animation.EASING_DEFAULT};
    }}

    @keyframes fade-in {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .success-message-icon {{
        font-size: 24px;
    }}

    .success-message-text {{
        flex: 1;
        font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};
    }}

    /* ========== 按钮反馈 ========== */

    .btn-loading {{
        position: relative;
        pointer-events: none;
        opacity: 0.7;
    }}

    .btn-loading::after {{
        content: "";
        position: absolute;
        width: 16px;
        height: 16px;
        top: 50%;
        left: 50%;
        margin-left: -8px;
        margin-top: -8px;
        border: 2px solid transparent;
        border-top-color: {DesignTokens.Colors.TEXT_CONTRAST};
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }}

    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}

    /* ========== 进度提示 ========== */

    .progress-toast {{
        background: {DesignTokens.Colors.WHITE};
        border-radius: {DesignTokens.Radius.MD};
        box-shadow: {DesignTokens.Shadow.LG};
        padding: {DesignTokens.Spacing.P_MD};
        margin-bottom: {DesignTokens.Spacing.M_SM};
        animation: toast-slide-in 0.3s {DesignTokens.Animation.EASING_OUT};
    }}

    .progress-toast-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .progress-toast-title {{
        font-weight: {DesignTokens.Typography.WEIGHT_SEMIBOLD};
        color: {DesignTokens.Colors.TEXT_PRIMARY};
    }}

    .progress-toast-percentage {{
        font-size: {DesignTokens.Typography.SMALL};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
    }}

    .progress-toast-bar {{
        height: 6px;
        background: {DesignTokens.Colors.GRAY_200};
        border-radius: {DesignTokens.Radius.FULL};
        overflow: hidden;
    }}

    .progress-toast-fill {{
        height: 100%;
        background: linear-gradient(90deg, {DesignTokens.Colors.PRIMARY}, {DesignTokens.Colors.PRIMARY_LIGHT});
        border-radius: {DesignTokens.Radius.FULL};
        transition: width 0.3s ease;
    }}
    </style>
    """

    st.markdown(feedback_styles, unsafe_allow_html=True)


def toast(
    message: str,
    toast_type: ToastType = ToastType.INFO,
    title: Optional[str] = None,
    duration: Optional[int] = None,
    icon: Optional[str] = None
):
    """
    显示Toast通知（使用st.toast，Streamlit原生支持）

    Args:
        message: 消息内容
        toast_type: Toast类型（success/error/warning/info）
        title: 标题（可选）
        duration: 持续时间（秒），None表示不自动关闭
        icon: 自定义图标（可选）
    """
    # Streamlit原生toast支持
    icon_map = {
        ToastType.SUCCESS: "✅",
        ToastType.ERROR: "❌",
        ToastType.WARNING: "⚠️",
        ToastType.INFO: "ℹ️"
    }

    toast_icon = icon or icon_map.get(toast_type, "ℹ️")
    full_message = f"{toast_icon} {message}"

    if title:
        full_message = f"**{title}**\n\n{full_message}"

    # 使用Streamlit原生toast
    st.toast(full_message, icon=toast_icon.value if isinstance(toast_icon, ToastType) else toast_icon)


def toast_success(message: str, title: Optional[str] = None):
    """显示成功Toast"""
    toast(message, ToastType.SUCCESS, title)


def toast_error(message: str, title: Optional[str] = None):
    """显示错误Toast"""
    toast(message, ToastType.ERROR, title)


def toast_warning(message: str, title: Optional[str] = None):
    """显示警告Toast"""
    toast(message, ToastType.WARNING, title)


def toast_info(message: str, title: Optional[str] = None):
    """显示信息Toast"""
    toast(message, ToastType.INFO, title)


def show_success_message(message: str, icon: str = "✅"):
    """
    显示成功消息（内联样式）

    Args:
        message: 消息内容
        icon: 图标
    """
    st.markdown(
        f"""
        <div class="success-message">
            <div class="success-message-icon">{icon}</div>
            <div class="success-message-text">{message}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_progress_toast(
    title: str,
    progress: float,
    message: Optional[str] = None
):
    """
    显示进度Toast（使用st.progress）

    Args:
        title: 标题
        progress: 进度值（0-100）
        message: 附加消息（可选）
    """
    # 使用Streamlit原生progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    progress_bar.progress(progress / 100)

    if message:
        status_text.text(f"{title}: {message} ({progress:.0f}%)")
    else:
        status_text.text(f"{title}: {progress:.0f}%")

    return progress_bar, status_text


def update_progress_toast(progress_bar, status_text, progress: float, message: Optional[str] = None):
    """
    更新进度Toast

    Args:
        progress_bar: 进度条对象
        status_text: 状态文本对象
        progress: 进度值（0-100）
        message: 附加消息（可选）
    """
    progress_bar.progress(progress / 100)

    if message:
        status_text.text(f"处理中: {message} ({progress:.0f}%)")
    else:
        status_text.text(f"处理中: {progress:.0f}%")


def confirm_action(
    message: str,
    button_label: str = "确认",
    button_type: str = "primary",
    cancel_label: str = "取消"
) -> bool:
    """
    显示确认对话框

    Args:
        message: 确认消息
        button_label: 确认按钮标签
        button_type: 按钮类型（primary/secondary）
        cancel_label: 取消按钮标签

    Returns:
        用户是否确认
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button(button_label, type="primary" if button_type == "primary" else "secondary"):
            return True

    with col2:
        if st.button(cancel_label):
            return False

    return False


def button_with_feedback(
    label: str,
    on_click: callable,
    loading_text: str = "处理中...",
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
    show_loading: bool = True
):
    """
    带反馈的按钮

    Args:
        label: 按钮标签
        on_click: 点击回调函数
        loading_text: 加载时文本
        success_message: 成功消息
        error_message: 错误消息
        show_loading: 是否显示加载状态

    Returns:
        函数执行结果
    """
    if st.button(label):
        try:
            if show_loading:
                with st.spinner(loading_text):
                    result = on_click()
            else:
                result = on_click()

            if success_message:
                toast_success(success_message)

            return result

        except Exception as e:
            if error_message:
                toast_error(f"{error_message}: {str(e)}")
            else:
                toast_error(str(e))

            return None


# 便捷装饰器：自动显示Toast反馈
def with_feedback(
    success_message: str = "操作成功",
    error_message: str = "操作失败",
    loading_message: str = "处理中..."
):
    """
    装饰器：自动为函数显示反馈

    Args:
        success_message: 成功消息
        error_message: 错误消息
        loading_message: 加载消息
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                with st.spinner(loading_message):
                    result = func(*args, **kwargs)

                toast_success(success_message)
                return result

            except Exception as e:
                toast_error(f"{error_message}: {str(e)}")
                return None

        return wrapper
    return decorator


# 示例：在Streamlit应用中使用
if __name__ == "__main__":
    apply_global_styles()
    apply_feedback_styles()

    st.title("反馈系统组件示例")

    # Toast示例
    st.subheader("Toast通知")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("成功"):
            toast_success("操作成功完成！")

    with col2:
        if st.button("错误"):
            toast_error("操作失败，请重试")

    with col3:
        if st.button("警告"):
            toast_warning("请注意潜在风险")

    with col4:
        if st.button("信息"):
            toast_info("这是一条提示信息")

    # 成功消息
    st.subheader("成功消息")
    if st.button("显示成功消息"):
        show_success_message("数据保存成功！")

    # 进度Toast
    st.subheader("进度Toast")
    if st.button("模拟进度"):
        progress_bar, status_text = show_progress_toast("处理任务", 0)

        for i in range(0, 101, 10):
            time.sleep(0.3)
            update_progress_toast(progress_bar, status_text, i, f"步骤 {i//10 + 1}/10")

        toast_success("任务完成！")

    # 确认对话框
    st.subheader("确认对话框")
    if confirm_action("确定要执行此操作吗？"):
        toast_success("操作已确认")
    else:
        toast_info("操作已取消")

    # 带反馈的按钮
    st.subheader("带反馈的按钮")

    def sample_task():
        time.sleep(2)
        return "任务完成"

    button_with_feedback(
        label="执行任务",
        on_click=sample_task,
        loading_text="正在执行任务...",
        success_message="任务执行成功！"
    )

    # 使用装饰器
    @with_feedback(
        success_message="数据加载成功",
        error_message="数据加载失败",
        loading_message="正在加载数据..."
    )
    def load_data():
        time.sleep(2)
        # 模拟成功
        return {"data": [1, 2, 3]}

    if st.button("加载数据"):
        result = load_data()
        if result:
            st.write("数据:", result)

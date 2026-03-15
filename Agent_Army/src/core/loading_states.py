"""
加载状态组件

提供各种加载状态的UI组件，包括骨架屏、进度条、加载动画等。

用途：改善用户体验，在数据加载时提供视觉反馈
"""

import streamlit as st
import time
from typing import Optional, List, Dict, Any
from .design_tokens import DesignTokens, rgba
from .global_styles import apply_global_styles


def apply_loading_styles():
    """应用加载状态相关的CSS样式"""
    loading_styles = f"""
    <style>
    /* ========== 骨架屏样式 ========== */

    .skeleton {{
        background: linear-gradient(90deg,
            {DesignTokens.Colors.GRAY_200} 0%,
            {DesignTokens.Colors.GRAY_100} 50%,
            {DesignTokens.Colors.GRAY_200} 100%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        border-radius: {DesignTokens.Radius.MD};
    }}

    .skeleton-text {{
        height: 1em;
        margin-bottom: {DesignTokens.Spacing.M_SM};
    }}

    .skeleton-title {{
        height: 1.5em;
        width: 60%;
        margin-bottom: {DesignTokens.Spacing.M_MD};
    }}

    .skeleton-card {{
        height: 120px;
        margin-bottom: {DesignTokens.Spacing.M_MD};
    }}

    .skeleton-avatar {{
        width: 40px;
        height: 40px;
        border-radius: {DesignTokens.Radius.FULL};
    }}

    @keyframes skeleton-loading {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}

    /* ========== 旋转加载器 ========== */

    .spinner {{
        border: 3px solid {DesignTokens.Colors.GRAY_200};
        border-top: 3px solid {DesignTokens.Colors.PRIMARY};
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: {DesignTokens.Spacing.M_MD} auto;
    }}

    .spinner-sm {{
        width: 20px;
        height: 20px;
        border-width: 2px;
    }}

    .spinner-lg {{
        width: 60px;
        height: 60px;
        border-width: 4px;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    /* ========== 脉冲加载器 ========== */

    .pulse-loader {{
        width: 40px;
        height: 40px;
        background: {DesignTokens.Colors.PRIMARY};
        border-radius: {DesignTokens.Radius.FULL};
        animation: pulse-scale 1.5s ease-in-out infinite;
        margin: {DesignTokens.Spacing.M_MD} auto;
    }}

    @keyframes pulse-scale {{
        0%, 100% {{
            transform: scale(1);
            opacity: 1;
        }}
        50% {{
            transform: scale(1.2);
            opacity: 0.7;
        }}
    }}

    /* ========== 点状加载器 ========== */

    .dot-loader {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: {DesignTokens.Spacing.M_SM};
        margin: {DesignTokens.Spacing.M_MD} auto;
    }}

    .dot {{
        width: 12px;
        height: 12px;
        background: {DesignTokens.Colors.PRIMARY};
        border-radius: {DesignTokens.Radius.FULL};
        animation: dot-bounce 1.4s ease-in-out infinite both;
    }}

    .dot:nth-child(1) {{ animation-delay: -0.32s; }}
    .dot:nth-child(2) {{ animation-delay: -0.16s; }}
    .dot:nth-child(3) {{ animation-delay: 0s; }}

    @keyframes dot-bounce {{
        0%, 80%, 100% {{
            transform: scale(0);
            opacity: 0.5;
        }}
        40% {{
            transform: scale(1);
            opacity: 1;
        }}
    }}

    /* ========== 进度条样式 ========== */

    .progress-container {{
        width: 100%;
        height: 8px;
        background: {DesignTokens.Colors.GRAY_200};
        border-radius: {DesignTokens.Radius.FULL};
        overflow: hidden;
        margin: {DesignTokens.Spacing.M_MD} 0;
    }}

    .progress-bar {{
        height: 100%;
        background: linear-gradient(90deg, {DesignTokens.Colors.PRIMARY}, {DesignTokens.Colors.PRIMARY_LIGHT});
        border-radius: {DesignTokens.Radius.FULL};
        transition: width {DesignTokens.Animation.DURATION_NORMAL} {DesignTokens.Animation.EASING_DEFAULT};
    }}

    .progress-striped {{
        background-image: linear-gradient(
            45deg,
            rgba(255, 255, 255, 0.15) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, 0.15) 50%,
            rgba(255, 255, 255, 0.15) 75%,
            transparent 75%,
            transparent
        );
        background-size: 1rem 1rem;
        animation: progress-stripes 1s linear infinite;
    }}

    @keyframes progress-stripes {{
        0% {{ background-position: 1rem 0; }}
        100% {{ background-position: 0 0; }}
    }}

    /* ========== 步骤进度条 ========== */

    .steps-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: {DesignTokens.Spacing.M_LG} 0;
        position: relative;
    }}

    .step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 1;
        flex: 1;
    }}

    .step-circle {{
        width: 40px;
        height: 40px;
        border-radius: {DesignTokens.Radius.FULL};
        background: {DesignTokens.Colors.GRAY_200};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        margin-bottom: {DesignTokens.Spacing.M_SM};
        transition: {DesignTokens.Animation.TRANSITION_NORMAL};
    }}

    .step.active .step-circle {{
        background: {DesignTokens.Colors.PRIMARY};
        color: {DesignTokens.Colors.TEXT_CONTRAST};
        box-shadow: 0 0 0 4px {rgba(DesignTokens.Colors.PRIMARY, 0.2)};
    }}

    .step.completed .step-circle {{
        background: {DesignTokens.Colors.SUCCESS};
        color: {DesignTokens.Colors.TEXT_CONTRAST};
    }}

    .step-label {{
        font-size: {DesignTokens.Typography.SMALL};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        text-align: center;
    }}

    .step.active .step-label {{
        color: {DesignTokens.Colors.PRIMARY};
        font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};
    }}

    .steps-line {{
        position: absolute;
        top: 20px;
        left: 0;
        right: 0;
        height: 2px;
        background: {DesignTokens.Colors.GRAY_200};
        z-index: 0;
    }}

    .steps-line-progress {{
        height: 100%;
        background: {DesignTokens.Colors.PRIMARY};
        transition: width {DesignTokens.Animation.DURATION_NORMAL} {DesignTokens.Animation.EASING_DEFAULT};
    }}

    /* ========== 加载覆盖层 ========== */

    .loading-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: {DesignTokens.ZIndex.MODAL};
    }}

    .loading-text {{
        margin-top: {DesignTokens.Spacing.M_MD};
        font-size: {DesignTokens.Typography.BODY};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
    }}
    </style>
    """

    st.markdown(loading_styles, unsafe_allow_html=True)


def show_spinner(size: str = "md", text: str = "加载中..."):
    """
    显示旋转加载器

    Args:
        size: 尺寸（sm/md/lg）
        text: 加载文本
    """
    size_class = f"spinner-{size}" if size != "md" else ""
    st.markdown(
        f"""
        <div class="spinner {size_class}"></div>
        <p class="text-center text-secondary">{text}</p>
        """,
        unsafe_allow_html=True
    )


def show_pulse_loader(text: str = "处理中..."):
    """
    显示脉冲加载器

    Args:
        text: 加载文本
    """
    st.markdown(
        f"""
        <div class="pulse-loader"></div>
        <p class="text-center text-secondary">{text}</p>
        """,
        unsafe_allow_html=True
    )


def show_dot_loader(text: str = "加载中..."):
    """
    显示点状加载器

    Args:
        text: 加载文本
    """
    st.markdown(
        f"""
        <div class="dot-loader">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
        <p class="text-center text-secondary">{text}</p>
        """,
        unsafe_allow_html=True
    )


def show_skeleton_card(count: int = 3):
    """
    显示骨架屏卡片

    Args:
        count: 卡片数量
    """
    cards_html = ""
    for _ in range(count):
        cards_html += f'<div class="skeleton skeleton-card"></div>'

    st.markdown(cards_html, unsafe_allow_html=True)


def show_skeleton_text(lines: int = 3, has_title: bool = True):
    """
    显示骨架屏文本

    Args:
        lines: 行数
        has_title: 是否包含标题
    """
    html = ""
    if has_title:
        html += '<div class="skeleton skeleton-title"></div>'

    for _ in range(lines):
        html += '<div class="skeleton skeleton-text"></div>'

    st.markdown(html, unsafe_allow_html=True)


def show_progress_bar(progress: float, text: Optional[str] = None, striped: bool = False):
    """
    显示进度条

    Args:
        progress: 进度值（0-100）
        text: 进度文本
        striped: 是否显示条纹动画
    """
    striped_class = "progress-striped" if striped else ""

    st.markdown(
        f"""
        <div class="progress-container">
            <div class="progress-bar {striped_class}" style="width: {progress}%"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if text:
        st.caption(f"{text} ({progress:.1f}%)")


def show_steps(
    steps: List[str],
    current_step: int,
    completed_steps: Optional[List[int]] = None
):
    """
    显示步骤进度条

    Args:
        steps: 步骤名称列表
        current_step: 当前步骤索引（从0开始）
        completed_steps: 已完成的步骤索引列表
    """
    completed_steps = completed_steps or []

    # 计算进度条宽度
    total_steps = len(steps)
    if total_steps <= 1:
        progress_width = 100
    else:
        progress_width = (current_step / (total_steps - 1)) * 100

    steps_html = '<div class="steps-container">'
    steps_html += f'<div class="steps-line"><div class="steps-line-progress" style="width: {progress_width}%"></div></div>'

    for i, step_name in enumerate(steps):
        step_class = "step"
        if i in completed_steps:
            step_class += " completed"
        elif i == current_step:
            step_class += " active"

        icon = "✓" if i in completed_steps else str(i + 1)

        steps_html += f"""
        <div class="{step_class}">
            <div class="step-circle">{icon}</div>
            <div class="step-label">{step_name}</div>
        </div>
        """

    steps_html += '</div>'

    st.markdown(steps_html, unsafe_allow_html=True)


def show_loading_overlay(text: str = "加载中...", loader_type: str = "spinner"):
    """
    显示加载覆盖层（使用st.status）

    Args:
        text: 加载文本
        loader_type: 加载器类型（spinner/pulse/dot）
    """
    with st.status(text, expanded=True) as status:
        if loader_type == "spinner":
            st.markdown('<div class="spinner"></div>', unsafe_allow_html=True)
        elif loader_type == "pulse":
            st.markdown('<div class="pulse-loader"></div>', unsafe_allow_html=True)
        elif loader_type == "dot":
            st.markdown("""
            <div class="dot-loader">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
            """, unsafe_allow_html=True)

        return status


# 示例：模拟长时间运行的任务
def simulate_long_task(task_name: str, duration: float = 3.0):
    """
    模拟长时间运行的任务（用于演示）

    Args:
        task_name: 任务名称
        duration: 持续时间（秒）
    """
    steps = ["初始化", "处理数据", "生成结果", "完成"]

    for i, step in enumerate(steps):
        show_steps(steps, i, completed_steps=list(range(i)))
        time.sleep(duration / len(steps))


# 便捷装饰器：自动显示加载状态
def with_loading(
    loading_text: str = "加载中...",
    loader_type: str = "spinner"
):
    """
    装饰器：自动为函数显示加载状态

    Args:
        loading_text: 加载文本
        loader_type: 加载器类型
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            status = show_loading_overlay(loading_text, loader_type)
            try:
                result = func(*args, **kwargs)
                status.update(label="完成！", state="complete", expanded=False)
                return result
            except Exception as e:
                status.update(label=f"错误: {str(e)}", state="error", expanded=True)
                raise
        return wrapper
    return decorator


# 示例：在Streamlit应用中使用
if __name__ == "__main__":
    apply_global_styles()
    apply_loading_styles()

    st.title("加载状态组件示例")

    # 旋转加载器
    st.subheader("旋转加载器")
    show_spinner()

    # 点状加载器
    st.subheader("点状加载器")
    show_dot_loader()

    # 进度条
    st.subheader("进度条")
    show_progress_bar(65, "处理中", striped=True)

    # 步骤进度条
    st.subheader("步骤进度条")
    show_steps(
        ["初始化", "分析数据", "生成报告", "完成"],
        current_step=1,
        completed_steps=[0]
    )

    # 骨架屏
    st.subheader("骨架屏卡片")
    show_skeleton_card(3)

    # 使用装饰器
    @with_loading("正在执行任务...", "pulse")
    def long_running_task():
        time.sleep(2)
        return "任务完成！"

    if st.button("执行任务"):
        result = long_running_task()
        st.success(result)

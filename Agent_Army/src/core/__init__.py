"""
Agent Army Core Module

核心模块，提供统一的设计系统和UI组件。
"""

# 导入设计系统
from .design_tokens import DesignTokens, get_army_color, rgba
from .global_styles import (
    get_global_styles,
    apply_global_styles,
    get_custom_css,
    apply_custom_css,
    styled_container,
    styled_text
)
from .loading_states import (
    apply_loading_styles,
    show_spinner,
    show_pulse_loader,
    show_dot_loader,
    show_skeleton_card,
    show_skeleton_text,
    show_progress_bar,
    show_steps,
    show_loading_overlay,
    with_loading
)
from .error_handling import (
    apply_error_styles,
    show_error_card,
    show_warning_card,
    show_alert,
    show_empty_state,
    show_error_boundary,
    exception_to_dict,
    handle_exception,
    catch_errors
)
from .feedback import (
    apply_feedback_styles,
    toast,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    show_success_message,
    show_progress_toast,
    update_progress_toast,
    confirm_action,
    button_with_feedback,
    with_feedback,
    ToastType
)

__all__ = [
    # 设计系统
    "DesignTokens",
    "get_army_color",
    "rgba",

    # 全局样式
    "get_global_styles",
    "apply_global_styles",
    "get_custom_css",
    "apply_custom_css",
    "styled_container",
    "styled_text",

    # 加载状态
    "apply_loading_styles",
    "show_spinner",
    "show_pulse_loader",
    "show_dot_loader",
    "show_skeleton_card",
    "show_skeleton_text",
    "show_progress_bar",
    "show_steps",
    "show_loading_overlay",
    "with_loading",

    # 错误处理
    "apply_error_styles",
    "show_error_card",
    "show_warning_card",
    "show_alert",
    "show_empty_state",
    "show_error_boundary",
    "exception_to_dict",
    "handle_exception",
    "catch_errors",

    # 反馈系统
    "apply_feedback_styles",
    "toast",
    "toast_success",
    "toast_error",
    "toast_warning",
    "toast_info",
    "show_success_message",
    "show_progress_toast",
    "update_progress_toast",
    "confirm_action",
    "button_with_feedback",
    "with_feedback",
    "ToastType",
]

__version__ = "2.0.0"
__author__ = "Agent Army Team"

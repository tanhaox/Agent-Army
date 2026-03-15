"""
设计系统使用示例

展示如何在Streamlit页面中使用新的设计系统和UI组件。

快速开始：
1. 导入模块
2. 应用全局样式
3. 使用组件
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import (
    DesignTokens,
    apply_global_styles,
    apply_loading_styles,
    apply_error_styles,
    apply_feedback_styles,
    toast_success,
    toast_error,
    show_skeleton_card,
    show_progress_bar,
    show_steps,
    show_error_card,
    show_empty_state,
    show_success_message
)


def page_header(title: str, subtitle: str = ""):
    """
    页面头部组件

    Args:
        title: 标题
        subtitle: 副标题
    """
    st.markdown(
        f"""
        <div style="margin-bottom: {DesignTokens.Spacing.LG};">
            <h1 style="color: {DesignTokens.Colors.PRIMARY}; margin-bottom: {DesignTokens.Spacing.XS};">
                {title}
            </h1>
            {f'<p style="color: {DesignTokens.Colors.TEXT_SECONDARY};">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    """主函数"""
    # 应用所有样式
    apply_global_styles()
    apply_loading_styles()
    apply_error_styles()
    apply_feedback_styles()

    # 页面标题
    page_header(
        "Agent Army V2.0 - 设计系统示例",
        "展示新的UI组件和设计系统"
    )

    # 示例1：颜色系统
    with st.expander("🎨 颜色系统", expanded=False):
        st.subheader("主色调")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div style="background: {DesignTokens.Colors.PRIMARY}; padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    Primary<br>{DesignTokens.Colors.PRIMARY}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style="background: {DesignTokens.Colors.SECONDARY}; padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    Secondary<br>{DesignTokens.Colors.SECONDARY}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div style="background: {DesignTokens.Colors.ACCENT}; padding: 20px; border-radius: 8px; color: white; text-align: center;">
                    Accent<br>{DesignTokens.Colors.ACCENT}
                </div>
                """,
                unsafe_allow_html=True
            )

    # 示例2：加载状态
    with st.expander("⏳ 加载状态", expanded=False):
        st.subheader("骨架屏")
        show_skeleton_card(3)

        st.subheader("进度条")
        show_progress_bar(65, "处理中", striped=True)

        st.subheader("步骤进度")
        show_steps(
            ["初始化", "分析数据", "生成报告", "完成"],
            current_step=1,
            completed_steps=[0]
        )

    # 示例3：错误处理
    with st.expander("❌ 错误处理", expanded=False):
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

        st.subheader("空状态")
        show_empty_state(
            title="暂无数据",
            description="还没有任何数据，点击下方按钮开始添加",
            icon="📊",
            action_label="添加数据",
            action_key="add_data"
        )

    # 示例4：反馈系统
    with st.expander("✅ 反馈系统", expanded=True):
        st.subheader("Toast通知")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("成功", key="success_btn"):
                toast_success("操作成功完成！")

        with col2:
            if st.button("错误", key="error_btn"):
                toast_error("操作失败，请重试")

        with col3:
            if st.button("警告", key="warning_btn"):
                toast_warning("请注意潜在风险")

        with col4:
            if st.button("信息", key="info_btn"):
                toast_info("这是一条提示信息")

        st.subheader("成功消息")
        if st.button("显示成功消息"):
            show_success_message("数据保存成功！")

    # 示例5：军团主题色
    with st.expander("🏷️ 军团主题色", expanded=False):
        st.subheader("各军团主题色")

        armies = [
            ("热点捕捉军团", DesignTokens.Colors.ARMY_HOTSPOT),
            ("产业分析军团", DesignTokens.Colors.ARMY_INDUSTRY),
            ("个股挖掘军团", DesignTokens.Colors.ARMY_STOCK),
            ("目标预测军团", DesignTokens.Colors.ARMY_TARGET),
            ("策略执行军团", DesignTokens.Colors.ARMY_STRATEGY),
            ("结果验证军团", DesignTokens.Colors.ARMY_VALIDATION),
            ("战略层", DesignTokens.Colors.ARMY_STRATEGIC),
        ]

        for army_name, color in armies:
            st.markdown(
                f"""
                <div style="
                    background: {color};
                    padding: 12px;
                    border-radius: 8px;
                    color: white;
                    margin-bottom: 8px;
                    font-weight: 500;
                ">
                    {army_name}
                </div>
                """,
                unsafe_allow_html=True
            )

    # 底部信息
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: {DesignTokens.Colors.TEXT_HINT}; padding: 20px;">
            <p>Agent Army V2.0 - 设计系统示例</p>
            <p style="font-size: {DesignTokens.Typography.XSMALL};">
                使用统一的Design Tokens、加载状态、错误处理和反馈系统
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

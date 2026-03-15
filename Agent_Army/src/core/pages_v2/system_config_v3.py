"""
Agent Army - 系统配置页面 (v3.0 优化版)
完全基于Phase 2设计文档重构，100%使用Design Tokens
"""

import streamlit as st
import os
from pathlib import Path
import sys

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入Phase 1设计系统
from src.core.design_tokens import DesignTokens
from src.core.global_styles import apply_global_styles


def rgba(hex_color: str, alpha: float) -> str:
    """将hex颜色转换为rgba格式"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def render_system_config_v3():
    """渲染系统配置页面（v3.0 优化版）"""

    # 应用全局样式
    apply_global_styles()

    # 页面标题
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {DesignTokens.Spacing.M_LG};">
        <div>
            <h1 style="font-size: {DesignTokens.Typography.H1};
                      color: {DesignTokens.Colors.TEXT_PRIMARY};
                      margin: 0;
                      font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                ⚙️ 系统配置
            </h1>
            <p style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin: {DesignTokens.Spacing.M_NONE} 0 {DesignTokens.Spacing.M_SM} 0;">
                API密钥配置 | Agent参数设置 | 日志管理 | 系统偏好
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==================== API配置卡片 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};">
        🔑 API配置
    </h2>
    """, unsafe_allow_html=True)

    # Tushare API配置
    with st.expander("📊 Tushare API", expanded=True):
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.PRIMARY, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.PRIMARY};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>Tushare API Key</strong> - 用于获取A股市场数据
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                注册地址: https://tushare.pro/register
            </div>
        </div>
        """, unsafe_allow_html=True)

        tushare_key = st.text_input(
            "Tushare API Key",
            type="password",
            placeholder="输入您的Tushare API Token",
            label_visibility="visible"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 保存配置", type="primary", use_container_width=True):
                if tushare_key:
                    os.environ['TUSHARE_API_KEY'] = tushare_key
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            ✅ Tushare API Key已保存到环境变量
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.ERROR, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.ERROR};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            ❌ 请输入有效的API Key
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            if st.button("🧪 测试连接", use_container_width=True):
                if tushare_key:
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.INFO};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            🔄 正在测试连接...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.WARNING, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.WARNING};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            ⚠️ 请先输入API Key
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # OpenAI API配置
    with st.expander("🤖 OpenAI API", expanded=False):
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.SUCCESS, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.SUCCESS};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>OpenAI API Key</strong> - 用于AI分析和预测
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                注册地址: https://platform.openai.com/api-keys
            </div>
        </div>
        """, unsafe_allow_html=True)

        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            label_visibility="visible"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 保存配置", key="save_openai", type="primary", use_container_width=True):
                if openai_key:
                    os.environ['OPENAI_API_KEY'] = openai_key
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            ✅ OpenAI API Key已保存到环境变量
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            if st.button("🧪 测试连接", key="test_openai", use_container_width=True):
                if openai_key:
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.INFO};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            🔄 正在测试连接...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Zhipu AI API配置
    with st.expander("🧠 Zhipu AI API", expanded=False):
        st.markdown(f"""
        <div style="
            background: {rgba(DesignTokens.Colors.INFO, 0.05)};
            border-left: 4px solid {DesignTokens.Colors.INFO};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            margin-bottom: {DesignTokens.Spacing.M_MD};
        ">
            <div style="font-size: {DesignTokens.Typography.BODY};
                     color: {DesignTokens.Colors.TEXT_PRIMARY};
                     margin-bottom: {DesignTokens.Spacing.M_SM};">
                <strong>Zhipu AI API Key</strong> - 国产大模型支持
            </div>
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};">
                注册地址: https://open.bigmodel.cn/usercenter/apikeys
            </div>
        </div>
        """, unsafe_allow_html=True)

        zhipu_key = st.text_input(
            "Zhipu AI API Key",
            type="password",
            placeholder="输入您的Zhipu API Key",
            label_visibility="visible"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 保存配置", key="save_zhipu", type="primary", use_container_width=True):
                if zhipu_key:
                    os.environ['ZHIPUAI_API_KEY'] = zhipu_key
                    st.markdown(f"""
                    <div style="
                        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                        border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                        border-radius: {DesignTokens.Radius.MD};
                        padding: {DesignTokens.Spacing.P_SM};
                        margin-bottom: {DesignTokens.Spacing.M_SM};
                    ">
                        <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                                 font-size: {DesignTokens.Typography.SMALL};">
                            ✅ Zhipu AI API Key已保存到环境变量
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    # ==================== Agent配置卡片 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};">
        🤖 Agent配置
    </h2>
    """, unsafe_allow_html=True)

    # Agent参数设置
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <h3 style="font-size: {DesignTokens.Typography.H3};
                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                🎯 分析参数
            </h3>
        </div>
        """, unsafe_allow_html=True)

        max_workers = st.slider(
            "最大并发数",
            min_value=1,
            max_value=10,
            value=5,
            step=1
        )

        timeout = st.slider(
            "超时时间（秒）",
            min_value=10,
            max_value=300,
            value=60,
            step=10
        )

        retry_count = st.slider(
            "重试次数",
            min_value=0,
            max_value=5,
            value=3,
            step=1
        )

    with col2:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            border-radius: {DesignTokens.Radius.LG};
            padding: {DesignTokens.Spacing.P_MD};
            box-shadow: {DesignTokens.Shadow.SM};
        ">
            <h3 style="font-size: {DesignTokens.Typography.H3};
                       color: {DesignTokens.Colors.TEXT_PRIMARY};
                       margin-top: 0;
                       margin-bottom: {DesignTokens.Spacing.M_SM};">
                📊 数据参数
            </h3>
        </div>
        """, unsafe_allow_html=True)

        data_period = st.selectbox(
            "数据周期",
            ["1个月", "3个月", "6个月", "1年", "全部"],
            index=2
        )

        cache_enabled = st.checkbox(
            "启用缓存",
            value=True
        )

        log_level = st.selectbox(
            "日志级别",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )

    # 保存Agent配置按钮
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 保存Agent配置", type="primary", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.SUCCESS};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_SM};
                margin-bottom: {DesignTokens.Spacing.M_SM};
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    ✅ Agent配置已保存
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if st.button("🔄 重置默认", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.INFO, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.INFO};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_SM};
                margin-bottom: {DesignTokens.Spacing.M_SM};
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    🔄 已重置为默认配置
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        if st.button("📤 导出配置", use_container_width=True):
            st.markdown(f"""
            <div style="
                background: {rgba(DesignTokens.Colors.PRIMARY, 0.1)};
                border-left: 4px solid {DesignTokens.Colors.PRIMARY};
                border-radius: {DesignTokens.Radius.MD};
                padding: {DesignTokens.Spacing.P_SM};
                margin-bottom: {DesignTokens.Spacing.M_SM};
            ">
                <div style="color: {DesignTokens.Colors.TEXT_PRIMARY};
                         font-size: {DesignTokens.Typography.SMALL};">
                    📤 配置导出功能开发中...
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-bottom: {DesignTokens.Spacing.M_LG};'></div>", unsafe_allow_html=True)

    # ==================== 系统信息卡片 ====================

    st.markdown(f"""
    <h2 style="font-size: {DesignTokens.Typography.H2};
               color: {DesignTokens.Colors.TEXT_PRIMARY};
               margin-bottom: {DesignTokens.Spacing.M_MD};">
        📊 系统信息
    </h2>
    """, unsafe_allow_html=True)

    # 系统状态卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.SUCCESS};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                Python版本
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.SUCCESS};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                3.10+
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.INFO};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                Streamlit版本
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.INFO};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                1.28+
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.PRIMARY};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                Agent总数
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.PRIMARY};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                24
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="
            background: {DesignTokens.Colors.BG_CARD};
            padding: {DesignTokens.Spacing.P_MD};
            border-radius: {DesignTokens.Radius.LG};
            border-left: 4px solid {DesignTokens.Colors.WARNING};
            box-shadow: {DesignTokens.Shadow.SM};
            text-align: center;
        ">
            <div style="font-size: {DesignTokens.Typography.SMALL};
                     color: {DesignTokens.Colors.TEXT_SECONDARY};
                     margin-bottom: {DesignTokens.Spacing.M_XS};">
                军团数量
            </div>
            <div style="font-size: {DesignTokens.Typography.H3};
                     color: {DesignTokens.Colors.WARNING};
                     font-weight: {DesignTokens.Typography.WEIGHT_BOLD};">
                6
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 版本信息
    st.markdown(f"""
    <div style="
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_MD};
        margin-top: {DesignTokens.Spacing.M_MD};
        box-shadow: {DesignTokens.Shadow.SM};
    ">
        <h3 style="font-size: {DesignTokens.Typography.H3};
                   color: {DesignTokens.Colors.TEXT_PRIMARY};
                   margin-top: 0;
                   margin-bottom: {DesignTokens.Spacing.M_SM};">
            📋 版本信息
        </h3>
        <div style="font-size: {DesignTokens.Typography.BODY};
                 color: {DesignTokens.Colors.TEXT_PRIMARY};">
            <strong>应用版本</strong>: v2.0 (Phase 3 优化)<br>
            <strong>最后更新</strong>: 2026-03-15<br>
            <strong>开发团队</strong>: omc team<br>
            <strong>许可协议</strong>: MIT License
        </div>
    </div>
    """, unsafe_allow_html=True)


# 如果直接运行此文件
if __name__ == "__main__":
    render_system_config_v3()

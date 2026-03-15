"""
全局样式系统

基于Design Tokens的统一CSS样式，用于Streamlit应用程序。

用途：提供全局样式、组件样式和实用工具类
"""

import streamlit as st
from .design_tokens import DesignTokens, rgba, get_army_color


def get_global_styles() -> str:
    """
    获取全局CSS样式

    返回完整的CSS字符串，包含：
    - 全局样式重置
    - 卡片样式
    - 按钮样式
    - 输入框样式
    - 实用工具类
    """

    return f"""
    <style>
    /* ========== 全局样式重置 ========== */

    /* 字体设置 */
    .css-1d391kg {{
        font-family: {DesignTokens.Typography.FONT_FAMILY};
    }}

    /* 隐藏Streamlit默认的菜单和页脚 */
    .css-18ni7ap {{
        visibility: hidden;
    }}

    .css-1lcbmhc {{
        visibility: hidden;
    }}

    /* ========== 卡片样式 ========== */

    .stCard {{
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        box-shadow: {DesignTokens.Shadow.SM};
        padding: {DesignTokens.Spacing.CARD_PADDING};
        border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT};
        transition: {DesignTokens.Animation.TRANSITION_NORMAL};
        margin-bottom: {DesignTokens.Spacing.M_MD};
    }}

    .stCard:hover {{
        box-shadow: {DesignTokens.Shadow.MD};
        border-color: {rgba(DesignTokens.Colors.PRIMARY, 0.3)};
    }}

    /* 主卡片（强调） */
    .card-primary {{
        background: linear-gradient(135deg, {DesignTokens.Colors.PRIMARY} 0%, {DesignTokens.Colors.PRIMARY_DARK} 100%);
        color: {DesignTokens.Colors.TEXT_CONTRAST};
    }}

    /* 成功卡片 */
    .card-success {{
        border-left: 4px solid {DesignTokens.Colors.SUCCESS};
        background: {rgba(DesignTokens.Colors.SUCCESS, 0.05)};
    }}

    /* 警告卡片 */
    .card-warning {{
        border-left: 4px solid {DesignTokens.Colors.WARNING};
        background: {rgba(DesignTokens.Colors.WARNING, 0.05)};
    }}

    /* 错误卡片 */
    .card-error {{
        border-left: 4px solid {DesignTokens.Colors.ERROR};
        background: {rgba(DesignTokens.Colors.ERROR, 0.05)};
    }}

    /* ========== 按钮样式 ========== */

    /* 主按钮 */
    .stButton > button {{
        background: {DesignTokens.Colors.PRIMARY};
        color: {DesignTokens.Colors.TEXT_CONTRAST};
        border-radius: {DesignTokens.Radius.MD};
        border: none;
        padding: {DesignTokens.Spacing.P_SM} {DesignTokens.Spacing.P_MD};
        font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};
        transition: {DesignTokens.Animation.TRANSITION_FAST};
        box-shadow: {DesignTokens.Shadow.XS};
    }}

    .stButton > button:hover {{
        background: {DesignTokens.Colors.PRIMARY_DARK};
        box-shadow: {DesignTokens.Shadow.SM};
        transform: translateY(-1px);
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    /* 次要按钮 */
    .stButton > button[kind="secondary"] {{
        background: {DesignTokens.Colors.WHITE};
        color: {DesignTokens.Colors.PRIMARY};
        border: 1px solid {DesignTokens.Colors.PRIMARY};
    }}

    .stButton > button[kind="secondary"]:hover {{
        background: {rgba(DesignTokens.Colors.PRIMARY, 0.05)};
    }}

    /* ========== 输入框样式 ========== */

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        border-radius: {DesignTokens.Radius.MD};
        border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT};
        padding: {DesignTokens.Spacing.P_SM};
        transition: {DesignTokens.Animation.TRANSITION_FAST};
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: {DesignTokens.Colors.BORDER_FOCUS};
        box-shadow: 0 0 0 3px {rgba(DesignTokens.Colors.PRIMARY, 0.1)};
        outline: none;
    }}

    /* ========== 指标卡片样式 ========== */

    .metric-card {{
        background: {DesignTokens.Colors.BG_CARD};
        border-radius: {DesignTokens.Radius.LG};
        padding: {DesignTokens.Spacing.P_MD};
        box-shadow: {DesignTokens.Shadow.SM};
        text-align: center;
        border: 1px solid {DesignTokens.Colors.BORDER_DEFAULT};
        transition: {DesignTokens.Animation.TRANSITION_NORMAL};
    }}

    .metric-card:hover {{
        box-shadow: {DesignTokens.Shadow.MD};
        transform: translateY(-2px);
    }}

    .metric-value {{
        font-size: {DesignTokens.Typography.H3};
        font-weight: {DesignTokens.Typography.WEIGHT_BOLD};
        color: {DesignTokens.Colors.PRIMARY};
        margin: {DesignTokens.Spacing.M_SM} 0;
    }}

    .metric-label {{
        font-size: {DesignTokens.Typography.SMALL};
        color: {DesignTokens.Colors.TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* ========== 状态徽章样式 ========== */

    .status-badge {{
        display: inline-block;
        padding: {DesignTokens.Spacing.P_XS} {DesignTokens.Spacing.P_SM};
        border-radius: {DesignTokens.Radius.FULL};
        font-size: {DesignTokens.Typography.XSMALL};
        font-weight: {DesignTokens.Typography.WEIGHT_MEDIUM};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .status-success {{
        background: {rgba(DesignTokens.Colors.SUCCESS, 0.1)};
        color: {DesignTokens.Colors.SUCCESS};
    }}

    .status-warning {{
        background: {rgba(DesignTokens.Colors.WARNING, 0.1)};
        color: {DesignTokens.Colors.WARNING};
    }}

    .status-error {{
        background: {rgba(DesignTokens.Colors.ERROR, 0.1)};
        color: {DesignTokens.Colors.ERROR};
    }}

    .status-info {{
        background: {rgba(DesignTokens.Colors.INFO, 0.1)};
        color: {DesignTokens.Colors.INFO};
    }}

    /* ========== 军团主题样式 ========== */

    .army-hotspot {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_HOTSPOT};
    }}

    .army-industry {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_INDUSTRY};
    }}

    .army-stock {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_STOCK};
    }}

    .army-target {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_TARGET};
    }}

    .army-strategy {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_STRATEGY};
    }}

    .army-validation {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_VALIDATION};
    }}

    .army-strategic {{
        border-left: 4px solid {DesignTokens.Colors.ARMY_STRATEGIC};
    }}

    /* ========== 实用工具类 ========== */

    /* 文本对齐 */
    .text-left {{ text-align: left; }}
    .text-center {{ text-align: center; }}
    .text-right {{ text-align: right; }}

    /* 文本颜色 */
    .text-primary {{ color: {DesignTokens.Colors.TEXT_PRIMARY}; }}
    .text-secondary {{ color: {DesignTokens.Colors.TEXT_SECONDARY}; }}
    .text-muted {{ color: {DesignTokens.Colors.TEXT_HINT}; }}

    /* 间距 */
    .mt-xs {{ margin-top: {DesignTokens.Spacing.M_XS}; }}
    .mt-sm {{ margin-top: {DesignTokens.Spacing.M_SM}; }}
    .mt-md {{ margin-top: {DesignTokens.Spacing.M_MD}; }}
    .mt-lg {{ margin-top: {DesignTokens.Spacing.M_LG}; }}
    .mt-xl {{ margin-top: {DesignTokens.Spacing.M_XL}; }}

    .mb-xs {{ margin-bottom: {DesignTokens.Spacing.M_XS}; }}
    .mb-sm {{ margin-bottom: {DesignTokens.Spacing.M_SM}; }}
    .mb-md {{ margin-bottom: {DesignTokens.Spacing.M_MD}; }}
    .mb-lg {{ margin-bottom: {DesignTokens.Spacing.M_LG}; }}
    .mb-xl {{ margin-bottom: {DesignTokens.Spacing.M_XL}; }}

    /* 显示/隐藏 */
    .hidden {{ display: none !important; }}
    .visible {{ display: block !important; }}

    /* ========== 自定义滚动条 ========== */

    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {DesignTokens.Colors.GRAY_100};
        border-radius: {DesignTokens.Radius.SM};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {DesignTokens.Colors.GRAY_400};
        border-radius: {DesignTokens.Radius.SM};
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {DesignTokens.Colors.GRAY_500};
    }}

    /* ========== 动画效果 ========== */

    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    @keyframes slideInFromTop {{
        from {{
            transform: translateY(-20px);
            opacity: 0;
        }}
        to {{
            transform: translateY(0);
            opacity: 1;
        }}
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}

    .fade-in {{
        animation: fadeIn {DesignTokens.Animation.DURATION_NORMAL} {DesignTokens.Animation.EASING_DEFAULT};
    }}

    .slide-in {{
        animation: slideInFromTop {DesignTokens.Animation.DURATION_NORMAL} {DesignTokens.Animation.EASING_DEFAULT};
    }}

    .pulse {{
        animation: pulse 2s {DesignTokens.Animation.EASING_DEFAULT} infinite;
    }}

    /* ========== 响应式设计 ========== */

    @media (max-width: {DesignTokens.Layout.BREAKPOINT_MD}) {{
        .stCard {{
            padding: {DesignTokens.Spacing.P_MD};
        }}

        .metric-value {{
            font-size: {DesignTokens.Typography.H4};
        }}
    }}
    </style>
    """


def apply_global_styles():
    """应用全局样式到Streamlit应用"""
    st.markdown(get_global_styles(), unsafe_allow_html=True)


def get_custom_css(custom_rules: str) -> str:
    """
    获取自定义CSS规则

    Args:
        custom_rules: 自定义CSS规则字符串

    Returns:
        完整的style标签字符串
    """
    return f"""
    <style>
    {custom_rules}
    </style>
    """


def apply_custom_css(custom_rules: str):
    """
    应用自定义CSS规则

    Args:
        custom_rules: 自定义CSS规则字符串
    """
    st.markdown(get_custom_css(custom_rules), unsafe_allow_html=True)


# 便捷函数：创建带样式的容器
def styled_container(css_class: str, content: str):
    """
    创建带自定义CSS类的容器

    Args:
        css_class: CSS类名
        content: HTML内容
    """
    st.markdown(
        f"""
        <div class="{css_class}">
            {content}
        </div>
        """,
        unsafe_allow_html=True
    )


# 便捷函数：创建带样式的文本
def styled_text(text: str, css_class: str = ""):
    """
    创建带自定义样式的文本

    Args:
        text: 文本内容
        css_class: CSS类名（可选）
    """
    class_attr = f' class="{css_class}"' if css_class else ""
    st.markdown(
        f'<span{class_attr}>{text}</span>',
        unsafe_allow_html=True
    )


# 示例：在Streamlit应用中使用
if __name__ == "__main__":
    # 应用全局样式
    apply_global_styles()

    # 使用自定义样式
    styled_text("这是一段重要文本", "text-primary font-weight-bold")

    # 应用额外的CSS规则
    apply_custom_css("""
    .my-custom-class {
        background: #f0f0f0;
        padding: 16px;
        border-radius: 8px;
    }
    """)

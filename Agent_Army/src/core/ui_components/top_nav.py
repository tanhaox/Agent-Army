"""
顶部导航组件 - Agent Army v2.0

实现固定顶部导航，替代侧边栏导航
- 固定在页面顶部
- 全宽内容区域
- URL 参数控制页面切换
- 移动端友好
"""

import streamlit as st
from typing import Optional


def render_top_nav() -> str:
    """
    渲染顶部导航栏

    Returns:
        str: 当前页面标识 (home/analysis/monitor/settings)
    """

    # ========== 自定义 CSS 样式 ==========
    st.markdown("""
    <style>
    /* 隐藏默认侧边栏 */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* 隐藏 Streamlit 默认的菜单和页脚 */
    [data-testid="stToolbar"] {
        display: none;
    }

    /* 顶部导航栏样式 */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: linear-gradient(90deg, #1E88E5 0%, #43A047 100%);
        display: flex;
        align-items: center;
        padding: 0 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 999;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .top-nav .logo {
        font-size: 20px;
        font-weight: bold;
        color: white;
        margin-right: 50px;
        white-space: nowrap;
    }

    .top-nav .nav-item {
        color: white;
        text-decoration: none;
        padding: 10px 20px;
        margin: 0 5px;
        border-radius: 5px;
        transition: background 0.3s;
        font-size: 16px;
        display: inline-block;
    }

    .top-nav .nav-item:hover {
        background: rgba(255,255,255,0.2);
        text-decoration: none;
    }

    .top-nav .nav-item.active {
        background: rgba(255,255,255,0.3);
        font-weight: bold;
    }

    /* 内容区域 padding（为固定顶部导航留出空间）*/
    .main-content {
        padding-top: 80px;
        padding-left: 20px;
        padding-right: 20px;
    }

    /* 移动端适配 */
    @media (max-width: 768px) {
        .top-nav {
            padding: 0 10px;
        }

        .top-nav .logo {
            font-size: 16px;
            margin-right: 20px;
        }

        .top-nav .nav-item {
            padding: 8px 12px;
            font-size: 14px;
            margin: 0 2px;
        }

        .main-content {
            padding-top: 70px;
            padding-left: 10px;
            padding-right: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # ========== 获取当前页面 ==========
    query_params = st.query_params
    current_page = query_params.get("page", ["home"])[0]

    # 允许的页面列表
    valid_pages = ["home", "analysis", "monitor", "settings"]

    # 验证页面参数，如果无效则使用默认值
    if current_page not in valid_pages:
        current_page = "home"

    # ========== 设置激活状态 ==========
    active_states = {
        "home": "active" if current_page == "home" else "",
        "analysis": "active" if current_page == "analysis" else "",
        "monitor": "active" if current_page == "monitor" else "",
        "settings": "active" if current_page == "settings" else ""
    }

    # ========== 顶部导航 HTML ==========
    nav_html = f"""
    <div class="top-nav">
        <div class="logo">🎖️ Agent Army</div>
        <a href="?page=home" class="nav-item {active_states['home']}">🏠 首页</a>
        <a href="?page=analysis" class="nav-item {active_states['analysis']}">📊 投资分析</a>
        <a href="?page=monitor" class="nav-item {active_states['monitor']}">🤖 系统监控</a>
        <a href="?page=settings" class="nav-item {active_states['settings']}">⚙️ 系统配置</a>
    </div>
    """

    st.markdown(nav_html, unsafe_allow_html=True)

    # ========== 开始主内容区域 ==========
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    return current_page


def close_main_content():
    """闭合主内容区域的 div 标签"""
    st.markdown("</div>", unsafe_allow_html=True)

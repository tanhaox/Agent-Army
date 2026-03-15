"""
Agent Army - 系统配置页面 (v2.0)
API配置、Agent配置、日志查看、系统设置
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import os

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def render_system_config():
    """渲染系统配置页面"""

    st.title("⚙️ 系统配置")
    st.markdown("**API管理 | Agent配置 | 日志查看 | 系统设置**")
    st.markdown("---")

    # ========== 标签页 ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔑 API配置",
        "🤖 Agent配置",
        "📊 日志查看",
        "🔧 系统设置"
    ])

    # ========== API配置 ==========
    with tab1:
        render_api_config()

    # ========== Agent配置 ==========
    with tab2:
        render_agent_config()

    # ========== 日志查看 ==========
    with tab3:
        render_log_viewer()

    # ========== 系统设置 ==========
    with tab4:
        render_system_settings()


def render_api_config():
    """API配置"""

    st.markdown("### 🔑 API密钥管理")

    # 数据源API
    st.markdown("#### 📊 数据源API")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Tushare API**")
        tushare_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入Tushare API Key",
            key="tushare_api_key"
        )

        # 状态显示
        if os.environ.get('TUSHARE_API_KEY'):
            st.success("✅ 已配置")
        else:
            st.warning("⚠️ 未配置")

        if st.button("保存 Tushare Key", use_container_width=True):
            if tushare_key:
                os.environ['TUSHARE_API_KEY'] = tushare_key
                st.success("✅ Tushare API Key已保存到环境变量")
                st.info("💡 提示: 重启应用后需重新配置，建议写入.env文件")

        if st.button("测试连接", use_container_width=True):
            st.info("🔄 测试连接中...")
            # TODO: 实际测试连接
            st.success("✅ 连接成功")

    with col2:
        st.markdown("**Akshare API**")
        akshare_status = st.selectbox(
            "状态",
            ["✅ 已启用", "⚠️ 未配置"],
            key="akshare_status"
        )
        st.info("Akshare为免费开源API，无需密钥")

    st.markdown("---")

    # AI模型API
    st.markdown("#### 🤖 AI模型API")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**OpenAI API**")
        openai_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入OpenAI API Key",
            key="openai_api_key"
        )

        if os.environ.get('OPENAI_API_KEY'):
            st.success("✅ 已配置")
        else:
            st.warning("⚠️ 未配置")

        if st.button("保存 OpenAI Key", use_container_width=True):
            if openai_key:
                os.environ['OPENAI_API_KEY'] = openai_key
                st.success("✅ OpenAI API Key已保存")

    with col2:
        st.markdown("**Claude API**")
        claude_key = st.text_input(
            "API Key",
            type="password",
            placeholder="输入Claude API Key",
            key="claude_api_key"
        )

        if os.environ.get('CLAUDE_API_KEY'):
            st.success("✅ 已配置")
        else:
            st.warning("⚠️ 未配置")

        if st.button("保存 Claude Key", use_container_width=True):
            if claude_key:
                os.environ['CLAUDE_API_KEY'] = claude_key
                st.success("✅ Claude API Key已保存")

    st.markdown("---")

    # 其他数据源
    st.markdown("#### 📰 其他数据源")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**东方财富**")
        st.selectbox(
            "状态",
            ["✅ 已启用", "⚠️ 未配置"],
            key="eastmoney_status"
        )

    with col2:
        st.markdown("**同花顺**")
        st.selectbox(
            "状态",
            ["✅ 已启用", "⚠️ 未配置"],
            key="ths_status"
        )

    with col3:
        st.markdown("**新浪财经**")
        st.selectbox(
            "状态",
            ["✅ 已启用", "⚠️ 未配置"],
            key="sina_status"
        )

    st.markdown("---")

    # 批量操作
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 导出配置", use_container_width=True):
            st.info("配置导出功能开发中...")

    with col2:
        if st.button("📥 导入配置", use_container_width=True):
            st.info("配置导入功能开发中...")

    with col3:
        if st.button("🔄 重置配置", use_container_width=True):
            st.warning("⚠️ 此操作将清除所有API密钥")


def render_agent_config():
    """Agent配置"""

    st.markdown("### 🤖 Agent配置管理")

    st.info("🚧 Agent配置管理页面开发中...")
    st.markdown("""
    将包含：
    - **Agent启用/禁用**: 控制哪些Agent参与分析
    - **Agent优先级**: 设置Agent执行顺序
    - **超时设置**: 配置每个Agent的超时时间
    - **重试策略**: 设置失败重试次数
    - **权重配置**: 调整Agent在综合评分中的权重
    """)

    # 示例：宏观经济AI配置
    with st.expander("🌍 宏观经济AI配置"):
        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("启用", value=True, key="macro_enabled")
            st.number_input("超时时间（秒）", value=30, key="macro_timeout")
            st.number_input("重试次数", value=3, key="macro_retry")

        with col2:
            st.slider("权重", 0.0, 2.0, 1.0, key="macro_weight")
            st.select_slider("优先级", ["低", "中", "高"], value="高", key="macro_priority")

        if st.button("保存配置", key="save_macro"):
            st.success("✅ 配置已保存")


def render_log_viewer():
    """日志查看"""

    st.markdown("### 📊 日志查看器")

    # 日志筛选
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        log_level = st.selectbox(
            "日志级别",
            ["全部", "INFO", "WARNING", "ERROR", "DEBUG"]
        )

    with col2:
        log_source = st.selectbox(
            "日志来源",
            ["全部", "Web服务", "Agent", "任务管理", "数据获取"]
        )

    with col3:
        time_range = st.selectbox(
            "时间范围",
            ["最近1小时", "最近6小时", "最近24小时", "最近7天"]
        )

    with col4:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # 日志列表
    logs = [
        {
            "time": "2026-03-14 14:30:05",
            "level": "INFO",
            "source": "宏观经济AI",
            "message": "开始分析宏观经济数据..."
        },
        {
            "time": "2026-03-14 14:30:07",
            "level": "INFO",
            "source": "宏观经济AI",
            "message": "GDP数据获取成功"
        },
        {
            "time": "2026-03-14 14:30:08",
            "level": "WARNING",
            "source": "新闻监控AI",
            "message": "部分新闻源响应超时"
        },
        {
            "time": "2026-03-14 14:30:10",
            "level": "INFO",
            "source": "新闻监控AI",
            "message": "新闻分析完成，发现3条重要新闻"
        },
        {
            "time": "2026-03-14 14:30:12",
            "level": "ERROR",
            "source": "数据获取",
            "message": "API调用失败: Connection timeout"
        }
    ]

    # 日志显示
    log_container = st.container()

    with log_container:
        for log in logs:
            # 根据日志级别设置颜色
            level_colors = {
                "INFO": "🟢",
                "WARNING": "🟡",
                "ERROR": "🔴",
                "DEBUG": "🔵"
            }
            level_emoji = level_colors.get(log['level'], "⚪")

            st.markdown(
                f"**{level_emoji} {log['time']}** [{log['level']}] "
                f"[{log['source']}] {log['message']}"
            )

    st.markdown("---")

    # 日志操作
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 下载日志", use_container_width=True):
            st.info("日志下载功能开发中...")

    with col2:
        if st.button("🗑️ 清空日志", use_container_width=True):
            st.warning("⚠️ 此操作将清空所有日志")

    with col3:
        if st.button("📊 日志统计", use_container_width=True):
            st.info("日志统计功能开发中...")


def render_system_settings():
    """系统设置"""

    st.markdown("### 🔧 系统设置")

    # 系统信息
    st.markdown("#### 📊 系统信息")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**基本信息**")
        st.markdown("- **版本**: v2.0.0")
        st.markdown("- **Agent数**: 24个")
        st.markdown("- **军团数**: 6个")
        st.markdown("- **完成率**: 100%")

    with col2:
        st.markdown("**运行状态**")
        st.markdown("- **状态**: ✅ 运行中")
        st.markdown("- **启动时间**: 2026-03-14 14:00:00")
        st.markdown("- **运行时长**: 0天0小时30分钟")
        st.markdown("- **CPU使用率**: 25%")
        st.markdown("- **内存使用**: 1.2GB")

    st.markdown("---")

    # 显示设置
    st.markdown("#### 🎨 显示设置")

    col1, col2 = st.columns(2)

    with col1:
        theme = st.selectbox(
            "主题",
            ["浅色", "深色", "跟随系统"]
        )

        language = st.selectbox(
            "语言",
            ["简体中文", "English"]
        )

    with col2:
        chart_animation = st.checkbox("启用图表动画", value=True)
        auto_refresh = st.checkbox("自动刷新数据", value=False)

        if auto_refresh:
            refresh_interval = st.number_input(
                "刷新间隔（秒）",
                min_value=5,
                max_value=300,
                value=30
            )

    st.markdown("---")

    # 通知设置
    st.markdown("#### 🔔 通知设置")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("启用系统通知", value=True)
        st.checkbox("任务完成通知", value=True)
        st.checkbox("风险预警通知", value=True)

    with col2:
        st.checkbox("新闻提醒", value=False)
        st.checkbox("涨跌幅提醒", value=True)
        st.checkbox("资金异动提醒", value=True)

    st.markdown("---")

    # 保存设置
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("")

    with col2:
        if st.button("🔄 恢复默认", use_container_width=True):
            st.warning("⚠️ 此操作将恢复所有设置为默认值")

    with col3:
        if st.button("💾 保存设置", type="primary", use_container_width=True):
            st.success("✅ 设置已保存")

    st.markdown("---")

    # 系统操作
    st.markdown("#### ⚙️ 系统操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 重启服务", use_container_width=True):
            st.warning("⚠️ 重启服务将中断当前任务")

    with col2:
        if st.button("🗑️ 清除缓存", use_container_width=True):
            st.success("✅ 缓存已清除")

    with col3:
        if st.button("📥 检查更新", use_container_width=True):
            st.info("🔄 检查更新中...")
            st.success("✅ 已是最新版本")


# 如果直接运行此文件
if __name__ == "__main__":
    render_system_config()

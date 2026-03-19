"""
UI组件库演示脚本

运行方式:
    streamlit run demo_ui_components.py

功能:
    演示所有可复用的UI组件
"""

import streamlit as st
from src.core.ui_components import (
    create_gradient_banner,
    create_metric_card,
    create_info_card,
    create_agent_workstation_card,
    get_status_badge,
    get_tool_tag
)

# 页面配置
st.set_page_config(
    page_title="🎨 UI组件库演示",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("🎨 Agent Army - UI组件库演示")

st.markdown("""
本页面展示所有可复用的UI组件，这些组件用于前端重构。

**设计师**: OMC Team Designer
**版本**: v1.0
**完成日期**: 2026-03-14
""")

st.markdown("---")

# ========== 1. 渐变横幅 ==========
st.markdown("## 1. 渐变横幅组件")
st.markdown("`create_gradient_banner()` - 用于页面顶部欢迎横幅")

create_gradient_banner(
    title="🎖️ Agent Army",
    subtitle="股票价值投资AI军团 - Phase 3 性能优化版本"
)

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import create_gradient_banner

create_gradient_banner(
    title="🎖️ Agent Army",
    subtitle="股票价值投资AI军团 - Phase 3 性能优化版本"
)
    """, language="python")

st.markdown("---")

# ========== 2. 指标卡片 ==========
st.markdown("## 2. 指标卡片组件")
st.markdown("`create_metric_card()` - 用于展示关键性能指标")

col1, col2, col3, col4 = st.columns(4)

with col1:
    create_metric_card(
        title="并发性能提升",
        value="4.76倍",
        delta="+376%",
        description="多Agent并发分析",
        icon="🚀",
        color="success"
    )

with col2:
    create_metric_card(
        title="缓存命中率",
        value="50-80%",
        description="减少API调用",
        icon="💾",
        color="info"
    )

with col3:
    create_metric_card(
        title="API节流控制",
        value="运行中",
        description="避免限流风险",
        icon="⚡",
        color="warning"
    )

with col4:
    create_metric_card(
        title="后台监控",
        value="运行中",
        description="自动清理过期缓存",
        icon="👁️",
        color="success"
    )

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import create_metric_card

create_metric_card(
    title="并发性能提升",
    value="4.76倍",
    delta="+376%",
    description="多Agent并发分析",
    icon="🚀",
    color="success"  # primary/success/warning/error/info
)
    """, language="python")

st.markdown("---")

# ========== 3. 状态徽章 ==========
st.markdown("## 3. 状态徽章组件")
st.markdown("`get_status_badge()` - 用于显示Agent/任务状态")

st.markdown("### 示例徽章")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(get_status_badge("运行中"), unsafe_allow_html=True)

with col2:
    st.markdown(get_status_badge("空闲"), unsafe_allow_html=True)

with col3:
    st.markdown(get_status_badge("异常"), unsafe_allow_html=True)

with col4:
    st.markdown(get_status_badge("已完成"), unsafe_allow_html=True)

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import get_status_badge

badge_html = get_status_badge("运行中")  # 运行中/空闲/异常/已完成/待执行/已停止
st.markdown(badge_html, unsafe_allow_html=True)
    """, language="python")

st.markdown("---")

# ========== 4. 工具标签 ==========
st.markdown("## 4. 工具标签组件")
st.markdown("`get_tool_tag()` - 用于显示工具标签")

st.markdown("### 示例标签")
tools_html = " ".join([
    get_tool_tag("FinancialTool"),
    get_tool_tag("LLMTool"),
    get_tool_tag("NewsTool"),
    get_tool_tag("NLPTool")
])
st.markdown(tools_html, unsafe_allow_html=True)

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import get_tool_tag

tag_html = get_tool_tag("FinancialTool")
st.markdown(tag_html, unsafe_allow_html=True)
    """, language="python")

st.markdown("---")

# ========== 5. 信息卡片 ==========
st.markdown("## 5. 信息卡片组件")
st.markdown("`create_info_card()` - 用于展示提示信息")

col1, col2 = st.columns(2)

with col1:
    create_info_card(
        title="系统提示",
        content="这是一个现代化的UI组件库，支持多种组件类型，可用于前端重构。",
        icon="💡",
        color="info"
    )

with col2:
    create_info_card(
        title="成功提示",
        content="所有组件已成功加载并可以使用！Phase 3性能优化成果显著。",
        icon="✅",
        color="success"
    )

col1, col2 = st.columns(2)

with col1:
    create_info_card(
        title="警告提示",
        content="API调用频率接近限制，建议启用缓存机制。",
        icon="⚠️",
        color="warning"
    )

with col2:
    create_info_card(
        title="错误提示",
        content="API密钥配置错误，请检查配置文件。",
        icon="❌",
        color="error"
    )

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import create_info_card

create_info_card(
    title="系统提示",
    content="这是一个现代化的UI组件库...",
    icon="💡",
    color="info"  # info/success/warning/error
)
    """, language="python")

st.markdown("---")

# ========== 6. Agent工作站 ==========
st.markdown("## 6. Agent工作站组件")
st.markdown("`create_agent_workstation_card()` - 用于展示Agent工作状态和日志")

create_agent_workstation_card(
    agent_name="产业链分析AI",
    agent_role="分析产业链上下游关系",
    status="运行中",
    progress=65,
    tools=["FinancialTool", "LLMTool"],
    logs=[
        {"time": "09:23:15", "level": "INFO", "message": "正在查询产业链数据..."},
        {"time": "09:23:16", "level": "SUCCESS", "message": "✅ 产业链数据获取成功"},
        {"time": "09:23:17", "level": "INFO", "message": "正在分析上下游关系..."},
        {"time": "09:23:18", "level": "INFO", "message": "识别上游企业 8家"},
        {"time": "09:23:19", "level": "INFO", "message": "识别下游企业 7家"},
        {"time": "09:23:20", "level": "SUCCESS", "message": "✅ 产业链分析完成"},
    ],
    elapsed_time="12.5秒"
)

with st.expander("📋 查看代码", expanded=False):
    st.code("""
from src.core.ui_components import create_agent_workstation_card

create_agent_workstation_card(
    agent_name="产业链分析AI",
    agent_role="分析产业链上下游关系",
    status="运行中",
    progress=65,
    tools=["FinancialTool", "LLMTool"],
    logs=[
        {"time": "09:23:15", "level": "INFO", "message": "正在查询产业链数据..."},
        {"time": "09:23:16", "level": "SUCCESS", "message": "✅ 产业链数据获取成功"},
        ...
    ],
    elapsed_time="12.5秒"
)
    """, language="python")

st.markdown("---")

# ========== 7. 组合使用示例 ==========
st.markdown("## 7. 组合使用示例")
st.markdown("展示如何组合使用多个组件")

create_gradient_banner(
    title="📊 投资分析仪表盘",
    subtitle="实时监控投资分析进度"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    create_metric_card(
        title="已分析股票",
        value="156",
        delta="+12",
        icon="📈",
        color="primary"
    )

with col2:
    create_metric_card(
        title="成功率",
        value="98.5%",
        icon="✅",
        color="success"
    )

with col3:
    create_metric_card(
        title="平均耗时",
        value="15.3秒",
        icon="⏱️",
        color="info"
    )

with col4:
    create_metric_card(
        title="缓存命中",
        value="72%",
        icon="💾",
        color="success"
    )

st.markdown("---")

create_agent_workstation_card(
    agent_name="基本面分析AI",
    agent_role="分析股票基本面情况",
    status="运行中",
    progress=80,
    tools=["FinancialTool", "FormulaTool"],
    logs=[
        {"time": "09:30:15", "level": "INFO", "message": "正在获取财务数据..."},
        {"time": "09:30:16", "level": "SUCCESS", "message": "✅ 财务数据获取成功"},
        {"time": "09:30:17", "level": "INFO", "message": "正在计算ROE..."},
        {"time": "09:30:18", "level": "INFO", "message": "正在计算PE..."},
        {"time": "09:30:19", "level": "INFO", "message": "正在生成分析报告..."},
    ],
    elapsed_time="8.2秒"
)

st.markdown("---")

# ========== 总结 ==========
st.markdown("## 📝 总结")

st.success("""
**UI组件库已全部演示完成！**

包含7个可复用组件：
1. ✅ 渐变横幅组件 - `create_gradient_banner()`
2. ✅ 指标卡片组件 - `create_metric_card()`
3. ✅ 状态徽章组件 - `get_status_badge()`
4. ✅ 工具标签组件 - `get_tool_tag()`
5. ✅ 信息卡片组件 - `create_info_card()`
6. ✅ Agent工作站组件 - `create_agent_workstation_card()`
7. ✅ 实时日志查看器 - `create_live_log_viewer()`（在Agent工作站中使用）

**使用场景**：
- 主页：性能监控仪表盘
- Agent状态页：Agent详情卡片
- 任务管理页：Agent工作站
- 报告查看页：报告展示卡片
- 系统配置页：配置提示卡片

**设计原则**：
- 模块化：每个组件独立封装
- 可复用：所有页面共享
- 现代化：渐变、卡片、阴影、圆角
- 统一性：遵循设计系统（色彩、字体、间距）
""")

st.markdown("---")

st.markdown("""
**设计师**: OMC Team Designer
**完成日期**: 2026-03-14
**版本**: v1.0
**文档**: [frontend_design_plan.md](docs/frontend_design_plan.md)
""")

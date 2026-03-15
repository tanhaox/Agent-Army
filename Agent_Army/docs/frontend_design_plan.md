# 前端设计升级方案

**创建日期**: 2026-03-14
**设计师**: OMC Team Designer
**版本**: v1.0
**状态**: 设计中

---

## 📋 概述

本文档描述 Agent Army 项目前端页面的全面升级重构方案，目标是将现有的基础 Streamlit 界面升级为现代化、高性能、用户友好的专业级前端。

---

## 🎯 设计目标

### 核心目标

1. **现代化视觉设计** ⭐⭐⭐⭐⭐
   - 引入现代设计语言（卡片式布局、阴影、圆角、渐变）
   - 统一的色彩系统和设计规范
   - 专业级的视觉层次

2. **性能监控可视化** ⭐⭐⭐⭐⭐
   - Phase 3 性能提升数据可视化（4.76倍并发提升）
   - 实时缓存命中率监控
   - API 调用节流状态展示
   - 后台监控线程状态

3. **Agent 工作站增强** ⭐⭐⭐⭐
   - 每个Agent独立工位展示
   - 实时工作日志（流式输出）
   - 工作进度可视化
   - 中间结果展示

4. **用户体验优化** ⭐⭐⭐⭐
   - 响应式布局（支持移动端）
   - 平滑动画过渡
   - 实时反馈机制
   - 智能导航

---

## 📊 当前问题分析

### 1. 视觉设计问题

| 问题 | 当前状态 | 影响 |
|------|---------|------|
| **UI风格过时** | Streamlit原生组件，缺乏设计感 | 专业性不足 |
| **色彩单调** | 主要使用默认颜色，缺少品牌色 | 视觉识别度低 |
| **信息密度低** | 大量垂直堆叠，空间利用率低 | 信息查找慢 |
| **缺少视觉层次** | 所有内容平铺，重点不突出 | 用户注意力分散 |

### 2. 功能展示问题

| 问题 | 当前状态 | 影响 |
|------|---------|------|
| **性能数据缺失** | Phase 3成果没有可视化展示 | 无法直观看到优化效果 |
| **Agent状态简陋** | 简单的文本状态显示 | 缺少工作过程透明度 |
| **进度反馈粗糙** | 基础进度条，缺少细节 | 用户无法了解具体进展 |
| **报告展示简单** | 纯文本展示，无可视化 | 报告可读性差 |

### 3. 交互体验问题

| 问题 | 当前状态 | 影响 |
|------|---------|------|
| **导航混乱** | 侧边栏单层导航，无面包屑 | 用户容易迷失 |
| **无动画效果** | 页面跳转生硬 | 用户体验差 |
| **响应式缺失** | 仅适配桌面端 | 移动端不可用 |
| **反馈不及时** | 缺少操作反馈 | 用户不确定操作是否成功 |

---

## 🎨 设计系统

### 色彩系统

```python
# 主题色彩
PRIMARY_COLOR = "#1E88E5"      # 主色（蓝色）
SECONDARY_COLOR = "#43A047"    # 辅助色（绿色）
ACCENT_COLOR = "#FB8C00"       # 强调色（橙色）
ERROR_COLOR = "#E53935"        # 错误色（红色）
WARNING_COLOR = "#FDD835"      # 警告色（黄色）
INFO_COLOR = "#00ACC1"         # 信息色（青色）

# 背景色
BG_PRIMARY = "#FFFFFF"         # 主背景
BG_SECONDARY = "#F5F5F5"       # 次级背景
BG_CARD = "#FFFFFF"            # 卡片背景

# 文字色
TEXT_PRIMARY = "#212121"       # 主要文字
TEXT_SECONDARY = "#757575"     # 次要文字
TEXT_DISABLED = "#BDBDBD"      # 禁用文字
```

### 字体系统

```python
# 字体大小（基于Streamlit默认）
FONT_SIZE_H1 = "2.5rem"        # 主标题
FONT_SIZE_H2 = "2.0rem"        # 次标题
FONT_SIZE_H3 = "1.5rem"        # 三级标题
FONT_SIZE_BODY = "1.0rem"      # 正文
FONT_SIZE_CAPTION = "0.875rem" # 说明文字

# 字重
FONT_WEIGHT_LIGHT = 300
FONT_WEIGHT_REGULAR = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700
```

### 间距系统

```python
# 标准间距
SPACING_XS = "4px"
SPACING_SM = "8px"
SPACING_MD = "16px"
SPACING_LG = "24px"
SPACING_XL = "32px"
SPACING_XXL = "48px"
```

### 圆角系统

```python
# 圆角半径
RADIUS_SM = "4px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
RADIUS_ROUND = "50%"
```

---

## 🏗️ 页面重构方案

### 1. 主页（🏠 主页）

#### 当前问题
- 信息密度低
- Phase 3成果没有展示
- 缺少视觉冲击力

#### 重构方案

**布局结构**：
```
┌─────────────────────────────────────────────────┐
│  🎯 欢迎横幅（渐变背景 + 核心数据）               │
├─────────────────────────────────────────────────┤
│  📊 Phase 3 性能监控仪表盘                        │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │ 并发提升  │ 缓存命中  │ API节流  │ 监控线程 │ │
│  │ 4.76倍   │ 50-80%   │ 运行中   │ 运行中   │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────┤
│  📈 系统概览（卡片式布局）                        │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │ Agent数  │ 工具数   │ 报告数   │ 任务数   │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────┤
│  🏗️ 组织架构（可交互树状图）                      │
├─────────────────────────────────────────────────┤
│  🚀 快速开始（3步骤卡片）                         │
└─────────────────────────────────────────────────┘
```

**新增内容**：
1. **Phase 3 性能监控仪表盘** ⭐⭐⭐⭐⭐
   ```python
   # 性能指标卡片
   col1, col2, col3, col4 = st.columns(4)

   with col1:
       create_metric_card(
           title="并发性能提升",
           value="4.76倍",
           delta="+376%",
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
   ```

2. **欢迎横幅（渐变背景）**
   ```python
   st.markdown("""
   <div style="
       background: linear-gradient(135deg, #1E88E5 0%, #43A047 100%);
       padding: 2rem;
       border-radius: 12px;
       color: white;
       margin-bottom: 2rem;
   ">
       <h1>🎖️ Agent Army</h1>
       <p>股票价值投资AI军团 - Phase 3 性能优化版本</p>
   </div>
   """, unsafe_allow_html=True)
   ```

3. **组织架构（可交互）**
   ```python
   # 使用Streamlit-AgGrid或自定义组件
   # 支持展开/折叠
   # 支持点击查看Agent详情
   ```

---

### 2. Agent状态（🤖 Agent状态）

#### 当前问题
- 状态信息简陋
- 缺少工作过程展示
- 无实时更新

#### 重构方案

**布局结构**：
```
┌─────────────────────────────────────────────────┐
│  🔍 Agent搜索 + 筛选                             │
├─────────────────────────────────────────────────┤
│  📊 Agent统计概览                                │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │ 总Agent  │ 运行中   │ 空闲     │ 异常     │ │
│  │ 8       │ 2       │ 6       │ 0       │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────┤
│  👔 管理层Agent（卡片式）                         │
│  ┌─────────────────────┬─────────────────────┐ │
│  │ HR Agent            │ Commander Agent     │ │
│  │ [状态] [工具] [日志] │ [状态] [工具] [日志] │ │
│  └─────────────────────┴─────────────────────┘ │
├─────────────────────────────────────────────────┤
│  📊 业务层Agent（可折叠卡片组）                   │
│  ┌─────────────────────────────────────────┐   │
│  │ 📰 热点捕捉军团 (3/4)                    ▼ │   │
│  │   [Agent1] [Agent2] [Agent3]              │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ 🏗️ 产业分析军团 (1/4)                    ▼ │   │
│  │   [Agent1]                                │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**新增内容**：
1. **Agent搜索和筛选**
   ```python
   search_query = st.text_input("🔍 搜索Agent", placeholder="输入Agent名称或关键词")
   status_filter = st.multiselect("状态筛选", ["运行中", "空闲", "异常"])
   ```

2. **Agent详情卡片（增强）**
   ```python
   with st.expander(f"👔 {agent.name}", expanded=True):
       # 状态指示器（带颜色）
       col1, col2, col3 = st.columns([2, 2, 1])
       with col1:
           st.markdown(f"**状态**: {get_status_badge(agent.status)}")
       with col2:
           st.markdown(f"**完成任务**: {agent.completed_tasks}")
       with col3:
           if st.button("📊 详情", key=f"detail_{agent.id}"):
               show_agent_detail(agent)

       # 工具列表（标签式）
       st.markdown("**工具**:")
       for tool in agent.tools:
           st.markdown(get_tool_tag(tool))

       # 最近任务（时间线）
       st.markdown("**最近任务**:")
       for task in agent.recent_tasks[:5]:
           create_timeline_item(task)
   ```

3. **实时状态更新**
   ```python
   # 使用st.rerun()或自动刷新
   if st.checkbox("自动刷新", value=True):
       time.sleep(5)
       st.rerun()
   ```

---

### 3. 任务管理（📋 任务管理）

#### 当前问题
- Agent工作站展示粗糙
- 缺少实时进度反馈
- 日志展示不清晰

#### 重构方案

**布局结构**：
```
┌─────────────────────────────────────────────────┐
│  📝 任务输入区（增强）                            │
│  ┌─────────────────────────────────────────┐   │
│  │ 💬 智能任务助手                          │   │
│  │ 输入自然语言指令或股票代码               │   │
│  └─────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  🔄 Agent工作站（实时）                          │
│  ┌─────────────────────────────────────────┐   │
│  │ 🤖 Agent #1: 产业链分析AI               │   │
│  │ ┌───────┬─────────────────────────────┐ │   │
│  │ │ 状态  │ 📊 工作日志（流式输出）      │ │   │
│  │ │ 进度  │ ✅ 查询产业链数据...         │ │   │
│  │ │ 工具  │ ✅ 分析上下游关系...         │ │   │
│  │ │ 耗时  │ ⏳ 生成分析报告...           │ │   │
│  │ └───────┴─────────────────────────────┘ │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ 🤖 Agent #2: 基本面分析AI               │   │
│  │ [同上结构]                              │   │
│  └─────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  📊 Commander审核（实时）                        │
│  ┌─────────────────────────────────────────┐   │
│  │ 审核状态: ⏳ 进行中                      │   │
│  │ 审核轮次: 1/4                           │   │
│  │ 审核意见: 等待Agent提交报告...          │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**新增内容**：
1. **Agent工作站卡片（增强）** ⭐⭐⭐⭐⭐
   ```python
   def create_agent_workstation(agent_name, agent_role):
       """创建Agent工作站卡片"""

       with st.container():
           st.markdown(f"#### 🤖 {agent_name}")

           col1, col2 = st.columns([1, 3])

           with col1:
               # 左侧：状态面板
               create_status_panel(
                   status="运行中",
                   progress=65,
                   tools=["FinancialTool", "LLMTool"],
                   elapsed_time="12.5秒"
               )

           with col2:
               # 右侧：工作日志（流式输出）
               create_live_log_viewer(
                   logs=[
                       {"time": "09:23:15", "level": "INFO", "message": "正在查询财务数据..."},
                       {"time": "09:23:16", "level": "SUCCESS", "message": "✅ 财务数据获取成功"},
                       {"time": "09:23:17", "level": "INFO", "message": "正在分析基本面..."},
                   ],
                   auto_scroll=True
               )

               # 中间数据展示（可折叠）
               with st.expander("📊 中间数据"):
                   st.json({
                       "revenue": 10000000000,
                       "net_profit": 1000000000,
                       "roe": 15.2
                   })
   ```

2. **实时进度条（增强）**
   ```python
   # 使用st.progress + 状态文字
   progress_bar = st.progress(0)
   status_text = st.empty()

   for i in range(100):
       progress_bar.progress(i + 1)
       status_text.caption(f"正在执行... {i+1}%")
       time.sleep(0.1)
   ```

3. **Commander审核面板（新增）**
   ```python
   with st.expander("🎖️ Commander审核", expanded=True):
       col1, col2, col3 = st.columns(3)

       with col1:
           st.metric("审核状态", "进行中", delta="第1轮")
       with col2:
           st.metric("已用时间", "45秒")
       with col3:
           st.metric("审核结果", "等待中")

       # 审核意见（实时更新）
       st.markdown("**最新审核意见**:")
       st.info("等待Agent提交报告...")
   ```

---

### 4. 报告查看（📊 报告查看）

#### 当前问题
- 纯文本展示
- 无数据可视化
- 可读性差

#### 重构方案

**布局结构**：
```
┌─────────────────────────────────────────────────┐
│  🔍 报告搜索 + 筛选                              │
├─────────────────────────────────────────────────┤
│  📊 报告概览（卡片列表）                          │
│  ┌─────────────────────────────────────────┐   │
│  │ 📄 贵州茅台(600519) 分析报告             │   │
│  │ 2026-03-14 09:23 | 评分: 85 | 审核: ✅   │   │
│  │ [查看] [下载] [分享]                     │   │
│  └─────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  📈 报告详情（增强）                             │
│  ┌─────────────────────────────────────────┐   │
│  │ 📊 核心指标可视化                        │   │
│  │ [ROE趋势图] [营收增长图] [评分雷达图]   │   │
│  ├─────────────────────────────────────────┤   │
│  │ 📝 分析结论（Markdown渲染）              │   │
│  ├─────────────────────────────────────────┤   │
│  │ 🎯 投资建议（突出显示）                  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**新增内容**：
1. **报告可视化（Plotly图表）**
   ```python
   import plotly.graph_objects as go

   # ROE趋势图
   fig_roe = go.Figure()
   fig_roe.add_trace(go.Scatter(
       x=years,
       y=roe_values,
       mode='lines+markers',
       name='ROE',
       line=dict(color='#1E88E5', width=3)
   ))
   fig_roe.update_layout(
       title='ROE趋势',
       xaxis_title='年份',
       yaxis_title='ROE(%)',
       template='plotly_white'
   )
   st.plotly_chart(fig_roe, use_container_width=True)

   # 评分雷达图
   categories = ['基本面', '技术面', '资金面', '情绪面', '成长性']
   fig_radar = go.Figure(data=go.Scatterpolar(
       r=[85, 78, 90, 75, 88],
       theta=categories,
       fill='toself',
       line=dict(color='#1E88E5')
   ))
   st.plotly_chart(fig_radar, use_container_width=True)
   ```

2. **报告导出（PDF/Markdown）**
   ```python
   col1, col2 = st.columns(2)
   with col1:
       if st.button("📥 导出PDF"):
           export_to_pdf(report_data)
   with col2:
       if st.button("📥 导出Markdown"):
           export_to_markdown(report_data)
   ```

---

### 5. 系统配置（⚙️ 系统配置）

#### 当前问题
- 配置项分散
- 缺少配置验证
- 无配置历史

#### 重构方案

**新增内容**：
1. **配置验证和测试（增强）**
   ```python
   if st.button("🔍 测试连接"):
       with st.spinner("测试中..."):
           result = test_api_connection(api_key)
           if result.success:
               st.success("✅ 连接成功")
               st.metric("响应时间", f"{result.latency}ms")
               st.metric("配额剩余", result.quota_remaining)
           else:
               st.error(f"❌ 连接失败: {result.error}")
   ```

2. **配置历史（新增）**
   ```python
   with st.expander("📜 配置历史"):
       for record in config_history:
           st.markdown(f"""
           - **{record.time}**: {record.action}
             - 操作人: {record.user}
             - 变更: {record.changes}
           """)
   ```

---

## 🧩 可复用组件

### 1. 指标卡片组件

```python
def create_metric_card(title, value, delta=None, description=None, icon=None, color="primary"):
    """
    创建指标卡片

    Args:
        title: 标题
        value: 数值
        delta: 变化值（可选）
        description: 描述（可选）
        icon: 图标（可选）
        color: 颜色（primary/success/warning/error/info）
    """
    color_map = {
        "primary": "#1E88E5",
        "success": "#43A047",
        "warning": "#FB8C00",
        "error": "#E53935",
        "info": "#00ACC1"
    }

    card_html = f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid {color_map[color]};
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            {f'<span style="font-size: 2rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''}
            <span style="font-size: 0.875rem; color: #757575;">{title}</span>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: {color_map[color]};">
            {value}
        </div>
        {f'<div style="font-size: 0.875rem; color: #757575; margin-top: 0.5rem;">{description}</div>' if description else ''}
        {f'<div style="font-size: 0.875rem; color: #43A047; margin-top: 0.5rem;">{delta}</div>' if delta else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)
```

### 2. 状态徽章组件

```python
def get_status_badge(status):
    """获取状态徽章"""
    badges = {
        "运行中": '<span style="background: #E8F5E9; color: #43A047; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem;">● 运行中</span>',
        "空闲": '<span style="background: #E3F2FD; color: #1E88E5; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem;">● 空闲</span>',
        "异常": '<span style="background: #FFEBEE; color: #E53935; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem;">● 异常</span>',
        "已停止": '<span style="background: #F5F5F5; color: #757575; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem;">● 已停止</span>'
    }
    return badges.get(status, badges["空闲"])
```

### 3. 实时日志查看器

```python
def create_live_log_viewer(logs, auto_scroll=True, max_height=300):
    """
    创建实时日志查看器

    Args:
        logs: 日志列表 [{"time": "...", "level": "...", "message": "..."}]
        auto_scroll: 是否自动滚动到底部
        max_height: 最大高度（像素）
    """
    log_container = st.container()

    with log_container:
        log_html = f'<div style="background: #263238; color: #ECEFF1; padding: 1rem; border-radius: 8px; font-family: monospace; font-size: 0.875rem; max-height: {max_height}px; overflow-y: auto;">'

        for log in logs:
            level_colors = {
                "INFO": "#4FC3F7",
                "SUCCESS": "#66BB6A",
                "WARNING": "#FFD54F",
                "ERROR": "#EF5350"
            }
            color = level_colors.get(log["level"], "#ECEFF1")

            log_html += f'<div style="margin-bottom: 0.5rem;">'
            log_html += f'<span style="color: #757575;">{log["time"]}</span> '
            log_html += f'<span style="color: {color}; font-weight: 500;">[{log["level"]}]</span> '
            log_html += f'<span>{log["message"]}</span>'
            log_html += '</div>'

        log_html += '</div>'

        st.markdown(log_html, unsafe_allow_html=True)

        if auto_scroll:
            st.markdown("""
            <script>
                var logContainer = document.querySelector('div[style*="overflow-y: auto"]');
                if (logContainer) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            </script>
            """, unsafe_allow_html=True)
```

### 4. Agent工作站组件

```python
def create_agent_workstation_card(agent_name, agent_role, status, progress, tools, logs):
    """
    创建Agent工作站卡片

    Args:
        agent_name: Agent名称
        agent_role: Agent角色
        status: 状态（运行中/空闲/异常）
        progress: 进度（0-100）
        tools: 工具列表
        logs: 日志列表
    """
    with st.container():
        # 标题栏
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### 🤖 {agent_name}")
            st.caption(f"职责: {agent_role}")
        with col2:
            st.markdown(get_status_badge(status))

        st.markdown("---")

        # 主体内容
        col1, col2 = st.columns([1, 3])

        with col1:
            # 状态面板
            st.markdown("**工作状态**")
            st.progress(progress / 100, text=f"{progress}%")

            st.markdown("**使用工具**")
            for tool in tools:
                st.markdown(f"- 🔧 {tool}")

            st.markdown(f"**耗时**: 12.5秒")

        with col2:
            # 工作日志
            create_live_log_viewer(logs, max_height=250)
```

---

## 📱 响应式设计

### 移动端适配

```python
# 检测设备类型
import streamlit.components.v1 as components

def is_mobile():
    """检测是否为移动端"""
    # 通过JavaScript检测屏幕宽度
    is_mobile_js = """
    <script>
        function isMobile() {
            return window.innerWidth <= 768;
        }
        document.write(isMobile());
    </script>
    """
    result = components.html(is_mobile_js, height=0)
    return result

# 根据设备调整布局
if is_mobile():
    # 移动端：单列布局
    col1, col2, col3 = st.columns([1])
else:
    # 桌面端：三列布局
    col1, col2, col3 = st.columns([1, 1, 1])
```

---

## 🚀 实施计划

### Phase 1: 设计系统建立（1天）

- [x] 定义色彩系统
- [x] 定义字体系统
- [x] 定义间距系统
- [x] 创建可复用组件库

### Phase 2: 主页重构（1天）

- [ ] 添加Phase 3性能监控仪表盘
- [ ] 重构欢迎横幅
- [ ] 优化组织架构展示
- [ ] 增强快速开始卡片

### Phase 3: Agent状态页重构（1天）

- [ ] 添加搜索和筛选功能
- [ ] 增强Agent详情卡片
- [ ] 添加实时状态更新
- [ ] 优化工具和任务展示

### Phase 4: 任务管理页重构（2天）

- [ ] 创建Agent工作站组件
- [ ] 增强实时进度反馈
- [ ] 优化日志展示
- [ ] 添加Commander审核面板

### Phase 5: 报告查看页重构（1天）

- [ ] 添加数据可视化
- [ ] 增强报告展示
- [ ] 添加导出功能
- [ ] 优化报告列表

### Phase 6: 系统配置页优化（0.5天）

- [ ] 增强配置验证
- [ ] 添加配置历史
- [ ] 优化配置布局

### Phase 7: 测试和优化（0.5天）

- [ ] 跨浏览器测试
- [ ] 响应式测试
- [ ] 性能优化
- [ ] 用户反馈收集

**总计**: 约7天

---

## 📊 成功指标

### 视觉改进

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| **UI现代化评分** | 5/10 | 9/10 | 设计评审 |
| **品牌一致性** | 3/10 | 8/10 | 设计系统遵循度 |
| **视觉层次** | 4/10 | 9/10 | 眼动追踪测试 |

### 功能展示

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| **Phase 3成果展示** | 0% | 100% | 功能覆盖 |
| **Agent透明度** | 40% | 90% | 信息完整度 |
| **数据可视化** | 10% | 80% | 图表数量 |

### 用户体验

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| **任务完成时间** | 5分钟 | 3分钟 | 用户测试 |
| **错误率** | 15% | 5% | 错误日志 |
| **用户满意度** | 6/10 | 9/10 | 用户调研 |

---

## 🎯 风险和缓解

### 风险1: Streamlit限制

**风险**: Streamlit的定制化能力有限，可能无法实现所有设计效果

**缓解方案**:
1. 使用HTML/CSS注入（`st.markdown(unsafe_allow_html=True)`）
2. 使用自定义组件（`streamlit.components.v1.html`）
3. 考虑迁移到更灵活的框架（如Dash或Next.js）

### 风险2: 性能影响

**风险**: 大量HTML/CSS注入和实时更新可能影响性能

**缓解方案**:
1. 使用缓存（`@st.cache_data`）
2. 优化重渲染频率
3. 懒加载非关键内容

### 风险3: 维护成本

**风险**: 自定义HTML/CSS增加维护难度

**缓解方案**:
1. 建立组件库（可复用）
2. 编写详细文档
3. 代码注释清晰

---

## 📚 参考资料

### 设计灵感

- [Material Design](https://material.io/design)
- [Ant Design](https://ant.design/)
- [Streamlit官方Gallery](https://streamlit.io/gallery)

### 技术文档

- [Streamlit文档](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [CSS Grid Layout](https://css-tricks.com/snippets/css/complete-guide-grid/)

---

## 📝 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-03-14 | v1.0 | 初始设计文档 |

---

**设计师**: OMC Team Designer
**最后更新**: 2026-03-14

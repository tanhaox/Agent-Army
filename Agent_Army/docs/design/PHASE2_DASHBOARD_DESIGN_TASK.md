# Phase 2设计任务：仪表板（Dashboard）重构

**任务类型**: UI/UX设计
**完成时间**: 预计1天
**依赖**: Phase 1设计系统已完成

---

## 🎯 设计目标

基于Phase 1建立的设计系统，重构仪表板页面，实现：
1. **统一的视觉风格** - 使用Design Tokens和全局样式
2. **优秀的用户体验** - 加载状态、错误处理、即时反馈
3. **清晰的信息架构** - 无隐藏功能，一目了然

---

## 📋 现状分析

### 当前Dashboard问题

**文件**: `src/core/pages_v2/dashboard.py` (228行)

**问题识别**:

1. **风格不统一**
   - ❌ 使用原生Streamlit组件（st.metric）
   - ❌ 硬编码颜色（没有使用Design Tokens）
   - ❌ 没有应用全局样式系统
   - ❌ 卡片样式不统一

2. **用户体验问题**
   - ❌ 没有加载状态（数据加载时显示空白）
   - ❌ 没有错误处理（数据获取失败无提示）
   - ❌ 没有即时反馈（按钮点击无状态）
   - ❌ 硬编码数据（不是真实数据）

3. **信息架构问题**
   - ❌ 顶部统计卡片布局拥挤（4列）
   - ❌ 军团状态展示冗长（垂直列表）
   - ❌ 快速分析区域不突出
   - ❌ 热点新闻缺少视觉吸引力

---

## 🎨 设计方案

### 1. 整体布局

```
┌─────────────────────────────────────────────────────┐
│  🎖️ Agent Army V2.0                    [刷新] [设置] │
│  AI价值投资分析系统 | 24个Agent | 100%完成            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  【顶部统计卡片】(统一风格，带图标和趋势)             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│  │ 24   │ │  6   │ │ 100% │ │  3   │               │
│  │Agent │ │军团  │ │完成率│ │活跃  │               │
│  └──────┘ └──────┘ └──────┘ └──────┘               │
│                                                     │
│  【快速分析区域】(突出显示，大按钮)                   │
│  ┌────────────────────┐ ┌──────────┐              │
│  │ 输入股票代码 [     ] │  🚀 分析 │              │
│  └────────────────────┘ └──────────┘              │
│                                                     │
│  【今日任务 & 热点新闻】(2列布局)                    │
│  ┌─────────────┐ ┌─────────────┐                 │
│  │ 今日任务     │ │ 热点新闻     │                 │
│  │  (3项)      │ │  (3条)      │                 │
│  │             │ │             │                 │
│  └─────────────┘ └─────────────┘                 │
│                                                     │
│  【军团活动状态】(卡片网格布局)                      │
│  ┌────────┐ ┌────────┐ ┌────────┐                │
│  │产业分析│ │热点捕捉│ │个股挖掘│                │
│  │ 5个Agt │ │ 4个Agt │ │ 4个Agt │                │
│  │ ⭐⭐⭐  │ │ ⭐⭐   │ │ ⭐⭐   │                │
│  └────────┘ └────────┘ └────────┘                │
│  ┌────────┐ ┌────────┐ ┌────────┐                │
│  │目标预测│ │策略执行│ │结果验证│                │
│  │ 5个Agt │ │ 5个Agt │ │ 5个Agt │                │
│  │ ⭐⭐⭐  │ │ ⭐⭐⭐  │ │ ⭐⭐⭐  │                │
│  └────────┘ └────────┘ └────────┘                │
│                                                     │
│  【快速入口】(4个大按钮)                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │Agent │ │任务  │ │报告  │ │监控  │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2. 组件设计

#### 2.1 顶部统计卡片

**设计要求**:
- 使用`DesignTokens.Colors`统一颜色
- 使用卡片样式（带阴影和悬停效果）
- 图标 + 数值 + 标签 + 趋势
- 响应式布局（移动端2列，桌面4列）

**代码示例**:
```python
# 使用军团主题色
from src.core import DesignTokens, apply_global_styles

apply_global_styles()

# 统计卡片
st.markdown(f"""
<div class="metric-card" style="border-left: 4px solid {DesignTokens.Colors.PRIMARY};">
    <div class="metric-label">Agent总数</div>
    <div class="metric-value">24</div>
    <div style="color: {DesignTokens.Colors.SUCCESS};">↑ 100%完成</div>
</div>
""", unsafe_allow_html=True)
```

#### 2.2 快速分析区域

**设计要求**:
- 突出显示（大输入框 + 大按钮）
- 按钮使用主色调（PRIMARY）
- 输入框使用焦点样式（BORDER_FOCUS）
- 按钮带loading状态

**交互流程**:
1. 用户输入股票代码
2. 点击"分析"按钮
3. 显示骨架屏（loading状态）
4. 分析完成，显示Toast通知
5. 跳转到任务管理页面

#### 2.3 今日任务列表

**设计要求**:
- 使用列表样式（简洁清晰）
- 状态徽章（使用`DesignTokens.Colors`）
- 点击任务可查看详情
- 空状态提示（无任务时）

**状态徽章设计**:
```python
# 待处理 - 黄色
status_badge("待处理", "warning")

# 进行中 - 蓝色
status_badge("分析中", "info")

# 已完成 - 绿色
status_badge("已完成", "success")

# 失败 - 红色
status_badge("失败", "error")
```

#### 2.4 热点新闻卡片

**设计要求**:
- 新闻卡片样式（带阴影和边框）
- 影响标记（正面🟢/负面🔴/中性🟡）
- 关联股票标签
- 发布时间

**卡片设计**:
```python
# 新闻卡片
st.markdown(f"""
<div class="news-card" style="
    border-left: 4px solid {DesignTokens.Colors.SUCCESS};
    padding: 16px;
    border-radius: 8px;
    box-shadow: {DesignTokens.Shadow.SM};
">
    <div style="color: {DesignTokens.Colors.TEXT_HINT};">14:30</div>
    <div style="font-weight: 600; color: {DesignTokens.Colors.TEXT_PRIMARY};">
        央行降准利好银行股
    </div>
    <div style="margin-top: 8px;">
        <span class="tag">平安银行</span>
        <span class="tag">招商银行</span>
    </div>
</div>
""", unsafe_allow_html=True)
```

#### 2.5 军团活动状态

**设计要求**:
- 网格布局（3列 × 2行）
- 每个军团一个卡片
- 使用军团主题色（ARMY_*）
- 完成度星级显示（⭐⭐⭐）
- 当前状态文字

**军团卡片设计**:
```python
from src.core import get_army_color

# 军团卡片
army_name = "产业分析军团"
army_color = get_army_color(army_name)

st.markdown(f"""
<div class="army-card" style="
    background: {rgba(army_color, 0.05)};
    border-left: 4px solid {army_color};
    border-radius: 8px;
    padding: 16px;
    box-shadow: {DesignTokens.Shadow.SM};
">
    <div style="display: flex; justify-content: space-between;">
        <div style="font-weight: 600;">🏭 产业分析军团</div>
        <div style="color: {army_color};">5个Agent</div>
    </div>
    <div style="margin-top: 8px;">
        <span style="color: {DesignTokens.Colors.WARNING};">⭐⭐⭐</span>
        <span style="color: {DesignTokens.Colors.TEXT_HINT};"> 125%完成</span>
    </div>
    <div style="margin-top: 4px; font-size: 14px; color: {DesignTokens.Colors.TEXT_SECONDARY};">
        宏观AI工作中
    </div>
</div>
""", unsafe_allow_html=True)
```

#### 2.6 快速入口

**设计要求**:
- 4个大按钮（网格布局）
- 图标 + 文字
- 悬停效果
- 点击跳转（使用`st.switch_page`或提示）

### 3. 加载状态设计

#### 3.1 初始加载

**实现**:
```python
from src.core import show_skeleton_card

# 显示骨架屏
show_skeleton_card(count=4)  # 4个统计卡片骨架
```

#### 3.2 数据刷新

**实现**:
```python
from src.core import show_loading_overlay, show_progress_toast

# 方法1: 全屏加载遮罩
status = show_loading_overlay("正在刷新数据...", "spinner")
# ... 加载数据 ...
status.update(label="刷新完成！", state="complete", expanded=False)

# 方法2: 进度Toast
progress_bar, status_text = show_progress_toast("刷新数据", 0)
for i in range(0, 101, 10):
    update_progress_toast(progress_bar, status_text, i, "加载中")
```

### 4. 错误处理设计

#### 4.1 数据加载失败

**实现**:
```python
from src.core import show_error_card

show_error_card(
    title="数据加载失败",
    message="无法获取Agent状态数据，请检查网络连接",
    icon="❌",
    details="ConnectionError: Connection refused",
    actions=[
        {"label": "重试", "key": "retry"},
        {"label": "刷新页面", "key": "refresh"}
    ]
)
```

#### 4.2 空状态提示

**实现**:
```python
from src.core import show_empty_state

show_empty_state(
    title="暂无任务",
    description="还没有任何分析任务，点击下方按钮创建第一个任务",
    icon="📋",
    action_label="创建任务",
    action_key="create_task"
)
```

### 5. 即时反馈设计

#### 5.1 Toast通知

**实现**:
```python
from src.core import toast_success, toast_error

# 成功提示
toast_success("分析任务已创建！")

# 错误提示
toast_error("股票代码格式错误，请重新输入")
```

#### 5.2 按钮状态

**实现**:
```python
from src.core import button_with_feedback

def analyze_stock():
    # 执行分析逻辑
    return {"status": "success"}

button_with_feedback(
    label="🚀 开始分析",
    on_click=analyze_stock,
    loading_text="正在创建分析任务...",
    success_message="分析任务已创建！",
    error_message="创建失败，请重试"
)
```

---

## 🎯 设计交付物

### 文档

1. **设计规范文档** (`docs/dashboard_design_spec.md`)
   - 页面布局规范
   - 组件使用规范
   - 颜色使用规范
   - 交互流程规范

2. **实现指南** (`docs/dashboard_implementation_guide.md`)
   - 代码结构说明
   - 组件导入指南
   - 数据接口说明
   - 测试方法说明

### 设计稿（可选）

1. **线框图** - 页面布局草图
2. **视觉稿** - 高保真设计稿（Figma/Sketch）
3. **交互原型** - 可点击的原型

### 代码模板

1. **Dashboard模块模板** (`src/core/pages_v2/dashboard_template.py`)
   - 完整的页面结构
   - 所有组件的实现
   - 注释和使用说明

---

## 📊 设计验收标准

### 视觉一致性

- [ ] 所有颜色使用`DesignTokens.Colors`
- [ ] 所有字体使用`DesignTokens.Typography`
- [ ] 所有间距使用`DesignTokens.Spacing`
- [ ] 所有卡片使用统一样式
- [ ] 所有军团使用正确主题色

### 用户体验

- [ ] 数据加载时显示骨架屏
- [ ] 错误时有友好的错误提示
- [ ] 操作成功时有Toast通知
- [ ] 按钮有loading状态
- [ ] 空状态有友好提示

### 功能完整性

- [ ] 顶部统计卡片显示正确数据
- [ ] 快速分析功能正常
- [ ] 今日任务列表可交互
- [ ] 热点新闻显示正常
- [ ] 军团状态展示正确
- [ ] 快速入口可跳转

### 响应式设计

- [ ] 移动端布局正常（<768px）
- [ ] 平板布局正常（768px-1024px）
- [ ] 桌面布局正常（>1024px）

---

## 🚀 下一步

完成设计后，进入**实施阶段**：

1. **Phase 2.1**: 重建Dashboard页面（使用设计系统）
2. **Phase 2.2**: 集成真实数据源
3. **Phase 2.3**: 测试和优化
4. **Phase 2.4**: 文档更新

---

**创建时间**: 2026-03-15
**设计者**: omc team designer
**状态**: 待开始

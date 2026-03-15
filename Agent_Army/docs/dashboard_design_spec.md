# Dashboard设计规范文档

**版本**: v2.1
**更新日期**: 2026-03-15
**基于**: Phase 1设计系统

---

## 📋 目录

1. [设计原则](#设计原则)
2. [布局规范](#布局规范)
3. [组件规范](#组件规范)
4. [颜色规范](#颜色规范)
5. [交互规范](#交互规范)
6. [响应式设计](#响应式设计)

---

## 🎨 设计原则

### 1. 风格统一

**规则**：
- ✅ 所有颜色必须使用`DesignTokens.Colors`
- ✅ 所有字体必须使用`DesignTokens.Typography`
- ✅ 所有间距必须使用`DesignTokens.Spacing`
- ✅ 所有圆角必须使用`DesignTokens.Radius`
- ✅ 所有阴影必须使用`DesignTokens.Shadow`

**示例**：
```python
from src.core import DesignTokens

# ✅ 正确
color = DesignTokens.Colors.PRIMARY
font_size = DesignTokens.Typography.H1
spacing = DesignTokens.Spacing.MD

# ❌ 错误
color = "#1E88E5"  # 硬编码
font_size = "2.5rem"  # 硬编码
spacing = "16px"  # 硬编码
```

### 2. 用户体验优秀

**规则**：
- ✅ 数据加载时显示骨架屏或进度条
- ✅ 错误时有友好的错误提示和恢复操作
- ✅ 操作成功时有Toast通知
- ✅ 按钮有loading状态
- ✅ 空状态有友好提示

**实现**：
```python
from src.core import show_skeleton_card, toast_success, show_error_card

# 加载状态
show_skeleton_card(count=4)

# 成功提示
toast_success("操作成功！")

# 错误处理
show_error_card(
    title="数据加载失败",
    message="无法连接到服务器",
    actions=[{"label": "重试", "key": "retry"}]
)
```

### 3. 无隐藏功能

**规则**：
- ✅ 所有功能在首页可见（不需要多次点击）
- ✅ 信息层级清晰（最多2层）
- ✅ 重要功能突出显示
- ✅ 次要功能有明确入口

---

## 📐 布局规范

### 页面结构

```
┌─────────────────────────────────────────┐
│ 页面头部（标题 + 时间）                    │
├─────────────────────────────────────────┤
│ 分隔线                                   │
├─────────────────────────────────────────┤
│ 【系统概览】标题                          │
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐ (4列统计卡片)  │
│ │24 │ │ 6 │ │100│ │ 3 │              │
│ └───┘ └───┘ └───┘ └───┘              │
├─────────────────────────────────────────┤
│ 【快速分析】标题                          │
│ ┌──────────────────┐ ┌────────┐       │
│ │ 输入框 [         ] │ 分析按钮 │       │
│ └──────────────────┘ └────────┘       │
├─────────────────────────────────────────┤
│ 【今日任务】         │ 【热点新闻】       │ (2列)
│ ┌─────────────────┐ │ ┌─────────────┐ │
│ │ 任务1           │ │ │ 新闻1        │ │
│ │ 任务2           │ │ │ 新闻2        │ │
│ └─────────────────┘ │ └─────────────┘ │
├─────────────────────────────────────────┤
│ 【军团活动状态】标题                      │
│ ┌────────┐ ┌────────┐ ┌────────┐ (3列) │
│ │产业分析│ │热点捕捉│ │个股挖掘│        │
│ └────────┘ └────────┘ └────────┘        │
│ ┌────────┐ ┌────────┐ ┌────────┐       │
│ │目标预测│ │策略执行│ │结果验证│       │
│ └────────┘ └────────┘ └────────┘       │
├─────────────────────────────────────────┤
│ 【快速入口】标题                          │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Agent │ │任务  │ │报告  │ │监控  │   │
│ └──────┘ └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────────────┤
│ 分隔线                                   │
│ 底部信息（版权、版本）                     │
└─────────────────────────────────────────┘
```

### 间距规范

| 位置 | 间距 | 说明 |
|------|------|------|
| 页面头部与内容 | `LG` (24px) | 使用`st.markdown("")` |
| 区块之间 | `MD` (16px) | 主要内容区块 |
| 卡片之间 | `MD` (16px) | 同一区块的卡片 |
| 卡片内部 | `SM` (8px) | 卡片内元素 |

### 宽度规范

| 布局 | 列数 | 说明 |
|------|------|------|
| 统计卡片 | 4列 | `st.columns(4)` |
| 快速分析 | 4:1 | 输入框4份，按钮1份 |
| 任务/新闻 | 2列 | `st.columns(2)` |
| 军团卡片 | 3列 | `st.columns(3)` |
| 快速入口 | 4列 | `st.columns(4)` |

---

## 🧩 组件规范

### 1. 统计卡片

**用途**：顶部4个统计卡片（Agent总数、军团数量、完成率、活跃任务）

**样式要求**：
- 左边框：4px实线，使用主题色
- 背景：主题色的5%透明度
- 数值颜色：使用主题色
- 趋势颜色：SUCCESS绿色

**函数签名**：
```python
def render_stat_card(label: str, value: str, delta: str, icon: str, color: str):
    """渲染统计卡片"""
```

**使用示例**：
```python
render_stat_card(
    label="Agent总数",
    value="24",
    delta="↑ 100%完成",
    icon="🤖",
    color=DesignTokens.Colors.PRIMARY
)
```

### 2. 新闻卡片

**用途**：热点新闻展示

**样式要求**：
- 左边框：3px实线，根据影响类型着色
- 背景：白色
- 阴影：`Shadow.XS`
- 圆角：`Radius.MD`

**影响颜色**：
- 正面：`DesignTokens.Colors.SUCCESS` (🟢)
- 负面：`DesignTokens.Colors.ERROR` (🔴)
- 中性：`DesignTokens.Colors.WARNING` (🟡)

**函数签名**：
```python
def render_news_card(title: str, time: str, impact: str, stocks: str):
    """渲染新闻卡片"""
```

### 3. 军团卡片

**用途**：6大军团状态展示

**样式要求**：
- 使用军团主题色（`get_army_color(name)`）
- 左边框：4px实线
- 背景：主题色的5%透明度
- 阴影：`Shadow.SM`
- 星级：使用⭐符号（1-3颗）

**函数签名**：
```python
def render_army_card(name: str, icon: str, agent_count: int,
                      completion: str, stars: int, status: str):
    """渲染军团卡片"""
```

### 4. 任务列表项

**用途**：今日任务列表

**样式要求**：
- 左边框：3px实线，根据状态着色
- 背景：状态颜色的5%透明度
- 图标 + 股票代码 + 状态徽章

**状态颜色**：
- 待处理：`DesignTokens.Colors.WARNING` (⏳)
- 分析中：`DesignTokens.Colors.INFO` (🔄)
- 已完成：`DesignTokens.Colors.SUCCESS` (✅)
- 失败：`DesignTokens.Colors.ERROR` (❌)

**函数签名**：
```python
def render_task_item(stock_code: str, task_type: str, status: str):
    """渲染任务列表项"""
```

---

## 🎨 颜色规范

### 军团主题色

| 军团 | 颜色代码 | 用途 |
|------|---------|------|
| 热点捕捉军团 | `#FF5722` | 新闻、龙虎榜、资金流向 |
| 产业分析军团 | `#2196F3` | 产业链、竞争格局、政策影响 |
| 个股挖掘军团 | `#4CAF50` | 基本面、技术面、估值 |
| 目标预测军团 | `#FF9800` | 盈利预测、目标价 |
| 策略执行军团 | `#9C27B0` | 仓位、止损止盈、风险控制 |
| 结果验证军团 | `#00BCD4` | 回测、实盘跟踪、策略优化 |
| 战略层 | `#E91E63` | 宏观经济、资产配置 |

**使用方法**：
```python
from src.core import get_army_color

army_color = get_army_color("产业分析军团")
```

### 功能色

| 用途 | 颜色代码 | 图标 |
|------|---------|------|
| 成功 | `#4CAF50` | ✅ 🟢 |
| 警告 | `#FF9800` | ⚠️ 🟡 |
| 错误 | `#F44336` | ❌ 🔴 |
| 信息 | `#2196F3` | ℹ️ 🔵 |

---

## 🔄 交互规范

### 1. 快速分析流程

```
用户输入股票代码
    ↓
点击"开始分析"按钮
    ↓
显示加载状态（spinner）
    ↓
创建任务（1秒模拟）
    ↓
显示Toast通知（成功）
    ↓
显示提示信息（跳转到任务管理）
```

**实现**：
```python
if analyze_button and stock_code:
    with show_loading_overlay("正在创建分析任务...", "spinner"):
        time.sleep(1)

    toast_success(f"分析任务已创建！正在分析 {stock_code}")
    st.info(f"✅ 任务已创建，请前往【📋 任务管理】查看进度")
```

### 2. 按钮点击反馈

**规则**：
- ✅ 主要操作使用`type="primary"`
- ✅ 次要操作使用默认按钮
- ✅ 避免使用按钮进行导航（使用文字提示）

**示例**：
```python
# ✅ 正确：主要操作
st.button("🚀 开始分析", type="primary", use_container_width=True)

# ✅ 正确：次要操作
st.button("查看全部任务 →")

# ❌ 错误：按钮用于导航
st.button("前往任务管理")  # 应该使用文字提示
```

### 3. 错误处理

**规则**：
- ✅ 数据加载失败：显示错误卡片
- ✅ 空数据：显示空状态提示
- ✅ 网络错误：提供重试按钮
- ✅ 输入错误：Toast通知 + 高亮输入框

**实现**：
```python
try:
    data = fetch_data()
    if not data:
        show_empty_state("暂无数据", "还没有任何数据")
except Exception as e:
    show_error_card(
        title="数据加载失败",
        message=str(e),
        actions=[{"label": "重试", "key": "retry"}]
    )
```

---

## 📱 响应式设计

### 断点规范

| 设备 | 宽度 | 布局调整 |
|------|------|---------|
| 手机（竖） | < 640px | 1列布局 |
| 手机（横） | 640px - 768px | 2列布局 |
| 平板 | 768px - 1024px | 2-3列布局 |
| 桌面 | > 1024px | 完整布局 |

### 实现方法

**使用CSS媒体查询**（已在`global_styles.py`中定义）：
```css
@media (max-width: 768px) {
    .stCard {
        padding: 16px;
    }
    .metric-value {
        font-size: 24px;
    }
}
```

**Streamlit响应式**：
```python
import streamlit as st

# 根据屏幕宽度调整列数
if st.session_state.get('screen_width', 1024) < 768:
    cols = st.columns(2)
else:
    cols = st.columns(4)
```

---

## ✅ 设计验收清单

### 视觉一致性

- [ ] 所有颜色使用`DesignTokens.Colors`
- [ ] 所有字体使用`DesignTokens.Typography`
- [ ] 所有间距使用`DesignTokens.Spacing`
- [ ] 所有卡片使用统一样式
- [ ] 所有军团使用正确主题色

### 用户体验

- [ ] 数据加载时显示骨架屏或进度条
- [ ] 错误时有友好的错误提示
- [ ] 操作成功时有Toast通知
- [ ] 空状态有友好提示
- [ ] 按钮有视觉反馈（悬停、点击）

### 功能完整性

- [ ] 顶部统计卡片显示正确数据
- [ ] 快速分析功能正常工作
- [ ] 今日任务列表正确显示
- [ ] 热点新闻正确显示
- [ ] 军团状态展示正确
- [ ] 快速入口有明确提示

### 代码质量

- [ ] 所有组件都有文档字符串
- [ ] 使用类型提示
- [ ] 代码格式统一
- [ ] 遵循PEP 8规范

---

## 📚 参考资料

- **Phase 1完成报告**: `docs/UI_UX_PHASE1_COMPLETION_REPORT.md`
- **设计系统**: `src/core/design_tokens.py`
- **全局样式**: `src/core/global_styles.py`
- **组件库**: `src/core/loading_states.py`, `src/core/error_handling.py`, `src/core/feedback.py`

---

**文档版本**: v2.1
**最后更新**: 2026-03-15
**维护者**: Agent Army UI/UX Team

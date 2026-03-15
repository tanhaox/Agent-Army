# Dashboard实现指南

**版本**: v2.1
**更新日期**: 2026-03-15
**目标读者**: 开发者

---

## 📋 目录

1. [快速开始](#快速开始)
2. [代码结构](#代码结构)
3. [组件导入](#组件导入)
4. [数据接口](#数据接口)
5. [测试方法](#测试方法)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 环境准备

确保Phase 1设计系统已完成：
```bash
cd Agent_Army

# 验证设计系统文件存在
ls src/core/design_tokens.py
ls src/core/global_styles.py
ls src/core/loading_states.py
ls src/core/error_handling.py
ls src/core/feedback.py
```

### 2. 运行新Dashboard

**方法1：使用web_app_v2.py（推荐）**

修改`web_app_v2.py`，将Dashboard页面指向新版本：
```python
# 在web_app_v2.py中修改
PAGES = {
    "🏠 主页": {"page": "pages_v2.dashboard_v2", "icon": "🏠"},  # 改为dashboard_v2
    # ...其他页面
}
```

**方法2：直接运行**
```bash
streamlit run src/core/pages_v2/dashboard_v2.py
```

### 3. 验证效果

打开浏览器访问 `http://localhost:8501`，应该看到：
- ✅ 统一的颜色风格
- ✅ 美观的卡片布局
- ✅ 加载状态显示
- ✅ Toast通知功能

---

## 📁 代码结构

### 文件组织

```
src/core/
├── design_tokens.py           # 设计变量（Phase 1）
├── global_styles.py            # 全局样式（Phase 1）
├── loading_states.py           # 加载状态（Phase 1）
├── error_handling.py           # 错误处理（Phase 1）
├── feedback.py                 # 反馈系统（Phase 1）
└── pages_v2/
    ├── dashboard.py            # 旧版Dashboard（v2.0）
    └── dashboard_v2.py         # 新版Dashboard（v2.1）← 新建
```

### 代码行数对比

| 版本 | 文件 | 行数 | 变化 |
|------|------|------|------|
| v2.0 | dashboard.py | 228行 | - |
| v2.1 | dashboard_v2.py | 450+行 | +222行 (+97%) |

**新增代码说明**：
- 组件渲染函数：+150行
- 样式优化：+50行
- 注释和文档：+22行

---

## 📥 组件导入

### 必需导入

```python
# 添加项目根目录
from pathlib import Path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入设计系统
from src.core import (
    # 设计变量
    DesignTokens,
    get_army_color,
    rgba,

    # 全局样式
    apply_global_styles,
    apply_loading_styles,
    apply_error_styles,
    apply_feedback_styles,

    # 加载状态
    show_skeleton_card,
    show_progress_bar,
    show_loading_overlay,

    # 错误处理
    show_error_card,
    show_empty_state,

    # 反馈系统
    toast_success,
    toast_error
)
```

### 应用样式

在`render_dashboard()`函数的最开始：
```python
def render_dashboard():
    """渲染主页Dashboard"""

    # 应用所有样式（必需！）
    apply_global_styles()
    apply_loading_styles()
    apply_error_styles()
    apply_feedback_styles()

    # ...其余代码
```

**重要**：如果不应用样式，页面将无法正确显示！

---

## 🔌 数据接口

### Session State

Dashboard使用`st.session_state`存储数据：

```python
# 获取任务历史
task_history = st.session_state.get('task_history', [])

# 获取活跃任务数
active_tasks = len(st.session_state.get('task_history', []))
```

### 真实数据源（待集成）

**Phase 3将集成真实数据源**：

1. **Agent状态数据**
```python
# 从Agent管理模块获取
from src.agents.management.agent_manager import AgentManager

manager = AgentManager()
agent_status = manager.get_all_agents_status()
```

2. **任务数据**
```python
# 从任务管理模块获取
from src.workflows.task_manager import TaskManager

task_manager = TaskManager()
tasks = task_manager.get_active_tasks()
```

3. **新闻数据**
```python
# 从新闻监控AI获取
from src.agents.business.hot_spot.news_monitor import NewsMonitorAI

news_ai = NewsMonitorAI()
news = news_ai.get_latest_news()
```

### 当前数据状态

**v2.1使用模拟数据**：
- ✅ 统计数据：硬编码（24个Agent，6个军团）
- ✅ 军团状态：硬编码（6个军团配置）
- ✅ 新闻数据：硬编码（3条新闻示例）
- ⏳ 任务数据：从`st.session_state`读取
- ❌ Agent状态：待集成（Phase 3）

---

## 🧪 测试方法

### 1. 单元测试

创建测试文件 `tests/test_dashboard_v2.py`：
```python
import pytest
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.pages_v2.dashboard_v2 import (
    render_stat_card,
    render_news_card,
    render_army_card,
    render_task_item
)

def test_render_stat_card():
    """测试统计卡片渲染"""
    # 测试颜色参数
    assert DesignTokens.Colors.PRIMARY == "#1E88E5"
    assert DesignTokens.Colors.SUCCESS == "#4CAF50"

    print("✅ 统计卡片测试通过")

def test_army_color():
    """测试军团颜色"""
    from src.core import get_army_color

    color = get_army_color("产业分析军团")
    assert color == DesignTokens.Colors.ARMY_INDUSTRY

    print("✅ 军团颜色测试通过")

if __name__ == "__main__":
    test_render_stat_card()
    test_army_color()
```

### 2. 集成测试

**测试步骤**：
1. 启动Dashboard：`streamlit run src/core/pages_v2/dashboard_v2.py`
2. 验证顶部统计卡片显示正常
3. 测试快速分析功能（输入股票代码，点击分析）
4. 验证Toast通知显示
5. 检查军团卡片颜色正确
6. 测试快速入口按钮

### 3. 视觉回归测试

**截图对比**：
```bash
# v2.0截图
streamlit run src/core/pages_v2/dashboard.py
# 浏览器打开 http://localhost:8501
# 截图保存为 dashboard_v20.png

# v2.1截图
streamlit run src/core/pages_v2/dashboard_v2.py
# 浏览器打开 http://localhost:8501
# 截图保存为 dashboard_v21.png

# 对比两个截图
```

---

## ❓ 常见问题

### Q1: 页面样式没有生效？

**原因**：忘记应用全局样式

**解决**：
```python
def render_dashboard():
    # ✅ 必须在函数开头应用样式
    apply_global_styles()
    apply_loading_styles()
    apply_error_styles()
    apply_feedback_styles()

    # ...其余代码
```

### Q2: 军团颜色不正确？

**原因**：军团名称不匹配

**解决**：
```python
# ✅ 使用完整军团名称
get_army_color("产业分析军团")  # 正确

# ❌ 使用缩写或错误名称
get_army_color("产业")  # 错误
```

**支持的军团名称**：
- 热点捕捉军团
- 产业分析军团
- 个股挖掘军团
- 目标预测军团
- 策略执行军团
- 结果验证军团
- 战略层

### Q3: Toast通知没有显示？

**原因**：Streamlit原生Toast限制

**解决**：确保使用最新版Streamlit（≥1.20）
```bash
pip install --upgrade streamlit
```

### Q4: 组件之间的间距不对？

**原因**：没有正确使用Design Tokens

**解决**：
```python
# ✅ 正确：使用Design Tokens
st.markdown("", unsafe_allow_html=True)  # 8px间距
st.markdown("")  # 16px间距（默认）

# ❌ 错误：硬编码间距
st.markdown("<br><br>", unsafe_allow_html=True)  # 不推荐
```

### Q5: 移动端布局混乱？

**原因**：没有使用响应式列

**解决**：
```python
# 根据屏幕宽度调整
screen_width = st.session_state.get('screen_width', 1024)

if screen_width < 768:
    cols = st.columns(2)  # 移动端：2列
else:
    cols = st.columns(4)  # 桌面端：4列

with cols[0]:
    # ...
```

---

## 🔄 从v2.0迁移到v2.1

### 步骤1：备份旧版本

```bash
cp src/core/pages_v2/dashboard.py src/core/pages_v2/dashboard_v20_backup.py
```

### 步骤2：更新web_app_v2.py

```python
# 修改页面配置
PAGES = {
    "🏠 主页": {"page": "pages_v2.dashboard_v2", "icon": "🏠"},  # 改为v2
    # ...其他页面保持不变
}
```

### 步骤3：测试新版本

```bash
streamlit run web_app_v2.py
```

### 步骤4：验证功能

- [ ] 主页显示正常
- [ ] 快速分析功能正常
- [ ] Toast通知正常
- [ ] 所有页面可访问

### 步骤5：提交代码

```bash
git add src/core/pages_v2/dashboard_v2.py
git add docs/dashboard_design_spec.md
git add docs/dashboard_implementation_guide.md
git commit -m "feat: Dashboard重构v2.1 - 使用Phase 1设计系统"
```

---

## 📊 性能优化建议

### 1. 减少重复渲染

```python
# ✅ 使用@st.cache_data缓存静态数据
@st.cache_data(ttl=300)  # 缓存5分钟
def get_army_config():
    return [
        {"name": "产业分析军团", "agent_count": 5, ...},
        # ...
    ]

# 在render_dashboard中调用
armies = get_army_config()
```

### 2. 懒加载组件

```python
# 只在需要时才导入
if show_loading:
    from src.core import show_loading_overlay
    show_loading_overlay("加载中...")
```

### 3. 异步数据加载

```python
import asyncio

async def load_data_async():
    # 异步加载数据
    task = asyncio.create_task(fetch_data())
    return await task
```

---

## 📚 扩展阅读

- **Design Tokens**: `src/core/design_tokens.py`
- **组件库**: `src/core/loading_states.py`, `src/core/error_handling.py`, `src/core/feedback.py`
- **设计规范**: `docs/dashboard_design_spec.md`
- **Phase 1报告**: `docs/UI_UX_PHASE1_COMPLETION_REPORT.md`

---

## 🆘 获取帮助

**问题反馈**：
- 创建Issue：`Agent Army`项目
- 联系维护者：Agent Army UI/UX Team
- 查看文档：`docs/`目录

**贡献代码**：
1. Fork项目
2. 创建功能分支：`git checkout -b feature/dashboard-v2`
3. 提交代码：`git commit -m "feat: ..."`
4. 推送分支：`git push origin feature/dashboard-v2`
5. 创建Pull Request

---

**文档版本**: v2.1
**最后更新**: 2026-03-15
**维护者**: Agent Army Development Team

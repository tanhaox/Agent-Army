# 决策记录：页面逻辑梳理

> **状态**：✅ 已确定
> **日期**：2026-07-08
> **关联页面**：21 个 web 页面

---

## 🎯 决策摘要

系统化梳理 21 个页面的关联逻辑，**修复 4 类问题**：
1. 🔴 缺失页面（4 个）
2. 🟡 关联断裂（6 处）
3. 🟢 可补强（3 处）
4. ⚪ 全局导航（logo 链接）

---

## 💬 讨论历程

### 问题发现

用户原话：
> "把几个页面逻辑再梳理一下，能关联的关联上。不能关联的看看哪里需要补强。"

通过全面检查发现 4 类问题：

### 1️⃣ 缺失页面

| 缺失 | 影响 |
|------|------|
| ❌ 章节大纲页 | 多个 Sidebar 引用 |
| ❌ 声纹档案页 | 角色档案标签页 |
| ❌ 弧光追踪页 | 角色档案标签页 |
| ❌ 总览页 | 多处提到的入口 |

### 2️⃣ 关联断裂

| 断裂 | 位置 |
|------|------|
| write.html ↔ 角色档案 | 写作时无法快速参考 |
| timeline.html ↔ 故事框架 | 缺少 5 大节点锚点 |
| foreshadow.html ↔ 05 伏笔 | 源在 setup-05 |
| audit.html ↔ setup 系列 | 审核结果无法跳回修改 |
| 角色档案 ↔ 时间线 | 出场记录无链接 |
| index.html ↔ 最近活动 | 不可点击 |

### 3️⃣ 可补强

- 写作页应能跳转到"参考档案"
- 审核页应能跳回对应章节
- 伏笔页应能跳回设定补充

### 4️⃣ 全局导航

- 所有页面左上角的 logo 都应能返回首页

---

## ✅ 最终设计

### A. 新增 4 个关键缺失页面

| 页面 | 行数 | 解决什么问题 |
|------|------|------------|
| **plan.html** | 294 | Step 2 章节大纲规划 |
| **character-voice.html** | 217 | 5 角色声纹对比总览 |
| **character-arc.html** | 308 | 5 角色弧光进度总览 |
| **dashboard.html** | 336 | 全书总览入口 |

### B. 优化现有页面

| 页面 | 补强内容 |
|------|---------|
| **write.html** | ① 侧边栏新增"📚 写作时参考"区块 ② AI 守护侧栏底部新增"📚 快速参考档案"（含 9 个跳转按钮） |
| **audit.html** | 操作按钮新增 3 个跳转（伏笔追踪 / 小七档案 / 设定补充） |
| **foreshadow.html** | 操作按钮新增 4 个跳转（设定补充 / 章节大纲 / 时间线 / 沉淀审核） |
| **timeline.html** | 5 大节点标题改为"5 大节点（快速锚点）" |
| **index.html** | ① 侧边栏新增"🏠 总览"入口 ② 3 个书库卡片改为可点击 ③ 最近活动 Feed 加跳转链接 |

### C. 全局导航

- 所有 20 个页面（除 index.html 自身）的 `<div class="topbar-logo">` 改为 `<a href="index.html" class="topbar-logo">`
- index.html 自身保持 `<div>`（首页点自己无意义）

---

## 📊 完整页面清单（21 个）

```
C:\AI-Agent-Local\Short story\web\
│
├── 🏠 书库
│   ├── index.html                       ← 书库
│   └── dashboard.html                   ← 🆕 全书总览
│
├── 📋 Step 1：设定（7 个）
│   ├── setup.html                       ← 设定总览
│   ├── setup-02-characters.html         ← 角色（含可点击列表 + 关系下拉框）
│   ├── setup-03-framework.html          ← 故事框架
│   ├── setup-04-tone.html               ← 基调
│   ├── setup-05-foreshadow.html         ← 伏笔
│   └── setup-06-audience.html           ← 商业定位
│
├── 👤 角色档案（5 + 2 = 7 个）
│   ├── character-profile-protagonist.html
│   ├── character-profile-ally1.html
│   ├── character-profile-rival1.html
│   ├── character-profile-bond1.html
│   ├── character-profile-neutral1.html
│   ├── character-voice.html             ← 🆕 声纹档案总览
│   └── character-arc.html               ← 🆕 弧光追踪总览
│
├── 📅 Step 2：规划（3 个）
│   ├── plan.html                        ← 🆕 章节大纲
│   ├── timeline.html                    ← 时间线（增强）
│   └── characters.html                  ← 关系图
│
├── ✍️ Step 3：写作（1 个 + 增强）
│   └── write.html                       ← 写作（含"快速参考档案"侧栏）
│
└── 🔍 Step 4：审核（3 个 + 增强）
    ├── foreshadow.html                  ← 伏笔追踪（增强）
    ├── audit.html                       ← 沉淀审核（增强）
    └── character-arc.html               ← 弧光追踪（同时属于 Step 1 和 Step 4）
```

---

## 🔗 核心关联链路

### 入口链路

```
index.html (书库)
   ├─ 点击书卡 → dashboard.html
   ├─ "总览"侧边栏 → dashboard.html
   └─ 最近活动 Feed → audit / foreshadow
```

### 4 步工作流

```
dashboard.html (总览)
   ├─ Step 1 设定（85%）→ setup.html 系列
   ├─ Step 2 规划（60%）→ plan.html → timeline.html
   ├─ Step 3 写作（25%）→ write.html
   └─ Step 4 审核（0%）→ audit.html / foreshadow.html
```

### 写作时参考链路

```
write.html (写作中)
   └─ "📚 快速参考档案" 侧栏
      ├─ 5 个角色档案（target="_blank" 新窗口）
      ├─ 伏笔登记表
      ├─ 章节大纲
      └─ 时间线位置
```

### 设定 → 档案链路

```
setup-02-characters.html (角色列表)
   └─ 点击角色 → character-profile-{role}.html
      ├─ #voice 锚点 → character-voice.html
      └─ #arc 锚点 → character-arc.html
```

### 审核修复链路

```
audit.html (审核报告)
   └─ "修复" 按钮组
      ├─ 🎣 跳到伏笔追踪
      ├─ 👤 跳到小七档案
      └─ 📋 跳到设定补充

foreshadow.html (伏笔追踪)
   └─ 操作按钮
      ├─ 📋 跳到设定补充
      ├─ 📋 跳到章节大纲
      ├─ 📅 跳到时间线
      └─ 🔍 跳到沉淀审核
```

---

## ✅ 确认的决策清单

| # | 决策项 | 决定 | 状态 |
|---|--------|------|------|
| 1 | 新增 plan.html | ✅ 采纳 | ✅ |
| 2 | 新增 character-voice.html | ✅ 采纳 | ✅ |
| 3 | 新增 character-arc.html | ✅ 采纳 | ✅ |
| 4 | 新增 dashboard.html | ✅ 采纳 | ✅ |
| 5 | write.html 加"快速参考档案" | ✅ 采纳 | ✅ |
| 6 | audit.html 加跳转按钮 | ✅ 采纳 | ✅ |
| 7 | foreshadow.html 加跳转按钮 | ✅ 采纳 | ✅ |
| 8 | timeline.html 强调 5 大节点锚点 | ✅ 采纳 | ✅ |
| 9 | index.html 书库卡片可点击 | ✅ 采纳 | ✅ |
| 10 | 所有页面 logo 链接 index.html | ✅ 采纳 | ✅ |

---

## 🔗 相关决策

- [伏笔追踪设计](./001-foreshadow-tracking.md) —— 伏笔的二级分类 + 3 个入口
- [系统质量防护](./003-system-quality-guards.md) —— 4 道质量门禁
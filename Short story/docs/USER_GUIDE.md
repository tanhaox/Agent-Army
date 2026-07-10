# Short story 用户使用手册

> **目标读者**：作者 / 想用本系统写作的人

---

## 🎯 系统是什么

**Short story** 不是一个"AI 自动写小说"的工具。

它是一个 **AI 写作协作者系统** —— 你写，AI 在 6 个维度上守护一致性。

**AI 帮你做的事**：
- ✅ 提醒"忘了前期设定"
- ✅ 检查"金手指用法不对"
- ✅ 追踪"伏笔忘了回收"
- ✅ 巡检"已设定但未用的角色/物品"
- ✅ 审核"10 章后整体是否对齐"
- ✅ 提供"基于已有设定的推断"

**AI 不帮你做的事**：
- ❌ 替你决策（你决定剧情走向）
- ❌ 替你创作情感和细节
- ❌ 替你闭门造车（你必须先有设定）

---

## 📂 文件结构速览

你的每本书都在 `books/<书名>/` 下：

```
books/my-novel/
├── meta.md                  ← 书名、简介、目标字数、当前进度
├── settings/                ← 6 维度设定（最重要！）
│   ├── 01-world.md          ← 世界观
│   ├── 02-characters.md     ← 角色（含声音指纹）
│   ├── 03-framework.md      ← 故事框架
│   ├── 04-tone.md           ← 叙事基调
│   ├── 05-foreshadow.md     ← 伏笔登记表
│   └── 06-audience.md       ← 商业定位
├── timeline.md              ← 故事时间线
├── voice_prints/            ← 声音指纹库
│   ├── protagonist.md
│   ├── ally-1.md
│   └── ...
├── chapters/                ← 章节目录
│   ├── chapter-001.md
│   ├── chapter-002.md
│   └── ...
└── fragments/               ← 素材库
    ├── quotes.md
    ├── inspirations.md
    └── excerpts/
```

---

## 🚀 5 步开始写作

### Step 1：复制书模板

```bash
cp -r books/_template books/my-novel
```

### Step 2：填写设定（最重要！）

打开 `books/my-novel/settings/` 下的 6 个文件，逐个填写。

**关键原则**：AI 协作者的所有推断都基于这些设定。**设定越完整，AI 守护越精准**。

**填写的优先顺序**：

| 优先级 | 文件 | 说明 |
|--------|------|------|
| 🔴 P0 | `03-framework.md` | 核心冲突是故事引擎 |
| 🔴 P0 | `02-characters.md` | 主角和核心配角必须有声音指纹 |
| 🔴 P0 | `01-world.md` | 世界观边界要清晰 |
| 🟡 P1 | `04-tone.md` | 基调决定修辞 |
| 🟡 P1 | `05-foreshadow.md` | 伏笔要登记 |
| 🟡 P1 | `06-audience.md` | 商业定位 |

### Step 3：填写时间线

打开 `books/my-novel/timeline.md`，按 [story-timeline 模板](../../AI-Agent-Local/docs/knowledge/novel-writing/story-timeline.md) 填写。

最少要包含：
- 章节范围（如 ch-001 ~ ch-030）
- 阶段（新手村 / 升级阶段 / 高潮转折）
- 关键节点（5 大节点）
- 触发点 / 转折点

### Step 4：填写声音指纹

为每个核心角色在 `books/my-novel/voice_prints/` 下创建档案，按 [voice_print-modeling 5 步法](../../AI-Agent-Local/docs/knowledge/novel-writing/voice_print-modeling.md) 填写：

- 高频词 / 禁用词
- 句法偏好
- 心理防御机制
- 生理与物理节拍

### Step 5：开始写作

打开 `books/my-novel/chapters/chapter-001.md`，开始写。

**写作流程**：

```
写一段 → 写一段 → 写一段
   ↓
一章写完 → 运行一致性守护 → 运行单章精修
   ↓
写下一章 → ...
   ↓
写满 10 章 → 运行沉淀审核
   ↓
继续写 → 每 10-30 章审核一次
```

---

## 🛡️ 10 大命令使用指南

### Step 1 阶段：设定梳理

#### `setup_consult.py` —— 引导式设定咨询

```bash
python ai-coauthor/commands/setup_consult.py books/my-novel
```

**何时使用**：
- 刚开始一本书，需要梳理设定时
- 卡在某个维度不知道写什么时

**功能**：
- 交互式问答
- 帮你梳理人物/关系/世界观/物品

#### `relationship_graph.py` —— 人物关系图

```bash
python ai-coauthor/commands/relationship_graph.py books/my-novel
```

**何时使用**：
- 角色超过 4 个时
- 想看关系网的全貌时
- 检查是否违反"米勒定律（核心 ≤ 6 人）"时

**输出**：`books/my-novel/relationships.md`（含 Mermaid 图）

### Step 2 阶段：内容规划

#### `plan_chapter.py` —— 章节规划

```bash
python ai-coauthor/commands/plan_chapter.py books/my-novel --chapter 50
```

**何时使用**：
- 写下一章之前
- 不确定本章该写什么时

**输出**：
- 本章阶段（升级阶段 / 高潮转折等）
- 应出场的人物
- 应升级的物品
- 目标推进度

#### `item_progression.py` —— 物品升级校验

```bash
python ai-coauthor/commands/item_progression.py books/my-novel
```

**何时使用**：
- 写完一章后（物品升级是否合理）
- 高潮转折前（伏笔是否兑现）

### Step 3 阶段：单章审视

#### `consistency_check.py` —— 一致性守护 ⭐ 最重要

```bash
python ai-coauthor/commands/consistency_check.py books/my-novel --text "主角今天去了东市"
```

**何时使用**：
- **每写一段都要用**（实时守护）
- 防胡写核心

**功能**：
- 实时对照设定检查
- 发现冲突立即警告

#### `voice_print_check.py` —— 声音指纹核对

```bash
python ai-coauthor/commands/voice_print_check.py books/my-novel --chapter chapters/chapter-001.md
```

**何时使用**：
- 写完一章后
- 不确定对话是否符合角色时

**功能**：
- 检查每个角色的对话是否符合声音指纹
- 提示"该角色不会这么说话"

#### `chapter_polish.py` —— 章节精修

```bash
python ai-coauthor/commands/chapter_polish.py books/my-novel --chapter chapters/chapter-001.md
```

**何时使用**：
- 写完一章后
- 复看章节时

**功能**：
- 4 维度审视：故事进展 / 修辞 / 引人入胜 / 违规词
- 给出修整建议

### Step 4 阶段：沉淀审核

#### `cumulative_audit.py` —— 沉淀审核 ⭐

```bash
python ai-coauthor/commands/cumulative_audit.py books/my-novel --range 1-30
```

**何时使用**：
- **每 10-30 章后用一次**
- 高潮转折前用一次

**功能**：
- 跨章一致性
- 伏笔追踪
- 人物弧光推进
- 时间线对齐
- 基调统一

#### `foreshadow_track.py` —— 伏笔追踪

```bash
python ai-coauthor/commands/foreshadow_track.py books/my-novel
```

**何时使用**：
- 写完一章后（检查该收未收的伏笔）
- 高潮转折前（列出待回收清单）

#### `unused_settings.py` —— 设定巡检

```bash
python ai-coauthor/commands/unused_settings.py books/my-novel
```

**何时使用**：
- 写完 10-20 章后
- 检查"已设定但未用"的角色/物品/规则

---

## 🎯 实战工作流

### 日常写作（每章）

```
1. 写 chapter-NNN.md
   ↓
2. 运行 chapter_polish.py（单章审视）
   ↓
3. 根据建议修改章节
   ↓
4. 运行 foreshadow_track.py（伏笔检查）
   ↓
5. 继续下一章
```

### 每 10-30 章

```
1. 运行 cumulative_audit.py（沉淀审核）
   ↓
2. 运行 unused_settings.py（设定巡检）
   ↓
3. 根据跨章问题修复
   ↓
4. 继续写作
```

### 高潮转折前

```
1. 运行 plan_chapter.py（章节规划）
   ↓
2. 运行 cumulative_audit.py（跨章检查）
   ↓
3. 列出"待回收伏笔清单"
   ↓
4. 开始写高潮章节
```

---

## ❓ 常见问题

### Q1：设定要填多详细？

A：**至少**要让 AI 能推断。模糊设定 = 模糊守护。

例如：
- ❌ "主角是个勇敢的人"（无法推断）
- ✅ "主角曾在战斗中替妹妹挡刀，从此无法容忍身边的人受伤"（可推断出他的行为模式）

### Q2：声音指纹必须填吗？

A：**核心 6 人以内**强烈建议填。声音指纹不填 → 对话"千人一面"。

### Q3：AI 提示冲突时，我一定要改吗？

A：**不一定要改**。AI 提供建议，你决策。

但请认真考虑警告 —— AI 比"作者本人"更容易发现设定漏洞。

### Q4：什么时候该暂停写新章，运行沉淀审核？

A：
- 每 10 章（小项目）
- 每 30 章（大项目）
- 高潮转折前
- 感觉自己"忘了之前写过什么"

### Q5：多本书可以同时管理吗？

A：**可以**。每本书独立目录，互不污染。

---

## 💡 写作心法

> "**作者主导创作，AI 辅助守护**"

- **写之前**：先填设定（设定越完整，AI 越有用）
- **写之中**：实时使用 consistency_check
- **写之后**：每章精修 + 每 10 章沉淀
- **AI 不替你决策**：AI 是助手，不是老板

---

## 📞 故障排查

### 命令报错"找不到文件"

- 检查 `books/<name>/` 目录是否存在
- 检查路径是否正确

### AI 输出"我不知道"

- 检查设定是否填写完整
- 检查提示词模板是否正确加载

### 一致性守护频繁报警

- 这是好事 —— 说明 AI 在守护
- 但要区分"真冲突"和"误报"
- 真冲突：违反设定 → 修改文章
- 误报：AI 理解错误 → 调整提示词

---

**版本**：v0.1
**最后更新**：2026-07-08
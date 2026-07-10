# Short story 系统架构设计

> **版本**：v0.1
> **日期**：2026-07-08
> **状态**：策划阶段

---

## 🎯 系统目标

构建一个**多本书的写作协作工作区**，AI 协作者能在 6 个维度上守护一致性、提醒设定、巡检全文。

### 核心价值

| 痛点 | AI 协作者解决方式 |
|------|-----------------|
| 写着写着忘了前期设定 | **一致性守护** —— 实时对照提醒 |
| 角色突然 OOC | **人物档案追踪** —— 性格、声音指纹核对 |
| 伏笔忘了兑现 | **伏笔追踪** —— 跨章自动提示 |
| 时间线混乱 | **时间线监控** —— 每章对照时间线位置 |
| 不知道设定是否用全 | **设定巡检** —— 已设定但未用的清单 |
| 不知道故事发展到哪 | **全局总览** —— 脉络图、人物关系图 |

---

## 🏗️ 系统 4 步工作流

```
┌─────────────────────────────────────────────────┐
│  Step 1：设定梳理（Setup）                        │
│  - 6 维度设定（人物/关系/世界观/物品/框架/看点）  │
│  - 4 大梳理任务                                    │
│  - 输出：完整的 6 维度设定库                       │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Step 2：内容规划（Planning）                     │
│  - 分章节大纲                                      │
│  - 人物出场 + 物品升级 + 目标校验                  │
│  - 输出：每章的规划（人/事/物）                    │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Step 3：内容生成（Generation）                   │
│  - 作者写章节 → AI 单章审视（4 大维度）          │
│  - 故事进展 / 修辞 / 引人入胜 / 违规词            │
│  - 输出：单章内容 + 审视报告 + 修改建议           │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Step 4：沉淀审核（Cumulative Audit）             │
│  - 10-30 章后统一审核                              │
│  - 4 大审核对象（文字/人物/故事/时间轴）          │
│  - 输出：跨章对齐报告                              │
└─────────────────────────────────────────────────┘
```

---

## 📐 核心架构

### 总体架构图

```
┌─────────────────────────────────────────────────────────┐
│                      作者界面                              │
│  - 设定填写 / 章节写作 / 命令调用                          │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    ai-coauthor/ 核心层                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  prompts/    │  │  commands/   │  │  logs/       │   │
│  │  提示词库    │  │  8+ 命令脚本 │  │  调用日志    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                     books/ 数据层                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  _template/  │  │  book-1/     │  │  book-2/     │   │
│  │  书模板      │  │  当前书      │  │  其他书      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   shared/ 共享层                          │
│  - writing-style.md / common-settings.md                │
└─────────────────────────────────────────────────────────┘
```

### 关键设计决策

#### 1. 文件即状态（无数据库）

- 所有设定、章节、笔记都是**普通 Markdown 文件**
- git 友好（diff/版本控制/协作）
- 作者可直接编辑
- AI 通过读取文件实现协作者

#### 2. 每本书独立子目录

- 多本书并存
- 互不污染
- 模板化复制（`_template/`）

#### 3. 系统主动推断

- 不只是"展示数据"
- 基于已有设定**计算和推断**
- 例：作者说"ch-050 主角遇到第二个盟友" → 系统推断盟友类型、建议出现时机

---

## 🔧 主要功能（10 大核心命令）

基于 4 步工作流，AI 协作者需要实现以下命令：

### Step 1：设定梳理阶段

| # | 命令 | 依据 | 功能 |
|---|------|------|------|
| 1️⃣ | `setup_consult.py` | character-network + special-setting + world-boundary | **引导式设定咨询** —— 帮助作者梳理人物/关系/世界观/物品 |
| 2️⃣ | `relationship_graph.py` | core-cast-and-grid + three-iron-laws | **人物关系图谱** —— 自动生成 Mermaid 图 + 关系矩阵 |

### Step 2：内容规划阶段

| # | 命令 | 依据 | 功能 |
|---|------|------|------|
| 3️⃣ | `plan_chapter.py` | story-timeline + protagonist-goal-obsession | **章节规划** —— 基于时间线、目标校验自动规划 |
| 4️⃣ | `item_progression.py` | special-setting | **物品升级校验** —— 检查金手指/物品升级节点是否合理 |

### Step 3：内容生成阶段（单章审视）

| # | 命令 | 依据 | 功能 |
|---|------|------|------|
| 5️⃣ | `consistency_check.py` | system-quality-guards + anti-pattern | **一致性守护** —— 对照设定/时间线/人物档案检查（防胡写） |
| 6️⃣ | `voice_print_check.py` | voice_print-modeling | **声音指纹核对** —— 对话是否符合人物性格和语料库 |
| 7️⃣ | `chapter_polish.py` | single-chapter-structure + revision-and-polishing + dialogue-writing | **章节精修** —— 开头/中间/结尾 + 修辞 + 对话 |

### Step 4：沉淀审核阶段

| # | 命令 | 依据 | 功能 |
|---|------|------|------|
| 8️⃣ | `cumulative_audit.py` | revision-and-polishing + system-quality-guards | **沉淀审核** —— 跨章对齐（10-30 章统一审核） |
| 9️⃣ | `foreshadow_track.py` | foreshadowing-and-hooks | **伏笔追踪** —— 已埋/待收/已收 三态追踪 |
| 🔟 | `unused_settings.py` | anti-pattern + world-building-expansion | **设定巡检** —— 已设定但未用的清单 |

---

## 🛡️ 4 道质量门禁（贯穿全流程）

按重要性排序：

| 优先级 | 门禁 | 触发时机 | 依据 |
|--------|------|---------|------|
| 🔴 P0 | **防胡写守护** | 实时每段 | system-quality-guards |
| 🔴 P0 | **违规词验证** | 发布前 | system-quality-guards + practical-anti-pattern |
| 🟡 P1 | **机械表达检测** | 每段 | system-quality-guards |
| 🟡 P1 | **AI 味检测** | 每章 | system-quality-guards |

**最重要的**：**防胡写守护**（用户最强调）

---

## 📂 项目目录结构

```
Short story/
├── README.md                              ← 项目说明
│
├── docs/                                  ← 项目文档
│   ├── ARCHITECTURE.md                    ← 本文件（系统架构）
│   ├── DEVELOPER_GUIDE.md                 ← 开发指南
│   ├── USER_GUIDE.md                      ← 用户使用手册
│   └── ROADMAP.md                         ← 开发路线图
│
├── ai-coauthor/                           ← AI 协作者核心
│   ├── prompts/                           ← 提示词库
│   │   ├── system-coauthor.md             ← 核心身份
│   │   └── roles/                         ← 角色化提示
│   │       ├── consistency-guard.md       ← 一致性守护者
│   │       ├── voice-guard.md             ← 声音指纹守护者
│   │       ├── structure-guard.md         ← 结构守护者
│   │       ├── tone-guard.md              ← 基调守护者
│   │       ├── foreshadow-tracker.md      ← 伏笔追踪者
│   │       └── book-auditor.md            ← 全文巡检员
│   ├── commands/                          ← 10 大核心命令
│   │   ├── setup_consult.py
│   │   ├── relationship_graph.py
│   │   ├── plan_chapter.py
│   │   ├── item_progression.py
│   │   ├── consistency_check.py
│   │   ├── voice_print_check.py
│   │   ├── chapter_polish.py
│   │   ├── cumulative_audit.py
│   │   ├── foreshadow_track.py
│   │   └── unused_settings.py
│   └── logs/                              ← 调用日志
│
├── books/                                 ← 多本书
│   ├── _template/                         ← 新书模板
│   │   ├── meta.md                        ← 书名/简介/进度
│   │   ├── settings/                      ← 6 维度设定
│   │   │   ├── 01-world.md
│   │   │   ├── 02-characters.md
│   │   │   ├── 03-framework.md
│   │   │   ├── 04-tone.md
│   │   │   ├── 05-foreshadow.md
│   │   │   └── 06-audience.md
│   │   ├── timeline.md                    ← 故事时间线
│   │   ├── voice_prints/                  ← 声音指纹库
│   │   │   └── *.md
│   │   ├── chapters/                      ← 章节目录
│   │   │   └── chapter-NNN.md
│   │   └── fragments/                     ← 素材库
│   │       ├── quotes.md
│   │       ├── inspirations.md
│   │       └── excerpts/
│   └── (其他书...)
│
├── shared/                                ← 跨书共享
│   ├── writing-style.md                   ← 通用写作风格
│   └── common-settings.md                 ← 通用设定
│
├── scripts/                               ← 工具脚本
│   └── (mmx 封装脚本等)
│
├── logs/                                  ← 全局日志
│
└── references/                            ← 引用资料
    └── (沉淀的 24 个专题副本或链接)
```

---

## 📊 数据流

### 作者与 AI 协作者的交互

```
作者输入 ─→ 命令调用 ─→ 命令读取 books/<name>/ 下文件
   ↑                              ↓
   │              ┌───────────────┴───────────────┐
   │              ↓                                ↓
   │         设定比对                          计算推断
   │              ↓                                ↓
   │              └───────────────┬────────────────┘
   │                              ↓
   │                         生成报告
   │                              ↓
   └────────────────── 反馈给作者
```

---

## 🎯 核心算法（伪代码）

### 一致性守护（consistency_check.py）

```python
class ConsistencyGuard:
    def check_new_paragraph(self, text, book_name):
        # 1. 读取该书所有设定
        settings = load_book_settings(book_name)
        # 2. 提取新段落中的"事实声明"
        claims = extract_facts(text)
        # 3. 比对设定
        issues = []
        for claim in claims:
            if contradicts(claim, settings):
                issues.append({
                    'type': '设定冲突',
                    'claim': claim,
                    'contradicting_setting': find_conflict(claim, settings),
                    'severity': 'high'
                })
        return issues
```

### 沉淀审核（cumulative_audit.py）

```python
class CumulativeAudit:
    def audit(self, book_name, recent_chapters):
        issues = []
        # 1. 跨章一致性
        issues.extend(self.cross_chapter_consistency(book_name, recent_chapters))
        # 2. 伏笔追踪
        issues.extend(self.foreshadow_tracking(book_name, recent_chapters))
        # 3. 人物弧光推进
        issues.extend(self.arc_progression(book_name, recent_chapters))
        # 4. 时间线对齐
        issues.extend(self.timeline_alignment(book_name, recent_chapters))
        # 5. 基调统一
        issues.extend(self.tone_consistency(book_name, recent_chapters))
        return issues
```

---

## 🔗 与沉淀知识的对应关系

每个核心命令都有明确的"沉淀依据"：

| 命令 | 主要依据 | 次要依据 |
|------|---------|---------|
| setup_consult | character-network + special-setting + world-boundary | voice_print-modeling |
| relationship_graph | core-cast-and-grid + three-iron-laws | character-network |
| plan_chapter | story-timeline + protagonist-goal-obsession | character-arc |
| item_progression | special-setting | story-timeline |
| consistency_check | system-quality-guards + anti-pattern | novel-writing-checklist |
| voice_print_check | voice_print-modeling + dialogue-writing | character-arc |
| chapter_polish | single-chapter-structure + revision-and-polishing | dialogue-writing |
| cumulative_audit | revision-and-polishing + system-quality-guards | top20-commonality-vs-uniqueness |
| foreshadow_track | foreshadowing-and-hooks | story-timeline |
| unused_settings | anti-pattern + world-building-expansion | special-setting |

---

## 🚦 实施阶段（按 4 步工作流）

### Phase 1：MVP（最小可用产品）
- Step 1：setup_consult（基础引导）
- Step 2：plan_chapter（基础规划）
- Step 3：consistency_check（基础守护）
- Step 4：foreshadow_track（基础追踪）

### Phase 2：完善核心功能
- 补齐 10 大命令
- 加入声音指纹
- 加入关系图

### Phase 3：高级功能
- 沉淀审核
- 设定巡检
- 数据诊断

### Phase 4：优化和扩展
- 自动化推断
- Web 界面（可选）
- 多书管理增强

详细路线图见 [ROADMAP.md](./ROADMAP.md)

---

**版本**：v0.1
**最后更新**：2026-07-08
**依赖**：所有 24 个专题沉淀 + mmx-cli（云端 AI 推理）
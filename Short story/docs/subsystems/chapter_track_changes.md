# chapter_track_changes.md — Word track changes 章节审查模式

> **决策依据**：F5（35 题压力测试锁定）+ H5（横纵向研判补遗）
> **重要性**：🟡 **重要**（MVP 简化为 track changes 数据模型；UI 在 Phase 4）
> **状态**：✅ 完整版
> **关联**：voice-print.md / quality-guards-granularity.md / content-attribution.md

---

## 🎯 系统职责

按 **Word track changes 模式**存储 AI 章节修改建议——作者可逐条 accept/reject，原文完整不被破坏。

**核心承诺**：

- ✅ AI 修改以**独立 suggestion 文件**存储，不污染原文
- ✅ 实时（writing 状态立即产生）
- ✅ 作者可逐条 accept / reject / 修改
- ✅ 接受后写入原文，suggestion 删除

---

## 📁 文件结构

```
books/<name>/chapters/
├── chapter-001.md              # 原文（作者手写，受 content-attribution 守护）
├── chapter-001-suggestions.md # AI 修改建议（track changes 模式）
├── chapter-001-facts.yaml     # 事实抽取
├── chapter-001-meta.yaml      # 章节元数据（接受 / 拒绝 / 修改统计）
├── ...
```

**目录约定**：

- 原文：`chapter-NNN.md`（git 主体）
- 建议：`chapter-NNN-suggestions.md`（git 主体，不污染原文 diff）
- 元数据：`chapter-NNN-meta.yaml`（建议统计）

---

## 📐 Suggestion 数据模型

```yaml
---
chapter: 50
generated_by: consistency_check    # 谁生成
generated_at: 2026-07-10T15:30:00
---
suggestions:
  - suggestion_id: sug_001
    type: enum [世界规则违反, 设定偏离, 人物 OOC, 伏笔遗漏, 禁说命中, 机械表达, AI 味]
    severity: enum [🔴, 🟡, 🟢]
    paragraph_ref: para_5           # 指向哪一段
    original_text_excerpt: "沈铁衣隐身进入酒馆"
    suggested_text: "沈铁衣使用道具伪装"
    reason: "隐身违反世界观规则：本界无隐身"
    state: enum [pending, accepted, rejected, modified]
    
    # 修改版本（如作者修改建议而非直接接受）
    author_modified_text: null       # 作者改了什么
    author_note: null                # 作者备注
```

## 状态生命周期

```
pending → 作者 accept → accepted → 写入原文，suggestion 删除
       → 作者 reject → rejected → 不动，suggestion 删除
       → 作者 modified → modified → 写入作者修改版，suggestion 删除
       → 关闭（章节末 / 手动 cleanup）
```

---

## ⏰ 触发时机（实时）

写作状态实时产生：

```
作者写完一段（保存段落）
   ↓
   state-detector：状态仍为 writing
   ↓
   router 立即调 consistency_check_realtime（防胡写）
   ↓
   输出 issues → 直接写入 chapter-NNN-suggestions.md
   ↓
   本段落红色虚线显示在 write.html（UI 层）
```

**关键**：suggestions.md 是**纯输出文件**，被 writing 状态保护（无云端泄露风险）。

---

## 🔌 作者操作：accept / reject / modify

### accept

```python
def accept_suggestion(chapter_n, suggestion_id):
    """接受建议，写入原文"""
    # 1. 读 chapter-NNN.md 与 chapter-NNN-suggestions.md
    # 2. 找到 paragraph_ref
    # 3. 替换 original_text_excerpt 为 suggested_text
    # 4. 标记 suggestion_state = accepted
    # 5. 写原文（注入 attribution source="author_revised"）
    # 6. 更新 chapter-NNN-meta.yaml
```

### reject

```python
def reject_suggestion(chapter_n, suggestion_id, reason=None):
    """拒绝建议，不动原文"""
    # 1. 标记 suggestion_state = rejected
    # 2. 如果有 reason → 写入 false-positive-loop
```

### modify

```python
def modify_suggestion(chapter_n, suggestion_id, author_modified_text, note=None):
    """接受但作者修改"""
    # 1. 写 author_modified_text 到原文
    # 2. 标记 suggestion_state = modified
```

---

## 📊 元数据（chapter-NNN-meta.yaml）

```yaml
---
chapter: 50
suggestion_total: 8
  - pending: 3
  - accepted: 2
  - rejected: 2
  - modified: 1
false_positive_rate: 0.25       # 2/8 被拒绝
last_cleanup: 2026-07-10T15:30:00
---
```

用于：

- cumulative_audit 中报告此章节的 AI 协作状况
- false-positive-loop 统计基础

---

## 🧹 清理机制

### 自动清理

**章节保存时**：

- 清理已 accepted / rejected / modified 的 suggestions
- pending 状态的 suggestions 保留供作者操作

```python
def cleanup_chapter_suggestions(chapter_n):
    """删除已处理的 suggestions，保留 pending"""
    suggestions = parse(f"chapter-{chapter_n}-suggestions.md")
    pending = [s for s in suggestions if s.state == "pending"]
    write(f"chapter-{chapter_n}-suggestions.md", pending)
```

### 手动清理

作者可手动 `cleanup --chapter N --force`，删除所有 suggestion。

---

## 🛡️ 守护：suggestions.md 自身

### 不能污染原文

AI 修改建议**绝对不**直接写入 chapter-NNN.md。原文由作者 + content-attribution 守护。

### 反向保护

如果 AI 想"接受自己的建议"：

- check_consistency(suggested_text, source=ai_drafted) → 豁免（自己的建议不卡自己）
- 但**原文**仍按 author_written / author_revised 守护
- 一旦 accept → source=author_revised → 完整守护

### 与 git diff 的关系

写作流的 commit：

```diff
- 沈铁衣隐身进入酒馆
+ 沈铁衣使用道具伪装进入酒馆
```

**chapter-NNN-suggestions.md** 同步变化：

- suggestion_001.state: pending → accepted
- 等下次 commit 包含

**chapter-NNN.md** 接受后：

- 段落 frontmatter 变为 `source="author_revised"`

---

## 🆚 与 git commit 快照模式的对比

| 维度 | Word track changes（本方案）| git 快照模式 |
|------|---------------------------|-------------|
| AI 修改可见性 | ✅ 实时可见 | 离线（提交后） |
| 作者控制 | ✅ 逐条 accept / reject | 全部接受或回退 |
| 原文保护 | ✅ 不污染 | AI 修改可能与原文冲突 |
| 复杂度 | 🟡 中等（双向状态）| 🟢 简单（单 commit） |
| 写章体验 | 🟢 沉浸式（看见 AI 提示）| 🟡 写完才知道 AI 意见 |
| 与 P10 配合 | 🟢 密切 | 🟢 密切 |

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| chapter-NNN-suggestions.md 存储 | ✅ | ✅ |
| 实时生成 | ✅ | ✅ |
| accept / reject / modify 命令 | ✅ | ✅ |
| 章节元数据统计 | ✅ | ✅ |
| Phase 2: write.html UI 显示 | ❌ | ✅（Phase 2-3） |
| Phase 2: 红色虚线前端展示 | ❌ | ✅（Phase 4 Web 阶段） |
| Phase 2: 自动 accept（如果 confidence > 0.95）| ❌ | ✅ |

---

## 🧪 测试用例（MVP 必过）

1. **段落保存产生 suggestion**：writing 中保存段落 → chapter-NNN-suggestions.md 新增 pending
2. **accept 写入原文**：段落"沈铁衣隐身"被替换为"沈铁衣使用道具伪装"
3. **reject 不动原文**：suggestion 标记 rejected，原文保存
4. **modify 应用作者版本**：作者修改的文本写入原文
5. **清理机制**：保存章节时清理已处理的 suggestions
6. **原文不被污染**：写作流 chapter-NNN.md 不被 AI 直接修改
7. **章节元数据正确统计**：`meta.yaml` 显示 pending/accepted/rejected/modified 计数

---

## 🔗 关联

- 子系统：`voice-print.md`（声纹禁说也用同一机制）/ `quality-guards-granularity.md`（4 道门禁都通过建议呈现）/ `content-attribution.md`（accept 后 source=author_revised）
- 决策：F5（Word track changes）+ H5（横纵向研判补遗确认）
- Web spec：`write.html` 的"红色虚线"UI 是 Phase 4

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🟡 重要（写作流的"AI 修改可见性"机制）
- **关联决策**：F5 / H5
- **关联子系统**：voice-print.md / quality-guards-granularity.md / content-attribution.md
- **关联命令**：`write`（accept/reject/modify 是其子动作）
- **关联文件**：chapter-NNN.md / chapter-NNN-suggestions.md / chapter-NNN-meta.yaml

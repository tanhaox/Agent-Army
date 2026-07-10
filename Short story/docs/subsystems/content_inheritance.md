# content_inheritance.md — 跨文件内容继承子系统

> **决策依据**：B4（横纵向研判补遗）— content_attribution.md 提及但未定义
> **重要性**：🔴 **关键**（自我审自我漏洞的修复依赖；MVP 必做）
> **状态**：✅ 完整版
> **关联**：content_attribution.md / kickoff_meeting.md / git_diff_trigger.md

---

## 🎯 系统职责

定义**章节内容如何被设定库继承**——确保 AI 起草的新设定能被检测到、被立项会复检。

**核心承诺**：

- ✅ 每章节末自动检测"本章新增/修改/删除的设定相关实体"
- ✅ 实体清单继承到 `02-characters.md` / `01-world.md` 等
- ✅ 立项会基于继承清单报告
- ✅ git_diff_trigger 也能基于继承清单

---

## 📦 "实体"的定义

继承的最小单位 = **实体**：

实体类型：

- **角色**：出现于 02-characters.md 的 character_id
- **物品**：出现于 04-special-setting.md 的 item_id
- **规则**：出现于 01-world.md 的 rule_id（隐身规则 / 修仙界规则）
- **关系**：出现于 02-characters.md §人物关系 的 relation_pair
- **目标**：出现于 03-framework.md 的 goal_id

每个实体有 **稳定 ID**：

```yaml
# 02-characters.md 节选
characters:
  - id: protagonist           # 角色 ID
    name: 沈铁衣
    ...
items_in_chapter:
  - invisible_ability        # 这个"隐身能力"也作为实体
```

---

## 🔍 自动检测

每章保存时（write.html 保存章节）：

```
chapter_save()
  ↓
扫描 chapter-NNN-facts.yaml
  ↓
  匹配已知实体 ID / 名称（在 settings/02-characters.md + 04-special-setting.md 已有列表中查找）
  ↓
  匹配**新实体**（不在已知列表）：
    - 抽取实体名、类型、attributes
    - 写入 chapter-NNN-inheritance.yaml
  ↓
  通知作者："本章新增 X 个实体，请审改"
```

新实体的判定：

- 名称首次出现
- 类型通过上下文识别（"主角获得"、"金手指"、"新规"）
- 不在当前 setting 文件

---

## 📐 数据模型

### `books/<name>/chapters/chapter-NNN-inheritance.yaml`

```yaml
---
chapter: 50
generated_at: 2026-07-10T15:30:00
extracted_from: chapter-NNN-facts.yaml
status: pending  # pending | confirmed | rejected
author_revised: 0
---
new_entities:
  - entity_id: ent_001
    type: 角色
    proposed_name: 神秘女子
    context: "主角在第 50 章酒楼遇到的女子"
    attributes:
      age_estimate: 25
      relationship_to_protagonist: 未定
    suggested_section: 02-characters.md  # 建议挂到哪个文件
    confidence: 0.85
new_rules:
  - rule_id: rule_001
    description: "本界无隐身术"
    context: "主角被发现隐身 → 反派察觉"
    suggested_section: 01-world.md
    confidence: 0.92
new_items:
  - item_id: item_001
    proposed_name: 古籍
    context: "师父赠主角"
    suggested_section: 04-special-setting.md
    confidence: 0.95
new_relationships:
  - relation_id: rel_001
    between: [protagonist, ent_001]
    type: encounter
    context: "初次相遇"
    suggested_section: 02-characters.md
```

### 状态生命周期

```
pending → 作者 confirm → 写入 settings/*.md + chapter-NNN-inheritance.yaml 删除该 entity
       → 作者 reject → 不写入，entity 标记 rejected（仅记录到 false_positive_loop）
       → 编辑后再次扫描：作者可以手动改 chapter-NNN-inheritance.yaml
```

---

## 🔄 与 kickoff_meeting / git_diff_trigger 的协同

### kickoff_meeting 复检

立项会读取所有 `chapter-NNN-inheritance.yaml`（pending）：

```
kickoff_meeting start
   ↓
   加载所有 pending entities
   ↓
   multi-agent 检测：新实体是否与既有设定冲突？
   ↓
   输出到 issues：
     - 🟠 必须修复：新实体与 02-characters.md 主角冲突
     - 🔴 硬否决：新实体（隐身能力）违反 01-world.md 规则
   ↓
   作者 confirm / reject → 清空 inheritance.yaml
```

### git_diff_trigger

git diff 也包括 `chapter-NNN-inheritance.yaml`：

```
git diff 触发
   ↓
   level 1: git grep 检测 inheritance.yaml 关键词
   ↓
   level 2: AI 语义判断 —— 修改是否影响核心设定
   ↓
   🔴 核心变更 → 触发 kickoff_meeting (increment)
```

---

## 📁 文件位置

```
books/<name>/chapters/
├── chapter-001.md
├── chapter-001-facts.yaml          # 客观事实（不区分新/旧）
├── chapter-001-inheritance.yaml   # 跨文件继承候选
├── chapter-001-suggestions.md     # AI 修改建议（track changes）
├── chapter-001-meta.yaml           # 章节元数据
```

---

## 🔌 实现

### detection 算法

```python
def detect_new_entities(chapter_text, chapter_n, book_name):
    """扫描新实体"""
    facts = load(f"chapter-{chapter_n}-facts.yaml")
    known_chars = load_book_characters(book_name)  # 02-characters.md
    known_items = load_book_items(book_name)
    known_rules = load_book_rules(book_name)
    
    new_entities = []
    for fact in facts.facts:
        # 已知实体跳过
        if fact.subject in known_chars: continue
        if fact.object in [item.name for item in known_items]: continue
        # 新实体 → 抽取候选
        new_entities.append(propose_entity(fact, chapter_n))
    
    return new_entities
```

### 触发时机

写作时**离线**抽取（保存章节后立即）：

```
chapter 保存完成
   ↓
   facts_extraction → chapter-NNN-facts.yaml
   ↓
   同时 detect_new_entities → chapter-NNN-inheritance.yaml
```

---

## 🛡️ 与自我审自我的关系

content_attribution.md §防"自己审自己" 漏洞：

> 漏洞：AI 起草金手指 隐身能力 → settings 没填 → 守护豁免 → 漏检
> 缓解：1. 立项会必看 2. 继承关系 3. 云端协同

**这次继承关系终于有了具体实现**：

- chapter-NNN-inheritance.yaml 让**所有新实体候选**被记录在案
- 立项会基于 inheritance.yaml 复检
- 即使 ai_drafted 段落被防胡写豁免，**新实体仍触发立项会**

---

## 🧪 测试用例（MVP 必过）

### detection

1. **新角色**：主角遇到"神秘女子" → inheritance.yaml 新增 entity
2. **新物品**：主角获得"古籍" → inheritance.yaml 新增 item
3. **新规则**：世界观出现"无隐身术" → inheritance.yaml 新增 rule
4. **已知实体**：主角已经在 02-characters.md → 不重复
5. **空章节**：facts 空 → inheritance.yaml 空

### 协同

6. **继承在立项会被复检**：pending entity 触发立项会 issue
7. **作者 confirm**：写入 settings/02-characters.md + inheritance.yaml 删除该 entity
8. **作者 reject**：entity 不写入 + 记录 false_positive_loop

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| chapter-NNN-inheritance.yaml | ✅ | ✅ |
| 自动 detect_new_entities | ✅ | ✅ |
| 5 类实体（角色 / 物品 / 规则 / 关系 / 目标）| ✅ | ✅ |
| 立项会复检 | ✅ | ✅ |
| git_diff_trigger 协同 | ✅ | ✅ |
| Phase 2: 跨章继承一致性（实体 ID 全局唯一）| ❌ | ✅ |
| Phase 2: 自动 confirm（高 confidence）| ❌ | ✅ |

---

## 🔗 关联

- 子系统：`content_attribution.md`（自我审自我漏洞的修复路径）/ `kickoff_meeting.md`（复检 inheritance.yaml）/ `git_diff_trigger.md`（新增实体也触发 diff）
- 决策：B4（横纵向研判补遗）+ F6（内容出处豁免的反向）

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键（自我审自我漏洞的修复）
- **关联决策**：B4 / F6
- **关联子系统**：content_attribution / kickoff_meeting / git_diff_trigger
- **关联命令**：write（保存章节后触发）
- **关联文件**：chapter-NNN-inheritance.yaml

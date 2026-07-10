# facts-extraction.md — 事实抽取子系统

> **决策依据**：F7（35 题压力测试锁定）/ V2（横纵向研判补遗）
> **重要性**：🔴 **关键**（`cumulative_audit` MVP 6 命令的算法核心）
> **状态**：✅ 完整版
> **关联**：cumulative_audit / gantt-audit.md / state-detector.md / router.md

---

## 🎯 系统职责

**每章节末保存时**，自动抽取该章的 15-20 条"客观事实"，写入 `chapter-NNN-facts.yaml`。

`cumulative_audit` 等命令**不再读原文**，只读 facts.yaml，节省 token 预算。

**目的**：把"事实"从"原文"中分离，让后续跨章审核可走事实层（不必每次都重读全文）。

---

## 📋 "事实"的定义

### 客观事件

> 客观陈述，事件级别，**不依赖主观解读**。

✅ **是事实**：

- "主角获得古籍"
- "主角在第 5 章与反派首次交锋"
- "盟主叛变"

❌ **不是事实**：

- "主角很帅"（主观）
- "作者想表达孤独"（元叙事）
- "本章节奏快"（感受）

### 抽取后的事实粒度

**15-20 条 / 章节**（V2.1 锁定）。这意味着：

- 短章节（2000 字）：12-15 条
- 中章节（4000 字）：15-18 条
- 长章节（6000+ 字）：18-22 条

每条事实包含：

```yaml
- event_id: f1
  type: 战斗 | 修炼 | 结识 | 领悟 | 失去 | 旅行 | 获得 | 揭露 | 决裂 | 调和 | ...
  subject: 主角
  object: 反派
  chapter: 50
  excerpt: "主角与反派首次交锋，险胜"
  importance: P0 | P1 | P2
```

**与"伏笔事件"的关系**：

- 事实库 ≠ 伏笔库
- 伏笔是"作者标注的隐含事件"（foreshadow-half-loop.md）
- 事实库是"客观陈述"
- 二者可联动：facts 中标记"埋下古籍"→ 提醒作者是否要标注伏笔

---

## ⏰ 触发时机（V2.2 锁定）

**章节保存时立即抽取**：

```
作者在 write.html 保存章节 → web 触发 `extract_facts(chapter_path)`
                                ↓
                       state-detector 自动 release writing.lock
                                ↓
                       router 调用 Ollama 做事实抽取（V2.3' 队列顺序）
                                ↓
                       写 chapter-NNN-facts.yaml
                                ↓
                       主流程继续
```

### 串行队列顺序（V2.3' 锁定 A 方案）

保存章节后：

```
保存事件触发：
├─ state-detector.release(writing.lock)        ← 释放 writing
├─ OLLAMA_QUEUE.consistency_check()          ← 防胡写复检（如有）
├─ OLLAMA_QUEUE.facts_extract()              ← 事实抽取（新增）
└─ OLLAMA_QUEUE.voice_check()                ← 声纹复检（如有）
```

**关键约束**：所有推理任务**串行**加入 OLLAMA_QUEUE，Ollama 实例**同时只跑一个**——避免单实例多任务并发崩溃。

### 串行延迟影响

- 1 推理任务：1-3 秒（Ollama 本地）
- 3 推理任务串行：3-9 秒
- 这是**保存后**的延迟，作者不会感到卡顿（保存操作本身已 async）

---

## 🤖 抽取算法

### Ollama 抽取（默认）

```python
def extract_facts(chapter_text, chapter_num, book_name):
    prompt = f"""
请抽取本章（{book_name} 第 {chapter_num} 章）的客观事实：

【要求】
1. 15-20 条
2. 客观陈述，不带主观
3. 包含事件、人物、地点、物品变化
4. 每条简明（不超过 30 字）

【章节正文】
{chapter_text}

【输出格式】（YAML）
```yaml
- event_id: f1
  type: <事件类型>
  subject: <主语>
  object: <宾语，可选>
  chapter: {chapter_num}
  excerpt: <原文 30 字内>
  importance: <P0 | P1 | P2>
```
"""
    return ollama.infer(prompt, persona='facts_extractor')
```

### 规则脚本补充（fallback）

如果 Ollama **3 次重试仍失败**，自动 fallback 到**轻量级规则脚本**：

```python
def extract_facts_rule_based(chapter_text):
    """无 AI 的规则抽取，0 延迟但精度低"""
    facts = []
    # 1. 检测"X 获得 Y" 模式
    for match in re.finditer(r'(.+?)获得(.+)', chapter_text):
        facts.append({
            "type": "获得",
            "subject": match.group(1),
            "object": match.group(2).strip(),
            "importance": "P1",
        })
    # 2. 检测"X 与 Y 战斗/对决/争吵"
    for match in re.finditer(r'(.+?)(?:与|和)(.+?)(?:战斗|对决|争吵|冲突)', chapter_text):
        facts.append({
            "type": "战斗",
            "subject": match.group(1),
            "object": match.group(2),
            "importance": "P0",
        })
    # 3. ... 8-10 个模式
    return facts[:10]  # 最多 10 条 fallback
```

**fallback 标记**：`chapter-NNN-facts.yaml` 含 `extracted_by: ollama | rule_based`。

---

## 📐 数据模型

### `books/<name>/chapters/chapter-NNN-facts.yaml`

```yaml
---
chapter: 50
extracted_by: ollama           # ollama | rule_based
extracted_at: 2026-07-10T15:30:00
author_revised: 0              # 作者审改次数
fact_count: 17
complete: true                 # 是否完成抽取（Ollama 失败时为 false）
---
facts:
  - event_id: f1
    type: 战斗
    subject: 主角
    object: 反派
    chapter: 50
    excerpt: "主角与反派首次交锋"
    importance: P0
  - event_id: f2
    type: 获得
    subject: 主角
    object: 古籍
    chapter: 50
    excerpt: "师父遗下古籍"
    importance: P0
  # ... 15-20 条
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|------|------|
| `chapter` | ✅ | 章节号 |
| `extracted_by` | ✅ | ollama / rule_based |
| `extracted_at` | ✅ | 抽取时间 |
| `author_revised` | ✅ | 作者修订次数（0 = 未修订） |
| `fact_count` | ✅ | 实际抽到的事实数 |
| `complete` | ✅ | true / false（Ollama 失败时 false） |
| `facts[].event_id` | ✅ | f1, f2, ... |
| `facts[].type` | ✅ | 战斗/修炼/结识/... |
| `facts[].subject` | ✅ | 主语 |
| `facts[].object` | ❌ | 宾语（可选） |
| `facts[].chapter` | ✅ | 同 chapter |
| `facts[].excerpt` | ✅ | 原文 ≤ 30 字 |
| `facts[].importance` | ✅ | P0 / P1 / P2 |

### `complete: false` 的语义

- Ollama 提取失败 → fallback 规则脚本
- 标记 `complete: false` → cumulative_audit 给出警告"本章事实不完整"
- 作者可手动补全（更新 yaml + author_revised += 1）

---

## 📁 存储位置

```
books/<name>/chapters/
├── chapter-001.md         # 原文
├── chapter-001-facts.yaml # 事实
├── chapter-002.md
├── chapter-002-facts.yaml
└── ...
```

事实文件与原文**平行存放**，便于管理和阅读。

---

## 🔌 与 cumulative_audit 的协同

### cumulative_audit 工作流（修订）

```
cumulative_audit 触发（每 10 章）
   ↓
读取 chapters/030-039-facts.yaml（共 10 个文件）
   ↓
按 6+ 泳池分类：
   - 伏笔泳池 → 引用 facts 中"埋下 / 回收"事件
   - 人物弧光 → facts.subject 聚合（主角的轨迹）
   - 物品升级 → facts 中"获得/损失"类型
   - 世界观 → facts 中涉及规则的事件
   - 看点 → facts.importance=P0 + 排列密度
   - 关系 → facts 中"结盟 / 决裂"
   ↓
汇成 gantt-audit.md
```

**关键**：cumulative_audit **不再读原文**，只看 facts.yaml——token 预算大幅下降。

### Token 预算对比

| 任务 | 读 facts 路径 | 读原文路径 |
|------|--------------|-----------|
| 10 章事实统计 | 10 × 2k = 20k | 10 × 4k = 40k |
| 30 章事实统计 | 30 × 2k = 60k | 30 × 4k = 120k |
| 节省 | **50%** | — |

---

## 🚨 V2.3' 串行队列约束（已经预留）

### OLLAMA_QUEUE 设计

```python
# Ollama 实例是单进程单队列
OLLAMA_QUEUE = []  # FIFO 任务队列
OLLAMA_RUNNING = False

def enqueue(task_name, payload):
    """Ollama 任务入队"""
    OLLAMA_QUEUE.append((task_name, payload))
    if not OLLAMA_RUNNING:
        run_next()

def run_next():
    global OLLAMA_RUNNING
    if not OLLAMA_QUEUE:
        OLLAMA_RUNNING = False
        return
    OLLAMA_RUNNING = True
    task_name, payload = OLLAMA_QUEUE.pop(0)
    try:
        result = ollama.infer(payload)
        process_result(task_name, result)
    finally:
        run_next()
```

**所有 Ollama 推理必须走此队列**——避免并发崩溃。

---

## 🔁 作者审改事实

作者可手动编辑 `chapter-NNN-facts.yaml`：

```bash
# CLI 命令
python -m ai_coauthor facts --edit --chapter 50 --book <name>

# 打开编辑器，事实 yaml 修改后
python -m ai_coauthor facts --confirm --chapter 50 --book <name>
# → author_revised += 1
# → meta.md 中的 fact_revision = N
```

作者可：
- 添加漏掉的事实
- 删除错误事实
- 修正 importance
- 重新分类

事实的"权威性" = Ollama 抽取 + 作者审改。Author has final say。

---

## 🧪 测试用例（MVP 必过）

### 抽取

1. **保存章节 → 自动抽取**：写入 `chapter-001-facts.yaml`，15-20 条
2. **保存抽不出**（Ollama 挂了）→ fallback 规则脚本 + `complete: false`
3. **作者手动审改** → `author_revised: 1`

### 协同

4. **cumulative_audit 读事实库**：10 章 facts → 6 泳池报告
5. **累积 30 章审计**：30 章 facts → 完整 gantt-audit
6. **缺 facts 章节** → cumulative_audit 警告"本章事实缺失"

### 串行队列

7. **保存章节后** 3 个 Ollama 任务串行执行
8. **并发触发** → 队列保证单实例

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| 保存即抽 Ollama | ✅ | ✅ |
| 15-20 条 | ✅ | ✅ |
| 规则 fallback | ✅ | ✅ |
| YAML 存储 | ✅ | ✅ |
| 作者审改 | ✅ | ✅ |
| 与 cumulative_audit 协同 | ✅ | ✅ |
| 类型自动分类（语义） | ❌ | ✅（Phase 2 增强 prompt） |
| 跨章事实序列追踪 | ❌ | ✅ |
| 事实可视化 | ❌ | ✅（Phase 4 Web）|

---

## 🔗 关联

- `gantt-audit.md §触发` —— cumulative_audit 读 facts
- `state-detector.md §退出触发` —— 串行调用
- `router.md §二任务类型路由` —— "facts_extract" 任务注册到 OLLAMA_QUEUE
- `cumulative_audit.py` MVP 6 命令之一
- `quality-guards-granularity.md §三 机械表达` —— 复杂度可复用

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键（`cumulative_audit` 算法核心）
- **关联决策**：F7 / V2（横纵向研判补遗）
- **关联子系统**：gantt-audit.md / state-detector.md / router.md / content-attribution.md
- **关联命令**：cumulative_audit.py（MVP 6 命令之一）
- **关联文件**：books/<name>/chapters/chapter-NNN-facts.yaml

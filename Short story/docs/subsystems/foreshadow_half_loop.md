# foreshadow-half-loop.md — 伏笔半自动闭环子系统

> **决策依据**：P11 / F2 / F3 / F4 / F8 / 001-v2-foreshadow-tracking.md
> **重要性**：🔴 **关键**（MVP 必做的 6 命令之一：`foreshadow_track`）
> **状态**：✅ 完整版（领域总览型，含误报反馈联动）
> **关联**：gantt-audit.md（每 10 章巡检）/ false-positive-loop.md（误报反馈）/ multi-agent-cloud.md（多 Agent 提议伏笔）/ kickoff-meeting.md（增量模式）

---

## 🎯 系统职责

让作者**完整掌控**伏笔创建 / 回收，同时让 AI 在合适时机给出**有依据的回收候选建议**。

**核心**：**半自动闭环**——AI 提议 → 作者接受 / 拒绝 → 误报反馈回训练。

> v1 决策 001（已废弃）："AI 自动检测 = 否决"
> v2 决策 001（当前）："AI 提议回收候选 = 接受 / 拒绝 / 反馈训练"

---

## 📋 4 个核心能力

| # | 能力 | AI 做 | 作者做 |
|---|------|------|------|
| 1 | **埋入伏笔** | ❌ AI 不扫原文 | ✅ 手动 📌 标注 / 时间线设计 / 人物设计 |
| 2 | **AI 提议** | ✅ 设定打磨时主动提议 | ✅ 接受 / 拒绝 / 改写 |
| 3 | **回收候选** | ✅ 每章末列出"该回收的伏笔" | ✅ 确认回收 / 调整章节 / 忽略 |
| 4 | **误报反馈** | ✅ 自动记录 + 阈值调整 | ✅ 拒绝时添加原因 |

---

## 📐 三态模型

```
🟢 已埋 (buried) ──→ 🟡 待收 (pending) ──→ 🔵 已收 (resolved)
                       ↑
                       │ 超过 chapter_due
                       ↓
                    🔴 过期 (overdue)
```

| 状态 | 含义 | 数据来源 |
|------|------|---------|
| 🟢 已埋 | 作者手标或 AI 提议接受；章节中标注 📌 | `05-foreshadow.md` |
| 🟡 待收 | 已埋但未回收；接近 chapter_due 触发回收建议 | 同上 |
| 🔵 已收 | 已在某章回收；记录"回收章节 + 摘要" | `chapters/chapter-NNN.md` + `05-foreshadow.md` |
| 🔴 过期 | 超过 chapter_due 但未标已收 | 派生状态（自动算） |

---

## 📐 三种一级分类

| 分类 | 子类 |
|------|------|
| 👤 **人** | ⬆️ 出场 / ⬇️ 退场 |
| 📅 **事** | ✅ 好事 / ❌ 坏事 |
| 🎁 **物** | ⬇️ 获得 / ⬆️ 损失 |

### 双重层级（可叠加）

| 层级 | 含义 |
|------|------|
| 📈 L1 推动 | 推动主线 |
| 🔄 L2 转折 | 造成反转 |

**例**：一个伏笔既是 L1 推动（主线）也是 L2 转折（揭示反派身世）→ **L1 + L2 双层叠加**。

---

## 🛠️ 4 个创建入口

| # | 入口 | 触发场景 | 数据流 |
|---|------|---------|--------|
| 1 | **写作时画线标注** | 作者在 write.html 写正文时标 📌 | 写作时立刻写入 `chapters/*.md` |
| 2 | **时间线预埋** | timeline.html 主动添加"未来伏笔" | 写入 `timeline.md` 伏笔段 |
| 3 | **人物设计预埋** | character-profile.html 添加伴随事件 | 写入 `02-characters.md` |
| 4 | **AI 提议（v2 新增）** | 设定打磨（多 Agent 设定会）时 AI 主动提议 | 由 kickoff_meeting / 打磨调用 |

### AI 提议的详细算法（v2 关键）

```python
def ai_propose_foreshadows(settings, characters, current_chapter=0):
    """AI 提议伏笔候选"""
    prompt = f"""
请基于以下设定，**提议**该书可能需要预埋的伏笔：

【设定摘要】
{settings.summary}

【已埋伏笔】
{foreshadows.list()}

【当前进度】
第 {current_chapter} 章

输出：3-5 条"建议预埋"——每条说明为什么（剧情 / 人物 / 世界观）。
注意：这是**建议**，不是必须。
"""
    return ollama.infer(prompt, persona='foreshadow_proposer')
```

**重要**：AI 只提议，**绝不**写入伏笔库。这是与 v1 决策的关键差异。

---

## 🤖 AI 的 3 项主动能力

### 能力 1：回收候选建议（每章末，F4）

```python
def foreshadow_track(chapter_n, foreshadows):
    """列出本章应回收的伏笔 + 已埋伏笔库"""
    candidates = []
    for f in foreshadows.list():
        # 接近 chapter_due → 提醒
        if f.chapter_due is not None and chapter_n >= f.chapter_due - 5:
            candidates.append({
                "id": f.id,
                "title": f.title,
                "type": f.type,
                "chapter_due": f.chapter_due,
                "urgency": "🔴 overdue" if chapter_n > f.chapter_due else "🟡 approaching",
                "summary": f.summary,
            })
    return candidates
```

**触发**：每章末自动执行（F4 决策）。

### 能力 2：密度检查（章节末）

```python
def foreshadow_density_check(chapter, foreshadows):
    """检查本章是否埋过多伏笔（回收风险）"""
    buried_in_chapter = [f for f in foreshadows if f.chapter_buried == chapter.number]
    if len(buried_in_chapter) > 3:  # 阈值
        return {
            "warning": "🔴",
            "type": "density_overload",
            "count": len(buried_in_chapter),
            "suggestion": "考虑推迟其中一些伏笔的埋入时机",
        }
    return None
```

### 能力 3：过期警告（每 10 章巡检）

```python
def foreshadow_overdue_report(foreshadows, current_chapter):
    """列出所有过期伏笔"""
    return [
        {"id": f.id, "title": f.title, "due": f.chapter_due, "overdue_by": current_chapter - f.chapter_due}
        for f in foreshadows
        if f.chapter_due is not None and current_chapter > f.chapter_due and f.chapter_resolved is None
    ]
```

**触发**：每 10 章触发 `cumulative_audit` 时，作为甘特图泳池之一（gantt-audit.md）。

---

## 🔄 半自动闭环（F3）

```
foreshadows.list() ──→ chapter 末扫
                        ↓
              列出"该回收"候选 (candidates)
                        ↓
               作者检查
                ↓              ↓
        接受（在某章回收）   拒绝（误报）
                ↓              ↓
       章节标记回收事件   false-positive-loop 记录
        state=已收            ↓
                         阈值调整
                         （防"AI 学坏"）
```

### 接受路径

```python
# 在 chapter-NNN.md 中标注回收事件
<!-- @attribution source="author_written" -->
[章节内容]

## 本章伏笔事件
- ✅ 收：foreshadow_001（古籍）
- ➕ 埋：foreshadow_007（新伏笔）
```

自动同步 `05-foreshadow.md`：foreshadow_001 state = 已收，chapter_resolved = NNN。

### 拒绝路径（误报反馈）

```python
# 作者点忽略候选
{
    "candidate_id": "foreshadow_005",
    "candidate_title": "玉佩",
    "decision": "reject",
    "reason": "实际不是伏笔，只是普通物品",
    "writer": "author",
    "ts": "2026-07-10T15:00:00"
}
# 记录到 logs/false_positives.log → false-positive-loop 处理
```

详见 `false-positive-loop.md`。

---

## ⚠️ AI 不能做的事（v1 否决原则的延伸）

- ❌ 扫原文自动检测"这里有伏笔"（v1 否决）
- ❌ 不经作者同意写入伏笔库
- ❌ 把伏笔标为已收（必须作者手动）
- ❌ 强制作者接受回收候选

---

## 📐 数据模型

### `books/<name>/settings/05-foreshadow.md`（全局伏笔库）

```yaml
foreshadows:
  - id: foreshadow_001
    title: 古籍
    type: 物-获得              # 人/事/物 + 子类
    level: L1                  # L1 推动 / L2 转折
    state: 待收                  # 已埋/待收/已收/过期（过期是派生）
    chapter_buried: 5
    chapter_due: 50             # 作者主动设定回收章
    chapter_resolved: null
    summary: "第 5 章主角师父遗留古籍给主角，预示主线"
    ai_suggestion_status: pending  # AI 提议后：pending | accepted | rejected
    source_entry: 写作时画线      # 创作入口
    created_by: author          # author | ai_proposal
```

### `books/<name>/chapters/chapter-NNN.md`（章节内伏笔事件）

```markdown
<!-- @attribution source="author_written" -->

[章节内容]

## 本章伏笔事件
- ➕ 埋：foreshadow_001（古籍）
- ➕ 埋：foreshadow_002（神秘女子）
- ✅ 收：foreshadow_005（玉佩）
```

**自动同步规则**：

- 检测到章节内的伏笔事件 → 自动更新 `05-foreshadow.md`
- 不依赖 AI（git diff 检测即可）

---

## 🔗 与误报反馈的协同（false-positive-loop.md）

### 误报类型

| 误报类型 | 触发场景 |
|---------|---------|
| **过期警告误报** | AI 判定过期，但作者说"这伏笔我就打算晚回收" |
| **密度误报** | AI 判定密度过高，但作者说"这一章就是埋伏笔密集章节" |
| **回收候选误报** | AI 列出的"该回收"，作者说"还没到时机" |

### 误报反馈路径

```
作者 reject 候选 → logs/false_positives.log 记录
   ↓
每 10 章统计（gantt-audit 中触发）
   ↓
false-positive-loop Layer 2：分类 + 计算 ignore_rate
   ↓
ignore_rate > 50% → Layer 3：阈值调整（warning 阈值上调 / 接受延迟）
```

详见 `false-positive-loop.md` §三层闭环。

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| 三态模型 | ✅ | ✅ |
| 三级分类（人/事/物） | ✅ | ✅ |
| 双层叠加（L1 + L2） | ✅ | ✅ |
| 4 个创建入口 | ✅ | ✅ |
| AI 提议接口 | ✅（仅接口，AI 派生 MVP 暂简化为手动填）| ✅ 增强 |
| 章节末回收候选 | ✅ | ✅ |
| 密度检查 | ✅ | ✅ |
| 过期警告（每 10 章） | ✅ | ✅ |
| 误报反馈 Layer 1 + 2 | ✅ | ✅ |
| 误报反馈 Layer 3 自动调 | ❌ | ✅ |
| 伏笔可视化 | ❌ | ✅（Phase 4 Web 甘特图）|

---

## 🧪 测试用例（MVP 必过）

### 基础三态

1. **作者手标埋入**：写入 05-foreshadow.md → state=已埋
2. **状态转换**：作者标回收 → state=已收
3. **过期检测**：chapter_due=50，当前=60 → 🔴 警告

### AI 提议（v2 关键）

4. **设定打磨时 AI 提议**：跑 multi-agent 打磨 → 产出 3-5 条伏笔候选 → 不写入库
5. **作者接受**：作者接受候选 → 写入 05-foreshadow.md，`created_by=ai_proposal`，`ai_suggestion_status=accepted`
6. **作者拒绝**：候选被 reject → 写入 logs/false_positives.log

### 每章末扫描

7. **接近 chapter_due 提醒**：foreshadow_001 chapter_due=50，当前 48 → 🟡 提醒
8. **过期警告**：chapter=60 但 foreshadow_001 chapter_due=50 → 🔴 警告
9. **密度检查**：本章埋 4 个伏笔 → 🔴 警告"密度过高"

### 误报反馈

10. **拒绝候选 → 日志**：作者拒绝 → false-positive-loop 记录
11. **统计触发**：累计 10 条 reject → 计算 ignore_rate
12. **阈值调整**：ignore_rate > 50% → Layer 3 调整

---

## 🔌 接口（命令：`foreshadow_track`）

### CLI 命令

```bash
# 列出当前所有伏笔
python -m ai_coauthor foreshadow_track --list --book <name>

# 列出本章应回收的候选
python -m ai_coauthor foreshadow_track --candidates --chapter N --book <name>

# AI 提议（reviewing 状态）
python -m ai_coauthor foreshadow_track --propose --book <name>

# 接受/拒绝候选
python -m ai_coauthor foreshadow_track --accept <id> --book <name>
python -m ai_coauthor foreshadow_track --reject <id> --reason "..." --book <name>

# 标记已收
python -m ai_coauthor foreshadow_track --resolve <id> --chapter N --book <name>
```

### 数据库与查询接口

```python
def foreshadow_track(
    action: str,        # list | candidates | propose | accept | reject | resolve
    book_name: str,
    chapter_n: int = None,
    foreshadow_id: str = None,
    reason: str = None,
) -> dict:
    """统一接口，所有动作经此"""
```

### 与路由器交互

| 动作 | 状态 | 任务类型 |
|------|------|---------|
| list | reviewing | local（纯文件） |
| candidates | reviewing | local（计算本地派生） |
| propose | reviewing | **cloud**（多 Agent 提议） |
| accept | reviewing | local（写入文件） |
| reject | reviewing | local（写入日志） |
| resolve | writing | local（即时） |

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键
- **关联决策**：P11 / F2-F4 / F8 / 001-v2
- **关联子系统**：gantt-audit.md / false-positive-loop.md / multi-agent-cloud.md / kickoff-meeting.md
- **关联命令**：foreshadow_track.py（MVP 6 命令之一）
- **关联算法**：R3 git diff 用于作者审改的伏笔状态自动转换

# 001-v2-foreshadow-tracking.md — 伏笔追踪设计（v2）

> **历史**：原 `001-foreshadow-tracking.md` 在 35 题压力测试中被反转
> **反转依据**：F3（半自动闭环）
> **v2 依据**：P11 + F2 + F3 + F4 + F8 + Q6-Q8, Q12, Q20
> **状态**：✅ 当前活跃决策

---

## 🎯 设计目标

让作者**完整掌控**伏笔，但又让 AI 在伏笔回收时给出**有依据的提示**。

---

## ✅ 锁定的设计（v2 取代 v1）

### 1. 三态模型（继承 v1）

伏笔的状态：

- 🟢 **已埋**（buried）—— 作者在章节中标注 📌，或 AI 在时间线/人物设计中预埋
- 🟡 **待收**（pending）—— 已埋但未回收，超过回收章节则变红
- 🔵 **已收**（resolved）—— 明确回收完成（标记章节 + 摘要）

### 2. 三种一级分类（继承 v1）

- 👤 **人**：⬆️ 出场 / ⬇️ 退场
- 📅 **事**：✅ 好事 / ❌ 坏事
- 🎁 **物**：⬇️ 获得 / ⬆️ 损失

### 3. 双重层级（继承 v1）

- 📈 **L1 推动**：推动主线
- 🔄 **L2 转折**：造成反转

### 4. **半自动闭环（v2 新增，反转 v1）**

#### v1 反转说明

- v1 说："AI 自动检测 → 否决（误报率高）"
- v2 改为："AI 提议 → 作者接受/拒绝 → 误报反馈回训练"

#### AI 只做"回收候选建议"

- AI **不**扫原文自动检测"这里有伏笔"（v1 否决的）
- AI **只**做已埋伏笔的"该回收提示"，作者已埋伏笔 → AI 提醒作者："第 N 章是你的回收期限，快到了"

#### 误报反馈（P2 / false_positive_loop）

- AI 误报 → 作者忽略 → 记录 → 阈值调整

#### MVP 收益

- 不破坏作者主控
- 大幅降低伏笔遗忘概率
- 通过反馈循环逐步降低误报率

---

## 🎨 创建入口（继承 v1）

仍保留 v1 的 3 个入口：

1. **写作时画线标注**：write.html 📌 按钮（v1 设计）
2. **时间线设计预埋**：timeline.html + 添加伏笔入口
3. **人物设计预埋**：character-profile + 伴随事件

### v2 新增：AI 提议入口

4. **AI 提议**：设定打磨时，AI 主动提议"这里适合埋伏笔" → 作者可一键接受 + 📌 标注（写入 frontmatter）

---

## 🔍 AI 在伏笔中的新角色

AI 提供 3 类主动能力：

| 能力 | AI 能做什么 | 触发时机 |
|------|------------|---------|
| **回收候选建议** | 按已埋伏笔 + target_chapter 排程提醒 | 每章末（F4） |
| **密度检查** | 检查当前章节是否埋过多伏笔（避免回收风险） | 章节末 |
| **过期警告** | 已超过 target_chapter 但未标记 resolved 的伏笔 | 每 10 章巡检（P11 甘特图泳池） |

AI **不能**做：

- ❌ 自动扫原文"这里有伏笔"
- ❌ 自动把伏笔标为已收（必须作者手动）

---

## 📐 数据模型

`books/<name>/settings/05-foreshadow.md`：

```yaml
foreshadows:
  - id: foreshadow_001
    title: 古籍
    type: 物-获得
    level: L1-推动
    state: 待收
    chapter_buried: 5
    chapter_due: 50
    chapter_resolved: null
    summary: "第 5 章主角师父遗留古籍给主角，预示主线"
    ai_suggestion_status: pending  # pending | accepted | rejected
```

每章 `chapters/chapter-NNN.md`：

```markdown
<!-- @attribution source="author_written" -->

[章节内容]

## 本章伏笔事件
- ➕ 埋：foreshadow_001（古籍）
- ✅ 收：foreshadow_005（玉佩）
```

---

## 🧪 测试用例（MVP 必过）

1. **作者手动埋**：写入 05-foreshadow.md → 状态 buried
2. **AI 提议**：打磨时 AI 提"这里适合埋伏笔" → 作者接受 → 加入 05-foreshadow.md
3. **每章末扫描**：F4 → AI 列出该章的伏笔事件
4. **过期警告**：超过 chapter_due 未 resolved → 警告
5. **状态转换**：作者标记 resolved → 状态变 resolved
6. **半自动闭环**：AI 推荐回收 → 作者拒绝（误报） → 反馈阈值

---

## 🔗 关联子系统

- `docs/subsystems/gantt_audit.md` —— 伏笔泳池巡检
- `docs/subsystems/false_positive_loop.md` —— AI 推荐被拒的反馈
- `docs/subsystems/multi_agent_cloud.md` —— 多 Agent 设定打磨时提议伏笔

---

## 📌 元信息

- **历史决策**：[001-foreshadow-tracking.md](./001-foreshadow-tracking.md)（保留作为历史）
- **反转触发**：Q6 / Q7.2 / Q8.1（共 3 题）
- **创建日期（原版）**：2026-07-08
- **v2 创建日期**：2026-07-10
- **重要性**：🔴 关键

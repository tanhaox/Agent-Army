# docs/api/ — MVP 9 命令 API Schema 总索引

> **创建日期**：2026-07-10
> **重要性**：🔴 关键（V1 横纵向研判补遗）
> **依据**：MVP_AUTHORITY §五 / ROADMAP §六 / 横纵向研判报告 V1

---

## 📂 9 个 MVP 命令 Schema

| # | 命令 | schema 路径 | 任务类型 | 主要职责 |
|---|------|-----------|---------|---------|
| 1 | `setup_consult` | [setup_consult.yaml](setup_consult.yaml) | setup_consult | 设定填写引导 |
| 2 | `character_card` | [character_card.yaml](character_card.yaml) | character_card | 角色卡 + 声纹展示 |
| 3 | `kickoff_meeting` | [kickoff_meeting.yaml](kickoff_meeting.yaml) | kickoff_meeting | 立项会 = 启动器 |
| 4 | `plan_chapter` | [plan_chapter.yaml](plan_chapter.yaml) | plan_chapter | 章节规划 |
| 5 | `write` | [write.yaml](write.yaml) | consistency_check_realtime | **核心写章节** |
| 6 | `consistency_check` | [consistency_check.yaml](consistency_check.yaml) | consistency_check_realtime | 防胡写守护 |
| 7 | `foreshadow_track` | [foreshadow_track.yaml](foreshadow_track.yaml) | foreshadow_scan | 伏笔半自动闭环 |
| 8 | `cumulative_audit` | [cumulative_audit.yaml](cumulative_audit.yaml) | gantt_audit | 6+ 泳池巡检 |
| 9 | `diff_check` | [diff_check.yaml](diff_check.yaml) | diff_check | git diff 联动触发 |

---

## 🎯 命令完整链路图

```
用户操作 → Step 1（设定）→ Step 2（立项）→ Step 3（写作）→ Step 4（巡检）
         ↓                ↓                ↓                ↓
   setup_consult      kickoff_meeting     write           cumulative_audit
   character_card                       consistency_check  foreshadow_track
                                          (real-time)
                                          
git commit 后自动：
   diff_check → 🔴→kickoff_meeting / 🟡→cumulative_audit / 🟢→log
```

---

## 📋 触发关系

| 上游命令 | 下游触发 |
|---------|---------|
| setup_consult | → kickoff_meeting（设定完成后） |
| kickoff_meeting（通过） | → voice_print.md 派生 |
| write（保存章节） | → facts_extraction（保存即抽） + state-detector release |
| diff_check（🔴 命中） | → kickoff_meeting(increment) |
| diff_check（🟡 命中） | → cumulative_audit |
| cumulative_audit（每 10 章） | → 自动 |

---

## 📁 已存在 vs 新增

| 类型 | 命令 | 来源 |
|------|------|------|
| **MVP 必做** | setup_consult / kickoff_meeting / plan_chapter / consistency_check / foreshadow_track / cumulative_audit | ROADMAP 6 命令 |
| **MVP 漏列（V1 补）** | write / character_card / diff_check | V1 横纵向研判补遗 |

`write` 之前漏列是因为 ROADMAP 默认有 write 但 ROADMAP 没显式声明它是 command。
`character_card` 之前漏列是因为 008-v2 把它视为"展示"而非"命令"。
`diff_check` 之前漏列是因为 R3 没上升到命令名。

---

## 🔌 与子系统的对应

| 命令 | 依赖子系统 |
|------|----------|
| setup_consult | content_attribution |
| character_card | voice_print / content_attribution |
| kickoff_meeting | kickoff_meeting / multi_agent_cloud / voice_print / facts-extraction |
| plan_chapter | foreshadow_half_loop / voice_print |
| write | state-detector / quality_guards_granularity / facts-extraction / voice_print / foreshadow_half_loop |
| consistency_check | router / content_attribution / voice_print / quality_guards_granularity |
| foreshadow_track | foreshadow_half_loop / false_positive_loop |
| cumulative_audit | gantt_audit / facts-extraction / state-detector / git_diff_trigger |
| diff_check | git_diff_trigger / state-detector |

---

## 📋 Phase 2 增加的命令

| # | 命令 | Phase | schema 路径 |
|---|------|-------|-----------|
| 10 | `chapter_polish` | Phase 2 | 待写 |
| 11 | `voice_print_check` | Phase 2 | 待写 |
| 12 | `relationship_graph` | Phase 2 | 待写 |
| 13 | `item_progression` | Phase 2 | 待写 |
| 14 | `ignore`（误报反馈工具） | Phase 1 但工具级 | 待写 |

---

## 🔍 测试与方法论

每个 schema 至少 5 个测试用例：

1. **happy path**：正常输入 → 正常输出
2. **缺参数**：必填参数空 → 退出码非零
3. **状态冲突**：状态冲突时按路由表拒绝
4. **数据完整**：output schema 字段不漏
5. **退出码语义**：exit code 与文档严格对应

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键（CLI 实现者的"地图"）
- **依据**：V1 横纵向研判补遗
- **关联文档**：MVP_AUTHORITY §五 / ROADMAP §六 / docs/subsystems/*.md

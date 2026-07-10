# MVP_AUTHORITY.md — Short story MVP 开发权威指南

> **创建日期**：2026-07-10
> **地位**：🔴 **MVP 开发的唯一权威入口**
> **依据**：本文档是 `docs/decisions/011-pressure-test-v3.md` 35 题压力审查后的固化输出
> **强制规则**：开发期间任何决策冲突以本文档为准，按 `DECISION_REVISION.md` 流程修订

---

## 🎯 本文档的作用

1. 汇总 MVP 阶段的全部关键决策（指向详细文档，不复制）
2. 定义子系统依赖关系（哪个子系统先开发、哪个后开发）
3. 标示当前 MVP 边界（MVP 之外的事 Phase 2+ 再考虑）
4. 提供 AI 协作的统一入口（让 AI 一眼看到全局）

---

## 🚦 MVP 第一原则（最简单版）

```
写作时 → 本地 Ollama，防胡写实时拦截
检视时 → 本地优先 + 云端协同，超出能力自动降级
立项时 → 多 Agent 云端协作，输出冲突清单
设定时 → 几万字是入场券，少填的字段守护豁免
反悔时 → git diff 细粒度判定，触发联动或立项会
```

---

## 📚 29 条决策的全索引

### A. 架构层（15 条 P 系列）

| # | 决策 | 一句话定义 | 详细 |
|---|------|-----------|------|
| **P1** | 防胡写守护机制 | 🔴 红色强制拦截 | docs/MVP_AUTHORITY.md §三 |
| **P2** | 误报反馈闭环 | 反向训练底座 | docs/subsystems/false_positive_loop.md |
| **P3** | AI 推理底座 | Ollama 本地 + mmx-cli 云端双底座 | docs/subsystems/router.md |
| **P4** | 后端架构 | 撤销 FastAPI；薄 Cloud Relay 仅做密钥托管 | docs/subsystems/router.md §三 |
| **P5'** | Web 21 页面 = spec | CLI 按 web 字段设计 | docs/subsystems/web_spec_sync.md |
| **P7** | 系统身份 | 协作者（AI 能起草设定草稿） | docs/decisions/011-pressure-test-v3.md |
| **P8** | 声音指纹定义 | 角色识别性特征，仅本书级 | docs/subsystems/voice_print.md（依赖） |
| **P9** | 设定哲学 | 填得多 = 守护有依据；少填 = 豁免 | docs/subsystems/setup-philosophy.md（依赖） |
| **P10** | 立项会 = 启动器 | Step 1 完成后强制；不合格就别写 | docs/subsystems/kickoff_meeting.md |
| **P11** | 6+ 泳池巡检 | 每 10 章 + 6+ 泳池并行 | docs/subsystems/gantt_audit.md |
| **P12** | MVP 范围 | 6 命令 + 立项会 + 6+ 泳池 + 4 门禁全 P0 | 见本文档 §四 |
| **P13** | 门禁全部 P0 | 防胡写/违规词/机械表达/AI 味 | docs/subsystems/quality_guards_granularity.md |
| **P14** | 多 Agent 部署 | 云端 mmx-cli 多 Agent；本地单 Agent 多通道 | docs/subsystems/multi_agent_cloud.md |
| **P15** | 状态切换原则 | writing/reviewing 状态自动切换 + 降级回退 | docs/subsystems/router.md §四 |

### B. 流程层（8 条 F 系列）

| # | 决策 | 一句话定义 | 详细 |
|---|------|-----------|------|
| **F1** | 设定填写路径 | AI 提问 + 作者手填（Phase 2 升级主持人模式） | docs/subsystems/setup-philosophy.md |
| **F2** | 伏笔 AI 推断性质 | 不扫原文找新伏笔；只推荐该回收的 | docs/subsystems/foreshadow_half_loop.md |
| **F3** | 伏笔机制 | 半自动闭环：候选 → 接受/拒绝 → 反馈训练 | docs/subsystems/foreshadow_half_loop.md |
| **F4** | 伏笔扫描时机 | 每章末扫一次 | docs/subsystems/foreshadow_half_loop.md |
| **F5** | 章节审查模式 | Word track changes 模式 | docs/subsystems/chapter_track_changes.md（依赖） |
| **F6** | 内容出处豁免 | 守护豁免 AI 起草内容 | docs/subsystems/content_attribution.md |
| **F7** | 跨章审计算法 | 事实抽取 + 云端兜底 | docs/subsystems/facts-extraction.md（依赖） |
| **F8** | 伏笔回收提醒 | 作者定回收章 + 系统排程 | docs/subsystems/foreshadow_half_loop.md |

### C / D / E 范畴（6 条）

| # | 决策 | 一句话 | 详细 |
|---|------|--------|------|
| **C1** | 多书角色复用 | MVP 不实现 | docs/subsystems/multi-book-design.md（依赖） |
| **C2** | 24 专题全集保留 | 全部 24 个，运行时取子集 | docs/subsystems/knowledge-base.md（依赖） |
| **C3** | 专题文档形式 | 散文 + 结构化双版本 | 同上 |
| **R1** | 反悔联动 | 整个时间段重算 | docs/subsystems/git_diff_trigger.md（依赖） |
| **R2** | 版本管理 | git 全保留 | 同上 |
| **R3** | 联动触发判定 | git diff 细粒度判定 | 同上 |
| **S1** | 系统真实身份 | 严格的质量管家 | docs/MVP_AUTHORITY.md §三 |

---

## 三、MVP 三原则解读

### P15 状态切换原则（最核心）

- **writing**：作者正在写章节，AI 进入 "红色强制拦截" 模式
  - 仅本地 Ollama
  - 防胡写 P0
  - 不响应云端
- **reviewing**：作者处于检视状态（设定打磨、立项会、跨章审核、巡检）
  - 本地优先
  - 本地能处理的本地处理（防胡写复检、声纹核对、伏笔扫描）
  - 超出本地能力（多 Agent 立项会、跨章深度审核）→ 云端协同
  - 自动降级回退（本地超时/截断自动转云端）

### P10 立项会原则

- Step 1 完成后**强制触发**
- 立项会**不是审核**，是**启动器**——不通过就不开始写
- 多 Agent 云端协作：档案 / 世界观 / 人物 / 节奏 / 读者视角 多角度审视
- 输出：必须解决的冲突清单 + 必要时返设定阶段
- 反悔机制：作者修改核心设定 → 自动触发新一轮立项会

### P13 4 道门禁全 P0

| 门禁 | 触发时机 | 实现方式 |
|------|---------|---------|
| 🔴 防胡写 | 写作时每段 + writing 状态全段 | Ollama 红警 + Git diff 复检 |
| 🔴 违规词 | 章节末 + 发布前 | 规则脚本（敏感词词典） |
| 🔴 机械表达 | 每段 | Ollama + 规则脚本混合 |
| 🔴 AI 味 | 每章末 | Ollama 抽样检测 |

---

## 四、MVP 必做清单（按依赖顺序）

### Phase 1.A 基础架构（先做）

1. `docs/ASSUMPTIONS.md` —— 架构假设清单（**立即做**）
2. `docs/subsystems/router.md` —— 状态切换 + 降级回退逻辑
3. `docs/subsystems/content_attribution.md` —— 段落 frontmatter 标注规则

### Phase 1.B 设定+立项阶段

4. `docs/subsystems/kickoff_meeting.md` —— 立项会协议
5. `docs/subsystems/multi_agent_cloud.md` —— 多 Agent 云端部署
6. 修订 `books/_template/settings/` —— 6 维度 + 章节 frontmatter + 立项会报告模板

### Phase 1.C 写作+巡检阶段

7. `docs/subsystems/foreshadow_half_loop.md` —— 半自动伏笔闭环
8. `docs/subsystems/gantt_audit.md` —— 6+ 泳池甘特图
9. `docs/subsystems/quality_guards_granularity.md` —— 4 道门禁颗粒度

### Phase 1.D 命令实现

10. 6 个核心命令：`setup_consult` / `kickoff_meeting` / `plan_chapter` / `consistency_check` / `foreshadow_track` / `cumulative_audit`
11. 4 道门禁的强度测试用例

---

## 五、命令依赖矩阵（MVP 必做的 6 命令）

| 命令 | 依赖的子系统 | 依赖的专题 |
|------|-------------|-----------|
| `kickoff_meeting` | 立项会 + 多 Agent 云端 + 内容出处标记 | core-conflict / character-network / world-boundary / special-setting / protagonist-goal-obsession |
| `setup_consult` | 设定哲学 + 内容出处标记 | character-network / special-setting / world-boundary |
| `plan_chapter` | 立项会输出 + 伏笔提醒系统 | story-timeline / protagonist-goal-obsession / character-arc |
| `consistency_check` | 状态切换 + 4 道门禁 + 内容出处豁免 | system-quality-guards + anti-pattern |
| `foreshadow_track` | 伏笔半自动闭环 | foreshadowing-and-hooks + story-timeline |
| `cumulative_audit` | 6+ 泳池巡检 + 事实抽取 + git diff 触发 | revision-and-polishing + system-quality-guards |

---

## 六、AI 协作守则

> AI 在协助开发时**必须遵守**的规则（本节 = AI 启动时的固定输入）

1. **任何代码变更前**：先查 `docs/MVP_AUTHORITY.md` 看是否在 MVP 范围内
2. **任何架构决策变更**：按 `docs/DECISION_REVISION.md` 流程修订
3. **任何守护功能**：必须先确认状态（writing 还是 reviewing）—— 错状态会触发 P15 违规
4. **任何内容引用**：必须保留 `source:` frontmatter
5. **任何决策冲突**：先查 `docs/decisions/011-pressure-test-v3.md` §五（七大冲突），按修正建议处理

---

## 七、明确不做（MVP 之外）

下列条目在 MVP **明确不做**，避免范围蔓延：

- ❌ 多书角色复用（C1）
- ❌ AI 主持人采访模式（Phase 2 才做）
- ❌ Web 端实际实现（Web 仅作为 spec，CLI 必须按其字段设计）
- ❌ 24 专题的散文版（仅结构化版本即可）
- ❌ 跨题材模板（玄幻/言情/悬疑/科幻模板）
- ❌ 风格迁移 / 自动写作 / VSCode 插件
- ❌ "自己审自己"的复杂豁免逻辑（F6 仅基础版）

---

## 八、MVP 验收金线（Phase 1 完成标准）

按 `docs/ROADMAP-v2.md` §八（修订后），MVP 必须通过：

- [ ] 一本完整测试书从空白到 30 章
- [ ] **防胡写红色拦截**：误报率 < 20%，漏报率 < 5%
- [ ] **设定填到几万字不会崩溃**（用户最强调的"top50 入场券"）
- [ ] **立项会能输出可执行的冲突清单**
- [ ] **6+ 泳池巡检能跑过测试书**
- [ ] **伏笔半自动闭环可演示**（候选 → 接受/拒绝 → 反馈）
- [ ] **git diff 触发联动可演示**（修改核心设定 → 触发全量重算）
- [ ] **状态切换可演示**（writing 锁云端 / reviewing 解锁）
- [ ] **每本书完全独立目录**（无跨书污染）
- [ ] **mmx-cli 密钥不暴露在 CLI 进程内**

---

## 📌 元信息

- **作者**：Claude（grill-me skill 驱动后）
- **审查依据**：35 题压力测试（011-pressure-test-v3.md）
- **下一步必读**：`docs/ASSUMPTIONS.md` ✅（已完成）
- **下次修订触发**：MVP 阶段任一 P 决策变更
- **关联文档**：
  - `docs/DECISION_REVISION.md` —— 决策修订流程
  - `docs/decisions/011-pressure-test-v3.md` —— 35 题审查主报告
  - `docs/decisions/README.md` —— 决策列表

# REVIEW-001-cross-cutting-analysis.md — 横纵向研判报告

> **审查对象**：2026-07-10 一次性沉淀的 13 份新文档（4 总入口 + 8 子系统 + 6 个 v2 决策）
> **审查方法**：横向（跨文档冲突 / 重复）+ 纵向（决策→子系统→命令的可实现性链）+ 已知冲突审计
> **审查日期**：2026-07-10
> **状态**：📋 待用户逐项讨论

---

## 🎯 审查目的

沉淀完 13 份文档后立刻做一次"冷静期审计"，找出：

1. **文档间冲突** —— A 说向东 B 说向西的硬冲突
2. **未解决的开放问题** —— 文档里说"待验证/待用户确认"但没人追的 TODO
3. **架构盲点** —— 整体看下来发现但任何单文档里没明确写的盲点
4. **可实现性追问** —— 决策→子系统→命令三层之间是否有 gap
5. **未引用 / 错引 / 悬空引用** —— 文档间链接错位

这是一份**不替用户决定**的研判记录，逐项列出等讨论。

---

## 一、横向研判：跨文档冲突 / 错位

### 🔴 H1：MVP_AUTHORITY.md 引用的 4 个子系统文件**根本不存在**

**位置**：[MVP_AUTHORITY.md:42-75](MVP_AUTHORITY.md#L42-L75)（决策详细列）

**问题**：MVP_AUTHORITY.md 引用了 8 个子系统文件路径，但**其中 4 个文件根本不存在**：

| 引用路径 | 实际文件 | 状态 |
|---------|---------|------|
| `docs/subsystems/voice-print.md` | ❌ 不存在 | 应是 **008-v2-voice-print.md（决策文档）** |
| `docs/subsystems/setup-philosophy.md` | ❌ 不存在 | 没有对应文件（设定哲学 P9 写在 v3 决策里，但无子系统文档） |
| `docs/subsystems/foreshalf-half-loop.md` | ❌ 不存在（多处拼写错，foreshalf → foreshadow） | 应是 **foreshalf-half-loop 也没真文件**。F3 伏笔半自动闭环散见于 001-v2 决策和 false-positive-loop.md，但**没有独立的"伏笔子系统"文档** |
| `docs/subsystems/chapter-track-changes.md` | ❌ 不存在 | F5 track changes 模式**只在 011-v3 决策里一句话提及**，没有任何子系统文档 |
| `docs/subsystems/facts-extraction.md` | ❌ 不存在 | F7 事实抽取**只被 gantt-audit.md 引用**为"依赖"，未实现 |
| `docs/subsystems/git-diff-trigger.md` | ❌ 不存在 | R1/R2/R3 git diff 联动**只在 ROADMAP 里出现**，无子系统文档 |
| `docs/subsystems/multi-book-design.md` | ❌ 不存在 | C1 多书角色复用 MVP 不实现，无子系统文档（这正常） |
| `docs/subsystems/knowledge-base.md` | ❌ 不存在 | C2/C3 24 专题只有 README 引用，未沉端子系统 |

**严重程度**：🔴 **致命** —— 这导致 MVP_AUTHORITY.md 多个表格的"详细"列是**真空链接**

**修复方向**：
- 方案 A：**写 8 个缺失的子系统文档**（chapter-track-changes / facts-extraction / git-diff-trigger / foreshalf-half-loop / setup-philosophy / voice-print-as-subsystem / knowledge-base 至少 6 个）
- 方案 B：**收缩 MVP_AUTHORITY.md 引用表**，改为"散见于决策 + 子系统"，不强行收敛到独立子系统文件

---

### 🔴 H2：`foreshalf` 拼写错误**遍布 5 个文档**

**出现位置**（按出现次数）：

| 文档 | 出现位置 |
|------|---------|
| `MVP_AUTHORITY.md` | §A P1/F2/F3/F4/F8 全部"详细"列 |
| `011-pressure-test-v3.md` | §A 决策行 |
| `decisions/README.md` | §四 |
| `foreshadow-track` 数据模型引用 | gantt-audit.md |

**拼写问题**：`foreshalf` ≠ `foreshadow`（少了 `dow`）。这在 IDE 里不会被 lint 抓到，但**会在搜索时漏掉**。

**严重程度**：🟡 重要 —— 跨文档搜索的隐性陷阱

**修复方向**：在所有文档中**全文替换** `foreshalf-half-loop` → `foreshadow-half-loop`（如要建子系统）。如不建子系统，则改名 `foreshadow-loop.md`。

---

### 🔴 H3：MVP 6 命令的命名与文档引用**存在 5 处不一致**

**MVP_AUTHORITY.md §四** 列的 6 命令：

```
setup_consult / kickoff_meeting / plan_chapter / consistency_check / foreshadow_track / cumulative_audit
```

但 `web-spec-sync.md` 和 `002-v2-page-data-contract.md` 中引用了**多出一倍的命令**：

| web-spec-sync.md | 002-v2-page-data-contract.md |
|------------------|-------------------------------|
| setup_consult | setup_consult ✓ |
| character_card | （无） |
| plan_chapter | plan_chapter ✓ |
| write | （无） |
| foreshadow_track | foreshadow_track ✓ |
| audit | audit |
| kickoff_meeting | kickoff_meeting ✓ |
| （无） | character_card |

**额外命令：**`character_card` / `write` / `audit` 三个

**ROADMAP §四** 列了"6 命令"：`setup_consult / kickoff_meeting / plan_chapter / consistency_check / foreshadow_track / cumulative_audit`

**`010-v2-multi-agent-architecture.md`** §关联引用：`kickoff_meeting / cumulative_audit / 跨章修订单`

**问题**：

1. **MVP 列了 6 命令**（plan_chapter），但 web spec 列了 **7+ 命令**（多了 write / character_card / audit）
2. `audit` 在 ROADMAP 里叫 `cumulative_audit`，web-spec-sync 里叫 `audit`
3. `consistency_check` 在 MVP 命令里列出，但 web spec 没列出（实际确实没 web 页面对应 → 一致）

**严重程度**：🟡 重要 —— 不修复，CLI 实现时会有命名混乱

**修复方向**：
- 决定：MVP 命令到底 6 个还是 7 个？
- 一致性建议：`audit` 应统一为 `cumulative_audit`（这是 ROADMAP 里的名字）
- `write` 应加入 MVP 命令列表（web spec 必有）
- `character_card` 是 MVP 还是 Phase 2？需决定

---

### 🟡 H4：state 字段有两种含义混淆

**出现位置**：

| 文档 | state 字段 | 含义 |
|------|-----------|------|
| router.md §一 | state | "writing" / "reviewing" / "force_local" 三态 |
| quality-guards-granularity.md §1.2 | state | "writing" \| "reviewing" 文本 |
| multi-agent-cloud.md §六 | state | "writing" / "reviewing" / "force_local" 三态 |

router.md §七 API 设计：

```python
def route_request(
    task_type: str,
    state: str,               # "writing" | "reviewing" | "force_local"
    payload: dict,
    fallback_enabled: bool,
)
```

看似一致——但 router.md 也提到：

```yaml
log:
  - timestamp
  - command
  - task_type
  - state (writing/reviewing)
```

**问题**：router.md 把 state 限制为三态（force_local 是 reviewing 强制本地模式），但写"writing/reviewing" 总结时**漏掉 force_local**

**严重程度**：🟢 轻微 —— 但后续日志记录字段和 API 字段定义不统一，会让监控失真

**修复方向**：明确 API 的 state 字段是 3 态，日志记录也是 3 态。

---

### 🟡 H5：声纹 vs Q11 章节授权——两个机制都缺独立子系统

**声纹（P8）**：
- 引用关系：MVP_AUTHORITY §A P8 → "subsystems/voice-print.md（依赖）"
- 真实文件：**存在**的是 `008-v2-voice-print.md`（决策文档）而不是子系统文档
- 子系统文档：**不存在**
- 影响：声纹的"对白自动核查算法"（Phase 2 必做）目前**无文档承载**

**Q11 章节授权（F5 track changes 模式）**：
- 011-pressure-test-v3.md 提到："用户 31 答了'Word 审查模式'，但**Word 审查有两种典型行为**（track changes 接受/拒绝 vs git commit 快照）"
- 修复建议：MVP_AUTHORITY 推断为 A（track changes），需要用户明确确认
- 影响：**这是一个待用户确认的悬念**——从未被显式解决

**严重程度**：🟡 重要 —— 是"V3 报告里已标记但没解决"的悬挂问题

**修复方向**：
1. 决定声纹是写子系统文档还是收敛到决策文档
2. 用户必须回答 Q11：F5 是 A 还是 B？

---

## 二、纵向研判：决策 → 子系统 → 命令的落地链

### 🔴 V1：6 个 MVP 命令的"输入输出 schema"**全部缺失**

ROADMAP §六 列了 6 命令名，但**没有一份文档**给出每个命令的：

- CLI 入参（args）
- 完整出参 schema（包含 web_spec 字段）
- 退出码
- 何时调用路由器、用什么 task_type

**已有部分**：
- `quality-guards-granularity.md` 给出 4 门禁的输入输出 schema，但不完整（如缺 web_spec）
- `router.md §七` 给出了"调用示例"（consistency_check 的一个），但其他 5 个命令缺

**严重程度**：🔴 **致命** —— 没有完整 schema，CLI 实现者要自己拍脑袋

**修复方向**：写一个 `docs/api/` 目录，每个命令一份 YAML schema，类似：

```yaml
# docs/api/foreshadow_track.yaml
command: foreshadow_track
args:
  - name: book_name
    type: str
    required: true
  - name: chapter
    type: int
output:
  type: object
  fields:
    - candidates (array)
    - warnings (array)
exit_codes:
  0: 成功
  1: 有建议
  2: 有必须处理
relates:
  subsystems: [gantt-audit, false-positive-loop, content-attribution]
  decisions: [001-v2]
```

**至少需要**：6 个 API schema 文件。

---

### 🔴 V2：F7 事实抽取算法**只被引用而未定义**

**引用处**：
- `MVP_AUTHORITY.md` §五 `cumulative_audit` 依赖 "facts-extraction"
- `gantt-audit.md` 顶部关联引用 `facts-extraction（依赖）`
- `011-pressure-test-v3.md` §A F7 决策行

**问题**：
- 没有任何 `facts-extraction.md` 文档
- 没有 facts.yaml 数据模型示例
- 没有抽取算法（关键词提取？AI 摘要？正则模板？）
- 没有任何测试用例

**严重程度**：🔴 **致命** —— `cumulative_audit` 是 MVP 6 命令之一，没有这个算法核心命令无法实现

**修复方向**：

1. 写 `docs/subsystems/facts-extraction.md`（独立子系统）
2. 明确数据模型（chapter-NNN-facts.yaml 的字段）
3. 明确算法（Ollama 抽取 vs 正则模板）
4. 明确 token 预算

---

### 🔴 V3：R3 git diff 联动判定**只锁定了规则未规定算法**

**`011-pressure-test-v3.md` §A R3**：

> git diff 细粒度判定：检测是否修改了核心角色名 / 关键道具名 / 设定术语，命中则触发全量重算

**问题**：
- 什么是"核心角色名"？所有 voice-prints 里出现过的？还是 meta.md 列出的？
- 什么是"关键道具名"？来自 04-special-setting.md 还是任一章节？
- "设定术语"如何识别？词典？正则？
- **没有算法设计、没有测试用例**

**严重程度**：🔴 **致命** —— 这是 R1 整个时间段重算的触发器，但没人知道怎么实现

**修复方向**：
1. 写 `docs/subsystems/git-diff-trigger.md`（独立子系统）
2. 词典定义在哪（`books/<name>/config/key_terms.yaml`？）
3. 算法是用 git grep + 角色名匹配？还是要 AI 判定？

---

### 🟡 V4：kickoff_meeting 命令的"`mode` 参数" 与 "强制本地"开关交互未定义

**kickoff-meeting.md §六**：

```yaml
kickoff_meeting 命令参数:
mode: increment | full   # 默认 increment
since: <chapter_or_time>
force: true | false
```

**问题**：
- 与 `router.md §一` 的"强制本地模式"开关如何协调？
- kickoff_meeting 默认走云端多 Agent；如果用户开了 force_local，会被路由器阻塞吗？
- 这是个**用户没注意到的细节**：MVP 阶段 force_local 与 多 Agent 立项会的冲突

**严重程度**：🟡 重要 —— 影响 force_local 的使用边界

**修复方向**：
- 在 kickoff-meeting.md §六**显式说明**：force_local=true 时，kickoff_meeting 必须降级为本地串行（甚至禁用）

---

### 🟡 V5：F5 track changes 模式**没人能写清楚**

**`MVP_AUTHORITY.md` 推测**：

> Word track changes 模式：AI 修改以"建议"形式可见，作者逐条 accept/reject，原文保存完整

**问题**：
- 这是 P15 状态切换的一部分吗？还是独立机制？
- "建议"在 markdown 文件里以什么形式存储？（HTML 注释？临时 diff 视图？）
- 与 `content-attribution.md` 的 frontmatter 关系？（frontmatter 是"出处标记"，不是"建议标记"）

**严重程度**：🟡 重要 —— 因为这直接决定了 write.html（Phase 1 未实现但 spec 必出）的 spec

**修复方向**：
1. 必须先让用户**明确 Q11 答案**——F5 是 Word track changes 模式 vs git commit 快照模式
2. 根据答案，决定子系统的存在

---

### 🟡 V6：6 命令中**声纹 chapter_polish 缺失**

ROADMAP §六 列 6 命令：

```
setup_consult / kickoff_meeting / plan_chapter / consistency_check / foreshadow_track / cumulative_audit
```

**对比**：Phase 2 命令集：

```
chapter_polish (chapter_polish.py) / voice_print_check / relationship_graph / item_progression
```

**问题**：

- `consistency_check` 与 `chapter_polish` 是不是同一回事？
- 008-v2 文档说"声纹核对是 MVP 简化为手动填写，Phase 2 完善对白核查"
- 但 MCP plan_chapter 也依赖声纹（用于章节规划时判别角色对白）
- 声纹**事实上是 MVP 的隐式依赖**，但没列入 6 命令

**严重程度**：🟡 重要 —— 6 命令集和声纹的边界可能错位

---

## 三、整体架构盲点（单文档里没人提到）

### 🔴 B1："writing 状态"由谁判定，没人定义

**router.md §一 状态判定**：

> writing 触发条件：
> - 作者正在写章节（最近 30 秒内有内容变更）

**问题**：
- "30 秒内有内容变更"——谁监测？文本编辑器？CLI 后台进程？
- 如果作者开编辑器离开 10 分钟，要不要"自动退出 writing 状态"？
- 如果作者读了存档回到 write.html 页面，writing 状态如何重置？
- 没有"会话管理器"的设计

**严重程度**：🔴 致命 —— 这是 P15 整个系统的感知神经

**修复方向**：写个 `docs/subsystems/state-detector.md` 子系统，定义：
- 哪些动作进入 writing（打开 write.html / CLI write 命令）
- 哪些动作退出 writing（保存章节 / 切走 / 退出编辑器）
- 检测粒度（30 秒？5 分钟？是否需要 session-manager 后台进程？）

---

### 🔴 B2：CLI 命令实际运行入口**完全没说**

**MVP_AUTHORITY** 说 "6 命令的 CLI stub 已就位（`python -m ai_coauthor --help`）"

**问题**：
- 项目当前根本没有 `ai_coauthor/` 目录
- 没有 `pyproject.toml`
- 没有 `setup.py`
- 入口 `python -m ai_coauthor` 是什么？模块名要不要调整？
- 没有测试目录 `tests/`

**严重程度**：🔴 致命 —— 但可能属于"等动手时再做"的隐性工作

**修复方向**：在 ROADMAP.md §"Phase 1.D 命令实现" 明确：
- 模块命名（`ai_coauthor` 这个名字？），放在 `projects/skills/` 还是项目根？
- 包管理（pyproject.toml）
- 测试套件（pytest）

---

### 🟡 B3：写作 vs 立项会 vs 跨章审核**三种工作的"完成度"概念不一致**

**当前定义**：
- 立项会：`kickoff_passed: true / false`（frontmatter）—— 单值
- 章节写作：每章文件存在 + frontmatter 状态？
- 跨章审核：每 10 章一份 `audit_report_*.md` 文件？

**问题**：
- 是否有"书的进度"概念？进度 0-100%？还是离散"已完成章节数 / 总章数"？
- 没有 dashboard 的实现指南

**严重程度**：🟡 重要 —— 因为 web spec 的 `dashboard.html`（已存在 mockup）需要这个

**修复方向**：
- 在 MVP_AUTHORITY.md 或 web-spec-sync.md 明确：
  - 进度如何计算（已完成章节 / 总章节 vs 设定完成度 vs 立项会通过次数）
  - dashboard 字段来源
- 写一个简单的"书状态"查询命令

---

### 🟡 B4：跨书/跨章节的设定引用机制——一个文件引用另一个文件如何表达？

**`content-attribution.md` §转换规则**：

> `ai_drafted` 段的"金手指"必须挂到 `02-characters.md` 或 `01-world.md`，否则继承不到

**问题**：
- 段落怎么"挂到"另一个文件？markdown 链接？frontmatter 显式声明？自动检测？
- 这是**继承机制**，不是引用机制；与 git 反向链接相同
- 没有定义清楚继承规则

**严重程度**：🟡 重要 —— 自己审自己漏洞的修复路径依赖这个

**修复方向**：
- 写一个"内容继承规则"子系统
- 明确：AI 起草的金手指**应该如何被系统检测到**且**自动加进设定库**？

---

### 🟡 B5：foreshadow_track 命令的"`since`"参数语义模糊

**kickoff-meeting.md §六**：

```yaml
mode: increment | full
since: <chapter_or_time>
```

但 `foreshadow_track.py` 的**相同 yaml** 在不同文档有不同含义。

**严重程度**：🟢 轻微

**修复方向**：foreshadow 和 kickoff 的 since 参数应分别文档化（如果共享就抽取）。

---

### 🟡 B6：角色声纹 vs 角色卡的关系**没说清楚**

**`MVP_AUTHORITY §MVP 必做清单`** 列了 `voice-prints/protagonist.md` 作为必填
**`web-spec-sync.md`** 列了 `character-profile-protagonist.html` 作为 spec

**问题**：
- 声纹是 character-card 的一个字段？还是独立文件？
- 角色卡包含"性格 / 背景 / 动机 / 声纹 / 弧光"等，声纹只是其中一项
- 但 P8 决策说"声纹是本书级独立子系统"——这暗示声纹不应该是 character-card 的子字段

**严重程度**：🟡 重要 —— 关系到 voice-prints/ 目录结构

**修复方向**：
- 决定：voice-prints/*.md 是独立文件（与 02-characters.md 并列）还是后者内嵌字段
- 影响 books/_template/ 的结构

---

### 🟡 B7："章节 frontmatter"与"段落 frontmatter"是两层，未显式区分

**content-attribution.md**：段落级 frontmatter（`<!-- @attribution -->`）

**kickoff-meeting.md**：章节/书 frontmatter（`kickoff_passed: true / false`）

**问题**：
- 这两个 frontmatter 都在 markdown 文件里
- 都是 `key: value` 格式
- 但前者是 HTML 注释形式（段落级），后者是 YAML 形式（文件级）
- 没有文档说明这两层的关系和边界

**严重程度**：🟡 重要 —— 实现时混乱

**修复方向**：在 content-attribution.md 顶部加一段：
- 段落 frontmatter：`<!-- @attribution source=... -->` 紧贴段落
- 文件/章节 frontmatter：`---\nkey: value\n---` 在文件头
- 关系：文件级 → 段落级 → 默认

---

### 🟢 B8：Web mockup 现状没在本轮沉淀里更新

**问题**：
- 用户在 Q23、Q24 反复强调"Web 稿不能白设计"
- 但 21 个 web HTML 实际是 7 月 8 日左右生成，**当前状态是 mockup**
- ASSUMPTIONS.md 直接写了"❌ 违反（HTML 是 mockup，字段并不实际存在）"
- 但 web-spec-sync.md 又假设 Web 字段是 spec 约束

**严重程度**：🟢 已知冲突（已显式化为 ❌ 项）

**修复方向**：
- 在 web/ 目录下**标记**哪些 HTML 已"提升为 spec"，哪些仅 mockup
- 或者**全部视为 spec**（用户已接受）

---

## 四、文件 / 链接错误（engineer 视角）

### 🟢 E1：cross-link 错位

- MVP_AUTHORITY.md 第 200 行：`下一步必读 docs/ASSUMPTIONS.md（待创建）` —— 已创建但文本未更新
- DECISION_REVISION.md §实例第三行：`011 主索引里明确写了"v1 / v2 已删除"` —— 但 011-pressure-test-v2.md 现在又出现在 docs/decisions/ 目录里
- 008-v2-voice-print.md §关联：`MVP_AUTHORITY.md §四 Phase 1.B` —— 但 MVP_AUTHORITY §四 Phase 1.B 是 kickoff-meeting.md，**不是 voice-print 章节**

### 🟢 E2：拼写错误

- `foreshalf` 应为 `foreshadow`（H2）
- `kickoff_meeting` 命令 vs 子系统命名多处不统一：`kickoff_meeting`（带下划线） vs `kickoff-meeting`（带连字符）在不同文档混用

### 🟢 E3：CHANGELOG 与 README v2 状态不同步

- `decisions/README.md` 显示 8 个 v2 决策
- 但 v3 报告实际只有 5 个决策文档（001-v2 / 002-v2 / 003-v2 / 008-v2 / 010-v2）+ ROADMAP 重写
- 数量对不上

---

## 五、按"严重度 + 修复成本"分级的未厘清清单

### 🔴 P0（必修，否则开发立即卡壳）

| # | 题目 | 影响 |
|---|------|------|
| H1 | 4 个子系统文档**根本不存在** | MVP_AUTHORITY 真空引用 |
| V1 | 6 命令 schema 文档缺失 | CLI 实现者必须自创 |
| V2 | F7 事实抽取无算法设计 | `cumulative_audit` 无法实现 |
| V3 | R3 git diff 联动无算法 | 反悔机制无法实现 |
| B1 | writing 状态检测机制缺失 | P15 整个系统的感知神经 |
| H5 | Q11 F5 章节授权语义悬空 | 是否需要 chapter-track-changes 子系统 |

### 🟡 P1（建议修，开发时碰会绕路）

| # | 题目 |
|---|------|
| H2 | foreshalf 拼写错误 |
| H3 | 6 命令 vs 7 命令命名不一致 |
| H4 | state 字段 2 态 vs 3 态 |
| V4 | force_local vs 多 Agent 冲突 |
| V6 | 声纹 vs 6 命令集边界 |
| B3 | 进度 / 完成度概念未统一 |
| B4 | 跨文件内容继承机制缺失 |
| B6 | 声纹 vs 角色卡关系 |
| B7 | 段落 / 文件 frontmatter 两层未文档化 |
| E1-E3 | cross-link 错位与拼写 |

### 🟢 P2（已知冲突，可延迟）

| # | 题目 |
|---|------|
| B8 | Web mockup 当前状态 |

---

## 六、这份报告本身的不确定性

诚实地说，这份报告有这些限制：

1. **只读了 13 份新文档**，没读 v1 决策（除 011 README 引用外）—— 可能遗漏 v1 中已经解决但 v2 没传承的部分
2. **没读 web/ 目录下 21 个 HTML**——没逐页核对 web-spec-sync.md 列的"页面字段"
3. **没读 MVP_AUTHORITY.md 中 8 个 topic 文件名所在的 docs/knowledge/novel-writing/**——24 专题实际内容与命令依赖矩阵的契合度未验证
4. **未跑任何实际命令**——所有结论都是文档级推论，未经过实测

---

## 七、建议后续讨论顺序

按从最痛到最轻的顺序：

### 第一阶段（立即讨论——影响 MVP 启动）

1. **H1**：决定缺失的 4 个子系统是写还是删（最有定性影响）
2. **B1 / V2 / V3**：writing 状态判定 + F7 事实抽取 + R3 git diff —— 三个 P15+ 反悔机制的核心算法
3. **V1**：6 命令 schema 文档——这是开发工作的起点
4. **H5**：Q11 章节授权语义用户确认（影响 F5 子系统是否存在）

### 第二阶段（中期讨论——影响 6 周内 MVP 完成度）

5. H2 / H3 / H4：拼写 + 命名 + 状态字段统一
6. V4 / V6 / B6：force_local、声纹、角色卡的边界
7. B3 / B4 / B7：进度、跨文件继承、frontmatter 双层
8. E1-E3：文档工程性修复

### 第三阶段（可推迟）

9. B8：Web mockup 状态

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **审查对象**：13 份 2026-07-10 新文档
- **下一动作**：与用户逐项讨论优先级最高的 4 个 P0 项
- **本次审查的局限**：未实际读 v1 / 未读 web HTML / 未跑实测
- **本次审查的价值**：避免"刚沉淀完就动工，后期撞墙"

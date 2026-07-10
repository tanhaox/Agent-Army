# ROADMAP.md — Short story 开发路线图（v2）

> **版本**：v2
> **创建日期**：2026-07-10
> **依据**：35 题压力测试（011-pressure-test-v3.md）+ 用户 6 次架构反转
> **状态**：📋 MVP 阶段 — 立即可启动

---

## 🎯 总体时间线

```
策划阶段 → MVP v2（6 命令 + 立项会 + 6+ 泳池 + 4 门禁全 P0）→ Beta（10 命令）→ 正式版
✅ 已完成   2026-?? 启动                                              2026-??      2026-??
```

---

## 📋 MVP v2 必做

### 6 个核心命令

| # | 命令 | 优先级 | 依据子系统 |
|---|------|--------|-----------|
| 1️⃣ | `setup_consult.py` | 🔴 P0 | 设定哲学 + content_attribution |
| 2️⃣ | `kickoff_meeting.py` | 🔴 P0（**新增**） | 立项会 + multi_agent_cloud |
| 3️⃣ | `plan_chapter.py` | 🔴 P0 | 立项会输出 + 伏笔提醒 |
| 4️⃣ | `consistency_check.py` | 🔴 P0 | router + content_attribution + quality-guards |
| 5️⃣ | `foreshadow_track.py` | 🔴 **P0 最关键**（**半自动闭环**） | foreshadow_half_loop |
| 6️⃣ | `cumulative_audit.py` | 🔴 **P0**（**甘特图 6+ 泳池**） | gantt_audit + facts-extraction |

### 必做的 4 道质量门禁（**全部 P0**——已升级）

| 门禁 | 优先级 | v2 变更 |
|------|--------|---------|
| 防胡写守护 | 🔴 P0 | 不变（红警强制拦截） |
| 违规词验证 | 🔴 P0 | 不变 |
| 机械表达检测 | 🟡→🔴 **P0** | **升级**（Q25.2） |
| AI 味检测 | 🟡→🔴 **P0** | **升级**（Q25.2） |

### MVP v2 必做的子系统（按启动顺序）

**Phase 1.A 基础架构（先做）**

1. **`docs/ASSUMPTIONS.md`** —— 架构假设清单 ✅ 已完成
2. **`docs/subsystems/router.md`** —— 状态切换 + 降级回退 ✅ 已完成
3. **`docs/subsystems/content_attribution.md`** —— 段落 frontmatter 规则 ✅ 已完成

**Phase 1.B 设定+立项阶段**

4. **`docs/subsystems/kickoff_meeting.md`** —— 立项会协议 ✅ 已完成
5. **`docs/subsystems/multi_agent_cloud.md`** —— 多 Agent 云端部署 ✅ 已完成
6. **薄 Cloud Relay**（P4）—— Flask 50 行加密钥托管 → Phase 1.B 实现

**Phase 1.C 写作+巡检阶段**

7. **`docs/subsystems/gantt_audit.md`** —— 6+ 泳池甘特图 ✅ 已完成
8. **`docs/subsystems/quality_guards_granularity.md`** —— 4 道门禁颗粒度 ✅ 已完成
9. **`docs/subsystems/false_positive_loop.md`** —— 误报反馈闭环 ✅ 已完成
10. **`docs/subsystems/web_spec_sync.md`** —— Web spec 数据契约 ✅ 已完成

**Phase 1.D 命令实现**

11. 6 个核心命令 + 4 道门禁的强度测试用例

---

## 🎯 MVP v2 验收金线（必须通过）

### 功能性验收

- [ ] 一本完整测试书从空白到 30 章
- [ ] **防胡写红色拦截**：误报率 < 20%，漏报率 < 5%
- [ ] **4 道门禁全部 P0 实现**：机械表达 / AI 味检测也必须能跑
- [ ] **多 Agent 立项会**：能跑云端多 Agent 立项，输出"独立报告 + 问题汇总"
- [ ] **6+ 泳池巡检**：能跑过测试书
- [ ] **伏笔半自动闭环**：候选 → 接受/拒绝 → 反馈
- [ ] **git diff 触发联动**：修改核心设定 → 触发全量重算
- [ ] **状态切换可演示**：writing 锁云端 / reviewing 解锁
- [ ] **每本书完全独立目录**（无跨书污染）
- [ ] **mmx-cli 密钥不暴露在 CLI 进程内**（通过 Cloud Relay）

### 架构性验收

- [ ] **本地 Ollama 可稳定跑通所有 writing 状态命令**（Ollama 模型实测）
- [ ] **Cloud Relay 可用**（密钥托管）
- [ ] **mmx-cli 调用延迟 < 30 秒**
- [ ] **Web 21 页面的数据契约文件 contracts/*.yaml 全部存在**
- [ ] **CLI 输出字段 ⊇ Web HTML 字段**

### 工程性验收

- [ ] **架构假设清单 ASSUMPTIONS.md 全部 ⚠️ 项有实测结论**
- [ ] **6 个 v2 决策文档 001-v2 / 002-v2 / 003-v2 / 008-v2 / 010-v2 与 011-v3 无冲突**
- [ ] **决策修订流程 DECISION_REVISION.md 已被实际跑过 1 次**
- [ ] **没有 P0 决策在 MVP 阶段擅自变更**

### 用户接受度验收（最重要的金线）

> 用户原话："**系统是要往 top50 以上的书榜去冲击的**"

- [ ] 作者能用 MVP 走完一本测试书，**且产出 top50 级别章节质量**
- [ ] **几万字设定不会被作者放弃**（填得动）
- [ ] **立项会反复打磨 1 周内能收敛到通过状态**（可承受）
- [ ] **防胡写红警不会让作者烦躁放弃系统**（误报率 OK）

---

## 📋 Phase 2 (Beta) 完善

### 4 个新增命令

| # | 命令 | 优先级 |
|---|------|--------|
| 7️⃣ | `chapter_polish.py` | 🟡 P1 |
| 8️⃣ | `voice_print_check.py`（完善对白核查） | 🟡 P1 |
| 9️⃣ | `relationship_graph.py` | 🟡 P1 |
| 🔟 | `item_progression.py` | 🟡 P1 |

### 质量与体验

- AI 主持人采访模式（升级 setup_consult）
- 6+ → 8+ 泳池（加线索网、哲学主题）
- 真实启用 mmx-cli 关键词轮换
- 多 Agent 报告自动合并可视化

### 题材模板

- 玄幻 / 言情 / 悬疑 / 科幻 模板差异化

---

## 📋 Phase 3 高级

- 自动推断（基于设定生成大纲草稿）
- Web 端实际实现（21 页面）
- 甘特图可视化（Mermaid → D3.js）
- AI 味精细化（识别具体 AI 模式）

---

## 📋 Phase 4 扩展

- 多书角色复用（C1 升级）
- 风格迁移（学作者笔触）
- VSCode 插件
- 自动写作（很后期）

---

## 🚦 MVP v2 启动检查清单

按用户 6 次架构反转，MVP 启动前**必须**完成：

- [ ] **架构假设验证**：Ollama 实测 + mmx-cli 延迟实测 + Cloud Relay 安全验证
- [ ] **关键 P0 决策确定**：Q11 章节授权语义再确认（v3 假设为 Word track changes）
- [ ] **8 个子系统文档全部完成** ✅
- [ ] **6 个原决策文档全部重写为 v2** ✅
- [ ] **决策修订流程已被实际跑过一次**（用 DECISION_REVISION.md）
- [ ] **立项会第 1 次跑通**（哪怕是空白书的轻量测试）
- [ ] **6 命令的 CLI stub 已就位**（能 `python -m ai_coauthor --help`）

---

## 📊 关键技术决策

### 决策 1：文件即状态
- 所有数据都是 Markdown 文件
- git 友好
- 无数据库

### 决策 2：每本书独立目录
- `books/<name>/` 下独立
- 模板化复制

### 决策 3：双底座 AI（P3 / P15）
- 本地 Ollama：writing 状态
- 云端 mmx-cli：reviewing 状态
- 自动降级回退

### 决策 4：模块化命令 + 子系统分层（**v2 新**）
- AI 推理统一通过 `router.py`
- 内容出处标记统一通过 `content_attribution.md`
- 多 Agent 通过 `multi_agent_cloud.md`
- 立项会 / 巡检独立子系统

### 决策 5：MVP 是"能跑完一遍全流程"（**v2 升级**）
- 不只是"4 命令最小可用"
- 必须跑完：设定 → 立项 → 规划 → 写章 → 巡检 全流程

### 决策 6：Web spec + 数据契约（v2 升级）
- 21 个 Web 页面是规格说明书
- CLI 输出字段 ⊇ Web 字段
- 数据契约文件 contracts/*.yaml

---

## ⚠️ 风险与缓解（v2 视角）

| 风险 | 影响 | 缓解 |
|------|------|------|
| Ollama 实测能力不足 | MVP 第一原则崩溃 | 多模型测试 + 选择合适的本地模型 |
| mmx-cli 密钥泄露 | 隐私灾难 | Cloud Relay + 不在 CLI 进程内持有 |
| 立项会反复打磨失控 | 用户放弃 | 默认增量模式 + 立项超时提醒 |
| 多 Agent 云端成本 | 用户不愿启用 | 增量模式 + 仅跨章/巡检触发 |
| 6+ 泳池误判 | 巡检失效 | 每泳池可调阈值 + 误报反馈回环 |

---

## 📅 时间线（v2 预估）

| 阶段 | 预计时间 | 说明 |
|------|---------|------|
| **MVP v2** | 4-6 周 | Phase 1.A → 1.D，6 命令 + 8 子系统 |
| Phase 2 (Beta) | 4-6 周 | 补齐 10 命令 + 主持人 |
| Phase 3 (高级) | 6-8 周 | Web 实现 + 可视化 |
| Phase 4 (扩展) | 长期 | 多书复用等 |

---

## 📌 元信息

- **作者**：Claude（grill-me skill 驱动后）
- **依据文档**：
  - `docs/decisions/011-pressure-test-v3.md` —— 35 题审查
  - `docs/MVP_AUTHORITY.md` —— MVP 总索引
  - `docs/ASSUMPTIONS.md` —— 架构假设
- **下次修订触发**：MVP 阶段任一 P 决策变更
- **创建日期**：2026-07-10
- **重要性**：🔴 关键

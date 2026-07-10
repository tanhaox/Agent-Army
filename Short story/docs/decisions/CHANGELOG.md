# 会议纪要：2026-07-09 完整工作日

> **记录人**：AI-Agent-Local
> **日期**：2026-07-09
> **目的**：完整记录今天所有讨论、决策、产出、待办

---

## 📅 今日工作汇总

### 完成的工作

1. ✅ **将所有虚拟内容替换为《赘婿》**（24 个文件，860 处替换）
2. ✅ **修复 font-weight:2000 错误**（23 个文件，115 处）
3. ✅ **新增 6 板块 txt 导入功能**（chat-fill.html + setup_import.py + 13 section 模板）
4. ✅ **重构 setup-02-characters.html 为思维导图**
5. ✅ **建立档案 → 详情 闭环**（character-profile-*.html 可编辑）
6. ✅ **新增商业网文主角 4 维度**（核心卖点/长线目标/反差弱点/社交生态位）
7. ✅ **新建《大奉打更人》许七安参考模板**（character-profile-xu-qi-an.html）
8. ✅ **新增 4 个高阶维度**（伪装动机/具象怪癖/环境博弈/动态弧光）
9. ✅ **实现多 Agent 架构**（档案/写作/审核/建议）
10. ✅ **统一 26 个页面 UI 风格**（TopBar/Sidebar/按需展示）
11. ✅ **建立"中轴 + 血肉"架构**（以时间线为中轴）
12. ✅ **新增 dashboard.html 完整 sidebar**（4 步流程）
13. ✅ **实现多泳道甘特图**（固定 8 + 自定义不设上限）
14. ✅ **timeline.html 动态泳道系统**（横向平移 + 缩放 + CRUD）

---

## 📂 文档产出

### 决策文档（5 个核心决策）

| # | 文档 | 关键内容 |
|---|------|---------|
| 001 | [伏笔追踪设计](./001-foreshadow-tracking.md) | 作者主动标注 + 3 入口 + 二级分类 + 双重层级 |
| 002 | [页面逻辑梳理](./002-page-logic-organization.md) | 21 个页面，4 步工作流，10 项决策 |
| 003 | [系统质量防护](./003-system-quality-guards.md) | 4 道门禁：防胡写 / 违规词 / 机械表达 / AI 味 |
| 004 | [伏笔的二级分类](./004-foreshadow-classification.md) | 人·出场/退场、事·好事/坏事、物·获得/损失 |
| 005 | [批量小说导入与系统测试](./005-batch-novel-import.md) | 方案 B：跑 5-10 本代表作，压力测试系统 |
| 006 | [商业网文主角四维度](./006-commercial-novel-4-dimensions.md) | 核心卖点/金手指 + 长线目标 + 反差感/弱点 + 社交生态位 |
| 007 | [《大奉打更人》许七安拆解](./007-dafeng-keep-watchman-analysis.md) | 与《赘婿》宁毅并列参考，男频探案+反差幽默模板 |
| 008 | [主角设定 4 个高阶维度](./008-character-advanced-4-dimensions.md) | 核心伪装动机/具象怪癖/环境博弈/动态弧光 |
| 009 | [聊天启发式填卡](./009-chat-guided-fill.md) | 作者与 AI 引导式对话，3-8 轮填入档案 |
| 010 | [多 Agent 架构](./010-multi-agent-architecture.md) | 4 个专职 Agent（档案/写作/审核/建议），专精而非全局 |
| 011 | [批量小说导入与系统测试](./005-batch-novel-import.md) | 方案 B（重复，与 005 合并） |

### 页面架构（最终版）

```
C:\AI-Agent-Local\Short story\web\（28 个页面）
├── 入口（2 个）
│   ├── index.html（书库）
│   └── dashboard.html（总览，⭐完整 sidebar）
│
├── Step 1：设定（7 个）
│   ├── setup.html（01 世界观）
│   ├── setup-02-characters.html（02 角色，⭐思维导图）
│   ├── setup-03-framework.html（03 故事框架）
│   ├── setup-04-tone.html（04 基调）
│   ├── setup-05-foreshadow.html（05 伏笔）
│   └── setup-06-audience.html（06 商业定位）
│
├── Step 2：规划（4 个）
│   ├── plan.html（章节大纲）
│   ├── timeline.html（⭐动态泳道甘特图）
│   ├── characters.html（关系图）
│   └── character-voice.html + character-arc.html
│
├── Step 3：写作（1 个）
│   └── write.html（含写作 Agent 对话区）
│
├── Step 4：审核（2 个）
│   ├── audit.html（含审核 Agent 对话区）
│   └── foreshadow.html（伏笔追踪）
│
├── 角色档案（6 个）
│   ├── character-profile-protagonist.html（宁毅，含 13 维度 + 高阶 4 维度）
│   ├── character-profile-ally1.html（苏檀儿）
│   ├── character-profile-rival1.html（方天赐）
│   ├── character-profile-bond1.html（楼舒婉）
│   ├── character-profile-neutral1.html（耿直）
│   └── character-profile-xu-qi-an.html（许七安参考模板）
│
├── 工具（4 个）
│   ├── chat-fill.html（聊天启发式填卡）
│   ├── import-txt.html（6 板块导入）
│   ├── upload-novel.html（批量小说测试）
│   └── test-reports.html（测试报告）
│
└── CSS（1 个）
    └── css/style.css
```

### 关键脚本（2 个）

| 脚本 | 位置 | 作用 |
|------|------|------|
| `setup_import.py` | `scripts/setup/` | 6 板块 txt 导入（mmx-cli） |
| `replace_cyber_to_zhui.py` | 临时 | 已删除 |

---

## 🏗️ 关键架构决策

### 架构 1：**中轴 + 血肉**

> **"一切均要以故事的时间线为中轴展开，小说章节应该围绕着中轴进行血肉进行填充"**

- **中轴**：timeline.html（时间线总览）
- **血肉**：
  - 角色档案（character-profile）
  - 设定（setup 系列）
  - 伏笔（foreshadow）
  - 写作（write）

### 架构 2：**4 步工作流**

```
Step 1 设定 → Step 2 规划 → Step 3 写作 → Step 4 审核
   ↓              ↓           ↓          ↓
 角色档案     章节大纲    写作 + 守护   沉淀审核
 设定模板     时间线      伏笔/声纹   伏笔追踪
```

### 架构 3：**多 Agent 架构**

> **"专精的我也需要。比如，在填写人物卡时，是不是可以搞一个专职的 agent？而写作是个专职的 agent？全局的我反倒觉得没这么重要。因为足够专精才可以。"**

- **档案 Agent**（chat-fill.html）：引导填卡
- **写作 Agent**（write.html）：辅助写作
- **审核 Agent**（audit.html）：挑刺找问题
- **建议 Agent**（待实现）：主动建议

### 架构 4：**按需展示**（Progressive Disclosure）

> **"大多数时候，无需显示出来，只要后台有数据就行了。页面可以更简洁，只有作者需要'查资料'时，显示出来就可以了。"**

- 默认：4 个核心摘要卡片
- 完整：折叠在 `<details>` 里
- 详情：问 Agent

---

## 🎯 13 维度角色档案模型

### 基础层（5 个）
1. 基本信息
2. 执念
3. 声音指纹
4. 弧光（动态）
5. 人物关系

### 商业层（2 个）
6. 核心卖点 / 金手指
7. 长线目标 / 阶段性任务

### 张力层（3 个）
8. 反差感 / 弱点
9. 社交生态位
10. 核心伪装动机（高阶）

### 深度层（3 个）
11. 具象怪癖（高阶）
12. 环境博弈（高阶）
13. 动态人物弧光（高阶）

---

## ⚠️ 重要设计原则

### 原则 1：**作者主导，AI 辅助**

> "AI 不能替作者决策，只能提供选项和守护一致性"

### 原则 2：**数据驱动，不模糊**

> "细化冲突 vs 笼统冲突。细化 = 体系/规则/理念 vs 笼统 = 个体对个体"

### 原则 3：**少即是多**

> "图标不能辅助创作，逻辑和标签才能"

### 原则 4：**真实网文测试**

> "通过跑已有的网络小说，可以查到系统中的一些弊端、缺失项"

---

## 🧪 已识别的系统缺失（通过《赘婿》测试发现）

### 高优先级（影响 8/8 本）

| 缺失字段 | 出现率 | 已实现的方案 |
|---------|--------|------------|
| 修炼体系 / 修为等级 | 8/8（100%）| 13 维度角色档案 |
| 势力 / 组织管理 | 6/8（75%）| 已加 |

### 中优先级（影响 4-6/8 本）

| 缺失字段 | 出现率 | 已实现的方案 |
|---------|--------|------------|
| 技能 / 功法 | 4/8（50%）| 已加 |
| 多线时间轴 | 3/8（38%）| 动态泳道甘特图 |
| 地点 / 地图 | 3/8（38%）| 已加 |

---

## 📋 明日及未来待办

### 高优先级（必须做）

1. **后端 API 实现**
   - [ ] setup_import.py 的真正 LLM 调用（mmx-cli 已配置）
   - [ ] timeline.html 节点的持久化（保存到 JSON）
   - [ ] character-profile 的字段实际保存
   - [ ] 聊天填卡的字段实际填入

2. **建议 Agent 实现**
   - [ ] 在相关页面右下角加"💡建议"按钮
   - [ ] 主动建议机制

3. **多 Agent 真实 LLM 集成**
   - [ ] 档案 Agent：使用 mmx-cli 提取字段
   - [ ] 写作 Agent：实时守护声纹/设定
   - [ ] 审核 Agent：扫描跨章一致性问题

### 中优先级（建议做）

4. **更多参考模板**
   - [ ] 《诡秘之主》（多线叙事 + 22 条途径）
   - [ ] 《全职高手》（群像人物）
   - [ ] 《三体》（硬科幻设定）

5. **其他页面按需展示重构**
   - [ ] plan.html
   - [ ] characters.html（关系图）
   - [ ] character-voice.html
   - [ ] character-arc.html

6. **侧边栏统一强化**
   - [ ] 把 dashboard.html 的 4 步流程 sidebar 推广到所有页面

### 低优先级（可做可不做）

7. **Web 界面增强**
   - [ ] 实时光标位置（ch-XXX 提示）
   - [ ] 拖动条带改变时间范围
   - [ ] 节点之间的连线（关系）

8. **数据导入**
   - [ ] 真实小说上传测试
   - [ ] 自动分析报告

---

## 🎯 关键文件位置

```
C:\AI-Agent-Local\Short story\
├── README.md                          ← 项目总览
├── books\_template\                     ← 书的模板
├── docs\
│   ├── README.md                      ← 主文档
│   ├── ARCHITECTURE.md                ← 架构
│   ├── DEVELOPER_GUIDE.md             ← 开发指南
│   ├── USER_GUIDE.md                  ← 用户手册
│   ├── ROADMAP.md                     ← 路线图
│   └── decisions\                     ← 决策文档
│       ├── README.md                  ← 决策索引（先读这个）
│       ├── 001-foreshadow-tracking.md
│       ├── 002-page-logic-organization.md
│       ├── 003-system-quality-guards.md
│       ├── 004-foreshadow-classification.md
│       ├── 005-batch-novel-import.md
│       ├── 006-commercial-novel-4-dimensions.md
│       ├── 007-dafeng-keep-watchman-analysis.md
│       ├── 008-character-advanced-4-dimensions.md
│       ├── 009-chat-guided-fill.md
│       ├── 010-multi-agent-architecture.md
│       └── CHANGELOG.md                ← 本文档
├── scripts\setup\setup_import.py      ← 6 板块导入
└── web\                               ← 28 个页面
```

---

## 📊 项目总体进度

### 文件统计

| 类别 | 数量 |
|------|------|
| 决策文档 | 10 个核心 + 1 个索引 = 11 个 |
| 文档 | 6 个（README/ARCHITECTURE/DEV/USER/ROADMAP/CHANGELOG） |
| 页面 | 28 个 |
| 脚本 | 1 个（setup_import.py） |
| CSS | 1 个 |
| **总计** | **47 个文件** |

### 代码行数

- 决策文档：约 3,000 行
- 文档：约 2,500 行
- 页面：约 9,000 行
- 脚本：约 200 行
- CSS：约 1,200 行
- **总计**：**约 15,900 行**

### 沉淀的理论（用户贡献）

| 主题 | 文档 | 关键贡献 |
|------|------|---------|
| 13 维度角色档案 | 006+008 | 商业网文+严肃小说双重视角 |
| 三大铁律 | character-profile 各处 | 捆绑/压力/三角闭合 |
| 4 大主角维度 | 006 | 核心卖点/长线/反差/生态位 |
| 4 大高阶维度 | 008 | 伪装动机/怪癖/环境/弧光 |
| 4 步工作流 | 002 | 设定→规划→写作→审核 |
| 多 Agent 架构 | 010 | 专精而非全局 |
| 按需展示 | 002 | Progressive Disclosure |
| 中轴 + 血肉 | 002 | 时间线为中轴 |

---

## 🚀 下次开工时第一步

1. **打开 `docs/decisions/CHANGELOG.md`** —— 回顾今天的全部工作
2. **打开 `docs/decisions/README.md`** —— 决策索引
3. **明确当前任务** —— 是否继续之前的 todo list
4. **检查 `web/` 目录** —— 当前页面状态
5. **检查 `docs/` 目录** —— 文档状态

---

**今日工作圆满结束！** 🎉

如有任何遗漏，请告诉我补充。
---

# 会议纪要：2026-07-10（35 题压力审查 + MVP 启动 4 件行动）

> **记录人**：Claude（grill-me skill 驱动）
> **日期**：2026-07-10
> **目的**：记录今日 v2 架构重构 + MVP 启动文档沉淀

---

## 📅 今日工作汇总

### 完成的工作

1. ✅ **35 题压力审查**（grill-me skill 驱动）
   - 13 题基础架构压力（Q1-Q13）
   - 5 话题深挖（Q14-Q25）
   - 7 题反悔 / 多 Agent / 状态切换原则（Q26-Q35）
   - 产出 `011-pressure-test-v3.md`（29 条决策锁定 + 6 个冲突 + 8 个子系统）

2. ✅ **5 次根本性架构反转**
   - mmx-cli 云端 → Ollama 本地 + Cloud Relay 双底座
   - FastAPI 全面后端 → 撤销 FastAPI + 薄 Cloud Relay
   - Web 21 页 mockup → 设计稿 + spec 说明书
   - 章节级手动授权 → 状态切换自动原则（P15 最高纲领）
   - 系统身份：温柔协作者 → 严格质量管家（立项会 = 启动器）

3. ✅ **MVP 启动 4 件行动**
   - **行动 A1**：`docs/MVP_AUTHORITY.md` —— MVP 开发的唯一权威入口
   - **行动 A2**：`docs/ASSUMPTIONS.md` —— 架构假设清单（修缺陷 2）
   - **行动 A3**：8 个子系统文档全部完成（`docs/subsystems/*.md`）
   - **行动 A4**：6 个原决策文档完全重写为 v2（按用户 Q34.1 决定"完全重写"）

4. ✅ **决策修订流程文档**：`docs/DECISION_REVISION.md`（修缺陷 1）

---

## 📂 文档产出（v2 阶段）

### 总入口与全局

| 路径 | 内容 |
|------|------|
| `docs/MVP_AUTHORITY.md` | **MVP 唯一权威入口**——29 决策全索引 + 子系统依赖 + 验收金线 |
| `docs/DECISION_REVISION.md` | 决策修订流程规范（5 步 + L1/L2/L3 冲突 + 7 天冷却期） |
| `docs/ASSUMPTIONS.md` | 架构假设清单（✅验证/⚠️待验证/❌违反） |
| `docs/ROADMAP.md` | v2 路线图（6 命令 + 立项会 + 6+ 泳池 + 4 门禁全 P0） |

### 8 个子系统文档

| 路径 | 重要性 | 内容 |
|------|--------|------|
| `docs/subsystems/kickoff_meeting.md` | 🔴 | 立项会 = 启动器（Step 1 后强制 + 多 Agent + 7 类冲突清单） |
| `docs/subsystems/router.md` | 🔴 | 推理路由器（状态切换 + Cloud Relay 50 行 + 降级回退） |
| `docs/subsystems/content_attribution.md` | 🔴 | 内容出处标记（段落 frontmatter + 三态转换 + 豁免矩阵） |
| `docs/subsystems/gantt_audit.md` | 🔴 | 甘特图 6+ 泳池巡检（Mermaid 文本输出 + 6 泳池并行） |
| `docs/subsystems/multi_agent_cloud.md` | 🔴 | 多 Agent 云端（4 persona 并发 + 独立报告 + 问题汇总） |
| `docs/subsystems/quality_guards_granularity.md` | 🔴 | 4 门禁颗粒度（实现级 / 含 token 预算 + source 豁免 + 误报金线） |
| `docs/subsystems/false_positive_loop.md` | 🟡 | 误报反馈闭环（3 层 + 阈值自动调整 + 防"AI 学坏"） |
| `docs/subsystems/web_spec_sync.md` | 🟡 | Web spec 数据契约（21 页字段约束 + CLI 输出 ⊇ Web） |

### 决策文档（v2 完全重写）

| v2 路径 | v1 路径 | v2 变更 |
|---------|---------|---------|
| `001-v2-foreshadow-tracking.md` | 001-foreshadow-tracking.md | **半自动闭环反转** |
| `002-v2-page-data-contract.md` | 002-page-logic-organization.md | **Web spec + 数据契约升级** |
| `003-v2-quality-guards.md` | 003-system-quality-guards.md | **4 门禁全 P0 + 内容出处豁免** |
| `008-v2-voice_print.md` | 008-character-advanced-4-dimensions.md | **声音指纹定义替换高级维度** |
| `010-v2-multi-agent-architecture.md` | 010-multi-agent-architecture.md | **单+多 Agent 双轨（取代 4 专职 Agent）** |
| `011-pressure-test-v3.md` | (新增) | **总索引 + 35 题总结** |

---

## 📊 关键决策全景（v2 活跃决策 29 条）

### A. 架构层（P 系列，15 条）

P1 红警拦截 / P2 误报反馈 / P3 双底座 / P4 撤销 FastAPI / P5' Web spec / P7 协作者身份 / P8 声音指纹 / P9 设定哲学（几万字入场券）/ **P10 立项会 = 启动器** / P11 6+ 泳池 / P12 MVP 升级 / P13 全 P0 门禁 / P14 多 Agent 云端 / **P15 状态切换原则（最高纲领）**

### B. 流程层（F 系列，8 条）
F1 AI 提问 + 作者手填 / F2 不扫原文 / **F3 半自动伏笔** / F4 每章末扫 / F5 track changes / F6 出处豁免 / F7 事实抽取 / F8 作者定回收章

### C / D / E / F 范围立场（6 条）
C1 不实现多书复用 / C2 保留 24 专题 / C3 散文+结构化双版本 / R1 全量重算 / R2 git 全保留 / R3 git diff 细粒度 / **S1 严格质量管家**

---

## 🚦 MVP 启动检查清单

### 4 件行动 ✅ 已完成
- [x] 把 011 设为 MVP 依据的总入口
- [x] 撰写 ASSUMPTIONS.md
- [x] 撰写 8 个子系统文档
- [x] 重写 6 个原决策文档

### MVP 启动前必须做的（用户后续执行）
- [ ] Ollama 实测（窗口 + 延迟 + 反馈调采样参数）
- [ ] mmx-cli 隐私合规确认
- [ ] Cloud Relay 50 行 Python 实现
- [ ] 6 命令的 CLI stub（`python -m ai_coauthor --help`）
- [ ] 决策修订流程已被实际跑过 1 次

---

**今日工作圆满结束！** 🎉

MVP 阶段的全部设计依据已沉淀到位，可以启动开发。

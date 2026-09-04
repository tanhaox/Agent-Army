# digital_human · 文档总索引

> 建立于 2026-08-27（全项目 md 盘点归类）。本文件是**所有 md 文档的唯一入口**——找文档先来这里。
> 存放规则见下方「二、存放规则」；新文档落位前先读规则，改完在本索引补一行。

---

## 一、快速导航（按用途找）

| 你要找什么 | 去哪 |
|---|---|
| 项目现在什么状态 / 待办 | [status/](status/)（状态总览 / 进度看板 / backlog） |
| 某功能怎么设计的 | [design/](design/)（设计方案 / 实施方案） |
| 系统怎么用 / 某模型怎么调 | [guides/](guides/)（系统结构总览 / 模型手册 / 实验定稿依据） |
| 拆解报告 / 模板套路 | [teardown/](teardown/) |
| 某次改进的完整记录 | [improvements/](improvements/)（`已完成-日期-主题` 命名） |
| 合规规则库原文 | [compliance/](compliance/)（豆包规则库各发） |
| 老文档 / 已完结项目 | [archive/](archive/) |
| Claude Code 交接记录 | [claude-code-handoffs/](claude-code-handoffs/) |
| 变更时间线 | [../CHANGELOG.md](../CHANGELOG.md)（根目录） |
| 开发者导览 | [../README.md](../README.md)（根目录） |

## 二、存放规则（docs/ 各文件夹）

### docs/ 根目录
**只放 `INDEX.md`（本文件），不散放任何文档。** 新文档必须落进下列子文件夹之一。

### status/ — 项目状态与待办（活文档，高频更新）
- **内容**：状态总览、进度看板、backlog（ID 编号待办）、迁移等运维清单。
- **命名**：语义名即可（`backlog.md`、`项目状态总览.md`）。
- **生命周期**：随项目演进持续更新；彻底过期的条目移入 `archive/`。

### design/ — 设计方案（某功能"怎么做"的定稿依据）
- **内容**：设计方案、实施方案、schema 设计、提示词框架改造（如七层模板定稿）。
- **命名**：`<主题>-设计方案.md` / `<主题>-实施方案.md` / `<主题>schema设计.md`。
- **生命周期**：方案落地后保留作依据；被新方案整体取代的移入 `archive/`。
- **注意**：代码 docstring 常引用本文件夹路径（`docs/design/xxx.md`），移动文件须同步改引用。

### guides/ — 指南与定稿知识（"怎么用 / 权威参数"）
- **内容**：系统结构总览、模型使用手册、实验定稿依据（如 TTS 情绪 α 定稿值）。
- **命名**：语义名 / 英文原名（`deepseek_v4_model_guide.md`）。
- **判别**：是"长期可查的知识"→ guides；是"某功能的蓝图"→ design。

### teardown/ — 拆解与复刻参考
- **内容**：参考片拆解、剪映模板拆解、套路/配方聚合分析。
- **命名**：`<对象>-<主题>.md`（`剪映模板拆解-45期-音字稿协同.md`）。
- **关联**：单条拆解的原始报告由 ref-teardown skill 落 `sandbox/reports/`（见下），本文件夹放**聚合后的知识**。

### improvements/ — 改进与排障记录（一次一篇，写完即冻结）
- **内容**：架构重构记录、bug 修复记录、审计盘点、提示词阶段定稿。
- **命名**：`已完成-<日期>-<主题>.md`（进行中的用 `进行中-` 前缀，完成后改名）。
- **生命周期**：**只增不改**——历史记录不回头改内容（路径失效属正常）；引用它的新文件以本索引为准。

### compliance/ — 合规规则库原文
- **内容**：豆包规则库各发原文（`豆包规则库-第N发.md` / `-拆书线第N发.md`）。
- **规则**：只存**原文存档**；生效规则在 `config/compliance_*.json`，加词改配置不改这里。

### archive/ — 归档（已完结 / 已失效）
- **内容**：过期立项文档、调研报告、旧执行清单、迁移走的旧项目清单。
- **规则**：移入即冻结，不再更新；删除须走回收站。

### claude-code-handoffs/ — Claude Code 会话交接
- **内容**：跨会话交接的任务卡（`ID-XXX-<主题>.md`）。

### refs/ — 外部参考仓（只读，不归类）
- **内容**：整仓引入的外部项目（如 cyxj-hyperframes）及其自带文档。
- **规则**：**保持原结构，不拆散、不重命名、不建索引**；内部结构由原项目自述。

## 三、docs/ 之外的 md（原地存放，不移动）

| 位置 | 文件 | 为什么留在原地 |
|---|---|---|
| 根目录 | `README.md` | 开发者导览，git/平台约定位置 |
| 根目录 | `CHANGELOG.md` | 变更时间线，git/平台约定位置 |
| `sop/` | `ComfyUI出图规范.md`、`Pexels素材合规.md`、`README.md` | md 与同目录 html SOP 配套成体系（`sop/XX-关键词.html`） |
| `sandbox/reports/` | `<视频id>_analysis.md` / `_teardown.md` ×5 | ref-teardown skill 固定输出位（`SKILL.md` 约定），新报告持续落此 |
| `data/jy_mining/` | `summary.md` | `scripts/mine_jy_templates.py` 脚本产物，重跑即覆盖 |
| `_ref_OpenMontage/` 等 `_ref_*` | 数百个 | 外部参考仓整体快照（待回收），只读 |
| `.pytest_cache/` | `README.md` | pytest 自动生成缓存 |

## 四、全量索引

### status/
- [backlog.md](status/backlog.md) — ID 编号待办总账（ID-001~050+），功能历史查这里的 ID
- [项目状态总览.md](status/项目状态总览.md) — 当前阶段 / 技术栈 / 模块全景
- [项目进度看板.md](status/项目进度看板.md) — 待办优先级 / 扩展方向落点
- [迁移准备清单.md](status/迁移准备清单.md) — 2026-08-22 数字人系统整机迁移清单（同盘符方案 A）

### design/
- [素材层2.0-实体驱动管线.md](design/素材层2.0-实体驱动管线.md) — 实体六类路由+油管入库+靶心调取（2026-08-28 首跑贯通，实验态待接产线）
- [证据图管线-设计方案.md](design/证据图管线-设计方案.md) — 搜图总闸→扫图打标→导演闸门→Ken Burns+图源角标 evidence_image 全链（2026-09-04）
- [模板入产线-风格页评审门.md](design/模板入产线-风格页评审门.md) — 新模板必须先过风格候选页评审（含「杂志风预览页面」命名约定 + 八处接线清单指引）
- [剪映草稿产线-设计方案.md](design/剪映草稿产线-设计方案.md) — J1 轨道搬运 / J2 特效产线 / J3 草稿直出
- [合规审查Pass-设计方案.md](design/合规审查Pass-设计方案.md) — 洗稿/拆书合规 Pass 流水线
- [合规统一词库-全系统入口.md](design/合规统一词库-全系统入口.md) — `compliance_common.json` 唯一事实源架构
- [数字人海报封面系统-设计方案.md](design/数字人海报封面系统-设计方案.md) — 封面/海报生成系统
- [拆书项目-实施方案.md](design/拆书项目-实施方案.md) — 拆书挂小黄车全链（书库→L0 蒸馏→六集脚本）
- [蒸馏产物schema设计.md](design/蒸馏产物schema设计.md) — 两级蒸馏 L0/L1 schema（book_service 权威依据）
- [p5_情绪标注升级方案.md](design/p5_情绪标注升级方案.md) — P5 情绪字典 / 8 维向量设计（P1-P3 部分已被砍除，见文首注记）
- [laotan_prompt_改造中-20260814.md](design/laotan_prompt_改造中-20260814.md) — laotan-tech 七层框架定稿过程（现行 `config/laotan-tech_7layer_v2.txt` 的由来）

### guides/
- [系统结构总览.md](guides/系统结构总览.md) — 全系统模块/数据流总览（新人入口）
- [deepseek_v4_model_guide.md](guides/deepseek_v4_model_guide.md) — DeepSeek V4 双模型使用手册
- [tts_emotion_experiments.md](guides/tts_emotion_experiments.md) — IndexTTS2 音色-情绪实验（**α 定稿值与音色基准坑的权威依据**）

### teardown/
- [参考片复刻兵器谱.md](teardown/参考片复刻兵器谱.md) — 参考片拆解结论聚合（证据在 `sandbox/reports/`）
- [剪映模板套路分析-效果配方库.md](teardown/剪映模板套路分析-效果配方库.md) — 29 模板效果配方 R1~R8+（J2 种子，`data/jy_effect_catalog.json`）
- [剪映模板拆解-45期-音字稿协同.md](teardown/剪映模板拆解-45期-音字稿协同.md) — 45 期音字稿协同拆解
- [剪映模板拆解-学习25期-抖音是小鼎呀.md](teardown/剪映模板拆解-学习25期-抖音是小鼎呀.md) — 25 期完整拆解（写入路径实验样本）

### improvements/（34 篇，按日期序）
- [已完成-20260905-HF身份互动卡入产线与逐字闸门.md](improvements/已完成-20260905-HF身份互动卡入产线与逐字闸门.md) — 06/07 两卡入产线(财经线专用) + 引用逐字闸门三层 + 模板接线八处清单定型(⑧template_filler 白名单=渲染原始占位符实锤) + 两次产线事故复盘
- [已完成-20260901-素材线切片质量攻坚与垃圾出清.md](improvements/已完成-20260901-素材线切片质量攻坚与垃圾出清.md) — 切片 8 修(切点/兜底/GOP/窗容差/闪字/音画) + is_real_footage 判据 + 三轮出清(库8780→5000) + CC 字幕轴决策
- [已完成-20260901-三大文件架构拆包.md](improvements/已完成-20260901-三大文件架构拆包.md) — jy_draft_service/boost_service 拆包 + orchestrator 三分 (函数原样搬运零行为变更)
- [已完成-20260901-安全密钥迁移与代码健康清理.md](improvements/已完成-20260901-安全密钥迁移与代码健康清理.md) — siliconflow key 入 .env / 死代码清理 / 回收站函数三合一(safe_trash 永久删除红线违规修复) / 安全扫描
- [参考-20260807-Python大文件架构重构-规范.md](improvements/参考-20260807-Python大文件架构重构-规范.md) — 大文件拆包规范（2026-08-08 重构批的依据）
- [审计-孤岛孤儿盘点-20260827.md](improvements/审计-孤岛孤儿盘点-20260827.md) — 孤岛/孤儿资产盘点与清理记录（遗留：`_ref_*` 待回收）
- 已完成-20260726 ~ 已完成-20260813 共 24 篇：4层产物集成测试 / LTX23端到端 / IndexTTS2对照测试 / ID002视觉导演Agent2 / 全项目排查 / 素材生命周期 / 架构重构×13（alignment/composition/director×4/gpu_service/pexels/routers/slot_workflows/tts_client/video_tagging）/ P线本地碰撞ID034 / 抽帧修复 / 本地碰撞门槛 / P5情绪标注千问flash / 老谭提示词精进（[目录清单](improvements/)）
- [爆品改造-阶段提示词.md](improvements/爆品改造-阶段提示词.md) — 三 Pass 提示词定稿（历史参考，现行版在 `app/services/boost_service.py`）
- [视频数据记录-20260812.md](improvements/视频数据记录-20260812.md) / [视频脚本收录-20260812.md](improvements/视频脚本收录-20260812.md) — 发布数据与脚本存档
- test_input/ — 提示词调优的输入样本（原稿/口播稿/Pass1 提示词）

### compliance/（9 发）
- [豆包规则库-第1~3发.md](compliance/)（新闻/科技线）+ [豆包规则库-拆书线第1~6发.md](compliance/)（拆书线）— 原文存档，生效版在 `config/compliance_rules_*.json`

### claude-code-handoffs/
- [ID-003-pexels-resolve.md](claude-code-handoffs/ID-003-pexels-resolve.md) — Pexels 素材合规排障交接
- [ID-032-director-catalog-decouple.md](claude-code-handoffs/ID-032-director-catalog-decouple.md) — 导演台目录解耦交接

### archive/（24 篇，冻结）
- 早期立项/调研：数字人计划调研更新版 / 自动化数字人新闻播报-本地部署方案 / 计划收益测算 / 执行计划清单 / YT各语种频道盈利性调研 / 什么是优秀的短视频系列×5
- 早期跑通记录：LTX23单音频多图分镜 / M0-GPU-checklist / M0-W1-D1-GPU自检报告 / TTS栈部署记录 / pose问题规律 / 数字人多维度定型图生成器跑通记录 / test_report_roles
- [projects-migrated-20260827.md](archive/projects-migrated-20260827.md) — 迁 G 盘的 23 个旧项目清单（~418MB）

### 根目录与原地存放
见「三、docs/ 之外的 md」。

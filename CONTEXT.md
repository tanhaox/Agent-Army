# AI-Agent-Local

AI 代理和技能开发平台，管理 51 个 AgentSkill 和 5 个本地 Web 服务。通过优先级触发体系让 Claude Code 在正确的场景自动激活正确的 skill。

## Language

**Skill**:
一个 Markdown 文件（SKILL.md），包含 YAML frontmatter 和行为指令，教 Claude Code 如何在特定场景下完成任务。每个 skill 通过 description 字段中的 "Use when:" 条件自动触发。
_Avoid_: 技能、插件、能力、command、prompt

**Active Trigger**:
SKILL.md 的 description 字段中 "Use when: (1) ... (2) ... NOT for: ... [P:N]" 格式的触发条件。决定 skill 何时被自动调用、何时不被调用。
_Avoid_: 触发词、自动调用、关键词匹配

**Priority System**:
五级优先级体系 P:5→P:1，用于裁决多个 skill 同时被触发时的竞争。P:5=关键基础设施 > P:4=安全守卫 > P:3=领域专家 > P:2=过程增强 > P:1=后台支撑。
_Avoid_: 权重、排名、等级

**Registry**:
CLAUDE.md 中的 "Skill 自动加载注册表" 表格，列出全部 51 个 skill 的名称、来源和触发场景。每次新会话启动时加载。
_Avoid_: 清单、列表、目录

**Service**:
由 service_manager 管理的本地 Web 应用，监听特定端口提供服务（如 Ollama AI :5006、OCR :5002）。
_Avoid_: 进程、服务器、应用、daemon

**Agent**:
由 Claude Code 或 OMC 系统派生的子代理（sub-agent），独立执行搜索、探索或代码生成任务。
_Avoid_: worker、进程、线程、bot

**OMC** (oh-my-claudecode):
核心 skill 编排层，管理 agent 协作、工具路由、提交协议和管道。v4.13.6。
_Avoid_: 编排引擎、调度器、框架

**Project**:
位于 projects/skills/、projects/apps/ 或 projects/tools/ 下的代码包，实现一个独立的 skill 或应用。
_Avoid_: 仓库、模块、包

**Context**:
一个代码单元（仓库或子目录），拥有独立的 CONTEXT.md 和 docs/adr/，描述其领域语言和架构决策。
_Avoid_: 域、边界、子系统

**ADR** (Architecture Decision Record):
记录在 docs/adr/ 中的架构决策文档，按 0001-slug.md 编号。只记录难以逆转、脱离上下文会令人费解、来自真正权衡的决策。
_Avoid_: 设计文档、技术方案、会议纪要

**Three-Place Unity** (三地统一):
强制执行的部署纪律：代码只能在本地修改 → git push 到 GitHub → 服务器只做 git pull。禁止直接修改服务器文件。
_Avoid_: CI/CD、部署流水线、发布流程

**ScriptForge**:
AI-Agent-Local 的子项目，提供剧本生成、ASR、TTS、DeepSeek 集成等能力。
_Avoid_: 剧本工厂、SF

**dandanyi** (单单易):
Next.js 16 + PostgreSQL 航班到达数据管理应用。从本仓库管理，部署于马来西亚服务器。
_Avoid_: 单单、ddy

**miaoying** (秒应):
已归档的旧项目，停止维护（2026-03-05）。服务器目录名 /var/www/miaoying 是历史遗留。
_Avoid_: 秒应项目、my

## Relationships

- 一个 **Skill** 通过 **Active Trigger** 在特定场景被激活
- **Registry** 汇总全部 **Skill** 的 **Priority System** 分级
- **Service** 由 `service_manager` **Skill** 统一管理
- **OMC** 编排多个 **Agent** 协作执行任务
- 每个 **Project** 可以包含多个 **Skill**
- **Context** 通过 CONTEXT.md + ADR 记录领域语言和决策
- **Three-Place Unity** 约束从本地到服务器的代码流向
- **ScriptForge** 和 **dandanyi** 是本仓库管理的独立子项目

## Example dialogue

> **Dev:** "这个新功能应该做成一个新的 Skill 还是加到现有 Project 里？"
> **Domain expert:** "如果是独立的任务域（如搜索、调试），做成 Skill 放到 user skills。如果是已有 Project 的功能扩展（如给 ollama_ai 加新模型支持），直接改那个 Project。"
>
> **Dev:** "P:3 的 skill 被同时触发时怎么处理？"
> **Domain expert:** "同优先级按领域匹配精度裁决。比如用户说'设计一个登录页面'，frontend-design 和 ui-ux-pro-max-skill 都可能触发，但 frontend-design 匹配'页面'更精确，胜出。"

## Flagged ambiguities

- "Agent" 在项目中既指 Claude Code 子代理又指 Agent_Army 项目中的业务代理 → 已解决：默认指 Claude Code 子代理，Agent_Army 上下文时加前缀
- "服务" 既指本地 Web 服务又指 OMC 基础设施服务 → 已解决：未加限定的"服务"指本地 Web 服务

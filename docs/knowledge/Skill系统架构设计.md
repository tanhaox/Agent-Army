# Skill 系统架构设计

> 来源: 2026-05-07 对话讨论 | 状态: 已实施 | 版本: v3.0

---

## 架构演进历程

### v1.0 — 被动调用
Skill 靠用户打 `/` 命令或 AI 猜测调用。问题：47 个 skill 中只有 6 个有良好触发条件，大多数静默。

### v2.0 — 主动触发
关键发现：Claude Code 通过 SKILL.md 的 `description` 字段判断何时调用 skill。SKILL.md 正文只在被调用后才加载。**所有触发逻辑必须在 description 中。**

### v3.0 — 自动加载注册表
58 个 skill 全部写入 CLAUDE.md "Skill 自动加载注册表"，每次新会话自动加载。

---

## 核心机制

### 1. 主动触发模板

```yaml
description: "<能力描述>. Use when: (1) <场景/关键词>, (2) <场景>, (3) <场景>. NOT for: <排除>. [P:N]"
```

**三要素**:
- **Use when**: 3-5 个可被 Claude 检测的具体条件
- **NOT for**: 1-2 个边界条件防止误触发
- **[P:N]**: 优先级标签，N=1-5

### 2. 五级优先级体系

```
P:5 关键基础设施 → 必须最先触发（self-improvement, clawcn-windows-setup）
P:4 安全守卫     → 防破坏性操作（git-guardrails, karpathy-guidelines, cancel）
P:3 领域专家     → 用户核心任务域（frontend-design, playwright, github, local-ocr）
P:2 过程增强     → 管理其他工作的元技能（plan, tdd, triage, project-auditor, project-fixer）
P:1 后台支撑     → 仅显式需要时触发（setup, debug, skill, verify）
```

### 3. 竞争裁决规则

1. 多个 skill 同时匹配 → 高优先级胜出 (P:5 > P:4 > P:3 > P:2 > P:1)
2. 同优先级 → 按领域匹配精度裁决
3. 触发词越具体，匹配权重越高

### 4. 自动加载注册表

CLAUDE.md 中的集中注册表，按优先级分组：

```
新会话启动 → CLAUDE.md 加载 → 58 个 skill 注册表进入上下文
  → 用户消息匹配 "Use when:" 条件 → 对应 skill 自动激活
```

---

## 设计原则

| 原则 | 说明 |
|------|------|
| 自然语言 | 不需要用户记 `/` 命令，自然语句自动触发 |
| 默认并行 | project-auditor/project-fixer 等默认 6 agent 并行 |
| 中文优先 | 所有 description 使用中文触发条件 |
| 注册表是真相 | CLAUDE.md 注册表是唯一权威 skill 清单 |

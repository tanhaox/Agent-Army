# 外部 Skill 安装与改造流程

> 来源: 2026-05-07 对话讨论 | 适用: 所有新 skill 安装

---

## 标准安装流程

```
发现外部 skill → SSH clone（HTTPS 被墙）→ 阅读源码
  → 中文主动式改造（description 三要素）
  → 安装到 ~/.claude/skills/
  → 注册到 CLAUDE.md 注册表
  → service_manager 重新扫描验证
```

## 改造模板

每个新 skill 的 `description` 必须改造为：

```yaml
description: "<能力描述>. Use when: (1) <场景>, (2) <场景>. NOT for: <排除>. [P:N]"
```

---

## 已安装的外部 Skill 清单

### Matt Pocock 工程流（4 个）

| Skill | P | 能力 |
|-------|---|------|
| `grill-with-docs` | P:3 | 方案审问 + CONTEXT.md + ADR 实时构建 |
| `diagnose` | P:2 | 6 阶段硬 Bug 调试流水线 |
| `to-prd` | P:2 | 对话→PRD 自动合成 |
| `to-issues` | P:2 | PRD→垂直切片 Issue 拆分 |

### Python 代码质量（4 个） — [l-mb/python-refactoring-skills](https://github.com/l-mb/python-refactoring-skills)

| Skill | P | 能力 |
|-------|---|------|
| `py-security` | P:2 | OWASP 漏洞检测修复 |
| `py-code-health` | P:2 | 死代码/重复代码清理 |
| `py-complexity` | P:2 | 圈复杂度降低 |
| `py-refactor` | P:2 | 5 子 skill 全面重构编排 |

### 文件操作（1 个）

| Skill | P | 能力 |
|-------|---|------|
| `code-splitter` | P:2 | 大文件按行范围安全拆分 |

### 行为守则（1 个） — [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)

| Skill | P | 能力 |
|-------|---|------|
| `karpathy-guidelines` | P:4 | 四原则：先想后写/简洁至上/精准修改/目标驱动 |

> ⚠️ Karpathy 原则同时写入 CLAUDE.md 第 6 条编码规范，每次会话自动生效，不依赖 skill 触发。

### 浏览器自动化（5 个） — [jackwener/opencli](https://github.com/jackwener/opencli)

| Skill | P | 能力 |
|-------|---|------|
| `opencli-usage` | - | OpenCLI 命令速查 |
| `opencli-browser` | - | Chrome 浏览器驱动参考 |
| `opencli-adapter-author` | - | 网站适配器编写 |
| `opencli-autofix` | - | 适配器损坏自动修复 |
| `smart-search` | - | 智能搜索路由器（中文） |

---

## 安装注意事项

1. **GitHub HTTPS 被墙** → 永远用 SSH: `git clone git@github.com:owner/repo.git`
2. **gh CLI 不可用** → 用 WebSearch 替代 `gh repo view`
3. **WebFetch 不能访问 github.com** → WebSearch + SSH clone 组合
4. **安装后必须验证** → `service_manager --skills` 确认数量和优先级
5. **description 必须中文** → 否则语义匹配不准

# 003-v2-quality-guards.md — 4 道质量门禁（v2 全部 P0）

> **历史**：原 `003-system-quality-guards.md` 4 道门禁
> **v2 升级**：P13 + F6 + Q25.2（4 道门禁全部 P0；AI 起草豁免）
> **状态**：✅ 当前活跃决策

---

## 🎯 设计目标

为小说创作提供**严格但不阻断创作流**的质量守护。v1 是 4 道门禁 + P0/P1 优先级；v2 是 **4 道门禁全部 P0 + 内容出处豁免**。

---

## 🔴 4 道门禁（v2 全部 P0）

### 1. 🔴 P0 防胡写守护（最高优先级）

详见 `docs/subsystems/quality_guards_granularity.md` §一

- **触发**：writing 状态每段
- **机制**：🔴 红色强制拦截，不解决或手动忽略不能跳过
- **部署**：本地 Ollama 强制（写作时屏蔽云端）
- **与 source 交互**：
  - `author_written` → 完全检查
  - `ai_drafted` → 豁免
  - `author_revised` → 完全检查
- **误报率金线**：< 20%

### 2. 🔴 P0 违规词验证（原 P0）

详见 `docs/subsystems/quality_guards_granularity.md` §二

- **触发**：章节末 + 发布前
- **机制**：发布前必须解决违规词；写作时仅警告
- **部署**：纯本地规则脚本（词典匹配 + 正则）
- **与 source 交互**：所有 source 都检查（合规底线）

### 3. 🟡→🔴 P0 机械表达检测（原 P1 升级）

详见 `docs/subsystems/quality_guards_granularity.md` §三

- **触发**：段落级（规则脚本）+ 章节级（Ollama 抽样）
- **机制**：仅警告（不阻断）
- **检查项**：仿佛 / 忽然 / 不禁 / 蓦然 / 顿时 等模式化词频
- **部署**：本地规则 + Ollama
- **与 source 交互**：所有 source 都检查（AI 起草也容易机械）

### 4. 🟡→🔴 P0 AI 味检测（原 P1 升级）

详见 `docs/subsystems/quality_guards_granularity.md` §四

- **触发**：每章末 + 立项会多 Agent 维度
- **机制**：仅警告（不阻断）
- **检查项**：过度修辞 / 对称结构 / "眼中闪过一抹..." 类 AI 标识
- **部署**：Ollama
- **与 source 交互**：
  - `author_written` → 完全检查（防作者被 AI 污染）
  - `ai_drafted` → 🟢 豁免
  - `author_revised` → 完全检查

---

## 📊 v1 → v2 升级变更

| 门禁 | v1 优先级 | v2 优先级 | 变更说明 |
|------|----------|----------|---------|
| 防胡写 | 🔴 P0 | 🔴 P0 | 不变 |
| 违规词 | 🔴 P0 | 🔴 P0 | 不变 |
| 机械表达 | 🟡 P1 | 🔴 **P0** | 升级 |
| AI 味 | 🟡 P1 | 🔴 **P0** | 升级 |

### 升级理由（Q25.2）

> "全部门禁升 P0"—— 用户原话："机械表达 + AI 味检测升为 P0。与你'top50 冲金线'原则一致"

> 既然项目目标 = 冲 top50 书榜，4 道门禁必须齐全，不能 P1 推迟。

---

## 🔒 内容出处豁免（F6 + content_attribution.md）

### 豁免矩阵

|  | 防胡写 | 违规词 | 机械表达 | AI 味 |
|---|--------|--------|---------|-------|
| author_written | ✅ 检查 | ✅ 检查 | ✅ 检查 | ✅ 检查 |
| ai_drafted | 🟢 豁免 | ✅ 检查 | ✅ 检查 | 🟢 豁免 |
| author_revised | ✅ 检查 | ✅ 检查 | ✅ 检查 | ✅ 检查 |

### 豁免理由

- **防胡写豁免 ai_drafted**：AI 起草时按设定写作，本身就符合设定；豁免防"自己审自己"漏洞
- **AI 味豁免 ai_drafted**：AI 写的内容本来就是 AI 味；查了没意义
- **违规词全检**：合规底线，AI 也受约束
- **机械表达全检**：AI 起草通常机械，必须检查
- **author_revised 全检**：作者已审改，归属作者，承担同等责任

---

## 🎚️ 误报率控制（false_positive_loop）

详见 `docs/subsystems/false_positive_loop.md`

4 道门禁各有误报率金线：

| 门禁 | 目标 | 上限 |
|------|------|------|
| 防胡写 | < 20% | 50%（动态调整） |
| 违规词 | < 5% | 10%（机械匹配基本无误报） |
| 机械表达 | < 30% | 50% |
| AI 味 | < 30% | 50% |

超过上限时触发自动调整阈值 / persona 切换 / 提示用户。

---

## 🚦 触发时机总览

| 时机 | 防胡写 | 违规词 | 机械表达 | AI 味 |
|------|--------|--------|---------|-------|
| **writing 每段** | ✅ | 警告 | ✅ | — |
| **writing 章节末** | ✅（整章复检） | ✅ | ✅ | ✅ |
| **reviewing 立项会** | — | — | — | ✅ |
| **reviewing 跨章审核** | ✅ | ✅ | ✅ | ✅ |
| **发布前** | ✅ | ✅（必须解决） | ✅ | ✅ |

---

## 🧪 测试用例（MVP 必过）

见 `docs/subsystems/quality_guards_granularity.md` §六测试用例

每个门禁至少 3 个测试场景：

1. author_written 命中 / 不命中
2. ai_drafted 豁免生效
3. author_revised 受检

---

## 🔗 关联

- `docs/subsystems/quality_guards_granularity.md` —— 颗粒度规范
- `docs/subsystems/router.md` §二 —— 4 门禁路由规则
- `docs/subsystems/content_attribution.md` §四 —— source 豁免矩阵
- `docs/subsystems/false_positive_loop.md` —— 误报率反馈

---

## 📌 元信息

- **历史决策**：[003-system-quality-guards.md](./003-system-quality-guards.md)
- **变更触发**：P13（4 门禁全 P0）+ F6（内容出处豁免）
- **创建日期（原版）**：2026-07-08
- **v2 创建日期**：2026-07-10
- **重要性**：🔴 关键

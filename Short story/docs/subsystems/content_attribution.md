# content-attribution.md — 内容出处标记子系统

> **决策依据**：F6（35 题压力测试锁定）
> **重要性**：🔴 **关键**（守护豁免 AI 起草内容；MVP 必做）
> **状态**：📋 设计阶段
> **关联**：router.md / false-positive-loop.md

---

## 🎯 系统职责

每个段落必须有一个 `source` 字段标记内容出处。守护系统按此豁免 / 不豁免 AI 起草的内容。

**本质**：解决"自己审自己"的漏洞——AI 起草的内容不应被防胡写守护再检查一遍。

---

## 📋 三种出处 + 一元数据

### 1. `author_written`（作者手写）

- 含义：作者纯手写，未经过 AI 起草
- 守护：完全检查（最强守护）
- 误报后果：必须红色拦截
- 信任度：100%（被守护）

### 2. `ai_drafted`（AI 起草待审）

- 含义：AI 起草完成，作者尚未修改
- 守护：豁免（不检查 AI 起草内容本身）
- 仅检查：是否符合内部一致性（与设定库的内在一致性，不是与"作者意图"的一致性）
- 信任度：低（待审）
- **状态**：作者审改后转 `author_revised`

### 3. `author_revised`（作者审改）

- 含义：AI 起草后，作者修改过
- 守护：完全检查
- 含义：作者已经审过，AI 价值判断已被作者筛选过；守护可以正常检查
- 信任度：高（已被作者筛选）

### 元数据：可选`confidence` 字段（Phase 2+）

- AI 起草时自我评估的"自信度"
- 0-1 标量
- 仅供立项会参考（不是守护判断依据）
- MVP 不实现

---

## 📐 段落级 frontmatter 格式

### Markdown 段落格式

```markdown
<!-- @attribution source="author_written" ts="2026-07-10T14:30:00" -->

主角沈铁衣走进那扇门，看见师父已经倒在地上。

<!-- @attribution source="ai_drafted" ts="2026-07-10T14:35:00" confidence="0.8" -->

师父弥留之际，从怀中掏出一本古籍，递给沈铁衣。
```

### 字段规范

| 字段 | 必须 | 说明 |
|------|------|------|
| `source` | ✅ | `author_written` / `ai_drafted` / `author_revised` |
| `ts` | ✅ | ISO 8601 时间戳 |
| `confidence` | ❌ | 仅 ai_drafted 可选；Phase 2 实现 |
| `agent_persona` | ❌ | 仅 ai_drafted 可选；哪个 persona 起草；Phase 2 |

### 转换规则

| 状态变更 | 触发 | 转换 |
|---------|------|------|
| `author_written` → 同 | 无 | 不变 |
| `author_written` → `author_revised` | 不合法 | 非法转换（写作完成不应改 source） |
| `ai_drafted` → `author_revised` | git diff 检测到段落被修改 | 自动转换 |
| `author_revised` → `author_written` | 只能手动 | 视为"作者认为是纯手写" |

---

## 🛡️ 守护规则（按 source 分类）

### author_written

- 🔴 **完全守护**：所有 4 道门禁都要跑
- 误报后果：必须红色拦截

### ai_drafted

- 🟢 **豁免 AI 味检测**（AI 自己写的，AI 味没有意义）
- 🟢 **豁免防胡写检查**（AI 是按设定写的，本来就对）
- 🟡 **必须检查机械表达**（AI 容易有"仿佛""忽然""顿时"等模式化表达）
- 🟡 **必须检查违规词**（AI 可能违规）
- ⚠️ **检查内部一致性**：与同段相邻的 author_written / author_revised 是否冲突

### author_revised

- 🔴 **完全守护**：等同于 author_written
- 理由：作者修改已"过滤" AI 价值判断；现在内容归属作者

---

## 🔧 实现细节

### 段落识别

- 每个 markdown 段落以空行分隔
- 段落前可以有一个 `<!-- @attribution ... -->` 注释行（必须紧贴段落）
- 守护系统解析时**只读取 frontmatter 标记**，不读段落内容本身（性能优化）

### 自动注入

- 作者用编辑器手写段落 → 默认 `author_written`
- AI 生成段落 → CLI 自动注入 `ai_drafted`
- AI 起草 + 作者修改 → git diff 自动转 `author_revised`

### 默认值（MVP）

如果段落没有 `<!-- @attribution -->` 标记：

- 默认按 `author_written`（最严格守护）
- 但 CLI 启动时**警告**："发现 N 个段落无 frontmatter，已按 author_written 处理"

### 重写特殊处理

- 作者完全重写（删除段落 → 重新写）→ 段落被替换后默认 `author_written`
- git diff 检测"段落消失 + 出现" → **新段落按 author_written**

---

## 📁 文件级 vs 段落级

### 段落级（默认）

```markdown
<!-- @attribution source="author_written" -->

段落 A...
<!-- @attribution source="ai_drafted" -->

段落 B...
<!-- @attribution source="author_revised" -->

段落 C...
```

### 文件级（特殊情况）

当整章都是 AI 起草或作者手写时，可以用文件级 frontmatter：

```markdown
---
source: ai_drafted
created_at: 2026-07-10
---
# 第 50 章

本章所有段落都是 AI 起草待审。
...
```

**冲突规则**：段落级标记优先于文件级。

---

## 🔬 防"自己审自己"漏洞测试

### 漏洞定义

- AI 起草一个金手指设定 `setting: 主角拥有隐身能力`
- 设定库未填
- AI 防胡写守护扫这段 → 因为 `source="ai_drafted"` → 豁免
- 设定库没意识到这是冲突 → **漏洞**

### 漏洞缓解

1. **立项会必看**：`source="ai_drafted"` 的内容**必须**经过立项会复检
2. **继承关系**：AI 起草的金手指必须挂到 `02-characters.md` 或 `01-world.md`，**否则继承不到**
3. **云端协同**：跨章节时云端 AI 再核验一次（前提：作者授权）

### 测试用例

```python
def test_ai_self_draft_does_not_loophole():
    # AI 起草了一段，设定了"主角有隐身能力"
    chapter_text = """
<!-- @attribution source="ai_drafted" -->

主角发现自己突然拥有了隐身能力。
"""
    # 守护不应报错（豁免）
    assert consistency_check(text=chapter_text) == []  # 没问题

    # 但是，检查：隐身能力应该被加入设定库
    settings = load_settings()
    assert "隐身能力" in settings.protagonist.capabilities  # 必须有

    # 如果没继承 → 立项会必须挑出来
    kickoff_report = run_kickoff_meeting()
    assert "ai_drafted 内容未继承" in [issue.type for issue in kickoff_report.issues]
```

---

## 🎛️ 配置开关

`books/<name>/meta.md` 可以配置：

```yaml
attribution:
  enforcement: strict | lenient  # 严格（必须 frontmatter）| 宽松（默认 author_written）
  ai_self_check: true | false   # ai_drafted 是否完全豁免
```

- `enforcement: strict`（默认）：所有段落必须有 frontmatter，缺失警告
- `enforcement: lenient`：缺失默认 author_written，不警告
- `ai_self_check: false`：ai_drafted 不豁免（仅调试用）
- `ai_self_check: true`（默认）：豁免（按上面规则）

---

## 🧪 测试用例（MVP 必过）

1. **AI 起草豁免**：source="ai_drafted" 不被防胡写拦截
2. **作者手写被拦截**：source="author_written" 违规时被拦截
3. **自动状态转换**：git diff 修改 ai_drafted 后转 author_revised
4. **立项会复检**：ai_drafted 内容未被继承 → 立项会报告
5. **段落识别**：无 frontmatter 段落默认 author_written
6. **文件级 frontmatter 优先级**：文件级 + 段落级时，段落级优先

---

## 🔗 关联

- `router.md` —— 路由器在审查段落时读 frontmatter
- `false-positive-loop.md` —— AI 起草豁免后，作者审改变成 author_revised
- `quality-guards-granularity.md` —— 不同 source 的不同门禁触发

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🔴 关键
- **关联决策**：F6 / Q13

---

## 📋 B7 双层 frontmatter 边界澄清

本子系统使用**段落级 frontmatter**（HTML 注释形式）。项目其他地方用**文件级 frontmatter**（YAML）。这有明确的边界与优先级：

### 段落级 frontmatter（本子系统）

```html
<!-- @attribution source="author_written" ts="..." -->

段落内容
```

- **作用范围**：紧邻的单个段落
- **格式**：HTML 注释（`<!-- ... -->`）
- **触发位置**：每个段落前（紧贴）
- **守护系统**：content-attribution 专属

### 文件级 frontmatter（其他子系统）

```yaml
---
kickoff_passed: true
force_local: false
kickoff_decision: must_fix
created_at: 2026-07-10
---
```

- **作用范围**：整个文件 / 整个书（meta.md）
- **格式**：YAML frontmatter（`---\n---\n`）
- **触发位置**：文件最开头
- **其他子系统**：kickoff_meeting / dashboard / state_detector 等

### 优先级规则

- **段落级 > 文件级**：段落级 frontmatter 决定该段豁免，**文件级不影响**
- 段落 frontmatter 缺失时 → 默认按 `author_written` 处理
- 文件级 frontmatter 修改 → 不改变段落 source 字段

### 段落级继承的文件级字段

文件级 YAML 可以为段落提供**默认值**：

```yaml
---
default_attribution: author_written
ai_drafted_allowed: false
chapter_type: climax
---

<!-- @attribution source="author_written" -->

具体段落
```

但段落级**始终覆盖**文件级默认值。

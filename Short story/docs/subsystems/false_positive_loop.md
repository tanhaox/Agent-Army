# false-positive-loop.md — 误报反馈闭环子系统

> **决策依据**：P2 / F3（35 题压力测试锁定）
> **重要性**：🟡 **重要**（防止误报让作者放弃系统）
> **状态**：📋 设计阶段
> **关联**：router.md / content-attribution.md / quality-guards-granularity.md

---

## 🎯 系统职责

解决 "AI 误报频繁 → 作者放弃系统" 的核心风险。

**核心思想**：AI 每次被作者 ignore 的判断，下次应该更明智。这是个**反向训练**闭环。

> 用户原话："AI 误报反馈闭环 —— 每次作者点忽略就记录，反向训练 mmx-cli 的判定阈值"

虽然 mmx-cli 是黑盒不可训练，但**事实上的反向训练**可以通过：

1. **本地 Ollama**：调整采样参数（temperature, top_p）
2. **云端 mmx-cli**：修改 system prompt 中的判定阈值描述
3. **路由器**：动态选择更宽松的 persona

---

## 📋 三层误报闭环

### Layer 1：单次 ignore 记录

```yaml
# logs/false_positives.log
- timestamp: 2026-07-10T14:35:00
  command: consistency_check
  context: chapter_50
  para_text: "主角使用隐身能力..."
  ai_warning: "违反世界观规则：本界无隐身术"
  decision: ignored
  user_reason: "主角金手指是后续要立的新规"
```

### Layer 2：同类误报统计

```yaml
# books/<name>/stats/false_positives.yaml
- warning_type: "world_rule_violation"
  category: "隐身/飞行类"
  total_count: 12
  ignored_count: 8
  ignore_rate: 0.667  # 67% 误报率
  
  action: threshold_lowered
  old_threshold: 0.8
  new_threshold: 0.95
```

### Layer 3：阈值调整触发

```yaml
# books/<name>/config/thresholds.yaml
consistency_check:
  world_rule_violation:
    confidence_threshold: 0.95  # 仅当 confidence > 0.95 才报告
    context_whitelist:
      - "金手指启用"
      - "新规公告"
```

---

## 🔧 三层反馈实现

### Layer 1：单次 ignore 记录

CLI 提供 ignore 命令：

```bash
$ python -m ai_coauthor ignore --id <warning_id> --reason "..."
# 或者 Web "忽略"按钮 → POST /api/ignore
```

记录到 `logs/false_positives.log`。

### Layer 2：统计与分类

每 100 章（或作者主动触发），系统做：

1. 按 warning_type 分组
2. 计算 `ignore_rate`
3. 若 ignore_rate > 50%，进入"阈值调整"候选

### Layer 3：阈值调整

按 warning_type，自动调整：

- **本地 Ollama**：通过 persona 描述里的严格度描述（"宽松"/"严格"）
- **云端 mmx-cli**：修改 system prompt 阈值（"仅当非常确定是冲突时才报告"）
- **路由器**：动态选择

### MVP 简化

Phase 1.MVP 仅实现 Layer 1 + Layer 2（人工审阅，不自动调整）。
Phase 2+ 实现 Layer 3 自动调整。

---

## 📊 误报率的金线（验收标准）

| 误报率 | 系统行为 |
|--------|---------|
| < 20% | 理想范围，无需调整 |
| 20-50% | 自动放宽阈值（Layer 3） |
| 50-80% | 警告作者："AI 在频繁误报，是否调整严格度？" |
| > 80% | 强制重置阈值 + 提示"AI 可能不适合这个任务" |

### 与 system-quality-guards 的协同

- 防胡写（world_rule 类）误报率最高：因为小说就是作者自创规则
- 违规词误报率应该最低（纯规则脚本，机械判断）
- AI 味误报率中等（取决于模型能力）
- 机械表达误报率最低（规则脚本可处理多数）

---

## 🔒 防"AI 学坏"风险

如果反向训练过度：

- AI 越来越宽松 → 守护失效
- "系统趋于沉默"风险

### 防御措施

1. **金线锁定**：误报率最低阈值（如防胡写类不超过 30%）
2. **生效期间隔**：每次阈值调整间隔至少 N 个章节
3. **作者可锁定**：作者可手动锁定阈值，不让 AI 调整
4. **审计日志**：所有阈值调整必须记录到 `books/<name>/config/threshold_changes.log`

---

## 🧪 测试用例

1. **单次 ignore 记录**：作者点忽略 → 写入 logs
2. **同类统计**：100 章后统计 warning_type "world_rule_violation" 的 ignore_rate
3. **自动调整**：误报率 > 50% → 自动放宽阈值
4. **金线锁定**：误报率不能无限宽松到 < 10%
5. **作者手动锁定**：作者改阈值后 AI 不能自动调

---

## 🔗 关联

- `content-attribution.md` —— 被 AI 起草豁免的内容若被 ignore，不会触发误报统计
- `quality-guards-granularity.md` —— 各门禁的误报率金线
- `router.md` —— 阈值调整影响路由器对任务的部署

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🟡 重要
- **关联决策**：P2 / F3 / Q2.1
- **创建日期**：2026-07-10

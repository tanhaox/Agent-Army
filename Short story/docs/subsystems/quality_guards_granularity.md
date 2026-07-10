# quality-guards-granularity.md — 4 道质量门禁颗粒度规范

> **决策依据**：P13（35 题压力测试锁定：4 门禁全部升 P0）
> **重要性**：🔴 **关键**（解决"门禁颗粒度未细化"的根本缺陷）
> **状态**：📋 设计阶段
> **关联**：router.md §二任务类型路由 / content-attribution.md（门禁豁免）

---

## 🎯 系统职责

为 4 道门禁的每一条**细化到可实现级别**。包括：

- 触发时机
- token 预算
- 输入输出格式
- 误报率金线
- 与各 content source 的交互（author_written / ai_drafted / author_revised）
- 与 writing / reviewing 状态的交互

---

## 🔴 门禁 1：防胡写守护（最高优先级）

### 1.1 触发时机

- **每段保存**：在 `write.html` 中作者写完一段（按 Enter+空行）
- **writing 状态实时**：每 30 秒扫一次当前未保存内容
- **章节保存后**：整章保存时全章扫一次
- **作者主动触发**：`Ctrl+S` 或命令

### 1.2 输入

```json
{
  "paragraph_text": "主角沈铁衣隐身进入...",
  "chapter_context": {
    "chapter_id": "chapter_50",
    "previous_paras_summary": "..."
  },
  "settings_relevant": {
    "world_rules": [...],
    "character_settings": [...],
    "foreshadow_state": [...],
  },
  "source": "author_written",  # 见 content-attribution
  "state": "writing"
}
```

### 1.3 输出

```json
{
  "issues": [
    {
      "severity": "🔴",
      "type": "world_rule_violation",
      "category": "本界无隐身术",
      "location": "para_5",
      "text_excerpt": "主角隐身",
      "suggestion": "改为'主角使用道具伪装'"
    }
  ],
  "action": "BLOCK" | "WARN",
  "must_resolve": true
}
```

### 1.4 token 预算

- 写作时实时：4k
- 整章复检：8k

### 1.5 误报率金线

- **目标**：< 20%
- **可接受上限**：50%（与 false-positive-loop 联动）

### 1.6 与 content source 交互

| source | 行为 |
|--------|------|
| `author_written` | 完全检查，🔴 拦截 |
| `ai_drafted` | 豁免（只检查内部一致性） |
| `author_revised` | 等同 author_written |

### 1.7 与状态交互

- **writing**：强制本地，红警拦截
- **reviewing**：本地优先，超时降级云端，结果仅供参考

### 1.8 实现细节

```python
def check_consistency(text, settings, source, state):
    prompt = build_consistency_prompt(text, settings, source)
    backend = "local" if state == "writing" else "auto"
    response = router.infer(task="consistency_check", backend=backend, prompt=prompt)
    issues = parse_issues(response)
    
    if state == "writing" and any(i.severity == "🔴" for i in issues):
        return {"action": "BLOCK", "issues": issues}
    return {"action": "WARN", "issues": issues}
```

---

## 🔴 门禁 2：违规词验证

### 2.1 触发时机

- 章节末（章末保存时）
- 发布前（一次性扫描整本书）
- 写作时实时（仅警告词，不阻断）

### 2.2 输入

```json
{
  "text": "...",
  "policy": {
    "banned_words": ["色情", "政治敏感词..."],
    "soft_warnings": ["血腥", "成人..."],
    "platform_rules": "default"  # 起点 / 番茄 / 微信读书
  },
  "source": "author_written",
  "state": "writing" | "reviewing"
}
```

### 2.3 输出

```json
{
  "banned_violations": [
    {"word": "...", "location": "para_5", "policy_ref": "policy:web_publish"}
  ],
  "soft_warnings": [
    {"word": "...", "location": "para_8", "type": "blood"}
  ],
  "action": "BLOCK" | "WARN",
  "must_resolve": false  # 仅发布前才必须解决
}
```

### 2.4 token 预算

- 0（**纯本地规则脚本**，无需 AI）
- 词典匹配 + 正则即可

### 2.5 误报率金线

- **目标**：< 5%（机械匹配）
- **绝对上限**：10%

### 2.6 与 content source 交互

| source | 行为 |
|--------|------|
| `author_written` | 完全检查 |
| `ai_drafted` | 完全检查 |
| `author_revised` | 完全检查 |

**违规词不豁免任何 source**——保护合规底线。

### 2.7 与状态交互

- **writing**：实时检查，仅警告不阻断
- **reviewing**：发布前全量扫描，违规必阻断

---

## 🔴 门禁 3：机械表达检测

### 3.1 触发时机

- 章节末（章末扫描）
- 写作时每段（如耗时 < 0.5s）

### 3.2 输入

```json
{
  "text": "...",
  "rule_patterns": [
    {"pattern": "\\b仿佛\\b", "threshold": 0.05},  # 频率阈值
    {"pattern": "\\b忽然\\b", "threshold": 0.03},
    {"pattern": "\\b不禁\\b", "threshold": 0.02},
    {"pattern": "\\b蓦然\\b", "threshold": 0.015},
    # ...
  ],
  "source": "author_written"
}
```

### 3.3 输出

```json
{
  "mechanical_expressions": [
    {
      "pattern": "仿佛",
      "count": 5,
      "frequency": 0.062,
      "locations": ["para_2", "para_4", ...]
    }
  ],
  "action": "WARN",  # 永远不阻断，仅警告
  "must_resolve": false
}
```

### 3.4 token 预算

- 章节级（4k）—— 调用 Ollama 抽样
- 段落级（1k）—— 纯正则匹配，不调 AI

### 3.5 误报率金线

- **目标**：< 30%（规则较宽松）
- **可接受上限**：50%

### 3.6 与 content source 交互

| source | 行为 |
|--------|------|
| `author_written` | 完全检查 |
| `ai_drafted` | 完全检查（AI 容易机械） |
| `author_revised` | 完全检查 |

### 3.7 与状态交互

- **writing**：实时（仅规则脚本，仅警告）
- **reviewing**：章节级 Ollama 抽样（完整词频 + 上下文）

---

## 🔴 门禁 4：AI 味检测（最难）

### 4.1 触发时机

- **每章末**（不是每段）
- 立项会（每次多 Agent 都有 AI 味维度）
- 发布前最终扫

### 4.2 输入

```json
{
  "text": "整章内容...",
  "chapter_metadata": {
    "genre": "玄幻",
    "tone": "热血",
    "voice_prints": [...]
  },
  "source": "author_written",
  "judge_persona": "ai_smell_judge"
}
```

### 4.3 输出

```json
{
  "ai_smell_score": 0.72,  # 0-1
  "triggers": [
    {
      "type": "过度修辞",
      "location": "para_3",
      "text_excerpt": "眼中闪过一抹惊天的战意...",
      "severity": "🟡",
      "suggestion": "改用具体动作"
    },
    {
      "type": "对称结构",
      "location": "para_5",
      "text_excerpt": "不是因为...而是因为...",
      "severity": "🟡"
    }
  ],
  "action": "WARN",  # 警告但不阻断
  "must_resolve": false
}
```

### 4.4 token 预算

- 整章 8k

### 4.5 误报率金线

- **目标**：< 30%
- **可接受上限**：50%

### 4.6 与 content source 交互

| source | 行为 |
|--------|------|
| `author_written` | 完全检查 |
| `ai_drafted` | 🟢 **豁免**（AI 起草本来就有 AI 味，查了没意义） |
| `author_revised` | 完全检查 |

### 4.7 与状态交互

- **writing**：每章末触发
- **reviewing**：可云端（更精准）

### 4.8 特殊挑战

AI 味检测最大的难点：

- "AI 味" ≠ "AI 写"，而是文风机械、易识别为 AI 生成
- 长期写作后，作者可能被 AI "污染"，自己写也带 AI 味
- 因此 AI 味门禁对 `author_written` 仍然关键

---

## 📊 4 门禁总览

| 门禁 | 阻断性 | 主要实现 | writing 触发 | reviewing 触发 |
|------|--------|----------|--------------|----------------|
| 🔴 防胡写 | 强（必须红警拦截） | Ollama 本地 | 每段 + 红警 | 章节级 + 复检 |
| 🔴 违规词 | 弱警告，发布前强阻断 | 规则脚本 | 仅警告 | 发布前阻断 |
| 🔴 机械表达 | 仅警告 | 正则 + Ollama 抽样 | 实时规则 | 章节级 Ollama |
| 🔴 AI 味 | 仅警告 | Ollama | 每章末 | 立项会多 Agent + 整章 |

---

## 🧪 测试用例（MVP 必过）

### 防胡写
1. 作者写主角使用隐身 → 没设定 → 必须拦截
2. AI 起草内容 → 豁免
3. 主角对白违反声纹 → 拦截

### 违规词
4. 词典中"血腥"出现 → 警告
5. 起点平台禁用词 → 发布前阻断

### 机械表达
6. 段落中"仿佛"出现 3 次 → 警告
7. "忽然"密度 > 5% → 警告
8. AI 起草内容同样机械 → 必须警告

### AI 味
9. 章节含明显修辞堆砌 → 警告
10. AI 起草不触发（豁免）
11. 作者本身写得"AI 味"→ 必须警告

---

## 🔗 关联

- `router.md` §二 —— 4 门禁各自路由规则
- `content-attribution.md` §四 —— source 与门禁豁免
- `false-positive-loop.md` —— 各门禁误报率反馈

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🔴 关键
- **关联决策**：P13 / F6 / Q25.2
- **创建日期**：2026-07-10

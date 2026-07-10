# 决策记录：系统级质量防护（4 道门禁）

> **状态**：✅ 已确定
> **日期**：2026-07-08
> **关联**：所有写作相关页面

---

## 🎯 决策摘要

系统必须内置 **4 道质量门禁**，按优先级排序：

| 优先级 | 门禁 | 触发时机 |
|--------|------|---------|
| 🔴 P0 | 防胡写守护 | 实时每段 |
| 🔴 P0 | 违规词验证 | 发布前 |
| 🟡 P1 | 机械表达检测 | 每段 |
| 🟡 P1 | AI 味检测 | 每章 |

**核心洞察**：防胡写守护是用户**最强调**的门禁。

---

## ✅ 最终设计

### 4 道门禁详解

#### 1️⃣ 防胡写守护（最重要）

**职责**：检查设定一致性。

**4 个子检查**：
- 设定一致性（每段）
- 时间线一致性（每章）
- 人物一致性（每段）
- 逻辑一致性（每段）

**数据流**：

```python
class ConsistencyGuard:
    def check(self, text, book_settings):
        issues = []
        
        # 1. 提取事实声明
        claims = extract_facts(text)
        
        # 2. 比对设定
        for claim in claims:
            if contradicts(claim, book_settings):
                issues.append({
                    'type': '设定冲突',
                    'severity': 'high',
                    'claim': claim,
                    'contradicting_setting': find_conflict(...)
                })
        
        # 3. 检查时间线
        if violates_phase_expectations(text, current_phase):
            issues.append(...)
        
        # 4. 检查人物行为
        for action in extract_actions(text):
            if contradicts(action, character_profile):
                issues.append(...)
        
        return issues
```

#### 2️⃣ 违规词验证

**职责**：检查平台违规词。

```python
def compliance_check(text):
    sensitive_words = load_sensitive_dict()
    violations = []
    for word in sensitive_words:
        if word in text:
            violations.append({
                'word': word,
                'severity': 'high'
            })
    return violations
```

#### 3️⃣ 机械表达检测

**职责**：检测 AI 痕迹。

```python
MECHANICAL_PATTERNS = [
    r'首先[，,]',
    r'其次[，,]',
    r'综上所述',
    r'总之[，,]',
    r'值得注意的是',
    r'在一定程度上',
    r'不仅.{1,30}而且',
]
```

#### 4️⃣ AI 味检测

**职责**：检测 AI 生成概率。

```python
def ai_taste_check(text):
    return {
        'perplexity': calculate_perplexity(text),  # 困惑度
        'burstiness': calculate_burstiness(text),  # 突发性
        'sentence_variance': calculate_sentence_length_variance(text),
        'transition_density': count_transitions(text) / len(text),
        'emotional_markers': count_emotional_markers(text),  # 哎、唉、笑死
    }
```

---

## 🔗 相关决策

- [页面逻辑梳理](./002-page-logic-organization.md)
- [伏笔追踪设计](./001-foreshadow-tracking.md)
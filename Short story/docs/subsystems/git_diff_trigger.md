# git-diff-trigger.md — git diff 联动触发子系统

> **决策依据**：R1/R2/R3（35 题压力测试锁定）/ V3（横纵向研判补遗）
> **重要性**：🔴 **关键**（R1 整个时间段重算的触发器；MVP 必做）
> **状态**：✅ 完整版
> **关联**：kickoff-meeting.md（被触发）/ cumulative_audit / facts-extraction.md / state-detector.md / content-attribution.md

---

## 🎯 系统职责

**监视频繁的 git 提交**，当作者修改了"核心术语"时，**自动触发新一轮审查**。

**核心承诺**：

- ✅ 作者提交（commit）即监测
- ✅ 修改核心术语 → 自动触发立项会（默认）
- ✅ AI 语义判定（避免字面命中误报）
- ✅ 完全 git 即状态（无 daemon / 无数据库）

---

## 📐 核心术语词典（V3.2 锁定）

### 词典内容来源

合并 3 处：

| 来源 | 抽取方式 | 状态 |
|------|---------|------|
| `books/<name>/voice-prints/*.md` | 解析 markdown frontmatter 中 character_id + 文本中的"角色名" | ✅ |
| `books/<name>/settings/02-characters.md` | 解析 frontmatter 列出所有角色名 + 文中关键属性 | ✅ |
| `books/<name>/settings/04-special-setting.md` | 解析 frontmatter 列出所有物品 / 金手指 / 关键道具名 | ✅ |

### 词典生成

```python
def build_term_dictionary(book_name: str) -> set:
    """每次 kickoff_meeting 通过后重建"""
    terms = set()
    
    # 1. voice-prints 角色名
    for vp_file in glob(f"books/{book_name}/voice-prints/*.md"):
        vp = parse_markdown(vp_file)
        for char_id in vp.frontmatter.character_id:
            terms.add(char_id)
        # 也提取 role-related names like "沈铁衣"
        terms.update(extract_quoted_names(vp.body))
    
    # 2. 02-characters.md 角色 + 属性
    chars_md = parse_markdown(f"books/{book_name}/settings/02-characters.md")
    for char in chars_md.frontmatter.characters:
        terms.add(char.name)
        terms.add(char.alias)
    
    # 3. 04-special-setting.md 物品
    settings_md = parse_markdown(f"books/{book_name}/settings/04-special-setting.md")
    for item in settings_md.frontmatter.items:
        terms.add(item.name)
    
    return terms
```

### 词典更新时机

- 立项会通过后（kickoff_meeting 完成）
- voice-prints/*.md 变更后
- **不每次 commit 都重建**（避免性能问题）

---

## 🔍 检测算法（V3.1 锁定：git diff + AI 语义）

### Level 1：git grep 字面命中（快）

```python
def detect_changed_terms_via_grep(book_name: str, since_commit: str) -> list:
    """git diff 中是否包含核心术语"""
    diff_output = subprocess.check_output([
        "git", "diff", f"{since_commit}..HEAD", "--", 
        f"books/{book_name}/",
    ]).decode()
    
    terms = build_term_dictionary(book_name)
    changed_terms = []
    for line in diff_output.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            for term in terms:
                if term in line:
                    changed_terms.append({
                        "term": term,
                        "line": line,
                        "severity": "🔴",  # 字面命中 → 默认 🔴
                    })
    return changed_terms
```

**性能**：O(行数 × 词典大小)，毫秒级。

### Level 2：AI 语义判断（准）

```python
def detect_semantic_impact(book_name: str, since_commit: str) -> dict:
    """AI 判断改动是否真的影响核心设定"""
    diff_output = subprocess.check_output([
        "git", "diff", f"{since_commit}..HEAD", 
    ]).decode()
    
    prompt = f"""
以下是 {book_name} 最近一次 commit 改动的 diff：

```diff
{diff_output[:8000]}
```

请判断这次改动属于：
1. **核心设定变更**（角色核心属性 / 世界观根本规则 / 金手指机制）→ 🔴 触发立项会
2. **内容更新**（章节润色 / 对话修改 / 单章删除）→ 🟡 触发累积审核
3. **小修小补**（错别字 / 标点 / 单句改写）→ 🟢 不触发

只输出 1/2/3 + 一句话原因。
"""
    return ollama.infer(prompt, persona='diff_semantic_judge')
```

**性能**：O(seconds)，但仅在 grep 命中后才调用。

### 组合判定

```python
def detect_change_severity(book_name, since_commit):
    term_hits = detect_changed_terms_via_grep(book_name, since_commit)
    if not term_hits:
        return "🟢", "无核心术语改动"
    
    # git grep 命中，调用 AI 判定
    semantic = detect_semantic_impact(book_name, since_commit)
    if "1." in semantic:
        return "🔴", semantic
    elif "2." in semantic:
        return "🟡", semantic
    else:
        return "🟢", semantic
```

---

## 🚦 触发动作（V3.3 + V3.4 锁定）

### 严重度 → 动作映射

| 严重度 | 触发动作 | 含义 |
|--------|---------|------|
| 🔴 核心设定变更 | **自动 kickoff_meeting（**整个时间段重算**）** | 立项会重审，强制把增量变更同步到所有引用 |
| 🟡 内容更新 | **自动 cumulative_audit（最近 N 章重审）** | 累积审核，不动设定层 |
| 🟢 小修小补 | **不触发** | 仅记录到日志 |

### 默认值（V3.3 锁定）

> 用户原话："默认对立项会（重频但需走 P10）"

- 任何 git grep **命中核心术语** + AI 判定 = 1（核心变更）→ 走立项会
- 字面命中即默认 🔴——这是**最严格**的策略

### 立项会如何处理

```python
def on_diff_trigger_kickoff(book_name, changed_terms):
    """触发立项会"""
    kickoff_meeting(
        book_name=book_name,
        mode='increment',  # 增量模式（Q30 锁定）
        since='last_kickoff_or_diff',
        force_keywords=changed_terms,
    )
    log(f"git diff 触发立项会：{changed_terms}")
```

### 回滚处理（V3.4 锁定甲）

> "git revert 也是变更，不豁免"

```python
def on_git_revert(book_name, since_commit):
    """git revert 也走判定（不豁免）"""
    return detect_change_severity(book_name, since_commit)
```

回滚触发**同一条路径**——这意味着：

- 误修改 → revert → 仍触发立项会（重新确认）
- 简化 rollback：作者可选择"跳过本次触发"，否则自动立项

---

## 📁 状态与日志

### 触发日志

`books/<name>/logs/diff_triggers.log`：

```yaml
- timestamp: 2026-07-10T15:30:00
  commit: a1b2c3d
  changed_terms: [沈铁衣, 古籍]
  severity: 🔴
  action: kickoff_meeting (increment mode)
  result: success | failed
- timestamp: 2026-07-10T14:00:00
  commit: d4e5f6g
  changed_terms: []
  severity: 🟢
  action: none
- timestamp: 2026-07-10T13:30:00
  commit: h7i8j9k
  changed_terms: [设定术语: "修仙界规则"]
  severity: 🟡
  action: cumulative_audit
  result: success
```

### 与 R1 的协同（"整个时间段重算"已锁定）

R1 已锁定"整个时间段重算"，本子系统是触发器。

重算的范围 = 自**上次 kickoff_meeting 通过后**的所有变更。

```python
def get_diff_range(book_name):
    """获取自上次 kickoff 后的所有 diff"""
    last_kickoff = get_last_kickoff_passed(book_name)
    return f"{last_kickoff.commit_hash}..HEAD"
```

---

## 🔌 CLI 命令

```bash
# 手动检测（默认查最近 commit）
python -m ai_coauthor diff_check --book <name>

# 指定 commit 范围
python -m ai_coauthor diff_check --book <name> --since <commit> --until <commit>

# 跳过一次触发（作者明确知道）
python -m ai_coauthor diff_check --skip --book <name>

# 重置上次 kickoff 锚点（重大情形）
python -m ai_coauthor diff_check --reset-kickoff --book <name>
```

### 自动触发钩子（git hook）

MVP 阶段使用 `post-commit` git hook：

```bash
#!/bin/bash
# .git/hooks/post-commit
python -m ai_coauthor diff_check --book autodetect
```

**自动运行**：每次作者 commit → 自动检测。

### 与现有 git 工作流的集成

作者正常 `git commit -m "..."`：

```
git commit -m "修改第 30 章沈铁衣对白"
   ↓
post-commit hook
   ↓
diff_check 自动跑
   ↓
命中核心术语 → 触发立项会（增量模式）
未命中 → 仅记录日志
```

---

## 📐 词典变更的影响

### 何时重建词典

- ✅ kickoff_meeting 通过后
- ✅ voice-prints/*.md 变更后
- ✅ 02-characters.md 或 04-special-setting.md 变更后
- ❌ 章节内容变更不重建（不增加新术语）

### 重建触发

```python
def rebuild_term_dictionary_if_needed(book_name):
    last_rebuild = get_last_dict_rebuild_ts(book_name)
    last_kickoff = get_last_kickoff_passed_ts(book_name)
    if last_kickoff > last_rebuild:
        rebuild_term_dictionary(book_name)
```

---

## 🧪 测试用例（MVP 必过）

### 词典构建

1. **空书**: voice-prints 0 个 + 02-characters 空 → 词典空
2. **完整书**: voice-prints 3 个 + 02-characters 5 个 + 04-special 5 个 → 词典 13 项
3. **重建触发**: kickoff_meeting 通过后 → 词典重生成

### 检测

4. **字符命中**: commit 修改了"沈铁衣" → grep 命中
5. **上下文命中**: commit 在注释中提到"沈铁衣" → 仍命中
6. **未命中**: commit 仅修改对话文本不含角色名 → 不命中

### AI 语义

7. **内容润色**: 章节对话微调 → AI 判定 🟢
8. **章节重写**: 整章重写但设定不变 → AI 判定 🟡
9. **设定变更**: 修改 02-characters 中主角动机 → AI 判定 🔴

### 触发

10. **🔴 触发立项会**: kickoff_meeting 增量模式自动启动
11. **🟡 触发累积审核**: cumulative_audit 最近 N 章重审
12. **🟢 不触发**: 仅记录日志

### 回滚

13. **git revert 触发链路**: 同正向变更
14. **commit --amend 触发链路**: 同 commit

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| 核心术语词典（git grep） | ✅ | ✅ |
| AI 语义判断 | ✅ | ✅ |
| 严重度 → 动作映射 | ✅ | ✅ |
| 默认立项会（核心变更） | ✅ | ✅ |
| git post-commit hook | ✅ | ✅ |
| 词典重建触发 | ✅ | ✅ |
| 回滚处理 | ✅ | ✅ |
| 与 voice-print / 02-characters 集成 | ✅ | ✅ |
| Phase 2: 增加更多类型（功法名 / 门派名）| ❌ | ✅ |
| Phase 2: 智能词典分类（字典 vs 创意术语）| ❌ | ✅ |
| Phase 2: 多书交叉词典 | ❌ | ✅（Phase 4+） |

---

## 🔗 关联

- `kickoff-meeting.md` —— 被触发方
- `cumulative_audit` —— 被触发方
- `state-detector.md` —— 触发时 state=reviewing，可上云
- `voice-print.md` —— 词典来源之一
- `facts-extraction.md` —— 内容更新时同步
- `content-attribution.md` —— ai_drafted 变更不算核心

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键（R1 触发器，MVP 必做）
- **关联决策**：R1 / R2 / R3 / V3（横纵向研判补遗）
- **关联子系统**：kickoff-meeting.md / cumulative_audit / facts-extraction.md / state-detector.md
- **关联命令**：`diff_check.py`（MVP 新增命令，列入 7 命令之一）
- **关联文件**：books/<name>/logs/diff_triggers.log

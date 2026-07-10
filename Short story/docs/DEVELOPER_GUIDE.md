# Short story 开发指南

> **版本**：v0.1
> **目标读者**：开发者 / AI 协作者的实现者

---

## 🎯 开发前提

### 必备依赖

| 依赖 | 用途 | 安装 |
|------|------|------|
| **Python 3.11+** | 脚本运行 | 已预装 |
| **mmx-cli** | 调用 MiniMax API 进行 AI 推理 | `npm install -g mmx` |
| **MiniMax API Key** | 调用云端模型 | 用户配置 |

### 必备知识沉淀

所有功能都基于 24 个专题沉淀，开发者必须**先读沉淀**再写代码：

| 阅读顺序 | 文档 |
|---------|------|
| 1 | [novel-writing-checklist.md](../../AI-Agent-Local/docs/knowledge/novel-writing/novel-writing-checklist.md) 总纲 |
| 2 | [system-architecture-workflow.md](../../AI-Agent-Local/docs/knowledge/novel-writing/system-architecture-workflow.md) 系统骨架 |
| 3 | [system-quality-guards.md](../../AI-Agent-Local/docs/knowledge/novel-writing/system-quality-guards.md) 4 道门禁 |
| 4 | 其余专题按需 |

---

## 📐 核心设计原则

### 1. 文件即状态

- 所有数据都是普通 Markdown 文件
- 无数据库
- git 友好

### 2. 模块化命令

- 每个命令是独立 Python 脚本
- 命令可单独调用
- 命令之间通过文件系统通信

### 3. mmx-cli 调用模式

```python
import subprocess

def call_mmx(system_prompt, user_prompt, model="claude-fable-5"):
    result = subprocess.run(
        ['mmx', 'text', 'chat',
         '--model', model,
         '--system', system_prompt,
         '--user', user_prompt,
         '--output', 'text'],
        capture_output=True, text=True
    )
    return result.stdout
```

### 4. 提示词模板化

每个命令都有对应的提示词模板（保存在 `ai-coauthor/prompts/`）。

---

## 🔧 10 大命令的实现蓝图

### 命令 1：setup_consult.py（设定咨询）

**功能**：引导作者填写 6 维度设定

**实现要点**：
- 提供交互式问答
- 每个问题对应一个维度
- 自动保存到 `books/<name>/settings/NN-xxx.md`
- 可调用 LLM 帮助作者梳理思路

**伪代码**：

```python
def setup_consult(book_name):
    """引导作者填写设定"""
    questions = [
        ("01-world.md", "你的故事发生在什么世界？时代背景是什么？"),
        ("02-characters.md", "你的主角是谁？3-5 个核心配角分别是谁？"),
        ("03-framework.md", "你的核心冲突是什么？"),
        ("04-tone.md", "你的叙事基调是什么？"),
        ("05-foreshadow.md", "你埋了哪些伏笔？"),
        ("06-audience.md", "你的目标读者是谁？")
    ]
    
    for filename, question in questions:
        answer = input(question + "\n> ")
        save_to_book(book_name, f"settings/{filename}", answer)
```

---

### 命令 2：relationship_graph.py（人物关系图）

**功能**：从人物档案生成 Mermaid 关系图

**实现要点**：
- 读取 `books/<name>/settings/02-characters.md`
- 提取每个角色的关系
- 生成 Mermaid graph 代码
- 输出到 `books/<name>/relationships.md`

**伪代码**：

```python
import re

def extract_relationships(book_name):
    """提取人物关系"""
    content = read_file(f"books/{book_name}/settings/02-characters.md")
    characters = parse_characters(content)
    relationships = parse_relationships(content)
    return characters, relationships

def generate_mermaid(characters, relationships):
    """生成 Mermaid 图"""
    lines = ["graph TD"]
    for char in characters:
        lines.append(f"    {char['id']}[{char['name']}]")
    for rel in relationships:
        lines.append(f"    {rel['from']} -->|{rel['type']}| {rel['to']}")
    return "\n".join(lines)
```

---

### 命令 3：plan_chapter.py（章节规划）

**功能**：基于时间线和目标自动规划章节

**实现要点**：
- 读取 `books/<name>/timeline.md`
- 根据"主角目标"、"时间线阶段"推断本章内容
- 给出"人物出场"、"物品升级"、"目标推进"建议

**伪代码**：

```python
def plan_chapter(book_name, chapter_num):
    """规划第 N 章"""
    timeline = read_timeline(book_name)
    phase = timeline.get_phase(chapter_num)
    goal = read_goal(book_name)
    settings = read_settings(book_name)
    
    # 基于已有设定推断
    plan = {
        "phase": phase,
        "expected_events": timeline.get_expected_events(chapter_num),
        "characters_should_appear": infer_characters(phase, goal),
        "items_should_upgrade": infer_items(phase, settings),
        "goal_progress": calculate_goal_progress(chapter_num, goal),
    }
    return plan
```

---

### 命令 4：item_progression.py（物品升级校验）

**功能**：检查物品/金手指的升级节点是否合理

**实现要点**：
- 读取物品清单（含限制设定）
- 检查每个物品的出现/升级章节是否在合理范围
- 输出"提前出现"、"过晚出现"、"限制违反"等警告

---

### 命令 5：consistency_check.py（一致性守护）⭐ 最重要

**功能**：防胡写守护 —— 实时检查设定一致性

**实现要点**：
- 读取该书所有设定
- 提取新段落中的"事实声明"
- 比对设定，输出冲突清单
- 这是用户最强调的命令

**伪代码**：

```python
def consistency_check(book_name, new_paragraph):
    """一致性守护"""
    settings = read_book_settings(book_name)
    timeline = read_timeline(book_name)
    characters = read_characters(book_name)
    
    issues = []
    
    # 1. 设定一致性
    claims = extract_facts(new_paragraph)
    for claim in claims:
        if contradicts(claim, settings):
            issues.append({
                'type': '设定冲突',
                'severity': 'high',
                'claim': claim,
                'contradicting_setting': find_conflict(claim, settings)
            })
    
    # 2. 时间线一致性
    current_chapter = get_current_chapter(book_name)
    expected_phase = timeline.get_phase(current_chapter)
    if violates_phase_expectations(new_paragraph, expected_phase):
        issues.append({
            'type': '时间线偏离',
            'severity': 'medium'
        })
    
    # 3. 人物一致性（性格、声音指纹）
    actions = extract_actions(new_paragraph)
    for action in actions:
        if contradicts(action, characters[action['character']]):
            issues.append({
                'type': '人物 OOC',
                'severity': 'high'
            })
    
    return issues
```

---

### 命令 6：voice_print_check.py（声音指纹核对）

**功能**：检查对话是否符合人物的"声音指纹"

**实现要点**：
- 读取 `books/<name>/voice_prints/*.md`
- 提取对话文本
- 比对每个角色的高频词/禁用词/句式
- 提示"不符合声音指纹"的位置

---

### 命令 7：chapter_polish.py（章节精修）

**功能**：单章节的多维度审视

**实现要点**：
- 开头：动作切入检查
- 中间：阻碍 vs 流水
- 结尾：悬崖 vs 床
- 修辞：抽象→具体
- 对话：声音指纹 + 潜台词

---

### 命令 8：cumulative_audit.py（沉淀审核）

**功能**：10-30 章后的跨章对齐

**实现要点**：
- 检查伏笔是否兑现
- 检查人物弧光推进
- 检查时间线对齐
- 检查设定一致性
- 检查基调统一

---

### 命令 9：foreshadow_track.py（伏笔追踪）

**功能**：伏笔登记、追踪、回收提示

**实现要点**：
- 伏笔登记表：`books/<name>/foreshadowing.md`
- 状态：待埋 / 已埋 / 待收 / 已收
- 每章生成后自动检查"该收未收"
- 高潮转折前自动列出"待回收清单"

---

### 命令 10：unused_settings.py（设定巡检）

**功能**：已设定但未用的清单

**实现要点**：
- 读取所有设定（人物、伏笔、规则、物品）
- 扫描已写章节
- 输出"未使用清单"

---

## 🛡️ 4 道质量门禁的实现

按重要性排序：

### P0：防胡写守护（最重要）

```python
# 实时每段触发
def consistency_check(book_name, new_paragraph):
    # ... 见命令 5
```

### P0：违规词验证

```python
def compliance_check(text):
    sensitive_words = load_sensitive_dict()
    violations = []
    for word in sensitive_words:
        if word in text:
            violations.append({'word': word, 'severity': 'high'})
    return violations
```

### P1：机械表达检测

```python
def mechanical_pattern_check(text):
    patterns = [
        r'首先[，,]', r'其次[，,]', r'综上所述', r'总之[，,]',
        r'值得注意的是', r'在一定程度上'
    ]
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            matches.append({
                'pattern': pattern,
                'position': match.start(),
                'context': text[max(0, match.start()-20):match.end()+20]
            })
    return matches
```

### P1：AI 味检测

```python
def ai_taste_check(text):
    return {
        'perplexity': calculate_perplexity(text),
        'burstiness': calculate_burstiness(text),
        'sentence_variance': calculate_sentence_length_variance(text),
        'transition_density': count_transitions(text) / len(text),
        'emotional_markers': count_emotional_markers(text),
    }
```

---

## 📋 提示词模板

每个命令都需要调用 LLM。提示词模板保存在 `ai-coauthor/prompts/`：

- `system-coauthor.md` —— 核心身份提示
- `roles/consistency-guard.md` —— 一致性守护者提示
- `roles/voice-guard.md` —— 声音指纹守护者提示
- `roles/structure-guard.md` —— 结构守护者提示
- `roles/tone-guard.md` —— 基调守护者提示
- `roles/foreshadow-tracker.md` —— 伏笔追踪者提示
- `roles/book-auditor.md` —— 全文巡检员提示

每个提示词模板的格式：

```markdown
# 角色：[角色名]

## 身份
你是 ___

## 职责
1. ___
2. ___

## 工作流程
1. 读取 ___（依据）
2. 比对 ___
3. 输出 ___

## 输出格式
___
```

---

## 🧪 测试策略

### 单元测试

- 每个命令独立测试
- 用 `_template/` 作为测试数据

### 集成测试

- 完整跑 4 步工作流
- 用真实书籍验证

### 沉淀式审核

- 写 10 章 → 运行 cumulative_audit → 修复问题

---

## 🚀 快速上手

```bash
# 1. 创建新书
cp -r books/_template books/my-novel

# 2. 运行设定咨询
python ai-coauthor/commands/setup_consult.py books/my-novel

# 3. 编辑设定文件
# （在 books/my-novel/settings/ 下填入）

# 4. 写一章
# 写到 books/my-novel/chapters/chapter-001.md

# 5. 运行一致性守护
python ai-coauthor/commands/consistency_check.py books/my-novel

# 6. 运行伏笔追踪
python ai-coauthor/commands/foreshadow_track.py books/my-novel

# 7. 每 10 章运行沉淀审核
python ai-coauthor/commands/cumulative_audit.py books/my-novel
```

---

## 📚 扩展开发方向

### Web 界面（Phase 4）

- VSCode 插件
- 浏览器界面
- 桌面应用

### 多代理协同（Phase 4）

- 一个命令对应一个角色
- 多角色协同工作

### 自动推断（Phase 4）

- 基于已有设定自动生成章节大纲
- 基于人物档案自动生成对话

---

**版本**：v0.1
**最后更新**：2026-07-08
# voice-print.md — 声音指纹子系统

> **决策依据**：P8 / 008-v2-voice-print.md
> **重要性**：🟡 **重要**（**MVP 必写**：声纹是 6 维度设定的 AI 派生产物；**MVP 简化为手填**；**Phase 2 完善对白核查算法**）
> **状态**：✅ 完整版（非 mockup）
> **关联**：kickoff-meeting.md（声纹是立项会最末派生）/ content-attribution.md / quality-guards-granularity.md

---

## 🎯 系统职责

为**每个核心角色**生成一份"声音指纹"——声纹覆盖：

- ✅ **必说**：high-frequency 口头禅 / 标志性对话 / 行为触发句
- ❌ **禁说**：性格冲突词 / 角色类型不符 / **其他角色的标志语**

声纹是**角色识别码**——跨章节、跨场景保持一致。即使剥离上下文，仅看对话文字就应能识别"是这本书的哪个角色"。

> 用户原始定义（Q14.2）：
> "西游记的孙悟空，'你爷爷在此'，唐僧从来不会这么说"

---

## ⏰ 生成时机（H1.x.5a 锁定）

**声纹作为立项会的最后一项决议**——而非 setup_consult 顺生。

```
Step 1 设定填写完成
   ↓
   自动触发 kickoff_meeting
   ↓
   多 Agent 审查 → 产出可执行冲突清单
   ↓
   作者修改冲突项（如有）→ 重新立项（增量）
   ↓
   立项会通过 → "派生声纹"是最后一步
   ↓
   ↓   触发"人物 Agent"在云端
   ↓   输出: voice-prints/<character>.md 草稿
   ↓
   作者审改 / 补全 / 修改草稿
   ↓
   声纹最终版：voice-prints/<character>.md
   ↓
Step 2 章节规划可开始
```

### 为什么声纹必须在立项会末尾

> 用户原话（H1.x.5a）：
> "生文的派生可以作为立项会的最后一项决议……如果故事的框架还在改、时代背景还在改，甚至角色还在改，在这个过程中生成生文是没有意义的。"

依赖关系：

1. 时代背景已定（01-world.md）——声纹需要时代语感
2. 角色已定（02-characters.md）——声纹是角色派生物
3. 框架已定（03-framework.md）——声纹需符合故事框架的情绪
4. 立项会通过——声纹才有"基础坚实的状态"

### 为什么不放 setup_consult

声纹与时代背景强相关——若时代背景还在改，声纹派生无意义。setup_consult 顺生会引入"改一处声纹全部重做"的脆弱性。

---

## 🎭 双列表：必说 + 禁说（H1.x.2 锁定）

### 必说（say_list）

每个角色至少有 3 类必说：

1. **高频口头禅**：常挂在嘴边的句子（例：孙悟空"俺老孙"）
2. **标志性对话**：行为触发口癖（例：路飞"我可是要成为海贼王的男人"）
3. **自我定位句**：体现自我身份的关键句（例：机器猫"让我用这个发明帮助你"）

### 禁说（forbidden_list）

每个角色**至少**有 3 类禁说：

1. **性格冲突词**：与性格不符的语气词（例：刚毅角色不会"人家~"）
2. **角色类型不符**：英雄角色不会"我只想苟活" / 反派英雄不会"我为主角牺牲"
3. **其他角色的标志语**：跨角色混淆（例：沈铁衣绝不用"阁下"——这是反派用语）

### 跨文化原型参考（参考但不是模板）

| 原型 | 来源 | 必说案例 | 禁说案例 |
|------|------|---------|---------|
| **热血少年** | 《海贼王》路飞 | "我要成为……" | "我投降" |
| **工具伴侣** | 《机器猫》哆啦A梦 | "我有这个发明……" | "我要打你" |
| **冷面刺客** | 《银魂》土方 | "我就要剖腹……" | "人家……" |
| **自我毁灭型** | 《死亡笔记》夜神月 | "我就是神" | "我要忏悔" |

这些用作派生时的**启发式模板**，声纹子系统不会 1:1 复用。

---

## 🧠 性格模板：MBTI（16personalities）

声纹子系统采用 **MBTI 16 型人格**作为角色性格的参考框架：

- 4 个维度，每个角色对应 4 字母组合（如 `ISTJ` / `ENFP`）
- 推导公式：MBTI 类型 → 必说 / 禁说映射
- 与 02-characters.md 中"性格"字段联动

### 派生公式（概要）

```python
# 简化的 MBTI → 声纹映射
def mbti_to_voice(mbti_type: str) -> dict:
    I_or_E = mbti_type[0]  # 内向/外向
    N_or_S = mbti_type[1]  # 直觉/感觉
    T_or_F = mbti_type[2]  # 思维/情感
    J_or_P = mbti_type[3]  # 判断/感知
    
    # 例如 ENTP：外向 + 直觉 + 思维 + 感知 → 善辩、爱抬杠、跳跃性思维
    # 例如 ISFJ：内向 + 感觉 + 情感 + 判断 → 体贴、爱照顾人、回避冲突
    
    return {
        "say_list": derive_say(I_or_E, N_or_S, T_or_F, J_or_P),
        "forbidden_list": derive_forbidden(I_or_E, N_or_S, T_or_F, J_or_P),
    }
```

**注意**：MBTI 只是**启发式参考**，不是约束。角色性格可以"不是典型 MBTI"，AI 派生要保留 flex。

### 16 型人格参考（详细映射见附录 A）

声纹子系统维护一份 `voice-prints/_mbti_reference.yaml`：

```yaml
ENTP:
  core: 善辩、爱抬杠、跳跃性思维
  say_pattern: "我觉得……" / "可是你有没有想过……"
  forbidden_pattern: 
    - 不应绝对化（ENTP 不轻易下结论）
    - 不应回避辩论
ISTJ:
  core: 严谨、守规矩、可靠
  say_pattern: "按规矩来" / "我需要核实一下"
  forbidden_pattern:
    - 不应即兴冲动
    - 不应说"大概"、"或许"
# ... 共 16 型
```

---

## 📐 数据模型：`voice-prints/<character>.md`

每本书在 `books/<name>/voice-prints/` 下放每个核心角色的指纹：

```markdown
---
# 元信息（机械解析）

character_id: protagonist       # 角色 ID（与 02-characters.md 对应）
mbti: ISTJ                       # 性格类型（参考模板）
generated_by: persona_agent_v1   # 哪个 Agent 派生
generated_at: 2026-07-10T15:30:00
author_revised: 2                # 作者审改次数
---

# 沈铁衣 · 声音指纹

> "你爷爷在此" 式辨识度极高的口语化特征

## ✅ 必说

### 高频口头禅
- "看清楚了。"
- "在我这……"
- "——可别怪我不客气"

### 标志性对话
- 生气时："我就要——"（后接动作）
- 战斗时："接招吧"
- 思考时："让我看清楚了……"

### 自我定位句
- "铁衣取命，不问缘由"
- "我沈家的事，不需要外人插手"

## ❌ 禁说

### 性格冲突词
- ❌ "人家~"（与刚毅冲突）
- ❌ "嘤嘤嘤"
- ❌ "我好怕怕哦"

### 角色类型不符
- ❌ "我要投降"（沈铁衣绝不投降）
- ❌ "或许吧"（沈铁衣武断自信）
- ❌ "对不起"（除非特殊剧情）

### 其他角色的标志语
- ❌ "阁下"（这是反派的语气）
- ❌ "少主"（这是盟友的语气）
- ❌ "阿弥陀佛"（这是师父的语气）

## 🎬 示例对白（至少 3 条）

1. "看清楚了。"（生气时加重语气）
2. "你若再逼近一步，我可就要——"（威胁时常停顿）
3. "师父，弟子明白。"（与师父对话，语气恳切）

## 🧪 识别度测试（AI 自评）

- [x] 剥离上下文能否识别：✅ 是沈铁衣
- [x] 与配角的区别：反派用"阁下"，盟友用"少主"
- [x] 跨场景稳定：第 1 章与第 50 章同一句"看清楚了"识别度一致

## 🔗 与其他设定联动

- 02-characters.md §沈铁衣（出处）
- 01-world.md §时代背景（影响语感）
- 03-framework.md §故事框架（影响情绪基线）
```

---

## 🤖 AI 派生协议（在 kickoff_meeting 末尾触发）

### 派生流程

```
立项会通过 →
  ↓
  kickoff_meeting 命令调用"人物 Agent"
  ↓
  人物 Agent 加载：
    - 02-characters.md（角色核心性格）
    - 01-world.md（时代背景）
    - 03-framework.md（故事框架）
    - voice-prints/_mbti_reference.yaml（MBTI 参考）
    - 跨文化原型表（海贼/银魂/机器猫等）
  ↓
  对每个核心角色生成 voice-prints/<character>.md 草稿
  ↓
  输出到 books/<name>/voice-prints/<character>.md.draft.md
  ↓
  作者审改 → 移动到正式 voice-prints/<character>.md
```

### 派生失败回退

如果某角色 AI 派生失败（如 MBTI 类型不明）：

- 降级为**纯模板派生**（用原型表 + MBTI 参考）
- 仍需作者手动补全

---

## 🛡️ 守护机制：必说 + 禁说的检查（H1.x.5b + H1.x.5c 锁定）

### 双层检测

**第 1 层：正则直接匹配（禁说）**

```python
# 普适正则（角色级禁说的字面匹配）
def check_forbidden(paragraph, character_voiceprint):
    forbidden_patterns = character_voiceprint.forbidden_list
    hits = []
    for pattern in forbidden_patterns:
        if re.search(pattern, paragraph):
            hits.append({
                "pattern": pattern,
                "type": "forbidden_match",
                "severity": "🔴"  # 立即拦
            })
    return hits
```

**性能**：O(N) 极快，0 延迟

**第 2 层：AI 语义补充（必说 + 禁说）**

```python
# 仅当 第 1 层命中 → 触发第 2 层确认
def check_semantic(paragraph, character_voiceprint, persona='voice_guard'):
    prompt = f"""
角色: {character_voiceprint.name}
必说: {character_voiceprint.say_list}
禁说: {character_voiceprint.forbidden_list}

段落: {paragraph}

任务:
1. 检查必说是否充分（应有对话但没有 → 警告）
2. 检查禁说是否被违反（语义违反而非字面 → 警告）
3. 输出: 命中项 + 严重度
"""
    return ollama.infer(prompt, persona=persona)
```

**触发**：

- 🔴 字面命中禁说 → 🔴 **BLOCK**（必须改 / 手动忽略）
- 🟡 AI 判定语义违反 → 🟡 **WARN**
- 🟢 必说覆盖不足 → 🟢 **HINT**

### 优先级（与 quality-guards §3 机械表达的协同）

禁说的优先级**高于**机械表达：

| 检测来源 | 严重度 | 提示文案 |
|---------|--------|---------|
| 声纹禁说 字面 | 🔴 | "⚠️ 沈铁衣禁说：'人家'" |
| 声纹禁说 语义（AI 判定）| 🟡 | "⚠️ 沈铁衣可能违反禁说：对话风格偏软" |
| 机械表达（普适）| 🟡 | "⚠️ '仿佛' 出现 N 次" |

---

## 🔌 与系统的接口

### 写章节时（writing 状态）

```python
# routers 调用声纹守护
def write_chapter(paragraph, character_id):
    voiceprint = load_voiceprint(character_id)
    issues = []
    
    # 第 1 层正则（无 AI 介入）
    forbidden_hits = check_forbidden(paragraph, voiceprint)
    issues.extend(forbidden_hits)
    
    # 第 1.5 层正则（机械表达）
    mechanical_hits = check_mechanical(paragraph)
    issues.extend(mechanical_hits)
    
    # 第 2 层 AI（仅在有 fatal 时触发）
    if any(i.severity == '🔴' for i in issues):
        semantic_hits = check_semantic(paragraph, voiceprint)
        issues.extend(semantic_hits)
    
    return issues
```

### 立项会时（reviewing 状态，云端）

```python
# 人物 Agent 的额外职责：声纹派生
def persona_agent_for_kickoff(book):
    characters = book.characters
    voiceprints = []
    for char in characters:
        if not voiceprint_exists(char):
            voiceprints.append(generate_voiceprint(char, book))
    return voiceprints
```

---

## 🧪 测试用例（MVP 必过）

### 派生

1. **首次派生**：空白书的 kickoff_meeting 自动派生所有核心角色声纹草稿
2. **重新派生**：作者修改 02-characters.md 后，下次立项会重新派生对应角色
3. **作者审改**：作者修改草稿 → 移动到正式文件 → `author_revised: 1`

### 守护

4. **字面禁说匹配**：写"看清楚了，人家~" → 沈铁衣"人家"字面命中 → 🔴 BLOCK
5. **语义违规检测**：写大段很柔情的对话（不符合沈铁衣刚毅性格）→ AI 判定 → 🟡 WARN
6. **必说覆盖**：连续 10 章主角几乎不开口 → 🟢 HINT"必说覆盖率不足"
7. **跨角色混淆**：写"阁下"（反派语气，但出现在沈铁衣段）→ 🔴 BLOCK

### 性能

8. **正则 0 延迟**：第 1 层正则检测耗时 < 1ms
9. **AI 仅在 fatal 触发**：第 2 层 AI 仅在 🔴 命中后才调用，平均次数 < 5 次/章

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| 必说 + 禁说 双列表 | ✅ | ✅ |
| 字符面正则匹配 | ✅ | ✅ |
| AI 语义补充 | ✅（仅 fatal 时）| ✅ 全量 |
| MBTI 自动派生 | ✅（立项会末尾）| ✅ |
| 跨文化原型参考 | ✅（**海贼/银魂/机器猫** 4 例）| ✅ 扩展到 8+ |
| 自动对白抽取（章节末）| ❌ | ✅ |
| 必说覆盖率统计 | ❌ | ✅ |
| 声纹可视化 | ❌ | ✅（Phase 4 Web 阶段）|

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🟡 重要（MVP 简化为手填；AI 派生作为立项会末尾步骤）
- **关键决策来源**：
  - H1.x.5a 时序：立项会末尾
  - H1.x.2 双列表：必说 + 禁说
  - H1.x.5b 模板：MBTI 16personalities
  - H1.x.5c 算法：正则 + AI 语义补充
  - H1.x.5d 跨文化参考：海贼/银魂/机器猫原型
- **关联决策**：P8 / 008-v2 / P10（立项会）
- **关联子系统**：router.md（声纹守护调用 router）/ content-attribution.md（声纹豁免判定）/ quality-guards-granularity.md（机械表达优先级）
- **关联命令**：kickoff_meeting.py（末尾触发）/ write.html（character_id 关联）

# multi-agent-cloud.md — 多 Agent 云端协作子系统

> **决策依据**：P14 / Q30 / Q31 / Q33（35 题压力测试锁定）
> **重要性**：🔴 **关键**（立项会 / 打磨 / 深度审核的部署协议）
> **状态**：📋 设计阶段
> **关联**：router.md（路由器调用云端时） / kickoff-meeting.md（使用多 Agent） / gantt-audit.md

---

## 🎯 系统职责

定义"多 Agent 协作"的具体部署方式，让多个 AI 视角能**并行 / 高效**地审查设定。

### 部署边界（Q31 锁定）

> "agent 这个可以云端直接上。本地我估计够呛。能力也不足，反应更慢"

**结论**：

- **写作时**：单 Agent 本地 Ollama
- **检视/打磨/立项会**：多 Agent **云端 mmx-cli**

云端多 Agent 同时启动，本地**只跑 1 个 Ollama 实例**。

---

## 🧩 4 + 2 个 Agent persona（MVP + Phase 2）

### MVP 必做 4 个

| # | Agent persona | 视角 | 审查重点 |
|---|---------------|------|---------|
| 1 | **档案 Agent** | 设定档案完整性视角 | 字段是否齐全 / 是否符合模板 |
| 2 | **世界观 Agent** | 世界规则视角 | 世界观规则的内在一致性 |
| 3 | **人物 Agent** | 人物行为视角 | 性格 / 动机 / 弧光自洽性 |
| 4 | **节奏 Agent** | 故事结构视角 | 起承转合 / 高潮分布 / 钩子密度 |

### Phase 2 增加 2 个

| # | Agent persona | 视角 | 审查重点 |
|---|---------------|------|---------|
| 5 | **读者 Agent** | 受众期待视角 | 看点 vs 受众期待对齐 |
| 6 | **金手指 Agent** | 设定利用视角 | 金手指用法 / 限制 / 升级 |

---

## 📋 MVP 启动顺序（P11 决策：单进程 + 多 persona）

由于 Ollama 本地**只跑 1 个进程**，而本地"够呛"——MVP 阶段的多 Agent 部署采用：

### 云端部署

每个 Agent persona = **独立的 mmx-cli 调用**（并行）

```python
# 同时发起 4 个云端推理
import asyncio
import mmx

AGENTS = {
    "档案 Agent": "你是严苛的设定档案审查员...",
    "世界观 Agent": "你是世界观规则审查员...",
    # ...
}

async def run_agent(name, system_prompt, user_prompt):
    return await mmx.infer_async(
        system=system_prompt,
        user=user_prompt,
        model="mmx-cloud-default",
    )

async def run_kickoff_meeting(settings):
    tasks = [
        run_agent(name, sys_p, render_settings(settings))
        for name, sys_p in AGENTS.items()
    ]
    return dict(zip(AGENTS.keys(), await asyncio.gather(*tasks)))
```

### 本地降级

如果 Cloud Relay 不可用：

- 本地 Ollama 单进程**串行**跑 persona 切换（4 次推理）
- 性能明显下降，但作为兜底可用

---

## 📝 Agent 输出格式（独立报告）

每个 Agent 必须按统一格式输出（便于汇总）：

```yaml
agent: 档案 Agent
timestamp: 2026-07-10T14:30:00
scope: "6 维度设定 + 时间线"
findings:
  - severity: 🔴_hard_block
    category: 内部矛盾
    location: settings/02-characters.md
    title: 主角金手指与世界观规则冲突
    description: 设定'主角拥有隐身能力'但世界观边界规定'本界无隐身术'
    suggestion: 删除'隐身能力'或调整规则
  - severity: 🟠_must_fix
    category: 字段缺失
    location: settings/03-framework.md
    title: 故事分段缺失
    description: 框架文件未填写故事分卷
    suggestion: 按模板补全
  - severity: 🟡_should_improve
    category: 文字表达
    location: settings/01-world.md
    title: "修仙界规则描述略生硬"
    description: ...
    suggestion: ...
  - severity: 🟢_approved
    category: 已对齐
    location: ...
    title: 主角动机与冲突对齐
```

### 严重度 4 级（按 kickoff-meeting.md）

- 🔴 **硬否决**：内部致命冲突（与硬伤级别相同）
- 🟠 **必须修复**：内部不一致
- 🟡 **建议改进**：可接受但有更优
- 🟢 **已对齐**：通过

---

## 📊 报告汇总（Q33 锁定：独立报告 + 问题汇总）

`books/<name>/kickoff_report.md` 包含两部分：

### Part 1：独立报告

每个 Agent 的独立报告完整保留，作者可以看到每个视角的具体发现。

### Part 2：问题汇总

按"问题维度"归类（同一问题被多 Agent 挑出，重复合并）：

```markdown
# 跨视角问题汇总

## 类别 1：内部矛盾（被 3 个 Agent 挑出）

### 问题 1.1：主角隐身能力 vs 世界观规则
- 🔴 档案 Agent：挑出
- 🔴 世界观 Agent：挑出
- 🟠 人物 Agent：认为是问题但严重度低
- 处理：必须修复

## 类别 2：字段缺失（被 1 个 Agent 挑出）

### 问题 2.1：故事分段缺失
- 🟠 档案 Agent
- 处理：必须修复
```

这样作者能：
- 看每个视角的细节（独立报告）
- 也能快速看主要问题（汇总）

---

## 🔧 实现细节

### prompt 模板（MVP 暂用通用模板）

```yaml
# prompts/agents/档案_Agent.yaml
system: |
  你是 [书名] 的设定档案审查员。
  你的任务是检查所有设文件是否完整填写，是否符合模板字段。
  严格但公正，按 4 级严重度（🔴/🟠/🟡/🟢）分类问题。
  输出格式：YAML（见 §报告格式）。

user_template: |
  请审查以下设定：
  
  {settings}
  
  请按输出格式列出发现的问题。
```

### 并发控制（MVP）

```python
# 默认 4 个 persona 并发（云端）
# 本地降级：串行

async def invoke_agents(payload, parallelism="cloud"):
    if parallelism == "cloud":
        return await invoke_cloud_parallel(AGENTS, payload)
    elif parallelism == "local":
        return invoke_local_serial(AGENTS, payload)
```

### token 预算

- 4 Agent 并发，每个 16k token 预算（共 64k token 计算成本）
- 立项会属于高频操作（每周多次），需要做 token budget 监控

---

## 🔐 授权与隐私

### 触发多 Agent 即视为授权云端

按 Q31.1 锁定："整个系统，只有真正进入'章节'写作状态，才暂时屏蔽云端 ai"。

所以：
- **立项会状态** = reviewing（可云端）→ 多 Agent 默认开启
- **写作状态** = writing（屏蔽云端）→ 多 Agent 不可用

### 用户隐私保护

- 作者通过 Cloud Relay 使用多 Agent（密钥不暴露）
- 多 Agent 输出的报告**保留在本地**（不外传到云端）
- Cloud Relay 本身**不持久化**任何 prompt 或输出

---

## 🧪 测试用例

1. **4 Agent 并发**：mock 4 个 mmx 调用，确认并发执行
2. **汇总去重**：同一问题被 3 Agent 挑出 → 汇总里只出现 1 次（按维度归类）
3. **降级到本地串行**：Cloud Relay 离线 → 改为本地串行 4 次推理
4. **writing 状态屏蔽**：写作时调用多 Agent → 必须失败
5. **token 预算**：单 Agent 超 16k token → 截断到 16k

---

## 🔗 关联

- `router.md` §二 —— 任务类型路由，"立项会"强制云端多 Agent
- `kickoff-meeting.md` —— 多 Agent 产出的消费者（汇总写报告）
- `gantt-audit.md` —— 巡检也是多 Agent 协作场景
- `MVP_AUTHORITY.md` §四 Phase 1.B —— 多 Agent 在 MVP 启动顺序中

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🔴 关键
- **关联决策**：P14 / Q30 / Q31 / Q33

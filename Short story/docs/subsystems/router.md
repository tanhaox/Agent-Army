# router.md — 推理路由器子系统

> **决策依据**：P3 / P15 / Q35（35 题压力测试锁定）
> **重要性**：🔴 **关键**（所有 AI 推理命令的统一入口）
> **状态**：📋 设计阶段
> **关联**：multi-agent-cloud.md / content-attribution.md / quality-guards-granularity.md

---

## 🎯 系统职责

推理路由器 = **所有 AI 推理命令的统一入口**，负责：

1. **状态判定**：writing / reviewing（基于 P15）
2. **任务类型路由**：防胡写 / 立项会 / 跨章审核 等
3. **降级回退**：本地超时/截断自动转云端
4. **密钥隔离**：mmx-cli 密钥仅在 Cloud Relay 内（绝不暴露给 CLI 进程）
5. **token 预算管理**：防止长上下文超载

---

## 🏗️ 架构图

```
                ┌────────────────────────────────────┐
                │  CLI 命令（如 consistency_check） │
                └─────────────────┬──────────────────┘
                                  ↓
                ┌────────────────────────────────────┐
                │  🛣️  推理路由器（router.py）       │
                │                                     │
                │  1. 状态判定（writing/reviewing）   │
                │  2. 任务类型识别                    │
                │  3. 本地/云端路由                   │
                │  4. token 预算检查                  │
                │  5. 降级回退管理                    │
                └─────┬───────────────────────┬──────┘
                      ↓                       ↓
            ┌────────────────────┐    ┌────────────────────┐
            │  本地 Ollama       │    │  Cloud Relay       │
            │  - 单 Agent        │    │  - 多 Agent persona │
            │  - 多 persona      │    │  - 密钥托管         │
            │  - 防胡写实时      │    │  - 限流             │
            └────────────────────┘    └─────────┬──────────┘
                                                ↓
                                       ┌────────────────────┐
                                       │  mmx-cli 云端       │
                                       └────────────────────┘
```

---

## 一、状态判定（P15 核心）

### writing 状态

- **触发条件**：
  - 作者正在写章节（最近 30 秒内有内容变更）
  - 全章节正在被防胡写守护（consistency_check）
- **行为**：
  - 仅调用本地 Ollama
  - 防胡写 P0 强制拦截
  - mmx-cli 不可用（即使 Cloud Relay 在线）
  - token 预算收窄到 4k（确保实时响应）

### reviewing 状态

- **触发条件**：
  - 作者在跑立项会、跨章审核、巡检、反悔修订
  - 作者主动退出 writing 状态（保存章节或命令切换）
- **行为**：
  - 本地优先 + 云端协同
  - 本地能处理的本地处理（防胡写复检、声纹、伏笔扫描、违规词）
  - 超出本地能力 → 自动转云端
  - 多 Agent 协作触发 → 直接云端

### 强制本地模式（人工开关）

- 作者可手动开启 "强制本地模式"（创作核心剧情时）
- 此时 **writing + reviewing 都强制本地**
- meta.md 记录 `force_local: true / false`

### force_local 与多 Agent 协同的处理（V4 锁定）

按 §四降级回退规则：当 `force_local=true` 时：

| 任务类型 | force_local=true 时 |
|---------|--------------------|
| **设立项（强制云端）** | **降级为本地串行**（4 个 Agent persona 在 Ollama 内顺序跑） |
| **跨章深度审核（强制云端）** | **降级为本地串行**（同窗口大小约束） |
| **防胡写**（写作实时）| 不受影响（已经本地） |
| **伏笔扫描** | 不受影响（已本地） |
| **其他 reviewing 任务** | 不受影响（已本地） |

**为什么这样设计**：

- 多 Agent 立项会是 MVP 必做，不能被 force_local 完全禁用
- force_local 是"宁可弱一点也要数据不出本机"
- 本地串行跑多 Agent persona 速度慢但**功能等价**

**警告**：meta.md 同时记录 force_local + kickoff_meeting 调用，UI 层提示"本地多 Agent 速度较慢"。

---

## 二、任务类型路由

每个命令在调用路由器时声明"任务类型"，路由器按类型决定部署：

| 任务类型 | 默认部署 | 是否可云端 | 备注 |
|---------|---------|-----------|------|
| **防胡写（实时）** | 本地 | ❌ 强制本地 | writing 状态强制 |
| **防胡写（复检）** | 本地 | ✅ reviewing 可云端 | 跨章用 |
| **伏笔扫描** | 本地 | ✅ reviewing 可云端 | F4 |
| **伏笔半自动闭环** | 本地 | ✅ reviewing 可云端 | F3 |
| **违规词验证** | 本地 | ⚠️ 纯本地规则脚本即可 | 词典匹配 |
| **机械表达检测** | 本地 | ⚠️ 本地规则 + Ollama 抽样 | 混合 |
| **AI 味检测** | 本地 | ✅ reviewing 可云端 | |
| **声纹核对** | 本地 | ✅ reviewing 可云端 | |
| **立项会** | 云端 | ✅ **强制云端** | 多 Agent |
| **章节规划** | 本地 | ✅ reviewing 可云端 | |
| **跨章深度审核** | 云端 | ✅ **强制云端** | 大窗口 |
| **甘特图泳池巡检** | 混合 | ✅ | 本地按泳池，云端汇总 |
| **设定打磨（增量）** | 云端 | ✅ reviewing 可云端 | Q30 |

---

## 三、Cloud Relay（薄密钥托管层）

### 它做什么

Cloud Relay 是一个**极简**的 HTTP 服务，仅做三件事：

1. 接收 CLI 发来的推理请求（含 prompt、参数、模型选择）
2. 注入 mmx-cli API key（不暴露给 CLI 进程）
3. 调用 mmx-cli，返回结果

### 它不做什么

- ❌ 不做 AI 推理（由 mmx-cli 做）
- ❌ 不存 prompt 历史（除非用户主动启用）
- ❌ 不参与认证（仅本地 loopback 或局域网）

### 为什么需要这一层

直接让 CLI 进程持有 mmx-cli key 是**反模式**：
- CLI 进程可能被日志捕获 / 异常堆栈泄露
- 进程间 key 共享会让 key 写入磁盘的概率上升

通过 Cloud Relay，CLI 只发 HTTP 请求，**key 在另一个进程内**。

### MVP 实现策略

Phase 1.MVP 用最简单的 Cloud Relay：

```python
# cloud_relay.py (≤ 50 行)
from flask import Flask, request
import mmx

app = Flask(__name__)
MMX_KEY = os.environ['MMX_API_KEY']  # 仅在 Cloud Relay 进程内

@app.route('/infer', methods=['POST'])
def infer():
    data = request.json
    return mmx.infer(
        prompt=data['prompt'],
        model=data.get('model', 'default'),
        temperature=data.get('temperature', 0.7),
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
```

启动方式：

```bash
# 用户先启动 Cloud Relay
python shared/cloud_relay.py   # 需配置 MMX_API_KEY 环境变量

# CLI 通过 HTTP 调用
curl -X POST http://127.0.0.1:5001/infer -d '{...}'
```

---

## 四、降级回退（核心特性）

### 回退触发条件

1. **本地推理超时**（默认 30 秒，超时即回退）
2. **本地输出被截断**（token 达到上限，输出含 `...truncated`）
3. **本地置信度低**（Ollama 返回的 logprobs 平均值低于阈值）
4. **任务类型明确需要云端**（如多 Agent 立项会）

### 回退流程

```
[本地 Ollama 启动]
   ↓
   ├─ 成功 + 完整输出 → 返回
   ├─ 超时 / 截断 / 低置信度
   ↓
[Cloud Relay 启动]
   ↓
   ├─ 成功 → 返回
   ├─ 失败 → 上报错误，提示用户
```

### 回退日志

每次回退写到 `logs/router_fallbacks.log`，便于：

- 诊断本地能力不足
- 调整任务类型路由表
- 计算"本地优先 vs 云端兜底"的成功率

---

## 五、token 预算管理

### 各任务的 token 上限

| 任务 | 上限 | 说明 |
|------|------|------|
| 防胡写（实时） | 4k | 仅看当前段 + 直接相关设定 |
| 防胡写（复检） | 8k | 章节级 |
| 伏笔扫描 | 8k | 本章 + 已埋伏笔库 |
| 声纹核对 | 6k | 角色声纹 + 当前对话 |
| 立项会 | 16k+ | 多 Agent 协作必须大窗口 |
| 跨章深度审核 | 32k+ | mmx-cli 处理 |
| 泳池巡检（单泳池） | 4k | 每泳池独立 |
| 设定打磨（增量） | 8k | 修改字段 + 联动 |

### 超长输入的降级策略

如果设定库太大导致超出 token 上限，按优先级截断：

1. 必读：当前任务直接相关字段
2. 次要：任务类型相关的其他字段
3. 摘要：其余设定用 200 字摘要替代

---

## 六、prompt persona 切换（Q31 / P14）

### 单 Agent 多 persona

Ollama 部署**一个进程**，通过切换 system prompt 实现多 Agent：

```python
PERSONAS = {
    "档案 Agent": "你是设定档案审查员...",
    "世界观 Agent": "你是世界观规则审查员...",
    # ...
}

def invoke_agent(persona_name, prompt):
    full_prompt = f"{PERSONAS[persona_name]}\n\n{prompt}"
    return ollama.infer(full_prompt)
```

### MVP 选用的 4 个 persona（来自 kickoff-meeting.md）

- 档案 Agent
- 世界观 Agent
- 人物 Agent
- 节奏 Agent

（注：剩下"读者 Agent"和"金手指 Agent"在 Phase 2 补充。）

---

## 七、API 设计（MVP 路由器）

```python
# router.py 公开 API

def route_request(
    task_type: str,           # e.g. "foreshadow_scan"
    state: str,               # "writing" | "reviewing" （2 态）— force_local 是独立开关，不混入
    force_local: bool,        # True: 强制所有任务走本地
    payload: dict,            # 任务特定数据
    fallback_enabled: bool,   # 是否允许降级
) -> dict:
    """返回 {'output': ..., 'used': 'local' | 'cloud' | 'none'}"""
```

### 调用示例

```python
# consistency_check 命令调用路由器
result = router.route_request(
    task_type="consistency_check_realtime",
    state="writing",
    payload={
        "paragraph_text": current_para,
        "settings_summary": settings_summary,
    },
    fallback_enabled=False,  # writing 不允许降级
)
```

---

## 八、监控与审计

路由器每次调用都记录：

```yaml
logs/router_calls.log:
  - timestamp
  - command (e.g. consistency_check)
  - task_type
  - state (writing/reviewing)
  - force_local (true/false)
  - backend_used (local/cloud/none)
  - prompt_tokens
  - completion_tokens
  - latency_ms
  - fallback_triggered (true/false)
  - fallback_reason (timeout/truncated/low_confidence/forced)
```

这些数据用于：
- 计算"本地覆盖率"
- 发现 Ollama 模型不适合的任务
- 给用户展示"今天的 AI 工作量"

---

## 🧪 测试用例（MVP 必过）

1. **writing 状态屏蔽云端**：在 writing 状态调用云端任务 → 必须失败 / 警告
2. **本地超时触发降级**：mock 一个超长的本地任务 → 应该自动转云端
3. **跨章节自动切云端**：token > 8k 时应该走云端
4. **强制本地模式**：作者开启 force_local 时，云端路径全部短路
5. **Cloud Relay 离线**：CLI 不崩溃，仅上报错误
6. **多 persona 切换**：4 个 persona 输出风格必须明显不同

---

## 🔗 关联

- `multi-agent-cloud.md` —— 多 Agent 部署协议（路由器把请求路由到这里）
- `content-attribution.md` —— 路由器输出必须带 source 标注
- `quality-guards-granularity.md` —— 各门禁的 token 预算上限
- `MVP_AUTHORITY.md` §四 Phase 1.A —— 路由器在 MVP 启动顺序中第二顺位

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🔴 关键
- **关联决策**：P3 / P14 / P15 / Q31 / Q35

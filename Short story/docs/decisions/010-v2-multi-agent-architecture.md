# 010-v2-multi-agent-architecture.md — 多 Agent 架构（v2 双轨）

> **历史**：原 `010-multi-agent-architecture.md` "4 个专职 Agent"
> **v2 重写**：原文件讲"专精 Agent"，35 题压力测试反转：单 Agent 多通道（写作）+ 多 Agent 协作（云端立项会）双轨
> **v2 依据**：P14 + Q30 / Q31 / Q33
> **状态**：✅ 当前活跃决策

---

## 🎯 设计目标

让多 Agent 协作在**正确的时机**启用——本地写章时不必拖累，云端立项会时规模到位。

---

## ✅ v2 双轨架构（取代 v1 的"4 个专职 Agent")

### 轨道 1：写作流（本地 Ollama 单 Agent 多通道）

**适用场景**：防胡写实时 / 伏笔扫描 / 声纹核对 / 机械表达检测 / 违规词验证

**部署**：
- 单 Ollama 实例
- 通过切换 system prompt 实现"多 persona"
- 同时**只跑一个推理**

**为什么这样设计**：

- Ollama 本地窗口有限（4k-8k），并发 4 个 Agent 会爆
- 写作时不需要"多视角审查"，AI 角色固定为"严苛守护者"
- 性能优先——守护必须实时，<=0.5 秒

### 轨道 2：reviewing 流（云端 mmx-cli 多 Agent 协作）

**适用场景**：
- 立项会（kickoff_meeting）
- 设定打磨 / 跨章深度审核 / 反悔修订
- 甘特图 6+ 泳池巡检

**部署**：
- 4-6 个 mmx-cli 调用**并发**
- 每个 Agent 独立输出独立报告
- 合并为"问题汇总"

**为什么这样设计**：

- 用户原话（Q31）："agent 这个可以云端直接上。本地我估计够呛。能力也不足，反应更慢"
- 多 Agent 立项会要求**大窗口 + 强推理**，本地 Ollama 不够
- setting / 打磨 / 审核不是高频操作（每周几次），云端成本可接受

### 双轨切换

按 P15（状态切换原则）：
- writing 状态 → 走轨道 1
- reviewing 状态 → 可走轨道 1 + 轨道 2
- 强制本地模式 → 全走轨道 1

详见 `docs/subsystems/router.md` §一状态判定。

---

## 🤖 Agent Persona 定义（4 个 + 2 个）

### MVP 必做 4 个

| # | 名字 | 视角 | System Prompt 片段 |
|---|------|------|-------------------|
| 1 | **档案 Agent** | 设定档案完整性 | "你是严苛的设定档案审查员..." |
| 2 | **世界观 Agent** | 世界规则 | "你是世界观规则审查员..." |
| 3 | **人物 Agent** | 人物行为 | "你是人物行为审查员..." |
| 4 | **节奏 Agent** | 故事结构 | "你是故事节奏审查员..." |

### Phase 2 增加 2 个

| # | 名字 | 视角 |
|---|------|------|
| 5 | **读者 Agent** | 受众期待 |
| 6 | **金手指 Agent** | 设定利用 |

---

## 🔄 与原 v1 的差异

| 项目 | v1（已废弃） | v2（当前） |
|------|-------------|-----------|
| Agent 数 | 4 个专职 Agent 同时跑 | 1 个本地（写作时） + 4-6 个云端（reviewing） |
| 部署 | 全部在 Ollama | 单 Agent 本地；多 Agent 云端 |
| 何时启用 | 所有 AI 推理 | 仅 reviewing 状态 |
| prompt 切换 | 不需要 | Ollama 切换 system prompt |
| 任务分工 | 每个 Agent 一类任务 | Ollama 一个 Agent 处理所有实时任务 |

---

## 🛡️ 状态切换协议

详见 `docs/subsystems/router.md` §四

```
用户行为 → 系统判定 → 状态 → 启用 Agent 模式
─────────────────────────────────────────
write.html 写作 → writing → 单 Agent Ollama 多 persona
kickoff_meeting → reviewing → 多 Agent mmx-cli 并发
cumulative_audit → reviewing → 多 Agent mmx-cli + 跨章
跨章修订单 → reviewing → 多 Agent mmx-cli
手动 "force_local" → 强制本地 → 单 Agent Ollama
```

---

## 💰 成本与隐私权衡

### writing 状态

- **零云端成本**（writing 屏蔽云端）
- **零隐私泄露**（仅本地）
- 计算成本：本地 CPU / GPU

### reviewing 状态

- **云端成本**：每次多 Agent 跑 4-6 mmx 调用，每次 16k tokens
- **隐私风险**：设定 / 章节内容发往云端
- **作者掌控**：强制本地模式可关闭

### 优化策略

- 立项会触发时**只**在 reviewing 状态
- 立项会**不是每次都要多 Agent**：
  - 增量模式（Q30）→ 只跑相关 1-2 Agent
  - 全量模式 → 4-6 Agent 并发
- 巡检（甘特图）按泳池并行，单泳池 token 较小

---

## 🧪 测试用例

1. **writing 单 Agent**：写作时调本地 → 单进程，0.3 秒返回
2. **reviewing 多 Agent 并发**：4 Agent 并发 → 总耗时 ≤ 单 Agent × 2（云端带宽近似）
3. **降级**：Cloud Relay 断开 → 多 Agent 自动降级为本地单 Agent 串行
4. **强制本地**：作者开 force_local → 多 Agent 阻塞，必须 force_local=false 才能用
5. **prompt 切换**：同一 Ollama 实例切换 4 种 persona → 输出风格明显不同

---

## 🔗 关联

- `docs/subsystems/multi_agent_cloud.md` —— 多 Agent 部署协议（详细）
- `docs/subsystems/router.md` —— 状态切换 + 任务路由
- `docs/subsystems/kickoff_meeting.md` —— 多 Agent 的消费者
- `docs/MVP_AUTHORITY.md` §四 —— 部署时序

---

## 📌 元信息

- **历史决策**：[010-multi-agent-architecture.md](./010-multi-agent-architecture.md)
- **v1 关键问题**：4 个专职 Agent 同时跑 Ollama，本地窗口不够
- **v2 解决方案**：写作时单 Agent 多通道；reviewing 时多 Agent 云端并发
- **变更触发**：Q30 + Q31 + Q33 + P14
- **创建日期（原版）**：2026-07-08
- **v2 创建日期**：2026-07-10
- **重要性**：🔴 关键

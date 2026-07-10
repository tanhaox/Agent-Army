# state-detector.md — 状态检测子系统

> **决策依据**：P15 / B1（横纵向研判补遗）
> **重要性**：🔴 **关键**（P15 状态切换原则的"启动钥匙"；MVP 必做）
> **状态**：✅ 完整版
> **关联**：router.md（路由器读状态）/ content-attribution.md / multi-agent-cloud.md

---

## 🎯 系统职责

**自动检测 writing / reviewing 状态**，是 router（推理路由器）做"该走本地还是云端"判断的依据。

**核心承诺**：

- ✅ 作者不需要知道"状态"这个概念
- ✅ 打开 write.html → 自动进入 writing
- ✅ 保存章节 → 自动退出 writing
- ✅ 完全文件即状态（无 daemon / 无数据库）

---

## 📋 状态定义（极简）

只有 **2 个状态**（router.md §一 第三态 `force_local` 是 P15 内部细节，不影响本子系统）：

| 状态 | 含义 | 触发 | 锁定 |
|------|------|------|------|
| **writing** | 作者正在 write.html 上写 | 打开 write.html | 🔴 屏蔽云端 |
| **reviewing** | 其他所有情况 | 默认 | ✅ 本地 + 云端 |

---

## 📁 状态存储：`.state/writing.lock`

每本书在 `books/<name>/.state/writing.lock` 存状态：

```yaml
# writing.lock（存在即 writing，不存在即 reviewing）
---
state: writing
chapter: 50
entered_at: 2026-07-10T15:30:00
entered_by: write.html  # 或 cli/write.py
process_id: 12345       # 哪个进程持有
---
```

**判定规则**：

- 文件存在 → writing
- 文件不存在 → reviewing

**简单到不需要解析 YAML 内容**。但人类可读的 metadata 用于审计。

---

## 🪟 状态生命周期

### 进入 writing

**触发条件**（任一）：

1. **Web 端**：浏览器打开 `web/write.html` 加载完成
   - JS POST `/api/state/acquire`
   - 后端写 `.state/writing.lock`

2. **CLI 端**：`python -m ai_coauthor write --chapter N` 命令启动
   - 命令执行前自动 acquire

3. **CLI 端自动触发**：F4 每章末扫 / 防胡写守护等子任务
   - 守护命令启动前 acquire

### 退出 writing

**触发条件**（任一）：

1. **Web 端**：作者点击"保存"按钮，或 `Ctrl+S`
2. **Web 端**：浏览器关闭 / 切走 / unload 事件
3. **CLI 端**：write 命令自然结束
4. **CLI 端**：守护命令结束（如 `consistency_check --once` 完成）
5. **手动**：`python -m ai_coauthor state release`

### 异常退出

如果 acquire 进程崩溃（断电 / kill）：

- 锁文件残留 → 下次 acquire 会发现"已存在锁"
- 触发**僵尸锁检测**：如果 lock 文件的 process_id 已不存在 + 持有时间 > 30 分钟 → 自动释放

---

## 🚦 跨进程冲突处理

### 场景 1：作者同时开 2 个 write.html 标签

后到的 acquire 请求会发现 lock 存在。处理：

- **等待**（推荐，β 锁定）：每秒检查一次，最多等 30 秒
- 30 秒后仍未释放 → 报错给用户（"请先关闭另一个 write.html"）

### 场景 2：writing 中跑 reviewing 命令

如作者保存了一章，然后跑 `python -m ai_coauthor cumulative_audit`：

- save → 触发 release → writing.lock 删除
- cumulative_audit → acquire 自己 → state=reviewing
- 命令开始后 → 自动读取 lock 状态正常

### 场景 3：reviewing 中保存章节

如作者在 setup_consult 页面修改了设定，然后去 write.html：

- **修改设定不触发 writing 状态**（写设定 ≠ 写章节）
- 作者进 write.html 时才 acquire

---

## 📐 状态与命令的对应

| 命令 | 状态锁定 |
|------|---------|
| `write`（CLI 写章节） | writing |
| `consistency_check` | writing（如在写作中）或 reviewing |
| `foreshadow_track` | reviewing |
| `audit` | reviewing |
| `kickoff_meeting` | reviewing |
| `setup_consult` | reviewing |
| `plan_chapter` | reviewing |
| **任何其他** | reviewing |

---

## 🔌 API 设计

### Python API（路由器内部）

```python
# state_detector.py

def acquire_state(book_name: str, chapter: int, by: str) -> bool:
    """acquire writing 锁。返回 True / False（等待 30 秒后失败）"""
    
def release_state(book_name: str) -> bool:
    """释放 writing 锁"""

def get_current_state(book_name: str) -> str:
    """返回 'writing' | 'reviewing'"""

def check_zombie_lock(book_name: str) -> None:
    """清理过期锁"""
```

### HTTP API（Web 端用）

```
POST /api/state/acquire     # acquire
POST /api/state/release     # release
GET  /api/state             # 查询当前状态
```

---

## 🔒 防"AI 学坏"风险

### 反例 1：作者保存完去吃饭，1 小时后回来 → lock 残留

**已有方案**：

- 保存即 release（不会残留）
- zombie lock 检测（30 分钟无进程 → 清理）

### 反例 2：浏览器崩溃时未触发 unload

**防御**：

- `window.addEventListener('beforeunload')` 触发 release
- 前端定期 heartbeat（每 30 秒 PING）
- 后端超时清理（heartbeat 30 秒未更新 → 视为进程死亡）

---

## 🧪 测试用例（MVP 必过）

1. **打开 write.html → writing 锁自动创建**
2. **保存章节 → writing 锁自动删除**
3. **浏览器关闭 → writing 锁通过 unload 释放**
4. **断电恢复 → zombie lock 自动清理**（30 分钟超时）
5. **第二个 write.html 标签 → 后到者等待 / 报错**
6. **状态查询**：`get_current_state(book_name)` 返回正确
7. **跨命令**：从 reviewing 转 writing 再转 reviewing 链路正常

---

## 📁 状态目录结构

每本书新增 `.state/` 目录（git 忽略）：

```
books/<name>/
├── settings/
├── chapters/
├── timeline.md
├── voice-prints/
├── ...
└── .state/                   ← 新增（git 忽略）
    └── writing.lock          ← 当前 writing 锁（存在即 writing）
```

### `.gitignore` 追加

```gitignore
# 运行时状态文件
**/.state/*
!books/**/.gitkeep
```

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| 文件锁（writing.lock） | ✅ | ✅ |
| 自动进入/退出（打开 write.html / 保存） | ✅ | ✅ |
| Zombie 锁自动清理 | ✅ | ✅ |
| 跨进程等待 30 秒 | ✅ | ✅ |
| Web API `/api/state/*` | ✅ | ✅ |
| Heartbeat 长连接 | ❌ | ✅ |
| 多端协同写作（多人同时写） | ❌ | ✅（Phase 4+） |

---

## 🔗 与 P15 的协同

state-detector 是 P15 的"感知神经"：

```
state-detector (本子系统)
   ↓
   状态: writing / reviewing
   ↓
router.md §一 状态判定
   ↓
   task_type + state → 部署 (本地 / 云端)
```

P15 已经在 router.md 写好了状态如何影响任务路由；本子系统只负责"状态是什么"。

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🔴 关键
- **关联决策**：P15 / B1（横纵向研判补遗）
- **关联子系统**：router.md / content-attribution.md / multi-agent-cloud.md / all commands
- **关联命令**：写章节命令（acquire）/ 守护命令（trigger acquire）/ reviewing 命令（自动 reviewing 状态）
- **关联文件**：每本书 `.state/writing.lock`（git 忽略）

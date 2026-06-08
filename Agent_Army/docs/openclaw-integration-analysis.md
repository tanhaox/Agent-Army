# Agent Army + OpenClaw 集成方案分析

> **版本**: v1.0
> **日期**: 2026-03-20
> **关键问题**: edict基于OpenClaw框架，Agent Army如何集成？

---

## 一、OpenClaw框架分析

### 1.1 OpenClaw核心特性

根据搜索结果和edict文档，OpenClaw提供：

| 特性 | 说明 | Agent Army现状 |
|------|------|---------------|
| **Agent Workspace** | 每个agent独立工作空间 | ❌ 无 |
| **Skills系统** | 每个agent独立技能配置 | ❌ 无 |
| **权限矩阵** | agent间调用权限控制 | ❌ 无 |
| **状态机** | 任务状态流转管理 | ⚠️ 自定义实现 |
| **消息总线** | agent间通信机制 | ❌ 无 |
| **配置管理** | openclaw.json统一配置 | ⚠️ ConfigManager |
| **SOUL.md人格** | agent角色定义 | ❌ 无 |

### 1.2 edict对OpenClaw的依赖

```
edict = OpenClaw + 三省六部业务逻辑
        ↓
    - Agent Workspace（agents/目录）
    - 权限矩阵（openclaw.json）
    - SOUL.md人格定义
    - 状态机（_STATE_FLOW）
    - 消息派发（auto dispatch）
```

**关键依赖**：
1. **openclaw.json** - Agent注册和权限矩阵
2. **agents/*/SOUL.md** - Agent人格和规则
3. **OpenClaw Gateway** - Agent调度和通信
4. **Python stdlib server** - 后端API

---

## 二、集成方案对比

### 方案A：完全引入OpenClaw（彻底重构）

**实施方式**：
```
1. 安装OpenClaw框架
2. 将Agent Army的所有agent迁移到OpenClaw workspace
3. 复制edict的完整前端（React dashboard）
4. 后端使用OpenClaw Gateway
```

**优点**：
- ✅ 完全复制edict的所有功能
- ✅ 获得OpenClaw的成熟基础设施
- ✅ 与edict生态兼容
- ✅ 权限矩阵、状态机开箱即用

**缺点**：
- ❌ 需要完全重构现有代码
- ❌ 学习曲线陡峭（OpenClaw + edict双框架）
- ❌ 周期长（2-4周）
- ❌ 可能引入新的依赖问题

**工作量**：**2-4周**

---

### 方案B：复制UI，自己实现机制（渐进式）⭐ **推荐**

**实施方式**：
```
1. 复制edict的React dashboard（UI层）
2. 后端继续使用Agent Army现有架构
3. 自己实现类似OpenClaw的核心机制：
   - 状态机（_STATE_FLOW）
   - 权限矩阵（_PERMISSION_MATRIX）
   - Agent派发（auto_dispatch）
4. 提供REST API给前端调用
```

**优点**：
- ✅ 快速获得三省六部制UI
- ✅ 保持现有代码结构
- ✅ 可控的技术债务
- ✅ 灵活定制业务逻辑
- ✅ 周期短（1-2周）

**缺点**：
- ❌ 需要自己维护核心机制
- ❌ 无法直接使用edict的agent生态
- ❌ 后续可能需要重复造轮子

**工作量**：**1-2周**

---

### 方案C：混合方案（后期迁移到OpenClaw）

**实施方式**：
```
阶段1（1周）：
  - 复制edict UI
  - 后端实现简化版状态机
  - 快速上线

阶段2（2-3周）：
  - 逐步引入OpenClaw
  - 迁移agent到OpenClaw workspace
  - 完整权限矩阵

阶段3（1周）：
  - 完全切换到OpenClaw Gateway
  - 移除自造轮子
```

**优点**：
- ✅ 快速验证UI效果
- ✅ 降低一次性重构风险
- ✅ 可边做边学OpenClaw
- ✅ 最终达到完全兼容

**缺点**：
- ❌ 分两次开发，总工时可能更长
- ❌ 需要维护过渡期代码

**工作量**：**4-6周（总计）**

---

## 三、推荐方案：方案B（复制UI + 自实现机制）

### 3.1 为什么选方案B？

1. **风险可控**：
   - 不引入新框架
   - 现有代码继续工作
   - 可以快速回滚

2. **周期合理**：
   - 1-2周看到效果
   - 满足用户"要这种格式"的需求

3. **技术债务可控**：
   - 状态机、权限矩阵实现难度不高
   - Python stdlib即可实现后端
   - 前端使用现成React组件

4. **业务优先**：
   - 用户要的是"三省六部制的格式和体验"
   - 不是"要使用OpenClaw框架"
   - UI + 流程才是核心

### 3.2 实施架构

```
┌─────────────────────────────────────────────────────┐
│  React Frontend（复制edict）                          │
│  - dashboard.html + components/                      │
│  - WebSocket连接到Agent Army后端                     │
└────────────────┬────────────────────────────────────┘
                 │ REST API / WebSocket
┌────────────────▼────────────────────────────────────┐
│  Agent Army Backend（FastAPI/Streamlit）              │
│  - 状态机：_STATE_FLOW                               │
│  - 权限矩阵：_PERMISSION_MATRIX                      │
│  - Agent派发：auto_dispatch()                        │
│  - Agent包装：wrapper现有agent                        │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  现有Agent（保持不变）                                │
│  - IndustryChainAnalyzer                             │
│  - FundamentalAnalyzer                               │
│  - CommanderAgent                                    │
│  - InvestmentAnalysisWorkflow                        │
└─────────────────────────────────────────────────────┘
```

---

## 四、具体实施步骤（方案B）

### 4.1 阶段1：前端UI复制（3天）

**任务**：
1. ✅ 克隆edict的dashboard目录
2. ✅ 修改API endpoint指向Agent Army
3. ✅ 修改WebSocket连接地址
4. ✅ 调整配色和文案（如果需要）

**文件清单**：
```
frontend/
├── dashboard/
│   ├── index.html          # 主页面
│   ├── dashboard.html      # 看板页面
│   ├── dist/               # 构建产物
│   │   ├── index.html
│   │   ├── assets/
│   │   │   ├── index-*.js
│   │   │   └── index-*.css
│   └── server.py           # 开发服务器（可删除）
```

**修改API端点**：
```javascript
// 原来：连接OpenClaw Gateway
const WS_URL = 'ws://localhost:18789/ws';

// 修改为：连接Agent Army后端
const WS_URL = 'ws://localhost:8501/analysis-progress';
```

### 4.2 阶段2：后端核心机制实现（5天）

#### 4.2.1 状态机实现

```python
# src/core/state_machine.py

_STATE_FLOW = {
    'Pending':   ('Taizi',    '皇上',    '太子',     '待处理旨意转交太子分拣'),
    'Taizi':     ('Zhongshu', '太子',     '中书省',   '太子分拣完毕，转中书省起草'),
    'Zhongshu':  ('Menxia',   '中书省',   '门下省',   '中书省方案提交门下省审议'),
    'Menxia':    ('Assigned',  '门下省',   '尚书省',   '门下省准奏，转尚书省派发'),
    'Assigned':  ('Doing',    '尚书省',   '六部',     '尚书省开始派发执行'),
    'Doing':     ('Review',   '六部',     '尚书省',   '各部完成，进入汇总'),
    'Review':    ('Done',     '尚书省',   '中书省',   '全流程完成，中书省回奏'),
}

def advance_state(current_state):
    """状态转移"""
    if current_state in _STATE_FLOW:
        return _STATE_FLOW[current_state][0]
    raise ValueError(f"Invalid state: {current_state}")

def get_agent_for_state(state):
    """获取状态对应的agent"""
    _STATE_AGENT_MAP = {
        'Taizi':     'taizi',
        'Zhongshu':  'zhongshu',
        'Menxia':     'menxia',
        'Assigned':   'shangshu',
        'Doing':      None,  # 从org推断
        'Review':     'shangshu',
    }
    return _STATE_AGENT_MAP.get(state)
```

#### 4.2.2 权限矩阵实现

```python
# src/core/permission_matrix.py

_PERMISSION_MATRIX = {
    'taizi':     ['zhongshu'],
    'zhongshu':  ['menxia', 'shangshu'],
    'menxia':    ['shangshu', 'zhongshu'],  # 可回调中书
    'shangshu':  ['libu', 'hubu', 'bingbu', 'xingbu', 'gongbu', 'libu_hr'],
    'libu':      [],
    'hubu':      [],
    # ... 其他六部无权限调用他人
}

def check_permission(caller, callee):
    """检查caller是否有权限调用callee"""
    if caller not in _PERMISSION_MATRIX:
        return False
    return callee in _PERMISSION_MATRIX[caller]
```

#### 4.2.3 Agent派发实现

```python
# src/core/dispatcher.py

async def auto_dispatch_agent(task_id):
    """自动派发agent处理任务"""
    task = get_task(task_id)

    # 获取当前状态对应的agent
    agent_id = get_agent_for_state(task['state'])

    if not agent_id:
        # Doing状态，从org推断
        agent_id = _ORG_AGENT_MAP.get(task['org'])

    # 包装并调用agent
    agent = get_agent(agent_id)
    result = await agent.execute(task)

    # 更新任务状态
    update_task_progress(task_id, {
        'agent': agent_id,
        'result': result,
        'timestamp': datetime.now().isoformat()
    })

    # 自动推进状态
    new_state = advance_state(task['state'])
    update_task_state(task_id, new_state)

    return result
```

#### 4.2.4 REST API实现

```python
# src/api/routes.py

from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.post("/api/task/create")
async def create_task(stock_code: str):
    """创建分析任务（圣旨）"""
    task_id = f"ANALYSIS-{stock_code}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task = {
        'id': task_id,
        'stock_code': stock_code,
        'state': 'Pending',
        'flow_log': [],
        'progress_log': []
    }
    save_task(task)

    # 自动派发太子分拣
    await auto_dispatch_agent(task_id)

    return {'task_id': task_id}

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    return get_task(task_id)

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket推送实时进度"""
    await websocket.accept()

    task_id = await websocket.receive_text()

    # 订阅任务进度
    async for progress in subscribe_task_progress(task_id):
        await websocket.send_json(progress)
```

### 4.3 阶段3：Agent包装（2天）

```python
# src/core/agent_wrapper.py

class AgentWrapper:
    """包装现有agent为三省六部制接口"""

    def __init__(self, agent_id, agent_impl):
        self.agent_id = agent_id
        self.impl = agent_impl

    async def execute(self, task):
        """执行agent，返回标准格式"""

        # 转换输入格式
        stock_code = task['stock_code']

        # 调用原有agent
        if self.agent_id == 'zhongshu':
            # 中书省 = 产业链分析
            result = await self.impl.analyze(stock_code)

            # 转换输出格式
            return {
                'industry_score': result.get('score'),
                'market_share': result.get('market_share'),
                'ranking': result.get('ranking'),
                'todos': [
                    {'id': '1', 'title': '行业调研', 'status': 'completed'},
                    {'id': '2', 'title': '竞争分析', 'status': 'completed'},
                    {'id': '3', 'title': '待审议', 'status': 'pending'}
                ]
            }

        elif self.agent_id == 'menxia':
            # 门下省 = Commander审核
            result = await self.impl.precheck_report(
                agent_name="中书省",
                report_type="industry",
                report_data=task['department_results']['中书省']
            )

            return {
                'status': 'approved' if result['quality_score'] >= 80 else 'rejected',
                'quality_score': result['quality_score'],
                'review_comments': result.get('comments', [])
            }

        # ... 其他agent包装

# 包装现有agent
_wrapped_agents = {
    'zhongshu': AgentWrapper('zhongshu', IndustryChainAnalyzer(config)),
    'menxia': AgentWrapper('menxia', CommanderAgent()),
    'hubu': AgentWrapper('hubu', FundamentalAnalyzer(config)),
    # ...
}

def get_agent(agent_id):
    """获取包装后的agent"""
    return _wrapped_agents[agent_id]
```

---

## 五、关键文件清单（方案B）

### 5.1 新增文件

| 文件路径 | 说明 | 工作量 |
|---------|------|--------|
| `frontend/dashboard/` | 复制edict前端 | 1天 |
| `src/core/state_machine.py` | 状态机实现 | 0.5天 |
| `src/core/permission_matrix.py` | 权限矩阵实现 | 0.5天 |
| `src/core/dispatcher.py` | Agent派发 | 1天 |
| `src/core/agent_wrapper.py` | Agent包装 | 1天 |
| `src/api/routes.py` | REST API | 1天 |
| `src/api/websocket.py` | WebSocket推送 | 1天 |

### 5.2 修改文件

| 文件路径 | 修改内容 | 工作量 |
|---------|---------|--------|
| `web_app.py` | 集成前端路径 | 0.5天 |
| `agents/*/agent.json` | 创建agent配置 | 1天 |

**总计**：**10个工作日**（2周）

---

## 六、风险与缓解

### 6.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **WebSocket不稳定** | 🟡 中 | 高 | 使用SSE备选方案 |
| **状态机逻辑错误** | 🟢 低 | 高 | 详细单元测试 |
| **Agent包装失败** | 🟡 中 | 中 | 保留原始调用方式 |
| **前端兼容性** | 🟢 低 | 低 | 使用原版React代码 |

### 6.2 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **用户不适应新UI** | 🟢 低 | 低 | 保留旧入口 |
| **流程复杂度增加** | 🟡 中 | 中 | 新手引导 + Tooltip |
| **性能下降** | 🟢 低 | 中 | 性能测试 + 优化 |

---

## 七、后续优化路径（如果需要OpenClaw）

如果后期发现需要完整OpenClaw功能，可以渐进迁移：

### 7.1 阶段1：引入OpenClaw配置

- 创建 `openclaw.json`
- 添加 `SOUL.md` 人格定义
- 不改变代码结构

### 7.2 阶段2：迁移Agent Workspace

- 将agent移到 `agents/` 目录
- 遵循OpenClaw workspace结构
- 保留现有实现

### 7.3 阶段3：切换到OpenClaw Gateway

- 替换自实现的状态机
- 使用OpenClaw的权限矩阵
- 删除冗余代码

---

## 八、总结与建议

### 推荐方案：**方案B（复制UI + 自实现机制）**

**理由**：
1. ✅ **快速见效**：1-2周看到三省六部制UI
2. ✅ **风险可控**：不引入新框架依赖
3. ✅ **业务优先**：满足用户"要这种格式"的需求
4. ✅ **灵活定制**：可根据业务调整流程

### 实施时间表

```
Week 1：前端复制 + API实现
  Day 1-3：复制edict前端，修改endpoint
  Day 4-5：实现REST API和WebSocket

Week 2：后端机制 + Agent包装
  Day 1-2：状态机、权限矩阵、派发器
  Day 3-4：Agent包装
  Day 5：集成测试

Week 3（可选）：优化和上线
  Day 1-2：性能优化
  Day 3-4：用户测试
  Day 5：上线部署
```

### 关键决策点

**如果**后续发现：
- 需要更多OpenClaw特性 → 迁移到方案C
- 自维护成本太高 → 迁移到方案A
- 当前方案够用 → 保持方案B

---

**创建时间**: 2026-03-20
**设计师**: Claude
**状态**: 待用户确认

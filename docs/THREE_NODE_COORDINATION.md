# 三地协同架构详解

**日期**: 2026-03-13
**目的**: 解释本地、国内服务器、国外服务器如何协同工作

---

## 🎯 核心理念：各司其职 + 低延迟通信

```
┌─────────────────────────────────────────────────────────────────┐
│                        协同原则                                   │
├─────────────────────────────────────────────────────────────────┤
│  1. 本地：开发调试 + 本地LLM推理（利用GPU）                       │
│  2. 国内服务器：数据存储 + 业务API + 用户服务（低延迟给国内用户）  │
│  3. 国外服务器：AI Gateway + 海外API调用（突破网络限制）          │
│                                                                 │
│  通信方式: HTTP/WebSocket API 调用                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📐 架构全景图

```
                    用户请求流程
                        │
                        ▼
    ┌───────────────────────────────────────────────────────────┐
    │                         用户层                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
    │  │  Web前端     │  │  移动App     │  │  API调用者   │    │
    │  │  (Next.js)  │  │  (Flutter)   │  │  (开发者)    │    │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
    └─────────┼─────────────────┼─────────────────┼────────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
    ┌───────────────────────────────────────────────────────────┐
    │                    国内服务器 (112.126.61.223)            │
    │                    角色：业务中心 + 数据中心               │
    ├───────────────────────────────────────────────────────────┤
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │           API Gateway / 负载均衡                     │  │
    │  │           Nginx (端口 80/443)                       │  │
    │  └────────────────────┬────────────────────────────────┘  │
    │                       │                                   │
    │         ┌─────────────┼─────────────┐                     │
    │         ▼             ▼             ▼                     │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
    │  │Next.js   │  │PostgreSQL│  │  Redis   │                │
    │  │API服务   │  │  数据库   │  │  缓存    │                │
    │  │(端口6001)│  │(端口15432)│  │(端口6379)│                │
    │  └────┬─────┘  └──────────┘  └──────────┘                │
    │       │                                                     │
    │       │ 1. 接收用户请求                                      │
    │       │ 2. 查询本地缓存/数据库                               │
    │       │ 3. 如果需要AI推理 → 转发                             │
    │       │                                                     │
    └───────┼─────────────────────────────────────────────────────┘
            │
    ┌───────┼─────────────────────────────────────────────────────┐
    │       │            通信层 (HTTPS/WebSocket)                 │
    │       ▼                                                     │
    │  ┌──────────────────────────────────────────────────┐     │
    │  │     场景1：需要AI推理 → 调用本地或国外            │     │
    │  │     场景2：简单查询 → 直接返回                     │     │
    │  └──────────────────────────────────────────────────┘     │
    └───────┼─────────────────────────────────────────────────────┘
            │
      ┌─────┴─────┐
      ▼           ▼
┌─────────┐  ┌─────────────────────────────────────────────────┐
│ 本地    │  │              国外服务器                          │
│ 笔记本  │  │              角色：AI推理中心                    │
├─────────┤  ├─────────────────────────────────────────────────┤
│ 角色：  │  │  ┌───────────────────────────────────────────┐  │
│ 开发+  │  │  │      OpenClaw Gateway                      │  │
│ 本地LLM│  │  │      (端口 18789)                          │  │
├─────────┤  │  └────────────────────┬──────────────────────┘  │
│ 1.     │  │                       │                          │
│Ollama  │  │         ┌─────────────┼─────────────┐            │
│(本地LLM)│  │         ▼             ▼             ▼            │
│ 2.     │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│Jupyter │  │  │多智能体  │  │海外LLM  │  │AutoGen   │       │
│调试    │  │  │工作流    │  │API调用   │  │CrewAI    │       │
│ 3.     │  │  └──────────┘  └──────────┘  └──────────┘       │
│开发工具│  │                                                    │
└─────────┘  │  1. 接收国内服务器的AI推理请求                     │
             │  2. 执行多智能体协作工作流                          │
             │  3. 调用海外API（OpenAI等）                        │
             │  4. 返回推理结果                                   │
             └────────────────────────────────────────────────────┘
```

---

## 🔄 实际请求流程示例

### 示例1：简单查询（不需要AI）

```mermaid
用户 → 国内服务器 → PostgreSQL → 返回结果
```

**代码流程**：

```javascript
// 国内服务器 (Next.js API)
// 文件: /var/www/miaoying/src/app/api/query/route.ts

export async function GET(request: Request) {
  const { query } = await request.json();

  // 1. 检查缓存
  const cached = await redis.get(`query:${query}`);
  if (cached) {
    return Response.json(cached); // 直接返回，不调用AI
  }

  // 2. 查询数据库
  const result = await postgres.query(`
    SELECT * FROM flights WHERE flight_no = $1
  `, [query]);

  // 3. 缓存结果
  await redis.setex(`query:${query}`, 3600, JSON.stringify(result));

  // 4. 返回结果
  return Response.json(result);
}
```

---

### 示例2：AI推理（本地LLM）

```mermaid
用户 → 国内服务器 → 本地笔记本(Ollama) → 返回结果
```

**代码流程**：

```javascript
// 国内服务器 (Next.js API)
// 文件: /var/www/miaoying/src/app/api/ai/local/route.ts

export async function POST(request: Request) {
  const { query } = await request.json();

  // 调用本地笔记本的Ollama服务
  const response = await fetch('http://本地IP:11434/api/generate', {
    method: 'POST',
    body: JSON.stringify({
      model: 'llama3.2',
      prompt: query,
      stream: false
    })
  });

  const result = await response.json();
  return Response.json(result);
}
```

```python
# 本地笔记本 (Ollama服务)
# Ollama自动监听 11434 端口
# 无需额外代码，Ollama自动处理推理请求
```

---

### 示例3：复杂多智能体协作

```mermaid
用户 → 国内服务器 → 国外服务器(OpenClaw) → 多智能体工作流 → 返回结果
```

**代码流程**：

```javascript
// 国内服务器 (Next.js API)
// 文件: /var/www/miaoying/src/app/api/ai/complex/route.ts

export async function POST(request: Request) {
  const { task, agents } = await request.json();

  // 转发给国外服务器的OpenClaw Gateway
  const response = await fetch('http://国外服务器IP:18789/v1/agent/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_GATEWAY_TOKEN'
    },
    body: JSON.stringify({
      task: task,
      agents: agents,
      workflow: 'collaboration'
    })
  });

  const result = await response.json();
  return Response.json(result);
}
```

```python
# 国外服务器 (OpenClaw Gateway)
# 文件: OpenClaw Agent配置

# Agent接收到请求后，启动多智能体协作
# 1. Researcher Agent → 搜索信息
# 2. Analyst Agent → 分析数据
# 3. Writer Agent → 生成报告
# 4. 返回结果给国内服务器
```

---

## 🔌 通信接口定义

### 1. 国内服务器 → 本地笔记本

```yaml
# 场景：需要使用本地GPU加速LLM推理
接口: http://本地IP:11434/api/generate
方法: POST
认证: 无（内网信任）
用途: 简单问答、代码生成、文本摘要
延迟: ~100-500ms
```

**调用示例**：

```bash
# 从国内服务器调用本地Ollama
curl -X POST http://192.168.1.100:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "prompt": "解释什么是向量数据库",
    "stream": false
  }'
```

### 2. 国内服务器 → 国外服务器

```yaml
# 场景：复杂多智能体协作、需要调用海外API
接口: http://国外IP:18789/v1/agent/run
方法: POST
认证: Bearer Token
用途: 多智能体协作、海外LLM调用
延迟: ~1-5秒
```

**调用示例**：

```bash
# 从国内服务器调用国外OpenClaw
curl -X POST http://xx.xx.xx.xx:18789/v1/agent/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "研究并生成一份AI发展报告",
    "agents": ["researcher", "analyst", "writer"],
    "max_turns": 10
  }'
```

### 3. 国外服务器 → 海外API

```yaml
# 场景：调用OpenAI、Claude等海外服务
接口: https://api.openai.com/v1/chat/completions
方法: POST
认证: API Key
用途: 高质量推理、复杂任务
延迟: ~2-10秒
```

---

## 🎛️ 路由决策逻辑

```javascript
// 国内服务器 - 智能路由决策
// 文件: /var/www/miaoying/src/lib/ai-router.ts

interface AIRequest {
  query: string;
  complexity: 'simple' | 'medium' | 'complex';
  requiresOverseasAPI: boolean;
}

async function routeAIRequest(request: AIRequest) {
  // 决策树
  if (request.complexity === 'simple') {
    // 1. 简单查询 → 本地Ollama（免费、快速）
    return await callLocalOllama(request.query);
  }

  if (request.complexity === 'medium' && !request.requiresOverseasAPI) {
    // 2. 中等复杂 → 国内DeepSeek API（便宜）
    return await callDeepSeekAPI(request.query);
  }

  if (request.complexity === 'complex') {
    // 3. 高复杂度 → 国外OpenClaw多智能体（高质量）
    return await callOverseasOpenClaw(request);
  }

  // 4. 需要海外API → 国外服务器代理调用
  if (request.requiresOverseasAPI) {
    return await callOverseasProxy(request);
  }
}

// 成本对比
const COSTS = {
  localOllama: '0元',      // 本地GPU
  deepSeek: '0.001元/1K tokens',   // 国内便宜
  openClawMultiAgent: '0.01-0.1元/次', // 多智能体协作
  openaiGPT4: '0.1元/1K tokens'      // 最贵
};
```

---

## 🌐 网络配置

### 本地笔记本

```bash
# config.yaml
local:
  ollama:
    host: "0.0.0.0"  # 允许外网访问
    port: 11434
    gpu: true        # 启用RTX 4060加速

  # 开发环境
  jupyter:
    port: 8888
    tunnel: true     # 可选：ngrok穿透

  # 内网穿透（如果需要从外网访问）
  frpc:
    enabled: false
    server: "your-frp-server"
```

### 国内服务器

```nginx
# /etc/nginx/nginx.conf
upstream local_ollama {
    server 笔记本内网IP:11434;
}

upstream overseas_openclaw {
    server 国外服务器IP:18789;
}

server {
    listen 80;
    server_name ai.yourdomain.com;

    # 简单查询 → 本地Ollama
    location /api/ai/local {
        proxy_pass http://local_ollama;
    }

    # 复杂任务 → 国外OpenClaw
    location /api/ai/complex {
        proxy_pass http://overseas_openclaw;
        proxy_set_header Authorization "Bearer YOUR_TOKEN";
    }
}
```

### 国外服务器

```yaml
# OpenClaw Gateway配置
openclaw:
  gateway:
    port: 18789
    bind: "0.0.0.0"  # 允许外网访问
    token: "YOUR_GATEWAY_TOKEN"

  agents:
    - name: researcher
      model: "gpt-4o-mini"
    - name: analyst
      model: "gpt-4o"
    - name: writer
      model: "gpt-4o"

  # 海外API配置
  apis:
    openai:
      api_key: "${OPENAI_API_KEY}"
      base_url: "https://api.openai.com/v1"
```

---

## 🔒 安全通信

### API网关认证

```javascript
// JWT Token验证中间件
// 国内服务器

import jwt from 'jsonwebtoken';

export function verifyAuth(req: Request) {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    throw new Error('Unauthorized');
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (error) {
    throw new Error('Invalid token');
  }
}

// 使用示例
export async function POST(req: Request) {
  const user = verifyAuth(req);

  // 处理请求...
}
```

### 服务器间通信加密

```yaml
# mTLS配置（可选，用于服务器间通信）
mtls:
  enabled: true
  cert_file: "/etc/ssl/certs/client.crt"
  key_file: "/etc/ssl/private/client.key"
  ca_file: "/etc/ssl/certs/ca.crt"
```

---

## 📊 实际工作流程

### 开发流程（开发者视角）

```bash
# 1. 本地开发
笔:
├── 启动Ollama服务 (ollama serve)
├── 启动Jupyter调试
└── 编写Agent代码

# 2. 提交到Git
git add .
git commit -m "feat: 新增xxx Agent"
git push origin master

# 3. 部署到国内服务器
# (自动或手动触发)
cd /var/www/miaoying
git pull origin master
npm run build
pm2 restart miaoying

# 4. 更新国外服务器（如需要）
ssh 国外服务器
cd /path/to/openclaw
git pull origin master
# 重启OpenClaw Gateway
```

### 运行流程（用户请求视角）

```bash
# 用户: "帮我分析一下今天的航班数据并生成报告"

# 1. 请求到达国内服务器
POST /api/ai/analyze
{
  "query": "分析今天的航班数据",
  "data": {...}
}

# 2. 国内服务器决策
# - 需要复杂分析 → 转发国外服务器

# 3. 国外服务器执行
# - Agent1: 数据分析师 → 分析数据
# - Agent2: 报告撰写者 → 生成报告
# - Agent3: 审核员 → 质量检查

# 4. 结果返回
# 国外服务器 → 国内服务器 → 用户
```

---

## 🎯 总结：三地协同的本质

```
┌─────────────────────────────────────────────────────────┐
│                  三地协同 = 专业化分工                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  本地笔记本 = 开发环境 + 免费算力                        │
│  ├─ Ollama: 利用RTX 4060进行免费推理                    │
│  ├─ Jupyter: 交互式调试                                 │
│  └─ Git: 代码管理                                       │
│                                                         │
│  国内服务器 = 用户服务 + 数据中心                        │
│  ├─ Next.js API: 服务用户请求                           │
│  ├─ PostgreSQL: 持久化存储                              │
│  ├─ Redis: 缓存加速                                     │
│  └─ Neo4j/Qdrant: 知识管理                              │
│                                                         │
│  国外服务器 = AI推理中心 + 海外API代理                   │
│  ├─ OpenClaw: 多智能体工作流                            │
│  ├─ 无网络限制: 访问OpenAI/Claude                       │
│  └─ 高性能: 专注AI任务                                  │
│                                                         │
│  通信方式 = RESTful API + WebSocket                     │
│  ├─ HTTP: 标准请求响应                                  │
│  ├─ WebSocket: 实时流式输出                             │
│  └─ 认证: JWT + Bearer Token                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速验证命令

```bash
# 1. 验证本地Ollama
curl http://localhost:11434/api/tags

# 2. 验证国内服务器
curl http://国内IP:6001/api/health

# 3. 验证国外服务器
curl http://国外IP:18789/healthz

# 4. 端到端测试
curl -X POST http://国内IP:6001/api/ai/test \
  -H "Content-Type: application/json" \
  -d '{"query": "hello"}'
```

---

**是否需要我画一个更详细的序列图来展示具体请求流程？**

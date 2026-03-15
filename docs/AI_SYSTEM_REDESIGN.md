# 资源信息对齐 + 重新设计方案

**日期**: 2026-03-13
**目的**: 基于实际资源重新设计多智能体系统架构

---

## 📊 资源盘点（实际配置）

### 本地笔记本（开发环境）

| 组件 | 配置 | 说明 |
|------|------|------|
| **CPU** | i9-14900HX (32核心) | 超强算力 |
| **内存** | 50GB | 充足 |
| **GPU** | RTX 4060 8GB | 可跑本地模型 |
| **用途** | 开发调试 + 本地测试 | 不承担生产流量 |

### 国内服务器（阿里云 112.126.61.223）

| 组件 | 配置 | 说明 |
|------|------|------|
| **位置** | 北京（推测） | 国内用户延迟低 |
| **已部署** | Next.js + PostgreSQL + Redis | dandanyi项目 |
| **已部署** | OpenClaw Gateway (18789端口) | 多智能体框架 |
| **用途** | **主要生产服务** | API服务 + 数据存储 + AI推理 |

### 国外服务器

| 组件 | 配置 | 说明 |
|------|------|------|
| **位置** | 海外（具体待确认） | 访问海外API无限制 |
| **已部署** | OpenClaw Gateway | 多智能体框架 |
| **用途** | **辅助服务** | 海外API调用 + 备用 |

### API资源（核心资产）

| API | 状态 | 成本 | 能力 |
|-----|------|------|------|
| **智谱GLM-4** | ✅ 季度套餐 | **几乎无限** | 主力模型 |
| **智联网搜索** | ✅ 已开通 | 0.01元/次 | 实时搜索 |
| **DeepSeek** | ✅ 已充值 | 按量付费 | 简单任务 |
| **本地Ollama** | ✅ 可选 | 免费 | 开发测试 |

---

## 🎯 重新设计的核心原则

基于对齐后的信息，设计原则调整：

```
原原则: "本地免费优先，API兜底"
新原则: "智谱主力，按需分流"

原原则: "三地协同，复杂路由"
新原则: "简化架构，核心在阿里云"
```

---

## 🏗️ 简化后的架构设计

### 核心架构：单中心 + 辅助

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求                                  │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              阿里云服务器（112.126.61.223）核心中心              │
│                      ┌──────────────────────┐                   │
│                      │    API Gateway       │                   │
│                      │   (Next.js/6001)     │                   │
│                      └──────────┬───────────┘                   │
│                                 │                               │
│            ┌────────────────────┼────────────────────┐          │
│            ▼                    ▼                    ▼          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  PostgreSQL    │  │    Redis        │  │  OpenClaw      │  │
│  │  数据存储       │  │    缓存          │  │  Gateway       │  │
│  │  (15432)       │  │    (6379)       │  │  (18789)       │  │
│  └─────────────────┘  └─────────────────┘  └────────┬────────┘  │
│                                                  │             │
│                                    ┌─────────────┼─────────────┐
│                                    ▼             ▼             │
│                         ┌──────────────┐  ┌──────────────┐    │
│                         │  智谱GLM-4   │  │  智联网搜索   │    │
│                         │  (主力)      │  │  (实时信息)   │    │
│                         └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    国外服务器（辅助）                            │
│              ┌─────────────────────────────────┐                │
│              │  1. 备用OpenClaw Gateway         │                │
│              │  2. 海外API调用代理（如需要）     │                │
│              └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    本地笔记本（开发）                            │
│              ┌─────────────────────────────────┐                │
│              │  1. 代码开发                    │                │
│              │  2. 本地调试（Ollama可选）       │                │
│              │  3. Jupyter分析                 │                │
│              └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 智能路由策略（简化版）

### 决策逻辑

```javascript
// 阿里云服务器上的智能路由
async function routeAIRequest(task) {

  // 1. 简单快速任务 → DeepSeek（便宜）
  if (task.complexity === 'low' && task.type === 'chat') {
    return {
      provider: 'deepseek',
      model: 'deepseek-chat',
      reason: '简单问答，使用低成本方案'
    };
  }

  // 2. 需要实时信息 → 智联网搜索
  if (task.needsRealTimeData) {
    return {
      provider: 'zhipu',
      model: 'glm-4',
      tools: ['web_search_prime'],  // 智联网搜索
      reason: '需要最新信息，使用联网搜索'
    };
  }

  // 3. 复杂推理 → 智谱GLM-4（主力，token几乎无限）
  if (task.complexity === 'high') {
    return {
      provider: 'zhipu',
      model: 'glm-4-plus',  // 最强模型
      reason: '复杂任务，使用最强模型'
    };
  }

  // 4. 默认 → 智谱GLM-4（主力）
  return {
    provider: 'zhipu',
    model: 'glm-4',
    reason: '默认使用智谱主力模型'
  };
}
```

### 路由决策表

| 任务类型 | 复杂度 | 需要实时信息 | 使用的方案 | 成本 |
|---------|-------|-------------|-----------|------|
| 简单问答 | 低 | ❌ | DeepSeek | ¥ |
| 新闻查询 | 中 | ✅ | 智谱 + 联网搜索 | ¥ + 0.01元/次 |
| 代码生成 | 高 | ❌ | 智谱GLM-4 | ≈¥0 (套餐) |
| 数据分析 | 高 | ❌ | 智谱GLM-4-Plus | ≈¥0 (套餐) |
| 多智能体协作 | 高 | ❌ | OpenClaw + 智谱 | ≈¥0 (套餐) |

---

## 💰 成本分析（基于新架构）

### 月度成本估算

| 项目 | 成本 | 说明 |
|------|------|------|
| 阿里云服务器 | ~¥200-500/月 | 根据配置 |
| 国外服务器 | ~$10-20/月 | 较低配置即可 |
| 智谱GLM-4 | **¥0** | 季度套餐几乎无限 |
| 智联网搜索 | ¥1-50/月 | 按使用次数（0.01元/次） |
| DeepSeek | ¥10-100/月 | 简单任务分流 |
| **合计** | **¥211-650/月** | 主要是服务器成本 |

### 成本优化策略

```javascript
// 成本优化路由
const costOptimizedRouter = {
  // 免费使用智谱套餐（主力）
  zhipu: {
    budget: 'unlimited',  // 季度套餐
    priority: 1,          // 优先使用
    models: ['glm-4', 'glm-4-plus', 'glm-4-air']
  },

  // 联网搜索按需使用
  webSearch: {
    cost: 0.01,  // 每次搜索
    limit: 1000,  // 每日限制
    skipCache: true  // 缓存命中则不搜索
  },

  // DeepSeek作为补充
  deepseek: {
    cost: 0.001,  // 每1K tokens
    useFor: ['simple-chat', 'quick-response']
  }
};
```

---

## 🗄️ 数据库部署建议

### 阿里云服务器（主力）

```yaml
# docker-compose.yml 添加服务
services:
  # 已有: PostgreSQL + Redis

  # 新增: Neo4j 知识图谱
  neo4j:
    image: neo4j:5-community
    container_name: ai-neo4j
    restart: always
    ports:
      - "7474:7474"  # Web UI
      - "7687:7687"  # Bolt协议
    environment:
      NEO4J_AUTH: neo4j/change_password
      NEO4J_dbms_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
    networks:
      - ai-network

  # 新增: Qdrant 向量数据库
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-qdrant
    restart: always
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - ai-network

  # 新增: 智谱API代理服务
  zhipu-proxy:
    image: your-zhipu-proxy:latest
    container_name: zhipu-proxy
    restart: always
    ports:
      - "5000:5000"
    environment:
      ZHIPU_API_KEY: ${ZHIPU_API_KEY}
      ZHIPU_BASE_URL: https://open.bigmodel.cn/api/paas/v4/
    networks:
      - ai-network

volumes:
  neo4j_data:
  qdrant_data:

networks:
  ai-network:
    driver: bridge
```

---

## 🤖 多智能体系统部署

### 方案选择：OpenClaw（已部署）

既然阿里云和国外服务器都有OpenClaw Gateway，直接利用：

```javascript
// 智谱Agent配置（OpenClaw格式）
// 文件: /root/.openclaw/agents/researcher.json
{
  "name": "researcher",
  "model": {
    "provider": "zhipu",
    "name": "glm-4",
    "api_key": "${ZHIPU_API_KEY}"
  },
  "system_message": "你是一个专业的信息研究员，擅长搜索和分析。",
  "tools": [
    {
      "type": "web_search",
      "name": "web_search_prime",
      "enabled": true
    }
  ]
}

// 文件: /root/.openclaw/agents/analyst.json
{
  "name": "analyst",
  "model": {
    "provider": "zhipu",
    "name": "glm-4-plus"
  },
  "system_message": "你是一个数据分析师，擅长深入分析。"
}

// 文件: /root/.openclaw/teams/research-team.json
{
  "name": "research-team",
  "members": ["researcher", "analyst"],
  "max_turns": 10
}
```

### 调用示例

```javascript
// Next.js API调用
const response = await fetch('http://112.126.61.223:18789/v1/agent/run', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    task: "研究并分析AI行业最新动态",
    team: "research-team",
    tools: {
      web_search_prime: {
        top_k: 10,
        search_type: "pro"  // 使用高级搜索
      }
    }
  })
});
```

---

## 📋 实施步骤（简化版）

### 第一步：阿里云增强（1-2天）

```bash
# 1. SSH到阿里云
ssh root@112.126.61.223

# 2. 部署Neo4j和Qdrant
cd /var/www/miaoying
docker-compose -f docker-compose.ai.yml up -d

# 3. 配置OpenClaw使用智谱
cat > /root/.openclaw/auth-profiles.json << EOF
{
  "profiles": {
    "zhipu": {
      "provider": "zhipu",
      "api_key": "YOUR_ZHIPU_API_KEY",
      "base_url": "https://open.bigmodel.cn/api/paas/v4/"
    }
  }
}
EOF

# 4. 重启OpenClaw
docker restart openclaw-gateway
```

### 第二步：创建智能体（1天）

```bash
# 创建智谱智能体配置
cd /root/.openclaw/agents

# 创建研究员Agent
cat > researcher.json << 'EOF'
{
  "name": "researcher",
  "model": {
    "provider": "zhipu",
    "name": "glm-4"
  },
  "system_message": "你是研究员，擅长搜索和分析信息。",
  "tools": ["web_search_prime"]
}
EOF

# 创建分析师Agent
cat > analyst.json << 'EOF'
{
  "name": "analyst",
  "model": {
    "provider": "zhipu",
    "name": "glm-4-plus"
  },
  "system_message": "你是分析师，擅长深入分析数据。"
}
EOF
```

### 第三步：Next.js集成（2-3天）

```typescript
// /var/www/miaoying/src/lib/ai-client.ts
export class AIClient {
  private zhipuApiKey: string;
  private openclawUrl: string;

  constructor() {
    this.zhipuApiKey = process.env.ZHIPU_API_KEY!;
    this.openclawUrl = 'http://112.126.61.223:18789';
  }

  // 直接调用智谱API
  async callZhipu(messages: Message[], options?: { search?: boolean }) {
    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.zhipuApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'glm-4',
        messages,
        tools: options?.search ? [{
          "type": "web_search",
          "web_search": {
            "enable": true,
            "search_result": true
          }
        }] : undefined
      })
    });
    return response.json();
  }

  // 调用OpenClaw多智能体
  async callOpenClaw(task: string, team: string) {
    const response = await fetch(`${this.openclawUrl}/v1/agent/run`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENCLAW_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ task, team })
    });
    return response.json();
  }

  // 智能路由
  async process(task: string) {
    // 简单任务 → 直接智谱
    if (task.length < 100) {
      return this.callZhipu([{ role: 'user', content: task }]);
    }

    // 复杂任务 → 多智能体
    return this.callOpenClaw(task, 'research-team');
  }
}
```

### 第四步：测试验证（1天）

```bash
# 测试1: 直接智谱API
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4","messages":[{"role":"user","content":"你好"}]}'

# 测试2: 智谱联网搜索
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"glm-4",
    "messages":[{"role":"user","content":"今天北京的天气"}],
    "tools":[{"type":"web_search","web_search":{"enable":true}}]
  }'

# 测试3: OpenClaw多智能体
curl -X POST http://112.126.61.223:18789/v1/agent/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"分析AI行业趋势","team":"research-team"}'
```

---

## 📊 最终架构总结

### 核心变化

```
原方案: 本地Ollama + 国外Ollama + 多层降级
新方案: 智谱主力 + 智联网搜索 + 简单路由

原方案: 三地协同复杂架构
新方案: 阿里云单中心 + 国外备用

原方案: 多个LLM提供商
新方案: 智谱主力（几乎免费） + DeepSeek补充
```

### 优势

| 方面 | 原方案 | 新方案 | 改善 |
|------|--------|--------|------|
| **复杂度** | 高（多层降级） | 低（简单路由） | ✅ 简化70% |
| **成本** | $50-400/月 | ¥211-650/月 | ✅ 可控 |
| **稳定性** | 依赖本地 | 云端运行 | ✅ 7x24 |
| **开发效率** | 需维护多端 | 单中心开发 | ✅ 提升50% |
| **搜索能力** | 无 | 智联网搜索 | ✅ 新增能力 |

---

## ✅ 检查清单

在开始实施前，请确认：

- [ ] 智谱API Key已获取（季度套餐）
- [ ] 智联网搜索已开通
- [ ] DeepSeek API Key已配置
- [ ] 阿里云服务器有足够资源（内存、磁盘）
- [ ] 确认是否需要在阿里云部署Neo4j/Qdrant
- [ ] OpenClaw Token已获取

---

## 🚀 下一步

**请确认以下问题后开始实施**：

1. ✅ 智谱季度套餐的具体限制是什么？（QPM？QPD？）
2. ✅ 智联网搜索的每日/每月配额？
3. ✅ 阿里云服务器配置？（CPU/内存/磁盘）
4. ✅ 是否需要在阿里云部署Neo4j和Qdrant？
5. ✅ 国外服务器的具体配置和用途？

**确认后，我可以立即开始生成部署脚本和配置文件。**

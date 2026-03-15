# 完整资源盘点与最终架构设计

**日期**: 2026-03-14
**状态**: 所有资源信息已对齐

---

## 📊 完整资源盘点

### 三台设备配置对比

| 设备 | CPU | 内存 | 存储 | 网络/带宽 | 位置 | 成本 | 用途 |
|------|-----|------|------|----------|------|------|------|
| **本地笔记本** | i9-14900HX (32核) | 50 GB | - | 本地网络 | 本地 | ¥0 | 开发调试 |
| **阿里云服务器** | 2核 vCPU | 4 GB | 40 GB | 1 Mbps固定，**不限流量** | 国内 | ~¥200/月 | 生产服务 |
| **马来西亚服务器** | 1核 vCPU | 2 GB | 25 GB | 高带宽，**2TB/月限制** | 海外 | $12/月 | 辅助服务 |

**网络对比**：
- **阿里云**：1Mbps固定带宽 = 128KB/s，但24小时可用，不限总量
  - 每天最大传输：1Mbps × 86400秒 ≈ 10.8GB/天
  - 每月最大传输：10.8GB × 30 ≈ 324GB/月
  - **优势**：稳定、不限量、适合持续低带宽服务

- **马来西亚**：高带宽（推测100Mbps+），但总量限制2TB/月
  - 超出流量：另计费
  - **优势**：瞬时带宽高，适合突发大流量

### API资源

| 资源类型 | 规格 | 成本 | 有效期 |
|---------|------|------|--------|
| **智谱GLM-4 Max套餐** | 1600次/5小时, 8000次/周 | 季度套餐 | 季度 |
| **搜索资源包** | 9954次 (价值¥249) | 已购买 | 2026-09-12 |
| **DeepSeek充值** | 按量付费 | 已充值 | - |

---

## 🎯 最终架构设计

### 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│                    架构设计三原则                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ 量力而行：根据配置分配任务                              │
│     - 阿里云(4GB): 承担主要业务服务                         │
│     - 马来西亚(2GB): 承担轻量辅助服务                       │
│     - 本地(50GB): 开发调试 + 本地LLM                       │
│                                                             │
│  2️⃣ 扬长避短：发挥各自优势                                  │
│     - 阿里云: 国内延迟低，服务国内用户                      │
│     - 马来西亚: 海外网络好，访问海外API                     │
│     - 本地: 算力强，跑本地模型                              │
│                                                             │
│  3️⃣ 成本优先：充分利用现有资源                              │
│     - 智谱Max套餐: 几乎无限的token                         │
│     - 搜索资源包: 9954次搜索额度                            │
│     - 本地Ollama: 完全免费                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 最终架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户请求                                │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              阿里云服务器 (112.126.61.223) - 核心中心            │
│                      配置: 2核4GB, 1Mbps                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Next.js API Gateway (端口 6001)                │  │
│  │            - 用户认证                                     │  │
│  │            - 请求路由                                     │  │
│  │            - 业务逻辑                                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         ▼                 ▼                 ▼                  │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐           │
│  │ PostgreSQL │    │   Redis    │    │ OpenClaw   │           │
│  │ (端口15432)│    │ (端口6379) │    │ Gateway    │           │
│  │            │    │            │    │ (端口18789)│           │
│  │ ✅ 已部署  │    │ ✅ 已部署  │    │ ✅ 已部署  │           │
│  └────────────┘    └────────────┘    └────────────┘           │
│                                                                 │
│  内存分配:                                                      │
│  ├─ 系统: 800MB                                                │
│  ├─ PostgreSQL: 1GB (限制)                                     │
│  ├─ Redis: 256MB (限制)                                        │
│  ├─ Next.js: 300MB                                             │
│  ├─ OpenClaw: 1GB (限制)                                       │
│  └─ 剩余: ~644MB                                               │
│                                                                 │
│  ❌ 不部署: Neo4j, Qdrant (内存不足)                            │
│  ✅ 替代方案: SQLite + Redis向量缓存                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 需要海外API
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│         马来西亚服务器 (157.245.195.58) - 海外代理               │
│                     配置: 1核2GB, 2TB流量                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            API Proxy Service (端口 8080)                  │  │
│  │            - 转发海外API请求                              │  │
│  │            - OpenAI API调用                               │  │
│  │            - Claude API调用                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            OpenClaw Gateway (端口 18789)                  │  │
│  │            - 多智能体协作                                 │  │
│  │            - 复杂工作流                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  内存分配:                                                      │
│  ├─ 系统: 500MB                                                │
│  ├─ API Proxy: 300MB                                           │
│  ├─ OpenClaw: 800MB (限制)                                     │
│  └─ 剩余: ~400MB                                               │
│                                                                 │
│  ❌ 不部署: PostgreSQL, Redis, Neo4j (内存不足)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 本地开发调试
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    本地笔记本 - 开发环境                         │
│                 配置: i9-14900HX, 50GB, RTX 4060                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Ollama (端口 11434)                            │  │
│  │            - 本地LLM推理                                  │  │
│  │            - 免费，利用RTX 4060                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            开发工具                                       │  │
│  │            - VS Code                                      │  │
│  │            - Jupyter Notebook                             │  │
│  │            - Git                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ❌ 不承担: 生产流量                                            │
│  ✅ 用途: 开发调试 + 本地测试                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 数据流与路由策略

### 用户请求处理流程

```javascript
// 阿里云Next.js API路由
async function handleUserRequest(request) {
  const { query, needsRealtime, complexity } = request;

  // 1. 简单查询 → 本地数据库
  if (isSimpleQuery(query)) {
    return await queryLocalDatabase(query);
  }

  // 2. 需要联网搜索 → 智谱API（直接调用）
  if (needsRealtime) {
    return await callZhipuWithSearch(query);
  }

  // 3. 复杂推理 → 智谱GLM-4-Plus
  if (complexity === 'high') {
    return await callZhipuGLM4Plus(query);
  }

  // 4. 需要海外API → 转发马来西亚
  if (needsOverseasAPI(query)) {
    return await callMalaysiaProxy(query);
  }

  // 5. 多智能体协作 → OpenClaw（阿里云本地）
  if (needsMultiAgent(query)) {
    return await callOpenClawLocal(query);
  }

  // 6. 默认 → 智谱GLM-4
  return await callZhipuGLM4(query);
}
```

### 智能路由决策表

| 请求类型 | 复杂度 | 实时性 | 路由目标 | 理由 |
|---------|-------|--------|---------|------|
| 简单查询 | 低 | ❌ | PostgreSQL（阿里云） | 本地查询最快 |
| 需要搜索 | 中 | ✅ | 智谱+搜索（直连） | Max套餐配额充足 |
| 复杂推理 | 高 | ❌ | 智谱GLM-4-Plus | 最强模型 |
| 需要海外API | - | - | 马来西亚代理 | 突破网络限制 |
| 多智能体 | 高 | ❌ | OpenClaw（阿里云） | 已部署，可用 |
| 代码生成 | 中 | ❌ | CodeGeeX-4 | 专业模型 |
| **大文件传输** | - | - | **马来西亚** | **高带宽，快** |
| **持续API服务** | - | - | **阿里云** | **不限流量** |

### 网络流量策略

```javascript
// 基于正确的带宽理解
const NETWORK_STRATEGY = {
  // 阿里云：1Mbps固定，不限流量
  aliyun: {
    bandwidth: '1 Mbps (128 KB/s)',
    monthlyLimit: 'unlimited',
    suitableFor: [
      '持续API服务',      // 稳定
      '数据库查询',       // 低带宽
      '小文件传输',       // <10MB
      '实时通信'          // WebSocket
    ],
    avoid: [
      '大文件传输',       // 太慢
      '批量数据同步'     // 太慢
    ]
  },

  // 马来西亚：高带宽，2TB/月限制
  malaysia: {
    bandwidth: '~100 Mbps (推测)',
    monthlyLimit: '2 TB',
    suitableFor: [
      '大文件传输',       // 高带宽，快
      '海外API调用',     // 低延迟
      '批量数据同步',    // 高带宽
      '模型下载'         // 大文件
    ],
    avoid: [
      '持续低流量服务',   // 浪费流量配额
      '24小时监控'       // 累计流量
    ],
    monitoring: {
      alert: '1.8 TB',    // 90%告警
      critical: '1.9 TB'  // 95%严重告警
    }
  }
};

// 路由示例
function routeByDataSize(size) {
  // <10MB → 阿里云（不限流量）
  if (size < 10 * 1024 * 1024) {
    return 'aliyun';
  }

  // 10MB-100MB → 马来西亚（快）
  if (size < 100 * 1024 * 1024) {
    return 'malaysia';
  }

  // >100MB → 马来西亚 + 流量检查
  return checkMalaysiaTraffic()
    .then(traffic => {
      if (traffic > 1.8 * 1024 * 1024 * 1024 * 1024) {  // 1.8TB
        console.warn('马来西亚流量即将用完，降级到阿里云');
        return 'aliyun';  // 降级
      }
      return 'malaysia';
    });
}
```

---

## 💰 成本分析

### 月度成本估算

```
┌─────────────────────────────────────────────────────────────┐
│                     月度成本明细                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  服务器成本:                                                │
│  ├─ 阿里云: ~¥200/月 (2核4GB)                              │
│  ├─ 马来西亚: $12/月 ≈ ¥85/月                              │
│  └─ 小计: ¥285/月                                          │
│                                                             │
│  API成本:                                                   │
│  ├─ 智谱Max套餐: ¥0 (已付费季度)                           │
│  ├─ 搜索资源包: ¥0 (已购买9954次)                          │
│  ├─ DeepSeek: ¥50-100/月 (按需补充)                        │
│  └─ 小计: ¥50-100/月                                       │
│                                                             │
│  总计: ¥335-385/月                                         │
│                                                             │
│  优化后可降至: ¥285/月 (仅服务器成本)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 成本优化策略

```javascript
// 成本优化路由
const COST_OPTIMIZATION = {
  // 1. 优先使用免费的
  priority: [
    '本地Ollama',           // 免费
    '智谱Max套餐',          // 已付费
    '搜索资源包',           // 已购买
    'DeepSeek',             // 便宜
    '海外API'               // 最贵，最后用
  ],

  // 2. 缓存策略
  cache: {
    static: 86400,      // 静态内容缓存24小时
    dynamic: 3600,      // 动态内容缓存1小时
    realtime: 300       // 实时内容缓存5分钟
  },

  // 3. 降级策略
  fallback: {
    searchQuotaLow: '关闭搜索，使用模型知识',
    maxPlanQuotaLow: '使用DeepSeek',
    overseasAPIFailed: '使用国内API替代'
  }
};
```

---

## 🚀 部署步骤

### 第一阶段：阿里云服务器优化（1-2天）

```bash
# 1. SSH到阿里云
ssh root@112.126.61.223

# 2. 检查现有服务
docker ps
free -h
df -h

# 3. 优化Docker配置（添加内存限制）
cd /var/www/miaoying
vim docker-compose.yml

# 添加内存限制
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 1G

  redis:
    deploy:
      resources:
        limits:
          memory: 256M

  openclaw-gateway:
    deploy:
      resources:
        limits:
          memory: 1G

# 4. 重启服务
docker-compose down
docker-compose up -d

# 5. 部署轻量级知识存储
apt-get install sqlite3
cd /var/www/miaoying
sqlite3 data/knowledge.db < scripts/init_knowledge.sql

# 6. 配置智谱API
vim .env.local
# 添加:
# ZHIPU_API_KEY=your_key
# ZHIPU_SEARCH_BALANCE_STD=4962
# ZHIPU_SEARCH_BALANCE_PRO=2492
# ZHIPU_SEARCH_BALANCE_QUARK=2500
```

### 第二阶段：马来西亚服务器配置（1天）

```bash
# 1. SSH到马来西亚
ssh root@157.245.195.58

# 2. 安装Docker
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker

# 3. ⚠️ 安装流量监控工具（重要！）
apt-get update
apt-get install -y vnstat iftop

# 配置vnstat
vnstat --add -i eth0
systemctl start vnstat
systemctl enable vnstat

# 查看实时流量
vnstat -l

# 4. 部署API代理服务
mkdir -p /opt/api-proxy
cd /opt/api-proxy

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api-proxy:
    image: nginx:alpine
    container_name: api-proxy
    restart: always
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    deploy:
      resources:
        limits:
          memory: 300M

  openclaw-gateway:
    image: ${OPENCLAW_IMAGE:-openclaw:local}
    container_name: openclaw-gateway
    restart: always
    ports:
      - "18789:18789"
    environment:
      OPENCLAW_GATEWAY_TOKEN: ${OPENCLAW_GATEWAY_TOKEN}
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw
    deploy:
      resources:
        limits:
          memory: 800M

  # 流量监控服务
  traffic-monitor:
    image: python:3.11-slim
    container_name: traffic-monitor
    restart: always
    volumes:
      - ./monitor.py:/app/monitor.py
    command: python /app/monitor.py
    environment:
      ALERT_THRESHOLD: 1800000000000  # 1.8TB (bytes)
      CRITICAL_THRESHOLD: 1900000000000  # 1.9TB
    deploy:
      resources:
        limits:
          memory: 100M
EOF

# 5. 配置Nginx代理
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream openai {
        server api.openai.com:443;
    }

    upstream anthropic {
        server api.anthropic.com:443;
    }

    server {
        listen 80;

        location /v1/openai/ {
            proxy_pass https://openai/;
            proxy_ssl_server_name on;
            proxy_set_header Host api.openai.com;
            proxy_set_header Authorization $http_authorization;
        }

        location /v1/anthropic/ {
            proxy_pass https://anthropic/;
            proxy_ssl_server_name on;
            proxy_set_header Host api.anthropic.com;
            proxy_set_header X-Api-Key $http_x_api_key;
        }
    }
}
EOF

# 6. 创建流量监控脚本
cat > monitor.py << 'EOF'
import requests
import time
import os

def get_traffic():
    """从DigitalOcean API获取流量使用"""
    # 需要配置DO_API_TOKEN
    api_token = os.getenv('DO_API_TOKEN')
    droplet_id = os.getenv('DROPLET_ID')

    response = requests.get(
        f'https://api.digitalocean.com/v2/monitoring/droplets/{droplet_id}/bandwidth',
        headers={'Authorization': f'Bearer {api_token}'}
    )

    data = response.json()
    # 解析带宽使用情况
    return data

def check_and_alert():
    """检查流量并发送告警"""
    while True:
        traffic = get_traffic()
        used = traffic.get('outbound_bytes', 0)

        alert_threshold = int(os.getenv('ALERT_THRESHOLD', 1800000000000))
        critical_threshold = int(os.getenv('CRITICAL_THRESHOLD', 1900000000000))

        if used > critical_threshold:
            send_alert('CRITICAL', f'流量已使用 {used/1e12:.2f}TB，即将超出2TB限制')
        elif used > alert_threshold:
            send_alert('WARNING', f'流量已使用 {used/1e12:.2f}TB，达到90%')

        time.sleep(3600)  # 每小时检查一次

def send_alert(level, message):
    """发送告警（可接入企业微信/钉钉）"""
    print(f'[{level}] {message}')
    # TODO: 接入实际告警系统

if __name__ == '__main__':
    check_and_alert()
EOF

# 7. 启动服务
docker-compose up -d

# 8. 配置防火墙
ufw allow 8080
ufw allow 18789
```

### 第三阶段：本地环境配置（1天）

```bash
# 1. 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. 下载模型
ollama pull llama3.2
ollama pull deepseek-coder
ollama pull nomic-embed-text

# 3. 启动Ollama服务
ollama serve &

# 4. 验证
curl http://localhost:11434/api/tags

# 5. 配置Jupyter（可选）
pip install jupyter
jupyter notebook --generate-config
jupyter notebook password
jupyter notebook --ip=0.0.0.0 --port=8888 &
```

### 第四阶段：集成测试（1天）

```bash
# 1. 测试阿里云服务
curl http://112.126.61.223:6001/api/health
curl http://112.126.61.223:18789/healthz

# 2. 测试马来西亚代理
curl http://157.245.195.58:8080/v1/openai/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"

# 3. 测试本地Ollama
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2", "prompt": "hello"}'

# 4. 端到端测试
# 用户请求 → 阿里云 → 智谱API
curl -X POST http://112.126.61.223:6001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

---

## 📊 性能预估

### 并发能力

```
阿里云服务器:
├─ CPU: 2核 → ~50 QPS (实际)
├─ 内存: 4GB → ~50人同时在线
├─ 带宽: 1Mbps → ~10并发请求
└─ 推荐: 30 QPS, 30人同时在线

马来西亚服务器:
├─ CPU: 1核 → ~20 QPS
├─ 内存: 2GB → ~20人同时在线
├─ 带宽: 2TB/月 → 充足
└─ 推荐: 15 QPS, 15人同时在线
```

### 响应时间

```
简单查询:
├─ PostgreSQL: 50-200ms
├─ Redis缓存: <10ms
└─ 总计: 50-200ms

智谱API:
├─ 网络延迟: 50-100ms (国内)
├─ 模型推理: 500-2000ms
└─ 总计: 0.5-2秒

联网搜索:
├─ 搜索时间: 1-2秒
├─ 模型推理: 500-1000ms
└─ 总计: 1.5-3秒

海外API (通过马来西亚):
├─ 阿里云→马来西亚: 100-200ms
├─ 马来西亚→海外: 50-100ms
├─ 模型推理: 1-3秒
└─ 总计: 1.5-4秒
```

### 马来西亚流量管理

```
2TB/月流量分配策略:

1. 基础服务 (200GB/月)
   ├─ OpenClaw Gateway: ~50GB
   ├─ API代理: ~100GB
   └─ 监控和日志: ~50GB

2. 大文件传输 (800GB/月)
   ├─ 模型下载: ~300GB
   ├─ 数据同步: ~300GB
   └─ 用户文件: ~200GB

3. 海外API调用 (800GB/月)
   ├─ OpenAI API: ~400GB
   ├─ Claude API: ~200GB
   └─ 其他API: ~200GB

4. 备用缓冲 (200GB/月)
   └─ 突发流量缓冲

告警策略:
├─ 1.6TB (80%): 警告
├─ 1.8TB (90%): 严重警告，开始限流
└─ 1.9TB (95%): 紧急，只允许关键服务

降级策略:
├─ >1.8TB: 大文件传输暂停
├─ >1.9TB: 海外API调用限流
└─ >2.0TB: 仅保留OpenClaw Gateway
```

---

## ✅ 最终检查清单

### 阿里云服务器 (112.126.61.223)

- [ ] ✅ PostgreSQL已部署，内存限制1GB
- [ ] ✅ Redis已部署，内存限制256MB
- [ ] ✅ Next.js API已部署
- [ ] ✅ OpenClaw Gateway已部署，内存限制1GB
- [ ] ❌ Neo4j不部署（内存不足）
- [ ] ❌ Qdrant不部署（内存不足）
- [ ] ✅ SQLite轻量级知识图谱
- [ ] ✅ Redis向量缓存
- [ ] ✅ 智谱API集成
- [ ] ✅ 搜索资源包管理

### 马来西亚服务器 (157.245.195.58)

- [ ] ✅ API代理服务 (端口8080)
- [ ] ✅ OpenClaw Gateway (端口18789)
- [ ] ❌ PostgreSQL不部署（内存不足）
- [ ] ❌ Redis不部署（内存不足）
- [ ] ✅ Nginx代理配置
- [ ] ✅ 防火墙配置

### 本地笔记本

- [ ] ✅ Ollama服务 (端口11434)
- [ ] ✅ 开发环境 (VS Code, Git)
- [ ] ✅ Jupyter Notebook
- [ ] ❌ 不承担生产流量

---

## 🎯 总结

### 最终架构

```
┌─────────────────────────────────────────────────────────────┐
│                    三地协同最终方案                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阿里云 (2核4GB): 生产中心                                  │
│  ├─ 核心业务服务                                            │
│  ├─ 数据存储 (PostgreSQL + Redis)                          │
│  ├─ AI服务 (OpenClaw + 智谱API)                            │
│  └─ 轻量级知识存储 (SQLite + Redis)                        │
│                                                             │
│  马来西亚 (1核2GB): 海外代理                                │
│  ├─ API代理 (OpenAI/Claude)                                │
│  ├─ 多智能体协作 (OpenClaw备用)                            │
│  └─ 海外资源访问                                            │
│                                                             │
│  本地笔记本: 开发环境                                       │
│  ├─ 本地LLM (Ollama + RTX 4060)                           │
│  ├─ 代码开发                                                │
│  └─ 调试测试                                                │
│                                                             │
│  核心优势:                                                  │
│  ✅ 充分利用现有资源                                        │
│  ✅ 成本可控 (¥285-385/月)                                 │
│  ✅ 智谱Max套餐几乎无限                                    │
│  ✅ 搜索资源包充足 (9954次)                                │
│  ✅ 三地互补，避免单点故障                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 关键决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **Neo4j部署** | ❌ 不部署 | 内存不足(4GB)，改用SQLite |
| **Qdrant部署** | ❌ 不部署 | 内存不足(4GB)，改用Redis |
| **Ollama部署** | ❌ 不部署 | 配置不足，仅本地使用 |
| **马来西亚用途** | API代理+大文件 | 高带宽（2TB/月）优势 |
| **大文件路由** | → 马来西亚 | 高带宽快，但需监控流量 |
| **持续API服务** | → 阿里云 | 1Mbps不限流量，稳定 |
| **成本控制** | 优先用免费资源 | Max套餐+搜索包+本地Ollama |

### 带宽使用策略总结

```
┌─────────────────────────────────────────────────────────────┐
│                    带宽策略对比                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阿里云 (1Mbps固定，不限流量):                              │
│  ✅ 适合:                                                   │
│     - 持续API服务 (24小时运行)                             │
│     - 数据库查询 (小数据包)                                │
│     - WebSocket连接 (持续低带宽)                           │
│     - 小文件传输 (<10MB)                                   │
│                                                             │
│  ❌ 不适合:                                                 │
│     - 大文件传输 (10MB需要~80秒)                           │
│     - 批量数据同步 (太慢)                                  │
│                                                             │
│  马来西亚 (高带宽，2TB/月限制):                             │
│  ✅ 适合:                                                   │
│     - 大文件传输 (100MB只需~10秒)                          │
│     - 海外API调用 (低延迟)                                 │
│     - 模型下载 (大文件)                                    │
│     - 批量数据同步 (高带宽)                                │
│                                                             │
│  ❌ 不适合:                                                 │
│     - 持续低流量服务 (浪费流量配额)                        │
│     - 24小时监控 (累计流量快)                              │
│                                                             │
│  智能路由策略:                                              │
│     小文件 (<10MB) → 阿里云 (不限流量)                     │
│     大文件 (>10MB) → 马来西亚 (快，但需监控流量)           │
│     海外API → 马来西亚 (低延迟)                            │
│     持续服务 → 阿里云 (稳定不限量)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**架构设计完成！准备开始实施？**

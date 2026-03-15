# 阿里云服务器配置分析与部署建议

**日期**: 2026-03-14
**服务器**: 阿里云 112.126.61.223

---

## 📊 服务器配置详情

### 基础配置

| 配置项 | 规格 | 说明 |
|--------|------|------|
| **实例规格** | ecs.e-c1m2.large | 入门级实例 |
| **CPU** | 2核 vCPU | 有限并发能力 |
| **内存** | 4 GiB | **紧张** ⚠️ |
| **公网IP** | 112.126.61.223 | 固定IP |
| **私网IP** | 172.26.136.204 | 内网通信 |
| **带宽** | 1 Mbps | **慢** ⚠️ |
| **系统盘** | 40 GiB ESSD Entry | 空间有限 |
| **操作系统** | Ubuntu 22.04 64位 | ✅ 稳定 |
| **付费类型** | 包年包月 | 已付至2026-07-13 |
| **到期时间** | 2026年7月13日 | ~121天 |

### 配置评估

```
┌─────────────────────────────────────────────────────────────┐
│                    阿里云服务器评估                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CPU: 2核 vCPU                                              │
│  ├─ 评分: 🟡 中等                                           │
│  ├─ 影响: 并发处理能力有限                                  │
│  └─ 建议: 控制同时运行的容器数量 ≤ 5                        │
│                                                             │
│  内存: 4 GiB                                                │
│  ├─ 评分: 🔴 紧张                                           │
│  ├─ 影响: 多个Docker容器可能内存不足                        │
│  └─ 建议: 精简部署，避免内存密集型服务                      │
│                                                             │
│  带宽: 1 Mbps = 128 KB/s                                    │
│  ├─ 评分: 🔴 慢                                             │
│  ├─ 影响: 数据传输慢，API响应可能延迟                       │
│  └─ 建议: 大文件传输考虑CDN，API使用压缩                    │
│                                                             │
│  磁盘: 40 GiB                                               │
│  ├─ 评分: 🟡 有限                                           │
│  ├─ 影响: 数据库和日志空间有限                              │
│  └─ 建议: 定期清理日志，监控磁盘使用                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 部署策略调整

### 原方案 vs 实际配置

| 服务 | 原计划 | 实际可行性 | 调整方案 |
|------|--------|-----------|---------|
| **PostgreSQL** | ✅ 部署 | ✅ 可行 | 保留（已部署） |
| **Redis** | ✅ 部署 | ✅ 可行 | 保留（已部署） |
| **Next.js API** | ✅ 部署 | ✅ 可行 | 保留（已部署） |
| **OpenClaw Gateway** | ✅ 部署 | ✅ 可行 | 保留（已部署） |
| **Neo4j** | ✅ 部署 | ⚠️ 紧张 | **建议不部署** |
| **Qdrant** | ✅ 部署 | ⚠️ 紧张 | **建议不部署** |
| **Ollama备用** | ✅ 部署 | ❌ 不可行 | **不部署** |

### 内存占用分析

```
当前已部署服务:
├─ PostgreSQL: ~500MB
├─ Redis: ~100MB
├─ Next.js API: ~300MB
├─ OpenClaw Gateway: ~500MB
└─ 系统开销: ~800MB
────────────────────────
已使用: ~2.2GB
剩余: ~1.8GB

如果增加:
├─ Neo4j: ~1GB (堆内存) + ~500MB (页面缓存)
├─ Qdrant: ~500MB
────────────────────────
总计需要: ~4.2GB ❌ 超过4GB限制
```

---

## 📋 推荐部署方案

### 方案A：极简部署（推荐）⭐

```yaml
# docker-compose.yml（阿里云服务器）
services:
  # ✅ 已部署 - 保留
  postgres:
    image: postgis/postgis:16-3.4-alpine
    container_name: miaoying-postgres
    restart: always
    ports:
      - "15432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: didi
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ✅ 已部署 - 保留
  redis:
    image: redis:7-alpine
    container_name: miaoying-redis
    restart: always
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 256M

  # ✅ 已部署 - 保留
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
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  # 🆕 新增 - 轻量级知识存储
  # 使用SQLite替代Neo4j
  # 使用Redis向量缓存替代Qdrant
  # 见下方详细说明

volumes:
  postgres_data:
  redis_data:
```

### 方案B：升级配置（如果需要Neo4j/Qdrant）

如果确实需要知识图谱和向量数据库，建议升级服务器：

```
推荐配置:
- CPU: 4核
- 内存: 8GB (当前4GB的2倍)
- 磁盘: 100GB
- 带宽: 5Mbps

阿里云升级费用估算:
- 当前: ecs.e-c1m2.large (2核4G)
- 升级: ecs.c6.xlarge (4核8G)
- 费用: 约增加¥200-300/月
```

---

## 🔧 轻量级替代方案

### 1. 知识图谱 → SQLite + JSON

```javascript
// 替代Neo4j的轻量级方案
class LightweightKnowledgeGraph {
  constructor() {
    // 使用SQLite存储关系数据
    this.db = new Database('knowledge.db');

    // 初始化表结构
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        properties TEXT,  -- JSON格式
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_entity_id INTEGER NOT NULL,
        to_entity_id INTEGER NOT NULL,
        relation_type TEXT NOT NULL,
        properties TEXT,  -- JSON格式
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_entity_id) REFERENCES entities(id),
        FOREIGN KEY (to_entity_id) REFERENCES entities(id)
      );

      CREATE INDEX idx_entities_type ON entities(type);
      CREATE INDEX idx_entities_name ON entities(name);
      CREATE INDEX idx_relations_type ON relations(relation_type);
    `);
  }

  // 添加实体
  addEntity(type, name, properties = {}) {
    const stmt = this.db.prepare(
      'INSERT INTO entities (type, name, properties) VALUES (?, ?, ?)'
    );
    return stmt.run(type, name, JSON.stringify(properties));
  }

  // 添加关系
  addRelation(fromId, toId, relationType, properties = {}) {
    const stmt = this.db.prepare(
      'INSERT INTO relations (from_entity_id, to_entity_id, relation_type, properties) VALUES (?, ?, ?, ?)'
    );
    return stmt.run(fromId, toId, relationType, JSON.stringify(properties));
  }

  // 查询实体关系
  getRelations(entityId) {
    const stmt = this.db.prepare(`
      SELECT
        e.name as entity_name,
        e.type as entity_type,
        r.relation_type,
        r.properties
      FROM relations r
      JOIN entities e ON r.to_entity_id = e.id
      WHERE r.from_entity_id = ?
    `);
    return stmt.all(entityId);
  }
}
```

### 2. 向量存储 → Redis + 内存缓存

```javascript
// 替代Qdrant的轻量级方案
class LightweightVectorStore {
  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });

    // 内存缓存（热点数据）
    this.memoryCache = new Map();
    this.maxMemorySize = 1000;  // 最多缓存1000个向量
  }

  // 存储向量
  async storeVector(id, vector, metadata) {
    const key = `vector:${id}`;

    // 1. 存储到Redis（持久化）
    await this.redis.hset(key, {
      vector: JSON.stringify(vector),
      metadata: JSON.stringify(metadata)
    });

    // 2. 缓存到内存（快速访问）
    if (this.memoryCache.size < this.maxMemorySize) {
      this.memoryCache.set(id, { vector, metadata });
    }
  }

  // 搜索相似向量（简化版余弦相似度）
  async searchSimilar(queryVector, topK = 5) {
    const results = [];

    // 1. 先搜索内存缓存
    for (const [id, { vector, metadata }] of this.memoryCache) {
      const similarity = this.cosineSimilarity(queryVector, vector);
      results.push({ id, similarity, metadata });
    }

    // 2. 如果内存不足，从Redis搜索
    if (results.length < topK) {
      const keys = await this.redis.keys('vector:*');
      for (const key of keys.slice(0, 100)) {  // 限制搜索100个
        const data = await this.redis.hgetall(key);
        const vector = JSON.parse(data.vector);
        const metadata = JSON.parse(data.metadata);
        const similarity = this.cosineSimilarity(queryVector, vector);
        results.push({ id: key.replace('vector:', ''), similarity, metadata });
      }
    }

    // 3. 排序返回TopK
    return results
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);
  }

  // 余弦相似度计算
  cosineSimilarity(vec1, vec2) {
    const dotProduct = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
    const norm1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
    const norm2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));
    return dotProduct / (norm1 * norm2);
  }
}
```

---

## 📊 资源使用规划

### 内存分配（4GB总量）

```
系统预留: 800MB
├─ Ubuntu系统: ~500MB
├─ Docker守护进程: ~200MB
└─ 其他服务: ~100MB

应用服务: 2.7GB
├─ PostgreSQL: 1GB (限制)
├─ Redis: 256MB (限制)
├─ Next.js API: 300MB (估算)
├─ OpenClaw Gateway: 1GB (限制)
└─ Node.js/其他: ~144MB

剩余可用: ~500MB
└─ 突发情况缓冲
```

### 磁盘使用规划（40GB总量）

```
系统占用: 5GB
├─ Ubuntu系统: 3GB
├─ Docker镜像: 1.5GB
└─ 系统日志: 0.5GB

应用数据: 30GB
├─ PostgreSQL数据: 15GB
├─ Redis数据: 1GB
├─ OpenClaw数据: 2GB
├─ 知识图谱(SQLite): 5GB
├─ 向量数据(Redis): 2GB
└─ 应用日志: 5GB

剩余可用: 5GB
└─ 临时文件和缓冲
```

---

## ⚠️ 注意事项

### 1. 带宽限制（1 Mbps）

```
1 Mbps = 128 KB/s = 0.125 MB/s

影响:
- 大文件传输: 10MB文件需要 ~80秒
- API响应: 大JSON响应可能慢
- 用户上传: 速度慢

优化建议:
1. 启用Gzip压缩（减少70%传输量）
2. 使用CDN加速静态资源
3. API返回精简数据
4. 大文件考虑分片上传
```

### 2. 内存紧张

```bash
# 定期监控内存使用
docker stats --no-stream

# 设置内存限制
docker-compose.yml中添加:
deploy:
  resources:
    limits:
      memory: 1G

# 配置Redis内存淘汰策略
redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### 3. 磁盘空间

```bash
# 定期清理Docker
docker system prune -a

# 清理日志
find /var/log -type f -name "*.log" -mtime +7 -delete

# 监控磁盘使用
df -h
du -sh /var/lib/docker/*
```

---

## 🚀 部署步骤

### 第一步：SSH到服务器

```bash
ssh root@112.126.61.223
```

### 第二步：检查现有服务

```bash
# 查看运行中的容器
docker ps

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

### 第三步：优化现有服务

```bash
cd /var/www/miaoying

# 修改docker-compose.yml，添加内存限制
# 见上方配置

# 重启服务
docker-compose down
docker-compose up -d
```

### 第四步：部署轻量级知识存储

```bash
# 安装SQLite
apt-get update
apt-get install sqlite3

# 创建知识图谱数据库
cd /var/www/miaoying
sqlite3 data/knowledge.db < scripts/init_knowledge.sql
```

---

## 📊 性能预估

### 并发能力

```
CPU: 2核
├─ 理论并发: ~100 QPS
├─ 实际并发: ~50 QPS（考虑IO等待）
└─ 推荐并发: ~30 QPS（安全值）

内存: 4GB
├─ 可支持用户: ~50人同时在线
└─ 建议: 单用户请求间隔 > 2秒
```

### API响应时间

```
简单查询（无搜索）:
├─ 缓存命中: < 100ms
├─ 数据库查询: 100-300ms
└─ 模型推理: 500-2000ms

联网搜索:
├─ 智谱API调用: 1-3秒
├─ 数据处理: 100-500ms
└─ 总计: 1.5-4秒

带宽影响（1Mbps）:
├─ 小响应(<10KB): 无影响
├─ 中响应(10-100KB): +100-500ms
└─ 大响应(>1MB): +1-10秒
```

---

## ✅ 总结

### 推荐方案

```
┌─────────────────────────────────────────────────────────────┐
│               阿里云服务器部署方案（推荐）                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 保留现有服务:                                           │
│  - PostgreSQL (内存限制1GB)                                │
│  - Redis (内存限制256MB)                                   │
│  - Next.js API                                             │
│  - OpenClaw Gateway (内存限制1GB)                          │
│                                                             │
│  ❌ 不部署重型服务:                                         │
│  - Neo4j (改用SQLite轻量级方案)                            │
│  - Qdrant (改用Redis向量缓存)                              │
│  - Ollama (配置不足)                                       │
│                                                             │
│  ⚠️ 注意事项:                                               │
│  - 带宽只有1Mbps，启用Gzip压缩                             │
│  - 内存只有4GB，严格控制容器内存                           │
│  - 磁盘只有40GB，定期清理日志                              │
│  - 并发能力有限，建议30 QPS以内                            │
│                                                             │
│  💡 升级建议（如果需要更强能力）:                           │
│  - 升级到4核8GB (费用+¥200-300/月)                         │
│  - 或使用国外服务器跑重型服务                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**继续等待：**
4. 是否需要在阿里云部署Neo4j和Qdrant？
5. 国外服务器的具体用途？

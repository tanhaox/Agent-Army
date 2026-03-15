# Agent Army - Docker 部署指南

**版本**: v1.0
**更新日期**: 2026-03-15
**适用环境**: Linux, macOS, Windows（WSL2）

---

## 📦 部署架构

```
┌─────────────────────────────────────────────┐
│              Docker 容器集群                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐       │
│  │ agent-army   │  │ PostgreSQL   │       │
│  │ (Web UI)     │  │ (数据库)     │       │
│  │ Port: 8501   │  │ Port: 5432   │       │
│  └──────┬───────┘  └──────────────┘       │
│         │                                  │
│  ┌──────▼───────┐  ┌──────────────┐       │
│  │ Redis        │  │ Prometheus   │       │
│  │ (缓存)       │  │ (监控)       │       │
│  │ Port: 6379   │  │ Port: 9090   │       │
│  └──────────────┘  └──────┬───────┘       │
│                          │                  │
│                    ┌──────▼───────┐       │
│                    │ Grafana      │       │
│                    │ (可视化)     │       │
│                    │ Port: 3000   │       │
│                    └──────────────┘       │
└─────────────────────────────────────────────┘
```

---

## 🚀 快速开始（5分钟部署）

### 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 20GB+ 磁盘空间

### 部署步骤

#### 1. 创建 Dockerfile

**文件**: `Dockerfile`

```dockerfile
# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "web_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 2. 创建 docker-compose.yml

**文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Agent Army 主服务
  agent-army:
    build: .
    container_name: agent-army
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://postgres:your_password@db:5432/agent_army
      - REDIS_URL=redis://redis:6379
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TUSHARE_API_KEY=${TUSHARE_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - agent-army-network

  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    container_name: agent-army-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=agent_army
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - agent-army-network

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: agent-army-redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - agent-army-network

  # Prometheus 监控
  prometheus:
    image: prom/prometheus:latest
    container_name: agent-army-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - agent-army-network

  # Grafana 可视化
  grafana:
    image: grafana/grafana:latest
    container_name: agent-army-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/default.json
    depends_on:
      - prometheus
    networks:
      - agent-army-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  agent-army-network:
    driver: bridge
```

#### 3. 创建环境变量文件

**文件**: `.env`

```bash
# AI 模型 API 密钥
ZHIPU_API_KEY=your_zhipu_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 数据源 API 密钥
TUSHARE_API_KEY=your_tushare_api_key_here

# 数据库密码
POSTGRES_PASSWORD=your_secure_password_here
```

#### 4. 一键部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f agent-army
```

#### 5. 访问服务

- **Web界面**: http://localhost:8501
- **Grafana监控**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 🔧 配置详解

### 数据库配置

**PostgreSQL 连接URL**:
```
postgresql://postgres:your_password@db:5432/agent_army
```

**初始化脚本**（可选）:
```bash
# 进入容器
docker-compose exec db bash

# 连接到数据库
psql -U postgres -d agent_army

# 执行初始化脚本
\i /app/sql/init.sql
```

### Redis配置

**连接URL**:
```
redis://redis:6379
```

**最大内存**: 256MB
**淘汰策略**: allkeys-lru（最近最少使用）

### 监控配置

**Prometheus配置文件**: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agent-army'
    static_configs:
      - targets: ['agent-army:8501']
    metrics_path: '/_stcore/health'
```

**Grafana Dashboard**: `monitoring/grafana-dashboard.json`

```json
{
  "dashboard": {
    "title": "Agent Army 监控",
    "panels": [
      {
        "title": "Agent 执行时间",
        "targets": [{"expr": "agent_execution_seconds"}]
      },
      {
        "title": "API 调用次数",
        "targets": [{"expr": "api_calls_total"}]
      },
      {
        "title": "缓存命中率",
        "targets": [{"expr": "cache_hit_rate"}]
      },
      {
        "title": "错误率",
        "targets": [{"expr": "error_rate"}]
      }
    ]
  }
}
```

---

## 🛠️ 常用操作

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d agent-army

# 重新构建并启动
docker-compose up -d --build
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs -f agent-army

# 查看最近100行日志
docker-compose logs --tail=100 agent-army
```

### 进入容器

```bash
# 进入 agent-army 容器
docker-compose exec agent-army bash

# 进入数据库容器
docker-compose exec db psql -U postgres -d agent_army

# 进入 Redis 容器
docker-compose exec redis redis-cli
```

### 数据备份

```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres agent_army > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker-compose exec -T db psql -U postgres agent_army < backup_20260315.sql
```

---

## 🔒 安全建议

### 1. 修改默认密码

**修改 .env 文件**:
```bash
# 生成强密码
openssl rand -base64 32

# 更新 .env 文件
POSTGRES_PASSWORD=your_new_strong_password_here
```

### 2. 限制外部访问

**修改 docker-compose.yml**:
```yaml
services:
  db:
    # 删除 ports 映射，仅在容器内访问
    # ports:
    #   - "5432:5432"

  redis:
    # 删除 ports 映射
    # ports:
    #   - "6379:6379"
```

### 3. 使用 secrets 管理敏感信息

**创建 docker-compose.override.yml**（不提交到git）:
```yaml
version: '3.8'

services:
  agent-army:
    secrets:
      - zhipu_api_key
      - deepseek_api_key

secrets:
  zhipu_api_key:
    file: ./secrets/zhipu_api_key.txt
  deepseek_api_key:
    file: ./secrets/deepseek_api_key.txt
```

---

## 📊 性能优化

### 1. 资源限制

**修改 docker-compose.yml**:
```yaml
services:
  agent-army:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 2. 日志轮转

```bash
# 在容器内配置 logrotate
docker-compose exec agent-army apt-get install -y logrotate

# 配置 logrotate
cat > /etc/logrotate.d/agent-army <<EOF
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

---

## 🐛 故障排查

### 问题1: 容器无法启动

```bash
# 查看详细日志
docker-compose logs agent-army

# 检查端口占用
netstat -tuln | grep 8501

# 检查磁盘空间
df -h
```

### 问题2: 数据库连接失败

```bash
# 检查数据库状态
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 测试连接
docker-compose exec agent-army python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:your_password@db:5432/agent_army')
print('连接成功')
"
```

### 问题3: 缓存不生效

```bash
# 检查 Redis 状态
docker-compose exec redis redis-cli INFO

# 检查 Redis 连接
docker-compose exec agent-army python -c "
import redis
r = redis.from_url('redis://redis:6379')
print(r.ping())
"
```

---

## 📦 生产环境部署建议

### 1. 使用外部数据库

**修改 DATABASE_URL**:
```
DATABASE_URL=postgresql://user:password@external-db-host:5432/agent_army
```

### 2. 使用外部 Redis

**修改 REDIS_URL**:
```
REDIS_URL=redis://external-redis-host:6379
```

### 3. 配置反向代理（Nginx）

```nginx
location / {
    proxy_pass http://localhost:8501;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 4. 启用 HTTPS

**使用 Let's Encrypt 获取免费证书**:
```bash
certbot certonly --standalone -d your-domain.com
```

---

## ✅ 验收清单

### 部署检查

- [ ] Docker 镜像构建成功
- [ ] 所有容器正常启动
- [ ] Web 界面可访问
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 日志正常输出

### 功能检查

- [ ] Agent 分析功能正常
- [ ] 数据获取功能正常
- [ ] 缓存功能正常
- [ ] 监控数据正常

### 性能检查

- [ ] 响应时间 < 5秒
- [ ] 内存使用 < 4GB
- [ ] CPU 使用 < 80%

---

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Prometheus 文档](https://prometheus.io/)
- [Grafana 文档](https://grafana.com/docs/)

---

**文档完成时间**: 2026-03-15
**维护者**: Agent Army 团队

# Agent Army - Docker Desktop 部署指南

**版本**: v1.0
**更新日期**: 2026-03-15
**适用环境**: Windows + Docker Desktop

---

## 🚀 3分钟快速部署（推荐）

### 前置条件

- ✅ Docker Desktop 已安装
- ✅ 8GB+ 内存
- ✅ 20GB+ 磁盘空间

### 快速部署步骤

#### 1️⃣ 配置API密钥（1分钟）

**方式1: 使用提供的脚本**
```bash
# 双击运行
复制-env-template.bat
```

**方式2: 手动创建**
```bash
# 复制模板文件
copy .env.example .env

# 编辑 .env 文件，填入您的API密钥
notepad .env
```

**必需的API密钥**:
- `ZHIPU_API_KEY` - 智谱AI（获取：https://open.bigmodel.cn/）
- `TUSHARE_API_KEY` - Tushare（获取：https://tushare.pro/）

**可选的API密钥**:
- `DEEPSEEK_API_KEY` - DeepSeek（获取：https://platform.deepseek.com/）
- `OPENAI_API_KEY` - OpenAI（获取：https://platform.openai.com/）

#### 2️⃣ 一键启动（2分钟）

```bash
# 双击运行
start-docker.bat
```

**脚本会自动完成**:
1. ✅ 检查 Docker Desktop 是否运行
2. ✅ 检查环境变量文件
3. ✅ 创建必要的数据目录
4. ✅ 构建 Docker 镜像
5. ✅ 启动所有服务
6. ✅ 打开浏览器访问 Web 界面

#### 3️⃣ 访问服务（立即）

- **Web界面**: http://localhost:8501
- **Grafana监控**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

**🎉 完成！** 系统已启动并运行。

---

## 📋 部署架构

```
Docker Desktop
├── agent-army (Web UI)
├── db (PostgreSQL)
├── redis (Redis)
├── prometheus (监控)
└── grafana (可视化)
```

---

## 🔧 详细配置说明

### 文件结构

```
Agent_Army/
├── Dockerfile                  # Docker镜像配置
├── docker-compose.yml          # Docker Compose配置
├── .env.example               # 环境变量模板
├── .env                       # 您的环境变量（不提交到Git）
├── start-docker.bat           # 一键启动脚本 ⭐
├── stop-docker.bat            # 一键停止脚本
├── data/                      # 数据持久化目录
├── logs/                      # 日志文件目录
└── monitoring/                # 监控配置
    ├── prometheus.yml
    ├── grafana-dashboard.json
    └── grafana-datasources.yml
```

### 端口说明

| 服务 | 端口 | 访问地址 | 用途 |
|------|------|----------|------|
| **agent-army** | 8501 | http://localhost:8501 | Web界面 |
| **grafana** | 3000 | http://localhost:3000 | 监控可视化 |
| **prometheus** | 9090 | http://localhost:9090 | 监控数据 |
| **db** | 5432 | localhost:5432 | 数据库（可选） |
| **redis** | 6379 | localhost:6379 | 缓存（可选） |

---

## 🛠️ 常用操作

### 启动服务

```bash
# 方式1: 一键启动脚本（推荐）
start-docker.bat

# 方式2: Docker Desktop 界面
# 在 Docker Desktop 中点击 "Start"
```

### 查看服务状态

```bash
# 在 Docker Desktop 界面查看
# 或使用命令行：
docker-compose ps
```

### 查看日志

```bash
# 方式1: Docker Desktop 界面
# 点击容器 -> "Logs"

# 方式2: 命令行
docker-compose logs -f agent-army
```

### 停止服务

```bash
# 方式1: 一键停止脚本
stop-docker.bat

# 方式2: Docker Desktop 界面
# 点击 "Stop" 按钮

# 方式3: 命令行
docker-compose down
```

### 重启服务

```bash
# 在 Docker Desktop 界面
# 点击 "Restart" 按钮

# 或使用命令行：
docker-compose restart agent-army
```

---

## 📊 监控和可视化

### Grafana 监控仪表板

**访问**: http://localhost:3000
- **用户名**: admin
- **密码**: admin

**包含的监控指标**:
- Agent 执行时间
- API 调用次数
- 缓存命中率
- 错误率

### Prometheus 监控

**访问**: http://localhost:9090

**查看指标**: http://localhost:9090/metrics

---

## 🔒 安全建议

### 1. 保护API密钥

```bash
# ⚠️ 重要：不要将 .env 文件提交到Git
echo .env >> .gitignore
```

### 2. 修改默认密码

**修改 Grafana 密码**:
1. 访问 http://localhost:3000
2. 登录后修改 admin 密码

**修改数据库密码**:
```bash
# 编辑 .env 文件
POSTGRES_PASSWORD=your_new_strong_password
```

### 3. 限制外部访问

**修改 docker-compose.yml**:
```yaml
# 删除不必要的端口映射
services:
  agent-army:
    ports:
      - "127.0.0.1:8501:8501"  # 仅本地访问
```

---

## 🐛 故障排查

### 问题1: Docker Desktop 未运行

**错误信息**:
```
[ERROR] Docker Desktop 未运行！
```

**解决方案**:
1. 启动 Docker Desktop
2. 等待 Docker 图标变为运行状态
3. 重新运行 `start-docker.bat`

---

### 问题2: 容器启动失败

**错误信息**:
```
[ERROR] 服务启动失败！
```

**解决方案**:
```bash
# 查看详细日志
docker-compose logs agent-army

# 检查端口占用
netstat -ano | findstr :8501

# 重新构建镜像
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

### 问题3: 无法访问Web界面

**检查清单**:
1. ✅ Docker Desktop 正在运行
2. ✅ 容器状态为 "Running"
3. ✅ 浏览器访问 http://localhost:8501
4. ✅ 防火墙未阻止8501端口

**解决方案**:
```bash
# 查看容器状态
docker-compose ps

# 查看健康检查
docker-compose ps agent-army

# 查看日志
docker-compose logs agent-army
```

---

### 问题4: API密钥未生效

**解决方案**:
```bash
# 1. 停止服务
docker-compose down

# 2. 重新编辑 .env 文件
notepad .env

# 3. 重新启动服务
docker-compose up -d
```

---

## 📦 数据持久化

### 数据位置

**Windows路径**:
```
\\wsl$\docker-desktop-data\data\docker\volumes\
```

**容器内路径**:
```
/app/data    # 数据文件
/app/logs    # 日志文件
```

### 备份数据

```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres agent_army > backup_$(date +%Y%m%d).sql

# 备份数据文件
xcopy data data_backup /E /I

# 备份日志
xcopy logs logs_backup /E /I
```

### 恢复数据

```bash
# 恢复数据库
docker-compose exec -T db psql -U postgres agent_army < backup_20260315.sql

# 恢复数据文件
xcopy data_backup data /E /I
```

---

## 🚀 性能优化

### 1. 调整资源限制

**在 Docker Desktop 中**:
1. 右键点击容器
2. 选择 "Settings"
3. 调整 "Resources" 限制
4. CPU: 2-4核
5. 内存: 4-8GB

### 2. 启用GPU加速（可选）

**如果有 NVIDIA GPU**:
1. 安装 NVIDIA Container Toolkit
2. 在 docker-compose.yml 中添加：
```yaml
services:
  agent-army:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 📚 进阶操作

### 进入容器Shell

```bash
# 在 Docker Desktop 界面
# 右键点击容器 -> "Exec" -> "bash"

# 或使用命令行
docker-compose exec agent-army bash
```

### 更新代码

```bash
# 方式1: 重新构建（推荐）
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 方式2: 热重载（仅限代码修改）
docker-compose restart agent-army
```

### 清理未使用的资源

```bash
# 运行停止脚本
stop-docker.bat

# 或手动清理
docker system prune -a
```

---

## ✅ 部署验证

### 检查清单

- [ ] Docker Desktop 正在运行
- [ ] 环境变量已配置（.env 文件存在）
- [ ] 所有容器状态为 "Running"
- [ ] Web界面可访问（http://localhost:8501）
- [ ] Grafana 可访问（http://localhost:3000）
- [ ] 日志正常输出
- [ ] 数据持久化正常

---

## 🎯 下一步

部署完成后，您可以：

1. **开始使用**
   - 访问 http://localhost:8501
   - 输入股票代码进行分析

2. **查看监控**
   - 访问 http://localhost:3000
   - 查看Agent执行时间和性能指标

3. **阅读文档**
   - [API文档](API.md)
   - [快速启动指南](QUICKSTART.md)
   - [架构文档](ARCHITECTURE.md)

4. **提Issue**
   - 遇到问题：[GitHub Issues](https://github.com/tanhaox/AI-Agent-Local/issues)
   - 讨论问题：[GitHub Discussions](https://github.com/tanhaox/AI-Agent-Local/discussions)

---

**文档完成时间**: 2026-03-15
**维护者**: Agent Army 团队

**🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！**

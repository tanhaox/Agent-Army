# AI-Agent-Local 项目盘点报告

> 生成日期：2026-04-29 | 仓库根路径：`C:\AI-Agent-Local`

---

## 1. 项目目录结构

```
AI-Agent-Local/
├── .claude/                    # Claude Code 内部数据（worktrees、plans、settings）
├── .github/                    # GitHub Actions CI/CD 工作流
├── .omc/                       # oh-my-claudecode 配置
├── .vscode/                    # VS Code 工作区设置
│
├── Agent_Army/                 # ★ A 股 AI 投资分析系统（47 个 Agent、6 个军团）
│   ├── config/                 #   代理配置文件
│   ├── src/                    #   核心源码
│   ├── tests/                  #   测试套件
│   ├── data/                   #   市场数据
│   ├── docs/                   #   文档与完成报告
│   ├── scripts/                #   辅助脚本
│   ├── reports/                #   分析报告输出
│   ├── monitoring/             #   Prometheus + Grafana 监控
│   ├── credentials/            #   凭证文件
│   └── archive/                #   归档
│
├── dandanyi/                   # ★ 单单易 — 网约车司机智能助手（Next.js 16）
│   ├── src/                    #   应用源码（App Router）
│   ├── drizzle/                #   Drizzle ORM 数据库迁移
│   ├── public/                 #   静态资源
│   ├── scripts/                #   部署/分析脚本
│   └── openclaw/               #   OpenClaw 集成子模块
│
├── 短剧/                       # ★ 短剧 AI 批量生产系统（FastAPI + Vue 3）
│   ├── backend/                #   Python FastAPI 后端
│   │   ├── app/api/            #     12 个路由模块
│   │   ├── app/models/         #     11 个 SQLAlchemy ORM 模型
│   │   ├── app/services/       #     36+ 个业务服务模块
│   │   ├── app/schemas/        #     8 个 Pydantic Schema
│   │   ├── app/core/           #     配置与数据库引擎
│   │   ├── migrations/         #     18 个 Alembic 迁移
│   │   └── tests/              #     15+ 个测试文件
│   ├── frontend/               #   Vue 3 + TypeScript 前端
│   │   ├── src/api/            #     9 个 API 客户端模块
│   │   ├── src/components/     #     4 个核心组件
│   │   ├── src/views/          #     7 个页面视图
│   │   ├── src/router/         #     Vue Router 配置
│   │   └── src/stores/         #     Pinia 状态管理
│   └── docs/                   #   项目策划书
│
├── miaoying/                   # 🛑 已停用 — 旧的航班应用（被 dandanyi 取代）
│
├── projects/                   # 本地项目集合
│   ├── apps/                   #   应用类项目（intelligent-tutor、task-orchestrator）
│   ├── skills/                 #   12 个可复用技能（ollama_ai、api_manager 等）
│   └── tools/                  #   9 个工具（backup-agent、ddg-search 等）
│
├── shared/                     # 共享基础设施
│   ├── scripts/                #   项目生成器（create_project.py）
│   ├── subagents/              #   子代理框架（dispatcher、reviewer、workflow）
│   ├── templates/              #   技能模板
│   └── testing/                #   通用测试框架（fixtures、utils、templates）
│
├── openclaw-original/          # OpenClaw 上游仓库（Agent 框架）
├── openclaw-ali/               # OpenClaw 阿里云部署配置
├── oh-my-claudecode/           # Claude Code 增强框架
│
├── docs/                       # 全局文档（30+ 个 .md 文件）
│   ├── 项目组织规范.md         #   目录结构与命名约定
│   ├── 代码可维护性规范.md     #   模块化设计标准
│   ├── 开发指南.md             #   8 阶段开发工作流
│   └── improvements/           #   改进建议归档
│
├── github_downloads/           # 16 个第三方参考仓库（AutoGen、n8n-mcp 等）
├── archives/                   # 历史报告与旧目录
├── logs/                       # 全局日志
├── memory/                     # Claude 持久记忆
├── uploads/                    # 用户文件上传
│
├── CLAUDE.md                   # ★ 项目全局配置与约定（27KB）
├── README.md                   # 项目说明
├── .gitignore
├── .mcp.json                   # MCP 服务器配置
└── pytest.ini                  # 全局 Pytest 配置
```

---

## 2. 功能说明

### 2.1 项目定位

**AI-Agent-Local** 是一个 **AI Agent 与技能开发平台**，同时也是多个 AI 应用的孵化和管理工作空间。仓库遵循"三地统一"原则（本地 → GitHub → 服务器），通过严格的 git 工作流保障版本一致性。

### 2.2 核心子系统

#### A. 短剧 AI 批量生产系统（`短剧/`）

**目标**：单人工作室可月产 3-5 部商业竖屏微短剧的全流程 AI 生产线。

核心模块：

| 模块 | 职责 | 后端服务 | 前端组件 |
|------|------|---------|---------|
| **项目管理** | 项目 CRUD、进度跟踪 | `project_service.py` | `ProjectWorkspace.vue` |
| **剧本生成** | LLM 生成分集剧本 | `script_generation_service.py` | `StoryboardManager.vue` |
| **角色设计** | AI 生成数字演员形象 | `character_generation_service.py` | `CharacterManager.vue` |
| **分镜设计** | 智能导演分析 + 素材预生成 | `intelligent_director_service.py` | `LensProduction.vue` |
| **视频生成** | 多后端调度（Seedance/Kling） | `video_task_service.py` | LensProduction 视频区 |
| **TTS 配音** | Edge-TTS / 火山引擎 TTS | `tts_service.py` | 音频配置面板 |
| **后期合成** | FFmpeg 字幕叠加 | `ffmpeg_service.py` | — |

**AI 服务路由**：
- **LLM**：DeepSeek（主）→ Ollama qwen3:8b（fallback），通过 `services/llm/factory.py` 统一调度
- **图像生成**：ComfyUI / Seedream 4.0 / Seedream 5.0，通过 `services/image/base.py` 抽象
- **视频生成**：Seedance 2.0（火山引擎）/ Kling AI，通过 `services/video/base.py` 抽象
- **TTS**：Edge-TTS / 火山引擎 TTS

**数据流**：
```
项目创建 → 剧本生成 → 角色设计 → 分镜规划 → 智能导演分析
    → 素材预生成（Seedream）→ 视频生成（Seedance）→ 配音（TTS）
    → 后期合成（FFmpeg）→ 导出
```

#### B. Agent Army（`Agent_Army/`）

A 股价值投资 AI 分析系统。47 个专业 Agent 分 6 个军团：
- **工具层**：5 大工具类（数据采集、技术分析、基本面分析等）
- **业务层**：6 个军团覆盖投资全流程
- **管理层**：Commander + HR + 自我进化系统
- **Web UI**：Streamlit（localhost:8501）
- **监控**：Prometheus + Grafana

#### C. 单单易（`dandanyi/`）

网约车司机智能助手。Next.js 16 App Router：
- 订单截图 OCR 识别（百度 OCR）
- 航班信息追踪（PKX 系统 v7.1）
- 热力地图 + 路径推荐
- 天气服务（和风天气）
- DeepSeek AI 集成

### 2.3 共享基础设施

| 组件 | 位置 | 说明 |
|------|------|------|
| **项目生成器** | `shared/scripts/create_project.py` | 交互式创建标准化项目 |
| **子代理框架** | `shared/subagents/` | dispatcher → reviewer → workflow 协作 |
| **测试框架** | `shared/testing/` | 通用 fixtures、模板、验证工具 |
| **Claude Code 增强** | `oh-my-claudecode/` | 技能市场、钩子系统、代理管理 |
| **OpenClaw** | `openclaw-original/` | Agent 编排框架 |

---

## 3. 环境依赖

### 3.1 编程语言与运行时

| 子系统 | 语言 | 版本 | 运行时 |
|--------|------|------|--------|
| 短剧后端 | Python | 3.12 | Uvicorn + FastAPI |
| 短剧前端 | TypeScript | 5.7 | Vite 6 + Vue 3 |
| Agent Army | Python | 3.10+ | Streamlit |
| 单单易 | TypeScript | 5.x | Next.js 16 + Node 18 |
| 共享脚本 | Python | 3.10+ | CPython |

### 3.2 核心框架与库

**短剧后端** (`backend/requirements.txt`)：
- Web：FastAPI 0.115、Uvicorn 0.34、python-multipart
- 数据库：SQLAlchemy 2.0（async）、asyncpg 0.30、Alembic 1.15
- 缓存/队列：Redis 5.3、Celery 5.5
- AI/HTTP：httpx 0.28、openai≥1.30、tenacity 9.1
- TTS：edge-tts 7.0、volcengine-python-sdk
- 配置：pydantic-settings 2.9
- 测试：pytest 8.3、pytest-asyncio 0.26

**短剧前端** (`frontend/package.json`)：
- Vue 3.5、Vue Router 4.5、Pinia 3.0
- Naive UI 2.40（组件库）
- Axios 1.9（HTTP 客户端）
- Vite 6.3（构建工具）

**Agent Army**：
- LangGraph 1.0.7、AutoGen 0.10.0、CrewAI 0.134.0
- Streamlit 1.55.0

**单单易**：
- Next.js 16、Tailwind CSS、Drizzle ORM
- 百度 OCR、天地图、和风天气 API

### 3.3 数据库与中间件

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| PostgreSQL | Docker 镜像 | 15 | 短剧业务数据、单单易航班数据 |
| Redis | Docker 镜像 | 7-alpine | 缓存、任务队列 |
| Prometheus | Docker 镜像 | latest | Agent Army 监控 |
| Grafana | Docker 镜像 | latest | Agent Army 可视化 |

### 3.4 外部 API 集成

| API | 子系统 | 用途 |
|-----|--------|------|
| 火山引擎 Ark | 短剧 | Seedream 图像生成、Seedance 视频生成、TTS |
| DeepSeek API | 短剧、单单易 | LLM 文本生成 |
| Ollama (本地) | 短剧、项目 | 本地 LLM fallback（qwen3:8b） |
| Kling AI | 短剧 | 视频生成（备用） |
| 百度 OCR | 单单易 | 订单截图识别 |
| 天地图 | 单单易 | 地图与热力图 |
| 和风天气 | 单单易 | 天气数据 |
| 智谱 GLM | Agent Army | AI 分析主模型 |
| Tushare | Agent Army | A 股市场数据 |

### 3.5 工具链

| 工具 | 用途 |
|------|------|
| Docker + Docker Compose | 所有服务的容器化部署 |
| npm / pnpm | Node.js 包管理 |
| pip | Python 包管理 |
| Alembic | 数据库迁移 |
| Pytest | Python 测试 |
| Vite | 前端构建 |
| vue-tsc | TypeScript 类型检查 |
| ESLint / Prettier | 代码规范（部分项目） |

### 3.6 操作系统兼容性

- **开发环境**：Windows 11（主要） + WSL / Git Bash
- **生产环境**：Ubuntu 22.04（DigitalOcean 服务器 157.245.195.58）
- **容器化**：所有服务均可通过 Docker Compose 在任何支持 Docker 的系统上运行

---

## 4. 运行与构建指南

### 4.1 短剧系统

**启动**（推荐）：
```batch
# 双击桌面快捷方式
C:\Users\tanha\Desktop\短剧系统.bat
```

**手动启动**：
```bash
cd C:\AI-Agent-Local\短剧
docker compose up -d --build
```

**单独启动后端**（开发模式）：
```bash
cd C:\AI-Agent-Local\短剧\backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**单独启动前端**（开发模式）：
```bash
cd C:\AI-Agent-Local\短剧\frontend
npm install
npm run dev
```

**运行测试**：
```bash
cd C:\AI-Agent-Local\短剧\backend
pytest tests/ -v
```

**配置文件**：
| 文件 | 作用 |
|------|------|
| `短剧/.env` | 全局环境变量（API Key、模型名、数据库连接） |
| `短剧/.env.example` | 配置模板（不含真实密钥） |
| `短剧/docker-compose.yml` | 4 个服务编排（postgres、redis、backend、frontend） |
| `短剧/backend/app/core/config.py` | Pydantic Settings 配置加载器 |
| `短剧/frontend/nginx.conf` | Nginx 反向代理配置 |

**访问地址**：
- 前端：http://localhost
- 后端 API：http://localhost:8000
- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs

### 4.2 Agent Army

```bash
cd C:\AI-Agent-Local\Agent_Army
docker compose up -d          # 启动全部服务
# Web UI: http://localhost:8501
```

### 4.3 单单易

```bash
cd C:\AI-Agent-Local\dandanyi
pnpm install
pnpm dev                      # 开发模式
pnpm build && pnpm start      # 生产模式
```

### 4.4 共享工具

```bash
# 项目生成器
cd C:\AI-Agent-Local\shared\scripts
python create_project.py --type skill --name my-skill

# 子代理框架测试
cd C:\AI-Agent-Local\shared
python -m pytest testing/ -v
```

---

## 5. 潜在技术债务与注意事项

### 5.1 严重问题

| # | 问题 | 位置 | 风险 | 建议 |
|---|------|------|------|------|
| 1 | **API Key 明文存储** | `短剧/.env`、`Agent_Army/.env`、`dandanyi/.env` | 🔴 安全 | 使用 Docker secrets 或外部密钥管理服务 |
| 2 | **miaoying 项目混淆** | `dandanyi/` 服务器目录仍叫 `miaoying` | 🟡 运维 | 重命名服务器目录，消除历史遗留 |
| 3 | **重复备份目录** | 根目录 `backup-before-*`、`dandanyi_backup_*` | 🟡 磁盘 | 清理过时备份，统一用 archives/ |

### 5.2 架构问题

| # | 问题 | 说明 | 建议 |
|---|------|------|------|
| 4 | **部分项目无 Docker 化** | `projects/` 下的小项目缺少 Dockerfile | 补充 Dockerfile 或 docker-compose |
| 5 | **数据库密码硬编码** | `docker-compose.yml` 中有默认密码 `shortfilm123` | 强制从 .env 读取 |
| 6 | **短剧后端轮询无重试上限** | `video_task_service.py` 中的 `_poll_seedance_task` / `_poll_kling_task` 死循环 | 已修复（添加了独立 DB 会话），需加最大重试次数 |
| 7 | **前端无错误边界** | Vue 组件缺少 ErrorBoundary，API 失败时 UI 可能崩溃 | 添加全局错误处理组件 |

### 5.3 代码质量

| # | 问题 | 位置 | 建议 |
|---|------|------|------|
| 8 | **超大服务文件** | `storyboard_service.py`、`lensProduction.vue`（850+ 行） | 拆分为更小的模块 |
| 9 | **console.log 残留** | 前端部分组件 | 替换为统一日志方案 |
| 10 | **测试覆盖率不均** | 短剧后端有 15+ 测试文件，但前端无测试 | 添加 Vitest + Vue Test Utils |
| 11 | **部分 Python 项目缺少 requirements.txt** | `projects/skills/` 下部分技能 | 补充依赖声明 |
| 12 | **硬编码的 localhost URL** | `storyboards.py:809` `base = "http://localhost:8000"` | 改用配置项 |

### 5.4 文档与规范

| # | 问题 | 建议 |
|---|------|------|
| 13 | **根目录无 README**（只有 CLAUDE.md 和一个小 README） | 完善项目 README，说明整体架构 |
| 14 | **部分文档为中文，部分为英文** | 统一文档语言或提供双语版本 |
| 15 | **`projects/skills/` 下许多技能缺少 README** | 每个技能应包含基本说明 |

### 5.5 性能与运维

| # | 问题 | 说明 |
|---|------|------|
| 16 | **短剧后端 `pool_size=5` 较小** | 高并发时可能成为瓶颈，考虑根据负载调大 |
| 17 | **Docker 镜像未使用多阶段构建** | 短剧后端 Dockerfile 可优化体积 |
| 18 | **无日志轮转配置** | `logs/` 目录无自动清理策略 |
| 19 | **`.bat` 文件的 CRLF 问题** | 通过 Write 工具创建的 `.bat` 文件需手动转换行尾（LF → CRLF） |

---

## 附录 A：关键文件快速索引

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | 项目全局约定（三地统一、8 阶段开发流程、编码规范） |
| `短剧/.env` | 短剧系统环境变量（API Key、模型名） |
| `短剧/docker-compose.yml` | 短剧系统 4 个容器编排 |
| `短剧/backend/app/main.py` | FastAPI 入口 |
| `短剧/frontend/src/main.ts` | Vue 3 入口 |
| `docs/项目组织规范.md` | 目录结构标准 |
| `docs/开发指南.md` | 8 阶段开发工作流 |
| `shared/scripts/create_project.py` | 新项目生成器 |

---

## 附录 B：子系统快速状态

| 子系统 | 状态 | 版本 | 可访问地址 |
|--------|------|------|-----------|
| 短剧系统 | ✅ 活跃开发 | v0.1.0 | http://localhost |
| Agent Army | ✅ 生产就绪 | v2.0.0 | http://localhost:8501 |
| 单单易 | ✅ 生产运行 | v2.8.9 | https://112.126.61.223:6001 |
| 喵应 | 🛑 已停用 | — | — |
| Ollama AI 技能 | ✅ 可用 | — | http://localhost:5006 |
| 智能辅导 | ✅ 可用 | — | http://localhost:5000 |

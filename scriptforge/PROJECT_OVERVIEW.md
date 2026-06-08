# ScriptForge 项目盘点报告

> 生成日期: 2026-04-29 | 版本: v0.3.0

---

## 1. 项目目录结构

```
scriptforge/
├── docker-compose.yml            # 编排 Redis + ChromaDB + Celery Worker
├── .gitignore                    # Git 忽略规则
│
├── backend/                      # Python FastAPI 后端
│   ├── .env / .env.example       # 环境变量（实际 / 模板）
│   ├── Dockerfile                # 容器构建：python:3.12-slim + ffmpeg + Playwright
│   ├── requirements.txt          # Python 依赖清单
│   ├── alembic.ini               # Alembic 数据库迁移配置
│   ├── alembic/                  # 迁移版本（5 个历史版本）
│   ├── app/
│   │   ├── main.py               # FastAPI 入口：生命周期、中间件、限流、路由挂载
│   │   ├── api/                  # 11 个路由模块（REST 端点）
│   │   ├── core/                 # 基础设施：数据库、安全、配置、日志、异常、健康检查
│   │   ├── models/               # 9 个 SQLAlchemy 数据模型
│   │   ├── services/             # 15 个业务服务（LLM、ASR、抓取、分析等）
│   │   └── tasks/                # Celery 异步任务定义
│   ├── config/                   # 运行时配置（抖音 Cookie）
│   ├── logs/                     # 日志输出目录
│   └── uploads/                  # 上传文件存储
│
├── frontend/                     # React + Vite 前端
│   ├── package.json              # 依赖与脚本
│   ├── pnpm-lock.yaml            # pnpm 锁文件
│   ├── vite.config.ts            # Vite 配置（API 代理 + Tailwind）
│   ├── tsconfig*.json            # TypeScript 配置
│   ├── eslint.config.js          # ESLint 规则
│   ├── index.html                # HTML 入口
│   ├── src/
│   │   ├── main.tsx              # React 入口
│   │   ├── App.tsx               # 路由 + Query Client + Layout
│   │   ├── components/           # 通用组件（Layout、UI 库）
│   │   ├── pages/                # 6 个页面 + 子页面
│   │   ├── services/             # 10 个 API 服务模块
│   │   ├── hooks/                # 自定义 Hook（useApi）
│   │   ├── lib/                  # Axios 实例封装
│   │   └── types/                # TypeScript 类型定义
│   └── public/                   # 静态资源
│
└── tools/                        # 工具脚本
    ├── gen_startup_all.py        # 生成全栈启动 .bat（后端 + 前端）
    └── gen_startup_bat.py        # 生成后端启动 .bat
```

---

## 2. 功能说明

### 2.1 项目目标

ScriptForge 是一个**短视频剧本智能创作平台**，面向直播/短视频创作者，提供从竞品分析到剧本生成的全链路 AI 辅助工具。

### 2.2 核心模块

#### 模块 A：数据采集与 ASR

| 组件 | 职责 |
|------|------|
| `douyin_service.py` | 基于 Playwright 的抖音数据抓取服务，获取博主信息和视频列表 |
| `douyin_video_list_worker.py` | Celery 子进程 Worker，处理视频列表的并发抓取与筛选排序 |
| `asr.py` / `asr_worker.py` | 基于 faster-whisper 的语音转文字，支持 Celery 异步执行 |
| `search_enhancer.py` | 对转写结果进行搜索增强与语义优化 |

**数据流**: 抖音 URL → Playwright 抓取 → 筛选 Top N 视频 → yt-dlp 下载 → 提取音频 → faster-whisper 转写 → 结构化文本

#### 模块 B：人设分析

| 组件 | 职责 |
|------|------|
| `persona_analyzer.py` | 调用 DeepSeek LLM，从文本切片中提取说话风格、口头禅、反应模式、核心信念等 |
| `creator.py` | 创作者画像分析服务，支持自定义人物创建和融合 |
| `Persona` 模型 | 版本化存储人设，支持增量更新（`append_slices`）和演进追踪（`version_notes`） |

**特点**: 支持增量分析——新增素材时不重新计算全部数据，而是通过 `incremental_analyze` 合并新旧特征，保持版本号递增。

#### 模块 C：策略提取

| 组件 | 职责 |
|------|------|
| `strategy_extractor.py` | 从学习材料中提取叙事模式和句子模板 |
| `embedding.py` | 基于 BGE 模型的文本嵌入，支持 jieba 中文分词 |
| `vector_store.py` | 统一封装 ChromaDB 和 pgvector 两种向量存储后端 |
| `StrategyEntry` 模型 | 存储策略条目、嵌入向量、质量评分、使用次数 |

#### 模块 D：剧本生成

| 组件 | 职责 |
|------|------|
| `script_generator.py` | 核心剧本生成器，整合 Persona + RoomTone + GuestIdentity |
| `compliance.py` | 基于 Aho-Corasick 自动机的敏感词检测 |
| `deepseek_client.py` | DeepSeek API HTTP 客户端，带连接池、指数退避重试、错误分类 |
| `ScriptProject` 模型 | 存储剧本内容、版本、情绪曲线、策略组合、字数统计 |

**特点**: 支持多版本并行生成（`multi_version`），单个版本失败不阻塞其他版本（`return_exceptions=True`）。支持按说话人重新生成特定台词。

#### 模块 E：基础设施

| 组件 | 职责 |
|------|------|
| `security.py` | API Key 中间件 + 用户依赖注入 + 所有权检查 |
| `limiter.py` | slowapi 全局限流（默认 100/min，AI 端点 5-10/min） |
| `health.py` | 聚合健康检查（DB / Redis / ChromaDB / DeepSeek 独立探测） |
| `exceptions.py` | 分层异常体系（`AIServiceError` → Auth / RateLimit / Timeout / ServerError） |
| `celery.py` | Celery 应用配置，自动发现 `app.tasks` 下的任务 |
| `logger.py` | 集中日志系统，自动脱敏（API Key / Token / 密码），文件轮转保留 7 天 |

### 2.3 API 路由清单

| 前缀 | 主要端点 | 限流 |
|------|---------|------|
| `/api/asr` | `POST /transcribe`, `/batch`, `/task/{id}` | — |
| `/api/persona` | `POST /analyze`, `POST /{id}/append`, `GET /{id}`, `GET /`, `DELETE /{id}` | 10/min |
| `/api/scripts` | `POST /generate`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /{id}/regenerate` | 5/min |
| `/api/room_tones` | `POST /`, `GET /`, `GET /{id}`, `DELETE /{id}` | — |
| `/api/importer` | 多数据源导入端点（含 SSE 流式） | — |
| `/api/materials` | `POST /`, `GET /`, `DELETE /{id}` | — |
| `/api/strategies` | `POST /extract`, `POST /batch-extract`, `GET /`, `GET /{id}`, `DELETE /{id}` | 5-10/min |
| `/api/creator` | `POST /persona`, `POST /guests`, `POST /fusion`, `POST /save` | 10/min |
| `/api/sensitive_words` | `POST /`, `GET /`, `DELETE /{id}` | — |
| `/api/settings` | `GET /`, `PUT /` | — |
| `/api/logs` | 客户端日志上报 | — |
| `/api/health` | 聚合健康检查（含各依赖状态） | — |
| `/api/` | API 索引页 | — |

### 2.4 前端页面

| 路由 | 页面 | 说明 |
|------|------|------|
| `/scripts` | ScriptsPage | 剧本生成主界面：配置面板 + 剧本显示 |
| `/personas` | PersonasPage | 人设管理：列表 + 详情面板 |
| `/learn` | LearnPage | 学习资料：ASR 学习 / 人设学习 / 资料编辑器 / 进度面板 |
| `/creator` | CreatorPage | 创作者分析页面 |
| `/settings` | SettingsPage | 用户设置 |

---

## 3. 环境依赖

### 3.1 运行时

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端语言 | Python | 3.12 |
| 前端语言 | TypeScript | ~6.0 |
| 前端运行时 | Node.js | ≥18（Vite 8 要求） |
| 数据库 | PostgreSQL + pgvector | — |
| 缓存/队列 | Redis | 7-alpine |
| 向量存储 | ChromaDB（可选，pgvector 为主） | latest |
| 容器引擎 | Docker Compose | — |

### 3.2 后端核心依赖

| 类别 | 库 | 用途 |
|------|-----|------|
| Web 框架 | fastapi≥0.115, uvicorn≥0.34 | HTTP API |
| ORM | sqlalchemy[asyncio]≥2.0, asyncpg≥0.30 | 异步数据库 |
| 迁移 | alembic≥1.14 | 数据库版本管理 |
| 队列 | celery[redis]≥5.4, redis≥5.0 | 后台任务 |
| AI/ML | faster-whisper, ctranslate2, sentence-transformers | ASR + 嵌入 |
| LLM | httpx≥0.28（DeepSeek API 客户端） | 剧本 / 分析 |
| 抓取 | playwright≥1.40, yt-dlp | 数据采集 |
| 安全 | pyahocorasick, slowapi, tenacity | 敏感词 / 限流 / 重试 |
| 分词 | jieba | 中文处理 |

### 3.3 前端核心依赖

| 类别 | 库 | 用途 |
|------|-----|------|
| UI 框架 | react, react-dom | 19.2 |
| 路由 | react-router-dom | 7.14 |
| 数据获取 | @tanstack/react-query, axios | API 交互 |
| 样式 | tailwindcss | 4.2 |
| 构建 | vite | 8.0 |
| 图标 | lucide-react | 1.11 |

### 3.4 外部服务

| 服务 | 端点 | 用途 |
|------|------|------|
| DeepSeek API | `https://api.deepseek.com/v1` | LLM（剧本生成、人设分析、策略提取） |
| BGE 嵌入模型 | 本地加载 | 中文文本向量化 |

### 3.5 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | ✅ |
| `CELERY_BROKER_URL` | Redis 消息队列 URL | ✅ |
| `CELERY_RESULT_BACKEND` | Redis 结果后端 URL | ✅ |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | ✅ |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | — |
| `CHROMA_HOST / CHROMA_PORT` | ChromaDB 连接 | — |
| `SECRET_KEY` | 应用密钥（自动生成） | — |
| `API_AUTH_KEY` | API 认证密钥（空 = 不启用） | — |
| `DEBUG` | 调试模式开关 | — |

---

## 4. 运行与构建指南

### 4.1 环境准备

```bash
# 1. PostgreSQL（需独立安装或已有实例）
# 2. 启动 Docker 依赖
cd c:\Projects\scriptforge
docker-compose up -d redis chromadb

# 3. 后端依赖
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
playwright install chromium

# 4. 前端依赖
cd frontend
pnpm install
```

### 4.2 启动命令

```bash
# ── 方式一：一键启动（推荐） ──
# 双击桌面: ScriptForge-启动服务.bat
# 或:
python tools/gen_startup_all.py  # 生成 .bat

# ── 方式二：手动启动 ──
# 终端 1: 后端
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端 2: 前端
cd frontend
pnpm dev

# 终端 3: Celery Worker（如需后台任务）
cd backend
celery -A app.core.celery worker --concurrency=2 --loglevel=info
```

### 4.3 数据库迁移

```bash
cd backend
# 生成迁移（模型变更后）
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 4.4 验证

| 地址 | 说明 |
|------|------|
| `http://localhost:8000/api/health` | 后端健康检查 |
| `http://localhost:8000/docs` | Swagger API 文档 |
| `http://localhost:8000/api/` | API 索引 |
| `http://localhost:5173` | 前端页面 |

### 4.5 配置文件位置

| 文件 | 作用 |
|------|------|
| `backend/.env` | 生产环境变量（不提交 Git） |
| `backend/.env.example` | 环境变量模板 |
| `backend/alembic.ini` | 数据库迁移配置 |
| `backend/config/douyin_cookies.json` | 抖音抓取凭据 |
| `backend/data/sensitive_words.txt` | 敏感词库 |
| `docker-compose.yml` | 容器编排 |
| `frontend/vite.config.ts` | Vite 构建与代理配置 |
| `frontend/tsconfig*.json` | TypeScript 编译配置 |

---

## 5. 潜在技术债务与注意事项

### 5.1 架构层面

| 编号 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| A1 | **认证系统为占位实现** — `get_current_user` 自动创建 demo 用户，无 JWT/Session | 🔴 高 | 在 `security.py` 预留的缝合处接入 JWT 或 OAuth2 |
| A2 | **`API_AUTH_KEY` 认证可选** — 留空则完全跳过认证，生产环境有风险 | 🔴 高 | 生产环境强制设置 API Key，或迁移到 JWT |
| A3 | **StrategyEntry / SensitiveWord 无 `created_by` FK** — 无法追踪创建者 | 🟡 中 | 为多用户场景补充所有权字段 |
| A4 | **docker-compose 未包含 PostgreSQL** — 依赖宿主机数据库，环境搭建不便 | 🟡 中 | 添加 PostgreSQL 服务到编排文件，或提供 docker-compose.dev.yml |

### 5.2 代码质量

| 编号 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| C1 | **`importer.py` 有手动修复的缩进** — try/finally 块被手动调整为无条件清理代码，原始逻辑可能丢失 | 🟡 中 | 审查原始意图，恢复正确的 try/finally 结构 |
| C2 | **部分端点无限流** — asr、materials、room_tones、importer 等端点未加 `@limiter.limit` | 🟡 中 | 对所有数据修改端点添加限流 |
| C3 | **`emotion_curve` 使用字符串** — 本应使用结构化数据（如枚举或 JSON），目前为自由文本 | 🟢 低 | 定义情绪曲线枚举类型，在前端映射为可视化配置 |
| C4 | **硬编码的 CORS 域名** — `main.py` 中 `allow_origins` 写死 `localhost` | 🟢 低 | 迁移到环境变量 `CORS_ORIGINS` |
| C5 | **`config.py` 使用 `pydantic.BaseSettings`** — 该 API 在 Pydantic v2 中标记为 deprecated | 🟢 低 | 迁移到 `pydantic-settings` 的 `BaseSettings` |

### 5.3 安全

| 编号 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| S1 | **`.env` 中 API Key 明文存储** — `DEEPSEEK_API_KEY` 可见 | 🔴 高 | 生产环境使用 Secret 管理服务，或至少确保 `.env` 在 `.gitignore` 中 |
| S2 | **`SECRET_KEY` 自动生成** — 重启后变更可能导致 token 失效（如未来接入 JWT） | 🟡 中 | 生产环境通过环境变量显式设置固定值 |
| S3 | **Celery Worker 无认证** — Redis 未设置密码 | 🟡 中 | 生产环境为 Redis 添加密码认证 |

### 5.4 运维

| 编号 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| O1 | **无 CI/CD 配置** — 缺少 `.github/workflows` 或同类管道 | 🟡 中 | 添加 GitHub Actions 进行 lint → test → build 流水线 |
| O2 | **前端无测试** — `src/` 下无 `*.test.ts(x)` 文件 | 🟡 中 | 至少为核心页面和 API 服务层添加 Vitest + React Testing Library 测试 |
| O3 | **ChromaDB 为可选组件** — 启动失败仅 warning，但依赖它的功能会静默降级 | 🟢 低 | 在健康检查中明确报告 ChromaDB 状态，前端可展示警告 |
| O4 | **无日志聚合** — 后端日志仅存本地文件，容器化后难以集中查看 | 🟢 低 | 接入 ELK / Loki 等日志聚合方案 |

### 5.5 数据库

| 编号 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| D1 | **pgvector 依赖主机 PostgreSQL** — 需手动安装 pgvector 扩展 | 🟡 中 | 在 docker-compose 中使用 `pgvector/pgvector:pg16` 镜像 |
| D2 | **未使用数据库连接池调优** — 默认 pool_size=10, max_overflow=20 可能不足 | 🟢 低 | 根据负载测试结果调整，或在配置中暴露为环境变量 |
| D3 | **无数据备份方案** — 未见备份脚本或策略 | 🟡 中 | 添加 PostgreSQL dump 定时任务 |

---

## 6. 近期变更摘要（Phase 2 升级）

| 领域 | 变更内容 |
|------|---------|
| **权限系统** | 新增 `check_ownership` / `set_owner`，8 个路由模块接入 `current_user` 依赖 |
| **异常体系** | 统一 `ScriptForgeError` 分层异常，AI 服务按状态码分类 |
| **服务韧性** | DeepSeek 客户端添加连接池 + tenacity 重试（指数退避 1s-30s）；多版本生成单版本容错 |
| **健康检查** | 从静态字符串升级为 DB / Redis / ChromaDB / DeepSeek 独立探测 |
| **限流** | slowapi 全局限流 + AI 端点独立限流（5-10/min） |
| **代码修复** | `importer.py` 缩进错误修复；循环导入修复（limiter 提取为独立模块） |

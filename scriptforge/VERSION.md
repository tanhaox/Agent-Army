# ScriptForge v1.0 版本说明

> 发布日期：2026-05-04

## 项目定位

ScriptForge 是一个基于大语言模型的直播连线脚本生成系统。通过学习真实主播的直播素材（视频、音频、转写文字），自动构建仿生人设模型，并利用 AI 生成结构化的直播连线剧本。

核心流程：**素材导入 → 声纹建档 → AI 仿生分析 → 人设建模 → 编导策划 → 脚本生成**

---

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + TailwindCSS 4 |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 + pgvector 扩展 |
| 缓存 / 队列 | Redis 7 + Celery 5 |
| 向量存储 | ChromaDB |
| LLM | DeepSeek API (deepseek-chat) |
| ASR | faster-whisper large-v3 + CUDA 12.4 |
| 爬虫 | Playwright (Chromium) + yt-dlp + FFmpeg |
| 声纹 | resemblyzer (192维 speaker embedding) |
| 容器化 | Docker + Docker Compose + NVIDIA Container Toolkit |

---

## 核心功能模块

### 6 个核心页面

| 页面 | 路由 | 功能 |
|------|------|------|
| 学习中心 | `/learn` | 输入抖音主页 URL，自动下载视频、提取音频、语音转写、AI 分析，SSE 实时显示进度 |
| AI 仿生主播 | `/ai-anchors` | 管理仿生人设卡片，展示克隆完整度（18 维度评分），支持从素材资产生成 |
| 人设工坊 | `/personas` | 查看和编辑人设详情：语言风格、口头禅、反应模式、叙事单元、黑话地图、标签管理 |
| 剧情车间 | `/scripts` | 4 步向导式脚本生成：选基调 → 选参与者 → 设定剧情 → 生成剧本 |
| 素材资产 | `/assets` | 按主播分组管理视频/音频/转写文字，支持重新转写、声纹建档 |
| 系统设置 | `/settings` | 抖音 Cookie 配置、敏感词管理、策略管理、系统监控 |

---

## API 端点清单

共 14 个模块、91 个端点：

### 导入模块 (importer) — 7 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/import/url` | 从单个 URL 导入并转写 |
| GET | `/import/task/{task_id}` | 轮询导入任务状态 |
| POST | `/import/douyin-user-profile` | 获取抖音用户信息 |
| POST | `/import/douyin-user` | 导入抖音用户视频 |
| POST | `/import/douyin-user/task` | 提交异步导入任务 |
| GET | `/import/douyin-user/tasks` | 列出活跃导入任务 |
| POST | `/import/douyin-user/stream` | SSE 流式导入（实时进度） |

### 人设模块 (persona) — 15 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/persona/analyze` | 分析文本切片创建人设 |
| POST | `/persona/{id}/append` | 追加新文本切片 |
| POST | `/persona/cleanup-legacy` | 清理旧版人设 |
| POST | `/persona/reanalyze/{id}` | V2 18 维度重新分析 |
| POST | `/persona/{id}/lingo/import` | 导入黑话映射 |
| GET | `/persona/{id}/slices` | 获取人设切片列表 |
| GET | `/persona/{id}` | 获取人设详情 |
| GET | `/persona/` | 列出所有人设 |
| DELETE | `/persona/{id}` | 软删除人设 |
| GET | `/persona/anchors-without-persona` | 获取有待建卡主播 |
| POST | `/persona/generate-from-assets` | 从素材资产生成人设 |
| PATCH | `/persona/{id}` | 部分更新人设字段 |
| DELETE | `/persona/{id}/slices/{slice_id}` | 删除单个切片 |
| POST | `/persona/{id}/rollback` | 回滚人设版本 |

### 脚本模块 (scripts) — 6 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/scripts/generate` | 生成新脚本 |
| GET | `/scripts/{id}` | 获取脚本详情 |
| GET | `/scripts/` | 列出所有脚本 |
| PATCH | `/scripts/{id}` | 更新脚本内容 |
| DELETE | `/scripts/{id}` | 归档脚本 |
| POST | `/scripts/{id}/regenerate` | 重新生成指定角色对白 |

### 资产模块 (assets) — 12 个
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/assets` | 列出资产（分页过滤） |
| GET | `/assets/{id}` | 获取单个资产详情 |
| POST | `/assets` | 创建资产 |
| DELETE | `/assets/{id}` | 删除资产 |
| PATCH | `/assets/{id}` | 更新资产 |
| POST | `/assets/{id}/retranscribe` | 重新转写单个音频 |
| POST | `/assets/batch-retranscribe` | 批量重新转写 |
| GET | `/assets/batch-retranscribe-status` | 查询批量转写进度 |
| POST | `/assets/build-voice-profile` | 构建声纹档案 |
| GET | `/assets/voice-profiles` | 列出声纹档案 |
| DELETE | `/assets/voice-profiles/{name}` | 删除声纹档案 |
| POST | `/assets/cleanup-orphan-files` | 清理孤立文件 |
| GET | `/assets/stats/group-stats` | 按主播分组统计 |

### 编导模块 (director) — 5 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/scripts/{id}/director/roles` | 批量替换角色定义 |
| GET | `/scripts/{id}/director/roles` | 获取角色列表 |
| POST | `/scripts/{id}/director/acts` | 批量替换场次定义 |
| GET | `/scripts/{id}/director/acts` | 获取场次列表 |
| DELETE | `/scripts/{id}/director/all` | 删除全部编导设定 |

### 创作者模块 (creator) — 4 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/creator/persona` | AI 生成人设 |
| POST | `/creator/guests` | AI 生成嘉宾角色 |
| POST | `/creator/fusion` | 融合两个人设 |
| POST | `/creator/save` | 保存创作的人设 |

### 语音转写模块 (asr) — 3 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/asr/transcribe` | 转写单个音频 |
| POST | `/asr/batch` | 批量转写任务 |
| GET | `/asr/task/{task_id}` | 查询转写任务状态 |

### 策略模块 (strategies) — 5 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/strategies/extract` | 提取策略 |
| POST | `/strategies/batch-extract` | 批量提取策略 |
| GET | `/strategies/` | 列出策略 |
| GET | `/strategies/{id}` | 获取策略详情 |
| DELETE | `/strategies/{id}` | 删除策略 |

### 直播基调模块 (room_tones) — 4 个
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/room-tones/` | 列出直播基调 |
| GET | `/room-tones/{id}` | 获取基调详情 |
| POST | `/room-tones/` | 创建基调 |
| DELETE | `/room-tones/{id}` | 删除基调 |

### 敏感词模块 (sensitive_words) — 4 个
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sensitive-words/` | 列出敏感词 |
| POST | `/sensitive-words/` | 添加敏感词 |
| POST | `/sensitive-words/batch-import` | 批量导入敏感词 |
| DELETE | `/sensitive-words/{id}` | 删除敏感词 |

### 设置模块 (settings) — 4 个
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/settings/douyin-cookie` | 获取 Cookie 状态 |
| PUT | `/settings/douyin-cookie` | 更新 Cookie |
| GET | `/settings/` | 获取用户设置 |
| PATCH | `/settings/` | 更新用户设置 |

### 任务记录模块 (task_records) — 2 个
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/task-records` | 列出任务记录 |
| GET | `/task-records/{task_id}` | 获取任务详情 |

### 日志模块 (logs) — 1 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/logs/client` | 前端错误上报 |

### 管理模块 (admin) — 1 个
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/restart` | 重启后端进程 |

---

## 数据库表结构

共 12 张表：

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户 | username, email, plan_type, quota, settings |
| `personas` | AI 仿生人设 | name, global_style, catchphrases, language_style_v2(18维度), narrative_model, lingo_map, tags |
| `persona_slices` | 人设文本切片 | persona_id(FK), original_text, emotion_tag, source_url |
| `script_projects` | 脚本项目 | title, tone_id(FK), persona_id(FK), script_content(JSON), emotion_curve, status |
| `director_roles` | 编导角色 | script_id(FK), role_type(anchor/caller/extra), name, storyline |
| `director_acts` | 编导场次 | script_id(FK), title, task, participants(JSON) |
| `room_tones` | 直播基调 | name, core_rules, forbidden_topics, is_preset |
| `guest_identities` | 嘉宾身份 | name, age_range, occupation, personality, core_issue, speaking_style |
| `strategy_entries` | 策略条目 | title, category, extracted_pattern, embedding_vector(512维) |
| `sensitive_words` | 敏感词 | word, category, severity |
| `assets` | 素材资产 | task_id, anchor_name, asset_type(video/audio/transcript), transcription_text |
| `task_records` | 任务记录 | task_id, status, result_summary(JSON), video/download/transcribe counts |

---

## 关键架构决策

### 1. ASR 子进程隔离
语音转写使用 `faster-whisper`，通过独立 Python 子进程执行，避免 GPU 内存泄漏影响主进程。子进程通过 stdout JSON 通信，支持超时控制和心跳检测。

### 2. Playwright 子进程隔离
抖音爬虫通过独立子进程运行 Playwright Chromium，避免浏览器内存泄漏影响 API 服务。

### 3. SSE 实时进度
导入流程使用 Server-Sent Events 实时推送进度（下载/转写/分析），前端 TopBar 轮询 `task_records` 显示全局进度条。

### 4. 人设版本控制
人设字段支持 `user_edited_fields` 标记，AI 重新分析时保留用户手动编辑的内容，避免覆盖。

### 5. 声纹建档
使用 `resemblyzer` 提取 192 维 speaker embedding，构建声纹档案用于说话人分离。

### 6. 18 维度语言风格分析 (language_style_v2)
| 维度 | 说明 |
|------|------|
| tone | 语言基调 |
| vocabulary | 词汇特征 |
| rhythm_score | 节奏评分 |
| metaphor_usage | 比喻使用频率 |
| catchphrase_density | 口头禅密度 |
| empathy | 共情指数 |
| humor | 幽默指数 |
| aggressiveness | 攻击性 |
| rhetorical_question_freq | 反问频率 |
| interrupt_tendency | 打断倾向 |
| sharpness | 锐度 |
| self_deprecation | 自嘲程度 |
| humor_type | 幽默类型 |
| pace | 语速 |
| punchline_density | 金句密度 |
| opening_phrase | 开场白 |
| transition_phrase | 过渡语 |
| closing_phrase | 结束语 |

---

## 外部依赖

| 服务 | 用途 | 降级方案 |
|------|------|---------|
| DeepSeek API | 核心 AI 分析、脚本生成 | 降级为空白人设，无法生成脚本 |
| faster-whisper (GPU) | 语音转文字 | 无 GPU 时使用 CPU 模式，速度约 1:10 |
| Playwright | 抖音视频爬取 | 无降级，必须正常工作 |
| PostgreSQL | 数据持久化 | 无降级 |
| Redis | Celery 队列 + 缓存 | 部分功能可用，后台任务不可用 |
| NVIDIA CUDA | GPU 加速 | CPU 模式自动降级 |

---

## 环境要求

| 项目 | 要求 |
|------|------|
| Docker Desktop | 4.x+（必需） |
| NVIDIA 显卡驱动 | 550+（可选） |
| NVIDIA Container Toolkit | 最新版（可选） |
| 磁盘空间 | 至少 20 GB |
| 内存 | 建议 16 GB+ |
| 网络 | 安装时需要拉取镜像，运行时需要 DeepSeek API |

---

## 打包内容

```
scriptforge/
├── deployment/
│   ├── env-checker.html          # 环境检查工具（双击打开）
│   ├── setup.bat                 # 一键安装启动
│   ├── update.bat                # 系统更新
│   ├── .env.example              # 配置模板
│   ├── 安装指南.md                # 用户文档
│   ├── nginx.conf                # 前端 Nginx 配置
│   └── docker-images/
│       └── base-images.tar       # 基础 Docker 镜像包
├── docker-compose.yml            # 6 服务编排
├── backend/
│   ├── Dockerfile                # 后端镜像构建
│   ├── requirements.txt          # Python 依赖
│   └── offline_packages/         # 离线依赖包（可选）
├── frontend/
│   └── dist/                     # 前端构建产物
└── VERSION.md                    # 本文件
```

---

## 版本历史

### v1.0 (2026-05-04) — 首次正式发布

**6 个核心页面**：学习中心、AI 仿生主播、人设工坊、剧情车间、素材资产、系统设置

**91 个 API 端点**，覆盖 14 个功能模块

**12 张数据库表**，支持完整的业务数据流

**AI 能力**：
- 18 维度语言风格分析
- 声纹建档与说话人分离
- 编导模式（多角色/多麦序结构化剧本）
- 黑话地图自动提取
- 策略模式自动提取

**部署**：
- Docker 一键部署（6 服务编排）
- GPU 加速支持（NVIDIA CUDA）
- 数据库自动备份
- 前端 Nginx 反向代理

---

## 已知限制

- 仅支持 Windows（通过 Docker Desktop 运行）
- GPU 加速需要 NVIDIA 显卡
- 抖音下载需要定期更新 Cookie（约 7-15 天过期）
- 不支持移动端访问（桌面浏览器优化）
- DeepSeek API 不可用时核心 AI 功能无法使用
- 批量转写使用串行模式（GPU 安全考虑）

---

## 升级与打补丁指南

### 轻度补丁（前端/后端代码修改）

1. 用新文件覆盖对应目录
2. 双击 `deployment/update.bat`

### 重度补丁（新增依赖/数据库变更）

1. 用新文件覆盖对应目录
2. 双击 `deployment/update.bat`（将自动重新构建镜像）
3. 如有数据库变更，运行迁移：`docker compose exec backend alembic upgrade head`

### 回滚

1. 从 `backups/` 目录找到对应日期的备份
2. 覆盖项目目录后双击 `deployment/update.bat`
3. 如需回滚数据库：`cat backup.sql | docker compose exec -T postgres psql -U scriptforge scriptforge`

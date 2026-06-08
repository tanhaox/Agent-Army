# ScriptForge 系统架构盘点与加强方案

> **盘点日期**: 2026-05-03
> **项目路径**: `C:\AI-Agent-Local\scriptforge`
> **技术栈**: FastAPI + PostgreSQL + Celery/Redis + React/TypeScript + TanStack Query

---

## 一、按用户操作流程逐模块盘点

### 模块 1：学习中心 (`/learn`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 粘贴抖音主页链接，点击"一键处理" | `LearnPage.tsx` → `ProgressPanel` | `POST /api/import/douyin-user/stream` (SSE) | `importer.py` → `douyin_service.py` → `asr_worker.py` → `persona_analyzer.py` | `task_records`, `assets`, `personas`, `persona_slices`, `strategy_entries` |
| 2 | 粘贴抖音主页链接，点击"后台处理" | `LearnPage.tsx` | `POST /api/import/douyin-user/task` | `importer_tasks.py` → `douyin_video_list_worker.py` → `douyin_service.py` → `asr_worker.py` | `task_records`, `assets` |
| 3 | 粘贴单个视频链接，点击"开始导入" | `LearnPage.tsx` | `POST /api/import/url` | `importer.py` → `douyin_service.py` → `asr_worker.py` | `assets` |
| 4 | 拖拽视频文件，点击"全部转写" | `LearnPage.tsx` → `ProgressPanel` | `POST /api/asr/batch` | `asr.py` (WhisperASR) → `asr_tasks.py` | 无持久化（内存任务） |
| 5 | 拖拽 TXT 文件 | `LearnPage.tsx` → `TxtUploader` | 无 API（纯前端解析） | — | — |
| 6 | 编辑素材文本（区域二） | `LearnPage.tsx` → `MaterialEditor` | 前端 state 管理 | — | — |
| 7 | 标注角色（网红/连麦人A/B/C） | `VerificationPanel` | 前端 state 管理 | — | — |
| 8 | 添加情绪标签 | `VerificationPanel` | 前端 state 管理 | — | — |
| 9 | 点击时间戳查看视频片段 | `MaterialEditor` | 前端 `<video>` 控制 | — | — |
| 10 | 点击"校验完毕，锁定素材" | `LearnPage.tsx` | 前端 state 管理 | — | — |
| 11 | 点击"开始处理"（区域四） | `LearnPage.tsx` | `POST /api/persona/analyze` + `POST /api/strategies/batch-extract` | `persona_analyzer.py` (DeepSeek) + `strategy_extractor.py` (DeepSeek) | `personas`, `persona_slices`, `strategy_entries` |
| 12 | 查看人设分析报告 | `LearnPage.tsx` → `RadarChart` | 前端 state（analyze 返回结果） | — | — |
| 13 | 查看策略提取结果 | `LearnPage.tsx` | 前端 state（batchExtract 返回结果） | — | — |

### 模块 2：AI仿生主播 (`/ai-anchors`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 查看主播卡片列表 | `AiAnchorsPage.tsx` | `GET /api/persona/` | `persona.py` → SQLAlchemy | `personas` |
| 2 | 搜索主播 | `AiAnchorsPage.tsx` | 同上（前端过滤） | — | — |
| 3 | 点击卡片进入详情 | `AiAnchorsPage.tsx` | `navigate(/personas?select=id)` | — | — |
| 4 | 自定义标签（添加/删除） | `AiAnchorsPage.tsx` | `PATCH /api/persona/{id}` | `persona.py` → SQLAlchemy | `personas.tags` |
| 5 | 删除人设（三点菜单） | `AiAnchorsPage.tsx` | `DELETE /api/persona/{id}` | `persona.py` → SQLAlchemy | `personas`, `persona_slices` |

### 模块 3：人设工坊 (`/personas`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 查看人设列表 | `PersonasPage.tsx` → `PersonaList` | `GET /api/persona/` | `persona.py` | `personas` |
| 2 | 搜索人设 | `PersonaList` | 前端过滤 | — | — |
| 3 | 点击人设查看详情 | `PersonaDetailPanel` | `GET /api/persona/{id}` | `persona.py` | `personas` |
| 4 | 查看特征总览 Tab | `PersonaDetailPanel` | 前端渲染 | — | — |
| 5 | 查看切片素材 Tab | `PersonaDetailPanel` | `GET /api/persona/{id}/slices` | `persona.py` | `persona_slices` |
| 6 | 查看版本历史 Tab | `PersonaDetailPanel` | 前端渲染（persona.versions） | — | — |
| 7 | 编辑人设特征 | `PersonaDetailPanel` | `PATCH /api/persona/{id}` | `persona.py` | `personas` |
| 8 | 删除切片 | `PersonaDetailPanel` | `DELETE /api/persona/{id}/slices/{sid}` | `persona.py` | `persona_slices` |
| 9 | 上传新切片 | `PersonaDetailPanel` | `POST /api/persona/{id}/append` | `persona.py` → `persona_analyzer.py` | `persona_slices` |
| 10 | 回滚版本 | `PersonaDetailPanel` | `POST /api/persona/{id}/rollback` | `persona.py` | `personas`, `persona_slices` |
| 11 | 添加版本备注 | `PersonaDetailPanel` | `PATCH /api/persona/{id}` | `persona.py` | `personas` |
| 12 | 标记为模板/归档 | `PersonaDetailPanel` | `PATCH /api/persona/{id}` | `persona.py` | `personas` |
| 13 | 导出 JSON | `PersonaDetailPanel` | 前端处理（JSON 下载） | — | — |
| 14 | 复制 Prompt | `PersonaDetailPanel` | 前端处理（clipboard） | — | — |
| 15 | 查看雷达图 + 对比模式 | `PersonaDetailPanel` → `RadarChart` | 前端渲染 | — | — |
| 16 | 查看互补推荐卡片 | `PersonaDetailPanel` | 前端算法（向量相似度） | — | — |
| 17 | 查看调性适配柱状图 | `PersonaDetailPanel` | 前端渲染 | — | — |
| 18 | 查看精细特征（18维度） | `PersonaDetailPanel` | 前端渲染 | — | — |
| 19 | 查看替换词表 (Lingo) | `PersonaDetailPanel` | 前端渲染（persona.lingo_map） | — | — |
| 20 | 编辑/添加/删除替换词 | `PersonaDetailPanel` | `PATCH /api/persona/{id}` | `persona.py` | `personas.lingo_map` |
| 21 | 导入替换词表文件 | `PersonaDetailPanel` | `POST /api/persona/{id}/lingo/import` | `persona.py` | `personas.lingo_map` |
| 22 | 查看补充素材按钮 | `PersonaDetailPanel` | `navigate(/assets?task_id=xxx)` | — | — |
| 23 | 点击"用此主播生成脚本" | `PersonaDetailPanel` | `navigate(/scripts?persona_id=xxx)` | — | — |

### 模块 4：剧情车间 (`/scripts`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 选择调性（预设/自定义） | `StepOneForm` | `GET /api/room-tones/` | `room_tones.py` | `room_tones` |
| 2 | 选择连线场景类型 | `StepOneForm` | 前端 state | — | — |
| 3 | 选择剧本类型（简单/编导） | `StepOneForm` | 前端 state | — | — |
| 4 | 输入连线话题 | `StepOneForm` | 前端 state | — | — |
| 5 | 选择 AI 仿生主播 | `StepTwoForm` | `GET /api/persona/` | `persona.py` | `personas` |
| 6 | 添加连线人/群演 | `StepTwoForm` → `CreatorPage` | `POST /api/creator/guests` | `creator.py` (DeepSeek) | `guest_identities` |
| 7 | 编辑/删除角色 | `StepTwoForm` | 前端 state | — | — |
| 8 | 添加麦序（编导模式） | `StepThreeForm` | 前端 state | — | — |
| 9 | 编辑/删除/排序麦序 | `StepThreeForm` | 前端 state | — | — |
| 10 | 输入参考脚本（编导模式） | `StepThreeForm` | 前端 state | — | — |
| 11 | 设置情绪曲线 | `StepFourPanel` | 前端 state | — | — |
| 12 | 输入指定爆点/梗句 | `StepFourPanel` | 前端 state | — | — |
| 13 | 打开多版本生成 | `StepFourPanel` | 前端 state | — | — |
| 14 | 打开连线者增强 | `StepFourPanel` | 前端 state | — | — |
| 15 | 点击"生成脚本" | `ScriptsPage.tsx` | `POST /api/scripts/generate` | `script_generator.py` (DeepSeek) | `script_projects`, `director_roles`, `director_acts` |
| 16 | 查看生成的脚本 | `ScriptDisplay` | 前端 state（生成返回结果） | — | — |
| 17 | 重新生成全部/某一麦/某角色 | `ScriptDisplay` | `POST /api/scripts/{id}/regenerate` | `script_generator.py` (DeepSeek) | `script_projects` |
| 18 | 编辑台词并保存 | `ScriptDisplay` | `PATCH /api/scripts/{id}` | `scripts.py` | `script_projects` |
| 19 | 复制全部 | `ScriptDisplay` | 前端处理（clipboard） | — | — |
| 20 | 导出 TXT | `ScriptDisplay` | 前端处理（文件下载） | — | — |
| 21 | 查看合规检测结果 | `ScriptDisplay` | 前端渲染（compliance 字段） | `compliance.py` | `sensitive_words` |
| 22 | 查看高光时刻标记 | `ScriptDisplay` | 前端渲染（highlights 字段） | — | — |

### 模块 5：素材资产 (`/assets`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 查看素材统计 | `AssetsPage.tsx` | `GET /api/assets/stats/group-stats` | `assets.py` → SQLAlchemy | `assets` |
| 2 | 搜索素材 | `AssetsPage.tsx` | `GET /api/assets?search=xxx` | `assets.py` | `assets` |
| 3 | 筛选素材类型/日期 | `AssetsPage.tsx` | `GET /api/assets?type=xxx&date=xxx` | `assets.py` | `assets` |
| 4 | 切换卡片/列表视图 | `AssetsPage.tsx` | 前端 state | — | — |
| 5 | 点击视频卡片预览 | `AssetsPage.tsx` → `<video>` | `/uploads/videos/xxx.mp4` | 静态文件服务 | — |
| 6 | 点击音频卡片预览 | `AssetsPage.tsx` → `<audio>` | `/uploads/videos/xxx.wav` | 静态文件服务 | — |
| 7 | 点击转写文本查看全文 | `AssetsPage.tsx` | 前端展开（max-height 切换） | — | — |
| 8 | 删除素材 | `AssetsPage.tsx` | `DELETE /api/assets/{id}` | `assets.py` | `assets` |
| 9 | 重新转写单个素材 | `AssetsPage.tsx` | `POST /api/assets/{id}/retranscribe` | `assets.py` → `asr_worker.py` → `audio_processor.py` | `assets`, `task_records` |
| 10 | 构建声纹档案 | `AssetsPage.tsx` | `POST /api/assets/build-voice-profile` | `assets.py` → `voice_profile_builder.py` | `voice_profiles/` (文件系统) |
| 11 | 批量重新转写 | `AssetsPage.tsx` | `POST /api/assets/batch-retranscribe` | `assets.py` → `asr_worker.py` → `audio_processor.py` | `assets`, `task_records` |
| 12 | 查看批量转写进度 | `AssetsPage.tsx` | `GET /api/assets/batch-retranscribe-status` | `assets.py` | `task_records` |

### 模块 6：系统设置 (`/settings`)

| # | 用户操作 | 前端文件 | API 端点 | 后端服务 | 数据表 |
|---|---------|---------|----------|---------|--------|
| 1 | 重启后端服务 | `SettingsPage.tsx` | `POST /api/admin/restart` | `admin.py` → `os.execv` | — |
| 2 | 查看策略列表 | `SettingsPage.tsx` | `GET /api/strategies/` | `strategies.py` | `strategy_entries` |
| 3 | 搜索/筛选策略 | `SettingsPage.tsx` | `GET /api/strategies/?search=xxx` | `strategies.py` | `strategy_entries` |
| 4 | 查看详情/删除 | `SettingsPage.tsx` | `GET/DELETE /api/strategies/{id}` | `strategies.py` | `strategy_entries` |
| 5 | 查看敏感词列表 | `SettingsPage.tsx` | `GET /api/sensitive-words/` | `sensitive_words.py` | `sensitive_words` |
| 6 | 添加/删除敏感词 | `SettingsPage.tsx` | `POST/DELETE /api/sensitive-words/{id}` | `sensitive_words.py` | `sensitive_words` |
| 7 | 批量导入敏感词 | `SettingsPage.tsx` | `POST /api/sensitive-words/batch-import` | `sensitive_words.py` | `sensitive_words` |
| 8 | 查看抖音 Cookie 状态 | `SettingsPage.tsx` | `GET /api/settings/douyin-cookie` | `settings.py` | 文件系统 |
| 9 | 粘贴保存 Cookie | `SettingsPage.tsx` | `PUT /api/settings/douyin-cookie` | `settings.py` → 文件写入 | 文件系统 |
| 10 | 全局搜索 | `SettingsPage.tsx` | 无 API（前端本地） | — | — |

---

## 二、后端基础设施

### 2.1 完整 API 路由清单

| 模块 | 前缀 | 端点数 | 文件 |
|------|------|--------|------|
| Admin | `/api/admin` | 1 | `admin.py` |
| ASR | `/api/asr` | 3 | `asr.py` |
| Persona | `/api/persona` | 12 | `persona.py` |
| Scripts | `/api/scripts` | 6 | `scripts.py` |
| Room Tones | `/api/room-tones` | 4 | `room_tones.py` |
| Importer | `/api/import` | 7 | `importer.py` |
| Materials | `/api/materials` | 1 | `materials.py` |
| Strategies | `/api/strategies` | 5 | `strategies.py` |
| Creator | `/api/creator` | 4 | `creator.py` |
| Sensitive Words | `/api/sensitive-words` | 4 | `sensitive_words.py` |
| Logs | `/api/logs` | 1 | `logs.py` |
| Settings | `/api/settings` | 4 | `settings.py` |
| Assets | `/api/assets` | 12 | `assets.py` |
| Task Records | `/api/task-records` | 2 | `task_records.py` |
| Director | `/api/scripts/{id}/director` | 5 | `director.py` |
| **合计** | | **75** | |

### 2.2 Celery 任务

| 任务 | 文件 | 触发条件 | 涉及表 |
|------|------|----------|--------|
| `transcribe_file_task` | `asr_tasks.py` | 批量 ASR 端点 | 无持久化 |
| `batch_transcribe_task` | `asr_tasks.py` | 批量 ASR 端点 | 无持久化 |
| `import_video_task` | `importer_tasks.py` | 单视频 URL 导入 | `assets` |
| `process_douyin_user_task` | `importer_tasks.py` | 抖音用户后台导入 | `task_records`, `assets`, `personas`, `persona_slices`, `strategy_entries` |

### 2.3 数据库表

| 表名 | 模型文件 | 关键字段 | 记录量级 |
|------|---------|----------|---------|
| `users` | `user.py` | id, username, plan_type, quota | 用户级 |
| `room_tones` | `room_tone.py` | id, name, core_rules, is_preset | ~10条预设 |
| `personas` | `persona.py` | id, name, language_style_v2, narrative_model, version, tags, lingo_map | 核心数据 |
| `persona_slices` | `persona_slice.py` | id, persona_id, original_text, emotion_tag | 大量（每人设 N 条） |
| `script_projects` | `script_project.py` | id, tone_id, persona_id, script_content, compliance | 中等 |
| `strategy_entries` | `strategy_entry.py` | id, title, category, pattern_type, embedding_id | 中等 |
| `sensitive_words` | `sensitive_word.py` | id, word, category, severity | ~1000条 |
| `learning_materials` | `learning_material.py` | id, title, content, source_url | 少量 |
| `assets` | `asset.py` | id, task_id, asset_type, file_path, transcription_text | 大量 |
| `task_records` | `task_record.py` | id, task_id, trigger, status, video_count | 中等 |
| `guest_identities` | `guest_identity.py` | id, name, personality, background, speech_habits | 中等 |
| `director_roles` | `director_role.py` | id, script_project_id, role_type, name, persona_id | 与脚本关联 |
| `director_acts` | `director_act.py` | id, script_project_id, title, participants, sort_order | 与脚本关联 |

### 2.4 外部服务依赖

| 服务 | 用途 | 失败影响 | 降级方案 |
|------|------|---------|---------|
| **DeepSeek API** | 人设分析、脚本生成、策略提取、角色生成 | 核心功能全部瘫痪 | ❌ 无 |
| **PostgreSQL** | 所有数据持久化 | 系统完全不可用 | ❌ 无 |
| **Redis** | Celery 任务队列、会话管理 | 异步任务不可用，同步功能正常 | ✅ 降级到同步 |
| **ChromaDB** | 向量存储（策略/人设相似度） | 互补推荐、相似度搜索不可用 | ✅ pgvector 备用 |
| **faster-whisper** | 语音转写 | 导入流程核心功能瘫痪 | ❌ 无 |
| **Playwright** | 抖音页面爬取（视频列表） | 视频列表获取失败 | ❌ 无 |
| **demucs** | 人声分离 | 转写质量下降（背景噪音干扰） | ✅ 跳过使用原始音频 |
| **pyannote** | 说话人分离 | 无法区分主播/连线人 | ✅ 降级到无标注模式 |
| **yt-dlp** | 视频下载 | 抖音视频无法下载 | ❌ 无 |
| **NVIDIA CUDA** | GPU 加速 ASR | 转写速度下降 5-8 倍 | ✅ 自动降级到 CPU |

---

## 三、诊断

### 3.1 技术债

#### T1: Celery 任务几乎未被使用

**现状**: 注册了 4 个 Celery 任务，但实际只有 `process_douyin_user_task` 在后台导入时使用。批量 ASR、单视频导入实际走的是 `subprocess.Popen` 或 `asyncio.to_thread`，而非 Celery。Redis 常年未连接（health check 报 error），说明 Celery worker 根本没在跑。

**影响**: 后台任务缺乏重试、优先级、结果持久化等队列特性。

#### T2: 双路径 ASR 调用不一致

**现状**: ASR 转写存在两条路径：
- **路径 A**: `asr_worker.py` 子进程（`assets.py`, `importer.py` 使用）
- **路径 B**: `asr.py` WhisperASR 单例（`asr.py` API 端点使用）

两条路径的模型大小不同（worker 用 medium，单例用 large-v3），繁简转换修复位置不同，VAD 配置不同。

**影响**: 同样的音频可能产生不同的转写结果。

#### T3: `materials` API 只有一个 DELETE 端点

**现状**: `learning_materials` 表有完整模型，但 API 只暴露了 DELETE。没有列表/创建/更新端点。前端也没有对应的页面。该表和 `persona_slices` 功能重叠。

**影响**: 死代码，增加维护负担。

#### T4: 角色生成后的保存流程断裂

**现状**: `POST /api/creator/guests` 返回生成的连线人数据，但 `POST /api/creator/save` 保存时逻辑简单。`guest_identities` 表和脚本页面内的 guest_config 存在数据冗余。连线人数据在脚本生成时以内联 JSON 形式传递，不引用 `guest_identities` 表。

**影响**: 连线人数据没有持久化复用，每次都需重新生成。

#### T5: 前端大量操作纯前端 state，无持久化

**现状**: 学习中心的素材编辑（区域二）、角色标注（区域三）、情绪标签、锁定状态全部存在 React state 中。页面刷新即丢失。

**影响**: 用户校验了大量标注后意外刷新，全部白费。

#### T6: `sys.executable` vs venv Python 不一致

**现状**: `assets.py` 和 `importer.py` 曾直接使用 `sys.executable` 启动 asr_worker 子进程。在 Windows 环境下，主进程可能是系统 Python 而非 venv Python，导致子进程缺少依赖（本次繁体 bug 的根因之一）。已修复为 `_venv_python()` 但 `importer.py` 的 `_run_asr_sync` 也需要确认。

**影响**: 运行环境不一致导致难以复现的间歇性错误。

### 3.2 逻辑漏洞

#### L1: 学习中心"一键处理"SSE 流的断线重连缺失

**现状**: `POST /api/import/douyin-user/stream` 是 SSE 长连接。如果网络抖动或浏览器切后台，SSE 连接断开，前端无法恢复进度。后端任务仍在跑，但前端丢失了任务 ID 和进度。

**影响**: 长时间导入任务（10+ 分钟）在弱网环境下容易中断。

#### L2: 资产删除不清理文件系统

**现状**: `DELETE /api/assets/{id}` 只删除数据库记录，不删除 `uploads/videos/` 下的视频和音频文件。

**影响**: 磁盘空间泄漏，删除 100 条素材可能仍占用数 GB。

#### L3: 人设分析无去重/防重复

**现状**: `POST /api/persona/analyze` 接受 `force_new` 参数，但默认情况下如果同名人设已存在会更新。更新逻辑是全量覆盖 `language_style_v2` 等字段，而非合并。同一批素材分析两次，第二次的结果完全替换第一次。

**影响**: 用户可能无意中覆盖了精心调校过的人设。

#### L4: 批量重转写的并发控制硬编码

**现状**: `batch-retranscribe` 使用 `ThreadPoolExecutor(max_workers=2)` 硬编码 2 并发。在 4 核 CPU 上可能太保守，在低配机器上可能太高。

**影响**: 无法根据硬件配置优化性能。

#### L5: 编导模式角色/麦序的保存时机不明确

**现状**: `StepThreeForm` 中的角色和麦序数据在表单 state 中管理，只有点击"生成脚本"时才一起提交。没有实时保存。如果用户配置了 10 个角色的复杂编导方案，页面刷新就全丢了。

**影响**: 编导模式的用户体验风险高。

#### L6: 声纹档案与人设/资产无强关联

**现状**: `voice_profiles/` 目录下的声纹文件以 `anchor_name` 命名，而 `personas` 表和 `assets` 表使用 UUID 作为 ID。`anchor_name` 可能重复、变更，导致声纹档案匹配错误或丢失。

**影响**: 声纹建档后，如果修改了人设名称，声纹档案可能无法被正确引用。

### 3.3 体验断点

#### U1: 学习中心"后台处理"无进度反馈

**现状**: 点击"后台处理"后，前端只显示一个任务 ID，没有跳转到任务列表。用户需要手动去右上角任务列表查看。如果任务列表被关闭，用户完全不知道任务进展。

**影响**: 用户提交后感觉"消失了"。

#### U2: ASR 转写等待无预估时间

**现状**: 单个音频转写 3-5 分钟（CPU）或 20-40 秒（GPU），但前端只显示"处理中..."旋转图标，没有进度百分比或预估时间。`asr_worker.py` 有详细的进度上报（百分比、预估剩余时间），但只有 SSE 流式路径使用了这些数据。

**影响**: 用户不确定是否卡死，反复刷新或重复提交。

#### U3: 素材资产页面的分组统计加载慢

**现状**: `GET /api/assets/stats/group-stats` 涉及多表 JOIN + 聚合，在数据量大时可能超过 3 秒。前端加载时只显示 Spinner，没有骨架屏或渐进式加载。

**影响**: 页面首屏白屏时间长。

#### U4: 人设工坊详情面板信息密度过高

**现状**: `PersonaDetailPanel` 在一个面板内展示 18 维度特征、雷达图、切片列表、版本历史、替换词表、互补推荐、调性适配等大量信息。没有懒加载，切换人设时全部重新渲染。

**影响**: 切换人设时有明显卡顿，低配设备尤其明显。

#### U5: 设置页面无操作确认

**现状**: "重启后端服务"、"删除人设"、"批量删除策略"等危险操作只有按钮点击触发，无二次确认弹窗。

**影响**: 误操作可能导致数据丢失或服务中断。

#### U6: 前端无离线状态提示

**现状**: 后端服务不可用时，前端所有请求静默失败。没有全局的"连接断开"提示。

**影响**: 用户不知道是操作失败还是系统故障。

### 3.4 架构风险

#### A1: DeepSeek API 单点故障

**现状**: 人设分析、脚本生成、策略提取、角色生成、风格融合全部依赖 DeepSeek API。API Key 配额耗尽、服务宕机、网络不通时，所有 AI 功能完全不可用。无本地模型 fallback。

**影响**: 核心业务逻辑完全依赖第三方服务。

#### A2: 数据库无备份策略

**现状**: PostgreSQL 数据没有自动备份机制。`pg_dump` 没有配置 cron job。如果数据库损坏，所有人设、脚本、策略数据全部丢失。

**影响**: 数据安全风险极高。

#### A3: 文件上传无容量限制和清理机制

**现状**: `uploads/` 目录下的视频/音频文件没有自动清理机制。没有总容量监控。`watchdog.py` 只清理超过 2 小时的 asr_worker 进程，不清理文件。

**影响**: 长期运行后磁盘空间可能耗尽。

#### A4: 并发安全和竞态条件

**现状**: `batch-retranscribe` 使用全局 `progress_counter` 字典，多个批量任务并发时会互相干扰。`asr.py` 的模型单例用 threading.Lock 保护，但 GPU 内存清理 (`_cleanup_gpu`) 可能在转写过程中被其他线程调用。

**影响**: 并发场景下可能出现数据不一致或崩溃。

#### A5: 认证系统形同虚设

**现状**: `ApiKeyMiddleware` 检查 `X-API-Key` header，但前端从 `sessionStorage` 读取 key。如果 sessionStorage 为空，API 请求被拒绝但没有前端引导。没有登录页面，没有用户注册/密码重置。`User` 模型存在但只有一个固定用户。

**影响**: 安全性低，多用户场景不可用。

---

## 四、加强建议

### P0（紧急，影响核心功能）

| # | 建议 | 涉及文件 | 改动描述 | 预期效果 |
|---|------|---------|----------|---------|
| P0-1 | 统一 ASR 调用路径 | `asr.py`, `asr_worker.py`, `assets.py`, `importer.py` | 统一模型大小（都用 large-v3 或 medium），统一繁简转换、VAD 配置。消除双路径不一致 | 转写结果一致，维护成本降低 |
| P0-2 | 学习中心素材自动保存 | `LearnPage.tsx` | 编辑文本、标注角色时，每 5 秒自动保存到 localStorage，页面加载时恢复 | 防止刷新丢失校验数据 |
| P0-3 | 数据库自动备份 | 新建 `scripts/backup_db.sh` + cron | 每日 `pg_dump` + 保留 7 天备份 | 防止数据灾难性丢失 |
| P0-4 | 文件清理机制 | `watchdog.py` | 资产删除时同步删除文件系统上的视频/音频文件 | 防止磁盘空间泄漏 |

### P1（重要，影响用户体验）

| # | 建议 | 涉及文件 | 改动描述 | 预期效果 |
|---|------|---------|----------|---------|
| P1-1 | DeepSeek API 降级方案 | `persona_analyzer.py`, `script_generator.py` | 检测 API 不可用时，返回预设模板或使用本地小模型 | AI 功能不完全瘫痪 |
| P1-2 | 转写进度预估 | `AssetsPage.tsx`, `asr_worker.py` | 重转写时展示进度百分比和预估时间（利用 worker 已有的进度输出） | 用户不再"盲等" |
| P1-3 | SSE 断线重连 | `LearnPage.tsx` | SSE 连接断开时，自动用任务 ID 查询进度恢复 | 长时间导入不再丢失 |
| P1-4 | 危险操作二次确认 | 全局 | 删除人设、重启服务、批量操作前弹出确认对话框 | 防止误操作 |
| P1-5 | 编导模式实时保存 | `ScriptsPage.tsx`, `director.py` | 角色/麦序变更时自动保存到后端 | 防止复杂配置丢失 |
| P1-6 | 清理死代码 | `materials.py`, `learning_material.py` | 移除未使用的 Materials API 和模型（或完善功能） | 减少维护负担 |

### P2（优化，提升系统质量）

| # | 建议 | 涉及文件 | 改动描述 | 预期效果 |
|---|------|---------|----------|---------|
| P2-1 | 消除 Celery 依赖或全面启用 | `celery.py`, `asr_tasks.py` | 要么全面用 Celery 做任务队列，要么移除 Celery/Redis 依赖，用 subprocess + asyncpg 替代 | 减少不必要的依赖 |
| P2-2 | 并发安全改造 | `assets.py` | 批量重转写的进度改为 per-task 实例化，不用全局字典 | 支持多任务并发 |
| P2-3 | 人设更新合并策略 | `persona_analyzer.py` | 更新人设时，合并而非覆盖现有特征（增量式更新） | 防止覆盖精心调校的数据 |
| P2-4 | 磁盘空间监控 | `watchdog.py` | 每日检查 `uploads/` 目录大小，超过阈值告警 | 防止磁盘满导致系统崩溃 |
| P2-5 | 前端连接状态提示 | `Layout.tsx` 或 `api.ts` | API 请求连续失败时，全局显示"连接断开"提示 | 用户明确知道系统状态 |
| P2-6 | 声纹档案关联增强 | `voice_profile_builder.py`, `persona.py` | 声纹档案使用 persona_id 而非 anchor_name 关联 | 防止名称变更导致匹配失败 |
| P2-7 | 批量重转写并发数可配置 | `assets.py` | `max_workers` 从环境变量读取，默认 `min(4, os.cpu_count())` | 适配不同硬件 |
| P2-8 | 素材资产页面性能优化 | `AssetsPage.tsx` | 分组统计接口加缓存，前端加骨架屏 | 首屏加载体验提升 |

---

## 五、架构总览图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 (React + TS)                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │Learn │ │Anchor│ │Person│ │Script│ │Asset │ │Create│ │Setting│  │
│  │Page  │ │sPage │ │asPage│ │sPage │ │sPage │ │rPage │ │sPage  │  │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘  │
│     └────────┴────────┴────────┴────────┴────────┴────────┘       │
│                         TanStack Query + Axios                       │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ /api/*
┌──────────────────────────────────┼──────────────────────────────────┐
│                        后端 (FastAPI)                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │importer   │ │persona   │ │scripts   │ │assets    │ │creator   │ │
│  │75 endpoints│ │          │ │          │ │          │ │          │ │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│        │             │            │             │            │        │
│  ┌─────┴─────┐      │      ┌─────┴─────┐      │      ┌─────┴─────┐ │
│  │asr_worker │      │      │script_gen │      │      │creator    │ │
│  │(subprocess)│     │      │           │      │      │_service   │ │
│  └─────┬─────┘      │      └─────┬─────┘      │      └─────┬─────┘ │
│        │             │            │             │            │        │
│  ┌─────┴─────────────┴────────────┴─────────────┴────────────┘       │
│  │                    DeepSeek API (LLM)                             │
│  └────────────────────────────────────────────────────────────────── │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │faster-whisper│ │audio_processor│ │watchdog.py   │                 │
│  │(CUDA/CPU)   │  │(demucs+pyann)│  │(daemon thread)│                │
│  └────────────┘  └──────────────┘  └──────────────┘                 │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────┼──────────────────────────────────┐
│                        数据层                                        │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ PostgreSQL   │  │ Redis    │  │ ChromaDB │  │ 文件系统   │       │
│  │ (13 tables)  │  │ (未启用) │  │ (降级)   │  │ uploads/  │       │
│  └──────────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、总结

### 系统健康度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 功能完整性 | ★★★★☆ | 核心流程完整，编导模式已实现 |
| 代码质量 | ★★★☆☆ | 存在双路径调用、死代码、硬编码 |
| 数据安全 | ★★☆☆☆ | 无备份策略、删除不清理文件 |
| 用户体验 | ★★★☆☆ | 基本可用，缺少进度反馈和防丢失机制 |
| 架构健壮性 | ★★☆☆☆ | DeepSeek 单点故障、无降级方案 |
| 可维护性 | ★★★☆☆ | 模块划分清晰，但部分模块耦合度高 |

### 最紧迫的 3 件事

1. **数据库备份**（P0-3）— 一旦磁盘故障，所有数据不可恢复
2. **素材自动保存**（P0-2）— 用户辛苦标注的数据刷新即丢
3. **统一 ASR 路径**（P0-1）— 双路径导致结果不一致和繁简 bug

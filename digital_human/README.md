# digital_human — 开发者导览

**目标读者**: 第一次接触这个项目的开发者(或自己隔 2 周回来看)。读 10 分钟能上手开发。
**不替代**: [项目状态总览.md](项目状态总览.md)(当前阶段/技术栈)、[项目进度看板.md](项目进度看板.md)(待办/优先级)、[CHANGELOG.md](CHANGELOG.md)(时间线/版本)。

---

## 1. 这是什么

FastAPI 后端 + SQLite + ComfyUI LTX2.3 + HyperFrames 的**数字人短视频生产流水线**。一条视频 = 4 层产物: 文章 → DeepSeek 洗稿 → TTS 配音 → ComfyUI LTX23 数字人视频 → HyperFrames 视觉片段。前 3 层是核心管线,第 4 层(可视化新闻数据)是并行的独立管线。Web UI(`web/*.html`)给运营/主播用,所有功能都有可观测 API。

---

## 2. 技术栈

- **Python** 3.11+ (`.venv/` 内置,`./.venv/Scripts/python` 调用)
- **Web 框架**: FastAPI + uvicorn (启动见 §4)
- **数据库**: SQLite + SQLAlchemy 2.x ORM,自动建表(`app/database.py:init_db`),文件 `data/pipeline.db`
- **LLM**: DeepSeek V4 (`config/app.yaml:deepseek`:`flash` / `pro`)
- **TTS 引擎**: Fish Speech `127.0.0.1:7860` / F5-TTS `7861` / IndexTTS2 `7862`
- **视频渲染**: ComfyUI `127.0.0.1:8188` (LTX2.3 数字人, 4090 GPU)
- **视觉渲染**: HyperFrames 0.7.72 (`npx hyperframes`, CPU, 不占 4090)
- **关键依赖**: 见 [`requirements.txt`](requirements.txt)(fastapi / sqlalchemy / pydantic / pyyaml / requests / soundfile / numpy / msgpack / jsonschema)

---

## 3. 30 秒上手

```bash
# 1. 启动 54321 Web API (主入口)
./.venv/Scripts/python run_web.py
# → http://127.0.0.1:54321/web/index.html

# 2. 各 TTS 引擎 / ComfyUI 需先单独启动 (端口见上)
# 3. 验证
curl http://127.0.0.1:54321/openapi.json | head
curl http://127.0.0.1:8188/system_stats          # ComfyUI
curl http://127.0.0.1:7860/                     # Fish Speech
```

**关键文件**: `app/main.py` (FastAPI app + lifespan + 路由挂载) · `app/config.py` (Config 加载 + env 替换) · `config/app.yaml` (YAML 配置) · `run_web.py` (入口)。

---

## 4. 启动入口

| 入口 | 文件 | 说明 |
|---|---|---|
| **API 服务** | [`run_web.py`](run_web.py) | 启动 uvicorn,加载 `config/app.yaml`,监听 `127.0.0.1:54321`。**推荐** |
| 旧爬虫版 | `launch_system_fixed.bat` / `start_server.py` | `SimpleHTTPRequestHandler` 静态文件 + `/api/news` 单接口,非主入口 |
| 测试 | `smoke_test.py` / `test_hot_news.py` | 冒烟测试 |

> **注**: `.bat` 启动文件是 M0 时期的爬虫入口,**主入口已切到 `run_web.py`**。

---

## 5. 项目结构

```
digital_human/
├── app/                          # FastAPI 主程序 (核心)
│   ├── main.py                   #   FastAPI app + lifespan + 14 路由挂载
│   ├── config.py                 #   YAML 加载 + env 替换 + 全局 get_config()
│   ├── database.py               #   SQLAlchemy engine + get_db + get_session_maker
│   ├── models.py                 #   19 张表的 ORM 定义
│   ├── schemas.py                #   Pydantic 入参/出参 (含 validation_warnings)
│   ├── routers/                  #   14 个路由 (见 §6 浏览器入口)
│   └── services/                 #   11+ 个服务模块 (见 §7 模块依赖图)
├── config/app.yaml               # 配置 (端口/DeepSeek/TTS URL/HF 路径)
├── data/pipeline.db              # SQLite 自动建表产物
├── web/                          # 前端 SPA (见 §6)
├── workflows/                    # ComfyUI workflow JSON (见 §8)
├── tests/artifacts/              # TTS 测试 wav (idx_fresh_test_v[1-4].wav)
├── assets/                       # 静态素材 (头像/分镜)
├── crawler/                      # 旧爬虫代码 (M0 遗留)
├── scripts/tts_client.py         # TTS 客户端 (voices router 引用)
├── logs/                         # 运行日志
├── outputs/                      # 临时输出
├── run_web.py                    # 主入口
└── requirements.txt              # Python 依赖
```

---

## 6. 浏览器入口清单

| URL | 后端路由 | 作用 |
|---|---|---|
| [`/web/index.html`](web/index.html) | (主 SPA) | **新闻线索**: 文章输入 + 素材包 (多源聚合/七层审计/智谱补搜) |
| [`/web/writing.html`](web/writing.html) | `/api/articles/*` + `/api/scripts/*` | **文字加工中心**: 洗稿/修正/爆品改造/字数统计 |
| [`/web/audio.html`](web/audio.html) | `/api/audio/*` | **音频加工中心**: 段落选择 + TTS + 一键成片 |
| [`/web/director.html`](web/director.html) | `/api/director/*` | 导演控制台 (规划→执行→合成→下载) |
| [`/web/library.html`](web/library.html) | `/api/library/*` | 视频库 (素材库 + 成品库) |
| [`/web/templates.html`](web/templates.html) | `/api/articles/prompt-templates` | 提示词模板管理 |
| [`/web/personas.html`](web/personas.html) | `/api/personas/*` | 人物管理 (模板+音色+形象 三维绑定) |
| [`/web/voices.html`](web/voices.html) | `/api/voices` | 音色管理 (CRUD + 测试 + 试听) |
| [`/web/roles.html`](web/roles.html) | `/api/roles` + `/api/comfyui` | 角色管理 + ComfyUI 三视图生成 |
| [`/web/digital_human_video.html`](web/digital_human_video.html) | `/api/dhv/*` | DHV 数字人视频生成 (LTX23 管线) |
| [`/web/visual_render.html`](web/visual_render.html) | `/api/visual-render/*` | HF 视觉渲染 (新闻数据图) |
| [`/openapi.json`](http://127.0.0.1:54321/openapi.json) | - | 自动生成 API 文档 (Swagger) |
| 导航栏入口 | (在 `web/index.html`) | 顶部 3 链接导航 (全站 9 页统一: 写稿/音频/导演台) |

**后端路由清单** (15 个 router 模块, 全在 `app/routers/`, 其中 `director_routes/` 为 director 子包):
- `articles.py` — 文章 CRUD + DeepSeek 洗稿 (含解构 `POST /{id}/deconstruct`) + 提示词模板管理
- `materials.py` — 素材包 (七层审计 + 智谱补搜, 8 端点, SSE 后台线程)
- `scripts.py` — 脚本 + 分段 CRUD (编辑标 stale + P5 情绪重跑)
- `audio.py` — TTS 配音任务 (含聚合 + stale 清理)
- `voices.py` — 音色管理 + TTS 引擎测试
- `roles.py` — 角色管理 + ComfyUI 视图生成
- `comfyui.py` — ComfyUI workflow 同步 + 直提交
- `digital_human_video.py` — DHV 主链路 (8 端点)
- `visual_render.py` — HF 视觉渲染 (8 端点)
- `director.py` + `director_routes/` — 视觉导演 2.0 (planning/execution/compose/retry, 含 `replace-material` 与单 slot `preview`)
- `library.py` — 视频库 (素材 CRUD+搜索+标签+赞 / 成品 CRUD)
- `personas.py` — 人物关联 (模板+音色+形象, 含 `by-template` 音色锁)
- `tagging.py` — 素材 AI 打标
- `tts_services.py` — TTS 服务管理
- `hosts.py` / `jobs.py` — 主持人管理 + 任务状态 SSE 流

---

## 7. 模块依赖图

**核心依赖链** (谁 import 谁):

```
main.py
 ├─ config.{Config,load_config,set_config}
 ├─ database.{init_db,get_session_maker}
 ├─ models.{Host,Voice}
 ├─ services.workflow_sync.sync_workflows_on_startup
 └─ routers.*  ←── 15 个全部挂载

routers/digital_human_video.py (DHV 主链路)
 ├─ config.get_config
 ├─ services.audio_aggregator.aggregate_segments     # 多 wav 拼接 + 重采样
 ├─ services.lit_video_builder.build_ltx23_video_workflow  # Hermes 修复版 JSON + 改 4 字段
 ├─ services.video_validator.validate_mp4           # 7 项硬校验 (流/帧/时长/对齐)
 └─ models.{AudioFile,DigitalHumanVideo,Role}

routers/visual_render.py (HF 视觉渲染)
 ├─ config.get_config
 ├─ services.template_library.{list,get,resolve,validate}_input
 ├─ services.template_filler.fill_template          # 占位符替换 + 复制模板
 ├─ services.visual_render_service.execute_visual_render_job  # 5 步编排 (preparing → rendering → validating)
 └─ models.VisualRenderJob

routers/articles.py (文章 + 洗稿)
 ├─ config.get_config
 ├─ services.llm_service.LLMService   # DeepSeek 调用
 └─ services.boost_service            # 爆品改造 P4→P5 (解构伪评论 + 素材包注入)

routers/materials.py (素材包)
 ├─ services.material_service         # 七层审计 / 精选制注入块 / URL 批量抓取
 └─ services.zhipu_search             # 智谱 web_search (免费额度 2026-09-12 到期硬拦截)

routers/audio.py (TTS 配音)
 ├─ config.get_config
 └─ services.tts_service              # emotion_annotations → IndexTTS 情绪参数
```

**全部模块** 用 `config.get_config`(模块级 singleton);`main.py` 只导出 `Config / load_config / set_config`,没有 `get_config`。路由模块只能从 `..config` 取,不能从 `..main` 取。

---

## 8. 数据库表 + 写入方

**位置**: `data/pipeline.db` (SQLite,自动建表于首次启动)

| 表 | 写入方 (服务/router) | 用途 |
|---|---|---|
| `hosts` | `routers/hosts.py` | 主持人元数据 (persona/开场白/默认音色) |
| `voices` | `routers/voices.py` | 音色 CRUD (master_audio + backend URLs) |
| `articles` | `routers/articles.py` | 文章 + raw_text + status + deconstruct_json (评论层) |
| `scripts` | `routers/articles.py` (rewrite 后) | 洗稿脚本 (+ emotion_annotations / material_package_id / prompt_template) |
| `material_packages` | `routers/materials.py` + `services/material_service.py` | 素材包 (status: collecting→audited/failed, audit_json 七层审计) |
| `material_items` | `services/material_service.py` | 素材条目 (source_type: url/manual/search, layer_tags 审计回填) |
| `segments` | `routers/scripts.py` | 脚本分段 (line_index + control_chars) |
| `crawl_tasks` | (旧爬虫) | 抓取任务 (M0 遗留) |
| `audio_jobs` | `routers/audio.py` | TTS 任务 |
| `audio_files` | `routers/audio.py` | TTS 产物 wav |
| `roles` | `routers/roles.py` | 数字人角色 (含 views 多视角) |
| `workflow_syncs` | `services/workflow_sync.py` (启动时) | ComfyUI workflow SHA256 同步状态 |
| `digital_human_videos` | `routers/digital_human_video.py` | DHV 任务 (status: pending→aggregating→running→completed/failed) |
| `visual_render_jobs` | `routers/visual_render.py` | HF 渲染任务 (queued→preparing→rendering→validating→completed) |
| `director_jobs` | `routers/director.py` | 导演任务 (planning→executing→reviewing→completed/failed) |
| `director_slots` | `routers/director.py` | 导演 slot (queued→running→completed/failed/replaced) |
| `material_assets` | `services/pexels_service.py` | Pexels 素材本地缓存 (旧表, 逐步迁移到 video_assets) |
| `download_logs` | `services/pexels_service.py` | Pexels 下载配额审计 |
| `personas` | `routers/personas.py` | 人物关联 (模板+音色+形象 三维绑定) |
| `video_assets` | `routers/library.py` + `services/pexels_service.py` | 素材库 (Pexels 下载自动入库) |
| `video_outputs` | `routers/director.py` (compose 后) | 成品库 (合成自动登记) |

---

## 9. 关键 ComfyUI Workflows

源目录: [`workflows/`](workflows/),通过 `workflow_sync.sync_workflows_on_startup` 自动同步到 `E:/AI/ComfyUI_windows_portable/ComfyUI/user/default/workflows/`。

| workflow | 文件 | 用途 |
|---|---|---|
| `character_three_view` | `workflows/character_three_view.json` | 角色多视图定型 (正脸/侧脸/全身,Krea2 后端) — `roles.py` 调 `submit_and_wait` |
| `digital_human_video_ltx23` | `workflows/digital_human_video_ltx23.json` | 占位/参考 JSON。**真实 workflow 由 [`app/services/lit_video_builder.py`](app/services/lit_video_builder.py) 动态构造**: 读取 Hermes 已验证 `G:/下载/LTX23-单多图数字人语音驱动_已修复最小实验.json`,仅改 4 字段 (节点 36/301/423/369) |
| `krea2_*` | `workflows/krea2_*.json` | Krea2 后端多模板 (cyber/gufeng/body/face) — 角色图像生成实验用 |

**HF 视觉渲染独立**: 不接 ComfyUI,不占 4090。HyperFrames CLI 在 `E:/AI/digital_human/hf_prep/test_demo/` 项目目录跑。

---

## 10. 扩展指南

> 本节只列扩展位和方向,不写实现。具体改动落点见 [项目进度看板.md](项目进度看板.md)。

**新加 TTS 后端**: `app/services/tts_service.py` 加新 backend;`config/app.yaml:defaults` 加 `base_url_*`;`voices.backend` 字段加枚举。

**新加 ComfyUI workflow**: `workflows/<name>.json` + `workflows/manifest.yaml` 加条目 + `app/services/workflow_sync.py` 自动同步。

**新加 DHV workflow 节点字段**: 改 `app/services/lit_video_builder.py::build_ltx23_video_workflow` 的节点 ID 映射 (`36/301/423/369` 是当前 Hermes 已验证版)。

**新加 HF 模板**: `app/services/template_library.TEMPLATES` 加条目,其它不动 (router/service 自动适配)。

**新加前端页**: `web/<page>.html` + `app/routers/<page>.py` + `app/main.py:include_router` + `web/index.html:45` 加导航链接。

**新加数据库表**: `app/models.py` 加 ORM 类,启动时 `Base.metadata.create_all` 自动建表。

---

**报告完**。任何"这是干什么 / 进度如何 / 待办是什么" → 看另外 3 个 MD。本文件只回答"代码怎么搭、怎么跑、怎么改"。
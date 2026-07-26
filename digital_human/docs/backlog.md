# 数字人项目需求池（Backlog）

> 统一记录待开发需求，避免散落在对话中。每个需求条目包含：描述、动机、优先级、预计开发周期、相关文件/模块。
> 本文件随项目演进持续更新，开发结束后统一梳理、分周期排期。

---

## 需求模板

新增需求时按以下格式追加：

```markdown
### ID-XXX：需求标题

- **状态**: pending / in_progress / done / deferred
- **优先级**: P0 / P1 / P2 / P3
- **提出时间**: YYYY-MM-DD
- **开发周期**: M0 / M1 / M2 / 待定
- **描述**: ...
- **动机/背景**: ...
- **涉及模块**: ...
- **备注**: ...
```

---

## 需求列表

### ID-001：URL 自动抓取标题和正文

- **状态**: pending
- **优先级**: P1
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  在 Web UI 的原始文章输入区，用户直接粘贴头条等新闻 URL，后端自动抓取页面标题和正文，并自动填入标题、URL、原文内容字段。
- **动机/背景**:
  未来爬虫接入时，系统只会拿到标题和 URL，不会拿到全文。运营/审核人员需要仅凭标题决定是否保留该新闻，然后由系统自动抓取正文用于后续洗稿，无需人工打开原链接复制粘贴。
- **涉及模块**:
  - 后端：`app/routers/articles.py` 新增 `POST /api/articles/fetch-url`
  - 后端：复用/扩展 `crawler/api_fetcher.py` 的 HTTP 抓取能力
  - 前端：`web/index.html` 增加「抓取 URL」按钮，`web/app.js` 调用新接口
- **备注**:
  - 今日头条有反爬，需要配置合理的 Headers（UA、Referer 等）。
  - 建议实现分层解析：先尝试站点特定规则（头条），再回退到通用 meta/paragraph 提取。
  - 抓取失败时前端给出明确提示，不阻塞用户手动粘贴。

### ID-002：视觉导演 Agent 2.0 接口与数据库落地

- **状态**: pending
- **优先级**: P1
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  将已沉淀的 `config/visual_director_v2.txt` 提示词接入系统：在脚本生成后，调用 DeepSeek Pro 生成每句口播的画面指令 JSON（出镜/素材/混合），并持久化到数据库，供下游剪辑程序使用。
- **动机/背景**:
  视觉导演是架构中的 Agent 2，承上启下。当前提示词已写好，但缺少调用接口、数据表、与素材库的联动。
- **涉及模块**:
  - 后端：新增 `app/services/director_service.py`
  - 后端：新增 `app/models.py` 表 `video_directives` 或扩展 `segments` 表
  - 后端：`app/routers/scripts.py` 新增 `POST /api/scripts/{id}/direct`
  - 配置：`config/app.yaml` 增加 director 模型配置
  - 素材库：本地素材目录索引（ prerequisite，见 ID-003）
- **备注**:
  - 素材库未建设前，可用最小化清单或全部回退到“出镜”做端到端测试。

### ID-003：本地素材库目录索引

- **状态**: pending
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  建立本地素材目录结构（如 `materials/港口/`、`materials/工厂/`），并提供扫描/索引接口，生成视觉导演提示词所需的素材库清单 JSON。
- **动机/背景**:
  视觉导演需要基于真实存在的素材做决策，不能臆想。素材库是 ID-002 的前置条件。
- **涉及模块**:
  - 目录结构：`digital_human/materials/`
  - 后端：新增 `app/services/material_service.py` 扫描目录、读取 tags
  - 后端：`app/routers/` 增加素材清单读取接口
  - 配置：`config/app.yaml` 增加 `materials_dir`
- **备注**:
  - 可以先按文件夹名作为 category，文件名作为 file，tags 从文件名或同目录 `.meta.json` 读取。

### ID-004：动态素材 / HyperFrames / ComfyUI 渲染链路

- **状态**: pending
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 待定（M2 以后）
- **描述**:
  根据视觉导演输出的 dynamic 类型指令，调用 HyperFrames 或 ComfyUI 生成动态数据图表、地图高亮等素材。
- **动机/背景**:
  实现“数据图表”类 dynamic 素材的自动渲染，减少对静态素材的依赖。
- **涉及模块**:
  - 后端：新增 `app/services/render_service.py`
  - 后端：新增 render task 表
  - 配置：HyperFrames / ComfyUI API 地址
- **备注**:
  - 需要 ID-002 视觉导演输出 render_config。

### ID-005：视频合成（剪辑）引擎

- **状态**: pending
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 待定（M2 以后）
- **描述**:
  将音频（WAV + manifest）、数字人出镜画面、素材画面/动态素材按时间轴合成最终短视频。
- **动机/背景**:
  最终产出物是完整视频，当前只到音频阶段。
- **涉及模块**:
  - 后端：新增 `app/services/composition_service.py`
  - 后端：新增 composition job 表
  - 外部：ComfyUI 数字人工作流 / FFmpeg 合成
- **备注**:
  - 依赖 ID-002、ID-003、ID-004。

### ID-006：爬虫自动写入 articles 表

- **状态**: pending
- **优先级**: P1
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  将现有 `crawler/` 模块接入后端，定时或手动触发抓取热点新闻，并直接写入 `articles` 表，状态为 `pending`，供后续人工/自动选择是否洗稿。
- **动机/背景**:
  项目目标之一是自动化新闻获取，当前爬虫是独立脚本，未与数据库打通。
- **涉及模块**:
  - 后端：`app/routers/articles.py` 新增 `POST /api/articles/crawl` 或独立 router
  - 后端：复用 `crawler/news_scraper.py`、`hot_news_detector.py`
  - 数据库：`crawl_tasks` 表已预留
- **备注**:
  - 可先实现手动触发抓取，再扩展为定时任务。
  - 抓取结果只需标题、URL、摘要，正文通过 ID-001 的 URL 抓取在洗稿前补充。

### ID-007：批量导演选择 / 拖拽排序 UI

- **状态**: pending
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  优化当前分段列表：支持拖拽调整 `host_order`，支持批量勾选/取消 `selected_for_host`，显示 segment_type 和 estimated_duration。
- **动机/背景**:
  导演环节需要从 ~42 句中挑选 5-8 句，当前简单 checkbox 不够用。
- **涉及模块**:
  - 前端：`web/index.html`、`web/app.js`
  - 后端：已有 `PUT /api/segments/{id}` 和 `POST /api/scripts/{id}/segments/reorder`
- **备注**:
  - 可在 ID-002 之前先做，当前 segments 表已预留字段。

### ID-008：Web UI 模型选择开关

- **状态**: pending
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 待定
- **描述**:
  在洗稿按钮附近增加模型选择开关（flash / pro），前端传 `model` 字段到 `/api/articles/{id}/rewrite`。
- **动机/背景**:
  后端已支持 `RewriteRequest.model`，但前端默认不传，总是走 `default_model`。
- **涉及模块**:
  - 前端：`web/index.html`、`web/app.js`
- **备注**:
  - 简单改动，可快速完成。

---

## 已完成的关联需求

- ✅ DeepSeek key 与双模型别名配置（`flash` / `pro`）
- ✅ 洗稿接口支持 `model` 和 `prompt_template`
- ✅ 视觉导演 Agent 2.0 提示词沉淀（`config/visual_director_v2.txt`）
- ✅ DeepSeek V4 双模型使用指南（`docs/deepseek_v4_model_guide.md`）

---

## 排期建议（待用户确认）

### 近期（当前周期可推进）
1. ID-001：URL 自动抓取
2. ID-008：前端模型选择开关
3. ID-007：导演选择 UI 优化

### 中期（素材库建设后）
4. ID-003：本地素材库索引
5. ID-002：视觉导演 Agent 2.0 接口
6. ID-006：爬虫接入 articles 表

### 远期（M2 以后）
7. ID-004：动态素材渲染
8. ID-005：视频合成引擎

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

- **状态**: done
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

- **状态**: done（2026-08-01 全阶段完成）
- **优先级**: P1
- **提出时间**: 2026-07-25
- **开发周期**: 2026-07-27 ~ 2026-08-01
- **描述**:
  视觉导演作为"大 Agent"，在整段 TTS 音频生成后，基于 Whisper 文本-音频对齐得到的真实时间轴，输出按时间槽位（slot）组织的画面工序单；每个 slot 由下游小 Agent/工作流（host / broll_pexels / broll_local / hf_chart / hf_title / mixed_host_broll）独立执行；导演负责审核 slot 状态并在失败时自动替换，最终所有 slot 产物交给合成引擎拼接为 9:16 短视频。
- **动机/背景**:
  视觉导演是架构中的 Agent 2，承上启下。原 ID-007 "选句子 UI" 被确认为占位设计，现废弃；导演直接基于音频时间轴做决策，更符合短视频剪辑节奏。
- **涉及模块**:
  - 后端：新增 `app/services/director_service.py`（大导演 Agent）
  - 后端：新增 `app/services/alignment_service.py`（Whisper 文本-音频对齐）
  - 后端：新增 `app/services/slot_executor.py`（slot 分发执行 + 失败替换）
  - 后端：新增 `app/services/composition_service.py`（最终合成，预留接口）
  - 后端：新增 `app/routers/director.py`（导演任务 CRUD + 触发端点）
  - 后端：新增 `app/models.py` 表 `director_jobs` / `director_slots`
  - 后端：`app/schemas.py` 新增对应 Pydantic schemas
  - 配置：`config/app.yaml` 增加 director / alignment 配置
  - 素材库：ID-003 Pexels resolve 服务（本次先用 mock/硬编码最小清单跑通 ID-002）
- **开发计划**:
  - 见 `docs/improvements/已完成-20260727-ID002-视觉导演Agent2.md`
- **备注**:
  - 素材库未建设前，用最小化 mock 清单或全部回退到 "host" 做端到端测试。
  - 原 ID-007 "选句子 UI" 废弃，保留字段兼容旧数据。

### ID-003：Pexels 素材 resolve 服务模块（"本地有就复用、没有就下载"，2026-07-27 重写）

- **状态**: done
- **优先级**: P2
- **提出时间**: 2026-07-25（2026-07-27 重写为 resolve 服务）
- **开发周期**: 待定
- **描述**:
  给视觉导演（ID-002）一个 **"query in / 路径 out"** 的 Python 服务模块，**类似本地 LLM 兼容接口**。和 DeepSeek 一个范式——Pexels 本身有公开 API + key，**不需要在本地 54321 再架一层 HTTP 中间层**。核心语义：
  > **本地有就复用，本地没有就下载，下载不到就返元数据 + 标记 degraded。**
  
  - 工具对调用方（视觉导演 / 后续脚本）**完全透明**，调用方只传 `query`（任意字符串），不关心"本地 vs Pexels"细节
  - **不**做 HTTP router（54321 不加 `materials.py` 端点），**不**做 web/materials.html 前端页面
  - 外部系统（爬虫 / 独立视频合成器）**直接调 Pexels 官方 API**：`curl -H "Authorization: <key>" "https://api.pexels.com/v1/videos/search?query=..."`，**不**走 54321
  - **不**预设关键词白名单（白名单是反模式：限制导演创造力；"高频 vs 冷门"运行时按"本地有没有"自然解决）
  - **每天下载配额**（`pexels_daily_download_quota=200`）：超限后 resolve 仅返回元数据（不入本地），由调用方决定是否接受
- **动机/背景**:
  - 视觉导演根据脚本生成 query → 需要立刻拿到 B-Roll 视频
  - 原"本地累积 mp4"方案要用户每周手工搜素材，违反"自动化是最终目标"原则
  - 关键词白名单是反模式：调用方要的就是"任意 query 都能搜"，白名单限制创作
  - Pexels 提供免费商用视频素材（free tier 200 req/hour + 20000 req/month），免版权风险
  - **关键认知**：这是个 **Python 服务模块**（视觉导演 import 调用），**不是** HTTP 端点；外部系统直接调 Pexels 官方 API，**不需要**中间层
- **调用方式**:
  ```python
  # 视觉导演脚本（同一进程，import 调用）
  from app.services.pexels_service import pexels_service
  
  materials = pexels_service.resolve(
      query="port cranes at night",
      max_results=3,
      min_duration_sec=5,
  )
  # 行为:
  #   1. 查本地 DB: SELECT FROM material_assets WHERE tags LIKE %query% AND duration >= 5
  #   2. 本地够 max_results 条 → 直接返回本地路径（零网络）
  #   3. 本地不够 → 调 Pexels search，按 (FHD → HD) 顺序下载缺失条数
  #   4. 当天下载已达 pexels_daily_download_quota → 仅返回元数据，不下本地，标记 degraded
  #   5. 全部失败 → 返空 + 标记 degraded
  
  # 外部系统（跨进程，直接调 Pexels 官方 API）
  curl -H "Authorization: $PEXELS_API_KEY" \
       "https://api.pexels.com/v1/videos/search?query=port&per_page=5"
  ```
- **涉及模块**:
  - **敏感配置**：`.env` 写 `PEXELS_API_KEY`（**不**进 git，`.gitignore` 已含 `.env`），`config/app.yaml` 用 `pexels_api_key_env` 字段从 `os.environ` 读取
  - **配置**：`config/app.yaml` Defaults 块加 `materials_dir` / `pexels_daily_download_quota` / `pexels_default_max_results` / `pexels_min_duration_sec` / `pexels_preferred_resolution`
  - **后端（新增）**：`app/services/pexels_service.py`（search / download / quota 计数 / DB 落盘 / 缩略图 / resolve 编排）
  - **后端（修改）**：`app/models.py` 新增 `MaterialAsset` 表（id/pexels_id/source_url/photographer/photographer_url/local_path/duration_sec/width/height/fps/tags/created_at）+ `DownloadLog` 表（date/pexels_id/bytes/quota_used）
  - **后端（修改）**：`app/schemas.py` 加 Pydantic（`MaterialAssetOut` / `ResolveRequest` / `ResolveResponse` / `ResolveItem`）
  - **接 ID-002**：视觉导演接 `pexels_service.resolve(query)`（单接口，import 调用）
  - **合规 SOP**：新增 `sop/Pexels素材合规.md`，强制每素材存 `photographer + photographer_url`；合成导出版必显示 "Footage by {photographer} on Pexels"
  - **不**新增 `app/routers/materials.py`（**不**做 HTTP 端点）
  - **不**新增 `web/materials.html`（**不**做 web UI）
  - **不**改 `app/main.py`（无 router 要注册）
- **备注**:
  - Pexels 强制要求展示链接和摄影师署名（API Guidelines）
  - **不**引入关键词白名单（"高频 vs 冷门"由"本地有没有"自然解决）
  - quota 计数持久化（重启不丢），按"自然日"重置
  - 测试验证（2026-07-27 已实测）：搜 `port` → 找到 FHD 1920x1080 25fps mp4 → HEAD 验证 57.66 MB → 下载 4.8 MB/s → ffprobe 校验 h264 真视频
  - **架构关键**：Pexels 工具是**本地服务模块**，**不是**云端服务；外部系统需要时**直接调 Pexels 官方 API**（类似 DeepSeek 调用方式）

### ID-004：动态素材 / HyperFrames / ComfyUI 渲染链路

- **状态**: done（2026-08-03，HF/hf_title/hf_chart 渲染链已投入生产，visual_render_service + template_filler 运营中）
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 2026-07-26 ~ 2026-08-03
- **描述**:
  根据视觉导演输出的 dynamic 类型指令，调用 HyperFrames 或 ComfyUI 生成动态数据图表、地图高亮等素材。
- **动机/背景**:
  实现”数据图表”类 dynamic 素材的自动渲染，减少对静态素材的依赖。
- **涉及模块**:
  - 后端：`app/services/visual_render_service.py`（HF 渲染编排 + 归一化 wrapper）
  - 后端：`app/services/template_filler.py`（26-key 白名单占位符替换）
  - 后端：`app/services/slot_workflows.py`（hf_chart/hf_title slot workflow）
  - 后端：`app/models.py` VisualRenderJob 表
  - 配置：HyperFrames / ComfyUI API 地址
- **备注**:
  - 已跑通 hf_title（标题卡）和 hf_chart（图表卡）两类 dynamic 素材（ID-028 模板修复）。
  - 2026-08-03 导演生产路径优化 v3 中 HF 产物加归一化 wrapper（48kHz 静音轨注入），确保 concat 兼容。

### ID-005：视频合成（剪辑）引擎

- **状态**: done（2026-08-03，composition_service 全链路跑通 + v3 零拷贝优化完成）
- **优先级**: P2
- **提出时间**: 2026-07-25
- **开发周期**: 2026-07-27 ~ 2026-08-03
- **描述**:
  将音频（WAV + manifest）、数字人出镜画面、素材画面/动态素材按时间轴合成最终短视频。
- **动机/背景**:
  最终产出物是完整视频，当前只到音频阶段。
- **涉及模块**:
  - 后端：`app/services/composition_service.py`（concat copy + loudnorm + slot 素材保留策略）  - 后端：director.py compose 端点（异步后台线程 + SSE 进度透传）
  - 外部：ComfyUI 数字人工作流 / FFmpeg 合成
- **备注**:
  - 依赖 ID-002、ID-003、ID-004（均已 done）。
  - 2026-08-03 v3 优化：零拷贝流水线（`-c copy` concat 无需预归一化）、os.replace 替代 copy2、48kHz 音频统一。
  - 2026-08-07 素材生命周期策略升级：不再「合成后自动清理 slots/」，slot 素材默认保留 `slot_retention_days`（默认 7 天），超期由 `main.py` 保留扫描回收（留成片）；删除 slots/ 唯二出口 = 用户删 job / 保留扫描（详见 [已完成-20260807-素材生命周期保留策略.md](improvements/已完成-20260807-素材生命周期保留策略.md)）。

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

- **状态**: done（功能已废弃，保留字段兼容旧数据）
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
  - 2026-07-27 重新讨论后，确认"选句子 UI"为占位设计的占位设计，导演到位后不再必要。代码保留但不作为 ID-002 强依赖。

### ID-008：Web UI 模型选择开关

- **状态**: done
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

### ID-009：【BUG】导演台任务跑到“执行 Slots”阶段后服务死掉

- **状态**: done
- **优先级**: P0
- **提出时间**: 2026-07-29
- **开发周期**: 2026-07-29 ~ 2026-07-30
- **描述**:
  流水线→导演台自动衔接后，任务推进到“执行 Slots”阶段时服务死掉。
- **修复记录**:
  - 2026-07-29：`slot_executor.py` Phase 调度重构 + ComfyUI 纳入 GPU 托管
  - 2026-07-30：大文件上传修复（BaseHTTPMiddleware → ASGI）、HF 渲染死锁修复（Popen + taskkill /F /T）、GPU 服务失败优雅降级、Host–Persona–Role 关联链修复、replaced 状态不再被重复执行、僵尸 executing 状态检测
- **涉及模块**:
  - `app/services/slot_executor.py`（Phase 调度）
  - `app/services/gpu_service_manager.py`（comfyui session）
  - `app/routers/director.py`（execute 端点）
- **备注**:
  - 2026-07-30 修复完成。

### ID-010：【UI】导演台 Slot 时间轴横向溢出 + 页面布局偏移

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-07-29
- **开发周期**: 2026-07-30
- **描述**:
  导演台显示 Slot 时间轴后，39 个 slot 卡片横向排列超出页面宽度，没有水平滚动条，导致页面严重右偏。
- **修复记录**:
  - 2026-07-30：时间轴容器加水平滚动 + Workflow 类型中文化
- **涉及模块**: `web/director.html`（Slot 时间轴 CSS 布局）
- **备注**: 2026-07-30 修复完成。

### ID-011：【UI】导演台 SSE 日志升级为 Phase 业务流可视化

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-07-29
- **开发周期**: 2026-07-30
- **描述**:
  当前导演台左侧 SSE 信息流是扁平的日志行，无法快速看出“当前在跑哪个大步骤的哪个小步骤”。
  需要按 Phase 调度模型重新规划 SSE 展示。
- **修复记录**:
  - 2026-07-30：后端 SSE 事件增加 `phase` / `step` / `service_lifecycle` 字段，前端渲染改为层级树状展示
- **涉及模块**:
  - 后端：`app/routers/director.py` SSE 事件
  - 后端：`app/services/slot_executor.py` yield 结构化事件
  - 前端：`web/director.js` SSE 渲染逻辑
- **备注**: 2026-07-30 修复完成。

---

### ID-012：【BUG】导演台 SSE 执行日志面板始终为空

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-07-30
- **开发周期**: 2026-07-30 ~ 2026-07-31
- **描述**:
  点击"执行 Slots"后，SSE 日志面板不可见/始终为空。
- **修复记录**:
  - 2026-07-30：SSE 连接修复，日志能正常接收和渲染
  - 2026-07-31：执行日志从 grid 内部提升为 body 级固定底部抽屉（`position: fixed; bottom: 0; height: 260px; z-index: 200`）+ `_sseCollapseTimer` 定时器管理（仅 terminal 事件后 3s 自动收起）
  - 2026-07-31（续）：`showExecLog()`/`clearExecLog()` DOM 修复（`innerHTML=''` 改为 `pre.textContent=''`），避免销毁 `<pre id="exec-log-pre">` 导致 SSE 事件全部静默丢弃
- **涉及模块**:
  - 前端：`web/director.js` `connectSSE` / `appendExecEvent` / `_sseCollapseTimer` / `showExecLog` / `clearExecLog`
  - 前端：`web/director.css` exec-log 固定抽屉
  - 前端：`web/director.html` exec-log 移到 body 末尾
  - 后端：`app/routers/director.py` SSE events 端点
- **备注**: 2026-07-31 修复完成。

### ID-013：【BUG】数字人出镜次数远超硬约束（最多4次）

- **状态**: done
- **优先级**: P0
- **提出时间**: 2026-07-30
- **修复时间**: 2026-07-31
- **开发周期**: 2026-07-31
- **描述**:
  约束规则：一个视频中数字人（host）最多出现 4 次。但实际执行时 ComfyUI 连续生成了 17+ 个 host slot 视频片段，远超硬约束。
- **根因分析**:
  1. LLM 导演规划阶段（`visual_director_v2.txt` 提示词）虽然写了“数字人最多 4 段”，但 LLM 未严格遵守
  2. 执行阶段 `slot_executor.py` 在 Phase 1 开始前临时把超出的 host slot 降级为 broll_pexels，给用户的感觉是“还没执行就降级”
  3. parser 层 `cap_host_count` 只统计 `host`，没把 `mixed_host_broll` 也算作出镜，导致实际出镜数仍可能超上限
- **修复记录**:
  - `app/services/director_parser.py`：`cap_host_count` 把 `host` + `mixed_host_broll` 合并计为 host-family，超出时按比例保留（首尾必须保留），剩余在**规划阶段**降级为 `broll_pexels`
  - `config/visual_director_v2.txt`：明确“`host` + `mixed_host_broll` 合计硬上限 4 个，超过执行层会强制截断”
  - `app/services/slot_executor.py`：移除执行前静默降级逻辑，改为防御性 warning；若仍超上限则仅记录日志并向前端发送 `plan_warning`，不再修改 slot
  - `web/director.js`：新增 `plan_warning` 事件渲染（黄色 ⚠ 前缀）
- **涉及模块**:
  - `app/services/slot_executor.py`
  - `app/services/director_parser.py`
  - `config/visual_director_v2.txt`
  - `web/director.js`
- **备注**: 本次修复与 ID-012 同批次验证。

### ID-014：【BUG】停止按钮无法中断正在执行的 ComfyUI prompt

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-07-30
- **开发周期**: 2026-07-30
- **描述**:
  点击「■ 停止」按钮后，前端显示“已发送停止信号”，但 ComfyUI 正在跑的 prompt 不会停下来。
- **修复记录**:
  - 2026-07-30：`poll_comfyui_and_collect` 每次轮询检查 `_is_cancelled(job_id)`，若取消则向 ComfyUI 发 `POST /interrupt` 并抛异常；`_run_phase` 每个 slot 执行前检查取消标志
- **涉及模块**:
  - `app/services/slot_workflows.py`（poll_comfyui_and_collect 加取消检查）
  - `app/services/slot_executor.py`（_run_phase slot 级别检查）
- **备注**: 2026-07-30 修复完成。

---

### ID-015：【优化】ComfyUI 输入图质检与预处理

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  视觉导演 host / mixed_host_broll 槽位进入 ComfyUI 前，对 storyboard 输入图做统一质检：超大图缩放、格式转 PNG、RGBA 白底压平、文件大小告警，避免手机原图/PNG 炸弹拖慢 LTX23 VAE encode。
- **修复记录**:
  - `app/services/slot_workflows.py`：新增 `prepare_comfyui_storyboard()`，默认源图像素上限 2MP、文件大小告警 10MB，输出统一 PNG；对目标比例偏差 >5% 的图做白底 pad
  - `execute_host_slot`：复制进 ComfyUI input 前先走 `prepare_comfyui_storyboard`
- **涉及模块**:
  - `app/services/slot_workflows.py`
- **备注**: 与 ID-013 同批次验证。

### ID-016：【BUG】TTS 文生音频句内截断

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  多行文本合并成 batch 合成后，FFmpeg silence detect 把句内逗号/短停顿误判为行间边界，导致一句话被截成两段音频。
- **修复记录**:
  - `app/services/tts_service.py`：`synthesize_lines` 传入 `batch_max_chars=150`，减小单批字符数
  - `scripts/tts_client.py`：`_merge_lines_for_batch` 超长单行独立成 batch；`_split_wav_by_silence` 静音过滤阈值从 0s 提升到 0.25s，snap 容差从 `max(0.9, 0.35*avg)` 收紧到 `max(0.45, 0.22*avg)`
- **涉及模块**:
  - `app/services/tts_service.py`
  - `scripts/tts_client.py`
- **备注**: 待合成长文本实测验证。

### ID-017：【BUG】library.html 页面无法播放视频

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  素材库/成品库页面视频卡片使用 `<video>` 标签渲染，但缺少播放控件和点击交互，导致用户无法播放视频。
- **修复记录**:
  - `web/library.js`：素材/成品卡片统一添加 `controls playsinline`、播放遮罩层、点击播放/暂停；播放一个视频时自动暂停其他视频
  - `web/library.css`：新增 `.play-overlay`、`.play-icon`、`.playing` 状态样式，优化 controls 栏背景
  - `app/routers/library.py`：`/assets/{id}/file` 与 `/outputs/{id}/file` 改为 inline `FileResponse`，自动识别 MIME 类型（video/mp4/webm 等），支持浏览器 range 请求
- **涉及模块**:
  - `web/library.js`
  - `web/library.css`
  - `app/routers/library.py`
- **备注**: 与 ID-015、ID-016 同批次验证。

---

### ID-018：【优化】导演台 SSE 长静默阶段心跳升级

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台 SSE 日志面板在规划阶段（Whisper 首次加载约 70s）和执行阶段（ComfyUI 单 slot 2–5min）长时间无可见更新，用户容易误判为卡死。
- **修复记录**:
  - `app/routers/director.py`：SSE 保活从浏览器不可见的 `: keep-alive\n\n` comment 改为 `heartbeat` 事件，20s 无事件自动推送，携带已等待秒数
  - `app/services/alignment_service.py`：`_ensure_model` 模型加载期间每 5s 发送 `alignment_heartbeat`，直到加载完成
  - `app/services/slot_workflows.py`：`poll_comfyui_and_collect` 每 10s 发送 `slot_progress` 心跳，携带已运行秒数
  - `web/director.js`：`appendExecEvent` 增加 `heartbeat` / `alignment_heartbeat` / `slot_progress` 渲染，带 ⏳ 图标和等待时长
- **涉及模块**:
  - `app/routers/director.py`
  - `app/services/alignment_service.py`
  - `app/services/slot_workflows.py`
  - `web/director.js`
- **备注**: 与 ID-015、ID-016、ID-017 同批次验证。

### ID-019：【BUG】index.html 音频任务刷新/跳页后丢失

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  流水线首页在执行音频生成任务时，刷新页面或跳转到其他页面再返回，原本正在进行的任务不再显示，用户无法继续观察进度或下载结果。
- **修复记录**:
  - `app/routers/audio.py`：新增 `GET /api/audio/jobs?script_id=`，支持按脚本查询音频任务列表
  - `web/app.js`：`fetchScript` 后调用 `restoreAudioJobs`，自动恢复 `pending`/`running` 活跃任务并重连 SSE；同时加载最近 3 个已完成任务的历史音频文件
  - 提取 `connectAudioSSE` 公共函数，统一处理 `tts_service` / `tts_progress` / `tts_done` / `tts_error`
- **涉及模块**:
  - `app/routers/audio.py`
  - `web/app.js`
- **备注**: 与 ID-017、ID-018 同批次验证。

### ID-020：【BUG】导演台脚本无已完成音频 + 僵尸音频任务卡死

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台【快速选择脚本】选择脚本后，【快速选择音频】一直显示"该脚本无已完成音频"。根因是后端重启会杀掉 `_do_tts` 后台线程，但 DB 中 `AudioJob` 残留 `pending`/`running` → 前端 `restoreAudioJobs` 永远"恢复订阅"死任务而非新建 → 音频永不生成。
- **修复记录**:
  - `app/main.py`：lifespan 新增 `_cleanup_zombie_audio_jobs()`，重启时把残留 `pending`/`running` 复位为 `failed`（附错误原因，不删记录）；补 `AudioJob` 导入
  - `web/director.html`：【快速选择音频】区新增「🎙️ 生成音频」按钮 + 进度行
  - `web/director.js`：`loadAudioFiles` 无音频时显示按钮；新增 `regenerateAudio()`（查活跃任务→无则 `POST /api/audio/scripts/{script_id}/generate-audio?selected_only=true`，与 index.html 同一端点）+ `connectAudioGenSSE()`（复用 `/api/jobs/{job_id}/events` 的 `tts_service`/`tts_progress`/`tts_done`/`tts_error`）
- **数据修复**:
  - 5 个僵尸任务（`87c2e6e9`/`a6f3301a`/`d73c7925`/`ed57a114`/`d361662b`）复位为 `failed`，`error_message="服务重启中断 TTS 后台线程，任务失效（僵尸清理）"`
  - 33 个脚本核对结果：8 个有已完成音频，25 个无（11 个为 failed 可重试，14 个从未生成——均可在导演台一键「生成音频」重试）
- **涉及模块**:
  - `app/main.py`
  - `web/director.html`
  - `web/director.js`
- **备注**: 后端已重启（PID 23008）加载新代码，僵尸清理函数生效；fish 服务当前离线，生成需按需拉起。

### ID-021：【功能】导演台脚本删除功能（级联 + 回收站）

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台【快速选择脚本】下拉只能加载/选择脚本，没有删除/管理入口。用户需清理同稿多版本（如"中国机遇2.0" 8 版、"银行里的钱去哪了" 5 版）的冗余脚本。
- **修复记录**:
  - 后端 `app/routers/scripts.py`：新增 `DELETE /api/scripts/{script_id}`（204）—— 404 处理 → 409 阻止执行中的导演任务 → 显式删 director_jobs+slots → 收集磁盘音频路径 → 显式删 audio_files+flush（规避 Segment/AudioJob 双重 delete-orphan 冲突）→ 级联删 script → 回收站 best-effort
  - 新增模块级 `_recycle_file()`：PowerShell `Microsoft.VisualBasic.FileSystem::DeleteFile(..., 'SendToRecycleBin')` 移入回收站（`file_utils.safe_trash` 因 send2trash 未装会退化为永久删除，不可复用）
  - 前端 `web/director.html`：下拉旁新增「🗑 删除」按钮
  - 前端 `web/director.js`：`deleteScript()`（confirm → DELETE → 重置状态 → 刷新列表）+ 按钮可用态
- **数据/验证**:
  - 实测删除无音频冗余脚本 `375f8a28`（"全款买房" x5 之一）：级联 segments/audio_jobs/director_jobs/director_slots 全清，article 保留，同文其余 4 脚本保留
  - 实测删除有音频脚本 `5afb6642`（"中国机遇2.0" x8 之一）：磁盘 `000.wav` 移入 Windows 回收站（回收站核验 OrigPath 正确），DB 全清
  - 重复 DELETE → 404（幂等）
  - 删除前 DB 备份 `data/pipeline.db.bak-20260801-013547`
- **涉及模块**:
  - `app/routers/scripts.py`
  - `web/director.html`
  - `web/director.js`
- **备注**: 删除范围 = 脚本 + 所有关联音频记录 + 磁盘音频文件（回收站，可恢复）；保留 article 源文章。

### ID-022：【BUG】导演台任务状态在刷新/跳页后不可见

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台页面在执行过程中，用户刷新或跳转到其他页面再返回后，原本选中的导演任务（currentJobId 选择、进度、SSE 日志流）全部消失，回到空态。
- **根因分析**:
  1. `currentJobId` 是模块级变量，页面刷新后重置为 `null`
  2. init 只调用 `loadScripts(); refreshJobs();`，不恢复任何选中任务，也没有 localStorage 持久化
  3. 执行中的任务没有重连 SSE → 日志流丢失，用户无法继续观察进度
- **修复记录**:
  - `web/director.js` 新增 `persistCurrentJob()`：`selectJob` 时把选中任务 id 持久化到 `localStorage('director_current_job')`，删除任务时清理
  - init 新增 `restoreLastDirectorJob()` IIFE：读取持久化 id → 重新拉取详情渲染 → 按状态分支——`planning/executing/queued/reviewing` 活跃任务重连 `connectSSE` + 展开日志抽屉；`completed` 恢复视频预览/下载按钮；任务不存在则清理 localStorage 保持空态（不报错）
  - `selectJob` 手动点选活跃任务（`planning/executing/queued`）时同样重连 SSE，与刷新恢复行为一致（不含 reviewing，避免 terminal 事件后的自动调用误触发）
  - 竞态防护：URL 带 `script_id`（流水线跳转场景）时跳过恢复，交由 `handlePipelineHandoff` 处理
- **涉及模块**:
  - 前端：`web/director.js`（`selectJob` / init `restoreLastDirectorJob`）
- **备注**:
  - 后端合成期间 job.status 保持 `reviewing`（compose 端点不写 `composing` 状态），因此恢复逻辑对 `reviewing` 也重连 SSE，避免刷新后合成进度日志丢失
  - 方案参考 ID-019 `restoreAudioJobs` 模式（后端查活跃任务 + 重连 SSE）；本次为纯前端 localStorage 方案，无需后端改动
  - 已实测：规划中刷新恢复（SSE readyState=1 持续收 heartbeat/转录进度）、跳页返回恢复、手动点选重连、不存在的 job id 清理持久化不报错

### ID-023：【BUG】导演台规划期间点【停止】报 409

- **状态**: done
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台在规划阶段（`planning`，Whisper 对齐 + LLM 出工序单）点击【停止】按钮，前端显示 `取消失败: 409 job 状态为 planning，无法取消`。规划期间任务无法停止，只能等待漫长的模型加载/转录完成后才能操作。
- **根因分析**:
  1. 前端 `director.js` 停止按钮对 `planning` 也显示（`isExecuting = executing || planning`），但后端 `cancel_job` 端点只接受 `executing`，规划中点停止返回 409
  2. 规划线程 `_plan_in_background` 无取消检查点，即使取消信号已发出，Whisper 转录 / LLM 生成也不会中止
  3. **（二次发现）** `_PlanCancelled` 在 `alignment_service`、`director_service`、`director.py` 三处各自定义独立类，跨模块抛出的 sentinel 异常在 `_plan_in_background` 的 `except _PlanCancelled` 匹配不上，落到通用 except 导致 job 标记为 `create_director_plan crashed`（错误信息误导）
- **修复记录**:
  - 后端 `slot_executor.py`：新增 `clear_cancel(job_id)` / `is_cancelled(job_id)`（复用同一 `_cancel_flags` set，避免 flag 泄漏）
  - 后端 `director.py`：`cancel_job` 允许 `planning`（`status not in ("executing", "planning")` 才 409）；`_plan_in_background` 线程启动后检查取消、传入 `is_cancelled` lambda、新增 `except _PlanCancelled` 分支（job → `failed` + "规划被用户取消"，发布 `plan_cancelled` 事件）、finally 清 flag
  - 后端 `director_service.py`：`create_director_plan` 新增 `is_cancelled` 参数 + 5 个取消检查点（对齐前/对齐后、LLM 生成前/后、llm_done 后）；`except PlanCancelled: raise` 透传
  - 后端 `alignment_service.py`：`_transcribe_words` / `_match_segments` 循环内取消检查点（每 Whisper 段 / 每 20 脚本段）
  - 后端 `director_events.py`：定义共享 `PlanCancelled` sentinel，三处模块改为统一引用（修复跨模块捕获断裂）
  - 前端 `director.js`：`SSE_TERMINAL` 加入 `plan_cancelled`；`appendExecEvent` 新增 `case 'plan_cancelled'` 渲染（橙色 ⚠）
- **涉及模块**:
  - 后端：`app/routers/director.py`、`app/services/director_service.py`、`app/services/alignment_service.py`、`app/services/slot_executor.py`、`app/services/director_events.py`
  - 前端：`web/director.js`
- **备注**:
  - 实测通过：规划（Whisper 转录进行中）点【停止】→ POST /cancel 返回 200 `cancelling`（无 409）→ 转录循环检测取消 → job → `failed`「规划被用户取消」→ SSE `⚠ 用户取消，已停止规划` → 前端按钮恢复
  - 取消为**协作式**（检查点驱动），Whisper 单段转录（最长 30s）会完成后才检查，属预期

### ID-024：【优化】规划阶段跳过 Whisper，复用 TTS 段落时长秒级对齐

- **状态**: done（2026-08-01）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **开发周期**: 2026-08-01
- **描述**:
  导演台【创建并规划】最慢的步骤是 Whisper 整段转录（faster-whisper large-v3 + float32 对 ~458s 音频预估 5-15 分钟，约占规划总耗时 90%）。审计发现：TTS 生成时每 script segment 已产出独立 wav，`audio_files.duration` 存真实时长，规划根本不需要再转录一遍音频。实现「TTS 段落时长快路径」：当每个 host segment 都有对应 wav 时长时，直接累加建时间轴（跳过 faster-whisper），规划对齐阶段从分钟级降到秒级。
- **根因分析**:
  1. `create_director_plan` 无条件调用 `align_script_segments` → Whisper 整段转录（对齐的唯一途径），即使 TTS 阶段已经知道每段真实时长
  2. 数据验证：脚本 `216e3073` 85 个 host 段全部有 `audio_files.duration`，总和 458.3s ≈ 整段音频 458.31s（误差 0.01s）→ 快路径成立
- **修复记录**:
  - 后端 `alignment_service.py`：新增 `align_from_tts_durations(segments, on_event, is_cancelled)` —— 按段累加 duration 建 SegmentTiming（无 word-level，slots 按段对齐用不到），返回与 `align_script_segments` 同构 dict（`model: "tts-durations"`）
  - 后端 `director_service.py`：新增 `_collect_tts_segment_durations(db, script_id, segments)`（取最新 completed AudioJob 的 audio_files 按 segment_id 建 duration 映射，任一缺失返回 None）与 `_align_fast_or_whisper(db, audio, script_id, segments, ...)`（优先快路径，None 回退 `align_script_segments`）；`create_director_plan` 对齐调用改为 `_align_fast_or_whisper`
  - 后端 `director.py`：`_plan_in_background` 对齐消息改为中性措辞（「音频对齐中… (段落时长完整时秒级完成)」），不再暗示必须 Whisper
- **涉及模块**:
  - 后端：`app/services/alignment_service.py`、`app/services/director_service.py`、`app/routers/director.py`
- **备注**:
  - 实测通过：`total_duration_sec` 对齐完成即写入 458.314s（秒级）；85 slots 时间轴与 TTS 真实时长逐段对照零 mismatch；缺任一 segment_id / 空 segments / 无 completed job → 正确回退 Whisper
  - 快路径结果 `word_segments` 为空、`model="tts-durations"`，与 Whisper 版可区分
  - 规划剩余耗时主要在 LLM 工序单生成（deepseek 生成 85 段约 3-4 分钟），该步骤无法跳过，属必要开销

---

## 已完成的关联需求

- ✅ DeepSeek key 与双模型别名配置（`flash` / `pro`）
- ✅ 洗稿接口支持 `model` 和 `prompt_template`
- ✅ 视觉导演 Agent 2.0 提示词沉淀（`config/visual_director_v2.txt`）
- ✅ DeepSeek V4 双模型使用指南（`docs/deepseek_v4_model_guide.md`）
- ✅ TTS 句内截断修复（ID-016）
- ✅ ComfyUI 输入图质检（ID-015）
- ✅ library.html 视频播放修复（ID-017）
- ✅ 导演台 SSE 长静默阶段心跳升级（ID-018）
- ✅ index.html 音频任务刷新/跳页后丢失修复（ID-019）
- ✅ 导演台无音频脚本一键生成 + 僵尸音频任务清理（ID-020）
- ✅ 导演台脚本删除功能（级联 + 回收站）（ID-021）
- ✅ 导演台任务刷新/跳页后状态恢复（ID-022）
- ✅ 导演台规划期间可取消（ID-023）
- ✅ 导演台规划秒级对齐：复用 TTS 段落时长跳过 Whisper（ID-024）
- ✅ **2026-08-01 全项目审计修复收尾**（详见 `docs/improvements/进行中-20260801-全项目排查.md`）：
  - ✅ P0-1 失败 TTS 任务 DB/磁盘脱节（方案 1：失败不删盘 + 可续传，重试跳过已存在段）
  - ✅ P0-2 video_outputs 脏路径清洗（删 5882f87b 脏行 + 4 个 zombie visual job，残留目录回收站）
  - ✅ P1-1 app.js `btn-save-director` 空引用 5 处（`setSaveDirectorEnabled` helper）
  - ✅ P1-2 app.js `renderProjectDir` 崩溃（`.step:nth-of-type(2)` null → `script-text` 锚点 + 缺失守卫）
  - ✅ P1-3 library.js `tags` 未判空崩溃
  - ✅ P2-1~P2-7 收尾：HEAD 路由、SSE 重连上限、JSON.parse try/catch、fetch r.ok 检查、失败任务清理、.test_videos 回收站
  - ✅ **2026-08-03 导演生产路径优化 v3（8 阶段）**：零拷贝流水线（`-c copy` concat 无需预归一化）+ 48kHz 音频统一 + os.replace 替代 copy2 + composition_root/slots/ 目录统一 + 合成后 slots/ 自清理 + stale job 磁盘清理 + config deprecation。详见 ID-031。

### ID-025：合成视频「全程黑底」修复（多层根因）

- **状态**: in_progress（代码已改，待重跑 job 实测）
- **优先级**: P0
- **提出时间**: 2026-07-31
- **开发周期**: 2026-08-01
- **描述**:
  用户反馈合成视频全程黑底、有声音、字幕跳动。逐层排查确认是**多层根因叠加**，已逐层修复。
- **根因链与修复**:
  1. **host/主持人全崩 → 保底黑屏**（最大观感根因）：job 741c86ac 的 host/mixed_host_broll slot 全部
     `error_code='MODULENOTFOUNDERROR'`，`error_message="No module named 'PIL'"` → fallback broll_local
     也失败 → 最终 black_subtitle（黑底白字保底）垫场。**视频里主持人整段缺失，观感=全程黑底**。
     → 修复：`requirements.txt` 加 `Pillow`，venv 已装 12.3.0（`Image.Resampling` 可用），host 链路恢复。
  2. **fade 滤镜压黑**：`composition_service._concat_demuxer_concat` 旧写法
     `fade=t=out:st=0:d=0.2:alpha=0,fade=t=in:st=0:d=0.2` 在时间 0 同时淡出+淡入且 alpha=0 → 全片压黑。
     实证（`scripts/diag_*_tmp.py`）：
       - 本机 ffmpeg 的 `fade=t=out` 不带 `:alpha=1` 会把画面叠成黑底（亮度 0.0）
       - `fade=t=in` 带 `st>0` 会把该 fade 之前所有帧压黑 → 逐段淡入淡出在多段 concat 上只剩最后一段可见
     → 修复：**彻底去掉 fade**，`_concat_demuxer_concat` 直接返回 concat copy 产物（已实测 concat copy
     本身无损，关键帧 PTS 分布正常）。crossfade 仅 0.2s MVP 点缀，不值得承担黑屏风险。
  3. **横版参数未传入数字人**：`lit_video_builder.build_ltx23_video_workflow` 的 workflow JSON 节点
     296/297（INTConstant 输入宽/高）硬编码 576x1024，横版任务也被生成成竖版。
     → 修复：按 `get_video_format_spec(job.video_format).comfyui_w/h` 改写节点 296/297（已验证 landscape
     时 1024x576）。
  4. **合成硬编码竖版**：`_prepare_inputs` scale=1080:1920 + ASS `PlayResY:1920` 无视 job.video_format。
     → 修复：合成阶段读 `get_video_format_spec(job.video_format)` 的 width/height，scale 与 ASS 头都按
     横竖版切换。
- **涉及模块**:
  - `app/services/composition_service.py`（_concat_demuxer_concat 去 fade / _prepare_inputs、_write_ass_subtitles 横竖版）
  - `app/services/lit_video_builder.py`（node 296/297 宽高按 spec）
  - `app/services/slot_workflows.py`（black_subtitle 已按 spec 输出，未改）
  - `requirements.txt`（+Pillow）
- **备注**:
  - P1-5 升级项（2026-08-01 实测）：用户仅上传竖屏素材，**不补素材 ComfyUI 也能生成横版 host**，
    但结果「人物位置正确、其余白底」——LTX23 对竖屏参考图生成横版画布时，参考区之外补白。
    可用但不好看，**仍需上传横屏参考视频素材**才能让横版 host 全画面覆盖。
  - 字幕「跳动」问题与 ASS 时间轴/slot.start-end 有关，可一并处理。
  - 待办：用真实 landscape job 重跑合成，验证输出 1920x1080 且无黑屏；清理 `scripts/*_tmp.py`。

---

### ID-026：【功能】砍掉视频字幕体系（合成不再烧录 ASS 字幕）

- **状态**: done（2026-08-01 代码已改，py_compile 通过）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **描述**: 用户重跑合成后反馈「整个视频的字幕体系，我建议直接砍掉。不要用系统中的字幕了。」
- **改动**:
  - `composition_service.py` 移除 `_write_ass_subtitles` / `_burn_subtitles` / `_sec_to_ass` /
    `_clean_subtitle_text` / `_split_subtitle`（黑底白字保底，观感差）。
  - `compose_director_job` 原 Step 4（烧录字幕）改为直接响度归一，Step 5→Step 4 重新编号。
  - 模块 docstring 同步更新；`import re` 一并删除。
- **涉及模块**: `app/services/composition_service.py`
- **备注**: 若后续需要字幕，可再引入前端可控开关 + 外部软字幕（不进画面），本次从系统层面移除。

### ID-027：【优化】画面全局审视 + Pexels 降维搜索（画面违和/关联弱修复）

- **状态**: in_progress（代码已改，待用户重新规划脚本实测）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **描述**: 用户重跑合成后反馈：画面与文案关联弱 + 画面之间违和（欧美/中国/日本画面混用、
  空拍风景与艺术画面混用，拼接感强）。根因 = **缺全局审视视角**：导演提示词只按句给
  category+query，无全局风格/国家约束；pexels 按单关键词选素材无法区分国家/空拍/艺术。
- **改动（三层）**:
  1. **prompt 层**（`config/visual_director_v2.txt`）：新增 `## 规则5：全局画面一致性（硬性）`——
     - 5.1 全局主体关键词：全片只允许 1 个，放每个 broll_pexels 的 `keywords[0]`，仅口播点名海外案例才换。
     - 5.2 素材风格统一：全片只选 1 个主风格基调，禁止混用空拍风景/纯艺术（口播提到才用）。
     - 5.3 场景专一：同一 slot 只表达一个场景，相邻 slot 画面自然衔接。
     - 5.4 keywords 写法：按重要性降序 2~6 个词，词间不冲突。
     - `broll_pexels` params 约定由 `query` 改为 `keywords` 有序数组 + 质量自检清单新增 4 项全局一致性检查。
  2. **执行层**（`app/services/pexels_service.py` + `slot_workflows.py`）：
     - 新增 `PexelsService.resolve_descending(keywords, ...)`：从 `len(keywords)` 递减到 1，
       每次用前缀子数组（主关键词永远在首位）调 `resolve()`，命中非空即停，返回 `(items, used_query)`。
     - `execute_broll_pexels_slot` 优先读 `params.keywords` 调 `resolve_descending`；兼容旧 `params.category`。
  3. **合成层**：不改（concat copy 无损，画面关系靠规划层约束保证）。
- **涉及模块**: `app/services/pexels_service.py`、`app/services/slot_workflows.py`、`config/visual_director_v2.txt`
- **备注**:
  - 降维搜索策略为用户指定（2026-08-01）：「关键词太多搜不到内容，每次少一个=维度大一圈，
    2-3 个词必然有内容，且主关键词保证全片一致性」。
  - 待办：重新规划一条脚本，抽查 LLM 输出的 `keywords[0]` 是否全片一致、无欧美/日本混入。

### ID-028：【优化】hf_title 标题卡黑底白字 + 字幕残留修复（模板 + 喂料）

- **状态**: done（2026-08-01，已用真实 hf_title job 重渲染验证帧）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **描述**: 用户反馈两条：① 字幕去除不彻底（合成层 ASS 已砍，仍见字幕）；② 每到标题就变黑底白字、
  毫无设计/动感。用户判定问题出在 HTML 模板阶段。帧验证实锤根因有二：
  1. **模板残留黑条**：`news_magazine_v1/index.html` 底部 `#caption-bar`（#161616 黑底 + 血红上边框 +
     白字）在合成层砍字幕后被"漏网"保留，画面底部一条黑字幕条 → 观感"黑底白字"。
  2. **喂料塌方**：`execute_hf_visual_slot` 把整句口播（含 `||` 停顿符）硬塞进 `title`，metrics/chart 用
     口播占位垃圾（如 `value:"1"`）填充，subtitle/caption 为空 → 标题卡只剩一句长残句 + 垃圾数字。
- **改动（三层）**:
  1. **模板**（`E:\AI\digital_human\hf_prep\news_magazine_v1\index.html`）：删除 `#caption-bar` 的 CSS、
     元素、GSAP 滑入动画；保留 brand-bar/headline/blood-line/lead/metrics/chart/foot 完整设计。
  2. **喂料**（`app/services/slot_workflows.py`）：新增 `_extract_hf_content(text)` 从口播分句提取——
     - 标题：首句去情绪标签/去开场白（大家好/我是老陈等）后，标点感知截断（≤16 字，停在完整分句）；
       首句仅剩开场白时顺延用后续分句；空则回退「数据展示」。
     - 副题：第二分句（≤32 字）。
     - metrics/chart：仅抽取分句中的**真实数字**（带单位），percent 类进 chart，其余进 metrics；
       抽不到数字则跳过（模板 layout() 会删空 .m-row/.bar-row）。
     - 硬约束：input schema 强制 metrics 非空（minItems:1）→ 无数字时喂空占位行
       `[{"label":"","value":""}]`（视觉上被 layout 删除，不再塞 `value:"1"` 垃圾）。
  3. **白名单**（`app/services/template_filler.py`）：`_SAFE_KEYS` 确认无 `caption`。
- **涉及模块**: `E:\AI\digital_human\hf_prep\news_magazine_v1\index.html`、`app/services/slot_workflows.py`、
  `app/services/template_filler.py`
- **备注**:
  - 验证方式：新 job `2b812e70-e936-4740-abc0-4379176f803d` 走完整 `execute_hf_visual_slot` 链渲染成功，
    抽帧与旧 job `f90f6d4e` 像素对比——底部原黑条区 y1810-1920 血红占比 3.64%→0.00%（血红边消失）、
    纯黑暗区占满（无白字残留）；标题区亮度 22.5%→22.3%（标题正常渲染，未受损）。
  - metrics/chart 无数字时标题卡呈现「品牌条+标题+副题」简洁设计，属预期。

### ID-029：【BUG】重跑后字幕仍残留 + black_subtitle 兜底黑底白字（后端 reload=False 跑旧代码）

- **状态**: done（2026-08-01，代码已清、待用户重启后端验证）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **描述**: 用户按 A+B 修复重跑**完整合成管线**后反馈「重跑后，字幕依然在，还没有彻底清除干净」。
  排查重跑产物 `025a44f4-9674-49da-984e-c527d8572b61/`（21:01 最终片）实锤双重根因：
  1. **后端进程跑旧代码**：`run_web.py:24` `uvicorn.run(..., reload=False)` → Python 修改不热加载。
     产物里 `subtitles.ass`（Noto Sans 64px 白字）20:59 生成、`subtitled.mp4`、最终片 21:01，
     全程由 19:58 启动、加载 20:21 修改前代码的旧进程产生 → 合成层「砍字幕」的改动没生效。
  2. **black_subtitle 兜底漏网**：除已修 hf_title 模板 `#caption-bar` 外，`slot_workflows.py` 的
     `execute_black_subtitle_slot` 用 ffmpeg drawtext（`color=c=black` + `fontcolor=white:fontsize=64`）
     烧**黑底白字**，是第二个黑底白字来源。slot 38（225-327s 长段）实际走了该 workflow。
- **改动（四层清残留）**:
  1. `app/services/slot_workflows.py`：`execute_black_subtitle_slot` → `execute_black_placeholder_slot`
     （去掉 drawtext，改 `color=c=black:s={w}x{h}:d={duration}` 纯黑静帧 + `-an` 无声）；
     dispatch 表 `"black_placeholder": execute_black_placeholder_slot`。
  2. `app/services/director_service.py:356`：fallback 链末尾 `black_subtitle` → `black_placeholder`。
  3. `app/services/slot_executor.py:97`：phase `{"broll_local", "black_placeholder"}`。
  4. `app/services/composition_service.py`：`_WF_TIER` `"black_placeholder": 9` + 注释；`black_subtitle` 引用清理。
  5. `web/director.js:18`：`WF_LABELS` `black_subtitle: '黑底字幕'` → `black_placeholder: '黑屏兜底'`。
- **涉及模块**: `app/services/slot_workflows.py`、`app/services/director_service.py`、`app/services/slot_executor.py`、
  `app/services/composition_service.py`、`web/director.js`
- **备注**:
  - `python -m py_compile` 4 个改动文件全部通过；`black_subtitle` 已无任何 .py 引用（仅历史注释）。
  - ⚠️ **必须重启后端**再重跑合成验证（`reload=False` 不会自动加载新代码），否则本次改动无效。

### ID-030：【优化】Pexels 素材同视频去重（每个画面在同一段视频中只出现一次）

- **状态**: done（2026-08-01，代码完成 + py_compile 通过，待用户重启后端验证）
- **优先级**: P1
- **提出时间**: 2026-08-01
- **描述**: 用户反馈「在 pexels 产线中，一个素材被反复用，这里要有个限定，每个画面在同一段视频中只能使用一次」。
  即：同一个 Pexels 视频素材在同一 DirectorJob（一段视频）内只能用一次。
- **去重键**: `MaterialAsset.pexels_id`（Pexels API 全局唯一视频 ID）。注意 `ResolveItem.id` 是本地
  MaterialAsset 行 id，同一视频缓存复用时可指向同一 pexels_id，因此**不能**当视频唯一键。
- **改动**:
  1. `app/services/pexels_service.py`：`ResolveItem` 新增 `pexels_id` 字段（`_asset_to_item` 带出）；
     `resolve()` / `resolve_descending()` 新增 `exclude_pexels_ids: set[int] | None` 参数并透传；
     `_query_local` 加 SQL 过滤 `~MaterialAsset.pexels_id.in_(exclude_pexels_ids)`；
     `_process_candidates` / `_fill_with_degraded` 候选循环内 `if pexels_id in exclude_pexels_ids: continue`。
     顺带修正 `_fill_with_degraded` 内部去重键 `item.id` → `item.pexels_id`（原恒为 False）。
  2. `app/services/slot_workflows.py`：新增 `_collect_used_pexels_ids(db, slot)`，收集同 job 已完成的
     broll 类 slot（`workflow in ("broll_pexels", "mixed_host_broll")` 且 `slot_index < 当前`）中
     持久化的 `params_json["pexels_id"]`；`execute_broll_pexels_slot` 收集后传入
     resolve/resolve_descending，选中后写回 `slot.params_json["pexels_id"]`（db.commit 持久化）
     供同 job 后续 slot 排除。
- **涉及模块**: `app/services/pexels_service.py`、`app/services/slot_workflows.py`
- **备注**:
  - `python -m py_compile app/services/pexels_service.py app/services/slot_workflows.py` 通过。
  - 仅对**已完成且 slot_index 更小**的 slot 收集，保证时间顺序、避免自引用。
  - ⚠️ **必须重启后端**再重跑合成验证（`reload=False` 不会自动加载新代码）。

### ID-031：【优化】导演生产路径优化 v3 — 零拷贝 + 48kHz 统一 + 合成后自清理

- **状态**: done（2026-08-03，8 阶段全部完成；2026-08-07 第 7 项「合成后 slots/ 自清理」已被素材生命周期保留策略取代，见 ID-032）
- **优先级**: P1
- **提出时间**: 2026-08-03
- **开发周期**: 2026-08-03（单日完成）
- **描述**:
  从源头（ComfyUI workflow + TTS 切片）优化导演生产路径，消除三重浪费：ComfyUI 输出分辨率后归一化、poll 阶段 copy2 搬运、concat 前 `_prepare_inputs()` 二次 re-encode。
- **8 阶段改动**:
  1. ComfyUI 双 workflow 模板（竖版 1080×1920 + 横版 1920×1080，均 @30fps，+ImageScale node 440）
  2. poll_comfyui 零搬运（直接返回 ComfyUI 输出路径，不 copy2）
  3. 音频链路统一 48kHz（extract_audio_slice_wav、3 个非 host workflow +静音轨、mixed_host_broll +ar 48000）
  4. 删除 `_prepare_inputs()`（80 行代码 → 存在性校验 + 直接 `-c copy` concat）
  5. slot_root() 统一到 composition_output_root；HF 产物自动归一化 wrapper（48kHz 静音轨注入）
  6. copy2 → os.replace（5 处，跨盘 fallback copy2+unlink）
  7. 合成后 slots/ 自清理 + stale job 磁盘删除（⚠️ 2026-08-07 被 ID-032 取代：不再删除 slots/，改为默认保留 7 天）
  8. app.yaml deprecated 注释（director_output_root + hf_visual_root）
- **涉及模块**:
  - `app/services/slot_workflows.py`（poll 零搬运 / 48kHz / slot_root / 静音轨 / 删 fallback）
  - `app/services/composition_service.py`（删 _prepare_inputs / 存在性校验 / replace / slots 自清理）
  - `app/services/lit_video_builder.py`（orientation 参数选择模板 / fps 默认 30 / 删 width/height）
  - `app/services/visual_render_service.py`（HF 归一化 wrapper）
  - `app/routers/comfyui.py`（_persist_outputs copy2→replace）
  - `app/routers/digital_human_video.py`（Step E copy2→replace）
  - `app/main.py`（stale job + 磁盘删除）
  - `data/workflows/ltx23_video_portrait.json` + `ltx23_video_landscape.json`（新建双模板）
  - `config/app.yaml`（deprecated 注释）
- **备注**:
  - 计划文件：`C:\Users\tanhaox\.claude\plans\glowing-spinning-crayon.md`
  - 所有 8 阶段代码已完成，待重启后端后 E2E 验证。

### ID-032：【优化】素材生命周期策略升级 — 保留 slot 素材防返工

- **状态**: done（2026-08-07，验证 19/19 通过）
- **优先级**: P1
- **提出时间**: 2026-08-07
- **开发周期**: 2026-08-07（单日完成）
- **描述**:
  取代 ID-031 第 7 项「合成后 slots/ 自动清理」。原策略合成成功即 `shutil.rmtree(slots/)`，而 retry 只重置部分 slot → 「重试同类 / 换素材」局部重制后其余 completed slot 的 output_path 指向已删除文件 → REPAIR 用新素材补齐 = 返工，REPAIR 失败即合成崩溃。升级后 slot 素材默认保留 `slot_retention_days`（默认 7 天）。
- **改动清单**:
  1. composition_service.py 删除 Step 7 `rmtree(slots/)`（合成成功路径不再触碰 slots/）
  2. main.py `_auto_cleanup_stale_jobs()` 新增保留扫描分支：completed 且 completed_at 超 `slot_retention_days` → 清 slots/ + hf_visual/<job_id>/ + 孤儿中间件，**保留成片** director_<job_id>.mp4 + composition_manifest.json
  3. `_cleanup_intermediates` patterns 追加 `silence_fallback.wav`（master 音频缺失兜底）
  4. `purge_replaced_slots` 删 DB 行时连带删 `composition_output_root/<job_id>/slots/<replaced_id>/` 目录
  5. config: `DefaultsConfig.slot_retention_days: int`（默认 7）+ app.yaml `slot_retention_days: 7`（0 = 关闭保留回退旧行为）
- **删除 slots/ 唯二出口**:
  - ① 用户删 job → `_cleanup_job_files` rmtree 整个 job 目录（含 slots/）
  - ② 保留扫描 → completed 超保留天数
- **涉及模块**:
  - `app/services/composition_service.py`（删 Step 7 / 清理补充）
  - `app/main.py`（保留扫描分支）
  - `app/routers/director.py`（purge 连带删目录）
  - `app/config.py` + `config/app.yaml`（slot_retention_days）
  - `scripts/verify_retention.py`（新建隔离验证脚本）
- **验证**:
  - ✅ 隔离验证 19/19（临时 DB + 临时 composition 目录，不触碰真实数据）：核心链路 slots/ 保留 / retry 单条其余 slot mtime 不变 / 幂等返回 / 保留扫描清 slots 留成片+manifest / silence_fallback.wav 清理
  - ✅ 现状磁盘清理：85f51962 / b64aeb28 孤儿中间件、0f1f7ed3 silence_fallback.wav 已清
- **备注**:
  - 计划文件：`C:\Users\tanhaox\.claude\plans\glimmering-jumping-heron.md`
  - 详细报告：`docs/improvements/已完成-20260807-素材生命周期保留策略.md`
  - REPAIR 补齐逻辑保留为安全网（仅素材确实丢失时触发）；幂等守卫语义更新（job completed + 成片存在 + 无 slots_changed_since_compose → 幂等返回）

### ID-033：【挂起】素材库导入文件夹预标注 — 加快 AI 标注 + 补地域维度

> 讨论背景：2026-08-07 导演关键词动态包 + 本地碰撞方案讨论中提出。**已确认挂起**，待后续升级 AI 标注时实现。

- **现状痛点**：素材包（空拍/夜景/产业工人/街道街景等）以单一角度成批导入，且**都带固定先决条件**（如"中国"标签）。但当前 `location` 维度 93% 为 foreign、仅 7% domestic；AI 标注重新标注地域还**可能标错**。
- **方案**：素材库**导入时按文件夹做粗略预标注**（如"中国"、"空拍/航拍"），使 AI 标注时**直接跳过这两个维度**，加快标注速度。
- **关键点**：
  - 预标注 = 导入时从目录名/元数据推断硬维度（地域、拍摄角度），写入 VideoAsset 初始标签。
  - AI 标注阶段跳过已预标注的维度（减少 LLM 幻觉标错风险 + 省 token）。
  - 与本方案 ID-034（导演关键词动态包）衔接：预标注补全硬维度 → 本地碰撞的硬维度（地域/画幅/人物）命中率更高 → 少降级下载。
- **待定**：实现形式（导入器参数？目录约定？配置文件映射？）与预标注字段扩展。

### ID-034：【优化】导演关键词动态包 + 本地碰撞检索（替代全量素材清单）

> 2026-08-07 确认方案。解决「导演 LLM 全量素材清单发给 DeepSeek → 包过大 → 回传慢拖慢 slot 切片」。

- **核心矛盾**：现 `build_real_material_catalog` 每场景 top-8 裁剪后仍 ~26KB/1424 素材全量塞进 DeepSeek prompt（`stream=False`, timeout=120s）→ 回传极慢。
- **方案**：
  1. **关键词动态包** `data/vocabulary_pack.json`（~385 词 / ~3KB，比现包小 8 倍）：从全库聚合 scenes/shot_types/清洗后 tags/维度值，不写死；**AI 打标任务完成 / 素材导入 / 手动脚本后自动重建** → 每次从包里拉词，非开发更新。
  2. **导演选词约束**：按全维度输出检索条件，**每个维度 ≥1-2 个词**（非 3-6 个关键词）；第 1 个为画面主体词；只能从包内选词。
  3. **本地碰撞**（仅 AI 打标素材）：已有 `match_local_assets` 加权打分。**维度分级 + 命中规则**：硬维度（地域 location / 画幅 orientation / 人物 people）**必须全中**，否则排除；软维度（场景/镜头/tone/motion/content_density/time_of_day）**命中 ≥75%** 才算符合。
  4. **降级**：不符合 → 该 slot 转 broll_pexels 在线下载。
- **已确认决策**：维度分级（硬：地域/画幅/人物；软：其余 6）✅；命中规则（硬全中 + 软≥75%）✅；降级策略（全维度缺失就下载）✅；先只查 AI 打标素材（484 条）✅。
- **✅ 已落地（2026-08-09）**：三项缺口全部修复 + P 线本地碰撞 + 素材不复用登记，详见 `docs/improvements/已完成-20260809-P线本地碰撞-ID034匹配修复.md`：
  - `match_local_assets` 接入 location/people/orientation 硬维度硬过滤 + `min_duration_sec` 精确时长防护（素材须 ≥ slot 时长，防 render_scale_pad 黑尾截断）。
  - **根因修复**：scenes/shot_types 中文值在 SQLite JSON 列被存成 `\uXXXX` 字面量，`cast(String)+ilike` 永远 0 命中（P/L 两线本地匹配从未真正生效）→ 改 Python 层精确匹配，SQL 只按明文列 + 英文四维收窄。
  - `ai_tags_extra` 四维改为按值精确比对（含 4 条 time_of_day list 脏数据兼容）。
  - **P 线（broll_pexels）本地碰撞优先**：`_try_local_collision` 在下载前先查 9 维度守卫 + 碰撞，命中即 `register_asset_usage`（used_count 递增，`used_count.asc()` 排序自然降优先级，不做同 job 硬去重），未命中才走 Pexels 降维搜索；命中时 `chosen_pexels_id=None` 不污染 Pexels 同片去重。
  - L 线（broll_local）`_match_local` 传 `min_duration_sec=duration` + 命中登记 `register_asset_usage`（`_try_exact_file` 精确路径不登记）。
  - 提示词 4 处"建议"→"必须"（`_prompt.py` + `visual_director_v2.txt`）：broll_pexels 必须同时输出 9 维度（仅供本地碰撞，不参与 Pexels 下载搜索；keywords 仍为自由搜索词不受词表约束）；缺 9 维度则碰撞跳过（P 线全部走下载）。
  - 验证：词表包真实枚举值构造 P 线碰撞 2/6 HIT（城市+航拍 warm slow moderate day→685.mp4；自然+空镜 bright medium sparse sunset→584.mp4）；4 MISS 为数据稀疏（科技 12/财经 6），符合"词不在包内 → 转在线下载"预期；import/签名回归 OK。
- **数据现状**：1536 素材（全 hasfile）；portrait 943 / landscape 593；scenes 城市768/街景489/生活221/商业210/自然205/工业87/科技82/财经38/美食13/教育13/医疗7；shot_types 空镜626/建筑503/交通390/人像293/航拍279/特写221；tone cool499/warm376/bright322/neutral221/dark20/monochrome4。词表包 `data/vocabulary_pack.json` 聚合库内全标签（stats assets 1467）。
- **相关**：ID-033（文件夹预标注补硬维度，挂起）。

### ID-034 后续（2026-08-12）：门槛重构 + 同 job 硬排除 + 导演台素材操作

> 详见 `docs/improvements/已完成-20260812-本地碰撞门槛重构与导演台素材操作升级.md`。本会话在 ID-034 基础上修复了"本地碰撞命中率 ~4%"与"同素材一视频出现 28 次"两个核心问题，并补齐导演台素材操作功能。

- **✅ 门槛重构（0%→68%）**：软维度门槛 6 维降 3 维（scenes/shots/tone，3 中 ≥2），motion/content/time 降为加分维；空值跳过（素材未标不记失分）；备选值交集（shot_types=[建筑,特写] 任一命中）；location C 折中（strict 空才放宽 foreign + 标记）。
- **✅ 同 job 素材硬排除（一素材一视频只用一次）**：本地命中写回 `params_json["local_file"]` + `match_local_assets` 加 `exclude` 参数 + `_collect_used_local_files` 收集（按 status=completed，跨 phase）。实测 V20260807-0012 从 28 次 → 1 次。
- **✅ 导演台素材三件套**：禁用素材标（`POST .../disable-material`，本地线补 `preference!=dislike` 过滤）+ 替换去重校验（已用素材 → 409）+ 重新生成强制 P 线下载（`force_pexels` 跳过本地碰撞）。
- **✅ slot 视频预览 + 素材编号替换**：`GET .../slots/{id}/preview`（FileResponse）+ `POST .../replace-material`（填 asset_no → 写 params.file + 切 broll_local → 同步重渲染即时生效）；预览加 cache-busting 时间戳修复替换后不刷新。
- **✅ 音频过期标记（方案A）**：文稿改动 → 旧 AudioJob 标 `stale`；`generate_audio` 清理 stale job 磁盘 wav → 强制重新合成（修复"改稿后音频跳过不重生成"）。
- **✅ 脚本列表加保存时间**：下拉每项显示最后保存时间；`list_scripts` 排序改 `updated_at`。
- **✅ library 视频卡复制编号按钮**：`copyAssetNo` 一键复制 asset_no，与导演台替换闭环。

### ID-035：【BUG】圆饼图缺角修复 — offset 守恒 + 纯 opacity 淡入（模板层）

- **状态**: done（2026-08-08，双模板各重渲染含 0.1% 极小段的 pie 成片 + PIL 像素验证 4/4 帧无缺角）
- **优先级**: P1
- **提出时间**: 2026-08-08
- **描述**: 竖屏/横屏新闻杂志模板在「出现圆饼图」时生成的圆有缺角。帧验证 + 几何模拟实锤**三重叠根因**：
  1. **主段分离动画**：GSAP 对主扇区加 `scale: 1.1` 放大 + `rotation: 14°` 分离——圆周任何尺寸/角度变化都会在动画帧露出缺口。
  2. **小段 clamp 失配**：段间 gap 按固定弧长预留（名义比例），极小段（如 0.1%）被 `Math.max` clamp 失真，段间错位叠加缺口。
  3. **offset 不守恒**：偏移量用名义比例累加，与实际占用弧长不一致 → 末段 wrap 后落进第一段内部（几何模拟：旧算法段对重叠 2 次）。
- **改动**（`buildDonut` 三处守恒重写）:
  - `avail = C - n * SEG_GAP`：缺口按比例预留，不再用固定弧长。
  - `stroke-dashoffset = -used`，`used += len + SEG_GAP`：offset 全程守恒，段间无错位。
  - 去主段 `scale`/`rotation` 分离动画，扇区改**纯 opacity 错峰淡入**（任何尺寸/角度变化都会让圆周在动画帧出现缺口）。
- **涉及模块**: `E:\AI\digital_human\hf_prep\news_magazine_v1\index.html`、`news_magazine_v1_ls\index.html`（⚠️ 模板实体在仓库外，无版本控制）
- **验证**:
  - ✅ 竖屏/横屏各重渲染一条含 pie 成片（`items:[58,22,15,4.9,0.1]`，含 0.1% 极小段，duration 8s），抽 2.4s/7.8s 关键帧。
  - ✅ PIL 沿环 0.5° 步长扫描（R±40 内 5 径向样本）：竖屏 719/720、横屏 720/720 命中，**全部整环闭合**；缺失约 0.5° 为设计内 1px SEG_GAP 细缝。
  - ✅ 几何模拟同压测数据：旧算法段对重叠 2 次 → 新算法 0 次，段间 gap 均匀 0.3-0.4°。
- **备注**:
  - 模板实体位于 `E:\AI\digital_human\hf_prep\`（`hf_template_root` 默认路径），**不在 git 仓库内**，改动需手动备份。
  - 首版修复曾用「固定弧长 gap」思路，经几何模拟证明仍存在 wrap 重叠，故收敛为 offset 守恒方案。

### ID-036：【优化】HF 横屏模板 news-magazine-v1-ls — 按 video_format 自动选横/竖

- **状态**: done（代码引入 commit `4997ca1c` 2026-08-07；横竖屏成片像素验证 2026-08-08 随 ID-035 完成）
- **优先级**: P1
- **提出时间**: 2026-08-07
- **描述**: H 线 HF 视觉渲染此前**硬编码竖屏模板**，选 `landscape` 画幅时所有 HF 视频仍产出 1080×1920 竖屏。新增横屏模板 `news-magazine-v1-ls`（1920×1080，composition_id `news_main_ls`），`_pick_hf_template` 按 `job.video_format` 宽高比自动选横/竖模板。
- **改动清单**:
  1. `app/services/template_library.py`：`TEMPLATES` 新增 `news-magazine-v1-ls`（source_dir `news_magazine_v1_ls`，横屏 1920×1080，schema 与竖屏同构）。
  2. `app/services/slot_workflows/common.py`：新增 `_pick_hf_template(job)` — `spec["width"] > spec["height"]` → 横屏模板，否则竖屏。
  3. 模板源：`E:\AI\digital_human\hf_prep\news_magazine_v1_ls\index.html`（仓库外），donut 布局：`#chart` 居中 (960,540)、wrap 540×540、scale 1.35。
- **涉及模块**: `app/services/template_library.py`、`app/services/slot_workflows/common.py`、`E:\AI\digital_human\hf_prep\news_magazine_v1_ls\index.html`
- **备注**:
  - commit `4997ca1c` 同时含「合成缺失 slot 自动补齐」与「幂等守卫细化」（job completed + 成片存在 + 无 slot 变化才跳过）。
  - 横屏模板成片（含 pie）已随 ID-035 的 2026-08-08 重渲染完成 PIL 像素验证，无缺角。

### ID-037：【优化】HF 模板品牌泛化 — brand_name / stamp_name / brand_tag 注入

- **状态**: done（2026-08-08，工作区未提交，待重启后端验证）
- **优先级**: P2
- **提出时间**: 2026-08-08
- **描述**: 新闻杂志模板由多数数字人账号共享，品牌栏/印章此前**硬编码账号名**（如「老陈聊财经」）。新增三个品牌字段动态注入，模板不写死任何账号：
  - `brand_name`：账号名（从 `slot.director_job.script.host` 注入，缺省回退「财经频道」）。
  - `stamp_name`：印章字，取账号名前 2 字竖排（适配 120px 印章框；短名取首字符），回退「财经」。
  - `brand_tag`：标语，优先 `render_config` 覆盖，回退「数据解读」。
- **改动清单**:
  1. `app/services/template_filler.py`：`_SAFE_KEYS` 新增 3 个白名单 key（**27 个**）；`_build_substitutions` 从 `input_data` 填充三个品牌字段。
  2. `app/services/slot_workflows/hf.py`：新增 `_merge_brand(input_data, slot)` — 从 `slot.director_job.script.host.name` 注入（全部 lazy=selectin，**零额外查询**）；找不到 host 时回退中性占位，保证标题卡不出现他人账号名或空块。
- **涉及模块**: `app/services/template_filler.py`、`app/services/slot_workflows/hf.py`
- **备注**:
  - 若未来 hf_title 等模板引用 `{{brand_name}}` 等占位符，同一喂料链路自动注入。
  - ⚠️ **必须重启后端**再重跑合成验证（`reload=False` 不会自动加载新代码）。

### ID-038：【BUG】HF 渲染 300s 超时 — 本机 auto-worker calibration 卡死 + 模板 letterSpacing lint error

- **状态**: done（2026-08-08，代码已改；后端重启后新渲染自动生效）
- **优先级**: P0
- **提出时间**: 2026-08-08
- **描述**: job 79fc44b6 slot#2 渲染报 `HyperFrames timed out after 300s`。render.log 显示 compile 41.9s 后 **capture_calibration 阶段卡死**：两次 `Runtime.evaluate timed out`，150 帧 0 完成。
- **根因分析**（两点独立，均已修）:
  1. **auto-worker calibration 卡死（后端层）**: 本机 32 cores → `--workers auto` 高并发起多个 Chrome → Intel UHD 集显资源耗尽 → calibration `Runtime.evaluate` 超时。HF 兜底重试截图模式仍超时，浪费 ~95s 后才降级到 1 worker。
  2. **模板 letterSpacing 动画 lint error（模板层）**: 横屏模板 `tl.fromTo(headline, { letterSpacing: "0.12em" }, { letterSpacing: "0.02em" })` 触发 `gsap_non_transform_motion` lint error — 文本重排属性在 seek-by-frame 捕获引擎下 stutter。
- **修复方案**:
  1. `app/services/hf_client.py`：render 命令追加 `--low-memory-mode` — 固定 1 worker + 强制 screenshot 捕获 + 跳过 auto-worker calibration，**实测 39s 稳定出片**（之前 300s 超时）。
  2. `E:\AI\digital_human\hf_prep\news_magazine_v1_ls\index.html` L415-418：移除 letterSpacing 动画（字距展开感已由逐字 stagger 弹入承担），lint 干净，渲染验证通过。
- **涉及模块**: `app/services/hf_client.py`、`hf_prep/news_magazine_v1_ls/index.html`（仓库外）
- **验证**:
  - CLI + 后端链路（fill_template → render_visual）验证：44.6s exit=0，产物 1920×1080/30fps/h264 规格与成功 render 一致。
  - render.log 无 `gsap_non_transform` / `letterSpacing` lint error。
  - slot#2 产物已回填（`hf_title_002.mp4`，DB status=completed）。
- **备注**:
  - `--low-memory-mode` 只影响渲染 worker 数/捕获模式，产物规格不变，后续合成自动复用。
  - ⚠️ **必须重启后端**（`reload=False`）新渲染才用上 `--low-memory-mode`。
  - job 79fc44b6 另 6 个 CANCELLED slot（#26/31/41/51/54/57，用户主动取消）未重跑，待用户确认。

---

### ID-039：【功能】爆品改造流水线（Boost Service）— 洗稿后自动优化流量指标

- **状态**: done（2026-08-11，`d6897e03`；手动测试 3 Pass 全通，待真实投放数据验证）
- ⚠️ **2026-08-14 更新**：七层洗稿定稿后 P1/P2/P3 已全砍，流水线改 **P4→P5**，本条的 P1∥P2→P3 编排仅对旧六模块稿有效，详见 ID-046。
- **优先级**: P0
- **提出时间**: 2026-08-10
- **背景**: 零粉新号第一条视频（AI骗人）投放数据：2s 跳出 20%、5s 完播 47.85%、平均 28s（全片 5:10）、收藏24 vs 分享0、评论2。内容是高板（收藏好），短板是结构（开头冷、无互动引导、节奏无呼吸）。
- **方案**: 洗稿后自动跑爆品改造，3 个 Pass 编排：
  - **P1 开场专家**（治留存）：重写前 30 秒（冲击→闭环→呼吸→再钩 4 句编排）+ 标题 3 候选。JSON 输出，temp0.5，max_tokens4000，字数 120-150。
  - **P2 预埋专家**（治互动）：正文埋争议点 + 信息钩子，按结构分布协议回收（争议回收→收割段末、关注回收→固定结尾前一句、固定结尾 1:1）。真实性红线：禁编造，只允许情绪/逻辑后果/程度三类具象化。心法：拒绝礼貌/制造空洞/拒绝求关注。
  - **P3 节奏专家**（治完播）：高密度区插老谭式呼吸点（冷幽默/利益拉回/吐槽），每 90s 至多一个、总 ≤3。
  - 并行度：**P1∥P2 并行**（P1 产头、P2 不要头），P3 等两者回来再跑。
- **技术关键**:
  - `max_tokens ≥4000`（reasoning 模型思考 token 占大头，不足输出空）；`temp 0.5`；JSON 格式 > 纯文本。
  - `persona` 动态注入（`{persona}` 占位符 + host.name），多人物矩阵通用。
  - `_call` 空响应自动重试 2 次（reasoning 模型偶发空输出）。
  - 代码兜底：P3 丢 P1 开头时强制拼回；全 Pass 失败回退原稿（不卡死配音）。
- **涉及模块**: `app/services/boost_service.py`（新增）、`app/routers/articles.py`（rewrite 端点链式调）、`app/models/content.py`（Script 加 boosted_text/boost_titles）、`app/database.py`（迁移加列）
- **文档**: [已完成-老谭提示词精进-20260810.md](improvements/已完成-老谭提示词精进-20260810.md)（完整讨论+决策）、[爆品改造-阶段提示词.md](improvements/爆品改造-阶段提示词.md)（三 Pass 提示词定稿，已转历史参考）
- **验证**: 用老陈稿（瓜子水饺）跑 `run_boost` 端到端：P1/P2/P3 全成功，P1 新开头进稿、正文保留、预埋+呼吸点+结尾正确。
- **待办**:
  - 前端看稿页展示 boost_titles / boosted_text（人工确认用新标题）。
  - 用真实 laotan 稿完整跑一遍 rewrite 端点（含 boost）做最终验收。
  - 观察下一条视频投放数据，验证改造效果。
  - ⚠️ **新盲区（2026-08-11 双视频对照发现）**：爆品改造缺"密度压缩"能力。抖音章节点击数据显示：AI 片 01:35「开源闭源」37.5% 高点击（观众主动跳转=核心兴趣），00:29「测试结果」12.5%（观众活不到/不主动点）。0-1:35 是流失重灾区，但 P1-3 只改结构、不裁密度——测试结果段（122轮/19次/攻击细节，约 24.7-65s 占 40 秒）改造后仍会拖住观众。需给 P2 或独立 Pass 加"压缩数据堆/测试结果段"能力。
  - 封面优化（AI 赛道 3.87%→目标 6%）：属视觉/运营层，不在提示词范畴，需单独做。

### 双视频对照结论（2026-08-11，豆包数据 + 流程时间轴实测）
- **样本**：伊朗（地缘，封面11.11%强/2s跳出32.32%/章节00:51军事困境40%）vs AI（科技，封面3.87%弱/2s跳出20.07%/章节01:35开源闭源37.5%）
- **共性结构**：封面→（铺垫引言）→正文高质量。观众行为=封面进来→铺垫劝退或手动跳过→直达正文
- **验证**：钩子后置、铺垫前置是创作通病（两条视频一致）；正文质量都被章节高点击认可（40%/37.5%）
- **修正**：章节低点击（AI 00:29 12.5%、伊朗 00:00 引言 20%）不全是"主动跳过"，更多是"观众活不到那段就流失"
- **转化视角**：豆包以为稿子手写，不知道是 laotan 六模块流程产物。其"砍引言/钩子前置"建议翻译成流程语言 = 改模块顺序/长度约束 或靠爆品改造重构前段（已在做）
- **抖音章节 = parse_script 切分边界**：00:29=段5（122轮测试），01:35=段17/18（开源闭源）——章节点击率可作观众对每段的兴趣投票反馈信号

### ID-040：【选题层】选题思维链提示词 + laotan 介入时机后移（2026-08-11 讨论中）

> **方法论**：样本太少不能提炼。思维链靠"多来几条 → 抽共性 → 总结成提示词/Agent"。本条目持续记录用户选题思维链，攒够样本后再抽象。
> **目标定位（2026-08-11 澄清）**：不是"复刻用户的思考"，是"提供一个可给 AI 造钩子的行为实验"。用户提供的是"人类如何产生钩子的行为样本"，提炼目标是让 AI 学会**造钩子的行为模式**（通用机制），而非模仿特定个人。

**选题思维链实录 #1（智谱ARR新闻，2026-08-11）**——"天然钩子"第一手来源：
1. 刷到热点「传智谱ARR今年将达20亿美元」→ 点开
2. 读完第一反应："这么小的新闻，没什么感觉" → 深挖方向 = 国内AI大厂如何抢客户
3. 联想转折："现在的白领依托的不是AI底座，是办公用agent智能体。后面AI大模型影响因素没这么大" ← **认知颠覆**（大众以为AI竞争=模型之争，实际=agent之争）
4. 个人吐槽（最强钩子）："智谱，我抢不上时，你用户量没涨这么快，看来算力解决了" ← **当事人反差**（我亲历的体验 vs 新闻的数字）
5. 升维："算力？华为吧？美国的又买不到。华为是个可以聊的内容"
6. 新闻里"数据中心落地"一句话 → 这条被选中（**最终方向=华为算力/国产替代，已不是原新闻智谱本身**）

**选题思维链实录 #2（印度稀土大计，2026-08-11）**：
1. 刷到热点「原料、设备和资金全是坑，怎么跟中国争！印度稀土大计卡了」→ 点开（新闻讲印度728亿卢比稀土磁体计划，企业质疑补贴模式）
2. 第一反应："这条三哥的天然有点流量" ← **题材直觉**（印度=天然流量话题）
3. 讽刺联想："中国稀土卡欧美脖子，他就整稀土项目，真的是欧美的钱才是最好赚、最好骗的，这技能老实的中国人真不太行" ← **当事人反讽**（欧美钱好骗）
4. 隐忧升维："设备采购来自中国还是日本，中国光管理稀土成品不行，设备/技术/人才一个点也不能给三哥，否则早晚爬上来。这点是隐忧，需要去查下资料" ← **隐忧 + 调研需求**
5. 情绪细节共鸣："过去九年【哎，九年啊】，他频繁前往中国" ← **数字触发情绪**（九年这个细节戳人）
6. 印证自我认知："印度对全球稀土产量贡献不到1%果然是我认识的三哥" ← **共识确认**
7. 落点："这篇文章调侃一下可以的" ← **定风格**（调侃文，不是深度文）

**选题思维链实录 #3（巴铁/麦加共同防务协议，2026-08-11）**：
- **负样本（为什么跳过）**：「日本没被原子弹炸过！篡改历史的回旋镖砸向日本」→ "看标题就知道日本右翼在作妖，可是我不想讲日本，过" ← **题材疲劳跳过**（知道套路，无新意不值得讲）
- 正样本：「巴基斯坦与伊朗外长通话」→ "这个标题有点意思，巴铁"
- 读完抓住信息缺口："麦加共同防务协议，这是个非常好的点，这个能深度讲一下" ← **捕捉可深挖的信息缺口**
- 关联拆解："巴基斯坦、沙特阿拉伯和土耳其" + "中文新闻版面里土耳其好像很久没什么动静了" ← **信息缺口观察**（土耳其沉寂）
- 个人知识反差："巴基斯坦其实是中国小弟，沙特猴精的在自己机场给中国开自贸区，土耳其真没什么印象。这三个国为什么？巴基斯坦和沙特不是才签了一个什么你出钱我出命的条约么，怎么又加一个国家进来？" ← **认知缺口**（三角关系为何成立）
- 冷静判断："这是签完协议后的拜年话吧。给点新闻版面。这个可以。" ← **定调**（外交辞令，非实质突破）+ **可讲**

**选题思维链实录 #4（日本混动护城河被中国EV攻破，2026-08-11）**：
1. 刷到标题「日本车企的混动护城河被中国EV攻破！全球电车均价首次低于混动车」→ "这条可以。标题就可以。" ← **标题即钩子**（标题本身有冲突，直接可用）
2. 抓住新闻核心数据 → 连发质疑拆解：
   - "核心护城河正在被中国EV攻破，怎么攻破了？" ← **设问**（要求证据链）
   - "电池价格跌37%。电池便宜了。中国占全球电池产能八成份额实锤了。" ← **顺着数据推出结论**
   - "2025中国EV出口164万辆，五年增长16倍。这里面其实还有一层，就是产业真的升级了。" ← **数据背后读出更深层**（不只是出口，是产业升级）
3. 点破标题党："还有条新闻是byd的k-car在日本卖得也不错。这个文章完全是挂羊头卖狗肉。说了一堆数据，一个如何干日本都没提。" ← **拆穿新闻注水**（数据堆但不给结论/打法）
4. 交叉联想（中东/油价）："中东局势恶化推动油价上涨，霍尔木兹啊，伊朗啊，推高全球油价，帮助中国电动车崛起了。" ← **跨话题勾连**（地缘冲突→油价→中国EV受益）
5. 反向吐槽（拆日本）："丰田不知道在中国只有中国电动车和其他吗？这又是一头包的故事了。" + "什么不内卷，中国过去直接卷死他！" ← **态度收尾**（犀利、不留情）
6. 个人笃定结论："电池是中国的，日本成本下不来，只能被动挨打。结论可以说，但必须是这个方向。" ← **确立文章立意**（电池话语权→日本被动挨打，唯一正确的论证方向）

**选题思维链实录 #5（Meta 单卡可运行轻量模型，2026-08-11）**：
1. 标题「Meta发布可单卡运行轻量AI模型 扎克伯格描绘个人赋能新时代」→ "这个看看什么意思" ← **先不判定，看内容再定**（标题有信息但不够强）
2. 通篇逐句反问拆解：
   - "体量轻量可在单台电脑运行" → 【多轻？】← **追问量化**（轻到多少，没给具体）
   - "300亿参数，一张显卡就能运行" → 【显存多少手机能行？】← **现实对比**（手机/显存能不能跑，质疑宣传）
   - "主要用于智能体任务如日程管理、文件整理" → 【这不小艺什么的手机AI也行吗？】← **戳穿"新"**（手机已有类似功能，Meta 有何不同）
   - "模型权重在Hugging Face开放" → 【开源还行】← **正面认可**（唯一加分项）
   - 扎克伯格"个人赋能新时代" → 【情怀点赞，人不怎么样】← **人设反差**（说得好听，人/公司另说）
   - "想当AI时代的windows，可惜你没有系统入口，最多是个app，还是鸿蒙有未来呀，硬件系统都在自己手，想怎么弄就怎么弄" ← **战略升维**（Meta 想做平台但无入口 → 鸿蒙有硬件+系统闭环才有未来）
   - "Meta承诺投入超2万亿美元" → 【别人都在烧钱，你怎么就丰厚回报了？】← **质疑商业逻辑**
3. 尾部抓深挖方向："Meta还在制定计划准备开展云基础设施业务，向客户出售算力和模型使用权限" → 【后面可以挖挖那几家的动态】← **调研需求**（云基建/算力出售，各家对比）
4. 未明说但隐含的落点：Meta"个人AI"叙事 vs 现实差距（手机AI已有、无系统入口、烧钱难回报）——大概率"拆穿个人赋能宣传 + 华为/鸿蒙对比"

**当前初步识别（5 条样本，待验证）**：
- **共性浮现**：
  - **"逐句反问拆解"是稳定模式**：#1设问/#2数据推导/#3协议动机/#4怎么攻破/#5每句反问——**你的思维链几乎每篇都在"追问证据/戳穿宣传"**
  - **"现实对比戳穿"持续**：#1"抢不上"亲历 / #4手机车市 / #5"手机AI也能行吗"——**用日常体验验证新闻宣传**
  - **"开源/华为/鸿蒙"反复出现**：#1华为算力 / #5鸿蒙有未来——**国产替代是你反复升维的锚点**
  - **"质疑商业逻辑"浮现**：#5"烧钱怎么丰厚回报"（#1 也质疑过资本）
  - **调研需求持续**：#1算力/#2设备/#4车企/#5云基建各家动态
- **"三合一"假设持续成立**：#5 深挖（Meta战略）+ 调侃（人不怎么样/小艺也行）+ 拆解（无入口没戏）
- **触发模式观察**：#5 是"标题给信息但不够强→点开确认"，与 #4"标题即可用"、#3"看穿跳过"并列——**触发不是单一强度，是连续谱**
- **待更多样本**：5 条已到区间下沿，再 2-3 条可进入提炼

**关键洞察（待验证）**：
- 最强钩子来源 = 选题时刻天然好奇 + 个人体验反差，不是稿子写完后从稿里抽
- 选题最终方向（华为算力）≠ 原始新闻（智谱ARR）——原新闻只是触媒
- 多信息点需逐个调研（算力/华为/数据中心/agent），回来才成稿
- laotan 介入时机应后移：吃"调研完成后的综合稿"，而非"单篇新闻原文"

### ID-041：【缺层】钩子解构层（洗稿前前置）— 产出钩子清单+叙事线+资料清单

> **定位（2026-08-11 澄清）**：选题(选哪条)→**钩子解构(这一层，当前缺失)**→老谭洗稿(怎么讲)→爆品改造P1(留气口改30秒)。"怎么讲"是老谭的事，解构层只管"有什么钩子/讲哪些点/备什么料"。

**背景**：当前 laotan 洗稿直接吃原始新闻，缺"解构前置"→ 老谭六模块假设输入是结构化素材，但直接收到报告体新闻 → 只能顺着新闻结构走（先背景后正文）→ 造成铺垫过长、钩子后置（豆包章节数据印证）。大新闻小新闻都没经过"先想清楚这新闻在满足观众什么疑问"。

**核心原理（豆包+用户共识）**：普通用户点进/收听新闻时会产生相同疑问——"带着自己的问题，就会出现相同的问题"。钩子不是洗稿时临时想的，是新闻本身隐含的。这些钩子要在视频里**一个一个解答**，用**层层递进的故事模式**。

**解构层产出**（3 项）：
1. **钩子清单**：普通用户看到这新闻会问什么（疑问列表，如"土耳其为什么签""合约到底是什么"）
2. **叙事线**：层层递进的讲述顺序（先答什么再答什么，故事式），每层对应一个钩子的解答
3. **资料清单**：要讲清楚这些点需要备足哪些基础事实/资讯（调研清单）

**产出形态**：结构化叙事大纲 → 交给 laotan 洗稿 → 再走爆品改造 P1。

**✅ 验证成功（2026-08-11）**：用印度IT外包稿（夫妻自杀/AI砸饭碗）实测整条链路：
- **解构层（v4）**：AI 生成"用户真实反应清单"（8条，含懂/盲区/嫌累三类）——复刻真实用户看新闻的心理，包括"千年虫是啥""管理岗AI怎么替代""跟我有啥关系"
- **伪装技巧（用户拍板）**：解构产出**标注成"真实用户评论"**喂给老谭（不接真实评论区，AI自己生成伪装即可）
- **老谭成稿质变**：开头用用户评论#1悲剧画面（夫妻上吊跳楼+一行代码）、用大白话回应盲区（千年虫/管理岗AI替代/硅谷高管）、横向对照拉近"离我好远"（像咱们制造业冲击）、结尾升维"印度今天是很多国家明天的考题"
- **结论**：老谭从"原文找逻辑"变成"从观众疑问出发"——铺垫变解答，钩子不再抽象

**两篇验证（印度IT / Meta）后的固化教训（2026-08-11）**：
1. **结尾结构应在提示词层硬约束**，不是靠脚本事后重排。规则：**回收句(争议回收+关注回收) 整体放在赞块之前，赞是连续整体，最后是固定结尾**。不存在"赞1/预埋/赞2/赞3"散落方案。
2. **锚点不固定**：两篇锚点不同（"因为印度今天的惨剧"/"这事儿咱们得看透"）。需固化规则：找 laotan 身份段后的正文引导词。
3. 这些约束应写进 P3 提示词（或专门的结尾约束块），让模型一次生成就符合结构，避免手动重排。

**✅ 固化进系统（2026-08-11）**：
- `boost_service.py`：
  - 新增 `DECONSTRUCT_PROMPT` + `deconstruct_article()`（解构层：AI生成伪用户评论）+ `format_pseudo_comments()`
  - 新增 `_LAOTAN_ANCHORS` 锚点规则，`_find_end` 改为按 laotan 引导词切正文（比段落位置可靠，两篇稿验证通过）
  - `P3_PROMPT` 加【结尾结构硬约束】：回收句整体在赞前、赞块连续、固定结尾最后（两篇验证后模型一次生成即正确）
- `articles.py` rewrite 端点：洗稿前先跑 `deconstruct_article`，伪评论注入 laotan 输入（失败回退普通洗稿）
- **新流程**：新闻 → 解构层(伪用户评论) → 老谭洗稿 → P1∥P2 → 锚点拼接 → P3
- 验证：解构层测试 8 反应/6 层/8 资料；`_find_end` 对印度+Meta 两稿都正确切锚点

**当前缺的一层 = 解构层提示词**（v4 已跑通，需固化成正式提示词 + 接入流程）。

**待做**：
- [ ] 写"钩子解构"提示词（产出 用户反应清单+叙事线+资料清单）
- [x] 接入流程：新闻→解构(AI生成伪装用户评论)→laotan（✅ 2026-08-15：独立端点 `POST /api/articles/{id}/deconstruct` + 五种评论区人设伪评论注入洗稿 + 新闻线索页「评论层」面板，见 ID-048）
- [ ] 用真实新闻实验（如麦加协议：土耳其为什么签/合约是什么）验证解构初稿

### ID-042：【视觉+配音】视觉层与配音层已知问题（稿件源头已整治，视觉/配音待处理）

> 稿件源头（解构层→老谭→P1∥P2→P3）已整治完。本条记录视觉层 + 配音层的已知问题，集中整治完稿件后再处理。

**A. 视觉层问题（基于那条 AI 视频，pipelines=h,p）**：
1. **首帧是 hf_title 静态标题卡**：C 线(host出镜)被禁用 → host 降级 → hf_title 独占首帧 → 2s 跳出 20% 的视觉元凶。但 laotan host/role 出镜配置齐全（reference_image + view_groups），**C 线完全可用**，那条视频是当时临时禁的。
2. **hf_title 开头过密**：前 35s 出现 2 张 hf_title + 1 张 hf_chart，违反"hf_* 不得相邻"规则，但降级路径（_downgrade_hosts_c_disabled）绕过了强制。
3. **hf_title 越权用开头**：规则写"仅参考来源卡(尾部)"，降级时 LLM 用在开头，无"首帧禁空卡"硬约束。

**B. 前 5 秒听觉不可靠 → 视觉兜底（用户已知问题，核心）**：
- 前 3 秒可能配音没起/走神/提前播放，用户根本没听清精彩开头 5 秒 → 连问题都没搞清楚，不会看下去。
- **解法**：前 5 秒把标题 + 开头几句话集中贴成文字，**至少 5 秒后消失**（视觉兜听觉）。
- **修正**：不是"禁静态卡"，是"首帧卡必须承载开头台词"（有信息，不是空卡）。

**C. 配音层问题（记录，集中处理）**：
1. 历史/地缘（强逻辑）需慢语速给消化时间；AI/科技可快语速。
2. 现状两条视频都用"大学教授"音色（1.2 倍速）→ AI 天然赢、地缘天然拉。
3. 解法方向：语速按内容类型/人物设定差异化，非一刀切 1.2 倍。

**待做**：
- [ ] 视觉层：C 线是否恢复（首帧 host 出镜治 2s 跳出）/ 首帧禁空卡 / hf_title 降级保护
- [ ] 前 5 秒标题台词贴字 ≥5 秒（视觉兜听觉）
- [ ] 配音层：语速按内容类型差异化（集中处理，最后做）

**⚠️ 视觉层根问题：导演盲盒（2026-08-11）**：
- 我们把文章拆了一次又一次、结构改了一遍又一遍（解构→老谭→P1-3），但**导演 LLM 只拿到口播稿文本，完全不知道稿件的结构意图**。
- 它不知道：开头 5 秒是精心设计的冲击钩子（可能配个大蓝天）、哪里是争议预埋（需视觉配合张力）、哪里是回收句（需视觉收束）、哪里是呼吸点（需视觉放松）。
- **结果**：导演对着文字"盲配画面"，跟稿件层信息完全脱节。这是视觉层**最上游的根问题**，比"首帧静态卡"更根本。
- **解法方向**：把稿件的结构意图（钩子/预埋/回收/呼吸点/金句）**显式传给导演**——比如随口播稿给一个"结构标记"（每段的情绪/视觉意图），导演据此配画面，而不是盲配。

### 视觉层整治候选方案（供讨论）
1. **结构意图传给导演**：给导演输入加"每段视觉意图标记"（钩子/预埋/回收/呼吸/金句 → 建议画面情绪/类型）
2. **前 5 秒视觉兜听觉**：标题+开头台词贴字 ≥5 秒（ID-042 B）
3. **首帧禁空卡**：hf_title 不得独占首帧，首帧要么 host 出镜要么承载台词
4. **C 线恢复**：laotan 出镜能力齐全，恢复 host 开场治 2s 跳出

**⚠️ C 线决策（2026-08-11，用户拍板）**：
- **C 线（数字人出镜）保持关闭，不恢复**。
- 原因：低粉阶段，数字人/真人/有人/无人都不影响数据。**关了 = 少一个判断干扰因素**，让留存数据纯净反映内容本身（稿件+视觉），不被"有没有人出镜"污染。
- **修正**：视觉层走"无人出镜"路线，首帧不是 host 出镜，而是**有冲击力的动态画面 / 承载台词的字幕卡**（不能是空卡）。C 线能力保留（laotan 配置齐全），但当前实验期不用。

**✅ 视觉层两步已实现（2026-08-11）**：
1. **导演用改造稿**：`_llm.py` `script_text = script.boosted_text or script.script_text`——导演配观众实际听到的爆品改造稿，而非旧洗稿稿（修复视听觉错位）。
2. **结构意图传导演（解盲盒）**：新增 `director_prompt/_intent.py` `extract_visual_intent()`——从改造稿提取情绪标签/预埋/回收/呼吸点 → 传给 `build_director_prompt` 的 `visual_intent` 参数 → 导演按"钩子/预埋/回收/呼吸/情绪"配画面，禁止蓝天白云配冲击段。
- 验证：extract_visual_intent 正确识别情绪×3/结构×2/呼吸×1。

### ID-043：【对标基准】对标视频六维拆解（求解式深度解说，不露脸）

> 用户对标视频（求解式深度解说、不露脸）的六维拆解，是"你追求的创作模式"的教科书。每条都可直接落地，作为后续稿件/视觉/配音的对照基准。

**一、开篇（0-15s 最大亮点）**：
- 不新闻式平铺，直接抛大众疑惑制造信息缺口。一上来和观众站在同一位置（非讲师居高临下）。
- 第一句就点明冲突/反常识 → 5 秒留存占优。背景后置。
- ⚠️ 易犯错误：开篇铺垫一大段背景再抛疑问，观众没等到钩子已划走。（= 爆品改造 P1 要解决的）

**二、文稿叙事逻辑（内核）**：
- **问题链驱动**（①疑问→解答；②随之疑问→解答；③再疑问→解答），非时间线驱动。素材永远服务问题，不堆砌新闻。
- **事实 vs 推论边界清晰**：客观事实明确讲；推测主动告知"基于现有信息推演，非既定事实，会变"。好处：①账号安全规避地缘风险 ②提升信任感。
- **解释"舆论现象本身"**：不只讲事件，还解释网上为何出现这种声音。拉开与资讯博主差距，收藏率提高。
- **信息筛选拒绝过载**：只保留对解答核心疑问有用的，次要细节舍弃。调研可海量，写稿狠心删减。（= 我们发现的"密度压缩"盲区）

**三、人声配音节奏**：
- 语速平稳克制，不激昂不煽情。理性探讨讲述感。
- **地缘稿件 1.0 倍速，AI 科技 1.2 倍速**（地缘信息密度高，语速过快 30s 留存受损）。（= ID-042 配音问题 C1）
- **停顿设计**：关键疑问/结论前短暂停顿，留消化时间。后期可人工制造停顿。
- 语音立场客观中立，不带好恶站队。情绪换点赞，理性深度换收藏关注（涨粉核心）。

**四、画面剪辑**：
- 拒绝素材轰炸，画面更换偏慢。大量静态图片/地图/资料截图。画面唯一使命=辅助理解，不靠眼花缭乱刺激眼球。
- **地图使用是亮点**：地缘博弈适时插简化地图，抽象文字配地图理解门槛大降。启示：地缘文稿能放地图就放。
- **字幕重点高亮**：关键概念/疑问/结论单独高亮放大，不全文铺满。观众开静音也能捕捉核心信息。（= ID-042 前5秒视觉兜底）

**五、结尾处理**：
- 不强行盖棺定论。复杂事件信息不完整，强总结既失真风险高。**结尾复盘梳理逻辑，列 2-3 条演化路径，点明每条的成立前提**。
- 温和互动引导，不生硬乞讨评论。顺着问题抛衍生思考题，评论区质量高。（= 爆品改造 P2 预埋回收方向一致）

**六、整体 IP 气质**：
- 塑造"求知者/分析者"而非无所不知的专家。给观众"他也在思考，把思考过程展示给我看"。
- 观众关注不是因为他知道答案，而是他**思考问题的方式有启发**。

**对照自查清单**（写稿后剪辑前逐条对照）：
✅开篇：第一句抛反常识疑问？还是先大段背景？
✅主线：问题链驱动 还是 事件时间流水账？
✅边界：事实和推演区分？有无绝对化预言？
✅素材：是否舍不得删减全堆砌？
✅配音：地缘 1.0 倍？必要停顿？
✅立场：克制没站队输出情绪？
✅画面：有无无意义素材轰炸？善用地图？
✅字幕：关键结论/疑问高亮，不是全文铺满？
✅结尾：不强求唯一答案，列可能，自然引导互动？

**可立刻做到**：开篇钩子改造、文稿问题链、事实推论区分、画面不堆砌、结尾处理。
**需慢慢打磨**：提问质量、资料取舍判断力、配音停顿节奏。
**当前主要差距集中在**：开篇钩子、文稿删减取舍、画面素材运用三块。

**与已有工作关联**：
- 开篇钩子 = 爆品改造 P1（已做）
- 文稿删减取舍 = ID-041"密度压缩"盲区（待做）
- 画面素材运用 = ID-042 视觉层（待做）
- 配音语速 = ID-042 C（待做）
- 结尾演化路径 = 爆品改造 P2 回收 + P3（已做，可对照强化）

### ID-044：【对标基准】工具型爆款拆解（心理测试×知识科普×系列化，汤三·Psyche）

> 第二份对标基准，与 ID-043（求解式深度解说）是两种不同爆款模型。本条为"工具/参与型"，财经内容接近 ID-043 的理性深度，但可吸收本条的**工具化+彩蛋+测试题**做增强。

**数据**：18:21 视频，点赞17.7万，收藏7.5万(≈42%)，分享3.2万(≈18%)，评论5574。收藏/分享比例 = 工具型爆款标志（"有用到必须存"+社交货币强）。

**标题公式**：集数编号 + 痛点提问 + 时间量化承诺 + 具体内容量 + 互动钩子。
例："第12集 | 你的天赋到底在哪里，18分钟科学详解「8条天赋分支」！每条天赋后都有测试题哦~"

**结构（总-分-总）**：
- 引言27s痛点共鸣 → 理论背书(哈佛/权威) → 全景地图 → 8 大智能各 1.5-2.5min 均匀节奏（适合跳看）→ 彩蛋 → 总结
- 前两个板块信息密度高峰（先喂饱再递减）
- **彩蛋设计**：观众以为讲完时再加一个，制造超预期交付，防提前退出

**钩子（三层嵌套）**：
- 开头钩（痛点）→ 权威钩（哈佛背书）→ 进度钩（章节时间戳"还有X个没看"）→ 互动钩（测试题）→ 悬念钩（彩蛋）→ 评论区钩（弹幕玩梗）

**核心钩子逻辑**：不是震惊体，是"自我发现"钩（巴纳姆效应+心理测试瘾）——"每个人都想知道自己属于哪一类"。

**互动**：
- 测试题 = 天然停顿点（观众暂停思考，提升完播）
- 高赞评论全是"天赋在另一个时空"的玩梗段子 → 段子型评论区天然带分享属性
- 搜索热词"内省智能测试" = 观众看完主动搜索，最强行为转化信号

**关注引导（隐性）**：
- 合集绑定（第12集，右侧整个系列）→ 看完自然看其他集
- 系列编号制造 FOMO
- 作者名即品类（"认知科普"）→ 关注后知道持续获得什么
- 赞粉比14.6:1 → 路人点赞多但关注转化有空间

**可落地到财经/数字人内容**：
1. **工具化拉收藏**：财经稿加"对照清单/自查步骤/三个信号"，抬收藏率（我们收藏24≈40%点赞，比例已接近，可强设计再抬）
2. **彩蛋设计**：正文讲完后补一个"彩蛋"，防提前退出
3. **测试题=停顿点**：每段论证后抛自测/反问，既是互动又是天然停顿
4. **章节视觉分段**：每段配清晰视觉标记，观众可跳看（关联 ID-042 视觉层）
5. **合集系列化**：未来矩阵化后用"系列编号"制造 FOMO（关注引擎）
6. **评论玩梗**：印证爆品改造 P2"讨论预埋"方向（激发观众接梗）

### 视觉层完成态 + hf_quote 挂起（2026-08-11）

**已完成**：
- 导演用爆品改造稿（boosted_text）修复视听觉错位 + 结构意图传导演（_intent.py）解盲盒
- hf_opening 片头（v1 警告风 / v2 Apple / v3 财经 chrome-text）+ 执行层强制开场
- visual_director_v2.txt：视觉隐喻协议（禁素材库废话+符号映射）+ 开场/首帧规则 + hf_quote 提示词强化
- 控制字符修复（_json.py _clean_control_chars）——导演 LLM 偶发 JSON 控制字符/格式错误
- 引用卡 hf_quote_v1 模板 + 渲染链路已通（人像槽 base64 已验证可用）

**hf_quote 挂起（真正用到再说）**：
- 模板+渲染已就绪，但导演 LLM 对新增视觉类型采用率低（花边段仍用 hf_title，未用 hf_quote）
- 即使提示词加了对错示例/判据/信号词，导演仍倾向用熟悉的 hf_title/broll
- **判断**：hf_quote 依赖"花边段恰好是一句XX说X的引语"，很多稿子的花边不是这种形态；且人像素材未解决
- **结论**：挂起。遇到真有"名人言"引语的稿子、或人物素材库建好后再调导演触发
- **⚠️ 坑（2026-08-11）**：hf_quote **纯文字引用模式可用**（无人物/无名人物 → 不需要人像），只有"知名人物引语"才需要人像素材。本地库无人像图，所以**知名人物引用卡暂不可用**；无名/纯文字引用卡随时可用。别因为"想用人像"而阻塞纯文字引用卡的导演触发。

**待办**：
- [ ] 人物素材库（名人人像，用户负责准备素材）+ 人脸居中预处理
- [ ] 导演触发 hf_quote（有真实名人言稿子时调）
- ~~收尾 logo 卡~~（**砍掉**，2026-08-11 决策，等想用再说，不再补视觉场景）

### 配音层：语速按内容类型差异化（✅ 2026-08-11 完成）

**方案**：人物拆分，一人物一音色一语速（纯配置，不改代码）。
- 提示词：`laotan.txt` → `laotan-tech.txt`（科技）/ `laotan-geo.txt`（地缘），暂只改名，内容跑数据再调
- 音色：大学教授 → `大学教授·科技版`(speed=1.2) / `大学教授·地缘版`(speed=1.0)，复用原声纹
- host/persona：老谭 → `老谭聊科技`(tech提示词+科技音色) / `老谭聊地缘`(geo提示词+地缘音色)
- **使用**：主页选人物自动带出对应音色语速，解决"AI天然赢、地缘天然拉"
- 语速链路：`persona.voice_id → voice.config_json.params.speed → TTS atempo`

**待办**：
- [ ] 跑数据后调 tech/geo 提示词内容（关键词/叙事差异）

### 科技版提示词约束（✅ 2026-08-11 已加 laotan-tech）

laotan-tech 加【科技版专属约束】（高于通用规则）：
1. **去重词**：引导词/口头禅全篇≤1次（"这事儿""剥开看""咱们得看透"等）
2. **降密度**：每句≤20字，一句一意，禁长复合句
3. **比喻克制**：全篇强比喻≤3个，不连环，只放难懂处

**验证**：智谱稿 laotan-tech 洗稿，重复词消失、短句化、比喻≈3个，质量明显提升。

**⚠️ 记忆点（地缘版待调，2026-08-11，先不改）**：
- laotan-geo 目前=laotan 原样复制，**未加科技版那套约束**
- 地缘版将来可能要：**慢语速(1.0)+更深的背景纵深+更重的历史对照**（地缘深度稿的密度/比喻容忍度可能不同）
- 但**先不改**，跑地缘数据后再定约束。别在没数据时猜地缘版的调整方向

### 待办（ID-040 续）：
- [ ] 继续收集用户选题思维链（≥5-8 条后提炼共性）
- [ ] 提炼后：写"选题思维链提示词"（产出选题疑问/反差点/认知颠覆/调研清单）
- [ ] laotan 介入时机后移调研（多源调研 → 综合稿 → laotan 洗稿）

---

## 2026-08-13 ~ 08-15 批次（情绪链路 / boost 七层适配 / 素材聚合 / 三页拆分）

### ID-045：【功能】P5 情绪标注生产化 + 情绪链路全线打通（✅ 2026-08-13/08-14 完成）

- **状态**: done（8/13 方案落地 `improvements/已完成-20260813-P5情绪标注生产化.md`；8/14 链路三处连环 bug 修复后 IndexTTS 首次真正拿到情绪）
- **链路**：P5 段落级 `[情绪/强度1-7]` 标注 → `scripts.emotion_annotations` 落库 → TTS `synthesize_lines(emotion_segments=...)` → 导演 `_intent.py` 情绪转视觉意图
- **统一情绪字典**：`app/services/emotion_dict.py` — 8 维向量（happy/angry/.../calm）+ 强度档→α 坡度（0.30~0.60 步进 0.05），全链路共享
- **8/14 修复的三处连环 bug**：
  1. `scripts.py` P5 落库 key 错（`emotion_annotations`→`p5_annotated` 写错，读回恒 None → IndexTTS 永走 calm）
  2. `tts_service.py` 不消费 `emotion_annotations`（新增 `_parse_emotion_annotations` + `resolve_emotion`）
  3. 段落拼接破音 → `_concat_wavs_with_fade`（fade 消段接缝，gap=0）
- **配套**：`lines.py` 按 P5 情绪段落分组行、每批带情绪参数；`enable_thinking: False`（DeepSeek-V4-Flash reasoning 失控思考，单步 110s→15s）
- **文档**: [p5_情绪标注升级方案.md](p5_情绪标注升级方案.md)（注意：其中 P1-P3 标意图的三层分工已被 ID-046 砍除）、[tts_emotion_experiments.md](tts_emotion_experiments.md)（α 参数定稿依据）

### ID-046：【重构】爆品改造 boost 七层适配 — P1-P3 砍除（✅ 2026-08-14 完成）

- **状态**: done（基于 `_test_7layer_ab.py` A/B 实证：7 层洗稿稿已是完整爆款结构，P1(电击开场)/P2(预埋)/P3(呼吸点) 是旧六模块逻辑、对七层稿纯破坏）
- **新流水线**：`run_boost` 只保留 **P4（逐句精修）→ P5（情绪标注）**，`boost_titles` 恒空（P1 砍掉）
- **P4_PROMPT 重写**：结构锁定铁律（1:1 锁结构/身份段/结尾/钩子）+ 信息守恒（字数 ≥95%、数字零丢失、数字锚定、型号连字符转中文读法）+ **兜底：输出 <88% 原文长度视为越权压缩 → 回退原稿**
- **LLM 通道**：`_resolve_llm_cfg` 硅基流动(siliconflow)优先、DeepSeek 回退；`_call` 默认 flash；新增 `config/siliconflow.yaml`
- **清洗**：`clean_boosted_text` 剥 `## 第X层` 标题 / `【888999000】` 锚点行 / "（此处口播为X）"标注；`_find_end` 加正文锚点优先定位
- ⚠️ ID-039 的 P1∥P2→P3 编排已被本条推翻；`improvements/爆品改造-阶段提示词.md` 已转历史参考

### ID-047：【功能】素材聚合层（七层喂饱）+ 智谱定向补搜（✅ 2026-08-15 上线）

- **状态**: done（已上线；无包 827 字 → 带包 1843 字实测）
- **背景**：7 层模板要求 1370~1550 字且每层需特定信息类型（背景/参数/实测/商业），单篇原文喂不饱 L3~L6 导致字数塌陷
- **新模块**：`app/routers/materials.py`（8 端点：素材包 CRUD / items 增删(URL 抓取+手动粘贴) / 重新审计 / 定向补搜）+ `app/services/material_service.py` + `app/services/zhipu_search.py`；后台 daemon 线程（照抄 boost 模式），SSE：`material_fetch_progress / material_search_start / material_audit_start / material_done / material_error`
- **新表**：`material_packages`（status/audit_json 七层审计/search_rounds）+ `material_items`（source_type=url|manual|search / layer_tags 审计回填）；`scripts.material_package_id` 回溯
- **七层审计**：LLM JSON 审计每层 applicable/覆盖度；**applicable 跨轮锁定防翻转**（补搜后重审沿用首轮判定，重置需新建包）
- **精选制注入**（实验结论）：全量注入稀释主题/人设——仅 L3~L6 分桶、每层 ≤3 条、单条 800 字、search 素材无层标注即丢弃；洗稿注入块尾部带"审计缺口提示：未覆盖的层不要编造"
- **智谱补搜**：独立 `/web_search` 端点；缺口补搜词 cap 6；link+同源系列标题去重；**免费额度 2026-09-12 到期，客户端日期比对 + 服务端额度关键词双保险拦截**（明确中文报错不静默），前端常显到期提示
- **待办**：
  - [ ] 投稿数据验证素材包对完播/字数的实际增益
  - [ ] 智谱额度 2026-09-12 到期前换搜索源或充值
  - [ ] ⚠️ `config/siliconflow.yaml` 硬编码真实 api_key，应移入 `.env`

### ID-048：【重构】流水线前端三页拆分（✅ 2026-08-15 完成）

- **状态**: done
- **拆分**：原 `index.html` 单页（文章→洗稿→音频一条龙）→ 三页：
  - `index.html` + `news.js` — **新闻线索页**：文章输入 + 素材包面板（多 URL 批量抓取/手动贴/七层红绿审计 chip/补搜词 checkbox/一键补搜）+ 评论层面板（五种评论人设渲染）
  - `writing.html` + `writing.js` — **文字加工中心**：洗稿/修正观点/爆品改造/保存 + 素材包徽章 + 字数实时统计（目标 2100~2400）+ URL 带参跳转（article_id/package_id）
  - `audio.html` + `audio.js` — **音频加工中心**：段落勾选/拖拽 + 音色 + C/P/H 管线 + 一键成片 + **persona 音色锁**（按 `script.prompt_template` 调 `/api/personas/by-template/{template}`）
- **app.js v6→v7**：879→213 行，只留跨页共享层（api/status/toggle/toast/管线开关），全元素 null 守卫；**删除 index.js**；全站 9 页 nav 统一三链接
- **验证**：`scripts/_verify_pages.py`（Playwright 三页 console 错误 + 跳转链断言）
- **配套**：`POST /api/articles/{id}/deconstruct` 独立解构端点（SSE），五种评论区人设（tech_explainer/national_supporter/brand_fan/brand_hater/source_tracker）伪评论注入洗稿 —— ID-041 的解构接入流程就此固化

### ID-049：【优化】素材匹配门槛重构 + 导演台/音频一致性杂项（✅ 2026-08-14/15 完成）

- **素材匹配（`asset_matcher.py`）**：
  - location 硬过滤改折中：strict 为空才放宽 foreign 并标 `location_relaxed=True`（本地库 foreign 占 1215/1672，原一刀切全灭）
  - 门槛维（scenes/shot_types/tone，3 中 ≥2）与加分维（motion/content_density/time_of_day 不排除）拆分，与导演 `_constants.py` 对齐
  - 同 job 素材硬排除（`params_json["local_file"]` 写回）；`preference=="dislike"` 本地线也排除
  - **成片复用硬上限**：`used_count >= local_asset_max_uses`（config 默认 2）出局，防"万能素材"每片被选
- **导演台新端点**：`POST /jobs/{id}/slots/{id}/replace-material`（按 asset_no 换素材+同步重渲染）、`GET /jobs/{id}/slots/{id}/preview`（单 slot 预览）；retry 加 `force_pexels`；broll_pexels 剥离与 API orientation 矛盾的方位词（vertical/portrait 导致 Pexels 全拒）
- **规划质量钳制（`_postprocess.py`）**：最小 slot 时长（broll 2.5s / HF 卡 3.0s）、hf_title ≤5 张、碎片并入、同秒去重、**时间轴满铺**（修 323s 音频 223s 处 8.7s 空洞致成片音轨错位）
- **音频过期一致性**：编辑文稿/最终稿 → 旧 completed 音频标 `stale`；编辑 boosted_text 后后台线程重跑 P5；生成音频时清 stale wav+记录（杜绝断点续传误复用旧音频）；脚本列表排序 created_at→updated_at
- **HF 渲染提速参数化**：`workers`（多 Chrome 并行）/ `fast_capture`（~2x）/ `gpu_encode`（NVENC）

---

## 2026-08-15 J 线上线后新增（导演关键词 + 新素材源）

### ID-050：【优化】P 线关键词提示词 — 抽象概念词 Pexels 匹配差（2026-08-15 用户实测反馈）

- **现象**：导演给出的 `artificial intelligence / data center / server room / digital graph` 匹配效果不好
- **根因**：`visual_director_v2.txt` §检索关键词有"主体优先铁律"但**没有概念→具象的翻译层**——LLM 直接输出文稿里的抽象概念词，而 Pexels 检索只对"摄像机拍得到的具体物"友好（"artificial intelligence"返回的是烂大街的神经网络素材；"digital graph"根本不是摄影词）
- **改法**（提示词层）：
  1. 加硬规则：**关键词必须是"镜头能拍到的东西"**，禁抽象概念词（AI/智能/数据/科技/数字/digital/intelligence/technology 一律不得直接出现）
  2. 加【概念→具象映射表】few-shot：`AI → circuit board close up / robot arm factory / programmer typing code`；`数据中心 → server racks corridor / network cables`；`数据图表 → stock market screen / dashboard screen close up`
  3. 每词 ≤3 个英文单词，名词短语，不加修饰语
- **验证**：同一篇稿子改前/改后各跑一次导演，对比 Pexels 下载素材的可用率

### ID-051：【素材源】flaticon 视频动效版 SVG 图标/大厂 logo（2026-08-15 用户提供方向）

- **价值**：科技财经稿必备的**图标与公司 logo**（英伟达/华为/OpenAI...），P 线永远不会有，HF 线手画质量不够——flaticon 的动效 SVG 正好补这块
- **落点**：与 J 线天然契合——SVG 可转 PNG 序列/GIF 进草稿贴纸轨，或做进 HF 模板；建议进 `jy_effect_library` 素材清单
- **⚠️ 合规待确认**：flaticon 免费版商用需**署名**（attribution）；大厂 logo 本身有商标权问题（内容里"报道引用"通常可，做品牌装饰有风险）——批量使用前确认授权方案（付费版免署名）
- **待做**：调研动效 SVG → 剪映可用形态（贴纸/WebM 透明通道）的转换管线

### ID-052：【素材源】canva 图表 — 比 HF 线精良、导出基本无水印（2026-08-15 用户提供方向）

- **价值**：canva 图表模板质量远超 HF 线自制，导出即用
- **落点**：两条路——① 手动精修通道：hf_chart 类 slot 允许"canva 素材替换"（导演台已有 replace-material 端点，正好用）；② 建 canva 图表素材库进本地素材库（video_assets），C 线碰撞复用
- **⚠️ 合规待确认**：canva 内容许可协议对"导出素材脱离设计单独复用"有限制条款（免费素材可入设计、单独提取复用属灰色）——矩阵化商用前要过一遍
- **定位**：HF 线保持全自动兜底，canva 作为**精修增强**（人工半自动），不替代

### 近期（当前周期可推进）
1. ~~ID-001：URL 自动抓取~~（done）
2. ~~ID-008：前端模型选择开关~~（done）
3. ~~ID-007：导演选择 UI 优化~~（done）
4. ~~ID-013：数字人出镜次数硬约束~~（done）
5. ~~ID-015：ComfyUI 输入图质检~~（done）
6. ~~ID-016：TTS 句内截断修复~~（done）
7. ~~ID-017：library.html 视频播放修复~~（done）
8. ~~ID-018：导演台 SSE 长静默阶段心跳升级~~（done）
9. ~~ID-019：index.html 音频任务刷新/跳页后丢失修复~~（done）
10. ~~ID-020：导演台无音频脚本一键生成 + 僵尸音频任务清理~~（done）
11. ~~ID-021：导演台脚本删除功能（级联 + 回收站）~~（done）
12. ~~ID-022：导演台任务刷新/跳页后状态恢复~~（done）

### 中期
5. ~~ID-003：本地素材库索引~~（done — 2026-07-27 完成 pexels_service.resolve + 2026-07-31 视频库自动入库）
6. ~~ID-002：视觉导演 Agent 2.0 接口~~（done — 2026-08-01 阶段 7 文档收尾）
7. ID-006：爬虫接入 articles 表

### 已完成（已从远期移除）
- ID-004：动态素材渲染（done 2026-08-03，HF/hf_title/hf_chart 渲染链已投入生产）
- ID-005：视频合成引擎（done 2026-08-03，composition_service 全链路跑通 + v3 零拷贝优化完成）
- ID-031：导演生产路径优化 v3（done 2026-08-03，8 阶段零拷贝流水线）
- ID-039：爆品改造流水线（done 2026-08-11，Boost Service 三 Pass 编排已集成，待投放数据验证）

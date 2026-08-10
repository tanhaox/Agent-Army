# 进行中-20260808-video_tagging_service-诊断报告

**文件**: `app/services/video_tagging_service.py`(828 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成 — 拆分为包 (11 模块 / 1270 行), 见 [已完成-20260808-video_tagging_service-架构重构](已完成-20260808-video_tagging_service-架构重构.md)

## 现状

视频素材 AI 打标编排器 — 4 通道智能分析流水线(scdet 智能抽帧 → 运动分析 → OCR 预扫 → LLM 综合打标) → 写入数据库,后台线程执行,进度经 `director_events` 推送,完成后重建关键词词表包 (ID-034)。

**公共 API(4 个)**: `start_tagging_job` / `tag_single_asset` / `get_job_status` / `cancel_job` — 被 `app/routers/tagging.py:17-22` 导入(唯一代码引用面)。`director_prompt.py:506/553` 仅为注释提及,无代码引用。

**顶层结构** (18 个函数, 0 个类):

| 函数 | 行 | 职责 | 类别 |
|---|---|---|---|
| `_now_iso` | 2 | UTC 时间戳 | 工具 |
| `_build_enriched_user_prompt` | 33 | 通道 2/3 结果注入 user prompt | Prompt |
| `_extract_frame_at` | 27 | ffmpeg 单帧提取(内部工具) | [已废弃] |
| `extract_keyframes` | 24 | 25/50/75% 三帧抽取(向后兼容) | [已废弃] |
| `_try_parse_json` | 18 | LLM 输出 JSON 多层提取 | 解析 |
| `_validate_tag` | 11 | 单维度标签校验过滤 | 解析 |
| `frame_tagging_result` | **57** | LLM 输出→结构化标签,失败回退规则引擎 | 解析 |
| `_is_llama_running` | 8 | llama-server 健康检查 | llama |
| `_ensure_llama_server` | **60** | 确保 llama-server 运行,未运行自动拉起 | llama |
| `_kill_port_owner` | 22 | Windows 杀端口占用进程 | llama |
| `_run_pipeline_for_asset` | **91** | 单素材 4 通道流水线 | 编排 |
| `_write_asset_tags` | 27 | 标签写库(独立 session) | DB |
| `_rebuild_vocabulary_pack` | 12 | 重建词表包 (ID-034, lazy import) | DB |
| `_run_tagging_job_thread` | **149** | 后台线程主循环: 状态机+进度+取消+写回 | 编排 |
| `start_tagging_job` | **43** | 启动批量任务(线程) | API |
| `tag_single_asset` | **44** | 同步单素材打标 | API |
| `get_job_status` | 4 | 查询任务状态 | API |
| `cancel_job` | 7 | 请求取消 | API |

**全局状态**: `_jobs: dict[str, dict]` + `_jobs_lock = threading.Lock()`(跨 `start_tagging_job` / `get_job_status` / `cancel_job` / `_run_tagging_job_thread` 共享)。`_LLAMA_PROC` + `_LLAMA_PROC_LOCK`(llama 子进程句柄,仅 llama 模块内用)。

## 问题 (违反硬性约束)

**文件超限**: 828 行 > 250。

**6 个超限函数** (均 >40 行):

| 函数 | 行数 | 拆分方案 | 状态 |
|---|---|---|---|
| `frame_tagging_result` | 57 | 拆 `_build_fallback_result`(回退 dict)+ `_apply_validated_tags`(校验后 result 组装) | ⏳ 待拆 |
| `_ensure_llama_server` | 60 | 拆 `_spawn_llama_server`(Popen 启动)+ `_wait_llama_ready`(120s 轮询) | ⏳ 待拆 |
| `_run_pipeline_for_asset` | 91 | 拆 `_run_channel1_frames`(抽帧+空帧回退)/`_run_channel2_motion`/`_run_channel3_ocr`/`_run_channel4_llm`(LLM 调用+异常收敛)/`_inject_analysis_extra`(通道2/3 注入 `_ai_extra`) | ⏳ 待拆 |
| `_run_tagging_job_thread` | 149 | 拆 `_mark_running`/`_fail_startup`(llama 启动失败)/`_check_cancelled`(循环内取消)/`_load_asset_context`(素材加载)/`_register_missing_asset`(素材不存在)/`_cleanup_frames`(临时帧清理)/`_finalize_thread`(循环后完成/取消) | ⏳ 待拆 |
| `start_tagging_job` | 43 | 拆 `_resolve_asset_ids`(None→全量查询)+`_spawn_thread`(线程启动) | ⏳ 待拆 |
| `tag_single_asset` | 44 | 拆 `_load_single_asset_context`(素材+fallback 加载) | ⏳ 待拆 |

**其他需处理**:
- `frame_tagging_result` 内部 3 处 `return {**fallback_tags, "_fallback": True, "_ai_raw": ...}` 结构重复 → 收敛到 `_build_fallback_result` helper(3 参: fallback/raw/_ai_raw 值)。
- `_jobs` / `_jobs_lock` 被 4 个 API 共享 → 放入 `jobs.py` 模块级。
- `SYSTEM_PROMPT` 与 `_LLAMA_*` 常量(含磁盘路径/端口)当前散落模块顶层 → 归 `constants.py`。
- `extract_keyframes` / `_extract_frame_at` 已废弃但保留向后兼容(公共面) → 归 `legacy_frames.py`,行为不变。

## 依赖与调用面

- **接入点**: `app/routers/tagging.py:17-22` — `from ..services.video_tagging_service import (cancel_job, get_job_status, start_tagging_job, tag_single_asset)`。
- **顶层 imports**: `json`/`logging`/`os`/`re`/`subprocess`/`tempfile`/`threading`/`time`/`urllib.request`/`uuid`/`datetime`/`Path`/`Any` + `get_config`/`db_session`/`get_session_maker`/`VideoAsset`/`infer_tags`/`publish`/`smart_extract_frames`/`LocalLLMClient`/`LocalLLMError`/`analyze_motion`/`ocr_scan_frames`。全部有使用,无死代码。
  - ⚠ `get_session_maker` 导入但**未使用**(死代码)→ 重构时移除。
- **依赖服务**: `asset_tagging.infer_tags` / `director_events.publish` / `frame_extraction.smart_extract_frames` / `local_llm_client` / `motion_analysis.analyze_motion` / `ocr_scan.ocr_scan_frames` — 均不反向引用本模块。
- **循环导入风险**: `_rebuild_vocabulary_pack` 延迟 import `director_prompt`(原注释: 避免模块级 import 冲突)→ **保留 lazy import 不变**。`tagging.py` router 延迟导入路径不变。

## 依赖方向

`video_tagging_service/` → `config` / `database` / `models` / `asset_tagging` / `director_events` / `frame_extraction` / `local_llm_client` / `motion_analysis` / `ocr_scan` / `director_prompt`(延迟)。无反向依赖,无循环。

## 重构方向

**方案: 拆为 `app/services/video_tagging_service/` 包**(与旧模块同名 — 参照 composition_service 结论: 同名包优先于同名模块, 原 `.py` shim 是不可达死代码, send2trash 删除不留)。调用面 `from ..services.video_tagging_service import (...)` 自动解析到包, **零改动**。

| 新模块 | 内容 | 预估行数 |
|---|---|---|
| `__init__.py` | re-export 4 个公共 API + `__all__` + 包布局 docstring | ~20 |
| `constants.py` | `ALL_SCENES`/`ALL_SHOT_TYPES`/`TONE_VALUES`/`DENSITY_VALUES`/`MOTION_VALUES`/`TIME_OF_DAY_VALUES`/`SYSTEM_PROMPT`/`_LLAMA_*` | ~110 |
| `parse.py` | `_JSON_PATTERN`/`_try_parse_json`/`_validate_tag`/`frame_tagging_result` + `_build_fallback_result`/`_apply_validated_tags` | ~90 |
| `llama.py` | `_is_llama_running`/`_ensure_llama_server`/`_kill_port_owner` + `_spawn_llama_server`/`_wait_llama_ready` | ~110 |
| `legacy_frames.py` | `_extract_frame_at`/`extract_keyframes`(已废弃向后兼容) | ~60 |
| `pipeline.py` | `_build_enriched_user_prompt`/`_run_pipeline_for_asset` + `_run_channel1_frames`/`_run_channel2_motion`/`_run_channel3_ocr`/`_run_channel4_llm`/`_inject_analysis_extra` | ~180 |
| `store.py` | `_write_asset_tags`/`_rebuild_vocabulary_pack` | ~50 |
| `jobs.py` | `_now_iso`/`_jobs`/`_jobs_lock`/`_run_tagging_job_thread`(主循环)+ `_mark_running`/`_fail_startup`/`_check_cancelled`/`_load_asset_context`/`_register_missing_asset`/`_cleanup_frames`/`_finalize_thread`/`start_tagging_job`/`get_job_status`/`cancel_job` | ~230 |
| `single.py` | `tag_single_asset` + `_load_single_asset_context` | ~60 |

**约束达成预估**: 全模块 ≤250 行; 超限函数全部收窄(编排函数 `_run_tagging_job_thread` 目标 ~65, 其余 ≤40 物理行); 绝对导入; `__all__` 齐全; 移除 `get_session_maker` 死代码; 无新增死代码。

## 行为契约 (重构后必须逐字保持)

- **公共 API 签名/返回**:
  - `start_tagging_job(asset_ids: list[str] | None = None) -> str` — 无素材时 `raise ValueError("没有可打标的素材")`; 返回 12 位 hex job_id; `_jobs[job_id]` 初始 dict 含 `status="pending"`/`total`/`done=0`/`failed=0`/`current_asset_no=None`/`started_at=None`/`finished_at=None`/`cancelled=False`。
  - `tag_single_asset(asset_id) -> dict` — 返回 dict 含 `_success`/`_error`/`_asset_no`/`_fallback`/`_ai_raw` 等; llama 未启动 → `{"_success": False, "_error": "llama-server 无法启动"}`; asset 不存在 → `{"_success": False, "_error": f"Asset not found: {asset_id}"}`。
  - `get_job_status(job_id) -> dict | None` — 不存在返回 `None`; 存在返回**副本**(`.copy()`, 防外部改全局)。
  - `cancel_job(job_id) -> bool` — 不存在或 status ∈ {completed, failed, cancelled} → `False`; 否则置 `cancelled=True` 返回 `True`。
- **SSE 事件 type 与字段逐字**: `complete`(error 时含 `error`)、`start`、`progress`(含 `current_asset_no`/`msg`)、`cancelled`、`item_done`、`channel`(含 `channel`/`channel_total=4`/`channel_name`/`done`/`failed`/`total`/`current_asset_no`/`msg`)。msg 逐字: `开始 AI 打标 (4通道流水线), 共 {total} 个素材`、`素材不存在: {aid}`、`正在处理 {asset_no} ({done + 1}/{total}) — 4通道流水线`、`完成 {asset_no} {'✓' if not tags.get('_fallback') else '⚠ 回退规则'}`、`AI 打标已取消: {done} 处理, {failed} 失败/回退`、`AI 打标完成: {done} 处理, {failed} 失败/回退`、通道 msg `{asset_no}: 抽帧完成 ({len(frames)} 帧)`/`{asset_no}: 运动分析完成`/`{asset_no}: OCR 预扫完成`/`{asset_no}: LLM 综合打标中…`。
- **任务状态机**: running 后置 `started_at`; 取消分支先置 `cancelled`+`finished_at` 再 publish; 循环末尾 `_jobs[job_id].get("cancelled")` **先于 completed 判定**; `all_failed = failed >= total` → status `failed` 否则 `completed`; `finished_at` 总是 `_now_iso()`。
- **进度计数语义**: 素材不存在 → `failed += 1; done += 1`(两个都加); 写库失败 `not ok` → `failed += 1`(done 已加); `_fallback` 命中 → `failed += 1`(done 已加)。每次变更后 `_jobs[job_id].update({"done": done, "failed": failed})`。
- **llama 启动**: 健康检查 GET `{host}:{port}/health` timeout=3; exe/model 缺失各自 `logger.error` 消息逐字; 启动前 `_kill_port_owner(8080)`; Popen 参数逐字(`-ngl 999`/`-c 32768`/`--device CUDA0`/`--sleep-idle-seconds 600` 等); 120s 轮询每秒 1 次; 超时置 `_LLAMA_PROC = None`。
- **4 通道流水线**: 无帧 → `{**fallback, "_fallback": True, "_ai_raw": "no frames extracted"}`; 通道 2/3 异常仅 warning 不中断; `LocalLLMError` → `{**fallback, "_fallback": True, "_ai_raw": f"LocalLLMError: {exc}"}`; 通道 2/3 结果注入 `_ai_extra`(`_motion_analysis`/`_ocr_scan`, 空则 None)。`job_id=None`(同步)时 publish 为 no-op。
- **DB 写回**: `asset.scenes/shot_types/source_type/location/people/description_zh` 默认值逐字(`"footage"`/`"foreign"`/`"none"`); `ai_tagged_at=datetime.now(timezone.utc)`; 失败 `logger.exception` + `session.rollback()` + 返回 False。
- **词表包重建**: 仅 3 处触发 — (1) 循环内取消且 `done > 0`; (2) 循环后非全失败; (3) `tag_single_asset` 且 `ok and not tags.get("_fallback")`。内部 lazy import `director_prompt.rebuild_vocabulary_pack(session)`, 异常仅记 `logger.exception`。
- **临时帧清理**: 循环内每素材后 `tmpdir.glob("frame_*.png")` unlink(`missing_ok=True`, OSError 忽略); `tempfile.TemporaryDirectory` 自动回收。同步单素材用 `prefix="tagging_single_"`。
- 所有 `logger` 消息逐字不变(带 `[pipeline:{asset_no}]`/`[tagging-job]`/`[llama]` 前缀)。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。

# 进行中-20260808-director-router-诊断报告

**文件**: `app/routers/director.py`(860 行)
**日期**: 2026-08-08
**阶段**: ✅ **已完成** — 拆分为 `app/routers/director_routes/` 包(10 模块),见 [已完成-20260808-director-router-架构重构.md](已完成-20260808-director-router-架构重构.md)。本报告保留诊断原始记录。

> **路径更正**: 待办清单中的 "director.py(864)" 实为 `app/routers/director.py`(860 行, FastAPI 路由层), 而非 services 下文件。`director_service.py`(524 行)是另一批待办。

## 现状

FastAPI 路由层, `director.router` 由 `app/main.py:299` `include_router` 接入。职责: Director 2.0 任务生命周期 8 类端点 + 3 个后台线程助手(`_plan_in_background`/`_execute_in_background`/`_compose_in_background`)。底层业务逻辑已下沉至 `director_service`/`slot_executor`/`composition_service`。

**顶层结构** (27 个函数, 0 个类, 含 11 个 @router 端点):

| 函数 | 行 | 职责 | 类别 |
|---|---|---|---|
| `_encode_pipelines` / `_decode_pipelines` | 4/7 | 管线约束三态编解码 (None/全关/部分) | 工具 |
| `_job_or_404` / `_slot_or_404` | 5/7 | DB 查询 + 404 | 工具 |
| `list_jobs` | 5 | 列任务 | GET 端点 |
| `_plan_in_background` | **59** | 后台规划线程: alignment + LLM + 事件透传 | 线程助手 |
| `create_job` | **74** | 创建任务 + 触发规划线程 | POST 端点 |
| `get_job` / `list_slots` | 2/8 | 详情 / slot 列表 | GET 端点 |
| `_execute_in_background` | 32 | 后台执行线程 | 线程助手 |
| `execute_job` | **53** | 触发后台执行 | POST 端点 |
| `_original_workflow` | 18 | trace replaced_from 链回退 | 工具 |
| `retry_slot` | **87** | 手动重试单 slot + 管线降级 | POST 端点 |
| `purge_replaced_slots` | 26 | 清理 replaced slot (连带删目录) | POST 端点 |
| `cancel_job` | 13 | 发送取消信号 | POST 端点 |
| `retry_by_workflow` | 32 | 按 workflow 批量重置 | POST 端点 |
| `_compose_in_background` | **70** | 后台合成线程 + SSE 进度 + 成品登记 | 线程助手 |
| `compose_job` | 30 | 触发后台合成 | POST 端点 |
| `download_job` | 15 | 下载产物 | GET 端点 |
| `open_output_folder` | 15 | 打开产物目录 | POST 端点 |
| `job_events` | 27 | SSE 进度流 | GET 端点 |
| `_find_composition_mp4` | 10 | manifest/回退找 mp4 | 工具 |
| `delete_job` | 13 | 删除任务 + 文件 | DELETE 端点 |
| `cleanup_jobs` | 32 | 批量清理 | POST 端点 |
| `_cleanup_job_files` | 15 | 删除 job 磁盘目录 | 工具 |

## 问题 (违反硬性约束)

**5 个超限函数** (均 >40 行):

| 函数 | 行数 | 拆分方案 | 状态 |
|---|---|---|---|
| `_plan_in_background` | 59 | 拆 `_plan_steps`(对齐+目录+LLM 主流程)+ `_mark_plan_failed`(异常收敛, 复用于 PlanCancelled/Exception 两条 except) | ✅ 已拆 |
| `create_job` | 74 | 拆 `_resolve_audio_id`(auto-pick 逻辑)+ `_validate_audio`(加载+存在性校验) | ✅ 已拆(37 物理行) |
| `execute_job` | 53 | 拆 `_decode_request_pipelines`(query 回退 job.pipelines + 三态解码)+ `_is_executable`(completed/failed 拦截判定) | ✅ 已拆(37 物理行, `_is_executable` 实际命名 `_check_executable`) |
| `retry_slot` | 87 | 拆 `_apply_retry_pipeline_degrade`(管线降级块)+ `_reset_slot_for_retry`(状态重置) | ✅ 已拆(39 物理行) |
| `_compose_in_background` | 70 | 拆 `_compose_start_trace` + `_compose_success`(成品登记+done trace)+ `_compose_failure`(异常收敛) | ✅ 已拆 |

## 依赖与调用面

- **唯一接入点**: `app/main.py:17` `from .routers import (…, director, …)` + `main.py:299` `app.include_router(director.router)`。无其他模块 import 本文件 → 循环导入面极窄。
- **顶层 imports 使用情况**(已逐个 grep 验证, 无死代码):
  - `director_service`: `create_director_plan`×3(其中 2 处模块级 import, 1 处延迟)、`mark_job_reviewed`×3、`replace_failed_slot`×6、`append_trace`×4(全为函数内延迟 import)。
  - `slot_executor`: `clear_cancel`/`execute_all_slots`/`execute_slot`/`is_cancelled`/`request_cancel` 均有使用。
  - `composition_service.compose_director_job`×4(1 处模块级 + 3 处延迟); `gpu_service_manager.get_gpu_service_manager`×2; `director_parser._best_fallback_workflow`×3; `director_events` 的 `publish`/`subscribe`/`unsubscribe`/`PlanCancelled`。
- **函数内延迟 import 观察**(保持现状可避循环): `_plan_in_background` 内的 `director_events`/`director_prompt.build_real_material_catalog`; `create_job` 内的 `director_events.publish`; `_compose_in_background` 内的 `director_events`/`composition_service`/`director_service.append_trace`; `_cleanup_job_files`/`purge_replaced_slots` 内的 `config`/`shutil`。
- **模块级常量**: `_WORKFLOW_PIPELINE`(7-key 映射)、`router`、`logger`、3 组 `_planning_jobs/_planning_lock`、`_executing_jobs/_executing_lock`、`_composing_jobs/_composing_lock`。

## 依赖方向

`routers/director` → `database` / `models` / `schemas` / `config`(延迟) / `services.director_service` / `services.slot_executor` / `services.composition_service`(延迟) / `services.director_events` / `services.director_prompt`(延迟) / `services.director_parser` / `services.gpu_service_manager` / `infrastructure`(经上述 service)。无反向依赖。

## 重构方向

**方案: 拆为 `app/routers/director_routes/` 包**, 端点按生命周期分组, 后台线程助手与工具函数下沉到私有子模块。最终 9 模块:

| 新模块 | 内容 |
|---|---|
| `__init__.py` | `router` 聚合 + 各分组 include_router + `__all__` |
| `common.py` | `_encode_pipelines`/`_decode_pipelines`/`_job_or_404`/`_slot_or_404`/`_WORKFLOW_PIPELINE`/`_find_composition_mp4`/`_cleanup_job_files` |
| `planning.py` | `create_job` + `_plan_in_background` + `_resolve_audio_id`/`_validate_audio`/`_plan_steps`/`_mark_plan_failed` |
| `execution.py` | `execute_job`/`_execute_in_background`/`cancel_job` + `_decode_request_pipelines`/`_is_executable` |
| `retry.py` | `retry_slot`/`retry_by_workflow`/`purge_replaced_slots` + `_original_workflow`/`_apply_retry_pipeline_degrade`/`_reset_slot_for_retry` |
| `compose.py` | `compose_job`/`_compose_in_background` + `_compose_start_trace`/`_compose_success`/`_compose_failure` |
| `download.py` | `download_job`/`open_output_folder` |
| `stream.py` | `job_events`(SSE) |
| `cleanup.py` | `delete_job`/`cleanup_jobs` |
| `list.py` | `list_jobs`/`get_job`/`list_slots` |

**注意**: 与 `slot_workflows` 批次同样的 shim 死代码问题 — 原文件 `app/routers/director.py` 若保留为 shim, 与包 `director_routes/` 同名? **不同名**(`director.py` vs `director_routes/`), 无冲突。但 `main.py:17` 引用的是 `routers.director` 模块名, 拆包后需改 `main.py` import 指向新包 (保持 `director.router` 属性名, 由包 `__init__.py` re-export, 最小改动)。原 `director.py` 删除(send2trash), 不留 shim — 见 slot_workflows 批次结论。

## 行为契约 (重构后必须逐字保持)

- 全部 11 个端点: 路由 path、HTTP 方法、response_model、状态码、HTTPException detail 逐字不变。
- 三态管线语义不变: None=全启用 / set()=全关 / 部分; `_encode_pipelines`(None→None, 空→"")与 `_decode_pipelines`(None→None, ""→set())落库列语义不变。
- 3 个后台线程: 各自锁/集合去重 (`_planning_jobs`/`_executing_jobs`/`_composing_jobs`)、threading.Thread daemon + name 模式、finally 清理、SSE 事件类型与 msg 逐字不变。
- `retry_slot` 管线降级顺序 + `_best_fallback_workflow` 降级 + black_placeholder 恢复原始 workflow 逻辑不变。
- `_find_composition_mp4`/`_cleanup_job_files`/`_cleanup_jobs` 磁盘路径与删除语义不变。
- 所有事件 msg 逐字不变 (plan_start/alignment_start/plan_done/plan_error/plan_cancelled/exec_done/compose_error/heartbeat 等)。

## 下一步

✅ **已完成**。拆分执行、行为契约断言、原文件 send2trash 删除、变更摘要均已落地。详见 [已完成-20260808-director-router-架构重构.md](已完成-20260808-director-router-架构重构.md)。

下一文件: **composition_service(593 行)** 诊断。

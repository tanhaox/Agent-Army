# 进行中-20260808-director_service-诊断报告

**文件**: `app/services/director_service.py`(524 行,无类,纯函数模块)
**日期**: 2026-08-08
**阶段**: ✅ 已完成 — 见 [已完成-20260808-director_service-架构重构.md](已完成-20260808-director_service-架构重构.md)

## 现状

Director Agent 2.0 公共 API。单一模块内聚 **5 大职责**:

1. **环节轨迹 (Trace)** — `append_trace`(34)/ `get_trace`(3)。复用 `plan_json["trace"]` 数组记录环节起止/状态/详情,无需新增 DB 列。
2. **对齐 (Alignment)** — `_align_fast_or_whisper`(52)/ `_collect_tts_segment_durations`(40)。TTS 时长快速对齐,缺时长时 Whisper 重转录兜底 (ID-024)。
3. **主规划 (create_director_plan)** — **249 行**,最大函数。音频对齐 → job 创建/更新 → LLM 工序单 → 时长 clamp → references 卡 → plan 落库 + slots 持久化。
4. **失败槽位替换 (Fallback)** — `replace_failed_slot`(69)。按管线开关/legacy 链选择替代工作流。
5. **作业生命周期 (Lifecycle)** — `mark_job_reviewed`(8)/ `complete_job_if_slots_done`(16)。

**公共 API**: `create_director_plan` / `replace_failed_slot` / `append_trace` / `mark_job_reviewed` / `complete_job_if_slots_done`。

## AST 测量 (物理行)

| 成员 | 行数 | 类型 |
|---|---|---|
| `create_director_plan` | **249** | OVER > 70 (核心编排, 多阶段) |
| `replace_failed_slot` | **69** | OVER > 40 (编排上限 70, 压线达标) |
| `_align_fast_or_whisper` | **52** | OVER > 40 (编排上限 70, 达标) |
| `_collect_tts_segment_durations` | 40 | OK (压线) |
| `append_trace` | 34 | OK |
| `complete_job_if_slots_done` | 16 | OK |
| `mark_job_reviewed` | 8 | OK |
| `get_trace` | 3 | OK |

无类、无超限类。**1 个超限函数**(`create_director_plan` 249 需拆),`replace_failed_slot`(69)与 `_align_fast_or_whisper`(52)压线编排上限。

## 问题 (违反硬性约束)

1. **文件 524 行 > 250** — 需拆包。
2. **`create_director_plan` 249 行** — 单函数做对齐/job 管理/LLM/落库 4+ 件事,远超编排上限 70,必须拆阶段。

## 依赖与调用面

**依赖**(均不反向引用,无循环导入风险):
- `app.services.director_events` — `PlanCancelled` / `publish` (`_evt`)
- `app.services.director_parser` — `parse_llm_plan` / `_HOST_FAMILY` / `_best_fallback_workflow`
- `app.services.director_prompt` — `build_director_prompt`
- `app.services.alignment_service` — `align_script_segments` / `align_from_tts_durations`
- `app.services.llm_service` — `LLMService`
- `app.config` / `app.models` / `app.schemas`(lazy)

**外部引用面(6 处代码 + 0 处测试)**:
| 引用方 | 符号 | 说明 |
|---|---|---|
| `app/routers/director_routes/planning.py:18` | `create_director_plan` | 顶层导入 |
| `app/routers/director_routes/compose.py:32,45,88` | `append_trace` | lazy 导入 |
| `app/routers/director_routes/execution.py:17,72` | `mark_job_reviewed` / `append_trace` | 顶层 + lazy |
| `app/services/slot_executor.py:16,370` | `replace_failed_slot` / `append_trace` / `complete_job_if_slots_done` | 顶层 + lazy |
| `scripts/verify_timeline.py:11` | `_collect_tts_segment_durations` | **私有符号外部引用**, __init__ 需 re-export |

`get_trace` 无外部引用,但为公共 API 稳定性保留 re-export。

## 行为契约 (逐字保持)

- **`append_trace`**: `_json` 参数跳过 deepcopy 就地 append;`detail[:400]` 截断;`n` 基于既有 trace 长度;`timespec="seconds"` UTC ISO;`_json is None` 时 `job.plan_json = plan` + `db.commit()`。
- **`_align_fast_or_whisper`**: fast path 事件消息 `"检查 TTS 段落时长…"`;fast 命中日志 `"[director %s] fast path: %d segments aligned from TTS durations"`;fallback 日志 `"[director %s] fast path unavailable, falling back to Whisper"` + 事件 `"段落时长不完整，改用 Whisper 转录…"`。
- **`_collect_tts_segment_durations`**: 查最新 completed AudioJob;任何 seg 缺 duration 即返回 None;空 result 返回 None。
- **`create_director_plan`**: 每个 evt 消息逐字(`alignment_progress` 对齐 N 段 / `alignment_done` 对齐完成 Xs / `llm_start` / `llm_done` / `llm_error`);trace step/status 逐字;alignment 失败 → job failed + `error_message=f"alignment failed: {alignment.get('error')}"`;LLM 失败 → `error_message=f"director agent failed: {type(exc).__name__}: {exc}"` + trace `plan_llm/error`;duration clamp 公式;references slot 15s / `hf_title` / `no_voiceover=True`;trace 保留 (prev_trace 覆盖前备份);slots 字段逐字 (`view_group_index=job.view_group_index or 0` / `status="queued"`)。
- **`replace_failed_slot`**: legacy 链 `["broll_pexels", "broll_local", "black_placeholder"]`;无管线链 `["broll_local", "black_placeholder"]`;family_priorities 三组逐字;`list(dict.fromkeys(...))` 去重;new_slot `params_json={"replaced_from": current, **slot.params_json}`;日志 `"Slot %s replaced: %s -> %s"`。
- **`mark_job_reviewed`**: 不存在抛 `ValueError(f"DirectorJob {job_id} not found")`。
- **`complete_job_if_slots_done`**: terminal set `{"completed", "failed", "replaced", "skipped"}`;any_failed → failed + `error_message=f"{len(failed)} slot(s) ultimately failed"`;completed_at UTC now。

## 拆分方案 (5 模块, 全部 ≤250 行)

| 新模块 | 职责 | 迁入函数 | 预估行数 |
|---|---|---|---|
| `__init__.py` | re-export 6 公共 API(含 `_collect_tts_segment_durations`)+ `get_trace` + `__all__` | — | ~30 |
| `_trace.py` | 环节轨迹 | `append_trace` / `get_trace` | ~45 |
| `_alignment.py` | TTS 快速对齐 + Whisper 兜底 | `_align_fast_or_whisper` / `_collect_tts_segment_durations` | ~100 |
| `_plan.py` | 主规划多阶段 | `create_director_plan` 编排 + `_resolve_inputs` / `_alignment_phase` / `_mark_plan_failed` / `_ensure_director_job` / `_llm_plan_phase` / `_postprocess_plan` / `_persist_plan` | ~250 |
| `_fallback.py` | 失败槽位替换 | `replace_failed_slot` | ~75 |
| `_lifecycle.py` | 作业生命周期 | `mark_job_reviewed` / `complete_job_if_slots_done` | ~30 |

**`create_director_plan` 249 行拆 7 阶段 helper**,编排函数压到 ≤20 行。`replace_failed_slot`(69)/ `_align_fast_or_whisper`(52)压线编排上限,不拆,以 `--orch` 声明。

## 实际拆分 (8 模块, 比方案多拆 2 个)

方案中 `_plan.py` 预估 ~250 行,实测编排 + 7 helper 达 338 行,超 250 上限。
将 LLM 阶段与后处理拆为独立模块,`_plan.py` 压到 211 行,编排函数 66 行:

| 新模块 | 职责 | 迁入函数 | 行数 |
|---|---|---|---|
| `_plan.py` | 主规划编排 | `create_director_plan`(66) + `_resolve_inputs` / `_record_alignment_done` / `_mark_plan_failed` / `_ensure_director_job` | 211 |
| `_llm.py` | LLM 工序单阶段 | `_llm_plan_phase`(53, 编排) | 78 |
| `_postprocess.py` | clamp / references 卡 / 落库 | `_clamp_slot_durations` / `_append_references_slot` / `_persist_plan` | 98 |

`_llm_plan_phase`(53)与 `create_director_plan`(66)均以 `--orch` 声明(编排上限 70)。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。

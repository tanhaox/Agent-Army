# 进行中-20260808-composition_service-诊断报告

**文件**: `app/services/composition_service.py`(589 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成 — 见 [已完成-20260808-composition_service-架构重构.md](已完成-20260808-composition_service-架构重构.md)

## 现状

合成服务, `compose_director_job` 将 DirectorJob 全部 completed slot 剪辑为最终 9:16 MP4。唯一对外导出 `compose_director_job`(被 `director_routes/compose.py:102` 后台线程与 `scripts/verify_retention.py:26` 引用); 5 个私有 helper 全仓无外部引用, 可自由拆分。

**顶层结构** (10 个函数, 0 个类, 无嵌套 with>2, 无 if/elif 链 >4 分支):

| 函数 | 行 | 职责 | 类别 |
|---|---|---|---|
| `_now` | 2 | UTC 时间戳 | 工具 |
| `_job_root` / `_ensure_root` | 3/4 | job 输出目录 | 工具 |
| `_cleanup_intermediates` | 39 | 删除中间件, 保留成片+manifest | 工具 |
| `_run_ffmpeg` | 6 | ffmpeg 薄包装(timeout 600) | 工具 |
| `_concat_demuxer_concat` | 31 | concat demuxer 无 crossfade 拼接 | ffmpeg |
| `_has_audio_stream` | 13 | ffprobe 检测音频流 | ffmpeg |
| `_loudnorm` | **66** | 两遍响度归一 (-14 LUFS) | ffmpeg |
| `_mix_master_audio` | **80** | 混入 TTS 主音轨 (分段时间轴) | 音频 |
| `compose_director_job` | **287** | 主流程: 幂等守卫→去重→REPAIR→concat→混音→loudnorm→校验→manifest→清理 | 编排 |

## 问题 (违反硬性约束)

**3 个超限函数** (均 >40 行):

| 函数 | 行数 | 拆分方案 | 状态 |
|---|---|---|---|
| `_loudnorm` | 66 | 拆 `_parse_loudnorm_json`(stderr→measured dict)+ `_loudnorm_pass1`(测量)+ `_loudnorm_pass2`(应用) | ⏳ 待拆 |
| `_mix_master_audio` | 80 | 拆 `_gen_silence_fallback`(静音生成)+ `_build_segment_filters`(segment filter 构建) | ⏳ 待拆 |
| `compose_director_job` | 287 | 拆 11 个 helper: `_maybe_idempotent_return`(幂等)/`_dedupe_completed_slots`(去重)/`_detect_timeline_gaps`(空隙)/`_build_slot_segments`(timeline)/`_collect_slot_sources`(Step1 校验)/`_repair_slot_output`(REPAIR)/`_run_build_pipeline`(Step2-4)/`_finalize_output`(Step5)/`_build_manifest`/`_finalize_cleanup`(Step6)/`_compose_failed`(异常收敛) | ⏳ 待拆 |

**其他需处理**:
- 函数体内延迟导入 `from ..services.slot_workflows import WORKFLOW_HANDLERS`(REPAIR 分支): 在 `app.services` 包上下文 `..` 解析到 `app`,`..services` = `app.services` — 实际正确, 但违反绝对导入约束 → 改 `from app.services.slot_workflows`。
- `from collections import Counter`(dedup SSE)函数体内导入 → 提顶层。

## 依赖与调用面

- **接入点**: `director_routes/compose.py:102`(后台线程延迟导入)、`scripts/verify_retention.py:26`。均只引 `compose_director_job`。
- **顶层 imports**: `json`/`logging`/`os`/`subprocess`/`datetime`/`Path`/`Any`/`Session`/`get_config`/`run_ffmpeg`/`DirectorJob`/`DirectorSlot`/`ffprobe_metadata`。全部有使用, 无死代码。
- **循环导入风险**: `slot_workflows` 包不 import composition_service → REPAIR 延迟导入可安全改绝对。`director_routes/compose.py` 延迟导入不变。
- **基础设施已封装**: `run_ffmpeg`(app.infrastructure.ffmpeg)、`ffprobe_metadata`(video_validator)。本文件不新建基础设施。

## 依赖方向

`services/composition_service` → `config` / `infrastructure.ffmpeg` / `models` / `services.video_validator` / `services.slot_workflows`(REPAIR, 延迟)。无反向依赖, 无循环。

## 重构方向

**方案: 拆为 `app/services/composition_service/` 包**(与旧模块同名 — 参照 slot_workflows 结论: 同名包优先于同名模块, 原 `.py` shim 是不可达死代码, 删除不留)。调用面 `from app.services.composition_service import compose_director_job` 自动解析到包, **零改动**。

| 新模块 | 内容 |
|---|---|
| `__init__.py` | re-export `compose_director_job` + `__all__` + 包布局 docstring |
| `common.py` | `_now`/`_job_root`/`_ensure_root`/`_cleanup_intermediates`/`_run_ffmpeg`/`_detect_timeline_gaps` |
| `ffmpeg_steps.py` | `_concat_demuxer_concat`/`_has_audio_stream`/`_loudnorm` + `_parse_loudnorm_json`/`_loudnorm_pass1`/`_loudnorm_pass2` |
| `audio.py` | `_mix_master_audio`/`_gen_silence_fallback`/`_build_segment_filters`/`_build_slot_segments`(+`_HOST_WF`)/`_resolve_master_audio`/`_audio_status_msg`/`_post_mix_audio_check` |
| `slots.py` | `_collect_slot_sources`(Step1 校验+缺失补齐)/`_repair_slot_output`(REPAIR) |
| `output.py` | `_finalize_output`(Step5 校验+manifest+写库)/`_build_manifest`/`_finalize_cleanup`(Step6) |
| `pipeline.py` | `compose_director_job`(编排)+ `_maybe_idempotent_return`/`_dedupe_completed_slots`/`_run_build_pipeline`/`_compose_failed` |

**约束达成预估**: 全模块 ≤250 行; 超限函数全部收窄 ≤40 物理行(compose_director_job 目标 ~37); 绝对导入; `__all__` 齐全; 无新增死代码。

## 行为契约 (重构后必须逐字保持)

- **返回 dict 4 种形状**(key 集合与 value 语义逐字):
  1. job 不存在 → `{"ok": False, "error": f"DirectorJob {job_id} not found"}`
  2. 幂等命中 → `{"ok": True, "output_path", "duration_sec": None, "manifest_path", "error": None}`
  3. 无 completed slot → `{"ok": False, "error": "no completed slots"}`
  4. 成功 → `{"ok": True, "output_path", "duration_sec", "manifest_path", "error": None}` / 失败 → `{"ok": False, "error", "output_path": old_output|None, "duration_sec": None}`(**失败无 manifest_path key**)
- **幂等守卫**: `status=="completed"` + `completed_at 非空` + 成片 `exists()` + 无 `slot.updated_at > completed_at` → 跳过重合成; 幂等返回 manifest_path = `composition_manifest.json` 路径。
- **去重质量层级** `_WF_TIER`: host/mixed=0, broll_pexels/broll_local/hf_chart/hf_title=1, black_placeholder=9, 未知=5; 同层级取 updated_at 最新。
- **REPAIR 补齐**: `WORKFLOW_HANDLERS.get`、hf_chart/hf_title 传 3 参否则 2 参、异常包装 `f"slot {idx} repair failed ({wf}): {exc}"` from exc、`slot.output_path = new_out` + `db.commit()`。错误消息逐字。
- **SSE 事件 type 与 msg 逐字**: `compose_step`(dedup/repair/validate/concat/audio/loudnorm)、`compose_start`、`compose_done`、`compose_error`、`compose_cleanup`; `去重结果: {dict(wf_counts)}`、`开始合成 {len(completed)} 个片段`、`补齐缺失片段 #{slot.slot_index} ({slot.workflow})…`、`校验 {len} 个片段…`、`拼接视频…`、`响度归一化…`、`校验输出…`、`混入 TTS 主音轨 (...)…`/`TTS 音频文件缺失 (...)…`/`无 TTS 音频，生成静音…`、`⚠ 混音后无音频流，请检查音频文件`、`合成完成: {:.1f}s`、`合成失败: {exc}`、`清理中间文件释放 {:.1f} MB`。
- **loudnorm 语义**: 无音频流→`os.replace` copy; 静音(input_i<-70)→skip copy; pass1 无 JSON→copy; 否则两遍 measured 应用。日志逐字。
- **失败路径**: `job.status="failed"`、`job.error_message=f"composition failed: {exc}"`、`job.completed_at=_now()`、`db.commit()`; 旧成片保留不覆盖(`old_output` 若存在)。
- **清理**: `_cleanup_intermediates` patterns 含 `silence_fallback.wav`(2026-08-07 素材生命周期策略 Step 1 A); **合成成功路径不触碰 slots/**(Step 7 已移除)。
- **manifest**: `schema_version="1.0"`/`status="completed"`/`slots`/`warnings`/`created_at` 等字段结构不变, `ensure_ascii=False, indent=2`。
- 所有 `logger` 消息逐字不变(带 `[compose]`/`[cleanup]`/`loudnorm` 前缀)。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。

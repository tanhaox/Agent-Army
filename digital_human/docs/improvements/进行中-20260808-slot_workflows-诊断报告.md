# 进行中-20260808-slot_workflows-诊断报告

**文件**: `app/services/slot_workflows.py`(845 行,非 920 — 实际行数比预估小)
**日期**: 2026-08-08
**阶段**: 第二批「核心服务层重构」第 2 个文件的第 1 步(诊断)

## 现状

单一文件包含 7 种视觉槽位 workflow 的实现 + 分发表。职责: 每个 workflow 类型一个顶层函数, 输入 `(db, slot)` 返回 mp4 输出路径。ffmpeg 底层已提取至 `app.infrastructure.ffmpeg`(第一批)。

**顶层结构** (17 个函数, 0 个类):

| 函数 | 行 | 职责 |
|---|---|---|
| `_pick_hf_template` | 10 | 按 video_format 选 HF 模板 |
| `slot_root` / `ensure_slot_dir` / `audio_slice_path` | 3/4/4 | 槽位目录与音频路径辅助 |
| `prepare_comfyui_storyboard` | 88 | 分镜图 QA(尺寸/格式/文件大小) |
| `execute_host_slot` | 106 | host 视频 → LTX23 → ComfyUI |
| `poll_comfyui_and_collect` | 64 | 轮询 ComfyUI + 取消/心跳/收件 |
| `_collect_used_pexels_ids` | 27 | 同片不重复素材 id 收集 |
| `execute_broll_pexels_slot` | 67 | Pexels 降维搜索 + trim |
| `execute_broll_local_slot` | 85 | 本地素材匹配 + 降级 |
| `_render_broll_local` | 11 | 本地素材渲染 helper |
| `_extract_hf_content` | 84 | 口播文本 → 标题卡内容 |
| `_normalize_chart_input` | 68 | render_config 归一化 |
| `execute_hf_visual_slot` | 51 | HF 图表/标题卡渲染 |
| `execute_mixed_host_broll_slot` | 23 | host 前景 + broll 背景合成 |
| `_pick_fallback_material` | 23 | 兜底素材选取 |
| `execute_black_placeholder_slot` | 19 | 兜底素材渲染 |
| `WORKFLOW_HANDLERS` | — | 分发表 |

## 问题 (违反硬性约束)

**8 个超限函数** (均 >40 行):

| 函数 | 行数 | 拆分方案 |
|---|---|---|
| `prepare_comfyui_storyboard` | 88 | 按 QA 三阶段拆: `_qa_convert_rgb` + `_qa_resize` + `_qa_letterbox` + `_qa_finalize` |
| `execute_host_slot` | 106 | 拆 `_load_host_storyboard`(图解析+回退)+ `_submit_comfyui`(HTTP 提交) |
| `poll_comfyui_and_collect` | 64 | 拆 `_send_interrupt` + `_emit_heartbeat` + `_find_comfy_output` |
| `execute_broll_pexels_slot` | 67 | 拆 `_resolve_pexels`(搜索+降级)+ 持久化段分离 |
| `execute_broll_local_slot` | 85 | 拆 `_match_local`(策略 1-3)+ `_build_local_keywords` |
| `_extract_hf_content` | 84 | 拆 `_pick_title` + `_extract_numbers` + `_score_metrics` |
| `_normalize_chart_input` | 68 | 拆 `_coerce_items` + `_chart_fallback` |
| `execute_hf_visual_slot` | 51 | 拆 `_merge_render_config` + `_ensure_metrics` |

## 依赖与调用面

- **外部引用仅 `WORKFLOW_HANDLERS`**:
  - `app/services/slot_executor.py:19` — `from app.services.slot_workflows import WORKFLOW_HANDLERS`(直接导入)
  - `app/services/composition_service.py:440` — 延迟导入(REPAIR 路径)
- 其余 18 个符号**无任何外部引用**(已全量 grep 验证)。
- `app/services/__init__.py` 为空 → 无 re-export 面。
- 延迟导入观察(函数体内 import): `prepare_comfyui_storyboard` 内的 `math`/`PIL`(可提升到模块顶层);`execute_host_slot` 内的 `build_ltx23_video_workflow`/`httpx`;`poll_comfyui_and_collect` 内的 `httpx`/`time`/`_is_cancelled`/`publish`;`execute_hf_visual_slot` 内的 `execute_visual_render_job`;`_pick_fallback_material` 内的 `random`。
- 无循环导入风险: 相关模块(`slot_executor`/`composition_service`/`director_events`/`visual_render_service`/`lit_video_builder`)均不 import slot_workflows 内容(除 WORKFLOW_HANDLERS)。

## 依赖方向

`slot_workflows` → `config` / `infrastructure` / `models` / `schemas` / `asset_matcher` / `pexels_service` / `lit_video_builder` / `slot_executor`(`_is_cancelled`, 函数级)/ `director_events` / `visual_render_service`(函数级)。无反向。

## 重构方向

**方案: 拆为 `app/services/slot_workflows/` 包**, 按 workflow 族分组 (对应 `_EXECUTION_PHASES` 的 C/P/H/L 四条线)。已实施, 最终 12 模块:

| 新模块 | 归属 | 内容 |
|---|---|---|
| `__init__.py` | 聚合 | `WORKFLOW_HANDLERS` 分发表 + `__all__` |
| `common.py` | — | `slot_root`/`ensure_slot_dir`/`audio_slice_path`/`_pick_hf_template`/HF 模板常量 |
| `host.py` | C 线 | `execute_host_slot` + `_resolve_host_role`/`_pick_storyboard_image`/`_prepare_host_inputs`/`_build_host_workflow` |
| `host_qa.py` | C 线 | `prepare_comfyui_storyboard` + `_qa_convert_rgb`/`_qa_resize`/`_qa_letterbox`/`_qa_finalize` |
| `host_comfy.py` | C 线 | `_submit_comfyui_workflow`/`_send_comfyui_interrupt`/`_emit_heartbeat`/`_find_comfy_output`/`_check_cancel`/`_maybe_emit_heartbeat`/`poll_comfyui_and_collect` |
| `broll.py` | L 线 | `execute_broll_local_slot` + 策略1/2-3/4 匹配 (`_try_exact_file`/`_build_local_keywords`/`_strategy_semantic_match`/`_render_broll_local`) |
| `broll_pexels.py` | P 线 | `_collect_used_pexels_ids`/`_resolve_pexels`/`_persist_chosen_pexels_id`/`execute_broll_pexels_slot` |
| `fallback.py` | L 线 | `_pick_fallback_material`/`execute_black_placeholder_slot` |
| `hf.py` | H 线 | `execute_hf_visual_slot` + `_merge_render_config`/`_ensure_metrics` |
| `hf_extract.py` | H 线 | `_extract_hf_content`/`_clean_fragment`/`_pick_title`/`_extract_numbers`/`_score_metrics` + `_EMOTION`/`_OPENING_PREFIX` |
| `hf_chart.py` | H 线 | `_normalize_chart_input`/`_coerce_items`/`_chart_fallback`/`_apply_chart_metadata` |
| `mixed.py` | C 线 | `execute_mixed_host_broll_slot` |

> **注意**: 原规划的弃用 shim `slot_workflows.py` 已删除 — 它与包同名, Python 导入规则下包永远优先, shim 是不可达死代码 (验证: `import app.services.slot_workflows` 解析到 `__init__.py`)。外部 `from app.services.slot_workflows import WORKFLOW_HANDLERS` 已直接指向包, 无需 shim。

## 行为契约 (重构后必须逐字保持)

- `WORKFLOW_HANDLERS` 的 7 个 key 与 handler 映射不变。
- `execute_hf_visual_slot` 签名 `(db, slot, workflow)` 不变 — slot_executor L71-72 特判传第三个参数。
- 所有错误消息逐字不变。
- `execute_broll_local_slot` 降级逻辑顺序不变 (策略1精确→策略2-3语义→策略4降级下载)。
- `_extract_hf_content` 的 title/subtitle/metrics/chart 结构不变。
- `poll_comfyui_and_collect` 取消/心跳/超时语义不变。

## 下一步

生成重构蓝图(本报告即蓝图初稿), 确认后执行拆分。

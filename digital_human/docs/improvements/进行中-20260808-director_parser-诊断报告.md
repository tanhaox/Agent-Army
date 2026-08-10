# 进行中-20260808-director_parser-诊断报告

**文件**: `app/services/director_parser.py`(420 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成（变更摘要见 [已完成-20260808-director_parser-架构重构.md](已完成-20260808-director_parser-架构重构.md)）

## 现状

Director LLM 输出的解析与 slot 规则执行:
1. `extract_json` 从 LLM 输出提取 JSON(兼容代码块包裹/混排解释文字)
2. 按新/旧 schema 分派 `parse_new_row`/`parse_legacy_row` → `DirectorSlotPlan`
3. 规则执行链: `enforce_host_rules`(首尾/中间强制 host) → `enforce_adjacency_rules`(相邻去重) → `cap_host_count`(host 上限降级)

纯后端服务, 无 HTTP/DB。依赖 `app.schemas`(DirectorPlan/DirectorSlotPlan) + `app.config.get_config`(延迟导入 `max_host_slots`)。

## 约束违规测量

| 违规 | 位置 | 行数 | 上限 |
|---|---|---|---|
| 文件超限 | 整个文件 | 420 | 250 |
| `parse_llm_plan` 超限 | 174-222 | 49 | 40 |
| `_best_fallback_workflow` 超限 | 232-276 | 45 | 40 |
| `enforce_host_rules` 超限 | 279-332 | 54 | 40 |
| `cap_host_count` 超限 | 335-385 | 51 | 40 |

类: 0 个(纯函数模块)→ 合规。

## 外部引用面

| 引用方 | 导入符号 |
|---|---|
| `app/services/director_service/_llm.py:16` | `parse_llm_plan` |
| `app/services/director_service/_fallback.py:13` | `_HOST_FAMILY` |
| `app/services/slot_executor.py:17` | `_best_fallback_workflow` |
| `app/routers/director_routes/retry.py:17` | `_best_fallback_workflow` |

→ 包化后 `__all__` 必须覆盖上述 3 符号 + 公共 API(`enforce_host_rules`/`cap_host_count`/`enforce_adjacency_rules`/`map_visual_type_to_workflow`/`extract_json`)。

## 拆分方案(5 模块包 `director_parser/`)

| 新文件 | 职责 | 迁入内容 |
|---|---|---|
| `__init__.py` | 公共 API + 私有外部依赖 | re-export 上述符号 + `__all__` |
| `_json.py` | JSON 提取 | `extract_json`(拆 `_strip_code_fence`) |
| `_rows.py` | 行解析器 | `_VALID_WORKFLOWS`、`map_visual_type_to_workflow`、`map_intensity`/`map_emotion`、`parse_legacy_row`、`parse_new_row`、`is_new_schema` |
| `_rules.py` | 规则执行 | `_HOST_FAMILY`、`_best_fallback_workflow`(数据化 `_FALLBACK_CHAINS`)、`enforce_host_rules`(拆 `_downgrade_hosts_c_disabled`/`_force_host_boundaries`)、`cap_host_count`(拆 `_force_host_ends`/`_pick_fallback_wf`/`_select_kept_hosts`/`_downgrade_excess_hosts`)、`enforce_adjacency_rules` |
| `_parse.py` | 编排入口 | `parse_llm_plan`(拆 `_extract_output`/`_build_slots`) |

依赖: `_rows` ← `_parse` → `_json`/`_rules`; `__init__` → 全部。`_rules` 延迟导入 `get_config`。无循环导入。

## 函数拆分

| 原函数 | 拆分 | 主函数剩余 |
|---|---|---|
| `parse_llm_plan` 49 | `_extract_output`(解析对象/数组+title)、`_build_slots`(schema 分派+排序+重编号) | ~10 |
| `_best_fallback_workflow` 45 | `_FALLBACK_CHAINS` 数据表 + `_WORKFLOW_PIPELINE`(workflow→管线 key) | ~12 |
| `enforce_host_rules` 54 | `_downgrade_hosts_c_disabled`(C线禁用分支)、`_force_host_boundaries`(首尾+中间强制) | ~15 |
| `cap_host_count` 51 | `_force_host_ends`(_HOST_FAMILY 版边界)、`_pick_fallback_wf`、`_select_kept_hosts`、`_downgrade_excess_hosts` | ~12 |

## 行为不变性(逐字保留, 不可丢)

- `extract_json`: 先剥 ``` 代码围栏, `json.loads` 失败后按 `{`/`[` 正则提取, 最后裸 `json.loads(text)`(最后一步可能抛 JSONDecodeError 原样上抛)
- 两个 ValueError 消息: `"Director response 'slots' is not a list"` / `"Director response is not a JSON object or array"`
- `parse_legacy_row`: `end <= start → end = start + 0.5`; static/dynamic params 分支; `visual_type` 默认 `"出镜"`
- `parse_new_row`: slot_index/start/end 解析失败返回 None; start/end 钳制 `[0, total_duration]`; `end = max(start+0.1, ...)`; camera 钳制 `[1,4]` 且非 host/mixed 置 1; params setdefault intensity/emotion
- `is_new_schema`: 只看 rows[0] 是否含 `workflow`/`start_sec`
- `parse_llm_plan`: slots sort 按 `(start_sec, slot_index)` 后重编号 `slot.slot_index = i`(从 0)
- `_best_fallback_workflow` 优先级链(数据化后严格等价):
  - host/mixed_host_broll → hf_title → broll_pexels → broll_local
  - hf_chart/hf_title → host → broll_pexels → broll_local
  - broll_pexels → host → hf_chart → broll_local
  - enabled_pipelines=None → 直接返回 prefer
- `enforce_host_rules`: `slots[-1].end_sec = min(..., total_duration)` 先执行; C线禁用分支降级日志 `"[director] slot %d downgraded %s→%s (C线禁用)"`; C线启用分支 fallback_reason 三处 `forced_host_opening`/`forced_host_ending`/`forced_host_middle`
- `cap_host_count`: `len(host_indices) <= max_host` 直接返回; 超限时 C线启用先强制首尾(_HOST_FAMILY 判定, 非 `== "host"`)→ 降级日志 `"host_cap_exceeded"`; `max_host` 默认 4
- `enforce_adjacency_rules`: 两轮扫描 `_same_family`/`_would_conflict`/`_swap_away`(host 相邻 + HF 相邻), 窗口 `range(i+2, min(i+6, len))`
- `get_config` 延迟导入(避免循环); `max_host_slots` 从 config.defaults 读
- 所有日志字符串 100% 一致

## 下一步

1. 创建 5 模块包(绝对导入 + `__all__`)
2. AST 硬约束检查(`scripts/_ast_check_director_parser.py`)
3. 行为契约断言(`scripts/_verify_director_parser.py`)— 新/旧 schema 分派、host 规则、cap、adjacency、fallback 链
4. 逐字 diff(`scripts/_diff_director_parser.py`)— 新旧输入输出一致
5. 原文件 send2trash(`director_parser.py` → 包同名, 原文件必须删)
6. 删除后重验 4 个引用方(_llm/_fallback/slot_executor/retry)
7. 编写 `已完成-20260808-director_parser-架构重构.md`, 更新本报告为 ✅

# 进行中-20260808-alignment_service-诊断报告

**文件**: `app/services/alignment_service.py`(460 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成（变更摘要见 [已完成-20260808-alignment_service-架构重构.md](已完成-20260808-alignment_service-架构重构.md)）

## 现状

Whisper 强制对齐服务 — 将脚本段落映射到真实音频时间轴:
1. faster-whisper 转录整段音频(关 word_timestamps 规避 CTranslate2 4.6.0 align() bug)
2. 按字符占比把脚本段贪心铺排到时间轴
3. 返回 word_segments + 每段 start/end/duration

纯后端服务, 无 HTTP 客户端。模块级副作用: `HF_HUB_OFFLINE=1` + tokenizer_fix 自动补丁(须先于 faster_whisper 加载生效)。模型进程级单例 `_MODEL_CACHE`(重复构造会损坏 CTranslate2 状态, 重载 ~70s)。

## 约束违规测量

| 违规 | 位置 | 行数 | 上限 |
|---|---|---|---|
| 文件超限 | 整个文件 | 460 | 250 |
| `_ensure_model` 超限 | 75-127 | 53 | 40 |
| `_transcribe_words` 超限 | 130-203 | 74 | 40 |
| `_match_segments` 超限 | 206-290 | 85 | 40 |
| `align_from_tts_durations` 超限 | 293-371 | 79 | 40 |
| `align_script_segments` 超限 | 374-460 | 87 | 40 |

类: 2 个纯数据 dataclass(`WordSegment`/`SegmentTiming`)→ 合规。

## 外部引用面

唯一消费方 `app/services/director_service/_alignment.py:83-85`:
```python
from app.services.alignment_service import (
    align_from_tts_durations,
    align_script_segments,
)
```
→ 包化后 `__all__` 必须覆盖这两函数 + 2 个 dataclass。

## 拆分方案(5 模块包 `alignment_service/`)

| 新文件 | 职责 | 迁入内容 |
|---|---|---|
| `__init__.py` | 公共 API + 模块副作用 | `HF_HUB_OFFLINE=1`、`apply_tokenizer_fix` 副作用(先于 faster_whisper)、re-export 4 符号 |
| `_models.py` | 模型加载 | `_WHISPER_LOCAL_CACHE`、`_MODEL_CACHE`、faster_whisper lazy import、`_ensure_model`(拆心跳)、`_start_heartbeat` |
| `_transcribe.py` | 转录 | `WordSegment`、`_normalize`、`_transcribe_words`(拆 `_collect_words`) |
| `_timings.py` | 时间轴铺排 | `SegmentTiming`、`_match_segments`(拆 `_empty_timings`/`_alloc_segment`/`_emit_match_progress`)、`align_from_tts_durations`(拆 `_tts_fast_timings`)、`_to_timing_dict` |
| `_align.py` | 对外主入口 | `align_script_segments`(拆 `_validate_audio`) |

依赖: `_models` ← `_transcribe` ← `_timings`(无), `_align` → 三者。`_align` 依赖 `_timings` 的 `_to_timing_dict`。无循环导入。

## 函数拆分

| 原函数 | 拆分 | 主函数剩余 |
|---|---|---|
| `_ensure_model` 53 | `_start_heartbeat`(18 行: 事件+线程+启动) | ~33 |
| `_transcribe_words` 74 | `_collect_words`(20 行: 迭代段+每 10 段进度) | ~35 |
| `_match_segments` 85 | `_empty_timings`(7)、`_alloc_segment`(14)、`_emit_match_progress`(4) | ~35 |
| `align_from_tts_durations` 79 | `_tts_fast_timings`(20)、`_to_timing_dict`(4, 复用) | ~22 |
| `align_script_segments` 87 | `_validate_audio`(8) | ~32 |

## 行为不变性(逐字保留, 不可丢)

- `word_timestamps=False` + **不传** `suppress_tokens`(空列表会崩 CTranslate2 4.6.0 generate) + `vad_parameters` 具体值(threshold 0.5 / min_speech 250ms / max_speech 30s)
- `_MODEL_CACHE` 键 `(size, dev)` 进程级单例; `compute_type="float32"`(CTranslate2 4.8.1 workaround)
- 心跳 `alignment_heartbeat`(5s 间隔, elapsed_sec 递增); `model_load_start`/`model_load_done`
- `_match_segments` 空输入 → 全零 timing; `total_chars==0` → 均分 fallback
- 进度回传节流: 转录每 10 段、匹配每 20 段(两处 msg 措辞各自保留)
- `PlanCancelled` 透传(不吞); 其他异常 `logger.exception` + `{ok:False, error:f"{type}: {exc}"}`
- 返回值 dict 键序与形状完全一致(ok/error/word_segments/segment_timings/total_duration_sec/model/device)
- `align_from_tts_durations` 快路径: `model="tts-durations"`, `device="n/a"`

## 下一步

1. 创建 5 模块包(绝对导入 + `__all__`)
2. AST 硬约束检查(`scripts/_ast_check_alignment.py`)
3. 行为契约断言(`scripts/_verify_alignment.py`)— 快路径、whisper 失败返回、PlanCancelled 透传、心跳 emit、进度节流
4. 逐字 diff(`scripts/_diff_alignment.py`)— 新旧输入输出一致
5. 原文件 send2trash(无同名包陷阱: `alignment_service.py` → 包同名, 原文件必须删)
6. 删除后重验 `director_service/_alignment.py` 引用方
7. 编写 `已完成-20260808-alignment_service-架构重构.md`, 更新本报告为 ✅

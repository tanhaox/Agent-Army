# 进行中-20260808-pexels_service-诊断报告

**文件**: `app/services/pexels_service.py`(552 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成 — 拆分为包 (9 模块 / 817 行), 见 [已完成-20260808-pexels_service-架构重构](已完成-20260808-pexels_service-架构重构.md)

## 现状

Pexels 素材 resolve 服务 (ID-003) — 视觉导演 import-only 调用范式: 本地缓存命中直接返回(零网络) → 缺失时调 Pexels API 下载 FHD mp4 → 落 DB → 返回本地路径; quota 超限/网络错/找不到 → 返回元数据并标记 `degraded=True`; 全部失败 → 空列表 + `degraded=True`。

**公共 API**: `pexels_service` 模块级单例 (`resolve` / `resolve_descending`), `PexelsService` 类, 异常 `PexelsAuthError` / `PexelsResolveError`, 数据结构 `ResolveItem`。

## AST 测量 (物理行)

| 成员 | 行数 | 类型 |
|---|---|---|
| `PexelsService` (类) | **466** | **OVER > 200** |
| `resolve` | **70** | OVER (编排上限 70, 压线达标) |
| `resolve_descending` | **46** | OVER > 40 |
| `_process_candidates` | **62** | OVER > 40 |
| `_register_video_asset` | **43** | OVER > 40 |
| `_query_local` | 31 | OK |
| `_download` | 29 | OK |
| `_upsert_asset` | 35 | OK |
| `_fill_with_degraded` | 34 | OK |
| `ResolveItem` (dataclass) | 27 | OK |
| 其余方法 | ≤20 | OK |

**类成员**: `PexelsService` 22 个方法 + `__init__`。状态: `_session` / `_api_key` / `_requests_session`(懒加载)。

## 问题 (违反硬性约束)

1. **类超限**: `PexelsService` 466 行 > 200。
2. **3 个超限函数** (>40, 非编排): `resolve_descending` / `_process_candidates` / `_register_video_asset`。
3. **`resolve` 70 行**: 编排函数压线(上限 70), 可选拆分但非必须。

## 依赖与调用面

- **代码引用面 (唯一)**: `app/services/slot_workflows/broll_pexels.py:17` — `from app.services.pexels_service import pexels_service`, 调用 `resolve_descending` / `resolve`。
- **测试面**: `tests/test_pexels_service.py` — 导入 `PexelsAuthError` / `PexelsService` / `pexels_service`; **直接使用私有接口**:
  - `svc._ensure_session()` (L77/92/95/150)
  - `svc._get_quota_used_today(db)` (L92/95/155)
  - `svc._cfg()` (L105)
  - `svc._api_key` / `svc._requests_session` 属性直接赋值 (L163/164)
  - `PexelsService()` 无参构造 (L59)
  - ⚠ **私有接口必须全部保留**(方法名/签名/行为逐字), 否则测试破坏。
- **schemas 面**: `app/schemas/assets.py` 的 `ResolveItem` 是独立 pydantic 模型, 与本模块 dataclass 无导入关系。
- **顶层 imports**: `json`/`logging`/`os`/`dataclass,field`/`date`/`Path`/`Any`/`urlparse`/`requests`/`func`/`Session`/`get_config`/`get_db`/`DownloadLog,MaterialAsset,VideoAsset`/`generate_asset_no,infer_tags`/`pexels_utils`(12 个符号)。全部有使用, 无死代码。
- **依赖服务**: `config` / `database` / `models` / `asset_tagging` / `pexels_utils` — 均不反向引用本模块, 无循环导入风险。

## 重构方向

**方案: 拆为 `app/services/pexels_service/` 同名包**(参照 video_tagging_service 结论: 同名包优先, 原 `.py` shim 不可达, send2trash 删除不留)。

`PexelsService` 类方法按**模块级 helper 函数**提取, 类方法保留同名 1-2 行转发 → 类行数从 466 压至 ≤200, 全部私有接口对测试零破坏。

| 新模块 | 内容 | 预估行数 |
|---|---|---|
| `__init__.py` | re-export `pexels_service`/`PexelsService`/`PexelsAuthError`/`PexelsResolveError`/`ResolveItem`/`PEXELS_API_BASE` + `__all__` | ~30 |
| `types.py` | `PEXELS_API_BASE` + 2 异常类 + `ResolveItem` dataclass | ~45 |
| `_session.py` | `session_factory`/`close_session`/`ensure_config`/`ensure_session`/`http_session`/`defaults`(配置/懒加载 helper, 接收 self) | ~55 |
| `_local.py` | `query_local`/`asset_to_item`(本地缓存) | ~45 |
| `_http.py` | `search_pexels`(API 搜索)/`download`(下载+校验) | ~55 |
| `_db.py` | `upsert_asset`/`increment_quota`/`register_video_asset`(+`build_video_asset`)/`get_quota_used_today`/`get_dislike_pexels_ids` | ~90 |
| `_degraded.py` | `merge_with_degraded`/`fill_with_degraded` | ~45 |
| `_candidates.py` | `process_candidates`(编排)+`handle_candidate`(单条: 过滤→选文件→下载→入库) | ~90 |
| `service.py` | `PexelsService` 主类: `__init__` + `resolve`/`resolve_descending` 编排 + 全部转发 | ~150 |

**约束达成预估**: 全模块 ≤250 行; 类 ≤200; 超限函数全部收窄(`resolve` 保持编排 ~65, `resolve_descending` 拆 `_descending_attempt` helper ≤40, `_process_candidates` 下放 `_candidates.py` 拆单条 helper, `_register_video_asset` 拆 `build_video_asset`); 绝对导入; `__all__` 齐全; 无新增死代码。

## 行为契约 (重构后必须逐字保持)

- **异常消息逐字**:
  - `PexelsAuthError(f"Missing Pexels API key in environment variable {key_env}")`
  - `PexelsAuthError(f"Pexels API returned 401. url={url}")`
  - `PexelsResolveError(f"network error: {exc}")`
  - `PexelsResolveError(f"Pexels API status {resp.status_code}: {resp.text[:200]}")`
  - `PexelsResolveError(f"invalid json: {exc}")`
  - `PexelsResolveError(f"download network error: {exc}")`
  - `PexelsResolveError(f"disk write error: {exc}")`
  - `PexelsResolveError(f"ffprobe validation failed: {dest}")`
- **logger 消息逐字**: `Pexels search failed: %s` / `resolve_descending attempt %r failed: %s` / `resolve_descending hit at %d keyword(s): %r` / `Download failed pexels_id=%s: %s` / `Pexels resolve unexpected error: %s`(logger.exception)。
- **resolve 流程** (逐字):
  - 外层 `try/except` 结构: `_ensure_config()` 内 try 捕获 `PexelsAuthError` 原样 raise; 主流程 `PexelsAuthError` 原样 raise; 其余异常 `logger.exception` + 返回 `[]`; `finally: _close_session()`。
  - `max_results`/`min_duration_sec`/`prefer_resolution` 缺省取 `cfg.pexels_default_max_results`/`cfg.pexels_min_duration_sec`/`cfg.pexels_preferred_resolution`; `prefer_resolution` 不在 `RESOLUTION_WIDTHS` → `"FHD"`。
  - dislike 黑名单合并: `exclude_pexels_ids | dislike_ids`。
  - 本地命中 ≥max → 直接返回 `local_items[:max_results]`; `needed = max_results - len(local_items)`; `remaining_quota = max(0, quota - used_today)`。
  - 搜索 `per_page=max(needed*3, 10)`; 搜索失败 → `_merge_with_degraded(local_items, needed, reason="search_failed")`。
  - 下载不足 → `_fill_with_degraded(..., reason="quota_exceeded_or_unreachable")`; `db.commit()`; 返回 `result[:max_results]`。
- **resolve_descending**: `clean[:6]`; 逆序 `range(len(clean), 0, -1)`; 主关键词 `clean[0]` 永远保留; 命中非空即停; `(items, used_query)` 返回; 全部失败 `([], None)`; `PexelsAuthError` 原样 raise。
- **`_search_pexels`**: URL `{PEXELS_API_BASE}/videos/search`; `per_page=min(per_page, 80)`; orientation 仅 portrait/landscape 下发(square 不下发, 注释逐字); `timeout=(10, 30)`; 401 → AuthError; 非 200 → ResolveError(status 消息); JSON 失败 → ResolveError; 返回 `data.get("videos", [])`。
- **`_process_candidates`**: `remaining_quota <= 0 or needed <= 0` 早退; `widths_sorted = sorted(RESOLUTION_WIDTHS.items(), key=lambda x: abs(x[1] - prefer_width))`; 过滤链逐字 (duration < min / !orientation_ok / 无 pexels_id / 在 exclude); 已存在且本地存在 → 复用不下载; quota 不足 → continue; `pick_video_file` None → continue; 下载失败 → warning + continue; 下载后 `file_size = Path(local_path).stat().st_size` → `_increment_quota` → `remaining_quota -= 1` → `_upsert_asset` → `_register_video_asset`。
- **`_download`**: `root.mkdir(parents=True, exist_ok=True)`; 扩展名白名单 `{".mp4",".mov",".webm"}` 兜底 `.mp4`; 目标 `pexels_{pexels_id}{ext}`; `timeout=(10, 300)`; `chunk_size=8192`; 网络/磁盘错 → 删残留文件 + raise; `validate_video(dest)` 失败 → `dest.unlink()` + raise; 返回 `str(dest.resolve())`。
- **`_upsert_asset`**: photographer/photographer_url/pexels_url 缺省逐字(`"Unknown Photographer"`/`"https://www.pexels.com"`/`f"https://www.pexels.com/video/{video.get(API_ID)}"`); width/height 取 chosen 优先; 新建 `db.add+flush` / 已存在更新字段, 字段列表逐字。
- **`_register_video_asset`**: 无 pexels_id 早退; 已存在 `VideoAsset.pexels_id` 去重早退; `infer_tags(raw_query or tags_str, width, height)`; `generate_asset_no(db)`; VideoAsset 字段逐字(含 `preference="neutral"`, `tags=[t for t in tags_str.split(",") if t] if tags_str else []`, `raw_query=(raw_query or tags_str)[:512]`)。
- **quota/dislike**: `DownloadLog(date=date.today(), pexels_id=pexels_id, bytes=size_bytes)`; `count(DownloadLog.id)` + `DownloadLog.date == date.today()`; dislike 查 `preference=="dislike"` 且 `pexels_id.isnot(None)`。
- **降级补齐**: `_merge_with_degraded` 把 local 全部置 `degraded=True` + reason; `_fill_with_degraded` 去重 (existing_pexels/seen_urls) + 过滤 (exclude/duration) + `pick_video_file(..., [(prefer_resolution, RESOLUTION_WIDTHS[prefer_resolution])])` + 缺省字段逐字 + reason 固定 `"quota_exceeded_or_unreachable"`。
- **单例**: 模块级 `pexels_service = PexelsService()`。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。

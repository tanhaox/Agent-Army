# 进行中-20260808-director_prompt-诊断报告

**文件**: `app/services/director_prompt.py`(783 行,无类,纯函数模块) → **已重构为 `director_prompt/` 包**
**日期**: 2026-08-08
**阶段**: ✅ 已完成 — 见 [已完成-20260808-director_prompt-架构重构.md](已完成-20260808-director_prompt-架构重构.md)

## 现状

Director LLM 提示词构建服务 (ID-034 / ID-003 相关)。单一模块内聚 **3 大职责**:

1. **提示词装配** — `load_director_prompt` / `build_director_prompt` / `_format_frame_spec` / `_build_pipeline_constraint_block` / `_format_vocabulary_constraint_block`。
2. **无出镜模式裁剪** — `_strip_host_mode`(12 步整节正则替换,含 100 行静态示例 `_NO_HOST_DEMO`)。
3. **词表包 (Vocabulary Pack)** — `build_vocabulary_pack` / `rebuild_vocabulary_pack` / `load_vocabulary_pack` + 清洗词表常量 (ID-034)。
4. **素材库目录** — `build_real_material_catalog` / `mock_material_catalog`。

**公共 API**: `build_director_prompt` / `build_real_material_catalog` / `rebuild_vocabulary_pack` / `build_vocabulary_pack` / `load_vocabulary_pack` / `mock_material_catalog` / `load_director_prompt`。

## AST 测量 (物理行)

| 成员 | 行数 | 类型 |
|---|---|---|
| `_strip_host_mode` | **136** | OVER > 40 (12 步正则替换 + 100 行静态示例) |
| `build_vocabulary_pack` | **131** | OVER > 40 (聚合 + 双桶清洗 + 组装) |
| `build_real_material_catalog` | **73** | OVER > 40 (查询 + 分组 + top-N 裁剪) |
| `build_director_prompt` | **69** | OVER (编排上限 70, 压线达标) |
| `_build_pipeline_constraint_block` | **47** | OVER > 40 |
| `mock_material_catalog` | 32 | OK |
| `_format_frame_spec` | 21 | OK |
| `_format_vocabulary_constraint_block` | 15 | OK |
| `rebuild_vocabulary_pack` | 15 | OK |
| `load_vocabulary_pack` | 10 | OK |
| `load_director_prompt` | 8 | OK |
| `_utc_now_iso` | 4 | OK |
| `_looks_chinese` | 6 | OK |

无类、无超限类。**5 个超限函数**,其中 `build_director_prompt` 69 行压线编排上限(不拆,参照 `resolve` 先例)。

## 问题 (违反硬性约束)

1. **文件 783 行 > 250** — 需拆包。
2. **`_strip_host_mode` 136 行**: 职责单一(12 步顺序替换)但体量过大,内含 100 行静态 `_NO_HOST_DEMO` 示例 + 多条长正则。
3. **`build_vocabulary_pack` 131 行**: 聚合资产 → 双桶清洗(中文视觉词优先/英文补位)→ 组装 pack,三阶段塞一个函数。
4. **`build_real_material_catalog` 73 行**: 查询 → 按主场景分组 → top-8 裁剪排序,三阶段塞一个函数。
5. **`_build_pipeline_constraint_block` 47 行**: 禁用管线列表构建 + 替代方案指引(嵌套条件)一函数。
6. **死代码**: 顶层 `import re` 与 `_strip_host_mode` 内 `import re` 重复 — 模块内除该函数外无 `re` 使用,顶层导入冗余。

## 依赖与调用面

- **代码引用面 (4 处, 全部走公共 API)**:
  - `app/services/director_service.py:21` — `from app.services.director_prompt import build_director_prompt`;L311 全关键字调用 (script_text/segment_timings/material_catalog/video_format/script_title/enabled_pipelines)。
  - `app/routers/director_routes/planning.py:67` — lazy `from app.services.director_prompt import build_real_material_catalog`;L78 位置调用 `(db)`。
  - `scripts/rebuild_vocabulary.py:30` — `from app.services.director_prompt import rebuild_vocabulary_pack`;L48 位置调用 `(session)`。
  - `app/services/video_tagging_service/store.py:52` — lazy `from app.services.director_prompt import rebuild_vocabulary_pack`;L55 位置调用 `(session)`。
- **测试面**: `tests/` 无 `director_prompt` 引用 — 无直接测试,靠调用面 + 行为契约保障。
- **内部私有引用**: `_strip_host_mode` / `_format_vocabulary_constraint_block` / `_format_frame_spec` / `_build_pipeline_constraint_block` 仅模块内 `build_director_prompt` 调用;`_looks_chinese` / `_utc_now_iso` 仅 `build_vocabulary_pack` 调用;`mock_material_catalog` 被 `build_real_material_catalog` 与 `build_director_prompt` 内部 fallback 调用。均无需对外暴露,但**模块间需传递**。
- **顶层 imports**: `json`/`logging`/`re`/`Path`/`Any`/`Session`/`PROJECT_ROOT`/`VideoAsset`/`get_video_format_spec` + `get_config`(函数内 lazy)。除顶层 `re` 冗余外全部有使用。
- **依赖服务**: `config` / `models` / `schemas` — 均不反向引用本模块,无循环导入风险。

## 重构方向

**方案: 拆为 `app/services/director_prompt/` 同名包**(无类模块 → 按职责横向分 5 模块,不套类;参照 pexels_service 包化模式: 同名包优先,原 `.py` send2trash 删除不留)。

| 新模块 | 内容 | 预估行数 |
|---|---|---|
| `__init__.py` | re-export 7 个公共函数 + `__all__` | ~15 |
| `_constants.py` | 词表包路径 / 硬软维度枚举 / 词量上下限 / 取值约束 / `_CLEANUP_*` 清洗词表 / `_CLEANUP_WORDS` 合并 / `_NO_HOST_DEMO` 静态示例 | ~100 |
| `_strip_host.py` | `_strip_host_mode` 编排 + 3 个分步 helper (管线表→规则块→示例/自检/兜底) | ~120 |
| `_prompt.py` | `load_director_prompt` / `build_director_prompt` (编排) / `_format_frame_spec` / `_build_pipeline_constraint_block`(拆替代指引 helper) / `_format_vocabulary_constraint_block` | ~120 |
| `_vocabulary.py` | `build_vocabulary_pack`(聚合/清洗/组装三 helper)+ `rebuild_vocabulary_pack` / `load_vocabulary_pack` / `_utc_now_iso` / `_looks_chinese` | ~120 |
| `_catalog.py` | `build_real_material_catalog`(分组/裁剪 helper)+ `mock_material_catalog` | ~120 |

**约束达成预估**: 全模块 ≤250 行;无类;超限函数全部收窄(`build_director_prompt` 保持编排压线;`_strip_host_mode` 拆 3 helper 后 ≤40;`build_vocabulary_pack` 拆聚合/清洗 helper;`build_real_material_catalog` 拆分组 helper;`_build_pipeline_constraint_block` 拆替代指引 helper);清理冗余顶层 `import re`;绝对导入;`__all__` 齐全;无新增死代码。

## 行为契约 (重构后必须逐字保持)

- **异常/边界逐字**: `build_vocabulary_pack` 无素材 → 返回空 pack (`dimensions:{}`/`stats:{}`);DB 失败 → `logger.exception` + 空 pack;`build_real_material_catalog` DB 失败/空库 → `mock_material_catalog()`;`load_vocabulary_pack` 缺失/解析失败 → `None`。
- **logger 消息逐字**: `build_vocabulary_pack: no VideoAsset found, returning empty pack` / `build_vocabulary_pack: %d assets, %s` / `rebuild_vocabulary_pack: wrote %s (%d words)` / `load_vocabulary_pack: %s missing` / `build_real_material_catalog: no VideoAsset found, using mock` / `build_real_material_catalog: %d scenes, %d assets` / `catalog_mode=vocabulary but pack missing (%s), falling back to full catalog`。
- **`build_director_prompt` 流程逐字**: `enabled_pipelines` 非 None 且不含 `"c"` → `_strip_host_mode`;标题/脚本占位符 replace;`_format_frame_spec` 追加;`catalog_mode` 判定 (get_config 异常 → `"vocabulary"`);vocabulary 模式 pack 缺失 → fallback 全量;JSON `ensure_ascii=False, indent=2`;`_format_vocabulary_constraint_block` 追加;timing JSON 追加;管线约束块追加。
- **`_format_frame_spec` 逐字**: `fmt = video_format or "portrait"`;三画幅分支文案逐字(portrait/landscape/else square);结尾 `当前画幅是 **{fmt}**...`。
- **`_build_pipeline_constraint_block` 逐字**: 管线映射 `{"c":("C线 ComfyUI",[host,mixed_host_broll]), "p":("P线 Pexels",[broll_pexels]), "h":("H线 HuggingFace",[hf_chart,hf_title])}`;disabled 行格式 `- {label} → 禁止工作流: {', '.join(wfs)}`;替代方案全部条件分支逐字(host/mixed 双禁→h/p/本地、broll_pexels 禁→c/h/本地、hf 双禁→c/本地)。
- **`_strip_host_mode` 12 步逐字**: 1-2 行删除 + params 字段删除正则;规则1/2/2.5/3/4.3/4.4 整节替换(替换表内容逐字);输出示例整块换 `_NO_HOST_DEMO`;7 条自检行删除;3 条注意事项 replace;核心能力描述 replace;兜底行删除 + `\n{3,}` 折叠 + `老陈出镜→画面呈现`。**替换表字符串逐字**(`_rule1`/`_rule2`/`_rule3` 内容不动)。
- **`build_vocabulary_pack` 数据流逐字**: pack 头部 (`type`/`version`/`built_at`/`dimensions`/`stats`/`_note` 逐字);查询 `file_path.isnot(None)` + `ai_tagged_at.desc().nullslast()`;scenes/shots 去重顺序;ai_tags_extra 四维度;tags/description_zh 双桶;中文视觉词优先 + 英文补位;`MAX_WORDS_PER_DIM` 截断;stats 三键。
- **词表清洗逐字**: 前缀 `_CLEANUP_PREFIXES`;`_CLEANUP_WORDS = _CLEANUP_RAW | _CLEANUP_EXTRA | _CLEANUP_EN_STOP | _CLEANUP_WEAK_CN`;`_looks_chinese` CJK 区间 `"一" <= c <= "鿿"` + ≥60%;description_zh 切分正则 `[,，。；;、！？!?：:\s]+` + 引号 strip + 2-8 字。
- **`rebuild_vocabulary_pack`**: `with_suffix(".json.tmp")` 写盘 + `tmp.replace` 原子替换。
- **`build_real_material_catalog`**: 排序 `ai_tagged_at.desc().nullslast(), used_count.asc()`;`primary_scene = (asset.scenes or ["未分类"])[0]`;条目 12 字段逐字;`_MAX_ITEMS_PER_SCENE = 8`;排序 `used_count` 升序 + ai 标签优先;`catalog["数据图表"]`/`catalog["标题卡"]` 动态渲染入口;日志 `len(catalog)-2`。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。

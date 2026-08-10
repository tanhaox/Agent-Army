"""逐字 diff — director_parser 新旧实现输出一致.

加载原单文件模块 (load_old, sys.modules 遮蔽) → 对相同输入跑新旧实现 →
flat() 转纯 dict 比较 dataclass 列表 → 报告差异.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields, is_dataclass
from types import ModuleType
from typing import Any

sys.path.insert(0, "F:/AI-Agent-Local/digital_human")

from app.config import load_config, set_config  # noqa: E402
set_config(load_config())  # 新旧实现 enforce_host_rules 内 get_config() 需要

OLD_PATH = "F:/AI-Agent-Local/digital_human/app/services/director_parser.py"
NEW = "app.services.director_parser"


def load_old() -> ModuleType:
    spec = importlib.util.spec_from_file_location("old_director_parser", OLD_PATH)
    assert spec and spec.loader, "无法加载原文件"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["old_director_parser"] = mod
    spec.loader.exec_module(mod)
    return mod


def del_sys_modules() -> None:
    """注销新包, 避免 sys.modules 遮蔽下轮加载."""
    for k in list(sys.modules):
        if k == NEW or k.startswith(NEW + "."):
            del sys.modules[k]


def flat(v: Any) -> Any:
    """dataclass → 纯 dict 递归 (跨模块 dataclass == 恒 False 的解法)."""
    if is_dataclass(v) and not isinstance(v, type):
        return {f.name: flat(getattr(v, f.name)) for f in fields(v)}
    if isinstance(v, dict):
        return {k: flat(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [flat(x) for x in v]
    return v


def _mk_new_rows(n: int) -> list[dict[str, Any]]:
    return [{
        "slot_index": i,
        "workflow": wf,
        "start_sec": i * 2.0,
        "end_sec": i * 2.0 + 1.5,
        "text_context": f"文本{i}",
        "segment_id": f"seg{i}",
        "params": {"intensity": "medium", "emotion": "rising", "k": i},
    } for i, wf in enumerate(
        ["host", "broll_pexels", "host", "hf_chart", "host", "broll_local", "host", "hf_title", "host"]
    )]


def _mk_legacy_rows(n: int) -> list[dict[str, Any]]:
    return [{
        "line_id": i + 1,
        "visual_type": vt,
        "intensity": "high" if i % 2 == 0 else "medium",
        "emotion": "climax" if i % 3 == 0 else "rising",
        "effect": "淡入",
        "sound": "bgm",
        "text": f"脚本{i}",
        "material_source": ms,
    } for i, (vt, ms) in enumerate([
        ("出镜", {"type": "static", "file": "/f1.png", "fallback_file": "/g1.png", "category": "人物"}),
        ("素材", {"type": "dynamic", "category": "标题字幕", "render_config": {"bg": 1}}),
        ("混合", {"type": "static", "file": "/f3.png"}),
        ("画面", {"type": "dynamic", "render_config": {}}),
    ])]


def run_old(old: ModuleType, fn: str, *args, **kwargs) -> Any:
    return flat(getattr(old, fn)(*args, **kwargs))


def run_new(fn: str, *args, **kwargs) -> Any:
    mod = importlib.import_module(NEW)
    return flat(getattr(mod, fn)(*args, **kwargs))


def diff(fn: str, *args, **kwargs) -> tuple[bool, str | None]:
    old = load_old()
    try:
        o = run_old(old, fn, *args, **kwargs)
    finally:
        del_sys_modules()
    n = run_new(fn, *args, **kwargs)
    if o == n:
        return True, None
    return False, f"\n  old={json.dumps(o, ensure_ascii=False, default=str)[:400]}\n  new={json.dumps(n, ensure_ascii=False, default=str)[:400]}"


def main() -> int:
    new_rows = _mk_new_rows(9)
    legacy_rows = _mk_legacy_rows(4)
    timings = {i + 1: {"start": i * 2.0, "end": i * 2.0 + 1.5, "segment_id": f"seg{i}"} for i in range(4)}

    cases: list[tuple[str, list, dict]] = [
        # (函数, 位置参数, 关键字参数)
        ("extract_json", ['{"video_title": "t", "slots": [{"a": 1}]}'], {}),
        ("extract_json", ["```json\n{\"a\": [1,2,3]}\n```"], {}),
        ("extract_json", ['说明文字 {"b": {"c": 1}} 结尾'], {}),
        ("extract_json", ['[{"a":1}, {"b":2}]'], {}),
        ("parse_legacy_row", [legacy_rows[0], timings, 100.0], {}),
        ("parse_legacy_row", [legacy_rows[1], timings, 100.0], {}),
        ("parse_legacy_row", [legacy_rows[3], timings, 100.0], {}),
        ("parse_legacy_row", [{"line_id": 999}, timings, 100.0], {}),
        ("parse_new_row", [new_rows[0], 100.0], {}),
        ("parse_new_row", [dict(new_rows[1], camera=9), 100.0], {}),
        ("parse_new_row", [dict(new_rows[1], camera="abc"), 100.0], {}),
        ("parse_new_row", [{"start_sec": "abc"}, 100.0], {}),
        ("parse_new_row", [dict(new_rows[0], start_sec=200.0), 100.0], {}),
        ("is_new_schema", [new_rows], {}),
        ("is_new_schema", [legacy_rows], {}),
        ("is_new_schema", [[]], {}),
        ("_best_fallback_workflow", [{"c", "h", "p"}], {"prefer": "host"}),
        ("_best_fallback_workflow", [{"h"}], {"prefer": "host"}),
        ("_best_fallback_workflow", [{"p"}], {"prefer": "host"}),
        ("_best_fallback_workflow", [set()], {"prefer": "host"}),
        ("_best_fallback_workflow", [set()], {"prefer": "broll_pexels"}),
        ("_best_fallback_workflow", [{"c"}], {"prefer": "hf_chart"}),
        ("_best_fallback_workflow", [None], {"prefer": "host"}),
        ("_best_fallback_workflow", [set()], {"prefer": "broll_local"}),
        ("enforce_host_rules", [[], 10.0], {}),  # 空输入
        ("cap_host_count", [[], 4], {}),  # 空输入
        ("enforce_adjacency_rules", [[]], {}),  # 空输入
    ]
    # 构造 dataclass 输入 (新旧实现各自构造, 见 run 里转 flat)
    # -- enforce_host_rules / cap / adjacency 用 dict 无法直接喂给 DirectorSlotPlan,
    #    这里改用一个统一 builder: 传入 workflow 列表, 在 load 侧构造.

    results: list[tuple[str, bool, str | None]] = []
    for fn, args, kwargs in cases:
        ok, msg = diff(fn, *args, **kwargs)
        results.append((fn, ok, msg))

    # dataclass 输入用例: 通过 helper 在两侧各构建 slots
    def _slots_of(wfs: list[str]) -> list:
        from app.schemas.director import DirectorSlotPlan
        return [DirectorSlotPlan(
            slot_index=i, start_sec=i * 2.0, end_sec=i * 2.0 + 1.0,
            text_context="s", segment_id=None,
            visual_type=wf,  # type: ignore[arg-type]
            workflow=wf,  # type: ignore[arg-type]
            params={"k": "v"},
        ) for i, wf in enumerate(wfs)]

    slot_cases = [
        ("enforce_host_rules", ["host", "broll_pexels", "host"], {"total_duration": 10.0, "enabled_pipelines": {"c", "p"}}),
        ("enforce_host_rules", ["broll_local", "broll_local", "broll_local"], {"total_duration": 10.0, "enabled_pipelines": {"c"}}),
        ("enforce_host_rules", ["host", "host", "host"], {"total_duration": 10.0, "enabled_pipelines": {"p", "h"}}),
        ("enforce_host_rules", ["host", "broll_pexels", "host"], {"total_duration": 10.0, "enabled_pipelines": {"h"}}),
        ("enforce_host_rules", ["host", "host", "host", "host", "host"], {"total_duration": 10.0, "enabled_pipelines": {"c", "p", "h"}}),
        ("cap_host_count", ["host"] * 8, {"max_host": 4, "enabled_pipelines": {"c", "p", "h"}}),
        ("cap_host_count", ["host"] * 8, {"max_host": 4, "enabled_pipelines": {"p"}}),
        ("cap_host_count", ["host"] * 3, {"max_host": 4, "enabled_pipelines": None}),
        ("enforce_adjacency_rules", ["host", "host", "broll_local", "host", "host"], {}),
        ("enforce_adjacency_rules", ["hf_chart", "hf_title", "broll_local", "hf_chart"], {}),
    ]

    def run_slot(m: ModuleType, fn: str, wfs: list[str], kw: dict) -> Any:
        slots = _slots_of(wfs)
        return flat(getattr(m, fn)(slots, **kw))

    for fn, wfs, kw in slot_cases:
        old = load_old()
        try:
            o = run_slot(old, fn, wfs, kw)
        finally:
            del_sys_modules()
        n = run_slot(importlib.import_module(NEW), fn, wfs, kw)
        ok = o == n
        msg = None if ok else f"\n  old={json.dumps(o, ensure_ascii=False, default=str)[:400]}\n  new={json.dumps(n, ensure_ascii=False, default=str)[:400]}"
        results.append((f"{fn}({wfs})", ok, msg))

    fails = [r for r in results if not r[1]]
    print(f"逐字 diff: {len(results) - len(fails)}/{len(results)} 一致")
    for name, ok, msg in results:
        if not ok:
            print(f"  ❌ {name}{msg}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

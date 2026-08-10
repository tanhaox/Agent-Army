"""行为契约断言 — director_parser 包化后.

覆盖: 新/旧 schema 分派、extract_json 三种形态、host 规则(C线启用/禁用)、
cap_host_count 超限采样、adjacency 去重、fallback 链、ValueError 消息、sort/重编号.
"""
from __future__ import annotations

import sys
from types import ModuleType
from typing import Callable

sys.path.insert(0, "F:/AI-Agent-Local/digital_human")

from app.config import load_config, set_config  # noqa: E402
set_config(load_config())  # enforce_host_rules 内 get_config() 需要

import app.services.director_parser as dp  # noqa: E402

PASS = 0
FAIL = 0
LOG: list[str] = []


def check(name: str, cond: bool) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        LOG.append(name)


def call(m: ModuleType, fn: str, *args, **kwargs):
    return getattr(m, fn)(*args, **kwargs)


# ---- fixture helpers ----
def _plan(title, slots):
    return {"title": title, "slots": slots}


# =====================================================================
# 1. extract_json 三种形态
# =====================================================================
check("extract_json 纯对象", call(dp, "extract_json", '{"video_title": "t", "slots": []}') == {"video_title": "t", "slots": []})
check("extract_json 代码围栏", call(dp, "extract_json", '```json\n{"a": 1}\n```') == {"a": 1})
check("extract_json 混排文字", call(dp, "extract_json", '结果是 {"a": 1} 结束') == {"a": 1})
check("extract_json 数组", call(dp, "extract_json", '[{"a": 1}, {"b": 2}]') == [{"a": 1}, {"b": 2}])

# =====================================================================
# 2. mapping helpers
# =====================================================================
check("map_visual_type 直通", call(dp, "map_visual_type_to_workflow", "host", {}) == "host")
check("map_visual_type 出镜", call(dp, "map_visual_type_to_workflow", "出镜", {}) == "host")
check("map_visual_type 混合", call(dp, "map_visual_type_to_workflow", "混合", {}) == "mixed_host_broll")
check("map_visual_type dynamic 标题", call(dp, "map_visual_type_to_workflow", "xx", {"type": "dynamic", "category": "标题字幕"}) == "hf_title")
check("map_visual_type dynamic chart", call(dp, "map_visual_type_to_workflow", "xx", {"type": "dynamic", "category": "数据"}) == "hf_chart")
check("map_visual_type file", call(dp, "map_visual_type_to_workflow", "xx", {"file": "/a.mp4"}) == "broll_local")
check("map_visual_type default", call(dp, "map_visual_type_to_workflow", "xx", {}) == "broll_pexels")
check("map_intensity 越界默认", call(dp, "map_intensity", "extreme") == "medium")
check("map_emotion 越界默认", call(dp, "map_emotion", "flat") == "rising")

# =====================================================================
# 3. legacy row 解析
# =====================================================================
timings = {1: {"start": 1.0, "end": 5.0, "segment_id": "seg1"}}
legacy = {
    "line_id": 1,
    "visual_type": "出镜",
    "intensity": "high",
    "emotion": "climax",
    "effect": "淡入",
    "sound": "bgm",
    "text": "大家好",
    "material_source": {"type": "static", "file": "/f.png", "fallback_file": "/g.png", "category": "人物"},
}
s = call(dp, "parse_legacy_row", legacy, timings, 100.0)
check("legacy row 非None", s is not None)
check("legacy slot_index", s.slot_index == 0)
check("legacy start", s.start_sec == 1.0)
check("legacy end", s.end_sec == 5.0)
check("legacy workflow", s.workflow == "host")
check("legacy params file", s.params["file"] == "/f.png")
check("legacy params fallback", s.params["fallback_file"] == "/g.png")
check("legacy params category", s.params["category"] == "人物")
check("legacy segment_id", s.segment_id == "seg1")

# legacy: end<=start 修正
legacy_bad = dict(legacy, material_source={"type": "dynamic", "render_config": {"bg": 1}})
legacy_bad["line_id"] = 2
timings[2] = {"start": 7.0, "end": 7.0, "segment_id": "seg2"}
s2 = call(dp, "parse_legacy_row", legacy_bad, timings, 100.0)
check("legacy end<=start 修正", s2 is not None and s2.end_sec == 7.5)
check("legacy dynamic render_config", s2.params["render_config"] == {"bg": 1})

# legacy: 无 timing → None
check("legacy 无timing None", call(dp, "parse_legacy_row", {"line_id": 999}, {}, 100.0) is None)

# =====================================================================
# 4. new row 解析
# =====================================================================
new = {
    "slot_index": 0,
    "workflow": "host",
    "start_sec": 1.0,
    "end_sec": 5.0,
    "text_context": "开场",
    "segment_id": "seg1",
    "camera": 3,
    "params": {"intensity": "low", "emotion": "opening", "extra": 1},
}
s3 = call(dp, "parse_new_row", new, 100.0)
check("new row 非None", s3 is not None)
check("new workflow", s3.workflow == "host")
check("new camera", s3.camera_angle == 3)
check("new params 保留", s3.params["extra"] == 1)
check("new params 不覆盖", s3.params["intensity"] == "low")

# new: camera 越界钳制
n2 = dict(new, camera=9)
check("new camera 钳制上", call(dp, "parse_new_row", n2, 100.0).camera_angle == 4)
# new: 非 host 相机强制 1
n3 = dict(new, workflow="broll_pexels", camera=2)
check("new 非host camera=1", call(dp, "parse_new_row", n3, 100.0).camera_angle == 1)
# new: start>total → 钳制
n4 = dict(new, start_sec=200.0)
s4 = call(dp, "parse_new_row", n4, 100.0)
check("new start 钳制", s4.start_sec == 100.0 and s4.end_sec == 100.1)  # end=max(start+0.1, min(...))
# new: 非法数字 → None
check("new 非法数字 None", call(dp, "parse_new_row", {"start_sec": "abc"}, 100.0) is None)

# =====================================================================
# 5. is_new_schema
# =====================================================================
check("is_new_schema new", call(dp, "is_new_schema", [{"workflow": "host"}]) is True)
check("is_new_schema legacy", call(dp, "is_new_schema", [{"line_id": 1}]) is False)
check("is_new_schema empty", call(dp, "is_new_schema", []) is False)

# =====================================================================
# 6. parse_llm_plan: 新格式全链路
# =====================================================================
plan = call(dp, "parse_llm_plan",
            '{"video_title": "测试", "slots": ['
            '{"slot_index": 1, "workflow": "broll_local", "start_sec": 3, "end_sec": 5, "text_context": "中"},'
            '{"slot_index": 0, "workflow": "host", "start_sec": 0, "end_sec": 3, "text_context": "首"},'
            '{"slot_index": 2, "workflow": "broll_pexels", "start_sec": 5, "end_sec": 8, "text_context": "尾"}]}',
            [], 100.0, enabled_pipelines=None)
check("plan title", plan.title == "测试")
check("plan slots 数量", len(plan.slots) == 3)
check("plan 排序重编号", [s.slot_index for s in plan.slots] == [0, 1, 2])
check("plan 首为host", plan.slots[0].workflow == "host")
check("plan 尾为host", plan.slots[-1].workflow == "host")
check("plan 首为原生host无reason", "fallback_reason" not in plan.slots[0].params)
check("plan 尾fallback_reason", plan.slots[-1].params.get("fallback_reason") == "forced_host_ending")

# =====================================================================
# 7. parse_llm_plan: 旧格式
# =====================================================================
legacy_rows = [
    {"line_id": 1, "visual_type": "出镜", "text": "开场", "material_source": {"type": "static", "file": "/f.png"}},
    {"line_id": 2, "visual_type": "素材", "text": "画面", "material_source": {"type": "dynamic", "category": "标题"}},
]
plan2 = call(dp, "parse_llm_plan",
             '[{"line_id": 1, "visual_type": "出镜", "text": "开场", "material_source": {"type": "static", "file": "/f.png"}},'
             '{"line_id": 2, "visual_type": "素材", "text": "画面", "material_source": {"type": "dynamic", "category": "标题"}}]',
             [{"start": 0, "end": 3}, {"start": 3, "end": 6}], 100.0)
check("legacy plan 数量", len(plan2.slots) == 2)
check("legacy plan 首host", plan2.slots[0].workflow == "host")
# 尾 hf_title 被规则强制为 host (forced_host_ending)
check("legacy plan 尾被强制host", plan2.slots[1].workflow == "host"
      and plan2.slots[1].params.get("fallback_reason") == "forced_host_ending")

# =====================================================================
# 8. ValueError 消息
# =====================================================================
try:
    call(dp, "parse_llm_plan", '{"slots": "not-a-list"}', [], 100.0)
    check("slots非list ValueError", False)
except ValueError as e:
    check("slots非list ValueError", str(e) == "Director response 'slots' is not a list")
try:
    call(dp, "parse_llm_plan", '"just a string"', [], 100.0)
    check("非对象数组 ValueError", False)
except ValueError as e:
    check("非对象数组 ValueError", str(e) == "Director response is not a JSON object or array")

# =====================================================================
# 9. _best_fallback_workflow 链
# =====================================================================
check("fallback host c开", call(dp, "_best_fallback_workflow", {"c"}, prefer="host") == "host")
check("fallback host 仅h", call(dp, "_best_fallback_workflow", {"h"}, prefer="host") == "hf_title")
check("fallback host 仅p", call(dp, "_best_fallback_workflow", {"p"}, prefer="host") == "broll_pexels")
check("fallback host 全禁", call(dp, "_best_fallback_workflow", set(), prefer="host") == "broll_local")
check("fallback hf 仅c", call(dp, "_best_fallback_workflow", {"c"}, prefer="hf_chart") == "host")
check("fallback hf 仅p", call(dp, "_best_fallback_workflow", {"p"}, prefer="hf_title") == "broll_pexels")
check("fallback pexels 仅h", call(dp, "_best_fallback_workflow", {"h"}, prefer="broll_pexels") == "hf_chart")
check("fallback None 直返", call(dp, "_best_fallback_workflow", None, prefer="host") == "host")
check("fallback mixed 直返", call(dp, "_best_fallback_workflow", {"c"}, prefer="mixed_host_broll") == "mixed_host_broll")
check("fallback local 直返", call(dp, "_best_fallback_workflow", set(), prefer="broll_local") == "broll_local")
check("fallback black 直返", call(dp, "_best_fallback_workflow", set(), prefer="black_placeholder") == "black_placeholder")

# =====================================================================
# 10. enforce_host_rules: C线禁用分支
# =====================================================================
def _mk_slots(wfs):
    from app.schemas.director import DirectorSlotPlan
    return [DirectorSlotPlan(
        slot_index=i, start_sec=i * 2.0, end_sec=i * 2.0 + 1.0,
        text_context="s", segment_id=None,
        visual_type=wf,  # type: ignore[arg-type]
        workflow=wf,  # type: ignore[arg-type]
        params={"k": "v"},
    ) for i, wf in enumerate(wfs)]

c_off = call(dp, "enforce_host_rules", _mk_slots(["host", "broll_pexels", "host"]), 10.0, enabled_pipelines={"p"})
check("C禁 host→hf_title(无h则pexels)", all(s.workflow != "host" for s in c_off))
check("C禁 fallback_reason", c_off[0].params["fallback_reason"] == "c_pipeline_disabled")

c_off_h = call(dp, "enforce_host_rules", _mk_slots(["host", "host", "broll_local"]), 10.0, enabled_pipelines={"h"})
check("C禁 仅h host→hf_title", c_off_h[0].workflow == "hf_title" and c_off_h[1].workflow == "hf_title")

# =====================================================================
# 11. cap_host_count 超限采样
# =====================================================================
many = _mk_slots(["host"] * 6)
capped = call(dp, "cap_host_count", many, max_host=4, enabled_pipelines=None)
host_cnt = sum(1 for s in capped if s.workflow == "host")
check("cap 保留≤4", host_cnt <= 4)
check("cap 首尾host", capped[0].workflow == "host" and capped[-1].workflow == "host")
downgraded = [s for s in capped if s.params.get("fallback_reason") == "host_cap_exceeded"]
check("cap 降级数", len(downgraded) == 6 - host_cnt)

# cap: 不超限直返
under = call(dp, "cap_host_count", _mk_slots(["host", "broll_local", "host"]), max_host=4)
check("cap 不超限", all(s.workflow != "broll_pexels" for s in under))

# =====================================================================
# 12. adjacency 去重
# =====================================================================
adj = call(dp, "enforce_adjacency_rules", _mk_slots(["host", "host", "hf_chart", "broll_pexels"]))
has_adj_host = any(adj[i].workflow == "host" and adj[i + 1].workflow == "host"
                   for i in range(len(adj) - 1))
check("adjacency 无相邻host", not has_adj_host)

adj2 = call(dp, "enforce_adjacency_rules", _mk_slots(["hf_chart", "hf_title", "broll_local", "broll_pexels"]))
has_adj_hf = any(adj2[i].workflow in {"hf_chart", "hf_title"} and adj2[i + 1].workflow in {"hf_chart", "hf_title"}
                 for i in range(len(adj2) - 1))
check("adjacency 无相邻HF", not has_adj_hf)

# =====================================================================
# 13. 导出面 (4 个引用方 + 公共 API)
# =====================================================================
for sym in ["parse_llm_plan", "_best_fallback_workflow", "_HOST_FAMILY",
            "enforce_host_rules", "cap_host_count", "enforce_adjacency_rules",
            "map_visual_type_to_workflow", "extract_json", "parse_legacy_row",
            "parse_new_row", "is_new_schema"]:
    check(f"导出 {sym}", hasattr(dp, sym))
check("_HOST_FAMILY 内容", dp._HOST_FAMILY == {"host", "mixed_host_broll"})

# =====================================================================
print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
for l in LOG:
    print(f"  ❌ {l}")
sys.exit(1 if FAIL else 0)

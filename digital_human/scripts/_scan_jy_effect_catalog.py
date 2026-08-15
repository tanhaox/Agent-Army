"""扫描 jy_template_snapshot 全部快照, 提取效果套路 → 聚合目录.

产出:
  1. 终端: 全局聚合(最常用效果/动画/转场/贴纸) + 每模板一行摘要
  2. data/jy_effect_catalog.json: 机器可读目录 (J2 jy_effect_library 的种子)
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SNAP = r"F:\AI-Agent-Local\digital_human\data\jy_template_snapshot"

# ---- pyJianYingDraft metadata: resource_id -> 中文名 ----
id2name = {}
try:
    from pyJianYingDraft.metadata import (video_scene_effect, video_character_effect,
                                          transition_meta, video_intro, video_outro,
                                          text_intro, text_outro, text_loop, filter_meta)
    for mod in (video_scene_effect, video_character_effect, transition_meta,
                filter_meta, video_intro, video_outro, text_intro, text_outro, text_loop):
        for enum_cls in vars(mod).values():
            if isinstance(enum_cls, type) and issubclass(enum_cls, object) and hasattr(enum_cls, "__members__"):
                try:
                    for m in enum_cls.__members__.values():
                        value = getattr(m, "value", None)
                        # EffectMeta/TransitionMeta: 检查常见字段
                        for field in ("resource_id", "effect_id", "id"):
                            rid = getattr(value, field, None)
                            if rid:
                                id2name[str(rid)] = getattr(m, "name", str(m))
                                break
                except Exception:
                    continue
except Exception as exc:
    print("metadata 映射加载失败(忽略, 用裸ID):", exc)


def nm(rid: str) -> str:
    return id2name.get(str(rid), "")


def scan_file(path: str) -> dict:
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    m = data.get("materials", {}) or {}
    out = {
        "anim": [], "effect": [], "video_effect": [], "transition": [],
        "sticker": [], "mask": 0, "speeds": Counter(), "kf": 0,
        "text_fonts": Counter(), "text_colors": Counter(),
        "n_tracks": len(data.get("tracks", [])),
        "n_compound": len(m.get("drafts", []) or []),
        "duration_s": round((data.get("duration") or 0) / 1e6, 1),
    }
    for an in m.get("material_animations", []) or []:
        for a in an.get("animations", []) or []:
            rid = a.get("resource_id")
            out["anim"].append({
                "name": a.get("name") or nm(rid) or rid,
                "type": a.get("type"), "dur_ms": round((a.get("duration") or 0) / 1000),
            })
    for grp, key in (("effects", "effect"), ("video_effects", "video_effect")):
        for e in m.get(grp, []) or []:
            rid = e.get("resource_id")
            out[key].append(e.get("name") or nm(rid) or rid)
    for t in m.get("transitions", []) or []:
        rid = t.get("resource_id")
        out["transition"].append(t.get("name") or nm(rid) or rid)
    for s in m.get("stickers", []) or []:
        out["sticker"].append(s.get("name") or s.get("title") or "?")
    out["mask"] = len(m.get("common_mask", []) or [])
    for sp in m.get("speeds", []) or []:
        if sp.get("speed") not in (None, 1.0, 1):
            out["speeds"][sp.get("speed")] += 1
    for kf in m.get("common_keyframes", []) or []:
        out["kf"] += len(kf.get("keyframes", []) or [])
    for t in m.get("texts", []) or []:
        try:
            c = json.loads(t.get("content") or "{}")
            for st in c.get("styles", []) or []:
                fill = (st.get("fill") or {}).get("content") or {}
                if fill.get("font"):
                    out["text_fonts"][fill["font"]] += 1
                if fill.get("solid"):
                    out["text_colors"][str(fill["solid"].get("color"))] += 1
        except Exception:
            pass
    return out


def find_main(draft_dir: str) -> str | None:
    """快照里主时间轴: Timelines_template.json 优先, 否则 template.json(.bak)."""
    for cand in ("Timelines_template.json", "template.json", "template.json.bak"):
        p = os.path.join(draft_dir, cand)
        if os.path.exists(p):
            return p
    return None


results = {}
for d in sorted(glob.glob(os.path.join(SNAP, "*"))):
    main = find_main(d)
    if not main:
        continue
    r = scan_file(main)
    if not r:
        continue
    # subdraft 也扫(复合片段里的效果)
    for p in glob.glob(os.path.join(d, "subdraft", "*", "draft_content.json")):
        sub = scan_file(p)
        r["anim"] += sub.get("anim", [])
        r["effect"] += sub.get("effect", [])
        r["video_effect"] += sub.get("video_effect", [])
        r["transition"] += sub.get("transition", [])
        r["sticker"] += sub.get("sticker", [])
        r["mask"] += sub.get("mask", 0)
        r["kf"] += sub.get("kf", 0)
    results[os.path.basename(d)] = r

# ---- 聚合 ----
agg = defaultdict(Counter)
for name, r in results.items():
    for a in r["anim"]:
        agg[f"anim_{a['type']}"][a["name"]] += 1
        agg["anim_dur_ms"][a["dur_ms"]] += 1
    for e in r["effect"]:
        agg["effect"][e] += 1
    for e in r["video_effect"]:
        agg["video_effect"][e] += 1
    for t in r["transition"]:
        agg["transition"][t] += 1
    for s in r["sticker"]:
        agg["sticker"][s] += 1

print(f"== 扫描 {len(results)} 个模板 ==\n")
print("== 全局 TOP 效果/动画/转场 ==")
for key in ("anim_in", "anim_out", "effect", "video_effect", "transition", "sticker"):
    if agg.get(key):
        print(f"\n[{key}]")
        for name, cnt in agg[key].most_common(15):
            print(f"  {cnt:3d}× {name}")
print("\n[动画时长分布(ms)]", dict(sorted(agg.get('anim_dur_ms', {}).items())[:12]))

print("\n== 每模板摘要 ==")
for name, r in sorted(results.items()):
    parts = [f"{r['duration_s']}s", f"{r['n_tracks']}轨", f"复合{r['n_compound']}",
             f"动画{len(r['anim'])}", f"特效{len(r['effect'])}+{len(r['video_effect'])}",
             f"转场{len(r['transition'])}", f"贴纸{len(r['sticker'])}",
             f"蒙版{r['mask']}", f"关键帧{r['kf']}"]
    print(f"  {name}: {' | '.join(parts)}")

# ---- 机器可读目录 ----
catalog = {
    "_meta": {"source": "jy_template_snapshot", "date": "2026-08-15", "templates": len(results)},
    "aggregated": {k: dict(v.most_common(30)) for k, v in agg.items() if isinstance(v, Counter)},
    "per_template": {k: {"duration_s": v["duration_s"], "tracks": v["n_tracks"],
                          "compound": v["n_compound"], "mask": v["mask"], "keyframes": v["kf"],
                          "animations": v["anim"], "effects": v["effect"] + v["video_effect"],
                          "transitions": v["transition"], "stickers": v["sticker"],
                          "fonts": dict(v["text_fonts"]), "speeds": dict(v["speeds"])}
                     for k, v in results.items()},
}
out_path = r"F:\AI-Agent-Local\digital_human\data\jy_effect_catalog.json"
json.dump(catalog, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n目录已写: {out_path}")

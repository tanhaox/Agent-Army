"""J 线效果演示: 真实 slot 素材 + 模板级一档特效全家桶.

目的: 用证据回答"这些特效我们的系统能不能融入进来"。
对比样本: 学习期模板分镜。本演示覆盖:
  入场/出场动画、转场、画面特效、滤镜、蒙版、花字、贴纸、独立特效轨。
"""
import glob
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import load_config, set_config

set_config(load_config())
from app.database import init_db, get_session_maker

init_db("sqlite:///data/pipeline.db")
db = get_session_maker()()

import pyJianYingDraft as d
from pyJianYingDraft import ClipSettings, StickerSegment, Timerange, trange

from app.models.director import DirectorJob
from app.services.jy_draft_service import (
    _US, find_highlight_ranges, split_subtitle, wash_subtitle_text,
)

US = _US
DRAFTS = r"C:\Users\tanhaox\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"

job = db.query(DirectorJob).filter(DirectorJob.id.like("338622ef%")).first()
slots = sorted([s for s in job.slots if s.status == "completed" and s.output_path],
               key=lambda s: s.slot_index)[:6]
audio = job.audio_file
manifest = json.load(open(str(audio.file_path).replace("full_paragraph.wav", "manifest.json"), encoding="utf-8"))

folder = d.DraftFolder(DRAFTS)
script = folder.create_draft("J线效果演示_全家桶", 1920, 1080, allow_replace=True)
script.append_tracks([
    d.TrackSpec(d.TrackType.audio, "voice"),
    d.TrackSpec(d.TrackType.video, "main"),
    d.TrackSpec(d.TrackType.effect, "fx"),
    d.TrackSpec(d.TrackType.text, "caption"),
    d.TrackSpec(d.TrackType.sticker, "deco"),
])

# ── audio: 前 25s 的分段 ──
cum = 0.0
audio_segs = 0
for seg in manifest["segments"]:
    dur = float(seg.get("duration") or 0)
    if cum >= 25:
        break
    import os
    wav = os.path.join(os.path.dirname(audio.file_path), seg["file"])
    if dur > 0 and os.path.exists(wav):
        script.add_segment(d.AudioSegment(wav, trange(int(round(cum * US)), int(round(dur * US))), volume=1.0), "voice")
        audio_segs += 1
    cum += dur

# ── video: 6 个 slot, 每个叠不同特效组合 ──
def pick(enum, names, default=None):
    for n in names:
        if hasattr(enum, n):
            return getattr(enum, n)
    return default

intro_pool = [pick(d.IntroType, ["放大"]), pick(d.IntroType, ["向上滑动"]),
              pick(d.IntroType, ["斜切"]), pick(d.IntroType, ["弹入"])]
effect_pool = [pick(d.VideoSceneEffectType, ["暗角"]), pick(d.VideoSceneEffectType, ["左右摇晃"]),
               pick(d.VideoSceneEffectType, ["星火"]), pick(d.VideoSceneEffectType, ["模糊"])]
filter_pool = [pick(d.FilterType, ["质感", "胶片", "清晰"])]
transition = pick(d.TransitionType, ["叠化"])

n_video = 0
prev = None
for i, s in enumerate(slots):
    import os
    if not os.path.exists(s.output_path):
        continue
    mat = d.VideoMaterial(s.output_path)
    alloc_us = int(round(s.duration_sec * US))
    mat_us = int(mat.duration)
    if mat_us < alloc_us:
        seg = d.VideoSegment(mat, trange(int(round(s.start_sec * US)), alloc_us),
                             source_timerange=Timerange(0, mat_us), speed=mat_us / alloc_us, volume=0)
    else:
        seg = d.VideoSegment(mat, trange(int(round(s.start_sec * US)), min(alloc_us, mat_us)), volume=0)
    # 入场动画轮换
    ani = intro_pool[i % len(intro_pool)]
    if ani is not None:
        try:
            seg.add_animation(ani)
        except Exception as e:
            print("动画失败:", e)
    # 画面特效轮换 (暗角/摇晃/星火/模糊)
    eff = effect_pool[i % len(effect_pool)]
    if eff is not None:
        try:
            seg.add_effect(eff)
        except Exception as e:
            print("特效失败:", e)
    # 滤镜 (只给第 2 段)
    if i == 1 and filter_pool[0] is not None:
        try:
            seg.add_filter(filter_pool[0], intensity=60.0)
        except Exception as e:
            print("滤镜失败:", e)
    # 蒙版 (只给第 3 段: 圆形羽化聚光)
    if i == 2:
        try:
            seg.add_mask(pick(d.MaskType, ["圆形"]) or d.MaskType.圆形, feather=0.15, size=0.75)
        except Exception as e:
            print("蒙版失败:", e)
    # 转场 (段间叠化)
    if prev is not None and transition is not None:
        try:
            prev.add_transition(transition)
        except Exception as e:
            print("转场失败:", e)
    script.add_segment(seg, "main")
    prev = seg
    n_video += 1

# ── 独立特效轨: 星火铺 10-20s (轨道级氛围) ──
try:
    fx = effect_pool[2]
    if fx is not None:
        script.add_segment(d.EffectSegment(fx, trange(int(10 * US), int(10 * US))), "fx")
        print("独立特效轨: OK")
except Exception as e:
    print("独立特效轨失败:", e)

# ── text: 前 25s 字幕, 花字 + 入出场动画 + 自动划重点 ──
from app.services.jy_draft_service import _StyledTextSegment

cum = 0.0
n_text = 0
for seg in manifest["segments"]:
    dur = float(seg.get("duration") or 0)
    text = (seg.get("text") or "").strip()
    if cum >= 25:
        break
    if dur > 0 and text:
        washed = wash_subtitle_text(text)
        chunks = split_subtitle(washed, 30)
        seg_start = int(round(cum * US))
        seg_dur = int(round(dur * US))
        alloc = [seg_dur * len(c) // max(len(washed), 1) for c in chunks]
        alloc[-1] = seg_dur - sum(alloc[:-1])
        for chunk, cu in zip(chunks, alloc):
            try:
                ts = _StyledTextSegment(
                    chunk, trange(seg_start, max(cu, 1000)),
                    highlight_ranges=find_highlight_ranges(chunk),
                    clip_settings=ClipSettings(transform_y=-0.75),
                )
                ts.add_effect("7296357486490140149")  # 花字 (demo 同款)
                ts.add_animation(d.TextIntro.渐显)
                ts.add_animation(d.TextOutro.渐隐)
                script.add_segment(ts, "caption")
                n_text += 1
            except Exception as e:
                print("字幕特效失败:", str(e)[:80])
        cum += dur
    else:
        cum += dur

# ── sticker: 从 25期快照抓一个贴纸 resource_id ──
try:
    snap = glob.glob(r"F:\AI-Agent-Local\digital_human\data\jy_template_snapshot\学习25期*\subdraft\*\draft_content.json")
    sticker_id = None
    for p in snap:
        data = json.load(open(p, encoding="utf-8"))
        for st in data.get("materials", {}).get("stickers", []):
            rid = st.get("resource_id") or st.get("resource_id#")
            if rid:
                sticker_id = rid
                break
        if sticker_id:
            break
    if sticker_id:
        script.add_segment(
            StickerSegment(sticker_id, trange(int(12 * US), int(6 * US)),
                           clip_settings=ClipSettings(transform_x=0.3, transform_y=0.3, scale=0.5)),
            "deco")
        print("贴纸 OK:", sticker_id)
    else:
        print("快照未找到贴纸 resource_id, 跳过")
except Exception as e:
    print("贴纸失败:", e)

script.save()
print(f"\n演示草稿已生成: J线效果演示_全家桶 | video={n_video} audio={audio_segs} text={n_text}")

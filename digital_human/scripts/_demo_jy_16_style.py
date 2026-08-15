# -*- coding: utf-8 -*-
"""J 线模仿: 学习16期_小羽毛 排版流 — 两层图 + 逐词字体变化.

16期拆解结论: 零特效/零贴纸, 纯排版 = 背景图片层 + 15条短文字逐词出现,
重点词 20号红 / 普通 15号白, 9种文字动画, 200-500ms。
本演示用我们真实口播稿复刻该模式。
"""
import glob
import json
import os
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import load_config, set_config

set_config(load_config())
from app.database import init_db, get_session_maker

init_db("sqlite:///data/pipeline.db")
db = get_session_maker()()

import pyJianYingDraft as d
from pyJianYingDraft import ClipSettings, trange

from app.models.director import DirectorJob
from app.services.jy_draft_service import _US, wash_subtitle_text

US = _US
DRAFTS = r"C:\Users\tanhaox\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
SRC16 = DRAFTS + r"\学习16期_小羽毛\Resources\local"

job = db.query(DirectorJob).filter(DirectorJob.id.like("338622ef%")).first()
manifest = json.load(open(str(job.audio_file.file_path).replace("full_paragraph.wav", "manifest.json"), encoding="utf-8"))

folder = d.DraftFolder(DRAFTS)
script = folder.create_draft("J线模仿_16期排版流", 1080, 1920, allow_replace=True)
script.append_tracks([
    d.TrackSpec(d.TrackType.audio, "voice"),
    d.TrackSpec(d.TrackType.video, "bg1"),
    d.TrackSpec(d.TrackType.video, "bg2"),
    d.TrackSpec(d.TrackType.text, "w1"),
    d.TrackSpec(d.TrackType.text, "w2"),
    d.TrackSpec(d.TrackType.text, "w3"),
    d.TrackSpec(d.TrackType.text, "w4"),
])

DUR = 16.0  # 演示时长

# ── 图层1: 格子背景 全程 (16期同款底图) ──
bg1 = os.path.join(SRC16, "752620c4c5289ea83c069075ca74c45d.jpg")
script.add_segment(d.VideoSegment(bg1, trange(0, int(DUR * US)), volume=0), "bg1")

# ── 图层2: 油画女 6s 入场 (向右露出 + 缩小出场) ──
bg2 = os.path.join(SRC16, "f76e7a9671743a02ee5beee5dfc91e6f.png")
seg2 = d.VideoSegment(bg2, trange(int(6 * US), int((DUR - 6) * US)), volume=0,
                      clip_settings=ClipSettings(transform_x=0.45, scale_x=0.6, scale_y=0.6))
seg2.add_animation(d.IntroType.渐显)
seg2.add_animation(d.OutroType.缩小)
script.add_segment(seg2, "bg2")

# ── 文字编排: 口播稿前几句 → 逐词组出现, 大小/颜色反差 + 16期动画轮换 ──
INTROS = [d.TextIntro.放大, d.TextIntro.跃进, d.TextIntro.向左露出,
          d.TextIntro.复古打字机, d.TextIntro.渐显, d.TextIntro.模糊缩小]
OUTROS = [d.TextOutro.溶解, d.TextOutro.向左滑动, d.TextOutro.缩小, d.TextOutro.渐隐]
RED = (0.72, 0.11, 0.11)

cum = 0.0
t_cursor = 0.3
n_text = 0
for seg in manifest["segments"]:
    dur = float(seg.get("duration") or 0)
    text = wash_subtitle_text((seg.get("text") or "").strip())
    if cum >= DUR - 2:
        break
    if dur > 0 and text:
        # 断成 2~4 字的词组 (16期的逐词节奏)
        words = [text[i:i + 4] for i in range(0, min(len(text), 12), 4)]
        for wi, w in enumerate(words):
            big = (wi == 1)  # 第2词组做大字
            interval = dur / max(len(words), 1) * 0.8
            show_dur = min(max(interval + 0.5, 0.9), 2.0)  # 四轨轮换下不与同轨重叠
            ts = d.TextSegment(
                w,
                trange(int(round(t_cursor * US)), int(round(show_dur * US))),
                style=d.TextStyle(size=20 if big else 15,
                                  color=RED if big else (1, 1, 1)),
                clip_settings=ClipSettings(
                    transform_y=0.35 - wi * 0.12,
                    transform_x=-0.25 if not big else 0.15,
                    scale_x=1.6 if big else 1.0, scale_y=1.6 if big else 1.0,
                ),
            )
            ts.add_animation(INTROS[n_text % len(INTROS)])
            ts.add_animation(OUTROS[n_text % len(OUTROS)])
            script.add_segment(ts, f"w{(n_text % 4) + 1}")  # 多文字轨 = 16期逐词并行的真相
            n_text += 1
            t_cursor += dur / max(len(words), 1) * 0.8
        cum += dur
    else:
        cum += dur

# ── audio: 对应时长 ──
cum = 0.0
for seg in manifest["segments"]:
    dur = float(seg.get("duration") or 0)
    if cum >= DUR:
        break
    wav = os.path.join(os.path.dirname(job.audio_file.file_path), seg["file"])
    if dur > 0 and os.path.exists(wav):
        take = min(dur, DUR - cum)
        script.add_segment(d.AudioSegment(wav, trange(int(round(cum * US)), int(round(take * US)))), "voice")
    cum += dur

script.save()
print(f"模仿草稿已生成: J线模仿_16期排版流 | 文字元素={n_text} | 底图=16期原素材")

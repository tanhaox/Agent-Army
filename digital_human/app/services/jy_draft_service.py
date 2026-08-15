# -*- coding: utf-8 -*-
"""J 线草稿导出服务 — 导演 job → 剪映明文草稿 (J1, 2026-08-15).

设计: docs/剪映草稿产线-设计方案.md §4
- slot 时间轴直接映射草稿 video 轨 (微秒制, source/target 双坐标系)
- TTS 分段 wav 逐段进 audio 轨 (不聚合, 段落级可在剪映再调)
- manifest 逐段文本进 text 轨 (字幕层)
- 音画不预合成; 渲染出口交给剪映 (人工审 + 调 BGM + 导出)

写入路径结论 (实验 A 验证): 新版剪映"打开时接受明文、保存时才加密",
pyJianYingDraft 生成的明文 draft_content.json 可直接被剪映打开。
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

import pyJianYingDraft as draft_mod
from pyJianYingDraft import ClipSettings, TextSegment, Timerange, trange

from app.config import get_config
from app.models.director import DirectorJob

logger = logging.getLogger(__name__)

__all__ = ["export_job_draft", "wash_subtitle_text", "split_subtitle"]

_US = 1_000_000  # 秒 → 微秒

# ── 字幕样式 (2026-08-15 用户口径: 美观字号 5, 非 pyJYD 默认 8) ──
_SUBTITLE_SIZE = 5.0
# 划重点高亮: 大一号 + 黄色 (取自剪映"智能划重点"实测 schema: size 6 / [1, 0.87, 0])
_HL_COLOR = (1.0, 0.87, 0.0)
_HL_SIZE_DELTA = 1.0

# ── 字幕洗涤 (TTS 读法 → 阅读文本) ──────────────────────────────
# 仅做确定性转换 (保守, 避免 LLM 成本/幻觉); 转换记录进日志供人工抽查。
_CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_NUM_WORD = "一二三四五六七八九十百"
_BREAK_PUNCT = "，。！？；：、—…,"


def _cn_to_int(s: str) -> int | None:
    """中文数字(≤999, 十/百 级) → 整数. 解析失败返回 None."""
    try:
        total, num = 0, 0
        for ch in s:
            if ch in _CN_DIGIT:
                num = num * 10 + _CN_DIGIT[ch]
            elif ch == "十":
                total += (num or 1) * 10
                num = 0
            elif ch == "百":
                total += (num or 1) * 100
                num = 0
            else:
                return None
        return total + num
    except Exception:
        return None


def _num_to_cn_pattern(text: str) -> str:
    """'X点Y' (两侧均为中文数字) → 'X.Y': 四点六→4.6, 二十八点三→28.3.

    右侧必须也是数字词, 排除'有点吓人'/'一点心意'这类真中文。
    """
    import re

    pat = re.compile(r"([一二三四五六七八九十百零〇]+)点([一二三四五六七八九十百零〇]+)")

    def repl(m: "re.Match[str]") -> str:
        a, b = _cn_to_int(m.group(1)), _cn_to_int(m.group(2))
        if a is None or b is None:
            return m.group(0)
        # 小数部分去掉无效前导零语义: 二十八点三 → 28.3 (b=3)
        return f"{a}.{b}"

    return pat.sub(repl, text)


def wash_subtitle_text(text: str) -> str:
    """TTS 读法 → 字幕阅读文本 (确定性规则).

    1. 'X点Y' 数字读法 → 'X.Y' (四点六 → 4.6)
    2. 拉丁字母后紧跟的中文数字 → 阿拉伯 + 空格 (Grok四点六/Grok4.6 → Grok 4.6;
       Mythos五 → Mythos 5)
    3. 折叠重复标点 (，，→ ，)、去首尾空白
    """
    import re

    t = text.strip()
    t = _num_to_cn_pattern(t)
    # latin + 中文数字 → latin + 空格 + 阿拉伯
    def _latin_num(m):
        v = _cn_to_int(m.group(2))
        return f"{m.group(1)} {v}" if v is not None else m.group(0)
    t = re.sub(r"([A-Za-z])([一二三四五六七八九])", _latin_num, t)
    # latin + 小数 (X点Y 转换产物如 GLM5.3) → 补空格; 纯整数版本号 (V4) 不动
    t = re.sub(r"([A-Za-z])(\d+\.\d+)", r"\1 \2", t)
    # 折叠重复标点
    t = re.sub(r"([，。！？；、…—])\1+", r"\1", t)
    return t.strip()


def split_subtitle(text: str, limit: int) -> list[str]:
    """超长字幕断句: 优先在标点处断, 无标点则硬断 (CJK 安全)."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    rest = text
    while len(rest) > limit:
        # 在 limit 窗口内找最后一个断点标点 (留 6 字下限防碎片)
        window = rest[: limit + 1]
        cut = -1
        for i in range(min(len(window) - 1, limit), 5, -1):
            if window[i] in _BREAK_PUNCT:
                cut = i + 1
                break
        if cut <= 0:
            cut = limit
        chunk = rest[:cut].strip(_BREAK_PUNCT + " ")
        if chunk:
            chunks.append(chunk)
        rest = rest[cut:].lstrip(_BREAK_PUNCT + " ")
    if rest.strip(_BREAK_PUNCT + " "):
        chunks.append(rest.strip(_BREAK_PUNCT + " "))
    return chunks


def find_highlight_ranges(text: str) -> list[tuple[int, int]]:
    """自动划重点: 数字与拉丁专有名词的字符区间 (0-based, 左闭右开).

    洗涤后的字幕里, 阿拉伯数字 (4.6 / 28.3%) 与模型名 (GLM / DeepSeek)
    天然是重点词 — schema 已在剪映"智能划重点"实测确认 (styles 多段 range)。
    """
    import re

    pat = re.compile(r"[0-9][0-9.,]*%?|[A-Za-z][A-Za-z0-9.+-]*")
    return [(m.start(), m.end()) for m in pat.finditer(text)]


class _StyledTextSegment(TextSegment):
    """字幕 + 自动划重点: 高亮区间大一号 + 黄色, 其余基础样式.

    pyJYD 原生只输出单一 style (覆盖全文); 本子类在导出时改写 content 的
    styles 数组为多段 range — 与剪映划重点的数据形态一致。
    """

    def __init__(self, text: str, timerange: Timerange, *,
                 highlight_ranges: list[tuple[int, int]] | None = None, **kwargs):
        kwargs.setdefault("style", draft_mod.TextStyle(size=_SUBTITLE_SIZE, color=(1.0, 1.0, 1.0)))
        super().__init__(text, timerange, **kwargs)
        self._hl_ranges = sorted(highlight_ranges or [])

    def export_material(self) -> dict:
        ret = super().export_material()
        if not self._hl_ranges:
            return ret
        content = json.loads(ret["content"])
        base = dict(content["styles"][0])
        hl = dict(base)
        hl["size"] = _SUBTITLE_SIZE + _HL_SIZE_DELTA
        fill = json.loads(json.dumps(base.get("fill") or {}))
        if "content" in fill and "solid" in fill["content"]:
            fill["content"]["solid"]["color"] = list(_HL_COLOR)
        hl["fill"] = fill

        styles: list[dict] = []
        pos = 0
        for s, e in self._hl_ranges:
            s = max(s, pos)
            if s >= e:
                continue
            if s > pos:
                styles.append({**base, "range": [pos, s]})
            styles.append({**hl, "range": [s, e]})
            pos = e
        if pos < len(self.text):
            styles.append({**base, "range": [pos, len(self.text)]})
        if styles:
            content["styles"] = styles
            ret["content"] = json.dumps(content, ensure_ascii=False)
        return ret


def _drafts_dir() -> Path:
    cfg = get_config()
    return Path(cfg.defaults.jianying_drafts_dir)


def _load_manifest(audio_path: str | Path) -> dict[str, Any] | None:
    """TTS manifest 与整段 wav 同目录 (projects/*/audio/manifest.json)."""
    p = Path(audio_path).parent / "manifest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[jy_export] manifest 解析失败 %s: %s", p, exc)
        return None


def _trange_sec(start_sec: float, dur_sec: float) -> draft_mod.Timerange:
    return trange(int(round(start_sec * _US)), int(round(dur_sec * _US)))


def export_job_draft(db: Session, job_id: str) -> dict[str, Any]:
    """导演 job → 剪映草稿文件夹. 同步执行 (纯 JSON 写盘, <1s).

    Returns: {draft_name, draft_dir, video_segments, audio_segments,
              text_segments, canvas, skipped_slots}
    Raises: ValueError (job 不存在 / 无可导出 slot / 无音频)
    """
    job = db.query(DirectorJob).filter(DirectorJob.id == job_id).first()
    if not job:
        raise ValueError(f"任务不存在: {job_id}")

    slots = [s for s in job.slots if s.status == "completed" and s.output_path]
    slots.sort(key=lambda s: s.slot_index)
    if not slots:
        raise ValueError("没有已完成的 slot, 先执行任务再导出")

    audio_file = job.audio_file
    if not audio_file or not Path(audio_file.file_path).exists():
        raise ValueError("任务没有已合成的音频 (audio_file 缺失)")

    width, height = (1080, 1920) if job.video_format != "landscape" else (1920, 1080)
    name = f"DH_{datetime.now().strftime('%Y%m%d_%H%M')}_{job.script_id[:8]}"
    folder = draft_mod.DraftFolder(str(_drafts_dir()))
    script = folder.create_draft(name, width, height, allow_replace=True)

    # 轨道: 后来居上 — 强调/字幕最上, video 中, audio 底
    # emph1~3 = R9 强调大字轨(多轨轮换, 45期协同三件套); sfx = 同帧音效轨
    script.append_tracks([
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "voice"),
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "sfx"),
        draft_mod.TrackSpec(draft_mod.TrackType.video, "main"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "caption"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "emph1"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "emph2"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "emph3"),
    ])

    # ── audio 轨: TTS 分段逐段进轨 (时间轴 = 累计时长), 无 manifest 回退整段 ──
    manifest = _load_manifest(audio_file.file_path)
    n_audio = 0
    if manifest and manifest.get("segments"):
        cum = 0.0
        for seg in manifest["segments"]:
            dur = float(seg.get("duration") or 0)
            wav = Path(audio_file.file_path).parent / seg["file"]
            if dur > 0 and wav.exists():
                script.add_segment(
                    draft_mod.AudioSegment(str(wav), _trange_sec(cum, dur), volume=1.0),
                    "voice",
                )
                n_audio += 1
            cum += dur
        audio_mode = f"manifest 分段 ×{n_audio}"
    else:
        dur = float(audio_file.duration or _probe_duration(audio_file.file_path) or 0)
        if dur <= 0:
            raise ValueError("音频时长未知且无 manifest, 无法导出")
        script.add_segment(
            draft_mod.AudioSegment(str(audio_file.file_path), _trange_sec(0, dur)),
            "voice",
        )
        n_audio = 1
        audio_mode = "整段 (无 manifest)"

    # ── video 轨: slot 产物按分配时间窗放轨, 静音 (声音归 TTS 轨) ──
    # 音画同步 (2026-08-15): 素材实际时长普遍略短于分配窗口 (毫秒级漂移累积
    # 曾致画面比音轨短 ~1.9s)。素材短 → 微降速拉满分配窗口 (≤15%, 不可感知);
    # 素材长 → 截取前段。素材实例缓存避免同素材多 slot 重复探测。
    skipped: list[int] = []
    mat_cache: dict[str, draft_mod.VideoMaterial] = {}
    for s in slots:
        if not Path(s.output_path).exists():
            skipped.append(s.slot_index)
            continue
        mat = mat_cache.get(s.output_path)
        if mat is None:
            mat = draft_mod.VideoMaterial(s.output_path)
            mat_cache[s.output_path] = mat
        alloc_us = int(round(s.duration_sec * _US))
        mat_us = int(mat.duration)
        seg: draft_mod.VideoSegment
        if mat_us < alloc_us and mat_us > 0:
            speed = mat_us / alloc_us
            if speed >= 0.85:
                seg = draft_mod.VideoSegment(
                    mat,
                    trange(int(round(s.start_sec * _US)), alloc_us),
                    source_timerange=Timerange(0, mat_us),
                    speed=speed,
                    volume=0,
                )
            else:  # 缺口过大不硬拉, 钳制并记录
                logger.warning("[jy_export] slot %d 素材缺口过大 (%.2fs/%.2fs), 保持钳制",
                               s.slot_index, mat_us / _US, alloc_us / _US)
                seg = draft_mod.VideoSegment(
                    mat, trange(int(round(s.start_sec * _US)), mat_us), volume=0)
        else:
            seg = draft_mod.VideoSegment(
                mat,
                trange(int(round(s.start_sec * _US)), min(alloc_us, mat_us)),
                volume=0,
            )
        script.add_segment(seg, "main")

    # ── text 轨: 逐段字幕 (洗 TTS 读法 + 超长断句, 时长按字数比例分配) ──
    # 横屏每屏上限 30 字 (2026-08-15 用户实测超出横屏); 竖屏画面窄取 18。
    max_chars = 18 if height > width else 30
    n_text = 0
    r9_stats = {"emphasis": 0, "sfx": 0, "sfx_missing": 0, "sfx_density_skip": 0}
    _emph_slot = [0]
    _last_sfx = [None]
    if manifest and manifest.get("segments"):
        cum = 0.0
        for seg in manifest["segments"]:
            dur = float(seg.get("duration") or 0)
            text = (seg.get("text") or "").strip()
            if dur > 0 and text:
                washed = wash_subtitle_text(text)
                if washed != text:
                    logger.info("[jy_export] 字幕洗涤: %r → %r", text, washed)
                total_len = max(len(washed), 1)
                chunks = split_subtitle(washed, max_chars)
                seg_start_us = int(round(cum * _US))
                seg_dur_us = int(round(dur * _US))
                # 整数微秒按字数分配, 末条吃余数 — 保证 Σchunk ≤ seg_dur, 不与下段重叠
                alloc = [seg_dur_us * len(c) // total_len for c in chunks]
                alloc[-1] = seg_dur_us - sum(alloc[:-1])
                for chunk, chunk_us in zip(chunks, alloc):
                    try:
                        script.add_segment(
                            _StyledTextSegment(
                                chunk,
                                trange(seg_start_us, max(chunk_us, 1000)),
                                highlight_ranges=find_highlight_ranges(chunk),
                                clip_settings=ClipSettings(transform_y=-0.75),
                            ),
                            "caption",
                        )
                        n_text += 1
                    except Exception as exc:  # 单条字幕失败不阻塞
                        logger.warning("[jy_export] 字幕段失败: %s | %s", chunk[:20], exc)
                    # R9 自动编排: 强调大字 + 同帧音效 (密度闸门在内部)
                    _auto_choreograph(script, chunk, seg_start_us, max(chunk_us, 1000),
                                      _emph_slot, r9_stats, _last_sfx)
                    seg_start_us += chunk_us
                cum += dur
            else:
                cum += dur

    script.save()
    draft_dir = _drafts_dir() / name
    result = {
        "draft_name": name,
        "draft_dir": str(draft_dir),
        "canvas": f"{width}x{height}",
        "video_segments": len(slots) - len(skipped),
        "audio_segments": n_audio,
        "audio_mode": audio_mode,
        "text_segments": n_text,
        "emphasis_words": r9_stats["emphasis"],
        "sfx_attached": r9_stats["sfx"],
        "sfx_missing": r9_stats["sfx_missing"],
        "sfx_density_skip": r9_stats["sfx_density_skip"],
        "skipped_slots": skipped,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
    }
    logger.info("[jy_export] %s -> %s (%s)", job_id, name, result)
    return result


# ── R9 自动编排 (2026-08-16): 划重点词→强调轨大字→同帧语义音效 + 密度规则 ──
# 知识来源: 45期协同三件套 / 音效语义库(用户标注) / 密度规则(用户口径) — 全确定性, 无 LLM
_EMPH_COLOR = (1.0, 0.96, 0.54)   # 引文金: 数字/金额大字 (45期 T6 实测值)
_EMPH_COLOR_RED = (0.72, 0.11, 0.11)  # 冲击红: 疑问/设问 (16/28/45期四证)
_EMPH_SIZE = _SUBTITLE_SIZE + 3.0
_EMPH_ANIMS = ("放大", "跃进", "向右滑动")  # 轮换 (45期/高频动画池)

# 金额语境词 (数字+语境 → money 族; 纯数字/专名 → punchline 叮族; 问句 → 悬疑族)
_MONEY_CTX = ("万", "亿", "元", "美元", "收入", "赚", "营收", "薪", "融资", "估值",
              "利润", "市值", "ARR", "GMV", "价格", "涨价", "降价", "关税", "成本")
_SFX_FAMILY = {
    "money": ("金币到账叮咚声", "叮", "综艺叮~~"),
    "punchline": ("叮", "综艺叮~~"),
    "suspense": ("诡异的滴水声", "紧张转场音效"),
}


def _classify_chunk(chunk: str) -> tuple[str, str | None]:
    """字幕块语义分类: (类别, 强调词). 类别 ∈ money/punchline/suspense/plain."""
    import re

    ranges = find_highlight_ranges(chunk)
    kw = None
    for s, e in ranges:
        cand = chunk[s:e]
        if len(cand) >= 2 or cand.isdigit():
            kw = cand
            break
    if re.search(r"[?？]$", chunk.strip()):
        return "suspense", None  # 问句: 音效即可, 不升大字 (R12 的 ? 由字幕承载)
    if kw and re.search(r"\d", kw) and any(w in chunk for w in _MONEY_CTX):
        return "money", kw
    if kw:
        return "punchline", kw
    return "plain", None


def _auto_choreograph(script: Any, chunk: str, start_us: int, dur_us: int,
                      emph_slot: list[int], stats: dict[str, int],
                      last_sound_us: list[int]) -> None:
    """R9: 每个字幕块 → 强调大字(金/红) + 同帧语义音效 + 密度闸门."""
    cat, kw = _classify_chunk(chunk)

    # ① 强调大字轨 (多轨轮换防重叠) — 关键词占比过大时跳过(字幕已承载)
    if kw and len(kw) <= max(int(len(chunk) * 0.7), 4):
        color = _EMPH_COLOR if cat in ("money", "punchline") else _EMPH_COLOR_RED
        track = f"emph{(emph_slot[0] % 3) + 1}"
        emph_slot[0] += 1
        anim = _EMPH_ANIMS[emph_slot[0] % len(_EMPH_ANIMS)]
        try:
            seg = _EmphTextSegment(
                kw, trange(start_us, max(dur_us, 500_000)),
                color=color,
                clip_settings=ClipSettings(transform_y=0.42, scale_x=1.25, scale_y=1.25),
            )
            seg.add_animation(getattr(draft_mod.TextIntro, anim))
            seg.add_animation(draft_mod.TextOutro.渐隐)
            script.add_segment(seg, track)
            stats["emphasis"] += 1
        except Exception as exc:
            logger.warning("[jy_export] 强调字失败 %r: %s", kw, exc)

    # ② 同帧音效 + 密度闸门: 前 30s 全类别高密度; 之后只留 money/punchline/suspense
    #    且间隔 ≥4s (用户口径: 长篇前 30 秒之外降档, 再多烦人)
    if cat == "plain":
        return
    if last_sound_us[0] is not None and start_us - last_sound_us[0] < 4_000_000 and start_us > 30_000_000:
        stats["sfx_density_skip"] += 1
        return
    fam = _SFX_FAMILY[cat]
    name = fam[stats.get(f"_rot_{cat}", 0) % len(fam)]  # 族内轮换防腻 (A/B 变奏规则)
    stats[f"_rot_{cat}"] = stats.get(f"_rot_{cat}", 0) + 1
    if attach_sound(script, "sfx", name, start_us / _US, volume=0.9):
        stats["sfx"] += 1
        last_sound_us[0] = start_us
    else:
        stats["sfx_missing"] += 1


class _EmphTextSegment(_StyledTextSegment):
    """强调大字: 固定大号金色样式 (R9)."""

    def __init__(self, text: str, timerange: Timerange, *, color=_EMPH_COLOR, **kw):
        super().__init__(text, timerange, highlight_ranges=[], **kw)
        self._emph_color = color

    def export_material(self) -> dict:
        ret = super().export_material()
        content = json.loads(ret["content"])
        for st in content.get("styles", []):
            st["size"] = _EMPH_SIZE
            fill = st.get("fill") or {}
            if "content" in fill and "solid" in fill["content"]:
                fill["content"]["solid"]["color"] = list(self._emph_color)
        ret["content"] = json.dumps(content, ensure_ascii=False)
        return ret


def _probe_duration(path: str | Path) -> float | None:
    """pymediainfo 兜底探测时长 (AudioFile.duration 为空时)."""
    try:
        import pymediainfo

        mi = pymediainfo.MediaInfo.parse(str(path))
        track = mi.tracks[0] if mi.tracks else None
        if track and track.duration:
            return float(track.duration) / 1000.0
    except Exception as exc:
        logger.warning("[jy_export] 时长探测失败 %s: %s", path, exc)
    return None


# ── 音效挂载 (J2 前置, 2026-08-16): 语义分类见 data/jy_sounds/_semantics.json ──
_SOUNDS_DIR = Path(__file__).resolve().parents[2] / "data" / "jy_sounds"


def sound_path(name: str) -> Path | None:
    """按语义名取音效文件 (库: data/jy_sounds/<名>.mp3)."""
    p = _SOUNDS_DIR / f"{name}.mp3"
    return p if p.exists() else None


def attach_sound(script: Any, track_name: str, sound_name: str, at_sec: float,
                 volume: float = 1.0) -> bool:
    """往草稿音效轨挂一个音效. 缺文件时记日志返回 False (不阻塞导出)."""
    p = sound_path(sound_name)
    if not p:
        logger.warning("[jy_export] 音效缺失, 跳过: %s", sound_name)
        return False
    dur = _probe_duration(p) or 1.0
    script.add_segment(
        draft_mod.AudioSegment(
            str(p), trange(int(round(at_sec * _US)), int(round(dur * _US))), volume=volume
        ),
        track_name,
    )
    return True

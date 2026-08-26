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
from pyJianYingDraft import ClipSettings, TextIntro, TextSegment, Timerange, trange

from app.config import get_config
from app.models.director import DirectorJob

logger = logging.getLogger(__name__)

__all__ = ["export_job_draft", "export_ppt_draft", "wash_subtitle_text", "split_subtitle"]

_US = 1_000_000  # 秒 → 微秒

# ── PPT 页整页动画 (2026-08-21 剪映分流) ──
# 每页 = 1 静态帧, 动效由剪映原生给: 整页入场动画 + 页间转场.
# 渐显最稳 (专业稿标配); 想更"活"可换 IntroType.向上滑动/轻微放大.
_JY_PPT_ENTRANCE = draft_mod.IntroType.渐显
_JY_PPT_TRANSITION = draft_mod.TransitionType.上移

# ── 字幕样式 (2026-08-15 用户口径: 美观字号 5, 非 pyJYD 默认 8) ──
_SUBTITLE_SIZE = 5.0
# 字幕黑底条 (2026-08-27 参考片同款): 用户实测 v9 后弃用 — 我们的字幕多压暗调画面,
# 黑底条反而累赘。pyJYD 写法备查: TextBackground(color="#000000", alpha=0.55, round_radius=0.08)
# 署名条 (黄底黑字, 引用卡署名用) 保留: _CREDIT_BG
_CREDIT_BG = draft_mod.TextBackground(color="#FFDE00", alpha=0.95, round_radius=0.06)
# 内联划重点升级 (2026-08-17 v2): +1→+2.5 字号差 + 金色, 代替被砍掉的独立强调轨
# (剪映"智能划重点"的真实做法 — 关键词嵌在字幕行内, 变色变大, 不另起文字层)
_HL_COLOR = (1.0, 0.96, 0.54)  # 引文金 (45期实测)
_HL_COLOR_RED = (0.72, 0.11, 0.11)  # 冲击红 (四模板验证)
_HL_SIZE_DELTA = 2.5

# ── R9 v3 (2026-08-18): 动态字幕 = TextIntro 动画挂字幕段本身 + 配对音效 ──
# 字幕抑制已撤 (2026-08-26 用户决策: 恢复全篇字幕): HF 卡是画面补充不是字幕替代,
# 抑制导致 HF 段无字幕且窗口错位误杀邻近字幕。hf_windows 仅保留给边界音效用。
# 知识源: config/jy_animation_sound_pairs.json (动画↔同帧音效配对, 库缺回退 _SFX_FAMILY)
#         config/jy_sound_semantics.json (title_in 族 = HF 边界转场音)
_HF_TEXT_FAMILIES = {"hf_title", "hf_chart", "hf_opening", "hf_quote"}


def _load_jy_config(name: str) -> dict:
    p = Path(__file__).resolve().parents[2] / "config" / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[jy_export] 配置加载失败 %s: %s", name, exc)
        return {}


_ANIM_PAIRS = _load_jy_config("jy_animation_sound_pairs.json").get("animation_sound_family", {})
_TITLE_IN_SOUNDS = (
    _load_jy_config("jy_sound_semantics.json")
    .get("categories", {}).get("title_in", {}).get("sounds", [])
)

# 类别 → TextIntro 动画 (首条可见字幕用卡拉OK 逐字点亮); 配对音库缺时回退 _SFX_FAMILY
_CAT_ANIM: dict[str, tuple[str, int]] = {
    "suspense": ("向上滑动", 400),
    "punchline": ("放大", 400),
    "money": ("星光闪闪", 400),
}

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

    0. 剥情绪标签 (2026-08-17 bug 修复): manifest 文本带 P5 内联标签 [calm]/[serious]/
       [confident]/[surprised] 等 — 不剥则标签进字幕, 且 latin 正则把 calm/serious
       当专名抓成强调大字+挂音效 (三重污染), 必须第一道工序清除
    0.5 剥拼音标注 (2026-08-25): <行|HANG2>/<铟|YIN1> (词表纠音 + 稿内手写临时标注)
       只给 TTS 读, 字幕/观众可见文本一律还原裸字
    1. 'X点Y' 数字读法 → 'X.Y' (四点六 → 4.6)
    2. 拉丁字母后紧跟的中文数字 → 阿拉伯 + 空格 (Grok四点六/Grok4.6 → Grok 4.6;
       Mythos五 → Mythos 5)
    3. 折叠重复标点 (，，→ ，)、去首尾空白
    """
    import re

    from .pinyin_fix import strip_pinyin_marks

    t = text.strip()
    t = strip_pinyin_marks(t)
    t = re.sub(r"\[[a-zA-Z]+\]\s*", "", t)  # 剥 [calm]/[serious] 等情绪标签
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
    """字幕 + 内联划重点: 高亮区间大两号半 + 变色, 其余基础样式.

    v2 (2026-08-17): 代替被砍掉的独立强调轨 — 剪映"智能划重点"的做法,
    关键词嵌在字幕行内变色变大, 不另起文字层(解决与字幕/HF卡重合+截断三问题).
    """
    _HL_DUAL_COLOR = True  # 数字/专名→金, 问句核心→红

    def __init__(self, text: str, timerange: Timerange, *,
                 highlight_ranges: list[tuple[int, int]] | None = None,
                 red_ranges: list[tuple[int, int]] | None = None,
                 **kwargs):
        kwargs.setdefault("style", draft_mod.TextStyle(
            size=_SUBTITLE_SIZE, color=_SUBTITLE_COLOR, align=_SUBTITLE_ALIGN))
        # 字幕黑底条已撤 (2026-08-27 用户实测弃用), 裸白字回归
        super().__init__(text, timerange, **kwargs)
        self._hl_ranges = sorted(highlight_ranges or [])
        self._red_ranges = sorted(red_ranges or [])

    def export_material(self) -> dict:
        ret = super().export_material()
        if not self._hl_ranges and not self._red_ranges:
            return ret
        content = json.loads(ret["content"])
        base = dict(content["styles"][0])

        def make_style(color, ranges):
            """仅产出高亮段 (金/红), 空档留给下方合并时统一填 base — 避免两组 base 重叠."""
            hl = dict(base)
            hl["size"] = _SUBTITLE_SIZE + _HL_SIZE_DELTA
            fill = json.loads(json.dumps(base.get("fill") or {}))
            if "content" in fill and "solid" in fill["content"]:
                fill["content"]["solid"]["color"] = list(color)
            hl["fill"] = fill
            return [{**hl, "range": [s, e]} for s, e in ranges if s < e]

        gold = make_style(_HL_COLOR, self._hl_ranges) if self._hl_ranges else []
        # 红通道并入金 (2026-08-26 用户决策): 放大字颜色统一 fff58a, 不再金红混用
        red = make_style(_HL_COLOR, self._red_ranges) if self._red_ranges else []
        # 合并两组 (金+红), 按位置排序, 空白用 base 填充; 重叠时先到者优先
        merged = sorted(gold + red, key=lambda s: s["range"][0])
        styles = []
        cursor = 0
        for st in merged:
            s, e = st["range"]
            if s < cursor:
                continue  # 已被更早区间覆盖, 丢弃避免嵌套样式
            if s > cursor:
                styles.append({**base, "range": [cursor, s]})
            styles.append(st)
            cursor = e
        if cursor < len(self.text):
            styles.append({**base, "range": [cursor, len(self.text)]})
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

    # 轨道: 后来居上 — caption 最上(内联划重点), video 中, audio 底
    # 2026-08-17 v2: 砍掉 emph1~3 独立强调轨(与字幕/HF卡高度重合+截断问题),
    # 强调改为字幕内联划重点(加大字号差+变色) — 剪映"智能划重点"的真实做法
    script.append_tracks([
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "voice"),
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "sfx"),
        draft_mod.TrackSpec(draft_mod.TrackType.video, "main"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "caption"),
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
    hf_windows: list[tuple[int, int]] = []  # 文字承载 HF 窗 (字幕抑制用, v3 独载分工)
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
            else:  # 缺口过大: 循环铺满分配窗口 (2026-08-26 改) — 旧版钳制留黑,
                # 50s 大 slot 配 20s 素材时尾部 ~30s 黑屏 (实测"尾部画面短缺"根因);
                # 素材重复播完即接续, 远好于黑场。配合 parse 层拆超长 slot, 此分支仅为最后兜底。
                logger.warning("[jy_export] slot %d 素材缺口大 (%.2fs/%.2fs), 循环铺满",
                               s.slot_index, mat_us / _US, alloc_us / _US)
                placed_us = 0
                while placed_us < alloc_us:
                    take = min(mat_us, alloc_us - placed_us)
                    script.add_segment(draft_mod.VideoSegment(
                        mat,
                        trange(int(round((s.start_sec * _US) + placed_us)), take),
                        source_timerange=Timerange(0, take),
                        volume=0,
                    ), "main")
                    placed_us += take
                if s.workflow in _HF_TEXT_FAMILIES:
                    ws = int(round(s.start_sec * _US))
                    hf_windows.append((ws, ws + alloc_us))
                continue
        else:
            seg = draft_mod.VideoSegment(
                mat,
                trange(int(round(s.start_sec * _US)), min(alloc_us, mat_us)),
                volume=0,
            )
        script.add_segment(seg, "main")
        if s.workflow in _HF_TEXT_FAMILIES:
            ws = int(round(s.start_sec * _US))
            hf_windows.append((ws, ws + alloc_us))

    # ── HF 边界转场音 (v3): 画面切换同帧挂 title_in 族 whoosh, 纯音频不碰文字 ──
    n_boundary = 0
    _title_in_avail = [s for s in _TITLE_IN_SOUNDS if sound_path(s)]
    for i, (ws, we) in enumerate(hf_windows):
        if not _title_in_avail:
            break
        # v2: whoosh 不超过其文字窗长 — 长音效跨窗会与后续字幕音效抢轨
        if attach_sound(script, "sfx", _title_in_avail[i % len(_title_in_avail)],
                        ws / _US, volume=0.9, max_sec=(we - ws) / _US):
            n_boundary += 1

    # ── text 轨: 逐段字幕 (洗 TTS 读法 + 超长断句, 时长按字数比例分配) ──
    # 横屏每屏上限 30 字 (2026-08-15 用户实测超出横屏); 竖屏画面窄取 18。
    max_chars = 18 if height > width else 30
    n_text = 0
    r9_stats = {"emphasis": 0, "sfx": 0, "sfx_missing": 0, "sfx_density_skip": 0,
                "anim": 0, "caption_suppressed": 0, "sfx_boundary": n_boundary}
    _last_sfx = [None]
    _first_caption = [True]
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
                    # 字幕抑制已撤 (2026-08-26 用户决策): HF 卡是画面补充不是字幕
                    # 替代 — 抑制导致 HF 段整段无字幕(听不清无兜底), 且 HF 时长被
                    # clamp 后窗口错位会误杀邻近字幕。恢复全篇逐句字幕。
                    # R9 v3: 分类拿内联高亮区间 + 动效(动画名) + 同帧音效
                    gold, red, anim, anim_ms = _auto_choreograph(
                        script, chunk, seg_start_us, r9_stats, _last_sfx,
                        first=_first_caption[0])
                    _first_caption[0] = False
                    # 内联划重点: R9 语义区间 + find_highlight_ranges 数字/专名兜底
                    hl = sorted(set(gold + find_highlight_ranges(chunk)))
                    rr = sorted(set(red))
                    try:
                        seg = _StyledTextSegment(
                            chunk,
                            trange(seg_start_us, max(chunk_us, 1000)),
                            highlight_ranges=hl,
                            red_ranges=rr,
                            clip_settings=ClipSettings(transform_y=-0.75),
                        )
                        # 动态字幕 v2→v3: 动画挂字幕段本身 (不加层, 零重合)
                        if anim:
                            seg.add_animation(
                                getattr(TextIntro, anim),
                                duration=anim_ms * 1000 if anim_ms else None,
                            )
                            r9_stats["anim"] += 1
                        script.add_segment(seg, "caption")
                        n_text += 1
                    except Exception as exc:  # 单条字幕失败不阻塞
                        logger.warning("[jy_export] 字幕段失败: %s | %s", chunk[:20], exc)
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
        "anim_attached": r9_stats["anim"],
        "caption_suppressed": r9_stats["caption_suppressed"],
        "sfx_boundary": r9_stats["sfx_boundary"],
        "skipped_slots": skipped,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
    }
    logger.info("[jy_export] %s -> %s (%s)", job_id, name, result)
    return result


def export_ppt_draft(job_id: str, work_root: str | Path) -> dict[str, Any]:
    """PPT 出片 → 剪映草稿 (2026-08-20): 各页 mp4 → video 轨, 整段音频 → voice 轨,
    每页台词 → caption 字幕轨. 音画不合成, 打开剪映即可审片/调 BGM/导出.

    ppt.py 管线产物: work_root/{job_id}/ppt_manifest.json 含 {clips[], audio}.
    纯 JSON 写盘, <1s. Raises ValueError 缺产物/音频.
    """
    workdir = Path(work_root) / job_id
    manifest_path = workdir / "ppt_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"PPT 产物缺失 (未完成渲染): {job_id}")
    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips = meta.get("clips") or []
    audio_path = meta.get("audio")
    if not clips:
        raise ValueError("没有已渲染的 PPT 页, 先完成成片再导出")
    if not audio_path or not Path(audio_path).exists():
        raise ValueError("PPT 音频缺失 (audio 未生成)")

    # 校验各页 mp4 存在
    valid_clips = []
    for c in clips:
        p = Path(c["path"])
        if p.exists():
            valid_clips.append(c)
    if not valid_clips:
        raise ValueError("各页 mp4 文件均缺失")

    width, height = 1920, 1080  # PPT 16:9 横屏
    name = f"PPT_{datetime.now().strftime('%Y%m%d_%H%M')}_{job_id[:8]}"
    folder = draft_mod.DraftFolder(str(_drafts_dir()))
    script = folder.create_draft(name, width, height, allow_replace=True)
    script.append_tracks([
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "voice"),
        draft_mod.TrackSpec(draft_mod.TrackType.audio, "sfx"),
        draft_mod.TrackSpec(draft_mod.TrackType.video, "main"),
        draft_mod.TrackSpec(draft_mod.TrackType.text, "caption"),
    ])

    # ── audio 轨: 整段 TTS (无 manifest, 直接整段) ──
    audio_path = Path(audio_path)
    dur = float(_probe_duration(audio_path) or 0)
    if dur <= 0:
        raise ValueError("音频时长未知, 无法导出")
    script.add_segment(
        draft_mod.AudioSegment(str(audio_path), _trange_sec(0, dur)),
        "voice",
    )

    # ── video 轨: 各页静态帧/mp4 按对齐 start_sec 放轨, 静音 (声音归 voice 轨) ──
    # 2026-08-21 剪映分流: 每页 = 1 静态帧 PNG (photo 素材), 入场动画+转场由剪映给,
    # 替代逐帧捕获 (21页真实稿 3h → 秒级截图 + 剪映 GPU 导出).
    # 素材实际时长可能略短于分配时长 (ffmpeg 帧数向下取整) → 用 mat.duration 钳制,
    # 避免 source_timerange 超出素材时长报错 (2026-08-20).
    mat_cache: dict[str, draft_mod.VideoMaterial] = {}
    for idx, c in enumerate(valid_clips):
        p = Path(c["path"])
        mat = mat_cache.get(str(p))
        if mat is None:
            mat = draft_mod.VideoMaterial(str(p))
            mat_cache[str(p)] = mat
        start_us = int(round(float(c.get("start_sec", 0.0)) * _US))
        alloc_us = int(round(float(c.get("duration_sec", 5.0)) * _US))
        mat_us = int(mat.duration) if mat.duration else alloc_us
        use_us = min(alloc_us, mat_us) if mat_us > 0 else alloc_us
        seg = draft_mod.VideoSegment(
            mat, trange(start_us, max(use_us, 100000)), volume=0,
        )
        # 入场动画: 整页渐显 (母本/知识付费稿标配); 首页不加转场
        if _JY_PPT_ENTRANCE is not None:
            seg.add_animation(_JY_PPT_ENTRANCE)
        if idx > 0 and _JY_PPT_TRANSITION is not None:
            seg.add_transition(_JY_PPT_TRANSITION)
        script.add_segment(seg, "main")

    # ── text 轨: 每页台词作字幕 (对齐该页窗口) ──
    n_text = 0
    for c in valid_clips:
        notes = (c.get("notes") or "").strip()
        if not notes:
            continue
        # 洗 TTS 读法 → 阅读文本; 超长断句 (横屏上限 30 字)
        washed = wash_subtitle_text(notes)
        chunks = split_subtitle(washed, 30)
        start_us = int(round(float(c.get("start_sec", 0.0)) * _US))
        dur_us = int(round(float(c.get("duration_sec", 5.0)) * _US))
        total_len = max(len(washed), 1)
        alloc = [dur_us * len(ch) // total_len for ch in chunks]
        alloc[-1] = dur_us - sum(alloc[:-1]) if alloc else dur_us
        seg_start = start_us
        for chunk, chunk_us in zip(chunks, alloc):
            try:
                seg = TextSegment(
                    chunk, trange(seg_start, max(chunk_us, 1000)),
                    clip_settings=ClipSettings(transform_y=-0.75),
                )
                script.add_segment(seg, "caption")
                n_text += 1
            except Exception as exc:
                logger.warning("[jy_export] PPT 字幕段失败: %s | %s", chunk[:20], exc)
            seg_start += chunk_us

    script.save()
    draft_dir = _drafts_dir() / name
    result = {
        "draft_name": name,
        "draft_dir": str(draft_dir),
        "canvas": f"{width}x{height}",
        "video_segments": len(valid_clips),
        "audio_segments": 1,
        "text_segments": n_text,
        "audio_mode": "整段 TTS",
        "skipped_slots": [],
        "exported_at": datetime.now().isoformat(timespec="seconds"),
    }
    logger.info("[jy_export] PPT %s -> %s (%s)", job_id, name, result)
    return result


# ── 元素级 PPT 草稿 (2026-08-21 整体复刻 + 逐级显示) ──────────────────────────
# 每页 = 1 base 层 (背景+装饰, 无动画) + 逐元素透明 PNG 层 (文字/前景图).
# 每元素独立 video 轨, 按角色序错峰渐显入场. base 轨页间加转场.
_ROLE_PRIORITY = {"title": 0, "subtitle": 1, "emphasis": 1.5,
                  "body": 2, "caption": 3, "other": 4}
_ELEMENT_ENTRANCE = draft_mod.IntroType.渐显
_BASE_TRANSITION = draft_mod.TransitionType.上移
# 句子停顿加权: 每句结束后额外停顿时长 (秒), 模拟 TTS 换气停顿
_SENT_PAUSE = 0.35
# 动效完成后的静止阅读窗口: 所有元素最晚入场 ≤ 页末 - 此值
_READ_WINDOW = 5.0
# 首帧免责字幕最小停留时长 (豆包统一约束: 右上角常驻≥20秒)
_MIN_DISCLAIMER_SEC = 20.0
def _jy_font(resource_id: str):
    """自定义剪映字体 (pyJianYingDraft FontType 枚举没有的, 如思源黑体 ID 6740439840254333443)."""
    _meta = type("FM", (), {"resource_id": resource_id})()
    return type("CF", (), {"value": _meta})()


# 剪映商用字体 (2026-08-21): pyJianYingDraft FontType 覆盖 797 个剪映授权字体, 配置化可随时换
_JY_FONT_BADGE = draft_mod.FontType.孤月体       # 系列角标 (2026-08-22 用户定稿: 孤月体/5/70%)
_JY_FONT_CAPTION = draft_mod.FontType.孤月体      # 台词字幕 (2026-08-21 用户定稿)
_JY_FONT_DISCLAIMER = draft_mod.FontType.孤月体   # 免责 (2026-08-22 用户定稿: 孤月体/5/70%)

# 字幕样式 (2026-08-21 用户定稿): 孤月体 / 字号5 / 奶油色 #F9F3C4 / 居中
_SUBTITLE_COLOR = (0.976, 0.953, 0.769)  # #F9F3C4
_SUBTITLE_ALIGN = 1  # 0=左 1=中 2=右
# 口播字幕位置 (2026-08-21 v3): 以 director 页【导出剪映草稿】的位置为准 —
#   transform_y=-0.75 (与 export_job_draft 一致, 用户认可该底部字幕位)。
#   v2 曾按错误符号推断改 +0.477 → 字幕跑屏顶; 本版以 director 实测值定稿。
_CAPTION_TRANSFORM_Y = -0.75
# 免责: 剪映面板读数(498, 961) 右上 → transform = 读数/画布全尺寸(1920, 1080)
# = (0.259, 0.890)。2026-08-22 v2: 此前误除剪映显示面板尺寸(2474×1958),
# 读数仍按 transform×画布(1920,1080) 显示 → 免责跑偏到(386,530)。实测校准:
# transform(0.201,0.491) → 剪映读数(386,530) = transform×(1920,1080)。
_DISCLAIMER_TRANSFORM = (0.259, 0.890)
# 角标: 剪映面板读数(-961, 961) 左上 → transform = (-961/1920, 961/1080)=(-0.501, 0.890)
_BADGE_TRANSFORM = (-0.501, 0.890)
# 免责/角标缩放 (2026-08-22 用户定稿: 剪映缩放 70%)
_BADGE_SCALE = 0.7
_DISCLAIMER_SCALE = 0.7

# 白字可读性机制 (2026-08-21): 字幕/角标/免责是白字, 白底页面会看不见 →
# 加深色描边 + 阴影, 任何底色都清晰. 描边/阴影可独立调.
_CAPTION_BORDER = draft_mod.TextBorder(alpha=0.85, color=(0.0, 0.0, 0.0), width=12)
_CAPTION_SHADOW = draft_mod.TextShadow(alpha=0.55, color=(0.0, 0.0, 0.0), diffuse=12, distance=3)
_BADGE_BORDER = draft_mod.TextBorder(alpha=0.80, color=(0.0, 0.0, 0.0), width=10)
_BADGE_SHADOW = draft_mod.TextShadow(alpha=0.50, color=(0.0, 0.0, 0.0), diffuse=10, distance=3)
_DISCLAIMER_BORDER = draft_mod.TextBorder(alpha=0.60, color=(0.0, 0.0, 0.0), width=8)


def _safe_deadline(page_dur: float) -> float:
    """元素最晚入场时刻: 长页留 5s 阅读窗; 短页至少留 0.5s 且不超页长."""
    return max(0.5, min(page_dur - _READ_WINDOW, page_dur - 0.5))


def split_narration(text: str) -> list[str]:
    """口播稿按句切分 (中文句末标点 .!?。！？;； 及换行)."""
    import re as _re
    text = (text or "").strip()
    if not text:
        return []
    parts = _re.split(r"(?<=[。！？；.!?])\s*|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _char_weight(sent: str) -> float:
    """句子权重: 字符数 (标点略降权)."""
    return sum(0.5 if c in "，、：；。！？,.!?;: " else 1.0 for c in sent)


def _match_score(el_text: str, sent: str) -> float:
    """元素文本 ↔ 口播句 匹配分.

    子串出现 → 1.0 (逐字吻合); 否则最长公共子串占比 (连续才算, 防短句
    靠共同常用字假阳性, 如 '其实是小麦驯化了我们' 与 '咱们...小麦的手下败将').
    """
    el = (el_text or "").strip()
    if not el:
        return 0.0
    if el in sent:
        return 1.0
    import difflib
    m = difflib.SequenceMatcher(None, el, sent).find_longest_match(0, len(el), 0, len(sent))
    return m.size / max(1, len(el))


def compute_element_timing(
    narration: str,
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
    group_gap: float = 0.25,
    match_threshold: float = 0.6,
) -> list[dict]:
    """按口播稿时序分配每个元素的入场时刻 (2026-08-21 v3).

    近似法 (TTS 合成音语速稳定, 无需 whisper): 口播按句切分, 每句时长
    ∝ 字符权重 + 停顿加权, 累计得句窗口.
    - 高置信匹配 (覆盖率≥0.6): 元素在该句说到时入场, 且**句内偏移**
      (元素文本在句中的位置 → 精确到该句内部时刻, 而非句首).
      同句多元素按角色序微错峰 0.25s.
    - 未匹配元素 (屏上文字与口播不逐字吻合): 补到已匹配之后的
      空闲句窗口, 保持逐级显示且不跳到已播内容之前.
    """
    sents = split_narration(narration)
    elems = [l for l in layers if l["kind"] != "base"]
    if not sents or page_dur <= 0 or not elems:
        return []
    # 句窗口 (字符权重比例 + 句尾停顿)
    weights = [_char_weight(s) + _SENT_PAUSE for s in sents]
    total_w = sum(weights)
    acc = first_delay
    sent_wins = []
    for i, w in enumerate(weights):
        sent_wins.append({"idx": i, "start": acc, "dur": page_dur * w / total_w})
        acc += page_dur * w / total_w
    sent_wins.sort(key=lambda x: x["start"])

    # 角色序 (title 优先占句)
    elems.sort(key=lambda l: (_ROLE_PRIORITY.get(l.get("role", "other"), 4), l.get("order", 0)))
    assigned: dict[int, float] = {}
    group_count: dict[int, int] = {}
    last_assign = first_delay

    # Phase 1: 高置信匹配 (同句最多 2 元素成组微错峰 — 标题副题常一口气说出)
    for ei, l in enumerate(elems):
        if l["kind"] != "text" or not l.get("text"):
            continue
        cand = [(w["idx"], _match_score(l["text"], sents[w["idx"]])) for w in sent_wins]
        cand.sort(key=lambda x: -x[1])
        for si, score in cand:
            if score < match_threshold:
                break
            if group_count.get(si, 0) >= 2:
                continue
            group_count[si] = group_count.get(si, 0) + 1
            win = next(w for w in sent_wins if w["idx"] == si)
            pos = sents[si].find(l["text"][:6]) if len(l["text"]) >= 2 else 0
            rel = max(0.0, pos) / max(1, len(sents[si]))
            t = win["start"] + win["dur"] * rel + (group_count[si] - 1) * group_gap
            assigned[ei] = t
            last_assign = max(last_assign, t)
            break

    # 动效完成窗口: 所有元素最晚入场 ≤ 页长安全线 (长页留 5s 阅读, 短页不超页长)
    safe_deadline = _safe_deadline(page_dur)

    # Phase 2: 未匹配 → 均匀铺满 [first_delay, safe_deadline]
    # 消除"尾部密集 + 前段空白": 未匹配元素按阅读序均布, 不与口播吻合元素争位
    # (不同轨共存, 时间可穿插, 无冲突).
    unmatched = [ei for ei in range(len(elems)) if ei not in assigned]
    if unmatched:
        n_u = len(unmatched)
        span = max(0.5, safe_deadline - first_delay)
        for j, ei in enumerate(unmatched):
            assigned[ei] = first_delay + (j + 1) * span / (n_u + 1)

    # 全局钳制: 匹配元素若落在安全窗内/后, 一并压到 safe_deadline
    for ei in assigned:
        if assigned[ei] > safe_deadline:
            assigned[ei] = safe_deadline

    out: list[dict] = []
    for ei, l in enumerate(elems):
        rel = min(assigned.get(ei, safe_deadline), safe_deadline)
        out.append({**l, "start_sec": round(page_start + rel, 3)})
    return out


def _build_caption_track(
    script: Any,
    pages: list[dict],
    width: int,
    height: int,
) -> dict[str, int]:
    """元素草稿字幕轨 (2026-08-21): 每页口播稿 → 底部字幕, 复用 R9 v3.

    逐页 narration 洗读法 → 断句 (横屏≤30字) → 时长按字数比例分到页窗口 →
    每条: 内联划重点(金/红) + TextIntro 动效 + 同帧音效 (与 director 草稿一致).
    """
    stats = {"emphasis": 0, "sfx": 0, "sfx_missing": 0, "sfx_density_skip": 0,
             "anim": 0, "caption_suppressed": 0}
    _last_sfx = [None]
    _first_caption = [True]
    n_text = 0
    max_chars = 18 if height > width else 30

    for pg in pages:
        narration = (pg.get("narration") or "").strip()
        start_sec = float(pg["start_sec"])
        dur_sec = float(pg["duration_sec"])
        if not narration or dur_sec <= 0:
            continue
        washed = wash_subtitle_text(narration)
        chunks = split_subtitle(washed, max_chars)
        total_len = max(len(washed), 1)
        seg_start_us = int(round(start_sec * _US))
        seg_dur_us = int(round(dur_sec * _US))
        alloc = [seg_dur_us * len(c) // total_len for c in chunks]
        alloc[-1] = seg_dur_us - sum(alloc[:-1])
        for chunk, chunk_us in zip(chunks, alloc):
            gold, red, anim, anim_ms = _auto_choreograph(
                script, chunk, seg_start_us, stats, _last_sfx, first=_first_caption[0])
            _first_caption[0] = False
            hl = sorted(set(gold + find_highlight_ranges(chunk)))
            rr = sorted(set(red))
            try:
                seg = _StyledTextSegment(
                    chunk,
                    trange(seg_start_us, max(chunk_us, 1000)),
                    font=_JY_FONT_CAPTION,
                    border=_CAPTION_BORDER,
                    shadow=_CAPTION_SHADOW,
                    highlight_ranges=hl,
                    red_ranges=rr,
                    clip_settings=ClipSettings(transform_y=_CAPTION_TRANSFORM_Y),
                )
                if anim:
                    seg.add_animation(getattr(TextIntro, anim),
                                      duration=anim_ms * 1000 if anim_ms else None)
                    stats["anim"] += 1
                script.add_segment(seg, "caption")
                n_text += 1
            except Exception as exc:
                logger.warning("[jy_export] 元素稿字幕段失败: %s | %s", chunk[:20], exc)
            seg_start_us += chunk_us
    return {"text": n_text, "sfx": stats["sfx"], "emphasis": stats["emphasis"]}


def _content_columns(layers: list[dict], height_emu: float = 6858000) -> int:
    """内容带列数 (结构化判定): 剔除页头/页脚后按 left 聚类得几列."""
    _, body, _ = _split_bands(layers, height_emu)
    cols: list[list] = []
    for l in sorted(body, key=lambda x: float(x.get("left", 0))):
        if cols and abs(float(l.get("left", 0)) - float(cols[-1][0].get("left", 0))) <= 320000:
            cols[-1].append(l)
        else:
            cols.append([l])
    return len(cols)


def _split_bands(
    elems: list[dict], height_emu: float = 6858000,
) -> tuple[list[dict], list[dict], list[dict]]:
    """按纵向位置分带: (页头 top<12%, 内容带, 页脚 top>85%)."""
    header, body, footer = [], [], []
    for l in elems:
        tr = float(l.get("top", 0)) / height_emu if height_emu else 0
        if tr < 0.12:
            header.append(l)
        elif tr > 0.85:
            footer.append(l)
        else:
            body.append(l)
    return header, body, footer


def _group_into_blocks(
    elems: list[dict],
    height_emu: float = 6858000,
    left_tol: float = 320000,
) -> list[list[dict]]:
    """按 PPT 版式把元素聚成信息块 (2026-08-21).

    - 页头 (top<12%高) → 独立块, 先显示
    - 页脚 (top>85%高) → 独立块, 后显示
    - 内容带按 left 聚类成列 (块): 三栏 PPT 的 01/02/03 各占一列
    - 图片随其列; 独立图作单块
    返回块列表, 每块内元素无序 (排序由调用方).
    """
    header, body, footer = _split_bands(elems, height_emu)
    cols: list[list[dict]] = []
    for l in sorted(body, key=lambda x: float(x.get("left", 0))):
        if cols and abs(float(l.get("left", 0)) - float(cols[-1][0].get("left", 0))) <= left_tol:
            cols[-1].append(l)
        else:
            cols.append([l])
    blocks: list[list[dict]] = []
    if header:
        blocks.append(header)
    blocks.extend(cols)
    if footer:
        blocks.append(footer)
    return blocks


def _grid_anchors(elems: list[dict], height_emu: float = 6858000) -> list[dict]:
    """宫格锚点候选 (2026-08-21): 数字标记(01/02/03) 或 短粗体标题(≥14pt≤20字),
    排除页头带. 返回锚点列表 (须再经行聚类判定是否真为宫格)."""
    import re as _re
    anchors = []
    for l in elems:
        if l["kind"] != "text":
            continue
        tr = float(l.get("top", 0)) / height_emu if height_emu else 0
        if tr < 0.12:
            continue
        text = (l.get("text") or "").strip()
        if not text:
            continue
        is_num = bool(_re.match(r"^\d{1,2}$", text))
        pt = float(l.get("pt") or 0)
        is_title = bool(l.get("bold")) and pt >= 14 and len(text) <= 20
        if is_num or is_title:
            anchors.append(l)
    return anchors


def _detect_grid_anchors(elems: list[dict], height_emu: float = 6858000) -> list[dict] | None:
    """宫格判定: 锚点按行聚类 (top 差≤600000 EMU), 任一行≥2 锚 → 宫格.

    优先数字标记(01), 其次短粗体标题. 返回最终锚点集; 非宫格返回 None.
    """
    anchors = _grid_anchors(elems, height_emu)
    if len(anchors) < 2:
        return None
    num_markers = [a for a in anchors if (a.get("text") or "").strip().isdigit()]
    pool = num_markers if len(num_markers) >= 2 else anchors
    pool_sorted = sorted(pool, key=lambda l: float(l.get("top", 0)))
    rows: list[list[dict]] = []
    for a in pool_sorted:
        if rows and abs(float(a.get("top", 0)) - float(rows[-1][0].get("top", 0))) <= 600000:
            rows[-1].append(a)
        else:
            rows.append([a])
    if any(len(r) >= 2 for r in rows):
        return pool
    return None


def _dist2(a: dict, b: dict) -> float:
    return (float(a.get("left", 0)) - float(b.get("left", 0))) ** 2 + \
           (float(a.get("top", 0)) - float(b.get("top", 0))) ** 2


def compute_cell_timing(
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
) -> list[dict] | None:
    """宫格布局逐格显示 (2026-08-21): 每格 图+标题同现 → 正文, 格按行优先.

    非宫格返回 None (调用方回退块级/口播). 页头先出, 页脚/游离元素后置.
    """
    elems = [l for l in layers if l["kind"] != "base"]
    anchors = _detect_grid_anchors(elems)
    if anchors is None:
        return None
    safe = _safe_deadline(page_dur)
    anchor_ids = {id(a) for a in anchors}

    # 非锚元素 → 最近锚点 (内容格); 游离元素(远)单独成块
    cells: dict[int, list[dict]] = {id(a): [a] for a in anchors}
    loose: list[dict] = []
    for l in elems:
        if id(l) in anchor_ids:
            continue
        tr = float(l.get("top", 0)) / 6858000
        if tr < 0.12 or tr > 0.85:  # 页头/页脚不入格、不入 loose (单独组)
            continue
        best = min(anchors, key=lambda a: _dist2(a, l))
        if _dist2(best, l) > (1.2e6) ** 2:  # 距锚点过远 → 游离
            loose.append(l)
        else:
            cells[id(best)].append(l)

    # 宫格语义只在"格内有图"(图+标题同现)时有意义; 纯文字列块(如 01/02/03
    # 三栏)回退给块级编排 — 否则 P3 这类会被错拆.
    if not any(any(l["kind"] == "image" for l in c) for c in cells.values()):
        return None

    # 行优先序
    ordered_cells: list[list[dict]] = []
    anchors_sorted = sorted(anchors, key=lambda a: float(a.get("top", 0)))
    rows: list[list[dict]] = []
    for a in anchors_sorted:
        if rows and abs(float(a.get("top", 0)) - float(rows[-1][0].get("top", 0))) <= 600000:
            rows[-1].append(a)
        else:
            rows.append([a])
    for row in sorted(rows, key=lambda r: float(r[0].get("top", 0))):
        for a in sorted(row, key=lambda x: float(x.get("left", 0))):
            ordered_cells.append(cells[id(a)])

    # 时序: 页头 → 宫格 → 游离(位置序) → 页脚
    header = sorted([l for l in elems if float(l.get("top", 0)) / 6858000 < 0.12],
                    key=lambda l: float(l.get("top", 0)))
    footer = sorted([l for l in elems if float(l.get("top", 0)) / 6858000 > 0.85],
                    key=lambda l: float(l.get("top", 0)))
    groups: list[list[dict]] = []
    if header:
        groups.append(header)
    groups.extend(ordered_cells)
    if loose:
        groups.append(sorted(loose, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0)))))
    if footer:
        groups.append(footer)

    total = sum(len(g) for g in groups)
    span = max(0.5, safe - first_delay)
    cursor = first_delay
    out: list[dict] = []
    for g in groups:
        n = max(len(g), 1)
        g_span = span * n / total
        has_img = any(l["kind"] == "image" for l in g)
        # 格内序: 有图 → 图+锚同现后正文; 无图 → 顶部序
        if len(anchors) == 1 and has_img:
            seq = [l for l in g if l["kind"] != "body"] + [l for l in g if l["kind"] == "body"]
        else:
            seq = sorted(g, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0))))
        if has_img:
            # 图+标题同现: 同时间戳
            img = [l for l in seq if l["kind"] == "image"]
            tit = [l for l in seq if l["kind"] == "text" and id(l) in anchor_ids]
            body = [l for l in seq if l["kind"] == "text" and id(l) not in anchor_ids]
            steps = []
            if img or tit:
                steps.append(img + tit)  # 同现
            steps.extend([[b] for b in body])
            # 展开: 同现组内同 start
            group_times: list[tuple[float, list[dict]]] = []
            t_cursor = cursor
            for st in steps:
                group_times.append((t_cursor, st))
                t_cursor += g_span / max(1, len(steps))
            for t, st in group_times:
                for l in st:
                    out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        else:
            for i, l in enumerate(seq):
                t = cursor + i * g_span / n
                out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        cursor += g_span
    return out


def compute_block_timing(
    layers: list[dict],
    page_start: float,
    page_dur: float,
    *,
    first_delay: float = 0.5,
    within_gap: float = 0.3,
) -> list[dict]:
    """按信息块逐级显示 (2026-08-21): 页头 → 列块(左→右) → 页脚.

    每块一个时间片 (按元素数比例分配), 块内元素 top→bottom 错峰.
    全局保证: 最晚入场 ≤ 页长 - 5 (留 5s 静止阅读). 确定性, 不依赖口播匹配
    (块序是版式语义, 三栏稿口播常一次提及所有块).
    """
    elems = [l for l in layers if l["kind"] != "base"]
    if not elems:
        return []
    safe = _safe_deadline(page_dur)
    blocks = _group_into_blocks(elems)
    total = sum(len(b) for b in blocks)
    span = max(0.5, safe - first_delay)
    cursor = first_delay
    out: list[dict] = []
    for block in blocks:
        n = len(block)
        block_span = span * n / total
        block_elems = sorted(block, key=lambda l: (float(l.get("top", 0)), float(l.get("left", 0))))
        for i, l in enumerate(block_elems):
            t = cursor + (i * block_span / max(1, n))
            out.append({**l, "start_sec": round(page_start + min(t, safe), 3)})
        cursor += block_span
    return out


def compute_page_timing(
    layers: list[dict],
    narration: str,
    page_start: float,
    page_dur: float,
) -> list[dict]:
    """统一入场编排 (2026-08-21):
    - 宫格布局 (数字标记/短粗体标题形成≥2格) → 逐格: 图+标题同现→正文
    - 结构化页 (内容带 ≥2 列, 如三栏信息块稿) → 块级逐级 (页头→列→页脚)
    - 单列/简单页 → 口播匹配 (标题随口播说到时入场)
    """
    cell = compute_cell_timing(layers, page_start, page_dur)
    if cell is not None:
        return cell
    if _content_columns(layers) >= 2:
        return compute_block_timing(layers, page_start, page_dur)
    timed = compute_element_timing(narration, layers, page_start, page_dur)
    if timed:
        return timed
    return compute_block_timing(layers, page_start, page_dur)  # 空口播兜底


def _add_disclaimer(script: Any, pages: list[dict], disclaimer_text: str) -> int:
    """首帧免责字幕 (2026-08-21): 口播不念, 画面右上角小字, 停留≥20秒 (豆包统一约束).

    字号比字幕(_SUBTITLE_SIZE=5)小两号 (~2.8), 白字半透明, 右上角.
    时长 = max(第一页时长, 20s) — 第一页过短时延续到第二页.
    """
    if not pages or not disclaimer_text:
        return 0
    p1 = pages[0]
    start_us = int(round(float(p1["start_sec"]) * _US))
    dur_us = int(round(max(float(p1["duration_sec"]), _MIN_DISCLAIMER_SEC) * _US))
    try:
        seg = draft_mod.TextSegment(
            disclaimer_text,
            trange(start_us, max(dur_us, 1000)),
            font=_JY_FONT_DISCLAIMER,
            border=_DISCLAIMER_BORDER,
            style=draft_mod.TextStyle(size=5.0, color=(1.0, 1.0, 1.0), alpha=0.85),
            clip_settings=ClipSettings(
                transform_x=_DISCLAIMER_TRANSFORM[0], transform_y=_DISCLAIMER_TRANSFORM[1],
                scale_x=_DISCLAIMER_SCALE, scale_y=_DISCLAIMER_SCALE,
            ),
        )
        script.add_segment(seg, "disclaimer")  # 独立轨, 防与底部字幕同轨重叠
        return 1
    except Exception as exc:
        logger.warning("[jy_export] 首帧免责字幕失败: %s", exc)
        return 0


def _add_series_badge(script: Any, pages: list[dict], badge_text: str, page_indices: list[int]) -> int:
    """系列角标 (2026-08-21): 左上角, '静姐读书:《书名》第X集，更多请主页观看'.

    在指定页(第2页/末页)全程亮起, 字号=字幕(_SUBTITLE_SIZE=5), 呼吸闪烁(闪烁 循环动画).
    """
    if not badge_text or not pages:
        return 0
    n = 0
    for pi in page_indices:
        if pi < 0 or pi >= len(pages):
            continue
        pg = pages[pi]
        start_us = int(round(float(pg["start_sec"]) * _US))
        dur_us = int(round(float(pg["duration_sec"]) * _US))
        try:
            seg = draft_mod.TextSegment(
                badge_text,
                trange(start_us, max(dur_us, 1000)),
                font=_JY_FONT_BADGE,
                border=_BADGE_BORDER,
                shadow=_BADGE_SHADOW,
                style=draft_mod.TextStyle(size=_SUBTITLE_SIZE, color=(1.0, 1.0, 1.0), alpha=0.95),
                clip_settings=ClipSettings(
                    transform_x=_BADGE_TRANSFORM[0], transform_y=_BADGE_TRANSFORM[1],  # 左上角
                    scale_x=_BADGE_SCALE, scale_y=_BADGE_SCALE,
                ),
            )
            seg.add_animation(draft_mod.TextLoopAnim.闪烁)  # 呼吸闪烁
            script.add_segment(seg, "badge")
            n += 1
        except Exception as exc:
            logger.warning("[jy_export] 系列角标失败: %s", exc)
    return n


def export_element_draft(
    draft_name: str,
    pages: list[dict],
    audio_path: str | Path | None = None,
    *,
    canvas: tuple[int, int] = (1920, 1080),
    stagger: float = 0.30,
    disclaimer: str | None = None,
    book_title: str | None = None,
    ep_index: int | None = None,
) -> dict[str, Any]:
    """元素级剪映草稿: 每页 base 层 + 逐元素透明层, 各自 video 轨, 渐显错峰.

    pages: [{
        start_sec: float, duration_sec: float,
        layers: [ {kind: 'base'|'text'|'image', file: str, text?: str, role?: str} ]
    }]
    - base 层 → 'main' 轨 (无入场动画), 页间 上移 转场
    - text/image 层 → e0..eK 轨, 按角色序错峰, 渐显入场 (全画布透明层, 动画安全)
    - 轨道按全稿最大元素数建, 跨页复用 (时序不重叠)
    """
    width, height = canvas
    folder = draft_mod.DraftFolder(str(_drafts_dir()))
    script = folder.create_draft(draft_name, width, height, allow_replace=True)

    # 轨道: voice/sfx 底, main(base) 中, e0..eK 元素, caption 最上 (后来居上)
    max_elements = max((len([l for l in pg.get("layers", []) if l["kind"] != "base"]) for pg in pages), default=0)
    track_specs = [draft_mod.TrackSpec(draft_mod.TrackType.audio, "voice"),
                   draft_mod.TrackSpec(draft_mod.TrackType.audio, "sfx"),
                   draft_mod.TrackSpec(draft_mod.TrackType.video, "main")]
    track_specs += [draft_mod.TrackSpec(draft_mod.TrackType.video, f"e{i}") for i in range(max_elements)]
    track_specs.append(draft_mod.TrackSpec(draft_mod.TrackType.text, "caption"))
    track_specs.append(draft_mod.TrackSpec(draft_mod.TrackType.text, "badge"))  # 系列角标(左上角)
    track_specs.append(draft_mod.TrackSpec(draft_mod.TrackType.text, "disclaimer"))  # 免责(右上角, 独立轨防与字幕重叠)
    script.append_tracks(track_specs)

    # audio 轨: 整段 TTS (若顶层给 audio_path), 或逐页 audio_file 段
    if audio_path and Path(audio_path).exists():
        dur = float(_probe_duration(audio_path) or 0)
        if dur > 0:
            script.add_segment(draft_mod.AudioSegment(str(audio_path), _trange_sec(0, dur)), "voice")

    mat_cache: dict[str, draft_mod.VideoMaterial] = {}
    n_base = n_elem = 0
    n_audio = 0

    def _photo(file: str) -> draft_mod.VideoMaterial:
        m = mat_cache.get(file)
        if m is None:
            m = draft_mod.VideoMaterial(file)
            mat_cache[file] = m
        return m

    for pg in pages:
        start_us = int(round(float(pg["start_sec"]) * _US))
        dur_us = int(round(float(pg["duration_sec"]) * _US))
        layers = pg.get("layers", [])

        # 逐页音频段 (如有) → voice 轨
        pg_audio = pg.get("audio_file")
        if pg_audio and Path(pg_audio).exists():
            a_dur = float(_probe_duration(pg_audio) or 0)
            if a_dur > 0:
                # 2026-08-22: 实测 a_dur 与 timings 窗口微差 (采样率/舍入) 逐页累积,
                # 靠后的页 a_dur 超出本页窗口 → 与下一段重叠 → 草稿导出崩
                # (SegmentOverlap)。段长钳制到本页窗口 min(a_dur, dur_us), 绝不重叠。
                seg_us = min(int(round(a_dur * _US)), dur_us)
                if seg_us >= 100000:  # ≥0.1s 才放 (防 0 时长段)
                    script.add_segment(
                        draft_mod.AudioSegment(str(pg_audio), trange(start_us, seg_us)),
                        "voice")
                    n_audio += 1

        # base 层 → main 轨
        base_layer = next((l for l in layers if l["kind"] == "base"), None)
        if base_layer:
            mat = _photo(base_layer["file"])
            seg = draft_mod.VideoSegment(mat, trange(start_us, dur_us), volume=0)
            if n_base > 0 and _BASE_TRANSITION is not None:
                seg.add_transition(_BASE_TRANSITION)
            script.add_segment(seg, "main")
            n_base += 1

        # 元素层 → e0..eK: 有口播时序(start_sec)用之, 否则按角色序错峰
        elems = [l for l in layers if l["kind"] != "base"]
        elems.sort(key=lambda l: (l.get("start_sec", 1e9), _ROLE_PRIORITY.get(l.get("role", "other"), 4), l.get("order", 0)))
        page_dur_s = max(1.5, float(pg["duration_sec"]))
        n = max(len(elems), 1)
        step = min(stagger, page_dur_s / (n + 1.5))  # 自适应: 页短时压缩错峰
        for idx, l in enumerate(elems):
            if l.get("start_sec") is not None:
                delay_us = int(round(max(0.0, float(l["start_sec"]) - pg["start_sec"]) * _US))
            else:
                delay_us = int(round(idx * step * _US))
            remain_us = dur_us - delay_us
            if remain_us < 200000:  # 至少留 0.2s 动画窗口
                break
            mat = _photo(l["file"])
            seg = draft_mod.VideoSegment(
                mat, trange(start_us + delay_us, max(remain_us, 200000)), volume=0)
            if _ELEMENT_ENTRANCE is not None:
                seg.add_animation(_ELEMENT_ENTRANCE)
            script.add_segment(seg, f"e{idx}")
            n_elem += 1

    # 字幕轨 (每页口播稿, R9 v3 动态字幕 + 同帧音效)
    cap_stats = _build_caption_track(script, pages, width, height)
    # 首帧免责字幕 (视觉化, 口播不念)
    n_disclaimer = 0
    if disclaimer:
        n_disclaimer = _add_disclaimer(script, pages, disclaimer)
    # 系列角标 (左上角, 第2页+末页, 呼吸闪烁)
    n_badge = 0
    if book_title:
        badge_text = f"静姐读书：《{book_title}》第{ep_index or '?'}集，更多请主页观看。"
        if len(pages) > 2:
            n_badge = _add_series_badge(script, pages, badge_text, [1, len(pages) - 1])
        elif pages:
            n_badge = _add_series_badge(script, pages, badge_text, [0])

    script.save()
    draft_dir = _drafts_dir() / draft_name
    result = {
        "draft_name": draft_name,
        "draft_dir": str(draft_dir),
        "canvas": f"{width}x{height}",
        "base_segments": n_base,
        "element_segments": n_elem,
        "audio_segments": n_audio,
        "caption_segments": cap_stats["text"],
        "sfx_segments": cap_stats["sfx"],
        "disclaimer": n_disclaimer,
        "series_badge": n_badge,
        "emphasis_words": cap_stats["emphasis"],
        "max_tracks": 4 + max_elements,
        "audio": bool(audio_path),
        "exported_at": datetime.now().isoformat(timespec="seconds"),
    }
    logger.info("[jy_export] 元素级草稿 %s -> %s (base=%d elem=%d caption=%d sfx=%d tracks=%d)",
                draft_name, draft_dir, n_base, n_elem, cap_stats["text"], cap_stats["sfx"],
                4 + max_elements)
    return result


# ── R9 自动编排 (2026-08-17): 分类→同帧语义音效 + 内联划重点(金/红) + 密度规则 ──
# 知识来源: 45期协同三件套 / 音效语义库(用户标注) / 密度规则(用户口径) — 全确定性, 无 LLM
# 视觉强调 v2: 砍掉独立强调轨, 改为字幕行内双色划重点 (解决与字幕/HF卡重合+截断)

# 金额语境词 (数字+语境 → money 族; 纯数字/专名 → punchline 叮族; 问句 → 悬疑族)
_MONEY_CTX = ("万", "亿", "元", "美元", "收入", "赚", "营收", "薪", "融资", "估值",
              "利润", "市值", "ARR", "GMV", "价格", "涨价", "降价", "关税", "成本")
_SFX_FAMILY = {
    "money": ("金币到账叮咚声", "叮", "综艺叮~~"),
    "punchline": ("叮", "综艺叮~~"),
    "suspense": ("诡异的滴水声", "紧张转场音效"),
}


def _suspense_core(chunk: str) -> str | None:
    """问句强调短语 (2026-08-26 v2): 疑问代词锚定 + 虚指兜底, 代替旧"剥疑问词取前14字"。

    旧规则把"是什么样的/怎么办呢"这类纯虚指尾巴也整块放大 (用户实测选字不精细)。
    - 实体代词 (谁/多少/几/啥): 取代词前后各 ~3 字窗口 — "算在谁头上"/"记在谁头上"
    - 方式代词 (什么/怎么/为什么…): 取最后一个标点后、代词前的实义词段 (≤6 字),
      剥边缘虚词 — "我们被灌输的美军是什么样的"→"灌输的美军"; "伊朗为什么这么干"→"伊朗"
    - 兜底: 句中数字/专名 (find_highlight_ranges); 再无 → None 不放大 (宁缺毋滥)。
    """
    import re

    text = chunk.strip().rstrip("？?。！")
    last = None  # (start, end, kind) — 取结束最靠后者; 同结束取更长词 ("为什么"胜过其内嵌"什么")
    for q in ("为什么", "凭什么", "什么样", "怎么", "多少", "哪些", "哪个", "什么", "谁", "啥", "哪", "几"):
        for m in re.finditer(q, text):
            cand = (m.start(), m.end(), "entity" if q in ("谁", "多少", "几", "啥") else "manner")
            if last is None or (cand[1], -cand[0]) > (last[1], -last[0]):
                last = cand
    if last is None:
        rngs = find_highlight_ranges(text)
        if rngs:
            s, e = rngs[0]
            return text[s:e][:8]
        return None

    s, e, kind = last
    if kind == "entity":
        win = text[max(0, s - 4):min(len(text), e + 3)]  # 前4字: 覆盖"到底/究竟"整词剥除
        win = re.sub(r"[，。！？；、,]", "", win)
        win = re.sub(r"(?:到底|究竟|最后|还是|就是|了|的|地|得)+$", "", win)
        win = re.sub(r"^(?:到底|究竟|最后|还是|真的)+", "", win)
        if len(win) >= 2:
            return win[:8]
    # 方式代词: 代词前最后一个分句; 不足 2 字则回溯倒数第二个分句
    # ("咱们普通人，又凭什么该关心…" → 尾分句"又"剥空 → 回溯"普通人")
    head = text[:s]
    clauses = [c.strip() for c in re.split(r"[，。！？；、,]", head) if c.strip()]
    for seg in reversed(clauses[-2:] if len(clauses) >= 2 else clauses):
        seg = re.sub(r"(?:到底|究竟|最后|真的|还是|就是|要是|能|会|是|了|的|地|得|又|也|才)+$", "", seg)
        seg = re.sub(r"^(?:到底|究竟|最后|可是|但是|所以|而且|咱们|我们|他们|又|也|才)+", "", seg)
        if len(seg) > 6:
            seg = seg[-6:]
        if len(seg) >= 2:
            return seg
    # 兜底: 代词本身+后 1-3 实字 ("多少钱"/"谁头上"型)
    mm = re.match(r"((?:谁|什么|多少|几)[一-鿿]{1,3})", text[s:])
    if mm:
        return mm.group(1)
    rngs = find_highlight_ranges(text)
    if rngs:
        st, en = rngs[0]
        return text[st:en][:8]
    return None


def _classify_chunk(chunk: str) -> tuple[str, str | None]:
    """字幕块语义分类: (类别, 强调短语). 类别 ∈ money/punchline/suspense/plain.

    强调短语升级 (2026-08-17 用户反馈: 之前只抓裸关键词 AI/32/SK, 完全没有
    金句/反转/概念级长内容) — 按优先级提取:
      ① 引号内容 → 金句/概念 (整段引用)
      ② 反转/金句标记词所在分句 → 概念句 (≤16字)
      ③ 数字+语境单位 → 金额/数据短语 (如 "涨了34%""20亿美元", 非裸数字)
      ④ 问句 → 疑问核心短语
    """
    import re

    if re.search(r"[?？]$", chunk.strip()):
        core = _suspense_core(chunk)
        return "suspense", core

    # ① 引号金句/概念: 「...」 “...” "..." （TTS 读法稿里引号保留完整）
    m = re.search(r"[「“\"]([^「」”\"]{4,24})[」”\"]", chunk)
    if m:
        return "punchline", m.group(1)

    # ② 反转/金句标记词 → 所在分句 (金句的"肉"在标记词附近)
    for marker in ("其实", "根本", "真相", "意味着", "这就是", "关键在于",
                   "没想到", "说白了", "恰恰是", "最狠的", "最讽刺"):
        if marker in chunk:
            # 取含标记词的分句 (按标点切), 超长则取标记词前后共 14 字
            for clause in re.split(r"[，。！？；、]", chunk):
                if marker in clause and len(clause.strip()) >= 4:
                    c = clause.strip()
                    if len(c) > 16:
                        i = c.index(marker)
                        c = c[max(0, i - 4):i + 12]
                    return "punchline", c
    # ③ 数字短语: 数字 + 单位/语境 (非裸数字)
    m = re.search(
        r"([一-鿿]{0,5}?[\d.]+\s*[万亿]?(?:%|倍|美元|元|日元|欧元|年|个月|天|次|人|条|名)?)",
        chunk,
    )
    if m and re.search(r"\d", m.group(1)):
        phrase = m.group(1).strip()
        if len(phrase) >= 2 and any(w in chunk for w in _MONEY_CTX):
            return "money", phrase[:16]
        if len(phrase) >= 3:  # 有语境的数字才做强调, 裸短数字放过
            return "punchline", phrase[:16]

    # ④ 专名兜底 (latin ≥3 字符, 排除已剥标签后的短缩写滥用)
    ranges = find_highlight_ranges(chunk)
    for s, e in ranges:
        cand = chunk[s:e]
        if len(cand) >= 4 and re.fullmatch(r"[A-Za-z][A-Za-z0-9 .+-]*", cand):
            return "punchline", cand
    return "plain", None


def _auto_choreograph(script: Any, chunk: str, start_us: int,
                      stats: dict[str, int], last_sound_us: list[int],
                      first: bool = False) -> tuple[list, list, str | None, int | None]:
    """R9 v3: 每个字幕块 → 内联高亮 (金/红) + 动效动画 + 同帧音效.

    v3 (2026-08-18): 动效 = TextIntro 动画挂字幕段本身 (不加层, 零重合);
    动画与音效同一次决策同帧触发 — 音效优先取动画配对
    (jy_animation_sound_pairs), 库缺回退类别族 _SFX_FAMILY。
    首条可见字幕用卡拉OK (逐字点亮跟音频)。
    密度闸门管整个事件 (动画+音效): 前 30s 全类别, 之后仅非 plain 且间隔 ≥4s。
    Returns: (gold_ranges, red_ranges, anim_name, anim_ms)。
    """
    cat, kw = _classify_chunk(chunk)

    gold: list[tuple[int, int]] = []
    red: list[tuple[int, int]] = []
    if kw:
        idx = chunk.find(kw)
        if idx >= 0:
            rng = (idx, idx + len(kw))
            if cat == "suspense":
                red.append(rng)
            else:
                gold.append(rng)
            stats["emphasis"] += 1
        # 兜底: 分类词不在 chunk 里(改写后), 用 find_highlight_ranges 补数字/专名
        elif cat in ("money", "punchline"):
            gold.extend(find_highlight_ranges(chunk)[:1])

    # 动效决策: 首条可见字幕卡拉OK; 其余按类别; 动画名须为 TextIntro 合法枚举
    anim: str | None = None
    anim_ms: int | None = None
    if first:
        anim = "卡拉OK"
    elif cat in _CAT_ANIM:
        anim, anim_ms = _CAT_ANIM[cat]
    if anim is not None and not hasattr(TextIntro, anim):
        anim, anim_ms = None, None

    # 同帧音效 + 密度闸门 (闸门管整个事件: 动画+音效)
    if cat != "plain":
        if last_sound_us[0] is not None and start_us - last_sound_us[0] < 4_000_000 and start_us > 30_000_000:
            stats["sfx_density_skip"] += 1
            return gold, red, None, None
        # 音效: 动画配对优先, 回退类别族; 库内可用者轮换
        fam: list[str] = []
        if anim:
            fam += list(_ANIM_PAIRS.get(anim, {}).get("sounds", []))
        fam += list(_SFX_FAMILY[cat])
        avail = list(dict.fromkeys(s for s in fam if sound_path(s)))
        if avail:
            rot = stats.get(f"_rot_{cat}", 0)
            name = avail[rot % len(avail)]
            stats[f"_rot_{cat}"] = rot + 1
            if attach_sound(script, "sfx", name, start_us / _US, volume=0.9):
                stats["sfx"] += 1
                last_sound_us[0] = start_us
            else:
                stats["sfx_missing"] += 1
        else:
            stats["sfx_missing"] += 1
    return gold, red, anim, anim_ms


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
                 volume: float = 1.0, max_sec: float | None = None) -> bool:
    """往草稿音效轨挂一个音效. 缺文件时记日志返回 False (不阻塞导出).

    重叠防护 v2 (2026-08-25, 修 400 "New segment overlaps"): sfx 轨既有 HF
    转场音(whoosh) 又有字幕音效, 各自独立触发。v1 (ID-054) 只把新段结尾
    截到不越过既有段起点, 漏了"新起点落在既有段内部"(长 whoosh 跨入字幕
    音效帧) → pyJianYingDraft SegmentOverlap 400。v2 双向:
      1. 新起点落在既有段内部 → 整段跳过 (推迟挂载破坏同帧语义, 不如不放)
      2. 既有段起点落在新段内部 → 截断新段结尾 (v1 原逻辑)
    max_sec: 可选时长上限 (如 HF 边界音不超过其文字窗长度)。
    """
    p = sound_path(sound_name)
    if not p:
        logger.warning("[jy_export] 音效缺失, 跳过: %s", sound_name)
        return False
    dur = _probe_duration(p) or 1.0
    start_us = int(round(at_sec * _US))
    end_us = start_us + int(round(dur * _US))
    # 查目标轨已挂段: 双向重叠防护
    try:
        track = script.tracks[track_name]
        for seg in track.segments:
            s0 = seg.target_timerange.start
            if s0 <= start_us < seg.target_timerange.end:
                logger.info(
                    "[jy_export] 音效 %s 起点 %.2fs 落在既有段 [%d,%d] 内, 跳过",
                    sound_name, at_sec, s0, seg.target_timerange.end,
                )
                return False
            if start_us < s0 < end_us:
                end_us = s0
    except (KeyError, AttributeError):
        pass  # 轨道不存在/无法访问 → 保持原时长
    if max_sec is not None:
        end_us = min(end_us, start_us + int(round(max_sec * _US)))
    if end_us - start_us < 100_000:  # <0.1s 无意义, 跳过
        logger.info("[jy_export] 音效 %s 与已挂段重叠过密, 跳过 (%.2fs)", sound_name, at_sec)
        return False
    script.add_segment(
        draft_mod.AudioSegment(
            str(p), trange(start_us, end_us - start_us), volume=volume
        ),
        track_name,
    )
    return True

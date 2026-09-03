# -*- coding: utf-8 -*-
"""Evidence Image 线: 素材包真实证据图 → Ken Burns + 图源角标 mp4 (2026-09-04).

对应 _EXECUTION_PHASES 的 P 线 (与 broll_pexels 同 phase, 无 GPU)。
选图/池逻辑在 evidence_service (管线②); 本模块只管成片:

  池内段级匹配选图 → 缓存图校验/重下 → 单次 ffmpeg:
  等比缩放+黑边 (榜单截图不变形) → zoompan Ken Burns (1.0→1.08) →
  淡入淡出 → drawtext 图源角标 (右下, 半透明, 避开底部字幕区) →
  render_scale_pad 归一化 (补静音轨+30fps, 与 broll 族一致)。

失败语义: 池空/无匹配/图损坏 → RuntimeError → slot_executor 走
fallback 链降级 broll_pexels (导演闸门之外的执行期兜底)。
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.infrastructure import render_scale_pad, run_ffmpeg
from app.models import DirectorJob, DirectorSlot, Script
from app.schemas import get_video_format_spec
from app.services.evidence_service import (
    collect_evidence_pool,
    pick_image_for_slot,
    _download_image,
)
from app.services.slot_workflows.common import ensure_slot_dir

logger = logging.getLogger(__name__)

__all__ = ["execute_evidence_image_slot"]

# 图源角标字体: 微软雅黑优先 (Win11 必带), 黑体兜底
_FONT_CANDIDATES = (
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def _pick_font() -> str | None:
    for f in _FONT_CANDIDATES:
        if Path(f).exists():
            return f
    return None


def _drawtext_escape(text: str) -> str:
    """drawtext text= 转义 (过滤器层: 冒号/引号/反斜杠/百分号)."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _filter_fontfile(path: str) -> str:
    """Windows 盘符路径 → drawtext fontfile 过滤器参数 (C: 的冒号须转义)."""
    return path.replace("\\", "/").replace(":", "\\:")


def _collect_used_evidence_urls(db: Session, slot: DirectorSlot) -> set[str]:
    """同 job 已用证据图 URL (写回 params_json.image_url, 仿 _collect_used_pexels_ids).
    按 completed 过滤 + 排除自身, 不按 slot_index 收紧 (跨 phase 同款防护)."""
    rows = (
        db.query(DirectorSlot)
        .filter(
            DirectorSlot.director_job_id == slot.director_job_id,
            DirectorSlot.workflow == "evidence_image",
            DirectorSlot.status == "completed",
        )
        .all()
    )
    used: set[str] = set()
    for r in rows:
        if r.id == slot.id:
            continue
        url = (r.params_json or {}).get("image_url")
        if url:
            used.add(str(url))
    return used


def _build_vf(width: int, height: int, duration: float,
              source_media: str | None) -> str:
    """等比缩放+pad → Ken Burns → fade → 图源角标 (单 pass, 无中间文件)."""
    dur = max(1.5, duration)
    fps = 25
    frames = int(dur * fps)
    vf = (
        # 先等比缩进画框再补黑边 — 榜单/跑分截图绝不能拉伸变形 (数字会糊)
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"zoompan=z='min(zoom+0.0004,1.08)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={max(0, dur - 0.4):.2f}:d=0.4"
    )
    # 图源角标 (证据图管线⑤): 右下角半透明, 底部预留 ~8% 避开字幕区
    font = _pick_font()
    label = (source_media or "").strip()
    if font and label:
        fontsize = max(18, int(height * 0.030))
        vf += (
            f",drawtext=fontfile='{_filter_fontfile(font)}'"
            f":text='{_drawtext_escape(f'图源：{label[:24]}')}'"
            f":fontcolor=white@0.75:fontsize={fontsize}"
            f":box=1:boxcolor=black@0.35:boxborderw=8"
            f":x=w-tw-{int(width * 0.03)}:y=h-th-{int(height * 0.08)}"
        )
    else:
        logger.debug("[evidence] 图源角标跳过 (无字体 %s 或来源名 %r)", font, label)
    return vf


def execute_evidence_image_slot(db: Session, slot: DirectorSlot) -> str:
    """池内选图 → Ken Burns+角标成片, 返回 mp4 路径.

    选图文本 = slot.text_context + params.claim (导演给的核心事实句,
    数字最全); keywords 参与次级加分。无合格图 raise RuntimeError
    → executor 走 fallback 链 (broll_pexels)。
    """
    root = ensure_slot_dir(slot)
    job: DirectorJob = slot.director_job
    spec = get_video_format_spec(job.video_format)
    duration = round(slot.end_sec - slot.start_sec, 3)

    script = db.get(Script, job.script_id)
    pool = collect_evidence_pool(db, script) if script else []
    if not pool:
        raise RuntimeError("证据图池为空: 素材包无合格证据图 (VLM 未标出 is_chart)")

    params = slot.params_json or {}
    search_text = " ".join(x for x in (slot.text_context, params.get("claim")) if x)
    used = _collect_used_evidence_urls(db, slot)
    cand = pick_image_for_slot(search_text, params.get("keywords") or [], pool, used)
    if cand is None:
        raise RuntimeError(
            f"证据图池 {len(pool)} 张无一匹配段落 (数字/关键词都不沾), 走降级"
        )

    img = Path(cand["local_path"])
    if not img.exists():
        # 缓存被清 → 按 URL 重下 (下载器含 Pillow 校验)
        redl = _download_image(cand["url"], img.parent)
        if not redl:
            raise RuntimeError(f"证据图缓存丢失且重下失败: {img.name}")
        img = Path(redl[0])

    tmp = root / f"evidence_{slot.slot_index:03d}_raw.mp4"
    run_ffmpeg([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(img),
        "-vf", _build_vf(spec["width"], spec["height"], duration, cand.get("source_media")),
        "-t", f"{max(1.5, duration):.2f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        str(tmp),
    ], timeout=120)

    out_path = root / f"evidence_{slot.slot_index:03d}.mp4"
    render_scale_pad(
        tmp, out_path,
        width=spec["width"], height=spec["height"], duration=duration,
    )
    tmp.unlink(missing_ok=True)  # 中间产物 (build artifact, 红线例外)

    # 写回选图依据 (可观测 + 同 job 去重), params_json 须整体赋值才触发落库
    new_params = dict(slot.params_json or {})
    new_params["image_url"] = cand["url"]
    new_params["source_media"] = cand.get("source_media") or ""
    new_params["image_desc"] = cand.get("desc_zh") or ""
    slot.params_json = new_params
    db.commit()
    logger.info(
        "[evidence] slot %d -> %s (%s | %s)",
        slot.slot_index, out_path.name, cand.get("source_media"), cand.get("desc_zh"),
    )
    return str(out_path)

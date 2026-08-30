# -*- coding: utf-8 -*-
"""material_ingest_service — 素材摄入产线 v2 (2026-08-30, 用户三需求:
①UI 推进不再靠对话 ②链接→下载→识别→切片全流程 ③VPN 检测+等待+自动续跑).

六段流水 (2026-08-30 用户纠序: 先筛后切, 脏片段不产生):
  download → probe(抽帧+切点探测) → ocr(整片1fps时间轴) → split(仅干净窗内切片)
  → tag(每片一帧 LLM 内容识别) → register(入库+9维回填)
  先切后筛的浪费: 切片半净半脏 → 整片陪葬; 先筛后切把文字检测变成时间轴,
  切点 ∩ 干净窗 = 零浪费, 且省去脏片占盘。
VPN 门控: download 需代理 ON / tag (GPU-VPN 互斥) 需代理 OFF —
  探针 = 经 9876 代理访问 youtube generate_204; 不满足进 waiting_* 轮询,
  满足自动续; 30min 超时进 paused_* (UI resume 续)。
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..database import db_session
from ..models import MaterialIngestJob, VideoAsset

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PROXY = "http://127.0.0.1:9876"
VPN_PROBE_URL = "https://www.youtube.com/generate_204"
VPN_POLL_SEC = 5
VPN_WAIT_TIMEOUT_SEC = 30 * 60
STAGE_DIR = ROOT / "data" / "materials" / "youtube"
FF = r"C:\Programs\ffmpeg\bin\ffmpeg.exe"

# 阶段序 (resume 从当前 stage 重入)
STAGES = ["download", "probe", "ocr", "split", "tag", "register"]


# ── VPN 探针/门控 ──────────────────────────────────────────────
def vpn_state(timeout: int = 4) -> dict:
    """代理探针: 经 9876 访问 youtube → on/off + 延迟."""
    t0 = time.time()
    handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(handler)
    try:
        with opener.open(VPN_PROBE_URL, timeout=timeout) as resp:
            ok = resp.status in (200, 204)
    except Exception:
        ok = False
    return {"state": "on" if ok else "off",
            "latency_ms": int((time.time() - t0) * 1000),
            "checked_at": time.strftime("%H:%M:%S")}


def _wait_vpn(db: Session, job: MaterialIngestJob, want_on: bool) -> bool:
    """门控等待: 轮询到目标态 → True; 超时 → False (调用方置 paused)."""
    waiting_stage = f"waiting_vpn_{'on' if want_on else 'off'}"
    job.stage = waiting_stage
    stats = dict(job.stats_json or {})
    stats["wait_until"] = time.strftime("%H:%M:%S", time.localtime(time.time() + VPN_WAIT_TIMEOUT_SEC))
    job.stats_json = stats
    db.commit()
    deadline = time.time() + VPN_WAIT_TIMEOUT_SEC
    while time.time() < deadline:
        time.sleep(VPN_POLL_SEC)
        st = vpn_state()
        if (st["state"] == "on") == want_on:
            return True
    return False


# ── 实体字典 ───────────────────────────────────────────────────
def load_entities() -> list[dict]:
    import yaml
    p = ROOT / "config" / "geo_entities.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("entities") or []


def entity_entry(name: str) -> dict | None:
    return next((e for e in load_entities() if e["name"] == name), None)


def stock_count(db: Session, name: str) -> int:
    """库内该实体干净素材数 (tags 含实体名 — Python 层精确匹配, JSON 列 cast 陷阱)."""
    rows = db.query(VideoAsset).all()
    return sum(1 for r in rows
               if name in (r.tags or []) and "no_subtitle" in (r.tags or []))


# ── 摄取核心段 (复用 yt_ingest) ────────────────────────────────
def _yt_dlp() -> str:
    return str(Path(sys.executable))  # python -m yt_dlp


def _download(job: MaterialIngestJob) -> str:
    """yt-dlp 经代理下载 → 返回 mp4 路径."""
    out = STAGE_DIR / f"yt_{job.video_id}.mp4"
    if out.exists():
        return str(out)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--proxy", PROXY,
         "-f", "bv*[height<=1080]+ba/b[height<=1080]",
         "--merge-output-format", "mp4", "-o", str(out),
         f"https://www.youtube.com/watch?v={job.video_id}"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    if not out.exists():
        raise RuntimeError(f"下载失败: {(r.stderr or '')[-200:]}")
    return str(out)


def _fetch_info(video_id: str) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--proxy", PROXY, "--skip-download",
         "--print", "%(title)s", f"https://www.youtube.com/watch?v={video_id}"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    return {"title": (r.stdout or "").strip()[:200]}


def _split(job: MaterialIngestJob) -> dict:
    """干净窗切片 (v2.1 用户纠序): 切点 ∩ OCR 干净窗 → 只切干净段."""
    mf = STAGE_DIR / job.video_id / "manifest.json"
    video = str(STAGE_DIR / f"yt_{job.video_id}.mp4")
    tl = json.loads((STAGE_DIR / job.video_id / "timeline.json").read_text(encoding="utf-8"))
    cuts = tl.get("cuts") or []
    windows = tl.get("clean_windows") or []
    total = tl.get("total_sec") or 0.0
    if not windows:
        return {"clips": 0, "note": "全片带文字, 无干净窗"}

    # 候选段 = 切点分段; 无切点(静态机位演讲) → 干净窗内均匀 ~10s 切
    bounds = sorted(set([0.0] + [c for c in cuts if 0 < c < total] + [total]))
    segs = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
            if bounds[i + 1] - bounds[i] > 0.4]
    final: list[tuple[float, float]] = []
    for s, e in segs:
        # 找覆盖该段的干净窗, 求交集 (只保留净部分)
        for ws, we in windows:
            ns, ne = max(s, ws), min(e, we)
            if ne - ns >= 4.0:  # 最小可用片段
                final.append((round(ns, 2), round(ne, 2)))
    # 无切点兜底: 干净窗 >12s 未被覆盖 → 均匀切
    covered = final or []
    for ws, we in windows:
        if we - ws < 4.0:
            continue
        n = max(1, int((we - ws) // 10))
        step = (we - ws) / n
        covered += [(round(ws + i * step, 2), round(ws + (i + 1) * step, 2))
                    for i in range(n)]

    clips_dir = STAGE_DIR / job.video_id / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, (s, e) in enumerate(covered):
        out = clips_dir / f"clip_{i:03d}.mp4"
        if not out.exists():
            subprocess.run([FF, "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}",
                            "-i", video, "-c", "copy", str(out)],
                           capture_output=True, timeout=120)
        if out.exists() and out.stat().st_size > 50000:
            clips.append({"n": i, "start": s, "end": e,
                          "file": str(out.relative_to(ROOT)),
                          "ocr_clean": True})  # 出自干净窗, 天然干净
    manifest = {"video_id": job.video_id, "title": job.title or "",
                "entity": job.entity or "", "clips": clips}
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"clips": len(clips)}


def _probe(job: MaterialIngestJob) -> dict:
    """抽帧+切点探测: 场景切点 → timeline.json (OCR 段消费)."""
    video = str(STAGE_DIR / f"yt_{job.video_id}.mp4")
    out = subprocess.run(
        [r"C:\Programs\ffmpeg\bin\ffprobe.exe", "-v", "error",
         "-show_entries", "format=duration", "-of", "csv=p=0", video],
        capture_output=True, text=True, timeout=60)
    total = float((out.stdout or "0").strip() or 0)
    r = subprocess.run([FF, "-i", video, "-vf",
                        "select='gt(scene,0.20)',metadata=print", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=600)
    cuts = sorted(float(m.group(1)) for m in
                  re.finditer(r"pts_time:([0-9.]+)", r.stderr or ""))
    d = STAGE_DIR / job.video_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "timeline.json").write_text(
        json.dumps({"total_sec": total, "cuts": cuts}, ensure_ascii=False),
        encoding="utf-8")
    return {"total_sec": round(total, 1), "cuts": len(cuts)}


def _ocr(job: MaterialIngestJob) -> dict:
    """OCR 时间轴 (v2.1): 整片 1fps 逐秒判定 → 干净窗清单写 timeline.json."""
    try:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
    except ImportError:
        return {"error": "rapidocr 未装"}

    import tempfile
    video = str(STAGE_DIR / f"yt_{job.video_id}.mp4")
    tl_path = STAGE_DIR / job.video_id / "timeline.json"
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    total = tl.get("total_sec") or 0.0
    tmp = tempfile.mkdtemp(prefix="ocrfull_")

    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    # 逐秒抽帧+OCR (长片 ~100ms/帧; 25min≈1500帧≈3-4min CPU)
    dirty_secs: set[int] = set()
    t = 0.5
    while t < total:
        fp = Path(tmp) / f"{int(t*2)}.jpg"
        subprocess.run([FF, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", video,
                        "-frames:v", "1", "-vf", "scale=1280:-2",
                        "-pix_fmt", "yuvj420p", str(fp)], capture_output=True)
        if fp.exists():
            try:
                result, _ = ocr(str(fp))
            except Exception:
                result = None
            if result:
                for r in result:
                    if _f(r[2]) >= 0.55 and (r[0][3][1] - r[0][1][1]) >= 9:
                        dirty_secs.add(int(t))
                        break
            fp.unlink(missing_ok=True)
        t += 1.0

    # 干净窗合并 (脏秒即断窗; 连续干净段收窗)
    windows: list[list[float]] = []
    run_start = None
    for sec in range(int(total) + 1):
        if sec in dirty_secs:
            if run_start is not None:
                windows.append([run_start, float(sec)])
                run_start = None
        else:
            if run_start is None:
                run_start = float(sec)
    if run_start is not None:
        windows.append([run_start, total])
    windows = [[max(0.0, ws - 0.5), min(total, we + 0.5)] for ws, we in windows]  # 半秒容差
    tl["clean_windows"] = windows
    tl["dirty_secs"] = len(dirty_secs)
    tl_path.write_text(json.dumps(tl, ensure_ascii=False), encoding="utf-8")
    clean_total = sum(we - ws for ws, we in windows)
    return {"clean_windows": len(windows),
            "clean_sec": round(clean_total), "dirty_sec": len(dirty_secs)}


def _tag(job: MaterialIngestJob) -> dict:
    from sandbox.yt_ingest import cmd_tag
    cmd_tag(job.video_id)
    mf = STAGE_DIR / job.video_id / "manifest.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    tagged = sum(1 for c in m.get("clips", []) if c.get("tags"))
    return {"tagged": tagged}


def _register(db: Session, job: MaterialIngestJob) -> dict:
    """双清入库 (ocr_clean + llm 干净) + 实体标签 + 9 维回填一次跑完."""
    mf = STAGE_DIR / job.video_id / "manifest.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    ent = job.entity or ""
    existing = {a.file_path for a in db.query(VideoAsset).all()}
    today = f"V{time.strftime('%Y%m%d')}-"
    nums = [int(a.asset_no[-4:]) for a in db.query(VideoAsset)
            .filter(VideoAsset.asset_no.like(today + "%")).all()
            if a.asset_no[-4:].isdigit()]
    seq = max(nums, default=0)
    n = 0
    for c in m.get("clips", []):
        t = c.get("tags") or {}
        if not t or t.get("has_burned_text") or c.get("ocr_clean") is False:
            continue
        if c["end"] - c["start"] < 4.0:
            continue
        fp = str((ROOT / c["file"]).resolve())
        if fp in existing:
            continue
        seq += 1
        kw = [k for k in (t.get("keywords_en") or []) if k]
        tags = list(dict.fromkeys(kw + ([ent] if ent else []) + ["no_subtitle"]))
        db.add(VideoAsset(asset_no=f"{today}{seq:04d}", source="youtube",
                          file_path=fp, orientation="landscape",
                          width=1920, height=1080,
                          duration_sec=round(c["end"] - c["start"], 2),
                          description_zh=t.get("desc_zh") or "",
                          description_en=", ".join(kw),
                          raw_query=f"youtube:{(m.get('title') or '')[:80]}",
                          tags=tags, source_type="footage", location="foreign"))
        n += 1
    db.commit()
    return {"registered": n}


def _backfill_dims(db: Session, job: MaterialIngestJob) -> int:
    """新入库片段 9 维回填 (flash, 同批内联跑 — 不再手动 backfill)."""
    rows = (db.query(VideoAsset)
            .filter(VideoAsset.source == "youtube",
                    VideoAsset.file_path.contains(job.video_id))
            .all())
    todo = [a for a in rows if not a.scenes or a.scenes in ("[]", "", "null")]
    if not todo:
        return 0
    from ..services.boost_service import _call, _extract_json
    import yaml as _yaml
    vocab = (_yaml.safe_load((ROOT / "data" / "vocabulary_pack.json")
            .read_text(encoding="utf-8")) or {}).get("dimensions") or {}
    batch, done = 10, 0
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        items = json.dumps([{"i": j, "desc_zh": a.description_zh or "",
                             "kw": (a.description_en or "")[:80]}
                            for j, a in enumerate(chunk)], ensure_ascii=False)
        prompt = (f"给视频素材补检索维度标签,只输出JSON数组。枚举: scenes={vocab.get('scenes')} "
                  f"shot_types={vocab.get('shot_types')} tone={vocab.get('tone')} "
                  f"motion_level={vocab.get('motion_level')} content_density={vocab.get('content_density')} "
                  f"time_of_day={vocab.get('time_of_day')}。与输入同序: "
                  f'[{{"i":0,"scenes":["科技"],"shot_types":["特写"],"tone":"cool",'
                  f'"motion_level":"slow","content_density":"moderate","time_of_day":"indoor"}}]。清单: {items}')
        try:
            data = _extract_json(_call(prompt, json_mode=True,
                                       max_tokens=6000, temperature=0.2)) or []
        except Exception:
            continue
        by_i = {d.get("i"): d for d in data if isinstance(d, dict)}
        for j, a in enumerate(chunk):
            d = by_i.get(j)
            if not d:
                continue
            a.scenes = json.dumps(d.get("scenes") or [], ensure_ascii=False)
            a.shot_types = json.dumps(d.get("shot_types") or [], ensure_ascii=False)
            a.tone = d.get("tone") or "neutral"
            a.motion_level = d.get("motion_level") or "slow"
            a.content_density = d.get("content_density") or "moderate"
            a.time_of_day = d.get("time_of_day") or "undefined"
            done += 1
        db.commit()
    return done


# ── 任务执行器 ─────────────────────────────────────────────────
def _run_job(job_id: str) -> None:
    with db_session() as db:
        job = db.query(MaterialIngestJob).filter(MaterialIngestJob.id == job_id).first()
        if not job:
            return
        try:
            _advance(db, job)
        except Exception as exc:
            logger.exception("[ingest %s] failed", job_id[:8])
            job.stage = "failed"
            job.error = str(exc)[:500]
            db.commit()


def _advance(db: Session, job: MaterialIngestJob) -> None:
    """从当前 stage 起推进到 done (幂等, 各段可重入)."""
    order = {s: i for i, s in enumerate(STAGES)}
    start = order.get(job.stage, 0) if job.stage in order else 0
    if job.stage.startswith(("waiting", "paused")):
        start = 0 if job.stage.endswith("_on") else 4  # wait_on → 从头; wait_off → 从 tag
    stats = dict(job.stats_json or {})

    for stage in STAGES[start:]:
        # VPN 门控
        if stage == "download":
            if vpn_state()["state"] != "on":
                if not _wait_vpn(db, job, want_on=True):
                    job.stage = "paused_vpn_on"
                    db.commit()
                    return
        if stage == "tag":
            if vpn_state()["state"] != "off":
                if not _wait_vpn(db, job, want_on=False):
                    job.stage = "paused_vpn_off"
                    db.commit()
                    return

        job.stage = {"download": "downloading", "probe": "probing", "ocr": "ocr",
                     "split": "splitting", "tag": "tagging",
                     "register": "registering"}[stage]
        db.commit()

        if stage == "download":
            if not job.video_id:
                m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", job.source_url or "")
                if not m:
                    raise ValueError(f"无法从 URL 解析视频 ID: {job.source_url}")
                job.video_id = m.group(1)
                db.commit()
            if not job.title:
                try:
                    job.title = _fetch_info(job.video_id).get("title") or ""
                    db.commit()
                except Exception:
                    pass
            _download(job)
        elif stage == "probe":
            stats.update(_probe(job))
        elif stage == "ocr":
            stats.update(_ocr(job))
        elif stage == "split":
            stats.update(_split(job))
        elif stage == "tag":
            stats.update(_tag(job))
        elif stage == "register":
            stats.update(_register(db, job))
            stats["dims_backfilled"] = _backfill_dims(db, job)
        job.stats_json = stats
        db.commit()

    job.stage = "done"
    db.commit()
    logger.info("[ingest %s] done: %s", job.id[:8], stats)


# ── 搜索规划器 (2026-08-30 用户单: 源头干净度是最上游杠杆) ────────
# 领域知识固化进提示词: 官方政府频道/国会/C-SPAN 是 raw 无字幕; 新闻台
# (CNN/BBC/DW/日テレ等) 上传必带 chyron 字幕条。LLM 按"干净源优先"生成
# 搜索词 + 指定官方频道 + 片名避雷词, 下载前预筛掉注定脏的源。

QUERY_PLANNER_PROMPT = """你是 YouTube 素材采购专家。为下面的实体生成"能搜到无字幕干净素材"的搜索方案。只输出 JSON。

# 干净源知识 (核心依据)
- 官方政府/机构频道 (The White House, 首相官邸, Kremlin, UN, 国会官方, C-SPAN, NATO, 白宫档案馆) = raw 无字幕, 最优
- 新闻台上传 (CNN/BBC/FOX/DW/NHK/日テレ/TBS/ABS-CBN/ANC...) = 必带字幕条+台标, 尽量避开
- 有利词: "full speech" "raw" "no commentary" "press conference" 官方口径
- 不利词(片名含则脏): "subtitles" "subtitulado" "字幕" "CC" "hardcoded" "highlights"(新闻剪辑)

# 任务
给实体生成 3 路搜索 (queries) + 若知道其官方频道给出频道 handle (channels, 没有给空) + 片名避雷正则词 (avoid, 除上述通用词外加该实体特有的)

# 输出
{"queries": ["...", "...", "..."], "channels": ["@Kantei...", ...], "avoid": ["新闻台名", ...]}"""

# 通用片名避雷 (静态): 预筛注定脏的源, 不浪费下载
_STATIC_AVOID = re.compile(
    r"subtitl|subtitulado|字幕|hardcoded|\bCC\b|closed.?caption|"
    r"\bCNN\b|\bBBC\b|\bFOX\b|\bMSNBC\b|\bDW News\b|\bAl.?Jazeera\b|"
    r"\bNHK\b|日テレ|テレ朝|TBS.?NEWS|\bABS.?CBN\b|\bANC\b|"
    r"news.?live|breaking", re.I)


def plan_queries(entity: str, etype: str) -> dict:
    """LLM 搜索规划: 干净源导向的 queries + 官方频道 + 避雷词."""
    try:
        from ..services.boost_service import _call, _extract_json
        raw = _call(QUERY_PLANNER_PROMPT + f"\n\n【实体】{entity} ({etype})",
                    json_mode=True, max_tokens=600, temperature=0.3)
        data = _extract_json(raw) or {}
        return {"queries": [q for q in (data.get("queries") or []) if q][:3],
                "channels": [c for c in (data.get("channels") or []) if c][:2],
                "avoid": [a for a in (data.get("avoid") or []) if a][:6]}
    except Exception as exc:
        logger.warning("[ingest] 搜索规划失败(退字典默认): %s", exc)
        return {"queries": [], "channels": [], "avoid": []}


def _title_clean(title: str, extra_avoid: list[str]) -> bool:
    """片名预筛: 避雷词命中 → 弃 (不浪费下载)."""
    if _STATIC_AVOID.search(title or ""):
        return False
    low = (title or "").lower()
    return not any(a.lower() in low for a in extra_avoid)


def _run_entity_batch(parent_id: str) -> None:
    """实体批: 搜索 → 建子任务 → 顺序执行."""
    with db_session() as db:
        parent = db.query(MaterialIngestJob).filter(
            MaterialIngestJob.id == parent_id).first()
        if not parent:
            return
        ent = entity_entry(parent.entity or "")
        custom_search = (parent.stats_json or {}).get("custom_search")
        if not ent and not custom_search:
            parent.stage = "failed"
            parent.error = f"实体字典无此实体: {parent.entity}"
            db.commit()
            return
        max_dur = int((ent or {}).get("max_duration", 3600))
        max_videos = int((ent or {}).get("max_videos", 2))
        etype = (ent or {}).get("type", "person")

        # 🔮 LLM 搜索规划 (2026-08-30): 干净源导向 — 官方频道优先/新闻台避雷
        plan = plan_queries(parent.entity or "", etype)
        queries: list[str] = []
        channels: list[str] = []
        if custom_search:
            queries.append(f"ytsearch{max_videos + 2}:" + custom_search)
        if ent and ent.get("channel"):
            channels.append(f"https://www.youtube.com/{ent['channel']}/videos")
        channels += [f"https://www.youtube.com/{c}/videos" for c in plan["channels"]]
        # 字典默认搜索词兜底 (规划空/全失败时)
        if not queries and not channels:
            base = (ent or {}).get("search") or custom_search or parent.entity
            queries.append(f"ytsearch{max_videos + 2}:" + base)
        else:
            for q in plan["queries"][:2]:
                queries.append(f"ytsearch{max(2, max_videos - 1)}:" + q)
            if ent and not custom_search and channels:
                queries.append(f"ytsearch2:" + (ent.get("search") or parent.entity))

        avoid = plan["avoid"]
        kids: dict[str, str] = {}  # video_id -> title (跨路去重)
        for src in channels + queries:
            if len(kids) >= max_videos + 2:
                break
            r = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--proxy", PROXY, "--flat-playlist",
                 "--print", "%(id)s|%(duration)s|%(title)s", src],
                cwd=str(ROOT), capture_output=True, text=True, timeout=300)
            for line in (r.stdout or "").splitlines():
                if len(kids) >= max_videos + 2:
                    break
                parts = [p.strip() for p in line.split("|")]
                if len(parts) != 3 or not parts[0] or parts[0] == "NA":
                    continue
                dur = float(parts[1]) if parts[1].replace(".", "").isdigit() else 0
                if not dur or not (30 <= dur <= max_dur):
                    continue
                if parts[0] in kids:
                    continue
                if not _title_clean(parts[2], avoid):  # 📋 片名预筛
                    continue
                kids[parts[0]] = parts[2][:200]

        child_ids = []
        for vid, title in list(kids.items())[:max_videos + 1]:
            kid = MaterialIngestJob(mode="url", entity=parent.entity,
                                    source_url=f"https://www.youtube.com/watch?v={vid}",
                                    video_id=vid, title=title,
                                    stage="queued", parent_id=parent.id)
            db.add(kid)
            db.flush()
            child_ids.append(kid.id)
        parent.stats_json = {"children": len(child_ids),
                             "planned_queries": plan["queries"],
                             "planned_channels": plan["channels"]}
        parent.stage = "done"  # 父任务=调度器, 子任务各自跑
        db.commit()

    for cid in child_ids:
        _run_job(cid)


def start_job(job_id: str, mode: str) -> None:
    t = threading.Thread(
        target=_run_entity_batch if mode == "entity" else _run_job,
        args=(job_id,), daemon=True, name=f"ingest-{job_id[:8]}")
    t.start()

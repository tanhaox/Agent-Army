# -*- coding: utf-8 -*-
"""material_ingest_service — 素材摄入产线 v2 (2026-08-30, 用户三需求:
①UI 推进不再靠对话 ②链接→下载→识别→切片全流程 ③VPN 检测+等待+自动续跑).

五段流水 (各段幂等断点): download → split → ocr → tag → register
VPN 门控: download 需代理 ON / tag (GPU-VPN 互斥) 需代理 OFF —
  探针 = 经 9876 代理访问 youtube generate_204; 不满足进 waiting_* 轮询,
  满足自动续; 30min 超时进 paused_* (UI resume 续)。
复用: sandbox/yt_ingest.py 的 split/ocr/tag 逻辑 (三轮实测打磨)。
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
STAGES = ["download", "split", "ocr", "tag", "register"]


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
    from sandbox.yt_ingest import cmd_split
    video = str(STAGE_DIR / f"yt_{job.video_id}.mp4")
    cmd_split(video, job.video_id, entity=job.entity or "", title=job.title or "")
    mf = STAGE_DIR / job.video_id / "manifest.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    return {"clips": len(m.get("clips", []))}


def _ocr(job: MaterialIngestJob) -> dict:
    from sandbox.yt_ingest import ocr_screen
    return ocr_screen(job.video_id)


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
        start = 0 if job.stage.endswith("_on") else 3  # wait_on → 从头; wait_off → 从 tag
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

        job.stage = stage + "ing" if stage != "register" else "registering"
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
        elif stage == "split":
            stats.update(_split(job))
        elif stage == "ocr":
            stats.update(_ocr(job))
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


def _run_entity_batch(parent_id: str) -> None:
    """实体批: 搜索 → 建子任务 → 顺序执行."""
    with db_session() as db:
        parent = db.query(MaterialIngestJob).filter(
            MaterialIngestJob.id == parent_id).first()
        if not parent:
            return
        ent = entity_entry(parent.entity or "")
        if not ent:
            parent.stage = "failed"
            parent.error = f"实体字典无此实体: {parent.entity}"
            db.commit()
            return
        query = (f"ytsearch{ent.get('max_videos', 2)}:" + ent["search"]
                 if not ent.get("channel") else
                 f"https://www.youtube.com/{ent['channel']}/videos")
        max_dur = int(ent.get("max_duration", 3600))
        r = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--proxy", PROXY, "--flat-playlist",
             "--print", "%(id)s|%(duration)s|%(title)s", query],
            cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        kids: list[str] = []
        for line in (r.stdout or "").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3 or not parts[0] or parts[0] == "NA":
                continue
            dur = float(parts[1]) if parts[1].replace(".", "").isdigit() else 0
            if not dur or not (30 <= dur <= max_dur):
                continue
            kid = MaterialIngestJob(mode="url", entity=parent.entity,
                                    source_url=f"https://www.youtube.com/watch?v={parts[0]}",
                                    video_id=parts[0], title=parts[2][:200],
                                    stage="queued", parent_id=parent.id)
            db.add(kid)
            db.flush()
            kids.append(kid.id)
        parent.stats_json = {"children": len(kids)}
        parent.stage = "done"  # 父任务=调度器, 子任务各自跑
        db.commit()

    for kid in kids:
        _run_job(kid)


def start_job(job_id: str, mode: str) -> None:
    t = threading.Thread(
        target=_run_entity_batch if mode == "entity" else _run_job,
        args=(job_id,), daemon=True, name=f"ingest-{job_id[:8]}")
    t.start()
